"""
PostgreSQL Connector for SQL Agent
"""
import streamlit as st
import os
import time
from typing import Dict, Any
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
        try:
            print("Initializing PostgreSQL connector")
            # Check if we have secrets available
            if "postgres" not in st.secrets:
                print("WARNING: 'postgres' section not found in st.secrets")
                print(f"Available secret sections: {list(st.secrets.keys())}")
                
            self.connection_params = {
                "host": st.secrets["postgres"]["POSTGRES_HOST"],
                "port": st.secrets["postgres"]["POSTGRES_PORT"],
                "database": st.secrets["postgres"]["POSTGRES_DB"],
                "user": st.secrets["postgres"]["POSTGRES_USER"],
                "password": st.secrets["postgres"]["POSTGRES_PASSWORD"]
            }
            # Connection timeout in seconds (default: 10 minutes)
            self.connection_timeout = int(os.getenv("POSTGRES_CONNECTION_TIMEOUT", "600"))
            self.connection = None
            self.last_used = 0
            self.connect()
        except Exception as e:
            import traceback
            print(f"Error initializing PostgreSQL connector: {str(e)}")
            print(f"Initialization error details: {traceback.format_exc()}")
            raise
    
    def connect(self):
        """
        Connect to the PostgreSQL database
        """
        try:
            # Update last_used timestamp whenever connect is called
            self.last_used = time.time()
            
            # Print connection parameters (without password)
            safe_params = self.connection_params.copy()
            safe_params["password"] = "*****"
            print(f"Attempting to connect with parameters: {safe_params}")
            
            if self.connection is None or self.connection.closed:
                self.connection = psycopg2.connect(**self.connection_params)
                print("Connected to PostgreSQL database successfully")
            else:
                # Test if connection is still alive
                try:
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    print("Existing connection is still valid")
                except Exception as conn_test_error:
                    # Connection is stale, reconnect
                    print(f"Connection test failed: {str(conn_test_error)}")
                    self.connection = psycopg2.connect(**self.connection_params)
                    print("Reconnected to PostgreSQL database successfully")
        except Exception as e:
            import traceback
            print(f"Error connecting to PostgreSQL database: {str(e)}")
            print(f"Connection error details: {traceback.format_exc()}")
            self.connection = None

    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Execute a SQL query with safety checks to prevent database modifications
        """
        try:
            print(f"Executing query: {query[:100]}{'...' if len(query) > 100 else ''}")
            
            # Safety check to prevent database modifications
            query_lower = query.lower().strip()
            dangerous_keywords = ['insert', 'update', 'delete', 'drop', 'alter', 'truncate', 'create', 'replace']
            
            # Check if query contains dangerous keywords
            for keyword in dangerous_keywords:
                if query_lower.startswith(keyword) or f" {keyword} " in query_lower:
                    print(f"Query rejected: contains dangerous keyword '{keyword}'")
                    return {
                        "success": False, 
                        "error": f"For security reasons, {keyword.upper()} operations are not allowed"
                    }
            
            # Check if connection exists
            if self.connection is None:
                print("No active database connection, attempting to connect...")
            
            # Ensure connection is active
            self.connect()
            
            if self.connection is None:
                print("Failed to establish database connection")
                return {"success": False, "error": "Unable to connect to the database"}
            
            # Update last_used timestamp
            self.last_used = time.time()
            
            print("Connection established, executing query...")
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute(query)
            
            # For SELECT queries, fetch results
            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                # Convert to list of dicts
                data = [dict(row) for row in results]
                row_count = len(data)
                print(f"Query executed successfully: {row_count} rows returned")
                self.connection.commit()
                cursor.close()
                return {"success": True, "data": data}
            else:
                # For non-SELECT queries, commit and return success
                self.connection.commit()
                affected_rows = cursor.rowcount
                print(f"Query executed successfully: {affected_rows} rows affected")
                cursor.close()
                return {"success": True, "data": [{"message": f"Query executed successfully. Rows affected: {affected_rows}"}]}
        except Exception as e:
            import traceback
            print(f"Error executing query: {str(e)}")
            print(f"Query execution error details: {traceback.format_exc()}")
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
