import { useMemo } from 'react';
import { useBondSpreadsUI } from '../context/BondSpreadsUIContext';
import type { SpreadHistoryResponse, TimePeriod, EnrichedCountry } from '../types';
import ChartLegend from './ChartLegend';
import { formatPeriod } from '@shared/utils/formatting';

interface HistoryChartProps {
  historyData: SpreadHistoryResponse | undefined;
  countries: EnrichedCountry[];
}

const TIME_PERIODS: { value: TimePeriod; label: string }[] = [
  { value: '1m', label: '1M' },
  { value: '3m', label: '3M' },
  { value: '6m', label: '6M' },
  { value: '1y', label: '1Y' },
  { value: '2y', label: '2Y' },
];

const COUNTRY_COLORS: Record<string, string> = {
  BR: 'var(--green)',
  US: 'var(--gold)',
  GB: 'var(--cyan)',
  DE: 'var(--red)',
  JP: 'var(--chart-purple)',
  FR: 'var(--blue)',
  CA: '#8a9a5b',
  AU: '#e07a5f',
  IN: '#81b29a',
  MX: '#f2cc8f',
};

const PERIOD_MONTHS: Record<TimePeriod, number> = {
  '1m': 1,
  '3m': 3,
  '6m': 6,
  '1y': 12,
  '2y': 24,
};

export default function HistoryChart({ historyData, countries }: HistoryChartProps) {
  const { timePeriod, setTimePeriod, selectedCountries } = useBondSpreadsUI();

  const chartData = useMemo(() => {
    if (!historyData) return null;

    const months = PERIOD_MONTHS[timePeriod];
    const selectedData = selectedCountries
      .map((code) => {
        const history = historyData.countries[code];
        if (!history) return null;

        const country = countries.find((c) => c.code === code);
        const points = history.slice(-months);

        return {
          code,
          name: country?.name || code,
          color: COUNTRY_COLORS[code] || 'var(--text-dim)',
          dashed: country?.is_inverted || false,
          points,
        };
      })
      .filter(Boolean) as Array<{
        code: string;
        name: string;
        color: string;
        dashed: boolean;
        points: Array<{ period: string; spread_bps: number }>;
      }>;

    // Get all unique periods
    const allPeriods = Array.from(
      new Set(selectedData.flatMap((d) => d.points.map((p) => p.period)))
    ).sort();

    // Find min/max for scaling
    const allValues = selectedData.flatMap((d) => d.points.map((p) => p.spread_bps));
    const maxBps = Math.max(...allValues, 100);
    const minBps = Math.min(...allValues, -100);

    return { selectedData, allPeriods, maxBps, minBps };
  }, [historyData, selectedCountries, timePeriod, countries]);

  const legendItems = useMemo(() => {
    if (!chartData) return [];
    return chartData.selectedData.map((d) => ({
      code: d.code,
      name: d.name,
      color: d.color,
      dashed: d.dashed,
    }));
  }, [chartData]);

  // Generate SVG paths
  const generatePath = (
    points: Array<{ period: string; spread_bps: number }>,
    allPeriods: string[],
    maxBps: number,
    minBps: number
  ): string => {
    const range = maxBps - minBps;
    const width = 900;
    const height = 220;

    const coords = allPeriods.map((period, i) => {
      const point = points.find((p) => p.period === period);
      const x = (i / (allPeriods.length - 1 || 1)) * width;
      const y = point
        ? height - ((point.spread_bps - minBps) / range) * height
        : height / 2;
      return `${x},${y}`;
    });

    return coords.join(' ');
  };

  // Y-axis labels
  const yLabels = useMemo(() => {
    if (!chartData) return ['+400 bps', '+300', '+200', '+100', '0', '-100'];
    const { maxBps, minBps } = chartData;
    const range = maxBps - minBps;
    const step = range / 5;
    return Array.from({ length: 6 }, (_, i) => {
      const value = Math.round(maxBps - i * step);
      return value >= 0 ? `+${value}` : `${value}`;
    });
  }, [chartData]);

  // X-axis labels
  const xLabels = useMemo(() => {
    if (!chartData || chartData.allPeriods.length === 0) return [];
    const periods = chartData.allPeriods;
    const step = Math.max(1, Math.floor(periods.length / 6));
    return periods.filter((_, i) => i % step === 0 || i === periods.length - 1).map(formatPeriod);
  }, [chartData]);

  // Zero line position
  const zeroLinePosition = useMemo(() => {
    if (!chartData) return 80;
    const { maxBps, minBps } = chartData;
    const range = maxBps - minBps;
    return ((maxBps - 0) / range) * 100;
  }, [chartData]);

  if (!historyData) {
    return (
      <div className="chart-panel">
        <div className="chart-header">
          <div className="chart-title">Historical <span>Spread</span> Comparison</div>
        </div>
        <div className="chart-area" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ color: 'var(--text-dim)' }}>Loading chart data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="chart-panel">
      <div className="chart-header">
        <div className="chart-title">
          Historical <span>Spread</span> Comparison
        </div>
        <div className="time-group">
          {TIME_PERIODS.map((period) => (
            <button
              key={period.value}
              className={`time-btn ${timePeriod === period.value ? 'active' : ''}`}
              onClick={() => setTimePeriod(period.value)}
            >
              {period.label}
            </button>
          ))}
        </div>
      </div>

      <div className="chart-area">
        <div className="chart-y">
          {yLabels.map((label, i) => (
            <span key={i}>{label}</span>
          ))}
        </div>

        <div className="chart-body">
          {/* Grid lines */}
          {[0, 20, 40, 60, 80, 100].map((pos) => (
            <div
              key={pos}
              className={pos === Math.round(zeroLinePosition) ? 'zero-line' : 'grid-line'}
              style={{ top: `${pos}%` }}
            />
          ))}

          {/* SVG Chart */}
          {chartData && (
            <svg className="chart-svg" viewBox="0 0 900 220" preserveAspectRatio="none">
              {/* Area fill for first country */}
              {chartData.selectedData.length > 0 && (
                <path
                  d={`M${generatePath(
                    chartData.selectedData[0].points,
                    chartData.allPeriods,
                    chartData.maxBps,
                    chartData.minBps
                  )
                    .split(' ')
                    .map((c, i) => (i === 0 ? `M${c}` : `L${c}`))
                    .join(' ')} L900,220 L0,220 Z`}
                  fill="url(#areaGrad)"
                  opacity="0.08"
                />
              )}

              {/* Lines */}
              {chartData.selectedData.map((data) => (
                <polyline
                  key={data.code}
                  fill="none"
                  stroke={data.color}
                  strokeWidth={data.dashed ? 1.8 : 2.5}
                  opacity={data.dashed ? 0.7 : 0.9}
                  strokeDasharray={data.dashed ? '6,4' : undefined}
                  points={generatePath(
                    data.points,
                    chartData.allPeriods,
                    chartData.maxBps,
                    chartData.minBps
                  )}
                />
              ))}

              <defs>
                <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--green)" />
                  <stop offset="100%" stopColor="var(--green)" stopOpacity="0" />
                </linearGradient>
              </defs>
            </svg>
          )}
        </div>

        <div className="chart-x">
          {xLabels.map((label, i) => (
            <span key={i}>{label}</span>
          ))}
        </div>
      </div>

      <ChartLegend items={legendItems} />
    </div>
  );
}
