"""JSON file generator for frontend consumption."""

from typing import Dict, List
from datetime import datetime
import statistics

from shared.dynamo_service import DynamoService
from features.bond_spreads.services.spread_calculator import SpreadCalculator
from features.bond_spreads.services.config import DYNAMO_PK_PREFIX, COUNTRIES
from features.bond_spreads.models.types import SpreadRecord, CountryConfig


class BondSpreadJsonGenerator:
    """Generator for bond spread JSON files."""

    def __init__(self, dynamo_service: DynamoService, spread_calculator: SpreadCalculator):
        """Initialize with dependencies."""
        self.dynamo = dynamo_service
        self.calc = spread_calculator

    def generate_latest(self) -> dict:
        """Generate spreads-latest.json content using each country's most recent record.

        Returns:
            JSON structure for latest spreads
        """
        records = []
        for country in COUNTRIES:
            pk = f"{DYNAMO_PK_PREFIX}#COUNTRY#{country.code}"
            items = self.dynamo.query_by_pk(pk, ascending=False, limit=1)
            if items:
                records.append(SpreadRecord.from_dynamo_item(items[0]))

        # Sort by spread_bps descending
        records.sort(key=lambda r: r.spread_bps, reverse=True)

        # Most recent period across all countries
        period = max((r.period for r in records), default='')

        countries = [{
            'code': r.country_code,
            'name': r.country_name,
            'currency': r.currency,
            'flag': r.flag,
            'yield_10y': r.yield_10y,
            'yield_3m': r.yield_3m,
            'spread_pct': r.spread_pct,
            'spread_bps': r.spread_bps,
            'is_inverted': r.is_inverted
        } for r in records]

        spread_values = [r.spread_bps for r in records]
        summary = {
            'avg_spread_bps': int(statistics.mean(spread_values)) if spread_values else 0,
            'median_spread_bps': int(statistics.median(spread_values)) if spread_values else 0,
            'inverted_count': sum(1 for r in records if r.is_inverted),
            'total_countries': len(records)
        }

        return {
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'period': period,
            'countries': countries,
            'summary': summary
        }

    def generate_history(self, countries: List[CountryConfig]) -> dict:
        """Generate spreads-history.json content.

        Args:
            countries: List of country configurations

        Returns:
            JSON structure for historical spreads
        """
        history = {}

        for country in countries:
            pk = f"{DYNAMO_PK_PREFIX}#COUNTRY#{country.code}"
            items = self.dynamo.query_by_pk(pk, ascending=True)  # Sort by period ascending

            country_history = []
            for item in items:
                record = SpreadRecord.from_dynamo_item(item)
                country_history.append({
                    'period': record.period,
                    'yield_10y': record.yield_10y,
                    'yield_3m': record.yield_3m,
                    'spread_pct': record.spread_pct,
                    'spread_bps': record.spread_bps,
                    'is_inverted': record.is_inverted
                })

            history[country.code] = country_history

        return {
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'countries': history
        }

    def generate_summary(self) -> dict:
        """Generate spreads-summary.json content using each country's most recent record.

        Returns:
            JSON structure with summary statistics
        """
        records = []
        for country in COUNTRIES:
            pk = f"{DYNAMO_PK_PREFIX}#COUNTRY#{country.code}"
            items = self.dynamo.query_by_pk(pk, ascending=False, limit=1)
            if items:
                records.append(SpreadRecord.from_dynamo_item(items[0]))

        period = max((r.period for r in records), default='')

        if not records:
            return {
                'updated_at': datetime.utcnow().isoformat() + 'Z',
                'period': period,
                'avg_spread_bps': 0,
                'median_spread_bps': 0,
                'widest': None,
                'narrowest': None,
                'inversions': [],
                'widening_count': 0,
                'narrowing_count': 0
            }

        # Calculate statistics
        spread_values = [r.spread_bps for r in records]
        avg_spread_bps = int(statistics.mean(spread_values))
        median_spread_bps = int(statistics.median(spread_values))

        # Widest and narrowest (non-inverted)
        non_inverted = [r for r in records if not r.is_inverted]
        widest = max(non_inverted, key=lambda r: r.spread_bps) if non_inverted else None
        narrowest = min(non_inverted, key=lambda r: r.spread_bps) if non_inverted else None

        # Inversions
        inversions = [
            {
                'code': r.country_code,
                'name': r.country_name,
                'flag': r.flag,
                'spread_bps': r.spread_bps
            }
            for r in records if r.is_inverted
        ]

        # Changes (widening/narrowing)
        widening_count = 0
        narrowing_count = 0

        for record in records:
            pk = f"{DYNAMO_PK_PREFIX}#COUNTRY#{record.country_code}"
            history_items = self.dynamo.query_by_pk(pk, ascending=False, limit=2)
            history = [SpreadRecord.from_dynamo_item(item) for item in history_items]

            if len(history) >= 2:
                change_1m, _, _ = self.calc.calculate_changes(record.spread_bps, history)
                if change_1m is not None:
                    if change_1m > 0:
                        widening_count += 1
                    elif change_1m < 0:
                        narrowing_count += 1

        return {
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'period': period,
            'avg_spread_bps': avg_spread_bps,
            'median_spread_bps': median_spread_bps,
            'widest': {
                'code': widest.country_code,
                'name': widest.country_name,
                'flag': widest.flag,
                'spread_bps': widest.spread_bps
            } if widest else None,
            'narrowest': {
                'code': narrowest.country_code,
                'name': narrowest.country_name,
                'flag': narrowest.flag,
                'spread_bps': narrowest.spread_bps
            } if narrowest else None,
            'inversions': inversions,
            'widening_count': widening_count,
            'narrowing_count': narrowing_count
        }
