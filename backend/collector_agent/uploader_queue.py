import queue
import threading
import time
import requests
import os
from collector_agent.collector import collect_metrics
from cloud_api.app import app  # Import app for context

# Create a queue with a maximum size to prevent memory overflow
metric_queue = queue.Queue(maxsize=100)

# Event flag to signal shutdown
shutdown_flag = threading.Event()

# Use Render's assigned URL or default to localhost for local testing
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000/api/metrics")

def enqueue_metrics():
    """Collect metrics and add them to the queue."""
    while not shutdown_flag.is_set():
        try:
            metrics = collect_metrics()
            metric_queue.put(metrics, timeout=1)  # Block for 1 second if the queue is full
            print("Enqueued metrics:", metrics)
        except queue.Full:
            print("Queue is full, dropping metrics.")
        time.sleep(5)

def upload_metric(metric):
    """Upload a single metric."""
    try:
        with app.app_context():  # Ensure context for Flask features
            response = requests.post(BACKEND_URL, json=metric)
            response.raise_for_status()
            print("Metric uploaded successfully:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("Failed to upload metric, retrying:", e)
        try:
            metric_queue.put(metric, timeout=1)  # Re-enqueue the metric for retry
        except queue.Full:
            print("Queue is full, dropping metric.")

def upload_metrics():
    """Process metrics from the queue and upload them."""
    while not shutdown_flag.is_set():
        try:
            metric = metric_queue.get(timeout=1)  # Block for 1 second if the queue is empty
            upload_metric(metric)
            metric_queue.task_done()
        except queue.Empty:
            continue  # No metrics to process, continue waiting

if __name__ == "__main__":
    try:
        threading.Thread(target=enqueue_metrics, daemon=True).start()
        threading.Thread(target=upload_metrics, daemon=True).start()
        while not shutdown_flag.is_set():
            time.sleep(1)  # Keep the main thread alive
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
        shutdown_flag.set()
