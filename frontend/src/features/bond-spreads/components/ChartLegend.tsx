interface LegendItem {
  code: string;
  name: string;
  color: string;
  dashed: boolean;
}

interface ChartLegendProps {
  items: LegendItem[];
}

export default function ChartLegend({ items }: ChartLegendProps) {
  return (
    <div className="chart-legend">
      {items.map((item) => (
        <div key={item.code} className="legend-item">
          {item.dashed ? (
            <div className="legend-dash" style={{ borderColor: item.color }} />
          ) : (
            <div className="legend-line" style={{ background: item.color }} />
          )}
          {item.name}
        </div>
      ))}
    </div>
  );
}
