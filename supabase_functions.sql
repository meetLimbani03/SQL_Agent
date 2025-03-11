-- SQL functions for Supabase to support the SQL Agent
-- Run these in your Supabase SQL Editor

-- Function to get schemas
CREATE OR REPLACE FUNCTION get_schemas()
RETURNS TABLE (schema_name text) AS $$
SELECT schema_name::text 
FROM information_schema.schemata 
WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
$$ LANGUAGE sql SECURITY DEFINER;

-- Function to get tables in a schema
CREATE OR REPLACE FUNCTION get_tables_in_schema(p_schema_name text)
RETURNS TABLE (table_name text) AS $$
SELECT table_name::text 
FROM information_schema.tables 
WHERE table_schema = p_schema_name
$$ LANGUAGE sql SECURITY DEFINER;

-- Function to get table schema
CREATE OR REPLACE FUNCTION get_table_schema(p_schema_name text, p_table_name text)
RETURNS TABLE (column_name text, data_type text, is_nullable text, column_default text) AS $$
SELECT 
    column_name::text, 
    data_type::text, 
    is_nullable::text, 
    column_default::text
FROM 
    information_schema.columns
WHERE 
    table_schema = p_schema_name 
    AND table_name = p_table_name
ORDER BY 
    ordinal_position
$$ LANGUAGE sql SECURITY DEFINER;

-- Function to get foreign keys
CREATE OR REPLACE FUNCTION get_foreign_keys(p_schema_name text, p_table_name text)
RETURNS TABLE (column_name text, foreign_table_schema text, foreign_table_name text, foreign_column_name text) AS $$
SELECT
    kcu.column_name::text,
    ccu.table_schema::text AS foreign_table_schema,
    ccu.table_name::text AS foreign_table_name,
    ccu.column_name::text AS foreign_column_name
FROM
    information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage ccu
      ON ccu.constraint_name = tc.constraint_name
WHERE
    tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = p_schema_name
    AND tc.table_name = p_table_name
$$ LANGUAGE sql SECURITY DEFINER;

-- Function to execute SQL queries
-- Note: This function requires elevated privileges and should be used with caution
CREATE OR REPLACE FUNCTION execute_sql(p_query text)
RETURNS SETOF json AS $$
DECLARE
    result json;
BEGIN
    -- For SELECT queries, we can use json_agg to convert the results to JSON
    IF lower(substring(trim(p_query) from 1 for 6)) = 'select' THEN
        EXECUTE 'SELECT json_agg(t) FROM (' || p_query || ') t' INTO result;
        IF result IS NULL THEN
            -- Return empty array if no results
            result := '[]'::json;
        END IF;
        RETURN QUERY SELECT result;
    ELSE
        -- For non-SELECT queries, execute and return success message
        EXECUTE p_query;
        RETURN QUERY SELECT json_build_object('message', 'Query executed successfully')::json;
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'SQL Error: %', SQLERRM;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
