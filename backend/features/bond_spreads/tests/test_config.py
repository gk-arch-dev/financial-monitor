"""Tests for config.py."""

import pytest
from features.bond_spreads.services.config import COUNTRIES, DYNAMO_PK_PREFIX, S3_DATA_PREFIX


def test_dynamo_prefix():
    """Test DynamoDB prefix is correct."""
    assert DYNAMO_PK_PREFIX == 'BS'


def test_s3_prefix():
    """Test S3 prefix is correct."""
    assert S3_DATA_PREFIX == 'data/bond-spreads'


def test_countries_list():
    """Test countries list has expected countries."""
    codes = [c.code for c in COUNTRIES]
    assert 'US' in codes
    assert 'DE' in codes
    assert 'GB' in codes
    assert len(codes) == len(set(codes))  # No duplicates


def test_country_config_fields():
    """Test all countries have required fields."""
    for country in COUNTRIES:
        assert len(country.code) == 2
        assert country.name
        assert len(country.currency) == 3
        assert country.flag  # Has emoji
        assert country.series_10y
        assert country.series_3m


def test_country_flags_are_emoji():
    """Test flags are emoji characters."""
    for country in COUNTRIES:
        # Emoji should have length > 1 when encoded
        assert len(country.flag.encode('utf-8')) > 2
