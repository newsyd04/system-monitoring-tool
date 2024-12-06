import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3
from database import insert_metrics, fetch_all_metrics  # Import after updating the path
from flask import Flask, request, jsonify, send_from_directory
from cloud_api.database import insert_metrics, fetch_all_metrics
DB_FILE = "metrics.db"
app = Flask(__name__, static_folder="../static")

from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/devices", methods=["GET"])
def get_devices():
    # Query the database for unique device IDs
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT device_id FROM metrics")
    devices = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(devices)

@app.route("/api/metrics", methods=["POST"])
def save_metrics():
    data = request.json
    insert_metrics(data["device_id"], data["cpu_usage"], data["memory_usage"])
    return jsonify({"status": "success"}), 200

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    device_id = request.args.get("device_id")
    start_time = request.args.get("start_time")
    end_time = request.args.get("end_time")

    query = "SELECT * FROM metrics WHERE 1=1"
    params = []

    if device_id:
        query += " AND device_id = ?"
        params.append(device_id)
    if start_time:
        query += " AND timestamp >= ?"
        params.append(start_time)
    if end_time:
        query += " AND timestamp <= ?"
        params.append(end_time)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return jsonify({"error": "Failed to fetch metrics"}), 500
    finally:
        conn.close()

    # Process the data
    history = []
    for row in rows:
        _, timestamp, device_id, cpu_usage, memory_usage = row
        history.append({
            "timestamp": timestamp,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage
        })

    # Calculate metrics
    if history:
        latest_entry = history[-1]
        metrics = [
            {"name": "CPU Usage", "value": f"{latest_entry['cpu_usage']}%"},
            {"name": "Memory Usage", "value": f"{latest_entry['memory_usage']}%"}
        ]
    else:
        metrics = [
            {"name": "CPU Usage", "value": "No data"},
            {"name": "Memory Usage", "value": "No data"}
        ]

    response = {
        "metrics": metrics,
        "history": history
    }

    # Log the response for debugging
    print(f"API Response: {response}")

    return jsonify(response)

@app.route("/")
def serve_dashboard():
    # Serve the main dashboard HTML file
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static_files(path):
    # Serve other static files like CSS and JS
    return send_from_directory(app.static_folder, path)

if __name__ == "__main__":
    from cloud_api.database import init_db
    init_db()
    app.run(host="0.0.0.0", port=5000)
