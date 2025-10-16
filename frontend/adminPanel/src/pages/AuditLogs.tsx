import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import  type { RootState, AppDispatch } from '../../redux';
import { fetchAuditLogs } from '../../redux/slices/auditSlice';
import { FilterBar, Table, Pagination } from '../components';

const AuditLogs = () => {
  const [filters, setFilters] = useState({ date: '', action: '' });
  const [currentPage, setCurrentPage] = useState(1);
  const dispatch = useDispatch<AppDispatch>();
  const { logs, loading, error } = useSelector((state: RootState) => state.audit);

  useEffect(() => {
    dispatch(fetchAuditLogs(filters));
  }, [dispatch, filters, currentPage]);

  const columns = [
    { key: 'time', label: 'Time', sortable: true },
    { key: 'user', label: 'User', sortable: true },
    { key: 'action', label: 'Action', sortable: true },
    { key: 'details', label: 'Details', sortable: false },
  ];

  const filterOptions = [
    { key: 'date', label: 'Date', options: [{ label: 'Today', value: 'today' }, { label: 'This Week', value: 'week' }] },
    { key: 'action', label: 'Action', options: [{ label: 'Create', value: 'create' }, { label: 'Update', value: 'update' }] },
  ];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4 text-gray-800 dark:text-white">Audit Logs</h1>
      <FilterBar filters={filterOptions} onFilterChange={(key, value) => setFilters({ ...filters, [key]: value })} />
      {loading && <div className="animate-pulse bg-gray-200 dark:bg-gray-700 h-64 rounded-lg"></div>}
      {error && (
        <div className="text-red-500 mb-4 p-4 bg-red-100 dark:bg-red-900 rounded-md">
          Error: {error} <button className="ml-2 text-blue-600 underline" onClick={() => dispatch(fetchAuditLogs(filters))}>Retry</button>
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

export default AuditLogs;