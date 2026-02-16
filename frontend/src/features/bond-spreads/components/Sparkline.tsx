import type { HistoryPoint } from '../types';

interface SparklineProps {
  history: HistoryPoint[];
  isInverted?: boolean;
}

export default function Sparkline({ history, isInverted = false }: SparklineProps) {
  // Take the last 10 data points
  const points = history.slice(-10);

  if (points.length === 0) {
    return <div className="spark" />;
  }

  // Find max absolute value for scaling
  const maxAbsValue = Math.max(...points.map((p) => Math.abs(p.spread_bps)));
  const scale = maxAbsValue > 0 ? 100 / maxAbsValue : 1;

  // Determine color based on current state
  const getColor = (spreadBps: number): string => {
    if (spreadBps < 0) return 'var(--red)';
    if (spreadBps < 50) return 'var(--gold)';
    return 'var(--green)';
  };

  // Use the last point to determine overall color
  const baseColor = isInverted ? 'var(--red)' : getColor(points[points.length - 1]?.spread_bps ?? 0);

  return (
    <div className="spark">
      {points.map((point, index) => {
        const height = Math.abs(point.spread_bps) * scale;
        const opacity = 0.35 + (index / points.length) * 0.65;

        return (
          <div
            key={point.period}
            className="spark-bar"
            style={{
              height: `${Math.max(height, 3)}%`,
              background: baseColor,
              opacity,
            }}
          />
        );
      })}
    </div>
  );
}
