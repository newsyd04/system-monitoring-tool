import psutil
import socket

def get_device_id():
    """Return a unique identifier for the device (e.g., hostname)."""
    return socket.gethostname()

def collect_metrics():
    """Collect metrics and include device ID."""
    return {
        "device_id": get_device_id(),
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "running_threads": psutil.cpu_count(logical=True),  # Add the number of running threads
    }
