import React, { useEffect, useState } from "react";
import Header from "../components/Header";
import DeviceSelector from "../components/DeviceSelector";
import MetricCard from "../components/MetricCard";
import MetricGraph from "../components/MetricGraph";

export default function Dashboard() {
  const [devices, setDevices] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState("");
  const [metrics, setMetrics] = useState([]);
  const [graphData, setGraphData] = useState({ labels: [], datasets: [] });

  console.log("Graph Data:", graphData);

  // Fetch the list of devices when the component mounts
  useEffect(() => {
    console.log("Fetching devices...");
    fetch("http://localhost:5000/api/devices")
      .then((res) => res.json())
      .then((devices) => {
        console.log("Devices Fetched:", devices);
        setDevices(devices);
        if (devices.length > 0) {
          setSelectedDevice(devices[0]); // Automatically select the first device
        }
      })
      .catch((err) => console.error("Error fetching devices:", err));
  }, []);

  

  // Fetch metrics and history for the selected device
  useEffect(() => {
    if (selectedDevice) {
      console.log("Fetching metrics for device:", selectedDevice);
      fetch(`http://localhost:5000/api/metrics?device_id=${selectedDevice}`)
        .then((res) => {
          console.log("Metrics API Response Status:", res.status);
          return res.json();
        })
        .then((data) => {
          console.log("Raw API Data:", data);

          // Update graph data
          if (data.history && Array.isArray(data.history)) {
            const labels = data.history.map((item) => item.timestamp);
            const cpuUsage = data.history.map((item) => item.cpu_usage);
            const memoryUsage = data.history.map((item) => item.memory_usage);

            setGraphData({
              labels,
              datasets: [
                {
                  label: "CPU Usage",
                  data: cpuUsage,
                  borderColor: "rgba(75, 192, 192, 1)",
                  backgroundColor: "rgba(75, 192, 192, 0.2)",
                  fill: true,
                },
                {
                  label: "Memory Usage",
                  data: memoryUsage,
                  borderColor: "rgba(192, 75, 192, 1)",
                  backgroundColor: "rgba(192, 75, 192, 0.2)",
                  fill: true,
                },
              ],
            });
            console.log("Graph Data Updated:", { labels, cpuUsage, memoryUsage });
          } else {
            console.error("Invalid or missing history data:", data.history);
            setGraphData({ labels: [], datasets: [] });
          }

          // Update metrics
          if (data.metrics && Array.isArray(data.metrics)) {
            setMetrics(data.metrics);
            console.log("Metrics Updated:", data.metrics);
          } else {
            console.error("Invalid or missing metrics data:", data.metrics);
            setMetrics([]);
          }
        })
        .catch((err) => console.error("Error fetching metrics:", err));
    }
  }, [selectedDevice]);

  return (
    <div className="min-h-screen bg-neutral-50 text-gray-900 pt-16">
      <Header />
      <div className="max-w-7xl mx-auto px-6 py-8">
        <DeviceSelector
          devices={devices}
          selectedDevice={selectedDevice}
          onSelect={(device) => {
            console.log("Selected Device:", device);
            setSelectedDevice(device);
          }}
        />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
          {metrics.length > 0 ? (
            metrics.map((metric) => (
              <MetricCard key={metric.name} title={metric.name} value={metric.value} />
            ))
          ) : (
            <p className="text-center text-gray-500">No metrics available.</p>
          )}
        </div>
        <div className="mt-12 bg-white rounded-lg shadow p-6">
          {graphData.labels.length > 0 ? (
            <MetricGraph data={graphData} />
          ) : (
            <p className="text-center text-gray-500">No data available for the graph.</p>
          )}
        </div>
      </div>
    </div>
  );
}
