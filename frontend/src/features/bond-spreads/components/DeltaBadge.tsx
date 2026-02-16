interface DeltaBadgeProps {
  value: number | null;
  unit?: 'bps' | 'pct';
}

export default function DeltaBadge({ value, unit = 'bps' }: DeltaBadgeProps) {
  if (value === null) {
    return <span className="delta delta-neutral">—</span>;
  }

  const isPositive = value > 0;
  const arrow = isPositive ? '▲' : '▼';
  const sign = isPositive ? '+' : '';
  const suffix = unit === 'bps' ? ' bps' : '%';
  const className = isPositive ? 'delta delta-up' : 'delta delta-down';

  return (
    <span className={className}>
      {arrow} {sign}{value}{suffix}
    </span>
  );
}
