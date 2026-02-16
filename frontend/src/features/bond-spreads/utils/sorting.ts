import type { EnrichedCountry, SortField, SortDirection } from '../types';

/**
 * Sort countries by the specified field and direction.
 */
export function sortCountries(
  countries: EnrichedCountry[],
  sortBy: SortField,
  direction: SortDirection
): EnrichedCountry[] {
  const sorted = [...countries].sort((a, b) => {
    let comparison = 0;

    switch (sortBy) {
      case 'spread':
        comparison = b.spread_bps - a.spread_bps;
        break;

      case 'change_1m':
        // Null values go to the end
        if (a.change_1m_bps === null && b.change_1m_bps === null) {
          comparison = 0;
        } else if (a.change_1m_bps === null) {
          comparison = 1;
        } else if (b.change_1m_bps === null) {
          comparison = -1;
        } else {
          comparison = Math.abs(b.change_1m_bps) - Math.abs(a.change_1m_bps);
        }
        break;

      case 'country':
        // For alphabetical, ascending means A-Z
        comparison = b.name.localeCompare(a.name);
        break;

      default:
        comparison = 0;
    }

    return direction === 'asc' ? -comparison : comparison;
  });

  // Re-assign ranks after sorting
  return sorted.map((country, index) => ({
    ...country,
    rank: index + 1,
  }));
}

/**
 * Get the top movers by absolute 1-month change.
 */
export function getTopMovers(
  countries: EnrichedCountry[],
  limit: number = 5
): EnrichedCountry[] {
  return [...countries]
    .filter((c) => c.change_1m_bps !== null)
    .sort((a, b) => Math.abs(b.change_1m_bps!) - Math.abs(a.change_1m_bps!))
    .slice(0, limit);
}
