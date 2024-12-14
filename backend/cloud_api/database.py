import psycopg2

DATABASE_URL = "postgresql://metricsdb_yqja_user:entPz514UvRf9JX3KneevRRy2xpktl9v@dpg-ctf0alt2ng1s738fois0-a/metricsdb_yqja"

def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aggregators (
            aggregator_id SERIAL PRIMARY KEY,
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
            device_metric_type_id SERIAL PRIMARY KEY,
            name TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metric_snapshots (
            metric_snapshot_id SERIAL PRIMARY KEY,
            device_id TEXT NOT NULL,
            client_timestamp_utc TIMESTAMP,
            client_timezone_mins INTEGER,
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

    conn.commit()
    conn.close()
