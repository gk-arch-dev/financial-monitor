import type { SpreadSummaryResponse } from '../types';
import { formatPercentage } from '@shared/utils/formatting';

interface StatsRowProps {
  summary: SpreadSummaryResponse;
  changeFromPrevMonth?: number;
}

export default function StatsRow({ summary, changeFromPrevMonth }: StatsRowProps) {
  const avgSpreadPct = summary.avg_spread_bps / 100;
  const widestPct = summary.widest ? summary.widest.spread_bps / 100 : 0;
  const narrowestPct = summary.narrowest ? summary.narrowest.spread_bps / 100 : 0;

  // Check for inversions to display narrowest
  const hasInversions = summary.inversions.length > 0;
  const mostInverted = hasInversions
    ? summary.inversions.reduce((min, inv) =>
        inv.spread_bps < min.spread_bps ? inv : min
      )
    : null;

  return (
    <div className="stats-row">
      {/* Global Avg Spread */}
      <div className="stat-card">
        <div className="stat-label">Global Avg Spread</div>
        <div className="stat-value gold">{formatPercentage(avgSpreadPct)}</div>
        <div className="stat-sub">
          {changeFromPrevMonth !== undefined && (
            <span className={`badge ${changeFromPrevMonth >= 0 ? 'badge-green' : 'badge-red'}`}>
              {changeFromPrevMonth >= 0 ? '↑' : '↓'} {changeFromPrevMonth >= 0 ? '+' : ''}{changeFromPrevMonth} bps
            </span>
          )}
          {changeFromPrevMonth !== undefined && ' vs prev. month'}
        </div>
      </div>

      {/* Widest Spread */}
      <div className="stat-card">
        <div className="stat-label">Widest Spread</div>
        <div className="stat-value green">{formatPercentage(widestPct)}</div>
        <div className="stat-sub">
          {summary.widest && (
            <>
              {summary.widest.flag} {summary.widest.name} · {summary.widest.spread_bps} bps
            </>
          )}
        </div>
      </div>

      {/* Narrowest / Most Inverted */}
      <div className="stat-card">
        <div className="stat-label">{hasInversions ? 'Most Inverted' : 'Narrowest Spread'}</div>
        <div className={`stat-value ${hasInversions ? 'red' : 'gold'}`}>
          {hasInversions && mostInverted
            ? formatPercentage(mostInverted.spread_bps / 100)
            : summary.narrowest
            ? formatPercentage(narrowestPct)
            : '—'}
        </div>
        <div className="stat-sub">
          {hasInversions && mostInverted ? (
            <>
              {mostInverted.flag} {mostInverted.name}
            </>
          ) : summary.narrowest ? (
            <>
              {summary.narrowest.flag} {summary.narrowest.name} · {summary.narrowest.spread_bps} bps
            </>
          ) : (
            '—'
          )}
        </div>
      </div>

      {/* Active Inversions */}
      <div className="stat-card">
        <div className="stat-label">Active Inversions</div>
        <div className={`stat-value ${summary.inversions.length > 0 ? 'red' : 'green'}`}>
          {summary.inversions.length}
        </div>
        <div className="stat-sub">
          {summary.inversions.length > 0 ? (
            <>
              {summary.inversions.map((inv) => inv.code).join(' · ')} — Recession signal
            </>
          ) : (
            'No inversions detected'
          )}
        </div>
      </div>
    </div>
  );
}
