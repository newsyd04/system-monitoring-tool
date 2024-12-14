import psycopg2

DATABASE_URL = "postgresql://metricsdb_yqja_user:entPz514UvRf9JX3KneevRRy2xpktl9v@dpg-ctf0alt2ng1s738fois0-a.oregon-postgres.render.com/metricsdb_yqja"

def test_connection():
    try:
        # Establish a connection to the database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        # Execute a simple query to check the connection
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        print("Database connection successful. Test query result:", result)

        # Close the connection
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        print("Error connecting to the database:", e)

if __name__ == "__main__":
    test_connection()
