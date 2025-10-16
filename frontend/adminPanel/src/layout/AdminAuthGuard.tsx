import { useSelector } from 'react-redux';
import { Navigate, Outlet } from 'react-router';
import type { RootState } from '../../redux/store';

interface AdminAuthGuardProps {
  children?: React.ReactNode;
}

const AdminAuthGuard = ({ children }: AdminAuthGuardProps) => {
  // const { user, isAuthenticated } = useSelector((state: RootState) => state.auth);

  // if (!isAuthenticated) {
  //   return <Navigate to="/login" replace />;
  // }

  // if (user?.role !== 'ADMIN') {
  //   return <Navigate to="/unauthorized" replace />;
  // }

  return children ? <>{children}</> : <Outlet />;
};

export default AdminAuthGuard;