"""FRED API client for fetching bond yield data."""

import requests
import time
from typing import List, Dict
from aws_lambda_powertools import Logger

logger = Logger()


class FredClient:
    """Client for Federal Reserve Economic Data (FRED) API."""

    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self, api_key: str, rate_limit: int = 120):
        """Initialize FRED client.

        Args:
            api_key: FRED API key from SSM
            rate_limit: Requests per hour (default 120 to be safe)
        """
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.min_interval = 3600 / rate_limit  # Seconds between requests
        self.last_request_time = 0

    def _wait_for_rate_limit(self) -> None:
        """Implement simple rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def get_series(
        self,
        series_id: str,
        start_date: str,
        end_date: str,
        frequency: str = "m"
    ) -> List[Dict[str, any]]:
        """Fetch data series from FRED.

        Args:
            series_id: FRED series identifier (e.g., 'DGS10')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            frequency: Data frequency ('m' for monthly)

        Returns:
            List of observations: [{"date": "2025-01-01", "value": 4.52}, ...]
            Filters out missing values (".") and converts to float
        """
        self._wait_for_rate_limit()

        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'observation_start': start_date,
            'observation_end': end_date,
            'frequency': frequency,
            'sort_order': 'asc'
        }

        try:
            logger.info("Fetching FRED series", extra={"series_id": series_id, "start": start_date, "end": end_date})
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            observations = data.get('observations', [])

            # Filter out missing values (marked as ".")
            # and convert string values to float
            result = []
            for obs in observations:
                if obs['value'] != '.':
                    try:
                        result.append({
                            'date': obs['date'],
                            'value': float(obs['value'])
                        })
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid observation: {obs}", extra={"error": str(e)})
                        continue

            logger.info(f"Fetched {len(result)} observations for {series_id}")
            return result

        except requests.RequestException as e:
            logger.error(f"FRED API error for {series_id}", extra={"error": str(e)})
            return []

    def validate_series(self, series_id: str) -> bool:
        """Check if series exists and has recent data.

        Args:
            series_id: FRED series identifier

        Returns:
            True if series exists and has data
        """
        from datetime import datetime, timedelta

        # Check last 6 months (OECD data has 2-3 month lag)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')

        data = self.get_series(series_id, start_date, end_date)
        return len(data) > 0
