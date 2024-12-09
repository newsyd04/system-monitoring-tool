import React from "react";

export default function DeviceSelector({ devices, selectedDevice, onSelect }) {
  return (
    <div id="selector" className="bg-white rounded-lg shadow p-6">
      <label htmlFor="device" className="block text-sm font-medium text-gray-600">
        Select Device:
      </label>
      <select
        id="device"
        value={selectedDevice}
        onChange={(e) => onSelect(e.target.value)}
        className="mt-2 w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {devices.map((device) => (
          <option key={device.id} value={device.id}>
            {device.name}
          </option>
        ))}
      </select>
    </div>
  );
}