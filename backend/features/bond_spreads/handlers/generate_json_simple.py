"""Generate JSON files from existing DynamoDB data - simplified version."""

import os
import statistics
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

    spread_values = [c['spread_bps'] for c in latest_countries]
    latest_json = {
        'period': latest_period,
        'updated_at': datetime.utcnow().isoformat() + 'Z',
        'countries': sorted(latest_countries, key=lambda x: x['spread_bps'], reverse=True),
        'summary': {
            'avg_spread_bps': int(statistics.mean(spread_values)) if spread_values else 0,
            'median_spread_bps': int(statistics.median(spread_values)) if spread_values else 0,
            'inverted_count': sum(1 for c in latest_countries if c['is_inverted']),
            'total_countries': len(latest_countries)
        }
    }

    s3.publish_json(f"{S3_DATA_PREFIX}/spreads-latest.json", latest_json)
    logger.info("✓ spreads-latest.json")

    # Generate spreads-history.json (last 120 periods for each country)
    history_data = {}
    for country in COUNTRIES:
        pk = f"BS#COUNTRY#{country.code}"
        items = dynamo.query_by_pk(pk=pk, ascending=True, limit=120)
        history_data[country.code] = [
            {
                'period': SpreadRecord.from_dynamo_item(item).period,
                'yield_10y': SpreadRecord.from_dynamo_item(item).yield_10y,
                'yield_3m': SpreadRecord.from_dynamo_item(item).yield_3m,
                'spread_pct': SpreadRecord.from_dynamo_item(item).spread_pct,
                'spread_bps': SpreadRecord.from_dynamo_item(item).spread_bps,
                'is_inverted': SpreadRecord.from_dynamo_item(item).is_inverted,
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
    spread_values_all = [c['spread_bps'] for c in latest_countries]
    non_inverted = [c for c in latest_countries if not c['is_inverted']]
    inversions = [
        {'code': c['code'], 'name': c['name'], 'flag': c['flag'], 'spread_bps': c['spread_bps']}
        for c in latest_countries if c['is_inverted']
    ]
    widest = max(non_inverted, key=lambda c: c['spread_bps']) if non_inverted else None
    narrowest = min(non_inverted, key=lambda c: c['spread_bps']) if non_inverted else None

    # Compute widening/narrowing by comparing latest with previous month
    widening_count = 0
    narrowing_count = 0
    for country in COUNTRIES:
        pk = f"BS#COUNTRY#{country.code}"
        items = dynamo.query_by_pk(pk=pk, ascending=False, limit=2)
        if len(items) >= 2:
            current = SpreadRecord.from_dynamo_item(items[0])
            previous = SpreadRecord.from_dynamo_item(items[1])
            delta = current.spread_bps - previous.spread_bps
            if delta > 0:
                widening_count += 1
            elif delta < 0:
                narrowing_count += 1

    summary_json = {
        'period': latest_period,
        'updated_at': datetime.utcnow().isoformat() + 'Z',
        'avg_spread_bps': int(statistics.mean(spread_values_all)) if spread_values_all else 0,
        'median_spread_bps': int(statistics.median(spread_values_all)) if spread_values_all else 0,
        'widest': {'code': widest['code'], 'name': widest['name'], 'flag': widest['flag'], 'spread_bps': widest['spread_bps']} if widest else None,
        'narrowest': {'code': narrowest['code'], 'name': narrowest['name'], 'flag': narrowest['flag'], 'spread_bps': narrowest['spread_bps']} if narrowest else None,
        'inversions': inversions,
        'widening_count': widening_count,
        'narrowing_count': narrowing_count,
    }

    s3.publish_json(f"{S3_DATA_PREFIX}/spreads-summary.json", summary_json)
    logger.info("✓ spreads-summary.json")

    # Invalidate CloudFront
    s3.invalidate_paths([f"/{S3_DATA_PREFIX}/*"])
    logger.info("✓ CloudFront invalidated")

    return {"statusCode": 200, "body": "JSON files generated successfully"}
