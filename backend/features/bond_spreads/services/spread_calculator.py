"""Spread calculation service for bond yields."""

from typing import Tuple, Optional, List
from datetime import datetime
from dateutil.relativedelta import relativedelta

from features.bond_spreads.models.types import SpreadRecord


class SpreadCalculator:
    """Calculator for yield curve spreads."""

    @staticmethod
    def calculate_spread(yield_10y: float, yield_3m: float) -> Tuple[float, int]:
        """Calculate spread between 10Y and 3M yields.

        Args:
            yield_10y: 10-year yield as percentage (e.g., 4.52)
            yield_3m: 3-month yield as percentage (e.g., 2.66)

        Returns:
            Tuple of (spread_pct, spread_bps)
            spread_pct: percentage points (e.g., 1.86)
            spread_bps: basis points (e.g., 186)
        """
        spread_pct = yield_10y - yield_3m
        spread_bps = int(round(spread_pct * 100))
        return spread_pct, spread_bps

    @staticmethod
    def calculate_changes(
        current_bps: int,
        history: List[SpreadRecord]
    ) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Calculate spread changes over time.

        Args:
            current_bps: Current spread in basis points
            history: Historical SpreadRecord list sorted by period descending

        Returns:
            Tuple of (change_1m, change_3m, change_6m) in basis points
            Returns None for periods without data
        """
        if not history:
            return None, None, None

        # Parse current period
        current_period = history[0].period
        current_date = datetime.strptime(current_period, '%Y-%m')

        # Build period lookup
        history_dict = {rec.period: rec.spread_bps for rec in history}

        # Calculate changes
        change_1m = None
        change_3m = None
        change_6m = None

        period_1m = (current_date - relativedelta(months=1)).strftime('%Y-%m')
        if period_1m in history_dict:
            change_1m = current_bps - history_dict[period_1m]

        period_3m = (current_date - relativedelta(months=3)).strftime('%Y-%m')
        if period_3m in history_dict:
            change_3m = current_bps - history_dict[period_3m]

        period_6m = (current_date - relativedelta(months=6)).strftime('%Y-%m')
        if period_6m in history_dict:
            change_6m = current_bps - history_dict[period_6m]

        return change_1m, change_3m, change_6m

    @staticmethod
    def is_inverted(spread_pct: float) -> bool:
        """Check if yield curve is inverted.

        Args:
            spread_pct: Spread in percentage points

        Returns:
            True if spread is negative (inverted curve)
        """
        return spread_pct < 0

    @staticmethod
    def calculate_inversion_streak(
        history: List[SpreadRecord]
    ) -> Tuple[Optional[str], Optional[int]]:
        """Calculate how long the curve has been inverted.

        Args:
            history: Historical SpreadRecord list sorted by period descending

        Returns:
            Tuple of (inverted_since_period, approx_days)
            Returns (None, None) if not currently inverted
        """
        if not history or not history[0].is_inverted:
            return None, None

        # Find first non-inverted period going backwards
        inverted_since = history[0].period

        for i, record in enumerate(history):
            if not record.is_inverted:
                # Found first non-inverted, so previous was start of inversion
                if i > 0:
                    inverted_since = history[i - 1].period
                break

        # Calculate approximate days (assume 30 days per month)
        current_date = datetime.strptime(history[0].period, '%Y-%m')
        inversion_start = datetime.strptime(inverted_since, '%Y-%m')
        delta = current_date - inversion_start
        approx_days = delta.days

        return inverted_since, approx_days
