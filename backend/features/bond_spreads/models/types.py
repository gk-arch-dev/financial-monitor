"""Type definitions for Bond Spreads feature."""

from dataclasses import dataclass
from datetime import date


@dataclass
class SpreadData:
    """Calculated spread data for a country."""

    country_code: str
    period: str  # YYYY-MM format
    yield_10y: float
    yield_3m: float
    spread_pct: float
    spread_bps: int
    is_inverted: bool


@dataclass
class CountrySpread:
    """Full country spread record for DynamoDB."""

    pk: str  # BS#COUNTRY#{country_code}
    sk: str  # YYYY-MM
    gsi1pk: str  # BS#PERIOD#{period}
    gsi1sk: int  # spread_bps (for sorting)
    country_code: str
    country_name: str
    currency: str
    flag: str
    period: str
    yield_10y: float
    yield_3m: float
    spread_pct: float
    spread_bps: int
    is_inverted: bool
    updated_at: str


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
