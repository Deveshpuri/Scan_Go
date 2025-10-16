import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from '../../redux/store';
import { fetchVehicles, blockVehicle, fetchQrCode } from '../../redux/slices/vehiclesSlice';
import { SearchBox, Table, Modal } from '../components';

const VehiclesList = () => {
  const [search, setSearch] = useState('');
  const [qrOpen, setQrOpen] = useState(false);
  const [selectedVehicleId, setSelectedVehicleId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const dispatch = useDispatch<AppDispatch>();
  const { vehicles, qrData, loading, error } = useSelector((state: RootState) => state.vehicles);

  useEffect(() => {
    dispatch(fetchVehicles({ search }));
  }, [dispatch, search, currentPage]);

  const columns = [
    { key: 'plate', label: 'Plate', sortable: true },
    { key: 'owner', label: 'Owner', sortable: true },
    { key: 'status', label: 'Status', sortable: true },
  ];

  const actions = [
    { label: 'Block/Unblock', onClick: (row: any) => dispatch(blockVehicle(row.id)) },
    { label: 'View QR', onClick: (row: any) => {
      setSelectedVehicleId(row.id);
      dispatch(fetchQrCode(row.id));
      setQrOpen(true);
    } },
  ];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4 text-gray-800 dark:text-white">Vehicles Management</h1>
      <div className="flex mb-4">
        <SearchBox value={search} onChange={setSearch} />
      </div>
      {loading && <div className="animate-pulse bg-gray-200 dark:bg-gray-700 h-64 rounded-lg"></div>}
      {error && (
        <div className="text-red-500 mb-4 p-4 bg-red-100 dark:bg-red-900 rounded-md">
          Error: {error} <button className="ml-2 text-blue-600 underline" onClick={() => dispatch(fetchVehicles({ search }))}>Retry</button>
        </div>
      )}
      {!loading && !error && (
        <>
          <Table
            columns={columns}
            data={vehicles}
            actions={actions}
            totalItems={vehicles.length}
            currentPage={currentPage}
            onPageChange={setCurrentPage}
          />
          <Modal open={qrOpen} onClose={() => setQrOpen(false)}>
            <div className="text-center">
              <h2 className="text-lg font-semibold mb-4">Vehicle QR Code</h2>
              {qrData ? <img src={qrData} alt="QR Code" className="mx-auto" /> : <p>Loading QR...</p>}
            </div>
          </Modal>
        </>
      )}
    </div>
  );
};

export default VehiclesList;