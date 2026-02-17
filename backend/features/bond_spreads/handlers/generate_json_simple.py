"""Generate JSON files from existing DynamoDB data - simplified version."""

import os
from datetime import datetime
from aws_lambda_powertools import Logger
from features.bond_spreads.services.config import COUNTRIES, S3_DATA_PREFIX
from shared.dynamo_service import DynamoService
from shared.s3_publisher import S3Publisher
from features.bond_spreads.models.types import SpreadRecord

logger = Logger()

def handler(event, context):
    """Generate JSON files from existing DynamoDB data."""
    table_name = os.environ["TABLE_NAME"]
    bucket_name = os.environ["BUCKET_NAME"]
    distribution_id = os.environ["DISTRIBUTION_ID"]

    logger.info("Generating JSON files from DynamoDB")

    dynamo = DynamoService(table_name)
    s3 = S3Publisher(bucket_name, distribution_id)

    # Get latest period by querying US data
    us_data = dynamo.query_by_pk(pk="BS#COUNTRY#US", ascending=False, limit=1)
    if not us_data:
        return {"statusCode": 404, "body": "No data found"}

    latest_period = us_data[0]["SK"]
    logger.info(f"Latest period: {latest_period}")

    # Generate spreads-latest.json (each country's latest available data)
    latest_countries = []
    for country in COUNTRIES:
        pk = f"BS#COUNTRY#{country.code}"
        # Get the most recent record for this country, regardless of period
        items = dynamo.query_by_pk(pk=pk, ascending=False, limit=1)
        if items:
            record = SpreadRecord.from_dynamo_item(items[0])
            latest_countries.append({
                'code': record.country_code,
                'name': record.country_name,
                'currency': record.currency,
                'flag': record.flag,
                'yield_10y': record.yield_10y,
                'yield_3m': record.yield_3m,
                'spread_pct': record.spread_pct,
                'spread_bps': record.spread_bps,
                'is_inverted': record.is_inverted
            })

    latest_json = {
        'period': latest_period,
        'updated_at': datetime.utcnow().isoformat() + 'Z',
        'countries': sorted(latest_countries, key=lambda x: x['spread_bps'], reverse=True)
    }

    s3.publish_json(f"{S3_DATA_PREFIX}/spreads-latest.json", latest_json)
    logger.info("✓ spreads-latest.json")

    # Generate spreads-history.json (last 120 periods for each country)
    history_data = {}
    for country in COUNTRIES:
        pk = f"BS#COUNTRY#{country.code}"
        items = dynamo.query_by_pk(pk=pk, ascending=False, limit=120)
        history_data[country.code] = [
            {
                'period': item['SK'],
                'spread_bps': int(item.get('spread_bps', 0))
            }
            for item in items
        ]

    history_json = {
        'updated_at': datetime.utcnow().isoformat() + 'Z',
        'countries': history_data
    }

    s3.publish_json(f"{S3_DATA_PREFIX}/spreads-history.json", history_json)
    logger.info("✓ spreads-history.json")

    # Generate spreads-summary.json
    summary_json = {
        'period': latest_period,
        'updated_at': datetime.utcnow().isoformat() + 'Z',
        'total_countries': len(latest_countries),
        'inverted_count': sum(1 for c in latest_countries if c['is_inverted']),
        'avg_spread_bps': sum(c['spread_bps'] for c in latest_countries) / len(latest_countries) if latest_countries else 0
    }

    s3.publish_json(f"{S3_DATA_PREFIX}/spreads-summary.json", summary_json)
    logger.info("✓ spreads-summary.json")

    # Invalidate CloudFront
    s3.invalidate_paths([f"/{S3_DATA_PREFIX}/*"])
    logger.info("✓ CloudFront invalidated")

    return {"statusCode": 200, "body": "JSON files generated successfully"}
