import { describe, it, expect } from 'vitest';
import {
  formatPercentage,
  formatBps,
  formatPeriod,
  formatNumber,
} from '../../src/shared/utils/formatting';

describe('formatPercentage', () => {
  it('formats positive values with + sign', () => {
    expect(formatPercentage(1.42)).toBe('+1.42%');
  });

  it('formats negative values without + sign', () => {
    expect(formatPercentage(-0.38)).toBe('-0.38%');
  });

  it('formats zero as +0.00%', () => {
    expect(formatPercentage(0)).toBe('+0.00%');
  });

  it('respects includeSign parameter', () => {
    expect(formatPercentage(1.42, false)).toBe('1.42%');
  });

  it('handles small decimals', () => {
    expect(formatPercentage(0.05)).toBe('+0.05%');
  });
});

describe('formatBps', () => {
  it('formats positive values', () => {
    expect(formatBps(142)).toBe('142 bps');
  });

  it('formats negative values', () => {
    expect(formatBps(-38)).toBe('-38 bps');
  });

  it('includes sign when requested', () => {
    expect(formatBps(142, true)).toBe('+142 bps');
  });

  it('handles zero', () => {
    expect(formatBps(0)).toBe('0 bps');
  });
});

describe('formatPeriod', () => {
  it('formats YYYY-MM to readable format', () => {
    expect(formatPeriod('2026-02')).toBe("Feb '26");
  });

  it('handles January correctly', () => {
    expect(formatPeriod('2025-01')).toBe("Jan '25");
  });

  it('handles December correctly', () => {
    expect(formatPeriod('2024-12')).toBe("Dec '24");
  });
});

describe('formatNumber', () => {
  it('formats with default 2 decimals', () => {
    expect(formatNumber(4.5)).toBe('4.50');
  });

  it('respects custom decimal places', () => {
    expect(formatNumber(4.5678, 1)).toBe('4.6');
  });

  it('adds thousands separators', () => {
    expect(formatNumber(1234.56)).toBe('1,234.56');
  });
});
