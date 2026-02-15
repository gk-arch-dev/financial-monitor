"""JSON file generator for frontend consumption."""


class JsonGenerator:
    """Generator for S3 JSON files."""

    def generate_latest(self, spreads: list[dict]) -> dict:
        """Generate spreads-latest.json content.

        Args:
            spreads: List of current spread data by country

        Returns:
            JSON-serializable dict for latest spreads
        """
        # TODO: Implement in step 1
        pass

    def generate_history(self, history: list[dict]) -> dict:
        """Generate spreads-history.json content.

        Args:
            history: Historical spread data

        Returns:
            JSON-serializable dict for historical data
        """
        # TODO: Implement in step 1
        pass

    def generate_summary(self, spreads: list[dict]) -> dict:
        """Generate spreads-summary.json content.

        Args:
            spreads: Current spread data

        Returns:
            JSON-serializable dict with summary statistics
        """
        # TODO: Implement in step 1
        pass
