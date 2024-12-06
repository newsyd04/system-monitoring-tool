import React from "react";

export default function MetricCard({ title, value }) {
  return (
    <div id="metric" className="bg-white rounded-lg shadow p-6 text-center hover:shadow-lg transition-shadow">
      <h3 className="text-xl font-semibold text-gray-700">{title}</h3>
      <p className="text-4xl font-bold text-gray-900 mt-2">{value}</p>
    </div>
  );
}
