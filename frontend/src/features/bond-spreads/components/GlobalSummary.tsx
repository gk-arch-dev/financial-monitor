import type { SpreadSummaryResponse } from '../types';

interface GlobalSummaryProps {
  summary: SpreadSummaryResponse;
  totalCountries: number;
}

export default function GlobalSummary({ summary, totalCountries }: GlobalSummaryProps) {
  return (
    <div className="sidebar-section">
      <div className="sidebar-header">
        <span className="sidebar-title">▸ Global Summary</span>
        <span className="sidebar-badge" style={{ color: 'var(--text-dim)' }}>
          STATS
        </span>
      </div>
      <div className="sidebar-body">
        <div className="stat-row">
          <span className="stat-row-label">Avg Spread</span>
          <span className="stat-row-value" style={{ color: 'var(--gold)' }}>
            {summary.avg_spread_bps >= 0 ? '+' : ''}{summary.avg_spread_bps} bps
          </span>
        </div>
        <div className="stat-row">
          <span className="stat-row-label">Median</span>
          <span className="stat-row-value" style={{ color: 'var(--gold)' }}>
            {summary.median_spread_bps >= 0 ? '+' : ''}{summary.median_spread_bps} bps
          </span>
        </div>
        <div className="stat-row">
          <span className="stat-row-label">Widening</span>
          <span className="stat-row-value" style={{ color: 'var(--green)' }}>
            {summary.widening_count} / {totalCountries}
          </span>
        </div>
        <div className="stat-row">
          <span className="stat-row-label">Narrowing</span>
          <span className="stat-row-value" style={{ color: 'var(--red)' }}>
            {summary.narrowing_count} / {totalCountries}
          </span>
        </div>
        <div className="stat-row">
          <span className="stat-row-label">Inversions</span>
          <span className="stat-row-value" style={{ color: 'var(--red)' }}>
            {summary.inversions.length}
          </span>
        </div>
        <div className="stat-row">
          <span className="stat-row-label">Countries</span>
          <span className="stat-row-value" style={{ color: 'var(--text)' }}>
            {totalCountries}
          </span>
        </div>
      </div>
    </div>
  );
}
