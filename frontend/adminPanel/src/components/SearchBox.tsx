import { useState, useEffect } from 'react';
import { debounce } from 'lodash';

interface SearchBoxProps {
  value: string;
  onChange: (value: string) => void;
}

const SearchBox = ({ value, onChange }: SearchBoxProps) => {
  const [input, setInput] = useState(value);

  const debouncedSearch = debounce((val: string) => onChange(val), 500);

  useEffect(() => {
    debouncedSearch(input);
    return () => debouncedSearch.cancel();
  }, [input]);

  return (
    <div className="relative w-full max-w-xs">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Search..."
        className="w-full pl-10 pr-4 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
      />
      <svg
        className="absolute left-3 top-3 h-5 w-5 text-gray-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    </div>
  );
};

export default SearchBox;