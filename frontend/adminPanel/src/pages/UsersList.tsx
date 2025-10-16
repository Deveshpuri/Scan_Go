import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from '../../redux';
import { fetchUsers, fetchUserDetails } from '../../redux/slices/usersSlice';
import { SearchBox, Table, Modal, Pagination } from '../components';

const UsersList = () => {
  const [search, setSearch] = useState('');
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const dispatch = useDispatch<AppDispatch>();
  const { users, selectedUser, loading, error } = useSelector((state: RootState) => state.users);

  useEffect(() => {
    dispatch(fetchUsers({ search }));
  }, [dispatch, search, currentPage]);

  const columns = [
    { key: 'name', label: 'Name', sortable: true },
    { key: 'email', label: 'Email', sortable: true },
    { key: 'role', label: 'Role', sortable: true },
  ];

  const actions = [
    { label: 'View', onClick: (row: any) => {
      dispatch(fetchUserDetails(row.id));
      setDetailsOpen(true);
    } },
  ];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4 text-gray-800 dark:text-white">Users Management</h1>
      <div className="flex mb-4">
        <SearchBox value={search} onChange={setSearch} />
      </div>
      {loading && <div className="animate-pulse bg-gray-200 dark:bg-gray-700 h-64 rounded-lg"></div>}
      {error && (
        <div className="text-red-500 mb-4 p-4 bg-red-100 dark:bg-red-900 rounded-md">
          Error: {error} <button className="ml-2 text-blue-600 underline" onClick={() => dispatch(fetchUsers({ search }))}>Retry</button>
        </div>
      )}
      {!loading && !error && (
        <>
          <Table
            columns={columns}
            data={users}
            actions={actions}
            totalItems={users.length}
            currentPage={currentPage}
            onPageChange={setCurrentPage}
          />
          <Modal open={detailsOpen} onClose={() => setDetailsOpen(false)}>
            <div className="text-center">
              <h2 className="text-lg font-semibold mb-4">User Details</h2>
              {selectedUser ? (
                <div className="text-left">
                  <p><strong>Name:</strong> {selectedUser.name}</p>
                  <p><strong>Email:</strong> {selectedUser.email}</p>
                  <p><strong>Role:</strong> {selectedUser.role}</p>
                </div>
              ) : (
                <p>Loading...</p>
              )}
            </div>
          </Modal>
        </>
      )}
    </div>
  );
};

export default UsersList;