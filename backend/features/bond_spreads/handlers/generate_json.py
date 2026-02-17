"""Generate JSON files from existing DynamoDB data - no data fetching."""

import os
from aws_lambda_powertools import Logger
from features.bond_spreads.services.config import COUNTRIES, S3_DATA_PREFIX
from features.bond_spreads.handlers.common import create_services

logger = Logger()

def handler(event, context):
    """Generate JSON files from existing DynamoDB data."""
    table_name = os.environ["TABLE_NAME"]
    bucket_name = os.environ["BUCKET_NAME"]
    distribution_id = os.environ["DISTRIBUTION_ID"]
    logger.info("Generating JSON files from DynamoDB")

    _, s3_publisher, _, _, json_generator = create_services(
        table_name=table_name,
        bucket_name=bucket_name,
        distribution_id=distribution_id,
        api_key="dummy"  # Not needed for JSON generation
    )

    # Generate all 3 JSON files
    s3_publisher.publish_json(
        f"{S3_DATA_PREFIX}/spreads-latest.json",
        json_generator.generate_latest()
    )
    s3_publisher.publish_json(
        f"{S3_DATA_PREFIX}/spreads-history.json",
        json_generator.generate_history(countries=COUNTRIES)
    )
    s3_publisher.publish_json(
        f"{S3_DATA_PREFIX}/spreads-summary.json",
        json_generator.generate_summary()
    )

    # Invalidate CloudFront
    s3_publisher.invalidate_paths([f"/{S3_DATA_PREFIX}/*"])

    logger.info("JSON files generated successfully")

    return {"statusCode": 200, "body": "JSON files generated"}
