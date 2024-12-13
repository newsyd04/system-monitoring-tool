import sys
import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import eventlet

DB_FILE = "metrics.db"

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/api/devices", methods=["GET"])
def get_devices():
    """Fetch all unique devices with their aggregators."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    query = """
        SELECT d.device_id, d.name, a.name AS aggregator_name
        FROM devices d
        LEFT JOIN aggregators a ON d.aggregator_id = a.aggregator_id
    """
    cursor.execute(query)
    devices = [
        {"device_id": row[0], "name": row[1], "aggregator_name": row[2] or "None"}
        for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify(devices)

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    """Fetch the most recent metrics for a specific device."""
    device_id = request.args.get("device_id")
    if not device_id:
        return jsonify({"error": "Missing required parameter: device_id"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Query to get the most recent metric value for each type
    query = """
        SELECT dmt.name AS metric_name, mv.value
        FROM metric_values mv
        JOIN metric_snapshots ms ON mv.metric_snapshot_id = ms.metric_snapshot_id
        JOIN device_metric_types dmt ON mv.device_metric_type_id = dmt.device_metric_type_id
        WHERE ms.device_id = ?
        AND ms.client_timestamp_utc = (
            SELECT MAX(ms2.client_timestamp_utc)
            FROM metric_snapshots ms2
            WHERE ms2.device_id = ms.device_id
        )
        GROUP BY dmt.name
    """
    cursor.execute(query, (device_id,))
    rows = cursor.fetchall()
    conn.close()

    # Format the response
    metrics = [{"metric_name": row[0], "value": row[1]} for row in rows]
    return jsonify(metrics)


@app.route("/api/metrics", methods=["POST"])
def save_metrics():
    """Save metrics and emit updates to connected clients."""
    data = request.json
    device_id = data["device_id"]
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

    # Insert all metric values dynamically
    metric_types = {
        "cpu_usage": 1,
        "memory_usage": 2,
        "running_threads": 3,
    }

    for metric_key, metric_id in metric_types.items():
        if metric_key in data:
            cursor.execute("""
                INSERT INTO metric_values (metric_snapshot_id, device_metric_type_id, value)
                VALUES (?, ?, ?)
            """, (metric_snapshot_id, metric_id, data[metric_key]))

    conn.commit()
    conn.close()

    # Emit the new metric to connected clients
    socketio.emit('new_metric', data)
    return jsonify({"status": "success"}), 200


@app.route("/api/metrics/history", methods=["GET"])
def get_metrics_history():
    """Fetch all metric uploads sorted by upload time."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    query = """
        SELECT ms.client_timestamp_utc, d.device_id, d.name, mv.value, dmt.name AS metric_name
        FROM metric_snapshots ms
        JOIN devices d ON ms.device_id = d.device_id
        JOIN metric_values mv ON ms.metric_snapshot_id = mv.metric_snapshot_id
        JOIN device_metric_types dmt ON mv.device_metric_type_id = dmt.device_metric_type_id
        ORDER BY ms.client_timestamp_utc DESC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    history = [
        {"timestamp": row[0], "device_id": row[1], "device_name": row[2], "metric": row[4], "value": row[3]}
        for row in rows
    ]
    return jsonify(history)


@app.route("/api/device/reboot", methods=["POST"])
def reboot_device():
    """Handle device reboot commands."""
    device_id = request.json.get("device_id")
    if not device_id:
        return jsonify({"error": "Device ID is required"}), 400

    # Emit a socket event to the device
    socketio.emit("reboot_command", {"device_id": device_id})
    return jsonify({"status": "success", "message": f"Reboot command sent to device {device_id}"}), 200


if __name__ == "__main__":
    from database import init_db
    init_db()
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), allow_unsafe_werkzeug=True)
