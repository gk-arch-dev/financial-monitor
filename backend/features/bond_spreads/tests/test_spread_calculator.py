"""Tests for SpreadCalculator."""

import pytest
from datetime import datetime
from features.bond_spreads.services.spread_calculator import SpreadCalculator
from features.bond_spreads.models.types import SpreadRecord


def test_calculate_spread_positive():
    """Test positive spread calculation."""
    calc = SpreadCalculator()

    spread_pct, spread_bps = calc.calculate_spread(4.52, 2.66)

    assert spread_pct == pytest.approx(1.86)
    assert spread_bps == 186


def test_calculate_spread_negative():
    """Test inverted curve (negative spread)."""
    calc = SpreadCalculator()

    spread_pct, spread_bps = calc.calculate_spread(2.50, 3.00)

    assert spread_pct == pytest.approx(-0.50)
    assert spread_bps == -50


def test_calculate_spread_zero():
    """Test flat curve."""
    calc = SpreadCalculator()

    spread_pct, spread_bps = calc.calculate_spread(3.00, 3.00)

    assert spread_pct == 0.0
    assert spread_bps == 0


def test_is_inverted():
    """Test inversion detection."""
    calc = SpreadCalculator()

    assert calc.is_inverted(-0.5) is True
    assert calc.is_inverted(0) is False
    assert calc.is_inverted(1.5) is False


def test_calculate_changes():
    """Test change calculations."""
    calc = SpreadCalculator()

    # Create history
    history = [
        SpreadRecord('US', 'United States', 'USD', '🇺🇸', '2025-04', 4.52, 2.66, 1.86, 186, False, '2025-04-01T00:00:00Z'),
        SpreadRecord('US', 'United States', 'USD', '🇺🇸', '2025-03', 4.40, 2.70, 1.70, 170, False, '2025-03-01T00:00:00Z'),
        SpreadRecord('US', 'United States', 'USD', '🇺🇸', '2025-01', 4.20, 2.80, 1.40, 140, False, '2025-01-01T00:00:00Z'),
        SpreadRecord('US', 'United States', 'USD', '🇺🇸', '2024-10', 4.00, 3.00, 1.00, 100, False, '2024-10-01T00:00:00Z'),
    ]

    change_1m, change_3m, change_6m = calc.calculate_changes(186, history)

    assert change_1m == 16  # 186 - 170
    assert change_3m == 46  # 186 - 140
    assert change_6m == 86  # 186 - 100


def test_calculate_inversion_streak():
    """Test inversion streak calculation."""
    calc = SpreadCalculator()

    # Currently inverted for 3 months
    history = [
        SpreadRecord('US', 'US', 'USD', '🇺🇸', '2025-03', 2.50, 3.00, -0.50, -50, True, '2025-03-01T00:00:00Z'),
        SpreadRecord('US', 'US', 'USD', '🇺🇸', '2025-02', 2.60, 3.10, -0.50, -50, True, '2025-02-01T00:00:00Z'),
        SpreadRecord('US', 'US', 'USD', '🇺🇸', '2025-01', 2.70, 3.00, -0.30, -30, True, '2025-01-01T00:00:00Z'),
        SpreadRecord('US', 'US', 'USD', '🇺🇸', '2024-12', 3.00, 2.80, 0.20, 20, False, '2024-12-01T00:00:00Z'),
    ]

    since, days = calc.calculate_inversion_streak(history)

    assert since == '2025-01'
    assert days >= 59  # Approximately 2-3 months


def test_calculate_inversion_streak_not_inverted():
    """Test when curve is not inverted."""
    calc = SpreadCalculator()

    history = [
        SpreadRecord('US', 'US', 'USD', '🇺🇸', '2025-01', 4.00, 3.00, 1.00, 100, False, '2025-01-01T00:00:00Z'),
    ]

    since, days = calc.calculate_inversion_streak(history)

    assert since is None
    assert days is None
