import ThemeToggle from './ThemeToggle';
import './Header.css';

interface HeaderProps {
  updatedAt?: string;
}

export default function Header({ updatedAt }: HeaderProps) {
  const now = new Date();
  const dateStr = now.toISOString().split('T')[0];
  const timeStr = updatedAt
    ? new Date(updatedAt).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
        timeZone: 'UTC',
      }) + ' UTC'
    : '--:-- UTC';

  return (
    <header className="header">
      <div className="logo-area">
        <div className="logo-mark">F</div>
        <div className="logo-text">
          Financial <span>Monitor</span>
        </div>
      </div>
      <div className="header-right">
        <ThemeToggle />
        <div className="live-indicator">
          <div className="live-dot" />
          LIVE
        </div>
        <span className="header-meta">10Y - 3M Spread · Updated {timeStr}</span>
        <span className="header-meta">{dateStr}</span>
      </div>
    </header>
  );
}
