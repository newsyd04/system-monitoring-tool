import sqlite3

DB_FILE = "metrics.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aggregators (
            aggregator_id INTEGER PRIMARY KEY,
            guid TEXT NOT NULL,
            name TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            device_id TEXT PRIMARY KEY,
            aggregator_id INTEGER NOT NULL,
            name TEXT,
            ordinal INTEGER,
            FOREIGN KEY (aggregator_id) REFERENCES aggregators(aggregator_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS device_metric_types (
            device_metric_type_id INTEGER PRIMARY KEY,
            device_id INTEGER NOT NULL,
            name TEXT,
            FOREIGN KEY (device_id) REFERENCES devices(device_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metric_snapshots (
            metric_snapshot_id INTEGER PRIMARY KEY,
            device_id INTEGER NOT NULL,
            client_timestamp_utc DATETIME,
            client_timezone_mins INTEGER,
            server_timestamp_utc DATETIME,
            server_timezone_mins INTEGER,
            FOREIGN KEY (device_id) REFERENCES devices(device_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metric_values (
            metric_snapshot_id INTEGER NOT NULL,
            device_metric_type_id INTEGER NOT NULL,
            value DECIMAL,
            PRIMARY KEY (metric_snapshot_id, device_metric_type_id),
            FOREIGN KEY (metric_snapshot_id) REFERENCES metric_snapshots(metric_snapshot_id),
            FOREIGN KEY (device_metric_type_id) REFERENCES device_metric_types(device_metric_type_id)
        )
    """)

    # Insert default metric types (CPU and memory)
    cursor.execute("""
        INSERT OR IGNORE INTO device_metric_types (device_metric_type_id, device_id, name)
        VALUES (1, 0, 'CPU Usage'), (2, 0, 'Memory Usage')
    """)

    conn.commit()
    conn.close()
