import { useQuery } from '@tanstack/react-query';
import type { SpreadHistoryResponse } from '../types';

export function useHistoryData() {
  return useQuery<SpreadHistoryResponse>({
    queryKey: ['bond-spreads', 'history'],
    queryFn: async () => {
      const response = await fetch('/data/bond-spreads/spreads-history.json');
      if (!response.ok) {
        throw new Error('Failed to fetch history data');
      }
      return response.json();
    },
    staleTime: 1000 * 60 * 60, // 1 hour
    gcTime: 1000 * 60 * 60 * 24, // 24 hours
    retry: 3,
  });
}
