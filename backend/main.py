import eventlet
eventlet.monkey_patch()  # This must be at the very top

import sys
import logging
import threading
import os
from flask_socketio import SocketIO
from cloud_api.app import app, socketio
from collector_agent.uploader_queue import enqueue_metrics, upload_metrics, shutdown_flag
from cloud_api.database import init_db

# Global logging configuration
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("Application")

def start_background_threads():
    """Start threads for metric collection and uploading."""
    enqueue_thread = threading.Thread(target=enqueue_metrics, daemon=True)
    upload_thread = threading.Thread(target=upload_metrics, daemon=True)
    enqueue_thread.start()
    upload_thread.start()
    return [enqueue_thread, upload_thread]

class Application:
    def __init__(self):
        """Initialize the application with required configuration and logging."""
        logger.debug("Application initialized")

        # Initialize database
        logger.info("Initializing database...")
        init_db()

        # Start background threads
        logger.info("Starting background threads...")
        self.threads = start_background_threads()

    def run(self):
        """Main application logic: start the WebSocket server."""
        try:
            logger.info("Starting WebSocket server...")
            socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
        finally:
            self.shutdown()

    def shutdown(self):
        """Shut down background threads gracefully."""
        logger.info("Shutting down background threads...")
        shutdown_flag.set()  # Signal all threads to terminate
        for thread in self.threads:
            thread.join()  # Wait for threads to complete
        logger.info("Background threads shut down gracefully.")

def main():
    """Entry point for the application."""
    app_instance = Application()
    return app_instance.run()

if __name__ == "__main__":
    sys.exit(main())
