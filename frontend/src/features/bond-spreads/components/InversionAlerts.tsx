import type { InversionEntry } from '../types';

interface InversionAlertsProps {
  inversions: InversionEntry[];
}

export default function InversionAlerts({ inversions }: InversionAlertsProps) {
  return (
    <div className="sidebar-section">
      <div className="sidebar-header">
        <span className="sidebar-title">▸ Yield Inversions</span>
        <span className="sidebar-badge" style={{ color: 'var(--red)' }}>
          {inversions.length} ACTIVE
        </span>
      </div>
      <div className="sidebar-body">
        {inversions.length === 0 ? (
          <div className="no-inversions">No active yield curve inversions</div>
        ) : (
          inversions.map((inv) => (
            <div key={inv.code} className="inversion-item">
              <div className="inv-left">
                <div className="inv-country">
                  {inv.flag} {inv.name}
                </div>
                <div className="inv-duration">INVERTED</div>
              </div>
              <div className="inv-value">{inv.spread_bps} bps</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
