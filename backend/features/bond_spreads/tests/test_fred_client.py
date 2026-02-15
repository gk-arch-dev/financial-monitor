"""Tests for FredClient."""

import pytest
from unittest.mock import Mock, patch
from features.bond_spreads.services.fred_client import FredClient


def test_get_series_success(mock_fred_response):
    """Test successful series fetch."""
    client = FredClient(api_key='test-key')

    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_fred_response
        mock_get.return_value.raise_for_status = Mock()

        result = client.get_series('DGS10', '2025-01-01', '2025-04-01')

        # Should filter out "." values
        assert len(result) == 3
        assert result[0]['value'] == 4.52
        assert result[1]['value'] == 4.61
        assert result[2]['value'] == 4.75


def test_get_series_filters_missing_values():
    """Test that missing values (.) are filtered."""
    client = FredClient(api_key='test-key')

    response = {
        'observations': [
            {'date': '2025-01-01', 'value': '.'},
            {'date': '2025-02-01', 'value': '.'},
        ]
    }

    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = response
        mock_get.return_value.raise_for_status = Mock()

        result = client.get_series('TEST', '2025-01-01', '2025-02-01')

        assert len(result) == 0


def test_get_series_api_error():
    """Test handling of API errors."""
    import requests
    client = FredClient(api_key='test-key')

    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException('API Error')

        result = client.get_series('INVALID', '2025-01-01', '2025-02-01')

        assert result == []


def test_validate_series():
    """Test series validation."""
    client = FredClient(api_key='test-key')

    with patch.object(client, 'get_series') as mock_get_series:
        mock_get_series.return_value = [{'date': '2025-01-01', 'value': 4.52}]

        assert client.validate_series('DGS10') is True

        mock_get_series.return_value = []

        assert client.validate_series('INVALID') is False
