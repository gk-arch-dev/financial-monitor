"""Type definitions for Bond Spreads feature."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class CountryConfig:
    """Configuration for a country's bond yield series."""
    code: str           # "US"
    name: str           # "United States"
    currency: str       # "USD"
    flag: str           # "🇺🇸"
    series_10y: str     # FRED series ID for 10-year yield
    series_3m: str      # FRED series ID for 3-month yield


@dataclass
class SpreadData:
    """Calculated spread data for a country (intermediate, not stored in DB)."""

    country_code: str
    period: str  # YYYY-MM format
    yield_10y: float
    yield_3m: float
    spread_pct: float
    spread_bps: int
    is_inverted: bool


@dataclass
class SpreadRecord:
    """Full bond spread record for DynamoDB storage."""

    country_code: str
    country_name: str
    currency: str
    flag: str
    period: str         # "2025-01"
    yield_10y: float
    yield_3m: float
    spread_pct: float
    spread_bps: int
    is_inverted: bool
    updated_at: str     # ISO 8601 timestamp

    def to_dynamo_item(self) -> dict:
        """Convert to DynamoDB put_item format with keys."""
        return {
            'PK': f"BS#COUNTRY#{self.country_code}",
            'SK': self.period,
            'GSI1PK': f"BS#PERIOD#{self.period}",
            'GSI1SK': self.spread_bps,
            'country_code': self.country_code,
            'country_name': self.country_name,
            'currency': self.currency,
            'flag': self.flag,
            'period': self.period,
            'yield_10y': Decimal(str(self.yield_10y)),
            'yield_3m': Decimal(str(self.yield_3m)),
            'spread_pct': Decimal(str(self.spread_pct)),
            'spread_bps': self.spread_bps,
            'is_inverted': self.is_inverted,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dynamo_item(cls, item: dict) -> 'SpreadRecord':
        """Parse DynamoDB item back to SpreadRecord."""
        return cls(
            country_code=item['country_code'],
            country_name=item['country_name'],
            currency=item['currency'],
            flag=item['flag'],
            period=item['period'],
            yield_10y=float(item['yield_10y']),
            yield_3m=float(item['yield_3m']),
            spread_pct=float(item['spread_pct']),
            spread_bps=int(item['spread_bps']),
            is_inverted=bool(item['is_inverted']),
            updated_at=item['updated_at']
        )


@dataclass
class LatestSpreadJson:
    """Structure for spreads-latest.json."""

    updated_at: str
    period: str
    countries: list[dict]
    summary: dict


@dataclass
class HistorySpreadJson:
    """Structure for spreads-history.json."""

    updated_at: str
    countries: dict  # country_code -> list of historical data


@dataclass
class SummarySpreadJson:
    """Structure for spreads-summary.json."""

    updated_at: str
    period: str
    avg_spread_bps: int
    median_spread_bps: int
    widest: dict
    narrowest: dict
    inversions: list[dict]
    widening_count: int
    narrowing_count: int
