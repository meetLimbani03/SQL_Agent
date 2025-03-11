"""
PostgreSQL Connector for SQL Agent
"""
import os
import time
from typing import List, Dict, Any, Optional
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PostgresConnector:
    """
    Connector for PostgreSQL database
    """
    def __init__(self):
        """
        Initialize the PostgreSQL connector
        """
        self.connection_params = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DB", "postgres"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", "postgres")
        }
        # Connection timeout in seconds (default: 10 minutes)
        self.connection_timeout = int(os.getenv("POSTGRES_CONNECTION_TIMEOUT", "600"))
        self.connection = None
        self.last_used = 0
        self.connect()
    
    def connect(self):
        """
        Connect to the PostgreSQL database
        """
        try:
            # Update last_used timestamp whenever connect is called
            self.last_used = time.time()
            
            if self.connection is None or self.connection.closed:
                self.connection = psycopg2.connect(**self.connection_params)
                print("Connected to PostgreSQL database")
            else:
                # Test if connection is still alive
                try:
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                except Exception:
                    # Connection is stale, reconnect
                    self.connection = psycopg2.connect(**self.connection_params)
                    print("Reconnected to PostgreSQL database")
        except Exception as e:
            print(f"Error connecting to PostgreSQL database: {str(e)}")
            self.connection = None

    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Execute a SQL query with safety checks to prevent database modifications
        """
        try:
            # Safety check to prevent database modifications
            query_lower = query.lower().strip()
            dangerous_keywords = ['insert', 'update', 'delete', 'drop', 'alter', 'truncate', 'create', 'replace']
            
            # Check if query contains dangerous keywords
            for keyword in dangerous_keywords:
                if query_lower.startswith(keyword) or f" {keyword} " in query_lower:
                    return {
                        "success": False, 
                        "error": f"For security reasons, {keyword.upper()} operations are not allowed"
                    }
            
            # Ensure connection is active
            self.connect()
            
            # Update last_used timestamp
            self.last_used = time.time()
                
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute(query)
            
            # For SELECT queries, fetch results
            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                # Convert to list of dicts
                data = [dict(row) for row in results]
                self.connection.commit()
                cursor.close()
                return {"success": True, "data": data}
            else:
                # For non-SELECT queries, commit and return success
                self.connection.commit()
                cursor.close()
                return {"success": True, "data": [{"message": f"Query executed successfully. Rows affected: {cursor.rowcount}"}]}
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return {"success": False, "error": str(e)}
    
    def close(self, force=False):
        """
        Close the database connection if it's been idle for too long or if force=True
        """
        current_time = time.time()
        if self.connection:
            # Close if forced or if connection has been idle for longer than timeout
            if force or (current_time - self.last_used > self.connection_timeout):
                self.connection.close()
                print("Connection to PostgreSQL database closed")
                self.connection = None
                return True
        return False
