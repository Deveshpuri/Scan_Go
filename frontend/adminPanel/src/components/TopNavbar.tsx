import { useState } from 'react';
import { UserCircleIcon, Bars3Icon } from '@heroicons/react/24/outline';

const TopNavbar = () => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <header className="bg-white dark:bg-gray-800 shadow fixed w-full z-10">
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center">
          <Bars3Icon
            className="w-6 h-6 md:hidden mr-4 cursor-pointer text-gray-700 dark:text-gray-200"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          />
          <h1 className="text-lg font-semibold text-gray-800 dark:text-white">Parking Management</h1>
        </div>
        <div className="relative">
          <UserCircleIcon
            className="w-8 h-8 cursor-pointer text-gray-700 dark:text-gray-200"
            onClick={() => setDropdownOpen(!dropdownOpen)}
          />
          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 shadow-lg rounded-md py-2 z-20">
              <button className="block w-full text-left px-4 py-2 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700">
                Profile
              </button>
              <button className="block w-full text-left px-4 py-2 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700">
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
      {sidebarOpen && (
        <div className="md:hidden bg-white dark:bg-gray-800 shadow-lg">
          {/* Sidebar content duplicated for mobile */}
        </div>
      )}
    </header>
  );
};

export default TopNavbar;