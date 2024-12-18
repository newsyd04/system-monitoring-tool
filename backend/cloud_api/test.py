import time
import random
import requests

# Configuration
SERVER_URL = "https://system-monitoring-tool-flask-backend.onrender.com/api/metrics"
DEVICE_ID = "esp32_PIR_device"

# Helper function to simulate realistic fluctuations
def simulate_metric(value, fluctuation, min_value, max_value):
    """Simulates metric fluctuations within realistic bounds."""
    change = random.uniform(-fluctuation, fluctuation)
    new_value = value + change
    return max(min_value, min(new_value, max_value))

def generate_fake_data():
    """Generates hyper-realistic fake data for the ESP32 device."""
    # Initialize metrics with realistic starting values
    cpu_usage = random.uniform(20, 30)  # CPU usage starts between 20% and 30%
    task_count = random.randint(10, 15)  # Task count between 10 and 15
    motion_detected = 0  # PIR sensor initially detects no motion

    while True:
        # Simulate CPU usage with slight fluctuations
        cpu_usage = simulate_metric(cpu_usage, fluctuation=2, min_value=15, max_value=80)

        # Simulate task count with minimal fluctuations
        task_count = simulate_metric(task_count, fluctuation=1, min_value=10, max_value=20)

        # Simulate PIR sensor: Motion detected sporadically (10% chance of detection)
        motion_detected = 1 if random.random() < 0.1 else 0

        # Create the payload
        payload = {
            "device_id": DEVICE_ID,
            "cpu_usage": round(cpu_usage, 1),
            "task_count": task_count,
            "motion_detected": motion_detected,
        }

        # Print the generated data for debugging
        print(f"Generated data: {payload}")

        # Send the data to the server
        try:
            response = requests.post(SERVER_URL, json=payload)
            if response.status_code == 200:
                print("Data sent successfully.")
            else:
                print(f"Failed to send data. Status code: {response.status_code}, Response: {response.text}")
        except requests.RequestException as e:
            print(f"Error sending data: {e}")

        # Wait 5 seconds before sending the next set of metrics
        time.sleep(5)

if __name__ == "__main__":
    generate_fake_data()
