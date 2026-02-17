import { useQuery } from '@tanstack/react-query';
import type { SpreadSummaryResponse } from '../types';

export function useSummaryData() {
  return useQuery<SpreadSummaryResponse>({
    queryKey: ['bond-spreads', 'summary'],
    queryFn: async () => {
      const response = await fetch('/data/bond-spreads/spreads-summary.json', { cache: 'no-cache' });
      if (!response.ok) {
        throw new Error('Failed to fetch summary data');
      }
      return response.json();
    },
    staleTime: 1000 * 60 * 60, // 1 hour
    gcTime: 1000 * 60 * 60 * 24, // 24 hours
    retry: 3,
  });
}
