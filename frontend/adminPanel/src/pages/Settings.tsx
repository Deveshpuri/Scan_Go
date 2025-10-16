import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from '../../redux';
import { fetchSettings, updateSettings } from '../../redux/slices/settingsSlice';
import { Card, ToggleSwitch } from '../components';

const Settings = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { settings, loading, error } = useSelector((state: RootState) => state.settings);
  const [form, setForm] = useState({ qrExpiry: 0, ocrEnabled: false, notificationTemplate: '' });

  useEffect(() => {
    dispatch(fetchSettings());
  }, [dispatch]);

  useEffect(() => {
    if (settings) {
      setForm({
        qrExpiry: settings.qrExpiry,
        ocrEnabled: settings.ocrEnabled,
        notificationTemplate: settings.notificationTemplate,
      });
    }
  }, [settings]);

  const handleSave = () => {
    dispatch(updateSettings(form));
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4 text-gray-800 dark:text-white">System Settings</h1>
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-gray-200 dark:bg-gray-700 h-32 rounded-lg animate-pulse"></div>
          ))}
        </div>
      )}
      {error && (
        <div className="text-red-500 mb-4 p-4 bg-red-100 dark:bg-red-900 rounded-md">
          Error: {error} <button className="ml-2 text-blue-600 underline" onClick={() => dispatch(fetchSettings())}>Retry</button>
        </div>
      )}
      {!loading && !error && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card title="QR Configuration" value={''}>
            <input
              type="number"
              value={form.qrExpiry}
              onChange={(e) => setForm({ ...form, qrExpiry: Number(e.target.value) })}
              className="w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              placeholder="QR Expiry (days)"
            />
          </Card>
          <Card title="OCR Toggle" value={''}>
            <ToggleSwitch
              checked={form.ocrEnabled}
              onChange={(checked) => setForm({ ...form, ocrEnabled: checked })}
              label="Enable OCR"
            />
          </Card>
          <Card title="Notification Templates" value={''}>
            <textarea
              value={form.notificationTemplate}
              onChange={(e) => setForm({ ...form, notificationTemplate: e.target.value })}
              className="w-full p-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              rows={5}
              placeholder="Notification template"
            />
          </Card>
          <button
            className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 mt-4"
            onClick={handleSave}
          >
            Save Changes
          </button>
        </div>
      )}
    </div>
  );
};

export default Settings;