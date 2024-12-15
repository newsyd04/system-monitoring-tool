import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO

DATABASE_URL = "postgresql://metricsdb_yqja_user:entPz514UvRf9JX3KneevRRy2xpktl9v@dpg-ctf0alt2ng1s738fois0-a.oregon-postgres.render.com/metricsdb_yqja"

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    return psycopg2.connect(DATABASE_URL)


@app.route("/api/devices", methods=["GET"])
def get_devices():
    """Fetch all unique devices with their aggregators."""
    conn = get_db_connection()
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

    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT dmt.name AS metric_name, mv.value
        FROM metric_values mv
        JOIN (
            SELECT ms.metric_snapshot_id
            FROM metric_snapshots ms
            WHERE ms.device_id = %s
            ORDER BY ms.client_timestamp_utc DESC
            LIMIT 1
        ) latest_snapshot ON mv.metric_snapshot_id = latest_snapshot.metric_snapshot_id
        JOIN device_metric_types dmt ON mv.device_metric_type_id = dmt.device_metric_type_id
    """
    cursor.execute(query, (device_id,))
    rows = cursor.fetchall()
    conn.close()

    metrics = [{"metric_name": row[0], "value": row[1]} for row in rows]
    return jsonify(metrics)


@app.route("/api/metrics", methods=["POST"])
def save_metrics():
    """Save metrics and emit updates to connected clients."""
    try:
        data = request.json
        device_id = data["device_id"]

        conn = get_db_connection()
        cursor = conn.cursor()

        # Ensure the aggregator exists
        cursor.execute("""
            INSERT INTO aggregators (aggregator_id, guid, name)
            VALUES (%s, %s, %s)
            ON CONFLICT (aggregator_id) DO NOTHING
        """, (1, "default-guid", "Default Aggregator"))

        # Ensure the device exists
        cursor.execute("""
            INSERT INTO devices (device_id, aggregator_id, name, ordinal)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (device_id) DO NOTHING
        """, (device_id, 1, device_id, 0))

        # Insert metric snapshot
        cursor.execute("""
            INSERT INTO metric_snapshots (device_id, client_timestamp_utc, client_timezone_mins)
            VALUES (%s, NOW(), 0)
            RETURNING metric_snapshot_id
        """, (device_id,))
        metric_snapshot_id = cursor.fetchone()[0]

        # Insert all metric values dynamically
        cursor.execute("SELECT * FROM device_metric_types;")
        print("Device Metric Types in DB:", cursor.fetchall())  # Debugging

        metric_types = {
            "cpu_usage": 1,
            "memory_usage": 2,
            "running_threads": 3,
        }

        for metric_key, metric_id in metric_types.items():
            if metric_key in data:
                cursor.execute("""
                    INSERT INTO metric_values (metric_snapshot_id, device_metric_type_id, value)
                    VALUES (%s, %s, %s)
                """, (metric_snapshot_id, metric_id, data[metric_key]))

        conn.commit()
        conn.close()

        # Emit the new metric to connected clients
        socketio.emit('new_metric', data)
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print("Error in save_metrics:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/metrics/history", methods=["GET"])
def get_metrics_history():
    """Fetch all metric uploads sorted by upload time for a specific device."""
    device_id = request.args.get("device_id")
    if not device_id:
        return jsonify({"error": "Missing required parameter: device_id"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Updated query
    query = """
        SELECT ms.client_timestamp_utc,
               mv.value AS metric_value,
               dmt.name AS metric_name
        FROM metric_snapshots ms
        JOIN metric_values mv ON ms.metric_snapshot_id = mv.metric_snapshot_id
        JOIN device_metric_types dmt ON mv.device_metric_type_id = dmt.device_metric_type_id
        WHERE ms.device_id = %s
        ORDER BY ms.client_timestamp_utc DESC;
    """
    cursor.execute(query, (device_id,))
    rows = cursor.fetchall()
    conn.close()

    # Transform rows into the desired structure
    history = {}
    for row in rows:
        timestamp, metric_value, metric_name = row
        if timestamp not in history:
            history[timestamp] = {
                "timestamp": timestamp,
                "cpu_usage": "N/A",
                "memory_usage": "N/A",
                "running_threads": "N/A",
            }
        history[timestamp][metric_name] = metric_value

    # Convert dict to a list of dictionaries
    result = list(history.values())
    return jsonify(result)


@app.route("/api/device/reboot", methods=["POST"])
def send_test_message():
    """Send a test message to the ESP32."""
    device_id = request.json.get("device_id")
    if not device_id:
        return jsonify({"error": "Device ID is required"}), 400

    # Emit test_message instead of reboot_command
    socketio.emit("test_message", {"device_id": device_id})
    return jsonify({"status": "success", "message": f"Test message sent to device {device_id}"}), 200


if __name__ == "__main__":
    from database import init_db
    init_db()
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
