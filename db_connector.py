"""
Database connector for Supabase
"""
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

class SupabaseConnector:
    """
    Connector class for Supabase database
    """
    def __init__(self):
        """
        Initialize Supabase client
        """
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_API_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and API key must be provided in .env file")
        
        self.client = create_client(self.supabase_url, self.supabase_key)
    
    def get_schemas(self) -> List[str]:
        """
        Get all schema names in the database
        """
        try:
            # Create a stored function in Supabase to get schemas
            # This function needs to be created in your Supabase database
            # CREATE OR REPLACE FUNCTION get_schemas()
            # RETURNS TABLE (schema_name text) AS $$
            # SELECT schema_name::text FROM information_schema.schemata 
            # WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            # $$ LANGUAGE sql SECURITY DEFINER;
            
            # Call the function using RPC
            response = self.client.rpc('get_schemas').execute()
            
            if hasattr(response, 'data') and response.data:
                return [schema["schema_name"] for schema in response.data]
            
            # Fallback to returning public schema
            return ["public"]
        except Exception as e:
            print(f"Error getting schemas: {str(e)}")
            # Fallback to returning common schemas
            return ["public"]
    
    def get_tables_in_schema(self, schema_name: str) -> List[str]:
        """
        Get all table names in a specific schema
        """
        try:
            # Create a stored function in Supabase to get tables in a schema
            # This function needs to be created in your Supabase database
            # CREATE OR REPLACE FUNCTION get_tables_in_schema(p_schema_name text)
            # RETURNS TABLE (table_name text) AS $$
            # SELECT table_name::text FROM information_schema.tables 
            # WHERE table_schema = p_schema_name
            # $$ LANGUAGE sql SECURITY DEFINER;
            
            # Call the function using RPC
            response = self.client.rpc('get_tables_in_schema', {"p_schema_name": schema_name}).execute()
            
            if hasattr(response, 'data') and response.data:
                return [table["table_name"] for table in response.data]
            return []
        except Exception as e:
            print(f"Error getting tables in schema {schema_name}: {str(e)}")
            return []
    
    def get_table_schema(self, schema_name: str, table_name: str) -> List[Dict[str, Any]]:
        """
        Get schema information for a specific table
        """
        try:
            # Create a stored function in Supabase to get table schema
            # This function needs to be created in your Supabase database
            # CREATE OR REPLACE FUNCTION get_table_schema(p_schema_name text, p_table_name text)
            # RETURNS TABLE (column_name text, data_type text, is_nullable text, column_default text) AS $$
            # SELECT 
            #     column_name::text, 
            #     data_type::text, 
            #     is_nullable::text, 
            #     column_default::text
            # FROM 
            #     information_schema.columns
            # WHERE 
            #     table_schema = p_schema_name 
            #     AND table_name = p_table_name
            # ORDER BY 
            #     ordinal_position
            # $$ LANGUAGE sql SECURITY DEFINER;
            
            # Call the function using RPC
            response = self.client.rpc('get_table_schema', {
                "p_schema_name": schema_name,
                "p_table_name": table_name
            }).execute()
            
            if hasattr(response, 'data') and response.data:
                return response.data
            return []
        except Exception as e:
            print(f"Error getting schema for {schema_name}.{table_name}: {str(e)}")
            return []
    
    def get_foreign_keys(self, schema_name: str, table_name: str) -> List[Dict[str, Any]]:
        """
        Get foreign key information for a specific table
        """
        try:
            # Create a stored function in Supabase to get foreign keys
            # This function needs to be created in your Supabase database
            # CREATE OR REPLACE FUNCTION get_foreign_keys(p_schema_name text, p_table_name text)
            # RETURNS TABLE (column_name text, foreign_table_schema text, foreign_table_name text, foreign_column_name text) AS $$
            # SELECT
            #     kcu.column_name::text,
            #     ccu.table_schema::text AS foreign_table_schema,
            #     ccu.table_name::text AS foreign_table_name,
            #     ccu.column_name::text AS foreign_column_name
            # FROM
            #     information_schema.table_constraints tc
            #     JOIN information_schema.key_column_usage kcu
            #       ON tc.constraint_name = kcu.constraint_name
            #     JOIN information_schema.constraint_column_usage ccu
            #       ON ccu.constraint_name = tc.constraint_name
            # WHERE
            #     tc.constraint_type = 'FOREIGN KEY'
            #     AND tc.table_schema = p_schema_name
            #     AND tc.table_name = p_table_name
            # $$ LANGUAGE sql SECURITY DEFINER;
            
            # Call the function using RPC
            response = self.client.rpc('get_foreign_keys', {
                "p_schema_name": schema_name,
                "p_table_name": table_name
            }).execute()
            
            if hasattr(response, 'data') and response.data:
                return response.data
            return []
        except Exception as e:
            print(f"Error getting foreign keys for {schema_name}.{table_name}: {str(e)}")
            return []
    
    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Execute a SQL query
        """
        try:
            # Create a stored function in Supabase to execute SQL queries
            # This function needs to be created in your Supabase database
            # CREATE OR REPLACE FUNCTION execute_sql(p_query text)
            # RETURNS SETOF json AS $$
            # DECLARE
            #     result json;
            # BEGIN
            #     EXECUTE p_query INTO result;
            #     RETURN QUERY SELECT result;
            #     EXCEPTION WHEN OTHERS THEN
            #     RAISE EXCEPTION 'SQL Error: %', SQLERRM;
            # END;
            # $$ LANGUAGE plpgsql SECURITY DEFINER;
            
            # Call the function using RPC
            response = self.client.rpc('execute_sql', {"p_query": query}).execute()
            
            if hasattr(response, 'data') and response.data:
                return {"success": True, "data": response.data}
            return {"success": True, "data": []}
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            return {"success": False, "error": str(e)}
