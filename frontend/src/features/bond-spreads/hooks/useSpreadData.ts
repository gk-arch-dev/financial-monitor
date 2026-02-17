import { useQuery } from '@tanstack/react-query';
import type { SpreadLatestResponse } from '../types';

export function useSpreadData() {
  return useQuery<SpreadLatestResponse>({
    queryKey: ['bond-spreads', 'latest'],
    queryFn: async () => {
      const response = await fetch('/data/bond-spreads/spreads-latest.json', { cache: 'no-cache' });
      if (!response.ok) {
        throw new Error('Failed to fetch spread data');
      }
      return response.json();
    },
    staleTime: 1000 * 60 * 60, // 1 hour
    gcTime: 1000 * 60 * 60 * 24, // 24 hours
    retry: 3,
  });
}
