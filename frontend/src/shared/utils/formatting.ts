/**
 * Format a number as a percentage string.
 * @param value - The percentage value (e.g., 1.42 for 1.42%)
 * @param includeSign - Whether to include + for positive values
 */
export function formatPercentage(value: number, includeSign = true): string {
  const sign = includeSign && value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * Format a number as basis points.
 * @param value - The basis points value
 * @param includeSign - Whether to include + for positive values
 */
export function formatBps(value: number, includeSign = false): string {
  const sign = includeSign && value > 0 ? '+' : '';
  return `${sign}${value} bps`;
}

/**
 * Format an ISO date string to a readable format.
 * @param isoString - ISO 8601 date string
 */
export function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format a time from an ISO date string.
 * @param isoString - ISO 8601 date string
 */
export function formatTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short',
  });
}

/**
 * Format a period string (YYYY-MM) to a readable format.
 * @param period - Period string in YYYY-MM format
 */
export function formatPeriod(period: string): string {
  const [year, month] = period.split('-');
  const date = new Date(parseInt(year), parseInt(month) - 1);
  const monthName = date.toLocaleDateString('en-US', { month: 'short' });
  const shortYear = year.slice(-2);
  return `${monthName} '${shortYear}`;
}

/**
 * Format a number with thousands separators.
 * @param value - The number to format
 * @param decimals - Number of decimal places
 */
export function formatNumber(value: number, decimals = 2): string {
  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}
