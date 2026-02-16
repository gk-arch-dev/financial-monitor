import { describe, it, expect } from 'vitest';
import { filterCountries, REGION_GROUPS } from '../../../src/features/bond-spreads/utils/filtering';
import type { EnrichedCountry } from '../../../src/features/bond-spreads/types';

const mockCountries: EnrichedCountry[] = [
  {
    code: 'US',
    name: 'United States',
    currency: 'USD',
    flag: '🇺🇸',
    yield_10y: 4.52,
    yield_3m: 2.66,
    spread_pct: 1.86,
    spread_bps: 186,
    is_inverted: false,
    rank: 1,
    change_1m_bps: 24,
    change_3m_bps: 41,
    history: [],
  },
  {
    code: 'GB',
    name: 'United Kingdom',
    currency: 'GBP',
    flag: '🇬🇧',
    yield_10y: 4.31,
    yield_3m: 2.89,
    spread_pct: 1.42,
    spread_bps: 142,
    is_inverted: false,
    rank: 2,
    change_1m_bps: 9,
    change_3m_bps: 18,
    history: [],
  },
  {
    code: 'IN',
    name: 'India',
    currency: 'INR',
    flag: '🇮🇳',
    yield_10y: 7.14,
    yield_3m: 4.27,
    spread_pct: 2.87,
    spread_bps: 287,
    is_inverted: false,
    rank: 3,
    change_1m_bps: 12,
    change_3m_bps: -8,
    history: [],
  },
  {
    code: 'MX',
    name: 'Mexico',
    currency: 'MXN',
    flag: '🇲🇽',
    yield_10y: 9.78,
    yield_3m: 7.33,
    spread_pct: 2.45,
    spread_bps: 245,
    is_inverted: false,
    rank: 4,
    change_1m_bps: -18,
    change_3m_bps: 21,
    history: [],
  },
];

describe('filterCountries', () => {
  describe('region filter', () => {
    it('returns all countries when filter is "all"', () => {
      const filtered = filterCountries(mockCountries, 'all', '');
      expect(filtered.length).toBe(4);
    });

    it('filters G7 countries correctly', () => {
      const filtered = filterCountries(mockCountries, 'g7', '');
      expect(filtered.length).toBe(2); // US and GB
      expect(filtered.map((c) => c.code)).toContain('US');
      expect(filtered.map((c) => c.code)).toContain('GB');
    });

    it('filters emerging markets correctly', () => {
      const filtered = filterCountries(mockCountries, 'emerging', '');
      expect(filtered.length).toBe(2); // IN and MX
      expect(filtered.map((c) => c.code)).toContain('IN');
      expect(filtered.map((c) => c.code)).toContain('MX');
    });
  });

  describe('search filter', () => {
    it('searches by country name', () => {
      const filtered = filterCountries(mockCountries, 'all', 'united');
      expect(filtered.length).toBe(2);
      expect(filtered.map((c) => c.name)).toContain('United States');
      expect(filtered.map((c) => c.name)).toContain('United Kingdom');
    });

    it('searches by country code', () => {
      const filtered = filterCountries(mockCountries, 'all', 'us');
      expect(filtered.length).toBe(1);
      expect(filtered[0].code).toBe('US');
    });

    it('searches by currency', () => {
      const filtered = filterCountries(mockCountries, 'all', 'inr');
      expect(filtered.length).toBe(1);
      expect(filtered[0].code).toBe('IN');
    });

    it('is case insensitive', () => {
      const filtered = filterCountries(mockCountries, 'all', 'INDIA');
      expect(filtered.length).toBe(1);
      expect(filtered[0].code).toBe('IN');
    });

    it('returns all when search is empty', () => {
      const filtered = filterCountries(mockCountries, 'all', '');
      expect(filtered.length).toBe(4);
    });

    it('handles whitespace', () => {
      const filtered = filterCountries(mockCountries, 'all', '  india  ');
      expect(filtered.length).toBe(1);
    });
  });

  describe('combined filters', () => {
    it('applies both region and search filters', () => {
      const filtered = filterCountries(mockCountries, 'emerging', 'ind');
      expect(filtered.length).toBe(1);
      expect(filtered[0].code).toBe('IN');
    });
  });
});

describe('REGION_GROUPS', () => {
  it('has empty array for "all" filter', () => {
    expect(REGION_GROUPS.all).toEqual([]);
  });

  it('has G7 countries defined', () => {
    expect(REGION_GROUPS.g7).toContain('US');
    expect(REGION_GROUPS.g7).toContain('GB');
    expect(REGION_GROUPS.g7).toContain('DE');
  });
});
