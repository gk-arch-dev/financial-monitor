import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import StatsRow from '../../../src/features/bond-spreads/components/StatsRow';
import type { SpreadSummaryResponse } from '../../../src/features/bond-spreads/types';

const mockSummary: SpreadSummaryResponse = {
  updated_at: '2026-02-16T14:30:00Z',
  period: '2026-02',
  avg_spread_bps: 142,
  median_spread_bps: 130,
  widest: {
    code: 'BR',
    name: 'Brazil',
    flag: '🇧🇷',
    spread_bps: 321,
  },
  narrowest: {
    code: 'CA',
    name: 'Canada',
    flag: '🇨🇦',
    spread_bps: 72,
  },
  inversions: [
    {
      code: 'JP',
      name: 'Japan',
      flag: '🇯🇵',
      spread_bps: -38,
    },
    {
      code: 'DE',
      name: 'Germany',
      flag: '🇩🇪',
      spread_bps: -12,
    },
  ],
  widening_count: 7,
  narrowing_count: 3,
};

describe('StatsRow', () => {
  it('renders all 4 stat cards', () => {
    render(<StatsRow summary={mockSummary} />);

    expect(screen.getByText('Global Avg Spread')).toBeInTheDocument();
    expect(screen.getByText('Widest Spread')).toBeInTheDocument();
    expect(screen.getByText(/Inverted|Narrowest/)).toBeInTheDocument();
    expect(screen.getByText('Active Inversions')).toBeInTheDocument();
  });

  it('displays correct average spread value', () => {
    render(<StatsRow summary={mockSummary} />);
    // 142 bps = 1.42%
    expect(screen.getByText('+1.42%')).toBeInTheDocument();
  });

  it('displays widest spread with country info', () => {
    render(<StatsRow summary={mockSummary} />);
    expect(screen.getByText('+3.21%')).toBeInTheDocument();
    expect(screen.getByText(/Brazil/)).toBeInTheDocument();
  });

  it('shows inversion count', () => {
    render(<StatsRow summary={mockSummary} />);
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('lists inverted country codes', () => {
    render(<StatsRow summary={mockSummary} />);
    expect(screen.getByText(/JP/)).toBeInTheDocument();
    expect(screen.getByText(/DE/)).toBeInTheDocument();
  });

  it('displays delta badge when change is provided', () => {
    render(<StatsRow summary={mockSummary} changeFromPrevMonth={8} />);
    expect(screen.getByText(/\+8 bps/)).toBeInTheDocument();
  });
});
