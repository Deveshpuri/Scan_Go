import { type ChangeEvent } from 'react';

interface FilterOption {
  label: string;
  value: string;
}

interface FilterBarProps {
  filters: { key: string; label: string; options: FilterOption[] }[];
  onFilterChange: (key: string, value: string) => void;
}

const FilterBar = ({ filters, onFilterChange }: FilterBarProps) => {
  return (
    <div className="flex space-x-4 mb-4">
      {filters.map((filter) => (
        <div key={filter.key} className="flex-1">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">{filter.label}</label>
          <select
            className="mt-1 block w-full border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            onChange={(e: ChangeEvent<HTMLSelectElement>) => onFilterChange(filter.key, e.target.value)}
          >
            <option value="">All</option>
            {filter.options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      ))}
    </div>
  );
};

export default FilterBar;