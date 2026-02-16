import type { EnrichedCountry, RegionFilter } from '../types';

/**
 * Region group definitions.
 * Note: Our backend only has 9 countries, so some groups may overlap.
 */
export const REGION_GROUPS: Record<RegionFilter, string[]> = {
  all: [], // Empty means all countries
  g7: ['US', 'GB', 'DE', 'FR', 'JP', 'CA'], // Italy not in our data
  g20: ['US', 'GB', 'DE', 'FR', 'JP', 'CA', 'AU', 'IN', 'MX', 'BR'], // All our countries
  brics: ['BR', 'IN'], // Brazil, India (Russia, China, South Africa not in data)
  emerging: ['IN', 'MX', 'BR'], // India, Mexico, Brazil
};

/**
 * Filter countries by region and search query.
 */
export function filterCountries(
  countries: EnrichedCountry[],
  regionFilter: RegionFilter,
  searchQuery: string
): EnrichedCountry[] {
  let filtered = countries;

  // Apply region filter
  if (regionFilter !== 'all') {
    const regionCodes = REGION_GROUPS[regionFilter];
    if (regionCodes.length > 0) {
      filtered = filtered.filter((c) => regionCodes.includes(c.code));
    }
  }

  // Apply search filter
  if (searchQuery.trim()) {
    const query = searchQuery.toLowerCase().trim();
    filtered = filtered.filter(
      (c) =>
        c.name.toLowerCase().includes(query) ||
        c.code.toLowerCase().includes(query) ||
        c.currency.toLowerCase().includes(query)
    );
  }

  return filtered;
}

/**
 * Get the display label for a region filter.
 */
export function getRegionLabel(filter: RegionFilter): string {
  switch (filter) {
    case 'all':
      return 'All';
    case 'g7':
      return 'G7';
    case 'g20':
      return 'G20';
    case 'brics':
      return 'BRICS';
    case 'emerging':
      return 'Emerging';
    default:
      return filter;
  }
}
