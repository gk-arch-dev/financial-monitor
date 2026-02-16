import { createContext, useContext, useState, ReactNode, useCallback } from 'react';
import type { SortField, SortDirection, RegionFilter, TimePeriod } from '../types';

interface BondSpreadsUIState {
  sortBy: SortField;
  sortDirection: SortDirection;
  regionFilter: RegionFilter;
  searchQuery: string;
  timePeriod: TimePeriod;
  selectedCountries: string[];
}

interface BondSpreadsUIContextValue extends BondSpreadsUIState {
  setSortBy: (field: SortField) => void;
  setSortDirection: (dir: SortDirection) => void;
  toggleSort: (field: SortField) => void;
  setRegionFilter: (filter: RegionFilter) => void;
  setSearchQuery: (query: string) => void;
  setTimePeriod: (period: TimePeriod) => void;
  toggleCountrySelection: (code: string) => void;
}

const BondSpreadsUIContext = createContext<BondSpreadsUIContextValue | undefined>(undefined);

const DEFAULT_STATE: BondSpreadsUIState = {
  sortBy: 'spread',
  sortDirection: 'desc',
  regionFilter: 'g20',
  searchQuery: '',
  timePeriod: '6m',
  selectedCountries: ['BR', 'US', 'GB', 'DE', 'JP'],
};

export function BondSpreadsUIProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<BondSpreadsUIState>(DEFAULT_STATE);

  const setSortBy = useCallback((field: SortField) => {
    setState((prev) => ({ ...prev, sortBy: field }));
  }, []);

  const setSortDirection = useCallback((dir: SortDirection) => {
    setState((prev) => ({ ...prev, sortDirection: dir }));
  }, []);

  const toggleSort = useCallback((field: SortField) => {
    setState((prev) => {
      if (prev.sortBy === field) {
        return { ...prev, sortDirection: prev.sortDirection === 'asc' ? 'desc' : 'asc' };
      }
      return { ...prev, sortBy: field, sortDirection: 'desc' };
    });
  }, []);

  const setRegionFilter = useCallback((filter: RegionFilter) => {
    setState((prev) => ({ ...prev, regionFilter: filter }));
  }, []);

  const setSearchQuery = useCallback((query: string) => {
    setState((prev) => ({ ...prev, searchQuery: query }));
  }, []);

  const setTimePeriod = useCallback((period: TimePeriod) => {
    setState((prev) => ({ ...prev, timePeriod: period }));
  }, []);

  const toggleCountrySelection = useCallback((code: string) => {
    setState((prev) => {
      const selected = prev.selectedCountries.includes(code)
        ? prev.selectedCountries.filter((c) => c !== code)
        : [...prev.selectedCountries, code].slice(0, 5); // Max 5 countries
      return { ...prev, selectedCountries: selected };
    });
  }, []);

  const value: BondSpreadsUIContextValue = {
    ...state,
    setSortBy,
    setSortDirection,
    toggleSort,
    setRegionFilter,
    setSearchQuery,
    setTimePeriod,
    toggleCountrySelection,
  };

  return (
    <BondSpreadsUIContext.Provider value={value}>
      {children}
    </BondSpreadsUIContext.Provider>
  );
}

export function useBondSpreadsUI(): BondSpreadsUIContextValue {
  const context = useContext(BondSpreadsUIContext);
  if (!context) {
    throw new Error('useBondSpreadsUI must be used within a BondSpreadsUIProvider');
  }
  return context;
}
