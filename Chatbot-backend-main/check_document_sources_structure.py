#!/usr/bin/env python3
"""
document_sourcesテーブル構造確認スクリプト
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
                # Check document_sources structure
                cur.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'document_sources'
                    ORDER BY ordinal_position
                """)
                columns = cur.fetchall()
                print('document_sources columns:')
                for col in columns:
                    print(f'  - {col["column_name"]}: {col["data_type"]} (nullable: {col["is_nullable"]}, default: {col["column_default"]})')
                
                # Check if there's any data
                cur.execute('SELECT COUNT(*) as count FROM document_sources')
                count = cur.fetchone()
                print(f'\ndocument_sources row count: {count["count"]}')
                
                # Check sample data if exists
                if count["count"] > 0:
                    cur.execute('SELECT * FROM document_sources LIMIT 1')
                    sample = cur.fetchone()
                    print('\nSample document_sources data:')
                    for key, value in sample.items():
                        print(f'  - {key}: {value}')

    except Exception as e:
        print(f'Database check error: {e}')

if __name__ == "__main__":
    main()