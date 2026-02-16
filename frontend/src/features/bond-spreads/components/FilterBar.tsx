import { useBondSpreadsUI } from '../context/BondSpreadsUIContext';
import type { RegionFilter } from '../types';

const REGION_OPTIONS: { value: RegionFilter; label: string }[] = [
  { value: 'g20', label: 'G20' },
  { value: 'g7', label: 'G7' },
  { value: 'brics', label: 'BRICS' },
  { value: 'emerging', label: 'Emerging' },
  { value: 'all', label: 'All' },
];

export default function FilterBar() {
  const { regionFilter, setRegionFilter, searchQuery, setSearchQuery } = useBondSpreadsUI();

  return (
    <div className="filter-bar">
      <span className="filter-prompt">Filter</span>
      <input
        className="filter-input"
        type="text"
        placeholder="Search country, currency, region..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />
      <div className="filter-divider" />
      <div className="filter-tags">
        {REGION_OPTIONS.map((option) => (
          <button
            key={option.value}
            className={`filter-tag ${regionFilter === option.value ? 'active' : ''}`}
            onClick={() => setRegionFilter(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
