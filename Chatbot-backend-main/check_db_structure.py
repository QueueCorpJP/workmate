#!/usr/bin/env python3
"""
データベース構造確認スクリプト
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_url():
    supabase_url = os.getenv('SUPABASE_URL')
    if 'supabase.co' in supabase_url:
        project_id = supabase_url.split('://')[1].split('.')[0]
        return f'postgresql://postgres.{project_id}:{os.getenv("DB_PASSWORD", "")}@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres'
    return os.getenv('DATABASE_URL')

def main():
    try:
        db_url = get_db_url()
        with psycopg2.connect(db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                # Check what tables exist
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('document_embeddings', 'chunks', 'document_sources')
                    ORDER BY table_name
                """)
                tables = cur.fetchall()
                print('Available tables:')
                for table in tables:
                    print(f'  - {table["table_name"]}')
                
                # Check document_embeddings structure if it exists
                if any(t['table_name'] == 'document_embeddings' for t in tables):
                    cur.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'document_embeddings'
                        ORDER BY ordinal_position
                    """)
                    columns = cur.fetchall()
                    print('\ndocument_embeddings columns:')
                    for col in columns:
                        print(f'  - {col["column_name"]}: {col["data_type"]}')
                    
                    # Check if there's any data
                    cur.execute('SELECT COUNT(*) as count FROM document_embeddings')
                    count = cur.fetchone()
                    print(f'\ndocument_embeddings row count: {count["count"]}')
                    
                    # Check sample data
                    if count["count"] > 0:
                        cur.execute('SELECT document_id, snippet FROM document_embeddings LIMIT 3')
                        samples = cur.fetchall()
                        print('\nSample document_embeddings data:')
                        for sample in samples:
                            print(f'  - {sample["document_id"]}: {sample["snippet"][:50] if sample["snippet"] else "No snippet"}...')
                
                # Check chunks structure if it exists
                if any(t['table_name'] == 'chunks' for t in tables):
                    cur.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'chunks'
                        ORDER BY ordinal_position
                    """)
                    columns = cur.fetchall()
                    print('\nchunks columns:')
                    for col in columns:
                        print(f'  - {col["column_name"]}: {col["data_type"]}')
                    
                    # Check if there's any data
                    cur.execute('SELECT COUNT(*) as count FROM chunks')
                    count = cur.fetchone()
                    print(f'\nchunks row count: {count["count"]}')

    except Exception as e:
        print(f'Database check error: {e}')

if __name__ == "__main__":
    main()