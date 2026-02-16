// Data types matching backend JSON structures

export interface SpreadCountry {
  code: string;
  name: string;
  currency: string;
  flag: string;
  yield_10y: number;
  yield_3m: number;
  spread_pct: number;
  spread_bps: number;
  is_inverted: boolean;
}

export interface SpreadSummary {
  avg_spread_bps: number;
  median_spread_bps: number;
  inverted_count: number;
  total_countries: number;
}

export interface SpreadLatestResponse {
  updated_at: string;
  period: string;
  countries: SpreadCountry[];
  summary: SpreadSummary;
}

export interface HistoryPoint {
  period: string;
  yield_10y: number;
  yield_3m: number;
  spread_pct: number;
  spread_bps: number;
  is_inverted: boolean;
}

export interface SpreadHistoryResponse {
  updated_at: string;
  countries: Record<string, HistoryPoint[]>;
}

export interface CountryRef {
  code: string;
  name: string;
  flag: string;
  spread_bps: number;
}

export interface InversionEntry extends CountryRef {}

export interface SpreadSummaryResponse {
  updated_at: string;
  period: string;
  avg_spread_bps: number;
  median_spread_bps: number;
  widest: CountryRef | null;
  narrowest: CountryRef | null;
  inversions: InversionEntry[];
  widening_count: number;
  narrowing_count: number;
}

// UI State types
export type SortField = 'spread' | 'change_1m' | 'country';
export type SortDirection = 'asc' | 'desc';
export type RegionFilter = 'all' | 'g7' | 'g20' | 'brics' | 'emerging';
export type TimePeriod = '1m' | '3m' | '6m' | '1y' | '2y';

// Extended country with computed fields for UI
export interface EnrichedCountry extends SpreadCountry {
  rank: number;
  change_1m_bps: number | null;
  change_3m_bps: number | null;
  history: HistoryPoint[];
}

// Chart data types
export interface ChartCountry {
  code: string;
  name: string;
  color: string;
  dashed: boolean;
}
