"""
Supabase adapter for the chatbot application
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

# Create Supabase client
try:
    supabase: Client = create_client(supabase_url, supabase_key)
    # タイムアウト設定を適用
    if hasattr(supabase, '_client'):
        supabase._client.timeout = 600
except Exception as e:
    print(f"Supabase client creation error: {e}")
    # フォールバック：デフォルト設定でクライアント作成
    supabase: Client = create_client(supabase_url, supabase_key)

def get_supabase_client():
    """Get the Supabase client instance"""
    return supabase

def execute_query(query, params=None):
    """Execute a SQL query on Supabase"""
    # This is a simple wrapper around the Supabase client's rpc function
    # You can use this to execute custom SQL queries
    try:
        # print(f"Executing query: {query}")
        result = supabase.rpc(
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

def insert_data(table, data):
    """Insert data into a table"""
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
        # タイムアウト付きで実行
        result = supabase.table(table).insert(data).execute()
        
        # 成功ログ
        if isinstance(data, dict) and 'content' in data:
            content_size = len(str(data['content']).encode('utf-8')) / (1024 * 1024)
            if content_size > 0.1:  # 100KB以上の場合
                print(f"✅ データ挿入成功: {content_size:.2f}MB (テーブル: {table})")
        
        return result
        
    except Exception as e:
        # エラーの詳細をログ出力
        error_msg = str(e)
        if isinstance(data, dict) and 'content' in data:
            content_size = len(str(data['content']).encode('utf-8')) / (1024 * 1024)
            print(f"❌ データ挿入エラー: {content_size:.2f}MB (テーブル: {table}) - {error_msg}")
        else:
            print(f"❌ データ挿入エラー (テーブル: {table}) - {error_msg}")
        
        # statement timeoutの場合は特別なエラーメッセージ
        if "statement timeout" in error_msg.lower() or "57014" in error_msg:
            raise Exception(f"データベースタイムアウト: コンテンツが大きすぎます。ファイルを分割してください。")
        
        raise

def update_data(table, data, match_column, match_value):
    """Update data in a table"""
    # Ensure all data values are properly converted to strings
    if isinstance(data, dict):
        for key, value in data.items():
            if value is None:
                # Keep NULL values as NULL for integer fields
                continue
            elif not isinstance(value, (str, int, float, bool)):
                data[key] = str(value)
    
    return supabase.table(table).update(data).eq(match_column, match_value).execute()

def delete_data(table, match_column, match_value):
    """Delete data from a table"""
    return supabase.table(table).delete().eq(match_column, match_value).execute()

def select_data(table, columns="*", filters=None, order=None, limit=None, offset=None):
    """Select data from a table with optional filters, ordering, and pagination"""
    # print(f"Selecting data from table: {table}, columns: {columns}, filters: {filters}, order: {order}, limit: {limit}, offset: {offset}")
    
    # Check if this is a COUNT query
    if isinstance(columns, str) and "COUNT" in columns.upper():
        # Use execute_query for COUNT operations
        count_query = f"SELECT COUNT(*) FROM {table}"
        
        # Add filters if provided
        if filters:
            conditions = []
            for column, value in filters.items():
                if isinstance(value, str):
                    conditions.append(f"{column} = '{value}'")
                else:
                    conditions.append(f"{column} = {value}")
            
            if conditions:
                count_query += " WHERE " + " AND ".join(conditions)
        
        # print(f"Executing COUNT query: {count_query}")
        
        # Execute the COUNT query
        try:
            count_result = execute_query(count_query)
            # print(f"COUNT result: {count_result}")
            
            # Create a wrapper for the result
            class ResultWrapper:
                def __init__(self, data):
                    self.data = data
                
                def order(self, column, ascending=True):
                    return self.data
                
                def __getitem__(self, key):
                    return self.data[key]
                
                def __len__(self):
                    return len(self.data)
                
                def __bool__(self):
                    return bool(self.data)
            
            # Format the result to match the expected structure
            result = type('obj', (object,), {
                'data': ResultWrapper([{'count': count_result[0]['count']}])
            })
            
            return result
        except Exception as e:
            print(f"Supabase API error in fetchall: {e}")
            import traceback
            print(traceback.format_exc())
            # Return empty result on error
            return type('obj', (object,), {'data': ResultWrapper([])})
    
    # For non-COUNT queries, use the standard approach
    # print(f"Using standard approach for table: {table}")
    query = supabase.table(table).select(columns)
    
    if filters:
        for column, value in filters.items():
            # print(f"Adding filter: {column} = {value}")
            query = query.eq(column, value)
    
    # Add ordering if specified
    if order:
        # print(f"Adding order: {order}")
        if " desc" in order.lower():
            column_name = order.replace(" desc", "").strip()
            query = query.order(column_name, desc=True)
        elif " asc" in order.lower():
            column_name = order.replace(" asc", "").strip()
            query = query.order(column_name, desc=False)
        else:
            query = query.order(order, desc=False)
    
    # Add limit and offset using range method
    if offset is not None or limit is not None:
        start = offset or 0
        if limit is not None:
            # range(start, end) where end is inclusive
            end = start + limit - 1
            # print(f"Adding range: {start} to {end}")
            query = query.range(start, end)
        else:
            # If no limit specified but offset is given, get a reasonable amount
            # print(f"Adding range from offset: {start}")
            query = query.range(start, start + 999)
    
    # Execute the query and return the result
    try:
        # print(f"Executing Supabase query for table: {table}")
        # print(f"Query details: columns={columns}, filters={filters}, order={order}, limit={limit}, offset={offset}")
        result = query.execute()
        # print(f"Query result for table {table}: {len(result.data) if result.data else 0} rows")
        
        # Create a wrapper class for the result data
        class ResultWrapper:
            def __init__(self, data):
                self.data = data
            
            def order(self, column, ascending=True):
                # Just return the original data, no ordering is performed
                return self.data
                
            def __getitem__(self, key):
                # Make the wrapper subscriptable
                return self.data[key]
                
            def __len__(self):
                # Support len() function
                return len(self.data)
                
            def __bool__(self):
                # Support boolean evaluation
                return bool(self.data)
        
        # Replace result.data with a wrapper that has an order method
        original_data = result.data
        result.data = ResultWrapper(original_data)
        
        return result
    except Exception as e:
        print(f"Error executing Supabase query for table {table}: {e}")
        # print(f"Query parameters - columns: {columns}, filters: {filters}, order: {order}, limit: {limit}, offset: {offset}")
        import traceback
        print(traceback.format_exc())
        
        # Create an empty result wrapper
        class ResultWrapper:
            def __init__(self, data):
                self.data = data
            
            def order(self, column, ascending=True):
                return self.data
                
            def __getitem__(self, key):
                return self.data[key]
                
            def __len__(self):
                return len(self.data)
                
            def __bool__(self):
                return bool(self.data)
        
        # Return empty result on error
        return type('obj', (object,), {'data': ResultWrapper([])})