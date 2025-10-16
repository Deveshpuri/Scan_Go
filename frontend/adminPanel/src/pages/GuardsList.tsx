import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from '../../redux';
import { fetchGuards, createGuard, assignGate } from '../../redux/slices/guardsSlice';
import { Table, Modal, Pagination } from '../components';

const GuardsList = () => {
  const [createOpen, setCreateOpen] = useState(false);
  const [assignOpen, setAssignOpen] = useState(false);
  const [selectedGuardId, setSelectedGuardId] = useState<string | null>(null);
  const [newGuard, setNewGuard] = useState({ name: '', gate: '' });
  const [currentPage, setCurrentPage] = useState(1);
  const dispatch = useDispatch<AppDispatch>();
  const { guards, loading, error } = useSelector((state: RootState) => state.guards);

  useEffect(() => {
    dispatch(fetchGuards());
  }, [dispatch, currentPage]);

  const columns = [
    { key: 'name', label: 'Name', sortable: true },
    { key: 'gate', label: 'Gate', sortable: true },
    { key: 'status', label: 'Status', sortable: true },
  ];

  const actions = [
    { label: 'Assign Gate', onClick: (row: any) => {
      setSelectedGuardId(row.id);
      setAssignOpen(true);
    } },
  ];

  const handleCreate = () => {
    dispatch(createGuard(newGuard));
    setCreateOpen(false);
    setNewGuard({ name: '', gate: '' });
  };

  const handleAssign = (gate: string) => {
    if (selectedGuardId) {
      dispatch(assignGate({ id: selectedGuardId, gate }));
      setAssignOpen(false);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Guards Management</h1>
        <button
          className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600"
          onClick={() => setCreateOpen(true)}
        >
          Create Guard
        </button>
      </div>
      {loading && <div className="animate-pulse bg-gray-200 dark:bg-gray-700 h-64 rounded-lg"></div>}
      {error && (
        <div className="text-red-500 mb-4 p-4 bg-red-100 dark:bg-red-900 rounded-md">
          Error: {error} <button className="ml-2 text-blue-600 underline" onClick={() => dispatch(fetchGuards())}>Retry</button>
        </div>
      )}
      {!loading && !error && (
        <Table
          columns={columns}
          data={guards}
          actions={actions}
          totalItems={guards.length}
          currentPage={currentPage}
          onPageChange={setCurrentPage}
        />
      )}
      <Modal open={createOpen} onClose={() => setCreateOpen(false)}>
        <div className="text-center">
          <h2 className="text-lg font-semibold mb-4">Create Guard</h2>
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Name"
              value={newGuard.name}
              onChange={(e) => setNewGuard({ ...newGuard, name: e.target.value })}
              className="w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <input
              type="text"
              placeholder="Gate"
              value={newGuard.gate}
              onChange={(e) => setNewGuard({ ...newGuard, gate: e.target.value })}
              className="w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <button
              className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600"
              onClick={handleCreate}
            >
              Save
            </button>
          </div>
        </div>
      </Modal>
      <Modal open={assignOpen} onClose={() => setAssignOpen(false)}>
        <div className="text-center">
          <h2 className="text-lg font-semibold mb-4">Assign Gate</h2>
          <input
            type="text"
            placeholder="Gate"
            onChange={(e) => handleAssign(e.target.value)}
            className="w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
        </div>
      </Modal>
    </div>
  );
};

export default GuardsList;