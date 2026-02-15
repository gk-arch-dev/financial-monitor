"""Generic S3 upload and CloudFront invalidation."""


class S3Publisher:
    """Service for publishing JSON files to S3 and invalidating CloudFront cache."""

    def __init__(self, bucket_name: str, distribution_id: str):
        """Initialize S3 publisher.

        Args:
            bucket_name: Name of the S3 bucket
            distribution_id: CloudFront distribution ID for cache invalidation
        """
        pass

    def publish_json(self, key: str, data: dict) -> None:
        """Publish JSON data to S3.

        Args:
            key: S3 object key
            data: Dictionary to serialize as JSON
        """
        pass

    def invalidate_paths(self, paths: list[str]) -> None:
        """Invalidate CloudFront cache for specified paths.

        Args:
            paths: List of paths to invalidate (e.g., ['/data/bond-spreads/*'])
        """
        pass
