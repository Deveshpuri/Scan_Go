import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from '../../redux/store';
import { fetchMetrics } from '../../redux/slices/metricsSlice';
import { Card, Table } from '../components';

const Dashboard = () => {
  const dispatch = useDispatch<AppDispatch>();
  const metricsState = useSelector((state: RootState) => state.metrics);

  useEffect(() => {
    dispatch(fetchMetrics());
  }, [dispatch]);

  const columns = [
    { key: 'id', label: 'ID', sortable: true },
    { key: 'vehicle', label: 'Vehicle', sortable: true },
    { key: 'status', label: 'Status', sortable: true },
  ];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4 text-gray-800 dark:text-white">Dashboard Overview</h1>
      {metricsState.loading && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-gray-200 dark:bg-gray-700 h-24 rounded-lg animate-pulse"></div>
          ))}
        </div>
      )}
      {metricsState.error && (
        <div className="text-red-500 mb-4 p-4 bg-red-100 dark:bg-red-900 rounded-md">
          Error: {metricsState.error} <button className="ml-2 text-blue-600 underline" onClick={() => dispatch(fetchMetrics())}>Retry</button>
        </div>
      )}
      {!metricsState.loading && !metricsState.error && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card title="Total Vehicles" value={metricsState.totalVehicles || 0} />
            <Card title="Currently Inside" value={metricsState.currentlyInside || 0} />
            <Card title="Visitors Today" value={metricsState.visitorsToday || 0} />
            <Card title="Pending Requests" value={metricsState.pendingRequests || 0} />
          </div>
          <Table
            columns={columns}
            data={metricsState.recentRequests || []}
            totalItems={metricsState.recentRequests?.length || 0}
            currentPage={1}
            onPageChange={() => {}}
          />
        </>
      )}
    </div>
  );
};

export default Dashboard;