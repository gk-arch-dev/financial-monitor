"""Spread calculation service for bond yields."""

from ..models.types import SpreadData


class SpreadCalculator:
    """Calculator for yield curve spreads."""

    def calculate_spread(
        self,
        yield_10y: float,
        yield_3m: float,
    ) -> SpreadData:
        """Calculate spread between 10Y and 3M yields.

        Args:
            yield_10y: 10-year yield as percentage (e.g., 4.52)
            yield_3m: 3-month yield as percentage (e.g., 2.66)

        Returns:
            SpreadData with spread in percentage and basis points
        """
        # TODO: Implement in step 1
        pass

    def is_inverted(self, spread_bps: int) -> bool:
        """Check if yield curve is inverted.

        Args:
            spread_bps: Spread in basis points

        Returns:
            True if spread is negative (inverted curve)
        """
        return spread_bps < 0
