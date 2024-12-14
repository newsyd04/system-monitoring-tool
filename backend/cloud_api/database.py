import psycopg2

DATABASE_URL = "postgresql://metricsdb_yqja_user:entPz514UvRf9JX3KneevRRy2xpktl9v@dpg-ctf0alt2ng1s738fois0-a.oregon-postgres.render.com/metricsdb_yqja"

def init_db():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        # Create tables
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
                name TEXT UNIQUE NOT NULL
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

        # Check and insert default metric types
        metric_types = ['cpu_usage', 'memory_usage', 'running_threads']
        for metric in metric_types:
            cursor.execute("SELECT COUNT(*) FROM device_metric_types WHERE name = %s", (metric,))
            exists = cursor.fetchone()[0]
            if not exists:
                cursor.execute("INSERT INTO device_metric_types (name) VALUES (%s)", (metric,))

        # Check and insert default aggregator
        cursor.execute("SELECT COUNT(*) FROM aggregators WHERE aggregator_id = %s", (1,))
        exists = cursor.fetchone()[0]
        if not exists:
            cursor.execute("""
                INSERT INTO aggregators (aggregator_id, guid, name)
                VALUES (%s, %s, %s)
            """, (1, "default-guid", "Default Aggregator"))

        conn.commit()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print("Error initializing database:", str(e))
