interface SpreadBarProps {
  spreadBps: number;
  maxSpreadBps?: number;
}

export default function SpreadBar({ spreadBps, maxSpreadBps = 400 }: SpreadBarProps) {
  const isPositive = spreadBps >= 0;
  const widthPercent = Math.min(Math.abs(spreadBps) / maxSpreadBps * 50, 50);

  return (
    <div className="bar-track">
      <div className="bar-zero" />
      <div
        className={`bar-fill ${isPositive ? 'right' : 'left'}`}
        style={{ width: `${widthPercent}%` }}
      />
    </div>
  );
}
