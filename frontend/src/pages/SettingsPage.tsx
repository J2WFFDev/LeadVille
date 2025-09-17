/**
 * Settings and configuration page
 */

export const SettingsPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">
          System Settings
        </h1>
        <p className="text-gray-600">
          Configuration and system parameters
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* WebSocket Configuration */}
        <div className="panel">
          <div className="panel-header">
            WebSocket Configuration
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                WebSocket URL
              </label>
              <input
                type="text"
                defaultValue="ws://192.168.1.124:8001"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-leadville-primary focus:border-transparent"
                readOnly
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Reconnect Interval (ms)
              </label>
              <input
                type="number"
                defaultValue="3000"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-leadville-primary focus:border-transparent"
                readOnly
              />
            </div>
          </div>
        </div>

        {/* Timer Configuration */}
        <div className="panel">
          <div className="panel-header">
            Timer Settings
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Timer Vendor
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-leadville-primary focus:border-transparent">
                <option value="amg_labs">AMG Labs Commander</option>
                <option value="specialpie">SpecialPie Pro Timer</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Device ID
              </label>
              <input
                type="text"
                defaultValue="60:09:C3:1F:DC:1A"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-leadville-primary focus:border-transparent font-mono"
                readOnly
              />
            </div>
          </div>
        </div>

        {/* Sensor Configuration */}
        <div className="panel">
          <div className="panel-header">
            Sensor Settings
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Detection Threshold (g)
              </label>
              <input
                type="number"
                defaultValue="10.0"
                step="0.1"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-leadville-primary focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Calibration Samples
              </label>
              <input
                type="number"
                defaultValue="100"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-leadville-primary focus:border-transparent"
              />
            </div>
          </div>
        </div>

        {/* System Information */}
        <div className="panel">
          <div className="panel-header">
            System Information
          </div>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Version:</span>
              <span className="font-mono">2.0.0</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Build:</span>
              <span className="font-mono">Production</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Platform:</span>
              <span className="font-mono">React + Vite + TypeScript</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Backend:</span>
              <span className="font-mono">Python WebSocket Server</span>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-4">
        <button className="btn-primary">
          Save Settings
        </button>
        <button className="btn-secondary">
          Reset to Defaults
        </button>
      </div>
    </div>
  );
};