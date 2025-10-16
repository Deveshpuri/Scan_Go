import { NavLink } from 'react-router';
import { HomeIcon, TruckIcon, UserIcon, ShieldCheckIcon, DocumentTextIcon, CurrencyDollarIcon, ClockIcon, CogIcon } from '@heroicons/react/24/outline';

const navItems = [
  { name: 'Dashboard', path: '/admin/dashboard', icon: HomeIcon },
  { name: 'Vehicles', path: '/admin/vehicles', icon: TruckIcon },
  { name: 'Users', path: '/admin/users', icon: UserIcon },
  { name: 'Guards', path: '/admin/guards', icon: ShieldCheckIcon },
  { name: 'Vehicle Requests', path: '/admin/requests', icon: DocumentTextIcon },
  { name: 'In/Out Logs', path: '/admin/logs', icon: ClockIcon },
  { name: 'Dues & Payments', path: '/admin/dues', icon: CurrencyDollarIcon },
  { name: 'Audit Logs', path: '/admin/audit', icon: DocumentTextIcon },
  { name: 'Settings', path: '/admin/settings', icon: CogIcon },
];

const Sidebar = () => {
  return (
    <aside className="w-64 bg-white dark:bg-gray-800 shadow-md h-screen md:block hidden">
      <div className="p-4">
        <h2 className="text-xl font-bold text-gray-800 dark:text-white">Parking Admin</h2>
      </div>
      <nav className="mt-4">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center p-4 text-gray-700 dark:text-gray-200 hover:bg-blue-100 dark:hover:bg-blue-900 ${
                isActive ? 'bg-blue-100 dark:bg-blue-900' : ''
              }`
            }
          >
            <item.icon className="w-6 h-6 mr-2" />
            {item.name}
          </NavLink>
        ))}
      </nav>
      <div className="p-4">
        <button className="w-full text-left text-gray-700 dark:text-gray-200 hover:bg-blue-100 dark:hover:bg-blue-900 p-4">
          Logout
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;