import sqlite3

DB_FILE = "metrics.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            device_id TEXT,
            cpu_usage REAL,
            memory_usage REAL
        )
    """)
    conn.commit()
    conn.close()

def insert_metrics(device_id, cpu_usage, memory_usage):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO metrics (device_id, cpu_usage, memory_usage)
        VALUES (?, ?, ?)
    """, (device_id, cpu_usage, memory_usage))
    conn.commit()
    conn.close()


def fetch_all_metrics():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM metrics")
    data = cursor.fetchall()
    conn.close()
    return data
