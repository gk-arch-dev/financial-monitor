"""Shared test fixtures."""

import pytest
import boto3
from moto import mock_aws


@pytest.fixture
def aws_credentials(monkeypatch):
    """Mock AWS credentials for moto."""
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'eu-central-1')


@pytest.fixture
def dynamodb_table(aws_credentials):
    """Create mock DynamoDB table."""
    with mock_aws():
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

        yield table


@pytest.fixture
def s3_bucket(aws_credentials):
    """Create mock S3 bucket."""
    with mock_aws():
        s3 = boto3.client('s3', region_name='eu-central-1')
        s3.create_bucket(
            Bucket='test-bucket',
            CreateBucketConfiguration={'LocationConstraint': 'eu-central-1'}
        )
        yield 'test-bucket'
