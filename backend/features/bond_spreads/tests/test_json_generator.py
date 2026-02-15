"""Tests for BondSpreadJsonGenerator."""

import pytest
from unittest.mock import Mock
from features.bond_spreads.services.json_generator import BondSpreadJsonGenerator
from features.bond_spreads.services.spread_calculator import SpreadCalculator
from features.bond_spreads.models.types import SpreadRecord


@pytest.fixture
def mock_dynamo_service():
    """Mock DynamoService."""
    return Mock()


@pytest.fixture
def json_generator(mock_dynamo_service):
    """Create JsonGenerator with mocked dependencies."""
    calc = SpreadCalculator()
    return BondSpreadJsonGenerator(mock_dynamo_service, calc)


def test_generate_latest(json_generator, mock_dynamo_service):
    """Test generate_latest produces correct structure."""
    # Mock query_gsi1 response
    mock_items = [
        {
            'country_code': 'US',
            'country_name': 'United States',
            'currency': 'USD',
            'flag': '🇺🇸',
            'period': '2025-01',
            'yield_10y': 4.52,
            'yield_3m': 2.66,
            'spread_pct': 1.86,
            'spread_bps': 186,
            'is_inverted': False,
            'updated_at': '2025-01-01T00:00:00Z'
        }
    ]
    mock_dynamo_service.query_gsi1.return_value = mock_items

    result = json_generator.generate_latest('2025-01')

    assert result['period'] == '2025-01'
    assert 'updated_at' in result
    assert len(result['countries']) == 1
    assert result['countries'][0]['code'] == 'US'
    assert result['summary']['total_countries'] == 1
    assert result['summary']['avg_spread_bps'] == 186


def test_generate_history(json_generator, mock_dynamo_service, sample_country_config):
    """Test generate_history produces correct structure."""
    # Mock query_by_pk response
    mock_items = [
        {
            'country_code': 'US',
            'country_name': 'United States',
            'currency': 'USD',
            'flag': '🇺🇸',
            'period': '2025-01',
            'yield_10y': 4.52,
            'yield_3m': 2.66,
            'spread_pct': 1.86,
            'spread_bps': 186,
            'is_inverted': False,
            'updated_at': '2025-01-01T00:00:00Z'
        }
    ]
    mock_dynamo_service.query_by_pk.return_value = mock_items

    result = json_generator.generate_history([sample_country_config])

    assert 'updated_at' in result
    assert 'US' in result['countries']
    assert len(result['countries']['US']) == 1
    assert result['countries']['US'][0]['period'] == '2025-01'


def test_generate_summary(json_generator, mock_dynamo_service):
    """Test generate_summary produces correct structure."""
    # Mock query_gsi1 response with multiple countries
    mock_items = [
        {
            'country_code': 'US',
            'country_name': 'United States',
            'currency': 'USD',
            'flag': '🇺🇸',
            'period': '2025-01',
            'yield_10y': 4.52,
            'yield_3m': 2.66,
            'spread_pct': 1.86,
            'spread_bps': 186,
            'is_inverted': False,
            'updated_at': '2025-01-01T00:00:00Z'
        },
        {
            'country_code': 'DE',
            'country_name': 'Germany',
            'currency': 'EUR',
            'flag': '🇩🇪',
            'period': '2025-01',
            'yield_10y': 2.50,
            'yield_3m': 3.00,
            'spread_pct': -0.50,
            'spread_bps': -50,
            'is_inverted': True,
            'updated_at': '2025-01-01T00:00:00Z'
        }
    ]
    mock_dynamo_service.query_gsi1.return_value = mock_items
    mock_dynamo_service.query_by_pk.return_value = mock_items[:1]  # For change calculation

    result = json_generator.generate_summary('2025-01')

    assert result['period'] == '2025-01'
    assert 'avg_spread_bps' in result
    assert 'median_spread_bps' in result
    assert result['widest']['code'] == 'US'
    assert len(result['inversions']) == 1
    assert result['inversions'][0]['code'] == 'DE'
