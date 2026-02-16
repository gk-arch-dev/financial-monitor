import type { EnrichedCountry } from '../types';
import SpreadBar from './SpreadBar';
import DeltaBadge from './DeltaBadge';
import Sparkline from './Sparkline';
import { formatPercentage, formatNumber } from '@shared/utils/formatting';

interface SpreadTableProps {
  countries: EnrichedCountry[];
}

export default function SpreadTable({ countries }: SpreadTableProps) {
  return (
    <div className="table-wrap desktop-only">
      <table className="spread-table">
        <thead>
          <tr>
            <th style={{ width: 36 }}>#</th>
            <th>Country</th>
            <th>Spread</th>
            <th>Spread Bar</th>
            <th>10Y Yield</th>
            <th>3M Yield</th>
            <th>1M Change</th>
            <th>3M Change</th>
            <th>6M Trend</th>
          </tr>
        </thead>
        <tbody>
          {countries.map((country, index) => (
            <tr key={country.code} style={{ animationDelay: `${index * 0.05}s` }}>
              <td>
                <span className="rank">{country.rank}</span>
              </td>
              <td>
                <div className="country-cell">
                  <span className="flag">{country.flag}</span>
                  <span className="country-name">
                    {country.name}
                    <span className="country-code">{country.currency}</span>
                  </span>
                </div>
              </td>
              <td>
                <div className="spread-cell">
                  <span className={`spread-pct ${country.spread_bps >= 0 ? 'positive' : 'negative'}`}>
                    {formatPercentage(country.spread_pct)}
                  </span>
                  <span className="spread-bps">{country.spread_bps} bps</span>
                </div>
              </td>
              <td className="bar-cell">
                <SpreadBar spreadBps={country.spread_bps} />
              </td>
              <td className="mono">{formatNumber(country.yield_10y)}%</td>
              <td className="mono">{formatNumber(country.yield_3m)}%</td>
              <td>
                <DeltaBadge value={country.change_1m_bps} />
              </td>
              <td>
                <DeltaBadge value={country.change_3m_bps} />
              </td>
              <td>
                <Sparkline history={country.history} isInverted={country.is_inverted} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
