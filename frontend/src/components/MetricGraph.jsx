import React from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Title, Tooltip, Legend);

const MetricGraph = ({ data }) => {
  const chartOptions = {
    plugins: {
      legend: { display: true },
      tooltip: { enabled: true },
    },
    scales: {
      x: {
        grid: { display: false },
      },
      y: {
        ticks: { beginAtZero: true },
        grid: { color: "#e5e5e5" },
      },
    },
  };

  return (
    <div id="graph" className="bg-white rounded-lg shadow p-6">
      <Line data={data} options={chartOptions} />
    </div>
  );
};

export default MetricGraph;
