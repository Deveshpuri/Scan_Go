import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from '../../redux';
import { fetchRequests, approveRequest, rejectRequest } from '../../redux/slices/requestsSlice';
import { FilterBar, Table, Modal, Pagination } from '../components';

const VehicleRequests = () => {
  const [filter, setFilter] = useState({ status: '' });
  const [modalOpen, setModalOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const dispatch = useDispatch<AppDispatch>();
  const { requests, loading, error } = useSelector((state: RootState) => state.requests);

  useEffect(() => {
    dispatch(fetchRequests(filter));
  }, [dispatch, filter, currentPage]);

  const columns = [
    { key: 'vehicle', label: 'Vehicle', sortable: true },
    { key: 'owner', label: 'Owner', sortable: true },
    { key: 'status', label: 'Status', sortable: true },
  ];

  const actions = [
    { label: 'Approve', onClick: (row: any) => dispatch(approveRequest(row.id)) },
    { label: 'Reject', onClick: (row: any) => {
      setSelectedRequestId(row.id);
      setModalOpen(true);
    } },
  ];

  const filters = [
    {
      key: 'status',
      label: 'Status',
      options: [
        { label: 'Pending', value: 'pending' },
        { label: 'Approved', value: 'approved' },
        { label: 'Rejected', value: 'rejected' },
      ],
    },
  ];

  const handleReject = () => {
    if (selectedRequestId) {
      dispatch(rejectRequest({ id: selectedRequestId, reason: rejectReason }));
      setModalOpen(false);
      setRejectReason('');
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4 text-gray-800 dark:text-white">Vehicle Requests</h1>
      <FilterBar filters={filters} onFilterChange={(key, value) => setFilter({ ...filter, [key]: value })} />
      {loading && <div className="animate-pulse bg-gray-200 dark:bg-gray-700 h-64 rounded-lg"></div>}
      {error && (
        <div className="text-red-500 mb-4 p-4 bg-red-100 dark:bg-red-900 rounded-md">
          Error: {error} <button className="ml-2 text-blue-600 underline" onClick={() => dispatch(fetchRequests(filter))}>Retry</button>
        </div>
      )}
      {!loading && !error && (
        <>
          <Table
            columns={columns}
            data={requests}
            actions={actions}
            totalItems={requests.length}
            currentPage={currentPage}
            onPageChange={setCurrentPage}
          />
          <Modal open={modalOpen} onClose={() => setModalOpen(false)}>
            <div className="text-center">
              <h2 className="text-lg font-semibold mb-4">Reject Request</h2>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Reason for rejection"
                className="w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                rows={4}
              />
              <button
                className="mt-4 bg-red-500 text-white px-4 py-2 rounded-md hover:bg-red-600"
                onClick={handleReject}
              >
                Submit
              </button>
            </div>
          </Modal>
        </>
      )}
    </div>
  );
};

export default VehicleRequests;