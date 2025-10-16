import type { ReactNode ,PropsWithChildren } from 'react';

interface CardProps {
  title: string;
  value: string | number;
  icon?: ReactNode;
  color?: string;
}

const Card = ({ title, value, icon, color = 'bg-blue-500' }:  PropsWithChildren<CardProps>) => {
  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 flex items-center">
      {icon && <div className={`mr-4 text-white p-3 rounded-full ${color}`}>{icon}</div>}
      <div>
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</h3>
        <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">{value}</p>
      </div>
    </div>
  );
};

export default Card;