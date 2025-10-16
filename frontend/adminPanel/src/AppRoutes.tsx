import { useRoutes } from 'react-router';
import { lazy, Suspense } from 'react';
import DashboardLayout from './layout/DashboardLayout';
import AdminAuthGuard from './layout/AdminAuthGuard';

// Lazy-loaded page components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const VehiclesList = lazy(() => import('./pages/VehiclesList'));
const UsersList = lazy(() => import('./pages/UsersList'));
const GuardsList = lazy(() => import('./pages/GuardsList'));
const VehicleRequests = lazy(() => import('./pages/VehicleRequests'));
const InOutLogs = lazy(() => import('./pages/InOutLogs'));
const DuesPayments = lazy(() => import('./pages/DuesPayments'));
const AuditLogs = lazy(() => import('./pages/AuditLogs'));
const Settings = lazy(() => import('./pages/Settings'));

// Route configuration
const routes = [
  {
    element: (
      <AdminAuthGuard>
        <DashboardLayout />
      </AdminAuthGuard>
    ),
    children: [
      { path: '/admin/dashboard', element: <Dashboard /> },
      { path: '/admin/vehicles', element: <VehiclesList /> },
      { path: '/admin/users', element: <UsersList /> },
      { path: '/admin/guards', element: <GuardsList /> },
      { path: '/admin/requests', element: <VehicleRequests /> },
      { path: '/admin/logs', element: <InOutLogs /> },
      { path: '/admin/dues', element: <DuesPayments /> },
      { path: '/admin/audit', element: <AuditLogs /> },
      { path: '/admin/settings', element: <Settings /> },
      { path: '*', element: <div>404 Not Found</div> }, // Fallback for unmatched routes
    ],
  },
];

const AppRoutes = () => {
  const element = useRoutes(routes);
  return <Suspense fallback={<div className="p-6">Loading...</div>}>{element}</Suspense>;
};

export default AppRoutes;