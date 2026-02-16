import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import SpreadBar from '../../../src/features/bond-spreads/components/SpreadBar';

describe('SpreadBar', () => {
  it('renders green bar on right for positive spread', () => {
    const { container } = render(<SpreadBar spreadBps={200} />);
    const fill = container.querySelector('.bar-fill');
    expect(fill).toHaveClass('right');
    expect(fill).not.toHaveClass('left');
  });

  it('renders red bar on left for negative spread', () => {
    const { container } = render(<SpreadBar spreadBps={-50} />);
    const fill = container.querySelector('.bar-fill');
    expect(fill).toHaveClass('left');
    expect(fill).not.toHaveClass('right');
  });

  it('renders zero-width bar for zero spread', () => {
    const { container } = render(<SpreadBar spreadBps={0} />);
    const fill = container.querySelector('.bar-fill');
    expect(fill).toHaveStyle({ width: '0%' });
  });

  it('scales width correctly based on maxSpreadBps', () => {
    const { container } = render(<SpreadBar spreadBps={200} maxSpreadBps={400} />);
    const fill = container.querySelector('.bar-fill');
    // 200/400 * 50 = 25%
    expect(fill).toHaveStyle({ width: '25%' });
  });

  it('caps width at 50% for values exceeding max', () => {
    const { container } = render(<SpreadBar spreadBps={600} maxSpreadBps={400} />);
    const fill = container.querySelector('.bar-fill');
    expect(fill).toHaveStyle({ width: '50%' });
  });

  it('renders the zero line', () => {
    const { container } = render(<SpreadBar spreadBps={100} />);
    const zeroLine = container.querySelector('.bar-zero');
    expect(zeroLine).toBeInTheDocument();
  });

  it('renders the track', () => {
    const { container } = render(<SpreadBar spreadBps={100} />);
    const track = container.querySelector('.bar-track');
    expect(track).toBeInTheDocument();
  });
});
