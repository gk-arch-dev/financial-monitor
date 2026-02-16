import './ErrorState.css';

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export default function ErrorState({
  message = 'Data temporarily unavailable',
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="error-state">
      <div className="error-icon">⚠</div>
      <p className="error-message">{message}</p>
      {onRetry && (
        <button className="error-retry" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
