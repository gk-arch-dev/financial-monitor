"""FRED API client for fetching bond yield data."""


class FredClient:
    """Client for Federal Reserve Economic Data (FRED) API."""

    def __init__(self, api_key: str):
        """Initialize FRED client.

        Args:
            api_key: FRED API key
        """
        self.api_key = api_key
        self.base_url = 'https://api.stlouisfed.org/fred'

    def get_series(
        self,
        series_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        """Fetch a data series from FRED.

        Args:
            series_id: FRED series identifier
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List of observations with date and value
        """
        # TODO: Implement in step 1
        pass

    def get_latest_observation(self, series_id: str) -> dict | None:
        """Get the most recent observation for a series.

        Args:
            series_id: FRED series identifier

        Returns:
            Latest observation dict or None
        """
        # TODO: Implement in step 1
        pass
