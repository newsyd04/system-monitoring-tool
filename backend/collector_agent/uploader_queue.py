
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collector import collect_metrics  # Import after updating the path

import threading
import queue
import time
import requests
from collector_agent.collector import collect_metrics

metric_queue = queue.Queue()

def enqueue_metrics():
    while True:
        metrics = collect_metrics()
        metric_queue.put(metrics)
        time.sleep(3)

def upload_metrics():
    while True:
        if not metric_queue.empty():
            metrics = metric_queue.get()
            try:
                print("Uploading metrics:", metrics)  # Debugging
                response = requests.post("http://localhost:5000/api/metrics", json=metrics)
                print("Response status:", response.status_code)
                print("Response text:", response.text)
            except Exception as e:
                print("Failed to upload metrics:", e)

if __name__ == "__main__":
    threading.Thread(target=enqueue_metrics, daemon=True).start()
    threading.Thread(target=upload_metrics, daemon=True).start()
    while True:
        time.sleep(1)  # Keep main thread alive
