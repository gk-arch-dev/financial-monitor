import './LoadingState.css';

interface LoadingStateProps {
  rows?: number;
  type?: 'stats' | 'table' | 'card';
}

export default function LoadingState({ rows = 4, type = 'table' }: LoadingStateProps) {
  if (type === 'stats') {
    return (
      <div className="loading-stats">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="loading-stat-card">
            <div className="loading-skeleton loading-label" />
            <div className="loading-skeleton loading-value" />
            <div className="loading-skeleton loading-sub" />
          </div>
        ))}
      </div>
    );
  }

  if (type === 'card') {
    return (
      <div className="loading-cards">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="loading-card">
            <div className="loading-skeleton loading-card-header" />
            <div className="loading-skeleton loading-card-bar" />
            <div className="loading-skeleton loading-card-footer" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="loading-table">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="loading-row">
          <div className="loading-skeleton loading-cell-sm" />
          <div className="loading-skeleton loading-cell-lg" />
          <div className="loading-skeleton loading-cell-md" />
          <div className="loading-skeleton loading-cell-bar" />
          <div className="loading-skeleton loading-cell-sm" />
          <div className="loading-skeleton loading-cell-sm" />
        </div>
      ))}
    </div>
  );
}
