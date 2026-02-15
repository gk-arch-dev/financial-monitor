"""Test fixtures for bond spreads feature."""

import pytest
from datetime import datetime
from features.bond_spreads.models.types import SpreadRecord, CountryConfig


@pytest.fixture
def sample_country_config():
    """Sample CountryConfig for testing."""
    return CountryConfig(
        code='US',
        name='United States',
        currency='USD',
        flag='🇺🇸',
        series_10y='DGS10',
        series_3m='DTB3'
    )


@pytest.fixture
def sample_spread_record():
    """Sample SpreadRecord for testing."""
    return SpreadRecord(
        country_code='US',
        country_name='United States',
        currency='USD',
        flag='🇺🇸',
        period='2025-01',
        yield_10y=4.52,
        yield_3m=2.66,
        spread_pct=1.86,
        spread_bps=186,
        is_inverted=False,
        updated_at=datetime.utcnow().isoformat() + 'Z'
    )


@pytest.fixture
def mock_fred_response():
    """Mock FRED API response."""
    return {
        'observations': [
            {'date': '2025-01-01', 'value': '4.52'},
            {'date': '2025-02-01', 'value': '4.61'},
            {'date': '2025-03-01', 'value': '.'},  # Missing value
            {'date': '2025-04-01', 'value': '4.75'}
        ]
    }
