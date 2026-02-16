"""Monthly data ingestion handler for Bond Spreads.

This Lambda is triggered monthly by EventBridge to fetch the latest
government bond yield data and update DynamoDB + S3 JSON files.
"""

import os
from datetime import datetime
from aws_lambda_powertools import Logger

from shared.ssm_utils import get_secure_parameter, is_kill_switch_active
from features.bond_spreads.services.config import COUNTRIES, S3_DATA_PREFIX
from features.bond_spreads.models.types import SpreadRecord
from features.bond_spreads.handlers.common import create_services, get_target_period

logger = Logger(service="bond-spreads")


def handler(event, context):
    """Lambda handler for monthly data ingestion.

    Args:
        event: Lambda event payload (from EventBridge)
        context: Lambda context object

    Returns:
        Response dict with status
    """
    # Environment variables set by CDK
    stage = os.environ.get("STAGE", "box")
    table_name = os.environ["TABLE_NAME"]
    bucket_name = os.environ["BUCKET_NAME"]
    distribution_id = os.environ["DISTRIBUTION_ID"]
    ssm_prefix = os.environ["SSM_PREFIX"]
    region = os.environ.get("AWS_REGION", "eu-central-1")

    logger.info("Starting monthly bond spreads ingestion", extra={
        "feature": "bond-spreads",
        "stage": stage
    })

    # 1. Check kill switch
    if is_kill_switch_active(ssm_prefix, region):
        logger.warning("Kill switch is active, aborting ingestion", extra={
            "feature": "bond-spreads"
        })
        return {
            "statusCode": 200,
            "body": "Kill switch active - skipped"
        }

    # 2. Read FRED API key from SSM
    api_key_param = f"{ssm_prefix}/features/bond-spreads/fred-api-key"
    try:
        api_key = get_secure_parameter(api_key_param, region)
    except Exception as e:
        logger.error("Failed to retrieve FRED API key from SSM", extra={
            "feature": "bond-spreads",
            "parameter": api_key_param,
            "error": str(e)
        })
        raise

    # 3. Initialize services
    dynamo_service, s3_publisher, fred_client, spread_calculator, json_generator = create_services(
        table_name=table_name,
        bucket_name=bucket_name,
        distribution_id=distribution_id,
        api_key=api_key,
        region=region
    )

    # 4. Determine target period (previous month)
    target_period = get_target_period()
    logger.info("Target period determined", extra={
        "feature": "bond-spreads",
        "period": target_period
    })

    # 5. Process each country
    processed = 0
    skipped = 0
    errors = 0

    for country in COUNTRIES:
        country_pk = f"BS#COUNTRY#{country.code}"

        # 5a. Skip if record exists (idempotent)
        if dynamo_service.item_exists(pk=country_pk, sk=target_period):
            logger.info("Record already exists, skipping", extra={
                "feature": "bond-spreads",
                "country": country.code,
                "period": target_period
            })
            skipped += 1
            continue

        try:
            # 5b. Fetch 10Y + 3M from FRED
            logger.debug("Fetching FRED data", extra={
                "feature": "bond-spreads",
                "country": country.code,
                "series_10y": country.series_10y,
                "series_3m": country.series_3m
            })

            # Get data for the target month (first and last day of month)
            start_date = f"{target_period}-01"
            # Simple approach: use start of next month as end date
            year, month = map(int, target_period.split('-'))
            next_month = month + 1 if month < 12 else 1
            next_year = year if month < 12 else year + 1
            end_date = f"{next_year:04d}-{next_month:02d}-01"

            data_10y = fred_client.get_series(
                series_id=country.series_10y,
                start_date=start_date,
                end_date=end_date,
                frequency="m"
            )
            data_3m = fred_client.get_series(
                series_id=country.series_3m,
                start_date=start_date,
                end_date=end_date,
                frequency="m"
            )

            # 5c. If no data → log error, skip country
            if not data_10y or not data_3m:
                logger.error("No FRED data available", extra={
                    "feature": "bond-spreads",
                    "country": country.code,
                    "period": target_period,
                    "has_10y": bool(data_10y),
                    "has_3m": bool(data_3m)
                })
                errors += 1
                continue

            # Get the latest value from the month
            yield_10y = float(data_10y[-1]["value"])
            yield_3m = float(data_3m[-1]["value"])

            # 5d. Calculate spread and save to DynamoDB
            spread_pct, spread_bps = spread_calculator.calculate_spread(yield_10y, yield_3m)
            is_inverted = spread_calculator.is_inverted(spread_pct)

            record = SpreadRecord(
                country_code=country.code,
                country_name=country.name,
                currency=country.currency,
                flag=country.flag,
                period=target_period,
                yield_10y=yield_10y,
                yield_3m=yield_3m,
                spread_pct=spread_pct,
                spread_bps=spread_bps,
                is_inverted=is_inverted,
                updated_at=datetime.utcnow().isoformat() + "Z"
            )

            # Save to DynamoDB
            dynamo_service.table.put_item(Item=record.to_dynamo_item())

            logger.info("Saved spread record", extra={
                "feature": "bond-spreads",
                "country": country.code,
                "period": target_period,
                "spread_bps": spread_bps,
                "is_inverted": is_inverted
            })

            processed += 1

        except Exception as e:
            logger.error("Failed to process country", extra={
                "feature": "bond-spreads",
                "country": country.code,
                "period": target_period,
                "error": str(e)
            }, exc_info=True)
            errors += 1
            # Continue with other countries

    # 6. Generate all 3 JSON files and upload to S3
    try:
        logger.info("Generating JSON files", extra={
            "feature": "bond-spreads",
            "period": target_period
        })

        # Generate latest spreads
        latest_data = json_generator.generate_latest(period=target_period)
        s3_publisher.publish_json(
            key=f"{S3_DATA_PREFIX}/spreads-latest.json",
            data=latest_data
        )

        # Generate history
        history_data = json_generator.generate_history(countries=COUNTRIES)
        s3_publisher.publish_json(
            key=f"{S3_DATA_PREFIX}/spreads-history.json",
            data=history_data
        )

        # Generate summary
        summary_data = json_generator.generate_summary(period=target_period)
        s3_publisher.publish_json(
            key=f"{S3_DATA_PREFIX}/spreads-summary.json",
            data=summary_data
        )

        logger.info("JSON files uploaded to S3", extra={
            "feature": "bond-spreads",
            "bucket": bucket_name,
            "prefix": S3_DATA_PREFIX
        })

    except Exception as e:
        logger.error("Failed to generate/upload JSON files", extra={
            "feature": "bond-spreads",
            "error": str(e)
        }, exc_info=True)
        raise

    # 7. Invalidate CloudFront
    try:
        s3_publisher.invalidate_paths([f"/{S3_DATA_PREFIX}/*"])
        logger.info("CloudFront invalidation created", extra={
            "feature": "bond-spreads",
            "distribution_id": distribution_id
        })
    except Exception as e:
        logger.error("Failed to invalidate CloudFront", extra={
            "feature": "bond-spreads",
            "error": str(e)
        }, exc_info=True)
        # Don't raise - invalidation is not critical

    # 8. Update metadata
    try:
        dynamo_service.put_item(
            pk="BS#META",
            sk="LAST_INGEST",
            attributes={
                "period": target_period,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "processed": processed,
                "skipped": skipped,
                "errors": errors
            }
        )
    except Exception as e:
        logger.error("Failed to update metadata", extra={
            "feature": "bond-spreads",
            "error": str(e)
        }, exc_info=True)
        # Don't raise - metadata is not critical

    # 9. Log summary
    logger.info("Monthly ingestion completed", extra={
        "feature": "bond-spreads",
        "period": target_period,
        "processed": processed,
        "skipped": skipped,
        "errors": errors,
        "total_countries": len(COUNTRIES)
    })

    return {
        "statusCode": 200,
        "body": {
            "period": target_period,
            "processed": processed,
            "skipped": skipped,
            "errors": errors
        }
    }
