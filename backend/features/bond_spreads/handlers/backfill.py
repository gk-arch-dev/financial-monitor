"""Historical data backfill handler for Bond Spreads.

This Lambda is triggered once on first deployment via CDK Custom Resource
to populate historical bond spread data.

Idempotent: skips countries that already have data.
"""

import os
import json
import urllib3
from datetime import datetime
from dateutil.relativedelta import relativedelta
from aws_lambda_powertools import Logger

from shared.ssm_utils import get_secure_parameter
from features.bond_spreads.services.config import COUNTRIES, S3_DATA_PREFIX
from features.bond_spreads.models.types import SpreadRecord
from features.bond_spreads.handlers.common import create_services

logger = Logger(service="bond-spreads-backfill")
http = urllib3.PoolManager()


def send_cfn_response(event, context, status, data=None, physical_resource_id=None, reason=None):
    """Send CloudFormation custom resource response.

    Args:
        event: Lambda event from CloudFormation
        context: Lambda context
        status: "SUCCESS" or "FAILED"
        data: Optional response data dict
        physical_resource_id: Optional physical resource ID
        reason: Optional failure reason
    """
    response_url = event.get("ResponseURL")
    if not response_url:
        logger.warning("No ResponseURL in event, skipping CFN response")
        return

    response_body = {
        "Status": status,
        "Reason": reason or f"See CloudWatch Log Stream: {context.log_stream_name}",
        "PhysicalResourceId": physical_resource_id or context.log_stream_name,
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "Data": data or {}
    }

    json_response = json.dumps(response_body)
    headers = {
        "Content-Type": "",
        "Content-Length": str(len(json_response))
    }

    try:
        http.request(
            "PUT",
            response_url,
            body=json_response.encode("utf-8"),
            headers=headers
        )
        logger.info("CFN response sent", extra={
            "feature": "bond-spreads",
            "status": status
        })
    except Exception as e:
        logger.error("Failed to send CFN response", extra={
            "feature": "bond-spreads",
            "error": str(e)
        }, exc_info=True)


def handler(event, context):
    """Lambda handler for historical data backfill.

    Args:
        event: Lambda event payload (from CDK Custom Resource)
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

    request_type = event.get("RequestType", "Create")
    logger.info("Backfill handler invoked", extra={
        "feature": "bond-spreads",
        "stage": stage,
        "request_type": request_type
    })

    # Handle Delete/Update - just send success
    if request_type in ["Delete", "Update"]:
        logger.info("Delete/Update request - nothing to do", extra={
            "feature": "bond-spreads",
            "request_type": request_type
        })
        send_cfn_response(event, context, "SUCCESS", data={"Message": "No action needed"})
        return {"statusCode": 200, "body": "No action needed"}

    try:
        # Read FRED API key first to fail fast if missing
        api_key_param = f"{ssm_prefix}/features/bond-spreads/fred-api-key"
        try:
            api_key = get_secure_parameter(api_key_param, region)
        except Exception as e:
            logger.error("Failed to retrieve FRED API key from SSM", extra={
                "feature": "bond-spreads",
                "parameter": api_key_param,
                "error": str(e)
            })
            send_cfn_response(event, context, "FAILED", reason=f"Failed to get FRED API key: {str(e)}")
            raise

        # Initialize services
        dynamo_service, s3_publisher, fred_client, spread_calculator, json_generator = create_services(
            table_name=table_name,
            bucket_name=bucket_name,
            distribution_id=distribution_id,
            api_key=api_key,
            region=region
        )

        # 1. Check if data already exists for ALL countries
        # Check if at least one country has data (to avoid full re-backfill if partially complete)
        all_countries_loaded = all(
            dynamo_service.has_items_with_prefix(f"BS#COUNTRY#{country.code}")
            for country in COUNTRIES
        )
        if all_countries_loaded:
            logger.info("Bond spread data already exists for all countries, skipping backfill", extra={
                "feature": "bond-spreads",
                "country_count": len(COUNTRIES)
            })
            send_cfn_response(event, context, "SUCCESS", data={
                "Message": "Data already exists for all countries",
                "Skipped": True
            })
            return {
                "statusCode": 200,
                "body": "Data already exists - skipped"
            }

        # Calculate date range: 10 years of historical data
        end_date = datetime.utcnow()
        start_date = end_date - relativedelta(years=10)

        logger.info("Starting historical backfill", extra={
            "feature": "bond-spreads",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "countries": len(COUNTRIES)
        })

        total_records = 0
        failed_countries = []

        # 3. Process each country
        for country in COUNTRIES:
            try:
                logger.info("Processing country", extra={
                    "feature": "bond-spreads",
                    "country": country.code
                })

                # 3a. Check if this country already has data (idempotent check)
                if dynamo_service.has_items_with_prefix(f"BS#COUNTRY#{country.code}"):
                    logger.info("Country data already exists, skipping", extra={
                        "feature": "bond-spreads",
                        "country": country.code
                    })
                    continue

                # 3c. Validate series IDs
                if not fred_client.validate_series(country.series_10y):
                    logger.error("Invalid 10Y series", extra={
                        "feature": "bond-spreads",
                        "country": country.code,
                        "series": country.series_10y
                    })
                    failed_countries.append(country.code)
                    continue

                if not fred_client.validate_series(country.series_3m):
                    logger.error("Invalid 3M series", extra={
                        "feature": "bond-spreads",
                        "country": country.code,
                        "series": country.series_3m
                    })
                    failed_countries.append(country.code)
                    continue

                # 3d. Fetch 10 years of monthly data
                data_10y = fred_client.get_series(
                    series_id=country.series_10y,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    frequency="m"
                )

                data_3m = fred_client.get_series(
                    series_id=country.series_3m,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    frequency="m"
                )

                if not data_10y or not data_3m:
                    logger.error("No historical data available", extra={
                        "feature": "bond-spreads",
                        "country": country.code,
                        "has_10y": bool(data_10y),
                        "has_3m": bool(data_3m)
                    })
                    failed_countries.append(country.code)
                    continue

                # 3e. Calculate spreads and prepare batch items
                # Create lookup dict for 3M data by period
                data_3m_dict = {}
                for entry in data_3m:
                    period = entry["date"][:7]  # Extract YYYY-MM
                    data_3m_dict[period] = float(entry["value"])

                records = []
                for entry_10y in data_10y:
                    period = entry_10y["date"][:7]  # Extract YYYY-MM

                    # Skip if no matching 3M data for this period
                    if period not in data_3m_dict:
                        continue

                    yield_10y = float(entry_10y["value"])
                    yield_3m = data_3m_dict[period]

                    # Calculate spread
                    spread_pct, spread_bps = spread_calculator.calculate_spread(yield_10y, yield_3m)
                    is_inverted = spread_calculator.is_inverted(spread_pct)

                    record = SpreadRecord(
                        country_code=country.code,
                        country_name=country.name,
                        currency=country.currency,
                        flag=country.flag,
                        period=period,
                        yield_10y=yield_10y,
                        yield_3m=yield_3m,
                        spread_pct=spread_pct,
                        spread_bps=spread_bps,
                        is_inverted=is_inverted,
                        updated_at=datetime.utcnow().isoformat() + "Z"
                    )

                    records.append(record.to_dynamo_item())

                # Batch write to DynamoDB
                if records:
                    dynamo_service.batch_put_items(records)
                    total_records += len(records)
                    logger.info("Saved historical records", extra={
                        "feature": "bond-spreads",
                        "country": country.code,
                        "record_count": len(records)
                    })

            except Exception as e:
                logger.error("Failed to process country during backfill", extra={
                    "feature": "bond-spreads",
                    "country": country.code,
                    "error": str(e)
                }, exc_info=True)
                failed_countries.append(country.code)
                # Continue with other countries

        # 4. Generate JSON files and upload to S3
        try:
            logger.info("Generating JSON files after backfill", extra={
                "feature": "bond-spreads"
            })

            # Get the latest period from the data
            latest_period = end_date.strftime("%Y-%m")

            # Generate latest spreads
            latest_data = json_generator.generate_latest(period=latest_period)
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
            summary_data = json_generator.generate_summary(period=latest_period)
            s3_publisher.publish_json(
                key=f"{S3_DATA_PREFIX}/spreads-summary.json",
                data=summary_data
            )

            logger.info("JSON files uploaded after backfill", extra={
                "feature": "bond-spreads",
                "bucket": bucket_name,
                "prefix": S3_DATA_PREFIX
            })

            # Invalidate CloudFront
            try:
                s3_publisher.invalidate_paths([f"/{S3_DATA_PREFIX}/*"])
            except Exception as cf_error:
                logger.error("Failed to invalidate CloudFront after backfill", extra={
                    "feature": "bond-spreads",
                    "error": str(cf_error)
                }, exc_info=True)
                # Don't fail backfill if CloudFront invalidation fails

        except Exception as e:
            logger.error("Failed to generate JSON files after backfill", extra={
                "feature": "bond-spreads",
                "error": str(e)
            }, exc_info=True)
            send_cfn_response(event, context, "FAILED", reason=f"Failed to generate JSON: {str(e)}")
            raise

        # Update metadata
        try:
            dynamo_service.put_item(
                pk="BS#META",
                sk="BACKFILL",
                attributes={
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "total_records": total_records,
                    "failed_countries": failed_countries,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                }
            )
        except Exception as e:
            logger.error("Failed to update backfill metadata", extra={
                "feature": "bond-spreads",
                "error": str(e)
            }, exc_info=True)

        logger.info("Backfill completed", extra={
            "feature": "bond-spreads",
            "total_records": total_records,
            "failed_countries": failed_countries
        })

        # 5. Send CloudFormation success response
        send_cfn_response(event, context, "SUCCESS", data={
            "TotalRecords": total_records,
            "FailedCountries": ",".join(failed_countries) if failed_countries else "None"
        })

        return {
            "statusCode": 200,
            "body": {
                "total_records": total_records,
                "failed_countries": failed_countries
            }
        }

    except Exception as e:
        logger.error("Backfill handler failed", extra={
            "feature": "bond-spreads",
            "error": str(e)
        }, exc_info=True)
        send_cfn_response(event, context, "FAILED", reason=str(e))
        raise
