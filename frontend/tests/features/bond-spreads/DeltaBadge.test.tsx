import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import DeltaBadge from '../../../src/features/bond-spreads/components/DeltaBadge';

describe('DeltaBadge', () => {
  it('shows green class with + prefix for positive value', () => {
    render(<DeltaBadge value={24} />);
    const badge = screen.getByText(/\+24/);
    expect(badge).toHaveClass('delta-up');
  });

  it('shows red class for negative value', () => {
    render(<DeltaBadge value={-15} />);
    const badge = screen.getByText(/-15/);
    expect(badge).toHaveClass('delta-down');
  });

  it('renders dash for null value', () => {
    render(<DeltaBadge value={null} />);
    const badge = screen.getByText('—');
    expect(badge).toBeInTheDocument();
  });

  it('displays bps unit by default', () => {
    render(<DeltaBadge value={10} />);
    expect(screen.getByText(/bps/)).toBeInTheDocument();
  });

  it('displays percentage when unit is pct', () => {
    render(<DeltaBadge value={5} unit="pct" />);
    expect(screen.getByText(/%/)).toBeInTheDocument();
  });

  it('includes up arrow for positive values', () => {
    render(<DeltaBadge value={10} />);
    expect(screen.getByText(/▲/)).toBeInTheDocument();
  });

  it('includes down arrow for negative values', () => {
    render(<DeltaBadge value={-10} />);
    expect(screen.getByText(/▼/)).toBeInTheDocument();
  });
});
