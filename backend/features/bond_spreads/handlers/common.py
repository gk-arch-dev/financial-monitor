"""Shared utilities for bond spreads Lambda handlers."""

import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from shared.dynamo_service import DynamoService
from shared.s3_publisher import S3Publisher
from features.bond_spreads.services.fred_client import FredClient
from features.bond_spreads.services.spread_calculator import SpreadCalculator
from features.bond_spreads.services.json_generator import BondSpreadJsonGenerator


def create_services(
    table_name: str,
    bucket_name: str,
    distribution_id: str,
    api_key: str
):
    """Factory function to create all required services with proper dependency injection.

    Args:
        table_name: DynamoDB table name
        bucket_name: S3 bucket name
        distribution_id: CloudFront distribution ID
        api_key: FRED API key

    Returns:
        Tuple of (dynamo_service, s3_publisher, fred_client, spread_calculator, json_generator)
    """
    dynamo_service = DynamoService(table_name=table_name)
    s3_publisher = S3Publisher(
        bucket_name=bucket_name,
        distribution_id=distribution_id
    )
    fred_client = FredClient(api_key=api_key)
    spread_calculator = SpreadCalculator()
    json_generator = BondSpreadJsonGenerator(
        dynamo_service=dynamo_service,
        spread_calculator=spread_calculator
    )

    return dynamo_service, s3_publisher, fred_client, spread_calculator, json_generator


def get_target_period() -> str:
    """Returns the target period for data ingestion as 'YYYY-MM'.

    FRED data has approximately 1 month lag, so we target the previous month.
    If running on Feb 1, 2026 → returns '2026-01'

    Returns:
        Period string in format 'YYYY-MM' (e.g., '2026-01')
    """
    # Get current date and subtract one month
    today = datetime.utcnow()
    target_date = today - relativedelta(months=1)

    return target_date.strftime("%Y-%m")
