"""Tests for backfill Lambda handler."""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from moto import mock_aws
import boto3

from features.bond_spreads.handlers.backfill import handler, send_cfn_response
from features.bond_spreads.models.types import CountryConfig
from features.bond_spreads.services.fred_client import FredClient


@pytest.fixture
def lambda_context():
    """Mock Lambda context."""
    context = Mock()
    context.function_name = "test-backfill-function"
    context.memory_limit_in_mb = 512
    context.invoked_function_arn = "arn:aws:lambda:eu-central-1:123456789012:function:test-backfill"
    context.aws_request_id = "test-request-id"
    context.log_stream_name = "test-log-stream"
    return context


@pytest.fixture
def lambda_env(monkeypatch):
    """Set Lambda environment variables."""
    monkeypatch.setenv("STAGE", "box")
    monkeypatch.setenv("TABLE_NAME", "test-table")
    monkeypatch.setenv("BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("DISTRIBUTION_ID", "E123456")
    monkeypatch.setenv("SSM_PREFIX", "/fm/box")
    monkeypatch.setenv("AWS_REGION", "eu-central-1")


@pytest.fixture
def cfn_create_event():
    """Mock CloudFormation CREATE event."""
    return {
        "RequestType": "Create",
        "ResponseURL": "https://cloudformation-custom-resource-response.s3.amazonaws.com/test",
        "StackId": "arn:aws:cloudformation:eu-central-1:123456789012:stack/test-stack/guid",
        "RequestId": "unique-request-id",
        "LogicalResourceId": "BondSpreadsBackfill",
        "ResourceType": "Custom::BondSpreadsBackfill"
    }


@pytest.fixture
def cfn_delete_event(cfn_create_event):
    """Mock CloudFormation DELETE event."""
    event = cfn_create_event.copy()
    event["RequestType"] = "Delete"
    return event


@pytest.fixture
def cfn_update_event(cfn_create_event):
    """Mock CloudFormation UPDATE event."""
    event = cfn_create_event.copy()
    event["RequestType"] = "Update"
    return event


@pytest.fixture
def mock_historical_fred_data():
    """Mock 10 years of FRED data."""
    data = []
    for year in range(2016, 2026):
        for month in range(1, 13):
            data.append({
                "date": f"{year}-{month:02d}-01",
                "value": str(4.0 + (year - 2016) * 0.05 + month * 0.01)
            })
    return data


@mock_aws
def test_backfill_success_empty_table(lambda_context, lambda_env, cfn_create_event, mock_historical_fred_data):
    """Test full backfill runs when table is empty."""
    # Create DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
    table = dynamodb.create_table(
        TableName='test-table',
        KeySchema=[
            {'AttributeName': 'pk', 'KeyType': 'HASH'},
            {'AttributeName': 'sk', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'pk', 'AttributeType': 'S'},
            {'AttributeName': 'sk', 'AttributeType': 'S'},
            {'AttributeName': 'gsi1pk', 'AttributeType': 'S'},
            {'AttributeName': 'gsi1sk', 'AttributeType': 'N'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'GSI1',
                'KeySchema': [
                    {'AttributeName': 'gsi1pk', 'KeyType': 'HASH'},
                    {'AttributeName': 'gsi1sk', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    # Create S3 bucket
    s3 = boto3.client('s3', region_name='eu-central-1')
    s3.create_bucket(
        Bucket='test-bucket',
        CreateBucketConfiguration={'LocationConstraint': 'eu-central-1'}
    )

    # Create CloudFront client
    boto3.client('cloudfront', region_name='eu-central-1')

    with patch('features.bond_spreads.handlers.backfill.get_secure_parameter') as mock_ssm, \
         patch('features.bond_spreads.handlers.backfill.COUNTRIES') as mock_countries, \
         patch('features.bond_spreads.handlers.backfill.send_cfn_response') as mock_cfn_response:

        mock_ssm.return_value = "test-api-key"

        # Use single country for simplicity
        mock_countries.__iter__ = lambda self: iter([
            CountryConfig(code="US", name="United States", currency="USD", flag="🇺🇸", series_10y="DGS10", series_3m="DTB3")
        ])
        mock_countries.__len__ = lambda self: 1

        with patch.object(FredClient, 'validate_series') as mock_validate, \
             patch.object(FredClient, 'get_series') as mock_get_series, \
             patch.object(FredClient, '_wait_for_rate_limit') as mock_rate_limit:
            # Disable rate limiting
            mock_rate_limit.return_value = None
            # Mock validate_series to always return True
            mock_validate.return_value = True
            # Mock get_series to return historical data (converted to float)
            historical_data = [
                {"date": entry["date"], "value": float(entry["value"])}
                for entry in mock_historical_fred_data[:120]
            ]
            mock_get_series.return_value = historical_data

            result = handler(cfn_create_event, lambda_context)

            # Verify success
            assert result['statusCode'] == 200
            assert result['body']['total_records'] > 0

            # Verify CFN response was sent
            mock_cfn_response.assert_called()
            call_args = mock_cfn_response.call_args
            assert call_args[0][2] == "SUCCESS"  # status

            # Verify data was written to DynamoDB with BS# prefix
            response = table.scan()
            items = response['Items']
            assert len(items) > 0

            # Check that records use BS# prefix
            country_records = [item for item in items if item['pk'].startswith('BS#COUNTRY#')]
            assert len(country_records) > 0

            # Verify metadata
            meta_items = [item for item in items if item['pk'] == 'BS#META']
            assert len(meta_items) > 0

            # Verify S3 uploads to data/bond-spreads/
            objects = s3.list_objects_v2(Bucket='test-bucket', Prefix='data/bond-spreads/')
            assert 'Contents' in objects
            keys = [obj['Key'] for obj in objects['Contents']]
            assert 'data/bond-spreads/spreads-latest.json' in keys
            assert 'data/bond-spreads/spreads-history.json' in keys
            assert 'data/bond-spreads/spreads-summary.json' in keys


@mock_aws
def test_backfill_skips_when_data_exists(lambda_context, lambda_env, cfn_create_event):
    """Test backfill exits successfully when data already exists."""
    # Create DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
    table = dynamodb.create_table(
        TableName='test-table',
        KeySchema=[
            {'AttributeName': 'pk', 'KeyType': 'HASH'},
            {'AttributeName': 'sk', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'pk', 'AttributeType': 'S'},
            {'AttributeName': 'sk', 'AttributeType': 'S'},
            {'AttributeName': 'gsi1pk', 'AttributeType': 'S'},
            {'AttributeName': 'gsi1sk', 'AttributeType': 'N'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'GSI1',
                'KeySchema': [
                    {'AttributeName': 'gsi1pk', 'KeyType': 'HASH'},
                    {'AttributeName': 'gsi1sk', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    # Pre-populate with BS# data
    table.put_item(Item={
        'pk': 'BS#COUNTRY#US',
        'sk': '2025-01',
        'country_code': 'US',
        'spread_bps': 100
    })

    with patch('features.bond_spreads.handlers.backfill.get_secure_parameter') as mock_ssm, \
         patch('features.bond_spreads.handlers.backfill.send_cfn_response') as mock_cfn_response:

        mock_ssm.return_value = "test-api-key"

        result = handler(cfn_create_event, lambda_context)

        # Verify skipped
        assert result['statusCode'] == 200
        assert result['body'] == "Data already exists - skipped"

        # Verify CFN response was sent with success
        mock_cfn_response.assert_called()
        call_args = mock_cfn_response.call_args
        assert call_args[0][2] == "SUCCESS"


@mock_aws
def test_backfill_delete_event_no_action(lambda_context, lambda_env, cfn_delete_event):
    """Test DELETE event does nothing and returns success."""
    with patch('features.bond_spreads.handlers.backfill.send_cfn_response') as mock_cfn_response:
        result = handler(cfn_delete_event, lambda_context)

        assert result['statusCode'] == 200
        assert result['body'] == "No action needed"

        # Verify CFN response
        mock_cfn_response.assert_called()
        call_args = mock_cfn_response.call_args
        assert call_args[0][2] == "SUCCESS"


@mock_aws
def test_backfill_update_event_no_action(lambda_context, lambda_env, cfn_update_event):
    """Test UPDATE event does nothing and returns success."""
    with patch('features.bond_spreads.handlers.backfill.send_cfn_response') as mock_cfn_response:
        result = handler(cfn_update_event, lambda_context)

        assert result['statusCode'] == 200
        assert result['body'] == "No action needed"

        # Verify CFN response
        mock_cfn_response.assert_called()
        call_args = mock_cfn_response.call_args
        assert call_args[0][2] == "SUCCESS"


@mock_aws
def test_backfill_uses_bs_prefix(lambda_context, lambda_env, cfn_create_event, mock_historical_fred_data):
    """Test that backfill writes use BS# prefix."""
    # Create DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
    table = dynamodb.create_table(
        TableName='test-table',
        KeySchema=[
            {'AttributeName': 'pk', 'KeyType': 'HASH'},
            {'AttributeName': 'sk', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'pk', 'AttributeType': 'S'},
            {'AttributeName': 'sk', 'AttributeType': 'S'},
            {'AttributeName': 'gsi1pk', 'AttributeType': 'S'},
            {'AttributeName': 'gsi1sk', 'AttributeType': 'N'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'GSI1',
                'KeySchema': [
                    {'AttributeName': 'gsi1pk', 'KeyType': 'HASH'},
                    {'AttributeName': 'gsi1sk', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    # Create S3 bucket
    s3 = boto3.client('s3', region_name='eu-central-1')
    s3.create_bucket(
        Bucket='test-bucket',
        CreateBucketConfiguration={'LocationConstraint': 'eu-central-1'}
    )

    # Create CloudFront client
    boto3.client('cloudfront', region_name='eu-central-1')

    with patch('features.bond_spreads.handlers.backfill.get_secure_parameter') as mock_ssm, \
         patch('features.bond_spreads.handlers.backfill.COUNTRIES') as mock_countries, \
         patch('features.bond_spreads.handlers.backfill.send_cfn_response') as mock_cfn_response:

        mock_ssm.return_value = "test-api-key"

        mock_countries.__iter__ = lambda self: iter([
            CountryConfig(code="DE", name="Germany", currency="EUR", flag="🇩🇪", series_10y="TEST10", series_3m="TEST3M")
        ])
        mock_countries.__len__ = lambda self: 1

        with patch.object(FredClient, 'validate_series') as mock_validate, \
             patch.object(FredClient, 'get_series') as mock_get_series, \
             patch.object(FredClient, '_wait_for_rate_limit') as mock_rate_limit:
            # Disable rate limiting
            mock_rate_limit.return_value = None
            mock_validate.return_value = True
            # Mock get_series
            historical_data = [
                {"date": entry["date"], "value": float(entry["value"])}
                for entry in mock_historical_fred_data[:24]  # 2 years
            ]
            mock_get_series.return_value = historical_data

            result = handler(cfn_create_event, lambda_context)

            # Verify records use BS#COUNTRY# prefix
            response = table.scan()
            country_records = [item for item in response['Items'] if item['pk'].startswith('BS#COUNTRY#')]
            assert len(country_records) > 0

            # Check specific record
            first_record = country_records[0]
            assert first_record['pk'] == 'BS#COUNTRY#DE'
            assert first_record['gsi1pk'].startswith('BS#PERIOD#')


@mock_aws
def test_backfill_handles_failed_countries(lambda_context, lambda_env, cfn_create_event):
    """Test that backfill continues when some countries fail."""
    # Create DynamoDB table
    dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
    table = dynamodb.create_table(
        TableName='test-table',
        KeySchema=[
            {'AttributeName': 'pk', 'KeyType': 'HASH'},
            {'AttributeName': 'sk', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'pk', 'AttributeType': 'S'},
            {'AttributeName': 'sk', 'AttributeType': 'S'},
            {'AttributeName': 'gsi1pk', 'AttributeType': 'S'},
            {'AttributeName': 'gsi1sk', 'AttributeType': 'N'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'GSI1',
                'KeySchema': [
                    {'AttributeName': 'gsi1pk', 'KeyType': 'HASH'},
                    {'AttributeName': 'gsi1sk', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    # Create S3 bucket
    s3 = boto3.client('s3', region_name='eu-central-1')
    s3.create_bucket(
        Bucket='test-bucket',
        CreateBucketConfiguration={'LocationConstraint': 'eu-central-1'}
    )

    # Create CloudFront client
    boto3.client('cloudfront', region_name='eu-central-1')

    with patch('features.bond_spreads.handlers.backfill.get_secure_parameter') as mock_ssm, \
         patch('features.bond_spreads.handlers.backfill.COUNTRIES') as mock_countries, \
         patch('features.bond_spreads.handlers.backfill.send_cfn_response') as mock_cfn_response:

        mock_ssm.return_value = "test-api-key"

        # Two countries - one will fail validation, one succeeds
        mock_countries.__iter__ = lambda self: iter([
            CountryConfig(code="XX", name="Bad", currency="XXX", flag="🏴", series_10y="BAD", series_3m="BAD"),
            CountryConfig(code="US", name="United States", currency="USD", flag="🇺🇸", series_10y="GOOD", series_3m="GOOD")
        ])
        mock_countries.__len__ = lambda self: 2

        with patch.object(FredClient, 'validate_series') as mock_validate, \
             patch.object(FredClient, 'get_series') as mock_get_series, \
             patch.object(FredClient, '_wait_for_rate_limit') as mock_rate_limit:
            # Disable rate limiting
            mock_rate_limit.return_value = None

            # First validation fails (for XX), second and third succeed (for US)
            mock_validate.side_effect = [False, True, True]

            # Mock get_series for US only
            mock_get_series.return_value = [
                {"date": "2025-01-01", "value": 4.5},
                {"date": "2025-02-01", "value": 4.6}
            ]

            result = handler(cfn_create_event, lambda_context)

            # Should succeed overall but report failed countries
            assert result['statusCode'] == 200
            assert 'XX' in result['body']['failed_countries']


def test_send_cfn_response_no_url(lambda_context):
    """Test send_cfn_response handles missing ResponseURL gracefully."""
    event = {"StackId": "test"}  # No ResponseURL

    # Should not raise, just log warning
    send_cfn_response(event, lambda_context, "SUCCESS")


def test_send_cfn_response_with_url(lambda_context):
    """Test send_cfn_response sends proper HTTP PUT."""
    event = {
        "ResponseURL": "https://example.com/response",
        "StackId": "arn:aws:cloudformation:eu-central-1:123456789012:stack/test/guid",
        "RequestId": "req-123",
        "LogicalResourceId": "TestResource"
    }

    with patch('features.bond_spreads.handlers.backfill.http.request') as mock_http:
        send_cfn_response(event, lambda_context, "SUCCESS", data={"Test": "Value"})

        # Verify HTTP PUT was called
        mock_http.assert_called_once()
        call_args = mock_http.call_args

        assert call_args[0][0] == "PUT"
        assert call_args[0][1] == "https://example.com/response"

        # Verify body contains required fields
        body = json.loads(call_args[1]['body'].decode('utf-8'))
        assert body['Status'] == 'SUCCESS'
        assert body['StackId'] == event['StackId']
        assert body['RequestId'] == event['RequestId']
        assert body['LogicalResourceId'] == event['LogicalResourceId']
        assert body['Data'] == {"Test": "Value"}
