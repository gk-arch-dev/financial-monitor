"""Generic S3 upload and CloudFront invalidation."""

import json
import time
from aws_lambda_powertools import Logger

from shared.aws_config import create_client, get_endpoint_url

logger = Logger()


class S3Publisher:
    """Service for publishing JSON files to S3 and invalidating CloudFront cache."""

    def __init__(self, bucket_name: str, distribution_id: str):
        """Initialize S3 publisher.

        Args:
            bucket_name: Name of the S3 bucket
            distribution_id: CloudFront distribution ID for cache invalidation
        """
        self.s3_client = create_client('s3')
        # CloudFront is not available in LocalStack, skip when using local endpoint
        self.cf_client = None if get_endpoint_url() else create_client('cloudfront')
        self.bucket_name = bucket_name
        self.distribution_id = distribution_id

    def publish_json(self, key: str, data: dict) -> None:
        """Publish JSON data to S3 with proper headers.

        Args:
            key: S3 object key (e.g., 'data/bond-spreads/spreads-latest.json')
            data: Dictionary to serialize as JSON
        """
        logger.info("Publishing JSON to S3", extra={"key": key, "bucket": self.bucket_name})

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json',
            CacheControl='public, max-age=3600, s-maxage=86400'  # browser: 1h, CDN: 24h
        )

    def invalidate_paths(self, paths: list[str]) -> None:
        """Invalidate CloudFront cache for specified paths.

        Args:
            paths: List of paths to invalidate (e.g., ['/data/bond-spreads/*'])
        """
        # Skip CloudFront invalidation in LocalStack (CloudFront not available)
        if self.cf_client is None:
            logger.info("Skipping CloudFront invalidation (LocalStack mode)", extra={"paths": paths})
            return

        caller_reference = f"fm-{int(time.time())}"

        logger.info("Creating CloudFront invalidation", extra={"paths": paths, "distribution": self.distribution_id})

        self.cf_client.create_invalidation(
            DistributionId=self.distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': paths
                },
                'CallerReference': caller_reference
            }
        )
