import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type{  RootState, AppDispatch } from '../../redux';
import { fetchDues, markDuePaid, blockVehicleForDue } from '../../redux/slices/duesSlice';
import { Table, Modal, Pagination } from '../components';

const DuesPayments = () => {
  const [paidOpen, setPaidOpen] = useState(false);
  const [blockOpen, setBlockOpen] = useState(false);
  const [selectedDueId, setSelectedDueId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const dispatch = useDispatch<AppDispatch>();
  const { dues, loading, error } = useSelector((state: RootState) => state.dues);

  useEffect(() => {
    dispatch(fetchDues());
  }, [dispatch, currentPage]);

  const columns = [
    { key: 'vehicle', label: 'Vehicle', sortable: true },
    { key: 'amount', label: 'Amount', sortable: true },
    { key: 'dueDate', label: 'Due Date', sortable: true },
    { key: 'status', label: 'Status', sortable: true },
  ];

  const actions = [
    { label: 'Mark Paid', onClick: (row: any) => {
      setSelectedDueId(row.id);
      setPaidOpen(true);
    } },
    { label: 'Block Vehicle', onClick: (row: any) => {
      setSelectedDueId(row.id);
      setBlockOpen(true);
    } },
  ];

  const handleMarkPaid = () => {
    if (selectedDueId) {
      dispatch(markDuePaid(selectedDueId));
      setPaidOpen(false);
    }
  };

  const handleBlockVehicle = () => {
    if (selectedDueId) {
      dispatch(blockVehicleForDue(selectedDueId));
      setBlockOpen(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4 text-gray-800 dark:text-white">Dues Management</h1>
      {loading && <div className="animate-pulse bg-gray-200 dark:bg-gray-700 h-64 rounded-lg"></div>}
      {error && (
        <div className="text-red-500 mb-4 p-4 bg-red-100 dark:bg-red-900 rounded-md">
          Error: {error} <button className="ml-2 text-blue-600 underline" onClick={() => dispatch(fetchDues())}>Retry</button>
        </div>
      )}
      {!loading && !error && (
        <>
          <Table
            columns={columns}
            data={dues}
            actions={actions}
            totalItems={dues.length}
            currentPage={currentPage}
            onPageChange={setCurrentPage}
          />
          <Modal open={paidOpen} onClose={() => setPaidOpen(false)}>
            <div className="text-center">
              <h2 className="text-lg font-semibold mb-4">Mark as Paid</h2>
              <p>Confirm marking this due as paid?</p>
              <button
                className="mt-4 bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600"
                onClick={handleMarkPaid}
              >
                Confirm
              </button>
            </div>
          </Modal>
          <Modal open={blockOpen} onClose={() => setBlockOpen(false)}>
            <div className="text-center">
              <h2 className="text-lg font-semibold mb-4">Block Vehicle</h2>
              <p>Confirm blocking this vehicle?</p>
              <button
                className="mt-4 bg-red-500 text-white px-4 py-2 rounded-md hover:bg-red-600"
                onClick={handleBlockVehicle}
              >
                Confirm
              </button>
            </div>
          </Modal>
        </>
      )}
    </div>
  );
};

export default DuesPayments;