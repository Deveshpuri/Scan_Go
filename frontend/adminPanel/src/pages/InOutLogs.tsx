import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from '../../redux';
import { fetchLogs, exportLogs } from '../../redux/slices/logsSlice';
import { FilterBar, SearchBox, Table, Pagination } from '../components';

const InOutLogs = () => {
  const [filters, setFilters] = useState({ date: '', guard: '', vehicle: '' });
  const [search, setSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const dispatch = useDispatch<AppDispatch>();
  const { logs, loading, error } = useSelector((state: RootState) => state.logs);

  useEffect(() => {
    dispatch(fetchLogs({ ...filters, vehicle: search }));
  }, [dispatch, filters, search, currentPage]);

  const columns = [
    { key: 'time', label: 'Time', sortable: true },
    { key: 'vehicle', label: 'Vehicle', sortable: true },
    { key: 'guard', label: 'Guard', sortable: true },
    { key: 'action', label: 'Action', sortable: true },
  ];

  const filterOptions = [
    { key: 'date', label: 'Date', options: [{ label: 'Today', value: 'today' }, { label: 'This Week', value: 'week' }] },
    { key: 'guard', label: 'Guard', options: [{ label: 'Guard 1', value: 'guard1' }, { label: 'Guard 2', value: 'guard2' }] },
  ];

  const handleExport = () => {
    dispatch(exportLogs()).then((result) => {
      const url = window.URL.createObjectURL(result.payload);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'logs.csv';
      link.click();
      window.URL.revokeObjectURL(url);
    });
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4 text-gray-800 dark:text-white">Access Logs</h1>
      <div className="flex mb-4 space-x-4">
        <FilterBar filters={filterOptions} onFilterChange={(key, value) => setFilters({ ...filters, [key]: value })} />
        <SearchBox value={search} onChange={setSearch} />
        <button
          className="bg-green-500 text-white px-4 py-2 rounded-md hover:bg-green-600"
          onClick={handleExport}
        >
          Export CSV
        </button>
      </div>
      {loading && <div className="animate-pulse bg-gray-200 dark:bg-gray-700 h-64 rounded-lg"></div>}
      {error && (
        <div className="text-red-500 mb-4 p-4 bg-red-100 dark:bg-red-900 rounded-md">
          Error: {error} <button className="ml-2 text-blue-600 underline" onClick={() => dispatch(fetchLogs({ ...filters, vehicle: search }))}>Retry</button>
        </div>
      )}
      {!loading && !error && (
        <Table
          columns={columns}
          data={logs}
          totalItems={logs.length}
          currentPage={currentPage}
          onPageChange={setCurrentPage}
        />
      )}
    </div>
  );
};

export default InOutLogs;