#!/usr/bin/env python3
"""
Supabaseデータベースの初期設定スクリプト
新しいテーブルやスキーマの変更を適用します
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from modules.database_schema import SCHEMA, INITIAL_DATA

def setup_supabase_db():
    """Set up the Supabase database with the required schema"""
    print("Setting up Supabase database...")
    
    # Load environment variables
    load_dotenv()
    
    # Get database connection parameters from environment variables
    db_params = {
        "dbname": os.getenv("DB_NAME", "postgres"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432")
    }
    
    try:
        # Connect to the database
        print("Connecting to Supabase PostgreSQL database...")
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Create tables from schema
        print("Creating tables...")
        for table_name, create_statement in SCHEMA.items():
            cursor.execute(create_statement)
            print(f"✓ {table_name} table initialized")
        
        # Insert initial data
        print("\nInserting initial data...")
        for data_name, insert_statement in INITIAL_DATA.items():
            cursor.execute(insert_statement)
            print(f"✓ {data_name} initial data inserted")
            
        # Create execute_sql function for dynamic SQL execution
        print("\nCreating execute_sql function...")
        execute_sql_function = """
        CREATE OR REPLACE FUNCTION public.execute_sql(sql_query text, params jsonb DEFAULT '[]'::jsonb)
        RETURNS jsonb
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        DECLARE
            result_rows jsonb;
            query_type text;
            affected_rows integer;
        BEGIN
            -- Determine query type (SELECT, INSERT, UPDATE, DELETE)
            query_type := upper(substring(trim(sql_query) from 1 for 6));
            
            -- For SELECT queries, return the results as JSON
            IF query_type = 'SELECT' THEN
                EXECUTE sql_query INTO result_rows;
                RETURN result_rows;
            -- For other query types, execute and return affected row count
            ELSE
                EXECUTE sql_query;
                GET DIAGNOSTICS affected_rows = ROW_COUNT;
                RETURN jsonb_build_object('affected_rows', affected_rows);
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RETURN jsonb_build_object('error', SQLERRM, 'query', sql_query);
        END;
        $$;
        """
        cursor.execute(execute_sql_function)
        print("✓ execute_sql function created")
        
        # Commit changes
        conn.commit()
        print("\nDatabase setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
    
    return True

if __name__ == "__main__":
    setup_supabase_db()