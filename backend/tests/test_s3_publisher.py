"""Tests for S3Publisher."""

import pytest
import boto3
import json
from moto import mock_aws
from shared.s3_publisher import S3Publisher


@pytest.fixture
def s3_setup(aws_credentials):
    """Set up mock S3 and CloudFront."""
    with mock_aws():
        # Create bucket
        s3 = boto3.client('s3', region_name='eu-central-1')
        s3.create_bucket(
            Bucket='test-bucket',
            CreateBucketConfiguration={'LocationConstraint': 'eu-central-1'}
        )

        # Create distribution
        cf = boto3.client('cloudfront', region_name='eu-central-1')
        response = cf.create_distribution(
            DistributionConfig={
                'CallerReference': 'test-ref',
                'Comment': 'Test distribution',
                'Enabled': True,
                'Origins': {
                    'Quantity': 1,
                    'Items': [
                        {
                            'Id': 'test-origin',
                            'DomainName': 'test-bucket.s3.amazonaws.com',
                            'S3OriginConfig': {'OriginAccessIdentity': ''}
                        }
                    ]
                },
                'DefaultCacheBehavior': {
                    'TargetOriginId': 'test-origin',
                    'ViewerProtocolPolicy': 'allow-all',
                    'TrustedSigners': {'Enabled': False, 'Quantity': 0},
                    'ForwardedValues': {
                        'QueryString': False,
                        'Cookies': {'Forward': 'none'}
                    },
                    'MinTTL': 0
                }
            }
        )

        dist_id = response['Distribution']['Id']
        yield 'test-bucket', dist_id


def test_publish_json(s3_setup):
    """Test publish_json uploads with correct headers."""
    bucket, dist_id = s3_setup
    publisher = S3Publisher(bucket, dist_id)

    data = {'test': 'value', 'number': 42}
    publisher.publish_json('data/test.json', data)

    # Verify upload
    s3 = boto3.client('s3', region_name='eu-central-1')
    response = s3.get_object(Bucket=bucket, Key='data/test.json')

    assert response['ContentType'] == 'application/json'
    assert 'max-age=2592000' in response['CacheControl']

    body = json.loads(response['Body'].read())
    assert body == data


def test_invalidate_paths(s3_setup):
    """Test invalidate_paths creates CloudFront invalidation."""
    bucket, dist_id = s3_setup
    publisher = S3Publisher(bucket, dist_id)

    publisher.invalidate_paths(['/data/*', '/index.html'])

    # Verify invalidation was created
    cf = boto3.client('cloudfront', region_name='eu-central-1')
    response = cf.list_invalidations(DistributionId=dist_id)

    assert response['InvalidationList']['Quantity'] > 0
