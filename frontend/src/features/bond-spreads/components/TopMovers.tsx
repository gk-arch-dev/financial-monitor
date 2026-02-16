import type { EnrichedCountry } from '../types';

interface TopMoversProps {
  countries: EnrichedCountry[];
  limit?: number;
}

export default function TopMovers({ countries, limit = 5 }: TopMoversProps) {
  // Sort by absolute 1-month change
  const movers = [...countries]
    .filter((c) => c.change_1m_bps !== null)
    .sort((a, b) => Math.abs(b.change_1m_bps!) - Math.abs(a.change_1m_bps!))
    .slice(0, limit);

  return (
    <div className="sidebar-section">
      <div className="sidebar-header">
        <span className="sidebar-title">▸ Biggest Movers · 1M</span>
        <span className="sidebar-badge" style={{ color: 'var(--text-dim)' }}>
          DELTA
        </span>
      </div>
      <div className="sidebar-body">
        {movers.map((country, index) => {
          const isPositive = (country.change_1m_bps ?? 0) > 0;
          const sign = isPositive ? '+' : '';
          const arrow = isPositive ? '▲' : '▼';

          return (
            <div key={country.code} className="mover-item">
              <div className="mover-left">
                <span className="mover-rank">{index + 1}</span>
                <span className="mover-name">
                  {country.flag} {country.name}
                </span>
              </div>
              <span className={`mover-value ${isPositive ? 'positive' : 'negative'}`}>
                {arrow} {sign}{country.change_1m_bps} bps
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
