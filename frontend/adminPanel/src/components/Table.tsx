import { useState } from 'react';
import Pagination from './Pagination';

interface TableProps<T> {
  columns: { key: string; label: string; sortable?: boolean }[];
  data: T[];
  actions?: { label: string; onClick: (row: T) => void }[];
  itemsPerPage?: number;
  totalItems: number;
  currentPage: number;
  onPageChange: (page: number) => void;
}

const Table = <T,>({ columns, data, actions, itemsPerPage = 10, totalItems, currentPage, onPageChange }: TableProps<T>) => {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const handleSort = (key: string) => {
    setSortKey(key);
    setSortOrder(sortKey === key && sortOrder === 'asc' ? 'desc' : 'asc');
  };

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-700">
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider ${
                  col.sortable ? 'cursor-pointer hover:text-gray-700 dark:hover:text-gray-100' : ''
                }`}
                onClick={() => col.sortable && handleSort(col.key)}
              >
                {col.label} {sortKey === col.key && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
            ))}
            {actions && <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Actions</th>}
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length + (actions ? 1 : 0)} className="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                No data available
              </td>
            </tr>
          ) : (
            data.map((row, index) => (
              <tr key={index}>
                {columns.map((col) => (
                  <td key={col.key} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                    {String(row[col.key as keyof T])}
                  </td>
                ))}
                {actions && (
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {actions.map((action) => (
                      <button
                        key={action.label}
                        className="text-blue-600 dark:text-blue-400 hover:underline mr-2"
                        onClick={() => action.onClick(row)}
                      >
                        {action.label}
                      </button>
                    ))}
                  </td>
                )}
              </tr>
            ))
          )}
        </tbody>
      </table>
      <Pagination
        totalItems={totalItems}
        itemsPerPage={itemsPerPage}
        currentPage={currentPage}
        onPageChange={onPageChange}
      />
    </div>
  );
};

export default Table;