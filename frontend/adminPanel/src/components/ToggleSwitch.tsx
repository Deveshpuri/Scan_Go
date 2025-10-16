interface ToggleSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
}

const ToggleSwitch = ({ checked, onChange, label }: ToggleSwitchProps) => {
  return (
    <div className="flex items-center">
      {label && <label className="mr-2 text-sm font-medium text-gray-700 dark:text-gray-300">{label}</label>}
      <div className="relative inline-flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          className="sr-only"
        />
        <div
          className={`w-11 h-6 bg-gray-200 rounded-full transition-colors duration-200 ease-in-out ${
            checked ? 'bg-blue-600' : ''
          }`}
        >
          <div
            className={`w-5 h-5 bg-white rounded-full shadow transform transition-transform duration-200 ease-in-out ${
              checked ? 'translate-x-5' : 'translate-x-0'
            }`}
          />
        </div>
      </div>
    </div>
  );
};

export default ToggleSwitch;