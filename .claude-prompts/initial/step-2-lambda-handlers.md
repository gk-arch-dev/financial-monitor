# Step 2: Lambda Handlers — Bond Spreads Ingest + Backfill

## Context
This is step 2 of **Financial Monitor**.
- Step 0: CDK infrastructure (shared core + bond-spreads feature stack)
- Step 1: Backend services (shared `dynamo_service`, `s3_publisher`, `ssm_utils` + bond-spreads feature `fred_client`, `spread_calculator`, `json_generator`, `config`)

We now implement the Lambda handler logic for the bond-spreads feature.

## Task

Implement `backend/features/bond_spreads/handlers/ingest.py` and `backfill.py`. Add handler tests.

## Environment Variables (set by CDK)

```
STAGE              = "box" | "pro"
TABLE_NAME         = "fm-box-data"
BUCKET_NAME        = "fm-box-frontend-{accountId}"
DISTRIBUTION_ID    = "E1234ABCDEF"
SSM_PREFIX         = "/fm/box"
FEATURE            = "bond-spreads"
DATA_PREFIX        = "data/bond-spreads"
```

## `handlers/ingest.py` — Monthly Data Ingestion

Triggered by: EventBridge cron (1st of month, 08:00 UTC)

```python
def handler(event, context):
    """
    1. Check kill switch → abort if active
    2. Read FRED API key from SSM: {SSM_PREFIX}/features/bond-spreads/fred-api-key
    3. Initialize services (shared + feature-specific)
    4. Determine target period (previous month — FRED has ~1 month lag)
    5. For each country in config:
       a. Skip if record exists for this period (idempotent)
       b. Fetch 10Y + 3M from FRED
       c. If no data → log error, skip country
       d. Calculate spread → save to DynamoDB (with BS# prefix)
    6. Generate all 3 JSON files → upload to S3 under data/bond-spreads/
    7. Invalidate CloudFront /data/bond-spreads/*
    8. Update BS#META / LAST_INGEST
    9. Log summary
    """
```

Key: uses `BS#` DynamoDB prefix and `data/bond-spreads/` S3 prefix from feature config.

## `handlers/backfill.py` — One-Time Historical Load

Triggered by: CDK Custom Resource on first deploy

```python
def handler(event, context):
    """
    1. Check if DynamoDB has BS# prefixed items → if yes, skip
    2. Read FRED API key from SSM
    3. For each country:
       a. Validate series IDs
       b. Fetch 10 years of data
       c. Calculate spreads, batch write to DynamoDB
    4. Generate JSON files → S3
    5. Return CloudFormation success response
    """
```

## Shared Handler Utilities

Create `backend/features/bond_spreads/handlers/common.py`:

```python
def create_services(table_name, bucket_name, distribution_id, api_key):
    """Factory: creates DynamoService, S3Publisher, FredClient,
    SpreadCalculator, BondSpreadJsonGenerator with proper DI"""

def get_target_period() -> str:
    """Returns previous month as 'YYYY-MM'.
    If running Feb 1 → returns '2026-01'.
    Tries previous month first, falls back to 2 months back if no data."""
```

## Tests

### `tests/test_ingest_handler.py`
- Full success: all countries processed, JSON uploaded to `data/bond-spreads/`
- Kill switch: exits immediately
- Partial failure: remaining countries still processed
- Idempotent: existing records skipped
- DynamoDB items use `BS#COUNTRY#` prefix

### `tests/test_backfill_handler.py`
- Empty table (no `BS#` items): full backfill runs
- Data exists: exits with success
- Writes use `BS#` prefix
- S3 uploads go to `data/bond-spreads/` path

### Test approach
- Mock SSM, mock FredClient, moto for DynamoDB/S3
- Verify DynamoDB PK format: `BS#COUNTRY#US`
- Verify S3 keys: `data/bond-spreads/spreads-latest.json`
- Verify CloudFront invalidation path: `/data/bond-spreads/*`

## Implementation Rules

- **Feature isolation**: handlers only import from `backend/shared/` and `backend/features/bond_spreads/`
- **Structured JSON logging**: include `feature: "bond-spreads"` in every log line
- **Dependency injection**: use factory function, tests inject mocks
- **Error aggregation**: fail per-country, not per-batch

Run: `cd backend && python -m pytest features/bond_spreads/tests/ -v`
