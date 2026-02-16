import { useMemo } from 'react';
import { BondSpreadsUIProvider, useBondSpreadsUI } from '../context/BondSpreadsUIContext';
import { useSpreadData } from '../hooks/useSpreadData';
import { useHistoryData } from '../hooks/useHistoryData';
import { useSummaryData } from '../hooks/useSummaryData';
import { sortCountries } from '../utils/sorting';
import { filterCountries } from '../utils/filtering';
import type { EnrichedCountry } from '../types';

import LoadingState from '@shared/components/LoadingState';
import ErrorState from '@shared/components/ErrorState';

import FilterBar from './FilterBar';
import StatsRow from './StatsRow';
import SortControls from './SortControls';
import SpreadTable from './SpreadTable';
import SpreadCardList from './SpreadCardList';
import HistoryChart from './HistoryChart';
import InversionAlerts from './InversionAlerts';
import TopMovers from './TopMovers';
import GlobalSummary from './GlobalSummary';

function DashboardContent() {
  const {
    data: latestData,
    isLoading: latestLoading,
    error: latestError,
    refetch: refetchLatest,
  } = useSpreadData();

  const { data: historyData } = useHistoryData();

  const {
    data: summaryData,
    isLoading: summaryLoading,
    error: summaryError,
    refetch: refetchSummary,
  } = useSummaryData();

  const { sortBy, sortDirection, regionFilter, searchQuery } = useBondSpreadsUI();

  // Enrich countries with history and computed fields
  const enrichedCountries = useMemo((): EnrichedCountry[] => {
    if (!latestData) return [];

    return latestData.countries.map((country, index) => {
      const history = historyData?.countries[country.code] || [];
      const historyLength = history.length;

      // Calculate changes from history
      let change_1m_bps: number | null = null;
      let change_3m_bps: number | null = null;

      if (historyLength >= 2) {
        const prevMonth = history[historyLength - 2];
        change_1m_bps = country.spread_bps - prevMonth.spread_bps;
      }

      if (historyLength >= 4) {
        const prev3Month = history[historyLength - 4];
        change_3m_bps = country.spread_bps - prev3Month.spread_bps;
      }

      return {
        ...country,
        rank: index + 1,
        change_1m_bps,
        change_3m_bps,
        history,
      };
    });
  }, [latestData, historyData]);

  // Filter and sort countries
  const filteredCountries = useMemo(() => {
    const filtered = filterCountries(enrichedCountries, regionFilter, searchQuery);
    return sortCountries(filtered, sortBy, sortDirection);
  }, [enrichedCountries, regionFilter, searchQuery, sortBy, sortDirection]);

  const isLoading = latestLoading || summaryLoading;
  const hasError = latestError || summaryError;

  if (isLoading && !latestData) {
    return (
      <>
        <div className="filter-bar-placeholder" style={{ height: 56, marginTop: 20 }} />
        <LoadingState type="stats" />
        <div style={{ marginTop: 20 }} />
        <LoadingState type="table" rows={8} />
      </>
    );
  }

  if (hasError) {
    return (
      <ErrorState
        message="Failed to load bond spread data. Please try again."
        onRetry={() => {
          refetchLatest();
          refetchSummary();
        }}
      />
    );
  }

  if (!latestData || !summaryData) {
    return null;
  }

  return (
    <>
      <FilterBar />
      <StatsRow summary={summaryData} />
      <SortControls />
      <SpreadTable countries={filteredCountries} />
      <SpreadCardList countries={filteredCountries} />
      <div className="bottom-grid">
        <HistoryChart historyData={historyData} countries={enrichedCountries} />
        <div className="sidebar-panel">
          <InversionAlerts inversions={summaryData.inversions} />
          <TopMovers countries={enrichedCountries} />
          <GlobalSummary summary={summaryData} totalCountries={latestData.countries.length} />
        </div>
      </div>
    </>
  );
}

export default function BondSpreadsDashboard() {
  return (
    <BondSpreadsUIProvider>
      <DashboardContent />
    </BondSpreadsUIProvider>
  );
}
