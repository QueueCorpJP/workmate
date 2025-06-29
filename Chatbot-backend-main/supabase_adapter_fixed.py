"""
Supabase adapter for the chatbot application (Fixed version with schema cache refresh)
This module provides functions to connect to Supabase and use it as a database backend
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment variables
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# Supabaseクライアント設定（タイムアウト設定追加）
client_options = {
    "timeout": 600,  # 10分のタイムアウト（大きなファイル処理用）
    "retry_count": 3,  # リトライ回数
}

# Global client variable
_supabase_client = None

def create_fresh_client():
    """Create a fresh Supabase client instance"""
    try:
        client = create_client(supabase_url, supabase_key)
        # タイムアウト設定を適用
        if hasattr(client, '_client'):
            client._client.timeout = 600
        return client
    except Exception as e:
        print(f"Supabase client creation error: {e}")
        # フォールバック：デフォルト設定でクライアント作成
        return create_client(supabase_url, supabase_key)

def get_supabase_client(force_refresh=False):
    """Get the Supabase client instance with optional refresh"""
    global _supabase_client
    
    if _supabase_client is None or force_refresh:
        print("🔄 Creating fresh Supabase client...")
        _supabase_client = create_fresh_client()
    
    return _supabase_client

def refresh_schema_cache():
    """Force refresh the Supabase client to clear schema cache"""
    global _supabase_client
    print("🔄 Refreshing Supabase schema cache...")
    _supabase_client = create_fresh_client()
    return _supabase_client

# Initialize the client
supabase = get_supabase_client()

def execute_query(query, params=None):
    """Execute a SQL query on Supabase"""
    # This is a simple wrapper around the Supabase client's rpc function
    # You can use this to execute custom SQL queries
    try:
        client = get_supabase_client()
        # print(f"Executing query: {query}")
        result = client.rpc(
            "execute_sql",
            {"sql_query": query, "params": params or []}
        ).execute()
        
        # Ensure we always return a list-like object
        if result.data is None:
            # print("Query result is None, returning empty list")
            return []
            
        # If result.data is not a list (e.g., it's an integer from COUNT),
        # wrap it in a list with appropriate structure
        if not isinstance(result.data, list):
            # print(f"Query result is not a list, type: {type(result.data)}, value: {result.data}")
            # For COUNT queries, format as a list with a dict containing the count
            if "COUNT(*)" in query.upper():
                return [{"count": result.data}]
            # For other non-list results, wrap in a list
            return [result.data]
        
        # print(f"Query returned {len(result.data)} results")
        return result.data
    except Exception as e:
        # print(f"Execute query error: {e}")
        import traceback
        # print(traceback.format_exc())
        return []

def insert_data(table, data, retry_with_fresh_client=True):
    """Insert data into a table with automatic schema cache refresh on error"""
    # Ensure all data values are properly converted to strings
    if isinstance(data, dict):
        # コンテンツサイズをチェック
        content_size = 0
        if 'content' in data and data['content']:
            content_size = len(str(data['content']).encode('utf-8')) / (1024 * 1024)
        
        # 大きなコンテンツの場合は警告ログ
        if content_size > 1:
            print(f"⚠️ 大きなコンテンツを挿入中: {content_size:.2f}MB (テーブル: {table})")
        
        for key, value in data.items():
            if value is None:
                # Keep NULL values as NULL for integer fields
                continue
            elif not isinstance(value, (str, int, float, bool)):
                data[key] = str(value)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                for key, value in item.items():
                    if value is None:
                        # Keep NULL values as NULL for integer fields
                        continue
                    elif not isinstance(value, (str, int, float, bool)):
                        item[key] = str(value)
    
    try:
        # Get current client
        client = get_supabase_client()
        
        # タイムアウト付きで実行
        result = client.table(table).insert(data).execute()
        
        # 成功ログ
        if isinstance(data, dict) and 'content' in data:
            content_size = len(str(data['content']).encode('utf-8')) / (1024 * 1024)
            if content_size > 0.1:  # 100KB以上の場合
                print(f"✅ データ挿入成功: {content_size:.2f}MB (テーブル: {table})")
        
        return result
        
    except Exception as e:
        # エラーの詳細をログ出力
        error_msg = str(e)
        
        # スキーマキャッシュエラーの場合は自動的にリトライ
        if "schema cache" in error_msg.lower() and retry_with_fresh_client:
            print(f"🔄 スキーマキャッシュエラーを検出。新しいクライアントでリトライ中...")
            
            # 新しいクライアントを作成
            fresh_client = refresh_schema_cache()
            
            try:
                # 新しいクライアントでリトライ
                result = fresh_client.table(table).insert(data).execute()
                print(f"✅ リトライ成功: データ挿入完了 (テーブル: {table})")
                return result
            except Exception as retry_error:
                print(f"❌ リトライも失敗: {retry_error}")
                raise retry_error
        
        # その他のエラーまたはリトライ失敗の場合
        if isinstance(data, dict) and 'content' in data:
            content_size = len(str(data['content']).encode('utf-8')) / (1024 * 1024)
            print(f"❌ データ挿入エラー: {content_size:.2f}MB (テーブル: {table}) - {error_msg}")
        else:
            print(f"❌ データ挿入エラー (テーブル: {table}) - {error_msg}")
        
        raise e

def select_data(table, columns="*", filters=None):
    """Select data from a table"""
    try:
        client = get_supabase_client()
        query = client.table(table).select(columns)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        result = query.execute()
        return result
    except Exception as e:
        print(f"Select data error: {e}")
        return None

def update_data(table, data, filters):
    """Update data in a table"""
    try:
        client = get_supabase_client()
        query = client.table(table).update(data)
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        result = query.execute()
        return result
    except Exception as e:
        print(f"Update data error: {e}")
        return None

def delete_data(table, filters):
    """Delete data from a table"""
    try:
        client = get_supabase_client()
        query = client.table(table).delete()
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        result = query.execute()
        return result
    except Exception as e:
        print(f"Delete data error: {e}")
        return None