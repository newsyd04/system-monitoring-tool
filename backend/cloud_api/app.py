import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

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


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print("Client connected")
    emit("connected", {"message": "Connected to WebSocket server"})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print("Client disconnected")


@socketio.on('request_metrics')
def handle_request_metrics(data):
    """Send metrics for a specific device."""
    device_id = data.get("device_id")
    if not device_id:
        emit("error", {"message": "Missing required parameter: device_id"})
        return

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
    emit("metrics_response", {"metrics": metrics})


@socketio.on('save_metric')
def handle_save_metric(data):
    """Save metrics and notify clients."""
    try:
        device_id = data["device_id"]

        conn = get_db_connection()
        cursor = conn.cursor()

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

        # Emit the new metric to all connected clients
        socketio.emit('new_metric', data)
        emit("save_success", {"message": "Metrics saved successfully"})
    except Exception as e:
        emit("error", {"message": str(e)})


if __name__ == "__main__":
    from database import init_db
    init_db()
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
