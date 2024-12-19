from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from cloud_api.database import engine, SessionLocal
from cloud_api.models import Device, MetricType, MetricSnapshot, MetricValue
from datetime import datetime
import psycopg2

DATABASE_URL = "postgresql://metricsdb_yqja_user:entPz514UvRf9JX3KneevRRy2xpktl9v@dpg-ctf0alt2ng1s738fois0-a.oregon-postgres.render.com/metricsdb_yqja"

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    return psycopg2.connect(DATABASE_URL)

@app.route("/api/devices", methods=["GET"])
def get_devices():
    session = SessionLocal()
    devices = session.query(Device).all()
    session.close()
    return jsonify([{"device_id": d.device_id, "name": d.name} for d in devices])

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    device_id = request.args.get("device_id")
    if not device_id:
        return jsonify({"error": "Missing required parameter: device_id"}), 400  # Explicit error

    session = SessionLocal()
    try:
        snapshots = (
            session.query(MetricValue)
            .join(MetricSnapshot)
            .join(MetricType)
            .filter(MetricSnapshot.device_id == device_id)
        ).all()

        if not snapshots:  # No data found
            return jsonify({"error": "No metrics found for the specified device_id"}), 404

        # Process and return the data
        metrics = [
            {"metric_name": snapshot.type.name, "value": snapshot.value}
            for snapshot in snapshots
        ]
        return jsonify(metrics), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@app.route("/api/metrics", methods=["POST"])
def save_metrics():
    data = request.json
    session = SessionLocal()

    try:
        # Ensure device exists
        device_id = data["device_id"]
        device = session.query(Device).filter_by(device_id=device_id).first()
        if not device:
            device = Device(device_id=device_id, name=device_id, aggregator_id=1)
            session.add(device)

        # Parse and validate the timestamp
        raw_timestamp = data.get("timestamp")
        if raw_timestamp:
            try:
                timestamp = datetime.fromisoformat(raw_timestamp)
            except ValueError:
                return jsonify({"error": "Invalid timestamp format"}), 400
        else:
            timestamp = datetime.utcnow()  # Use the current UTC time if no timestamp is provided

        # Create snapshot
        snapshot = MetricSnapshot(device_id=device_id, timestamp=timestamp)
        session.add(snapshot)
        session.flush()  # Flush to generate snapshot ID

        # Save metrics (excluding device_id and timestamp)
        for metric_name, metric_value in data.items():
            if metric_name in {"device_id", "timestamp"}:
                continue  # Skip non-metric fields
            try:
                metric_value = float(metric_value)  # Ensure the metric value is a float
            except ValueError:
                return jsonify({"error": f"Invalid value for {metric_name}: {metric_value}"}), 400

            metric_type = session.query(MetricType).filter_by(name=metric_name).first()
            if not metric_type:
                metric_type = MetricType(name=metric_name)
                session.add(metric_type)
                session.flush()  # Flush to generate type ID

            metric_value = MetricValue(
                snapshot_id=snapshot.id, type_id=metric_type.id, value=metric_value
            )
            session.add(metric_value)

        session.commit()
        socketio.emit("new_metric", data)
        return jsonify({"status": "success"}), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route("/api/metrics/history", methods=["GET"])
def get_metrics_history():
    """Fetch all recorded metrics dynamically for a specific device."""
    device_id = request.args.get("device_id")
    if not device_id:
        return jsonify({"error": "Missing required parameter: device_id"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT ms.timestamp,
               dmt.name AS metric_name,
               mv.value AS metric_value
        FROM metric_snapshots ms
        JOIN metric_values mv ON ms.id = mv.snapshot_id
        JOIN device_metric_types dmt ON mv.type_id = dmt.id
        WHERE ms.device_id = %s
        ORDER BY ms.timestamp DESC;
    """
    cursor.execute(query, (device_id,))
    rows = cursor.fetchall()
    conn.close()

    # Transform rows into a dynamic structure
    history = {}
    for timestamp, metric_name, metric_value in rows:
        if timestamp not in history:
            history[timestamp] = {"timestamp": timestamp}
        history[timestamp][metric_name] = metric_value

    # Convert dictionary to a list of records
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

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print("Client connected")
    emit("connected", {"message": "Connected to WebSocket server"})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print("Client disconnected")

if __name__ == "__main__":
    from database import init_db
    init_db()
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
