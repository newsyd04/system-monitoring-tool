import React, { useEffect, useState } from "react";
import { io } from "socket.io-client";
import Header from "../components/Header";
import DeviceSelector from "../components/DeviceSelector";
import MetricCard from "../components/MetricCard";
import MetricGraph from "../components/MetricGraph";

const socket = io("http://localhost:5000");

export default function Dashboard() {
  const [devices, setDevices] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState("");
  const [metrics, setMetrics] = useState([]);
  const [graphData, setGraphData] = useState({ labels: [], datasets: [] });

  console.log("Graph Data:", graphData);

  // Fetch the list of devices when the component mounts
  useEffect(() => {
    fetch("http://localhost:5000/api/devices")
      .then((res) => res.json())
      .then((devices) => {
        const formattedDevices = devices.map((device) => ({
          id: device.device_id,
          name: device.name,
        }));
        setDevices(formattedDevices);

        if (formattedDevices.length > 0) {
          setSelectedDevice(formattedDevices[0].id); // Automatically select the first device
        }
      })
      .catch((err) => console.error("Error fetching devices:", err));
  }, []);

  // Fetch metrics and history for the selected device
  useEffect(() => {
    if (selectedDevice) {
      fetch(`http://localhost:5000/api/metrics?device_id=${selectedDevice}`)
        .then((res) => res.json())
        .then((data) => {
          console.log("Fetched metrics data:", data);
          processAndSetGraphData(data);
        })
        .catch((err) => console.error("Error fetching metrics:", err));
    }
  }, [selectedDevice]);

  // Handle WebSocket updates
  useEffect(() => {
    socket.on("new_metric", (newMetric) => {
      console.log("WebSocket new_metric received:", newMetric);

      if (!newMetric.device_id || newMetric.device_id !== selectedDevice) {
        console.error("Invalid or mismatched metric received:", newMetric);
        return;
      }

      // Map metrics dynamically
      const metricsMap = {
        cpu_usage: "CPU Usage",
        memory_usage: "Memory Usage",
        running_threads: "Running Threads",
      };

      Object.entries(metricsMap).forEach(([key, metricName]) => {
        if (newMetric[key] !== undefined) {
          // Update graph data
          setGraphData((prevGraphData) => {
            const updatedLabels = [...prevGraphData.labels, newMetric.timestamp || new Date().toISOString()];
            const updatedDatasets = prevGraphData.datasets.map((dataset) => {
              if (dataset.label === metricName) {
                return {
                  ...dataset,
                  data: [...dataset.data, newMetric[key]],
                };
              }
              return dataset;
            });

            // Add a new dataset if the metricName is new
            const metricExists = updatedDatasets.some((dataset) => dataset.label === metricName);
            if (!metricExists) {
              updatedDatasets.push({
                label: metricName,
                data: Array(updatedLabels.length - 1).fill(null).concat(newMetric[key]),
                borderColor: getColorForMetric(metricName),
                backgroundColor: getColorForMetric(metricName, true),
                fill: true,
              });
            }

            return {
              labels: updatedLabels,
              datasets: updatedDatasets,
            };
          });

          // Update metric cards
          setMetrics((prevMetrics) => {
            const existingMetric = prevMetrics.find((metric) => metric.name === metricName);

            if (existingMetric) {
              // Update existing metric
              return prevMetrics.map((metric) =>
                metric.name === metricName
                  ? { ...metric, value: `${newMetric[key]}` }
                  : metric
              );
            } else {
              // Add new metric
              return [
                ...prevMetrics,
                {
                  name: metricName,
                  value: `${newMetric[key]}`,
                },
              ];
            }
          });
        }
      });
    });

    return () => socket.off("new_metric");
  }, [selectedDevice]);

  // Helper function to process and set graph data
  const processAndSetGraphData = (data) => {
    const sortedData = data.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    const uniqueTimestamps = [...new Set(sortedData.map((entry) => entry.timestamp))];

    const datasets = [
      ...new Set(sortedData.map((entry) => entry.metric_name)),
    ].map((metricName) => {
      const metricData = sortedData.filter((entry) => entry.metric_name === metricName);
      const data = uniqueTimestamps.map((timestamp) => {
        const entry = metricData.find((entry) => entry.timestamp === timestamp);
        return entry ? entry.value : null;
      });
      return {
        label: metricName,
        data,
        borderColor: getColorForMetric(metricName),
        backgroundColor: getColorForMetric(metricName, true),
        fill: true,
      };
    });

    setGraphData({ labels: uniqueTimestamps, datasets });

    if (uniqueTimestamps.length > 0) {
      const latestTimestamp = uniqueTimestamps[uniqueTimestamps.length - 1];
      const latestMetrics = sortedData
        .filter((entry) => entry.timestamp === latestTimestamp)
        .map((entry) => ({
          name: entry.metric_name,
          value: `${entry.value}`,
        }));
      setMetrics(latestMetrics);
    }
  };

  // Helper function to get colors for metrics
  const getColorForMetric = (metricName, background = false) => {
    const colors = {
      "CPU Usage": "rgba(75, 192, 192, 1)",
      "Memory Usage": "rgba(192, 75, 192, 1)",
      "Running Threads": "rgba(192, 192, 75, 1)",
    };

    if (background) {
      return colors[metricName].replace("1)", "0.2)");
    }

    return colors[metricName];
  };

  return (
    <div className="min-h-screen bg-neutral-50 text-gray-900 pt-16">
      <Header />
      <div className="max-w-7xl mx-auto px-6 py-8">
        <DeviceSelector
          devices={devices}
          selectedDevice={selectedDevice}
          onSelect={(deviceId) => {
            console.log("Selected Device ID:", deviceId);
            setSelectedDevice(deviceId);
          }}
        />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
          {metrics.length > 0 ? (
            metrics.map((metric, index) => (
              <MetricCard key={`${metric.name}-${index}`} title={metric.name} value={metric.value} />
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
