import sys
import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO

DB_FILE = "metrics.db"

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/api/devices", methods=["GET"])
def get_devices():
    """Fetch all unique devices."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT device_id, name FROM devices")
    devices = [{"device_id": row[0], "name": row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(devices)


@app.route("/api/metrics", methods=["POST"])
def save_metrics():
    """Save metrics and emit updates to connected clients."""
    data = request.json
    device_id = data["device_id"]
    cpu_usage = data["cpu_usage"]
    memory_usage = data["memory_usage"]
    running_threads = data["running_threads"]

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Ensure the device exists
    cursor.execute("""
        INSERT OR IGNORE INTO devices (device_id, aggregator_id, name, ordinal)
        VALUES (?, 1, ?, 0)
    """, (device_id, device_id))

    # Insert metric snapshot
    cursor.execute("""
        INSERT INTO metric_snapshots (device_id, client_timestamp_utc, client_timezone_mins)
        VALUES (?, datetime('now'), 0)
    """, (device_id,))
    metric_snapshot_id = cursor.lastrowid

    # Insert metric values
    cursor.execute("""
        INSERT INTO metric_values (metric_snapshot_id, device_metric_type_id, value)
        VALUES (?, 1, ?)
    """, (metric_snapshot_id, cpu_usage))
    cursor.execute("""
        INSERT INTO metric_values (metric_snapshot_id, device_metric_type_id, value)
        VALUES (?, 2, ?)
    """, (metric_snapshot_id, memory_usage))
    cursor.execute("""
        INSERT INTO metric_values (metric_snapshot_id, device_metric_type_id, value)
        VALUES (?, 3, ?)
    """, (metric_snapshot_id, running_threads))

    conn.commit()
    conn.close()

    # Emit the new metric to connected clients
    socketio.emit('new_metric', data)

    return jsonify({"status": "success"}), 200

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    """Fetch metrics for a specific device."""
    device_id = request.args.get("device_id")
    if not device_id:
        return jsonify({"error": "Missing required parameter: device_id"}), 400  # Enforce device_id

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    query = """
        SELECT ms.client_timestamp_utc, dmt.name, mv.value
        FROM metric_snapshots ms
        JOIN metric_values mv ON ms.metric_snapshot_id = mv.metric_snapshot_id
        JOIN device_metric_types dmt ON mv.device_metric_type_id = dmt.device_metric_type_id
        WHERE ms.device_id = ?
        ORDER BY ms.client_timestamp_utc DESC
    """
    cursor.execute(query, (device_id,))
    rows = cursor.fetchall()
    conn.close()

    # Structure the response
    metrics = []
    for row in rows:
        metrics.append({
            "timestamp": row[0],
            "metric_name": row[1],
            "value": row[2]
        })

    return jsonify(metrics)

if __name__ == "__main__":
    from database import init_db
    init_db()
    socketio.run(app, host="0.0.0.0", port=5000)
