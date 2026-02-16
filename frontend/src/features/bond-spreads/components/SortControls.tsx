import { useBondSpreadsUI } from '../context/BondSpreadsUIContext';
import type { SortField } from '../types';

const SORT_OPTIONS: { field: SortField; label: string }[] = [
  { field: 'spread', label: 'Spread' },
  { field: 'change_1m', label: '1M Δ' },
  { field: 'country', label: 'Country' },
];

export default function SortControls() {
  const { sortBy, sortDirection, toggleSort } = useBondSpreadsUI();

  const getButtonLabel = (field: SortField, label: string) => {
    if (sortBy === field) {
      const arrow = sortDirection === 'desc' ? '↓' : '↑';
      return `${label} ${arrow}`;
    }
    return label;
  };

  return (
    <div className="section-bar">
      <div className="section-title">
        Yield Curve <span>Spreads</span>
      </div>
      <div className="sort-group">
        <span className="sort-label">Sort</span>
        {SORT_OPTIONS.map((option) => (
          <button
            key={option.field}
            className={`sort-btn ${sortBy === option.field ? 'active' : ''}`}
            onClick={() => toggleSort(option.field)}
          >
            {getButtonLabel(option.field, option.label)}
          </button>
        ))}
      </div>
    </div>
  );
}
