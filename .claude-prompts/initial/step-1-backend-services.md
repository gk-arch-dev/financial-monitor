# Step 1: Backend Services — Shared + Bond Spreads Feature

## Context
This is step 1 of **Financial Monitor**. Step 0 deployed CDK infrastructure with a shared core (DynamoDB, S3, CloudFront, monitoring) and a bond-spreads feature stack (Lambdas, EventBridge).

We now build the backend: shared services used by all features, plus the bond-spreads feature module.

## Task

Build shared services in `backend/shared/`, bond-spreads feature services in `backend/features/bond_spreads/`, and comprehensive unit tests. Do NOT modify Lambda handlers yet (step 2).

## File Structure

```
backend/
├── shared/                             # Used by ALL features
│   ├── __init__.py
│   ├── dynamo_service.py               # Generic DynamoDB CRUD
│   ├── s3_publisher.py                 # S3 upload + CloudFront invalidation
│   ├── ssm_utils.py                    # SSM reads, kill switch check
│   └── models.py                       # Base dataclasses
├── features/
│   └── bond_spreads/                   # BOND SPREADS feature
│       ├── __init__.py
│       ├── handlers/                   # DON'T TOUCH — step 2
│       │   ├── __init__.py
│       │   ├── ingest.py
│       │   └── backfill.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── config.py               # Country/series ID config
│       │   ├── fred_client.py           # FRED API client
│       │   ├── spread_calculator.py     # Spread calculation logic
│       │   └── json_generator.py        # Generates bond-spread JSON files
│       ├── models/
│       │   ├── __init__.py
│       │   └── types.py                # Bond-spread specific types
│       └── tests/
│           ├── __init__.py
│           ├── conftest.py
│           ├── test_config.py
│           ├── test_fred_client.py
│           ├── test_spread_calculator.py
│           └── test_json_generator.py
├── tests/                              # Shared service tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_dynamo_service.py
│   └── test_s3_publisher.py
└── requirements.txt
```

## Shared Services (`backend/shared/`)

These are generic, feature-agnostic utilities reused across all features.

### `shared/models.py` — Base Types

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class DynamoRecord:
    """Base record for any DynamoDB item"""
    pk: str
    sk: str
    gsi1pk: str | None = None
    gsi1sk: float | int | None = None
    data: dict[str, Any] = None  # additional attributes
```

### `shared/dynamo_service.py` — Generic DynamoDB Operations

Feature-agnostic. Works with any PK/SK prefix pattern.

```python
class DynamoService:
    def __init__(self, table_name: str, region: str = "eu-central-1"):
        """Creates boto3 DynamoDB Table resource"""

    def put_item(self, pk: str, sk: str, attributes: dict,
                 gsi1pk: str = None, gsi1sk: float | int = None) -> None:
        """Generic put with optional GSI keys"""

    def batch_put_items(self, items: list[dict]) -> None:
        """Batch write with 25-item chunks"""

    def query_by_pk(self, pk: str, sk_begins_with: str = None,
                    sk_between: tuple[str, str] = None,
                    limit: int = None, ascending: bool = True) -> list[dict]:
        """Query by partition key with optional SK conditions"""

    def query_gsi1(self, gsi1pk: str, ascending: bool = False,
                   limit: int = None) -> list[dict]:
        """Query GSI1 by GSI1PK, optionally sorted"""

    def get_item(self, pk: str, sk: str) -> dict | None:
        """Get single item"""

    def item_exists(self, pk: str, sk: str) -> bool:
        """Check existence without fetching full item"""

    def has_items_with_prefix(self, pk_prefix: str) -> bool:
        """Scan with limit=1 to check if any items with this PK prefix exist.
        Used to check if a feature has been backfilled."""

    def delete_item(self, pk: str, sk: str) -> None:
        """Delete single item"""
```

### `shared/s3_publisher.py` — S3 Upload + CloudFront

```python
class S3Publisher:
    def __init__(self, bucket_name: str, distribution_id: str, region: str = "eu-central-1"):
        pass

    def publish_json(self, key: str, data: dict) -> None:
        """
        Upload JSON to S3.
        ContentType: application/json
        CacheControl: public, max-age=2592000, s-maxage=2592000
        Key example: "data/bond-spreads/spreads-latest.json"
        """

    def invalidate_paths(self, paths: list[str]) -> None:
        """Create CloudFront invalidation for given paths.
        Example: ["/data/bond-spreads/*"]
        """
```

### `shared/ssm_utils.py`

```python
def get_parameter(name: str, region: str = "eu-central-1") -> str:
    """Read SSM parameter"""

def get_secure_parameter(name: str, region: str = "eu-central-1") -> str:
    """Read SSM SecureString (decrypted)"""

def is_kill_switch_active(ssm_prefix: str, region: str = "eu-central-1") -> bool:
    """Check /fm/{stage}/kill-switch"""
```

## Bond Spreads Feature (`backend/features/bond_spreads/`)

### `models/types.py`

```python
@dataclass
class CountryConfig:
    code: str           # "US"
    name: str           # "United States"
    currency: str       # "USD"
    flag: str           # "🇺🇸"
    series_10y: str     # FRED series ID
    series_3m: str      # FRED series ID

@dataclass
class SpreadRecord:
    country_code: str
    country_name: str
    currency: str
    flag: str
    period: str         # "2025-01"
    yield_10y: float
    yield_3m: float
    spread: float       # percentage
    spread_bps: int     # basis points
    updated_at: str     # ISO 8601

    def to_dynamo_item(self) -> dict:
        """Convert to DynamoDB put_item kwargs.
        PK: BS#COUNTRY#{code}, SK: {period}
        GSI1PK: BS#PERIOD#{period}, GSI1SK: {spread_bps}
        """

    @classmethod
    def from_dynamo_item(cls, item: dict) -> 'SpreadRecord':
        """Parse DynamoDB item back to SpreadRecord"""
```

### `services/config.py` — Country Configuration

**CRITICAL: Research and verify correct FRED series IDs.**

Known patterns:
- Long-term 10Y: `IRLTLT01{CC}M156N` (OECD country code)
- Short-term 3M: `IR3TIB01{CC}M156N` or `IRSTCI01{CC}M156N`
- USA: `GS10` + `TB3MS`

Target countries: US, GB, DE, JP, FR, CA, AU, BR, IN, MX, KR, IT

```python
# Prefix used in DynamoDB for this feature
DYNAMO_PK_PREFIX = "BS"

# S3 data path for this feature
S3_DATA_PREFIX = "data/bond-spreads"

COUNTRIES: list[CountryConfig] = [
    CountryConfig(code="US", name="United States", currency="USD", flag="🇺🇸",
                  series_10y="GS10", series_3m="TB3MS"),
    # ... research and add all countries
]
```

### `services/fred_client.py` — FRED API Client

```python
class FredClient:
    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self, api_key: str, rate_limit: int = 120):
        pass

    def get_series(self, series_id: str, start_date: str, end_date: str,
                   frequency: str = "m") -> list[dict]:
        """Returns [{"date": "2025-01-01", "value": "4.52"}, ...]
        Handles "." as missing value. Parses values to float."""

    def validate_series(self, series_id: str) -> bool:
        """Check if series exists and has data"""
```

### `services/spread_calculator.py` — Pure Logic

```python
class SpreadCalculator:
    @staticmethod
    def calculate_spread(yield_10y: float, yield_3m: float) -> tuple[float, int]:
        """Returns (spread_pct, spread_bps)"""

    @staticmethod
    def calculate_changes(current_bps: int, history: list[SpreadRecord]) -> tuple[int|None, int|None, int|None]:
        """Returns (change_1m, change_3m, change_6m) in bps"""

    @staticmethod
    def is_inverted(spread: float) -> bool:
        pass

    @staticmethod
    def calculate_inversion_streak(history: list[SpreadRecord]) -> tuple[str|None, int|None]:
        """Returns (inverted_since_period, approx_days)"""
```

### `services/json_generator.py` — Generate Feature JSON

```python
class BondSpreadJsonGenerator:
    def __init__(self, dynamo_service: DynamoService, spread_calculator: SpreadCalculator):
        pass

    def generate_latest(self, period: str) -> dict:
        """Generates data/bond-spreads/spreads-latest.json"""

    def generate_history(self, countries: list[CountryConfig]) -> dict:
        """Generates data/bond-spreads/spreads-history.json"""

    def generate_summary(self, period: str) -> dict:
        """Generates data/bond-spreads/spreads-summary.json"""
```

Uses `BS#PERIOD#` and `BS#COUNTRY#` prefixes when querying DynamoDB.

Output JSON schemas — same as in the original spec. Key change: files go to `data/bond-spreads/` path on S3.

## Unit Tests

### Shared tests (`backend/tests/`)

**`test_dynamo_service.py`** (moto):
- put_item + query_by_pk roundtrip
- batch_put_items writes all items
- query_gsi1 returns correct results
- has_items_with_prefix true/false
- item_exists true/false
- get_item returns None for missing

**`test_s3_publisher.py`** (moto):
- publish_json uploads with correct content type and cache headers
- invalidate_paths creates CloudFront invalidation

### Feature tests (`backend/features/bond_spreads/tests/`)

**`conftest.py`**: fixtures for moto DynamoDB table, sample SpreadRecords, mock FRED responses

**`test_config.py`**: all countries have required fields, no duplicates, codes are 2 chars, flags are emoji

**`test_fred_client.py`**: successful parse, missing "." values filtered, API errors, empty responses, rate limiting

**`test_spread_calculator.py`**: positive/negative/zero spreads, change calculations, inversion detection, inversion streak

**`test_json_generator.py`**: correct JSON structure for all 3 files, sorting, summary calculations

## Implementation Rules

- **SOLID**: each service one responsibility
- **Dependency injection**: services receive dependencies in `__init__`
- **Shared vs feature**: if it's reusable across features → `shared/`. If it's bond-spread specific → `features/bond_spreads/`
- **DynamoDB prefix**: all bond spread operations use `BS#` prefix via config constant
- **Structured JSON logging**
- **Type hints on all signatures**
- **No hardcoded AWS resource names**

## requirements.txt
```
boto3>=1.34.0
requests>=2.31.0
pytest>=8.0.0
moto[dynamodb,s3]>=5.0.0
pytest-mock>=3.12.0
```

Run: `cd backend && python -m pytest tests/ features/bond_spreads/tests/ -v`
