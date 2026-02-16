import type { EnrichedCountry } from '../types';
import SpreadCard from './SpreadCard';

interface SpreadCardListProps {
  countries: EnrichedCountry[];
}

export default function SpreadCardList({ countries }: SpreadCardListProps) {
  return (
    <div className="spread-card-list mobile-only">
      {countries.map((country) => (
        <SpreadCard key={country.code} country={country} />
      ))}
    </div>
  );
}
