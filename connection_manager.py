"""
Connection manager for SQL Agent
"""
import time
import threading
from typing import Optional

class ConnectionManager:
    """
    Manages database connections to ensure they're closed after a period of inactivity
    """
    def __init__(self, db_connector, idle_timeout: int = 600):
        """
        Initialize the connection manager
        
        Args:
            db_connector: The database connector instance
            idle_timeout: Time in seconds after which to close idle connections (default: 10 minutes)
        """
        self.db_connector = db_connector
        self.idle_timeout = idle_timeout
        self.last_activity = time.time()
        self.monitor_thread = None
        self.stop_monitor = False
        
        # Start the connection monitor thread
        self.start_monitor()
    
    def update_activity(self):
        """
        Update the last activity timestamp
        """
        self.last_activity = time.time()
    
    def start_monitor(self):
        """
        Start the connection monitor thread
        """
        if self.monitor_thread is None:
            self.stop_monitor = False
            self.monitor_thread = threading.Thread(target=self._monitor_connection, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitor_thread(self):
        """
        Stop the connection monitor thread
        """
        if self.monitor_thread is not None:
            self.stop_monitor = True
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None
    
    def _monitor_connection(self):
        """
        Monitor the database connection and close it if idle for too long
        """
        while not self.stop_monitor:
            current_time = time.time()
            if current_time - self.last_activity > self.idle_timeout:
                # Connection has been idle for too long, close it
                self.db_connector.close(force=True)
                print(f"Closed idle database connection after {self.idle_timeout} seconds")
            
            # Check every 30 seconds
            time.sleep(30)
    
    def __del__(self):
        """
        Clean up resources when the object is destroyed
        """
        self.stop_monitor_thread()
        self.db_connector.close(force=True)
