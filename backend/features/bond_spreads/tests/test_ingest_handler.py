"""Tests for ingest Lambda handler."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from moto import mock_aws
import boto3

from features.bond_spreads.handlers.ingest import handler
from features.bond_spreads.models.types import CountryConfig
from features.bond_spreads.services.fred_client import FredClient


@pytest.fixture
def lambda_context():
    """Mock Lambda context."""
    context = Mock()
    context.function_name = "test-function"
    context.memory_limit_in_mb = 128
    context.invoked_function_arn = "arn:aws:lambda:eu-central-1:123456789012:function:test-function"
    context.aws_request_id = "test-request-id"
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
def mock_fred_data():
    """Mock FRED API responses."""
    return [
        {"date": "2026-01-01", "value": "4.52"},
        {"date": "2026-01-15", "value": "4.55"}
    ]


@mock_aws
def test_ingest_success_full_processing(lambda_context, lambda_env, mock_fred_data):
    """Test successful ingestion with all countries processed."""
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

    # Create CloudFront client (for moto)
    boto3.client('cloudfront', region_name='eu-central-1')

    with patch('features.bond_spreads.handlers.ingest.is_kill_switch_active') as mock_kill_switch, \
         patch('features.bond_spreads.handlers.ingest.get_secure_parameter') as mock_ssm, \
         patch('features.bond_spreads.handlers.ingest.COUNTRIES') as mock_countries, \
         patch('features.bond_spreads.handlers.ingest.get_target_period') as mock_period:

        # Setup mocks
        mock_kill_switch.return_value = False
        mock_ssm.return_value = "test-api-key"
        mock_period.return_value = "2026-01"

        # Use only one country for simplicity
        mock_countries.__iter__ = lambda self: iter([
            CountryConfig(
                code="US",
                name="United States",
                currency="USD",
                flag="🇺🇸",
                series_10y="DGS10",
                series_3m="DTB3"
            )
        ])
        mock_countries.__len__ = lambda self: 1

        with patch.object(FredClient, 'get_series') as mock_get_series, \
             patch.object(FredClient, '_wait_for_rate_limit') as mock_rate_limit:
            # Disable rate limiting in tests
            mock_rate_limit.return_value = None
            # Mock FRED API responses - return the actual data list
            mock_get_series.return_value = [
                {"date": "2026-01-01", "value": 4.52},
                {"date": "2026-01-15", "value": 4.55}
            ]

            # Call handler
            result = handler({}, lambda_context)

            # Verify response
            assert result['statusCode'] == 200
            assert result['body']['period'] == "2026-01"
            assert result['body']['processed'] == 1
            assert result['body']['skipped'] == 0
            assert result['body']['errors'] == 0

            # Verify DynamoDB record
            response = table.get_item(Key={'pk': 'BS#COUNTRY#US', 'sk': '2026-01'})
            assert 'Item' in response
            item = response['Item']
            assert item['country_code'] == 'US'
            assert item['gsi1pk'] == 'BS#PERIOD#2026-01'
            assert 'spread_bps' in item
            assert 'yield_10y' in item
            assert 'yield_3m' in item

            # Verify S3 uploads
            objects = s3.list_objects_v2(Bucket='test-bucket', Prefix='data/bond-spreads/')
            assert 'Contents' in objects
            keys = [obj['Key'] for obj in objects['Contents']]
            assert 'data/bond-spreads/spreads-latest.json' in keys
            assert 'data/bond-spreads/spreads-history.json' in keys
            assert 'data/bond-spreads/spreads-summary.json' in keys


@mock_aws
def test_ingest_kill_switch_active(lambda_context, lambda_env):
    """Test ingestion aborts when kill switch is active."""
    with patch('features.bond_spreads.handlers.ingest.is_kill_switch_active') as mock_kill_switch:
        mock_kill_switch.return_value = True

        result = handler({}, lambda_context)

        assert result['statusCode'] == 200
        assert result['body'] == "Kill switch active - skipped"


@mock_aws
def test_ingest_idempotent_skips_existing_records(lambda_context, lambda_env, mock_fred_data):
    """Test that existing records are skipped (idempotent behavior)."""
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

    # Pre-populate with existing record (must have all fields for from_dynamo_item)
    from decimal import Decimal
    table.put_item(Item={
        'pk': 'BS#COUNTRY#US',
        'sk': '2026-01',
        'gsi1pk': 'BS#PERIOD#2026-01',
        'gsi1sk': 100,
        'country_code': 'US',
        'country_name': 'United States',
        'currency': 'USD',
        'flag': '🇺🇸',
        'period': '2026-01',
        'yield_10y': Decimal('4.5'),
        'yield_3m': Decimal('2.5'),
        'spread_pct': Decimal('2.0'),
        'spread_bps': 200,
        'is_inverted': False,
        'updated_at': '2026-01-01T00:00:00Z'
    })

    # Create S3 bucket
    s3 = boto3.client('s3', region_name='eu-central-1')
    s3.create_bucket(
        Bucket='test-bucket',
        CreateBucketConfiguration={'LocationConstraint': 'eu-central-1'}
    )

    # Create CloudFront client
    boto3.client('cloudfront', region_name='eu-central-1')

    with patch('features.bond_spreads.handlers.ingest.is_kill_switch_active') as mock_kill_switch, \
         patch('features.bond_spreads.handlers.ingest.get_secure_parameter') as mock_ssm, \
         patch('features.bond_spreads.handlers.ingest.COUNTRIES') as mock_countries, \
         patch('features.bond_spreads.handlers.ingest.get_target_period') as mock_period:

        mock_kill_switch.return_value = False
        mock_ssm.return_value = "test-api-key"
        mock_period.return_value = "2026-01"

        mock_countries.__iter__ = lambda self: iter([
            CountryConfig(
                code="US",
                name="United States",
                currency="USD",
                flag="🇺🇸",
                series_10y="DGS10",
                series_3m="DTB3"
            )
        ])
        mock_countries.__len__ = lambda self: 1

        # Call handler
        result = handler({}, lambda_context)

        # Verify skipped
        assert result['statusCode'] == 200
        assert result['body']['processed'] == 0
        assert result['body']['skipped'] == 1
        assert result['body']['errors'] == 0


@mock_aws
def test_ingest_partial_failure_continues_processing(lambda_context, lambda_env):
    """Test that failures on individual countries don't stop processing others."""
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

    with patch('features.bond_spreads.handlers.ingest.is_kill_switch_active') as mock_kill_switch, \
         patch('features.bond_spreads.handlers.ingest.get_secure_parameter') as mock_ssm, \
         patch('features.bond_spreads.handlers.ingest.COUNTRIES') as mock_countries, \
         patch('features.bond_spreads.handlers.ingest.get_target_period') as mock_period:

        mock_kill_switch.return_value = False
        mock_ssm.return_value = "test-api-key"
        mock_period.return_value = "2026-01"

        # Two countries - one will fail, one will succeed
        mock_countries.__iter__ = lambda self: iter([
            CountryConfig(code="XX", name="Fail", currency="XXX", flag="🏴", series_10y="BAD", series_3m="BAD"),
            CountryConfig(code="US", name="United States", currency="USD", flag="🇺🇸", series_10y="DGS10", series_3m="DTB3")
        ])
        mock_countries.__len__ = lambda self: 2

        with patch.object(FredClient, 'get_series') as mock_get_series, \
             patch.object(FredClient, '_wait_for_rate_limit') as mock_rate_limit:
            # Disable rate limiting
            mock_rate_limit.return_value = None

            # First country fails (returns empty list), second succeeds
            mock_get_series.side_effect = [
                [],  # XX 10Y - fails
                [],  # XX 3M - fails
                [{"date": "2026-01-01", "value": 4.52}],  # US 10Y
                [{"date": "2026-01-01", "value": 2.66}]   # US 3M
            ]

            result = handler({}, lambda_context)

            # One should fail, one should succeed
            assert result['statusCode'] == 200
            assert result['body']['processed'] == 1
            assert result['body']['errors'] == 1


@mock_aws
def test_ingest_uses_bs_prefix_in_dynamodb(lambda_context, lambda_env, mock_fred_data):
    """Test that DynamoDB items use BS# prefix correctly."""
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

    with patch('features.bond_spreads.handlers.ingest.is_kill_switch_active') as mock_kill_switch, \
         patch('features.bond_spreads.handlers.ingest.get_secure_parameter') as mock_ssm, \
         patch('features.bond_spreads.handlers.ingest.COUNTRIES') as mock_countries, \
         patch('features.bond_spreads.handlers.ingest.get_target_period') as mock_period:

        mock_kill_switch.return_value = False
        mock_ssm.return_value = "test-api-key"
        mock_period.return_value = "2026-01"

        mock_countries.__iter__ = lambda self: iter([
            CountryConfig(code="DE", name="Germany", currency="EUR", flag="🇩🇪", series_10y="TEST10", series_3m="TEST3M")
        ])
        mock_countries.__len__ = lambda self: 1

        with patch.object(FredClient, 'get_series') as mock_get_series, \
             patch.object(FredClient, '_wait_for_rate_limit') as mock_rate_limit:
            # Disable rate limiting
            mock_rate_limit.return_value = None
            # Mock FRED responses
            mock_get_series.return_value = [
                {"date": "2026-01-01", "value": 4.52},
                {"date": "2026-01-15", "value": 4.55}
            ]

            result = handler({}, lambda_context)

            # Verify BS# prefix in DynamoDB
            response = table.get_item(Key={'pk': 'BS#COUNTRY#DE', 'sk': '2026-01'})
            assert 'Item' in response
            assert response['Item']['pk'] == 'BS#COUNTRY#DE'
            assert response['Item']['gsi1pk'] == 'BS#PERIOD#2026-01'

            # Verify metadata uses BS# prefix
            meta_response = table.get_item(Key={'pk': 'BS#META', 'sk': 'LAST_INGEST'})
            assert 'Item' in meta_response
            assert meta_response['Item']['pk'] == 'BS#META'
