import { describe, it, expect } from 'vitest';
import { sortCountries, getTopMovers } from '../../../src/features/bond-spreads/utils/sorting';
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
    code: 'DE',
    name: 'Germany',
    currency: 'EUR',
    flag: '🇩🇪',
    yield_10y: 2.48,
    yield_3m: 2.60,
    spread_pct: -0.12,
    spread_bps: -12,
    is_inverted: true,
    rank: 2,
    change_1m_bps: -8,
    change_3m_bps: -19,
    history: [],
  },
  {
    code: 'JP',
    name: 'Japan',
    currency: 'JPY',
    flag: '🇯🇵',
    yield_10y: 1.05,
    yield_3m: 1.43,
    spread_pct: -0.38,
    spread_bps: -38,
    is_inverted: true,
    rank: 3,
    change_1m_bps: null,
    change_3m_bps: -31,
    history: [],
  },
];

describe('sortCountries', () => {
  it('sorts by spread descending (highest first)', () => {
    const sorted = sortCountries(mockCountries, 'spread', 'desc');
    expect(sorted[0].code).toBe('US');
    expect(sorted[1].code).toBe('DE');
    expect(sorted[2].code).toBe('JP');
  });

  it('sorts by spread ascending (lowest first)', () => {
    const sorted = sortCountries(mockCountries, 'spread', 'asc');
    expect(sorted[0].code).toBe('JP');
    expect(sorted[1].code).toBe('DE');
    expect(sorted[2].code).toBe('US');
  });

  it('sorts by 1M change with nulls at end', () => {
    const sorted = sortCountries(mockCountries, 'change_1m', 'desc');
    // US has highest absolute change (24), DE has 8, JP has null
    expect(sorted[0].code).toBe('US');
    expect(sorted[1].code).toBe('DE');
    expect(sorted[2].code).toBe('JP'); // null at end
  });

  it('sorts by country name alphabetically', () => {
    const sorted = sortCountries(mockCountries, 'country', 'asc');
    expect(sorted[0].name).toBe('Germany');
    expect(sorted[1].name).toBe('Japan');
    expect(sorted[2].name).toBe('United States');
  });

  it('re-assigns ranks after sorting', () => {
    const sorted = sortCountries(mockCountries, 'spread', 'asc');
    expect(sorted[0].rank).toBe(1);
    expect(sorted[1].rank).toBe(2);
    expect(sorted[2].rank).toBe(3);
  });
});

describe('getTopMovers', () => {
  it('returns countries sorted by absolute 1M change', () => {
    const movers = getTopMovers(mockCountries, 5);
    expect(movers[0].code).toBe('US'); // |24| is highest
    expect(movers[1].code).toBe('DE'); // |8| is second
  });

  it('excludes countries with null change', () => {
    const movers = getTopMovers(mockCountries, 5);
    expect(movers.find((c) => c.code === 'JP')).toBeUndefined();
  });

  it('respects limit parameter', () => {
    const movers = getTopMovers(mockCountries, 1);
    expect(movers.length).toBe(1);
  });
});
