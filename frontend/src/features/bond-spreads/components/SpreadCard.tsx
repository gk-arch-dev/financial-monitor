import type { EnrichedCountry } from '../types';
import SpreadBar from './SpreadBar';
import DeltaBadge from './DeltaBadge';
import Sparkline from './Sparkline';
import { formatPercentage } from '@shared/utils/formatting';

interface SpreadCardProps {
  country: EnrichedCountry;
}

export default function SpreadCard({ country }: SpreadCardProps) {
  return (
    <div className="spread-card">
      {/* Row 1: Rank, Country, Spread */}
      <div className="spread-card-header">
        <span className="rank">{country.rank}</span>
        <div className="country-cell">
          <span className="flag">{country.flag}</span>
          <span className="country-name">{country.name}</span>
        </div>
        <div className="spread-cell">
          <span className={`spread-pct ${country.spread_bps >= 0 ? 'positive' : 'negative'}`}>
            {formatPercentage(country.spread_pct)}
          </span>
          <span className="spread-bps">{country.spread_bps} bps</span>
        </div>
      </div>

      {/* Row 2: Spread Bar */}
      <div className="spread-card-bar">
        <SpreadBar spreadBps={country.spread_bps} />
      </div>

      {/* Row 3: Deltas and Sparkline */}
      <div className="spread-card-footer">
        <DeltaBadge value={country.change_1m_bps} />
        <DeltaBadge value={country.change_3m_bps} />
        <Sparkline history={country.history} isInverted={country.is_inverted} />
      </div>
    </div>
  );
}
