"""
データベースモジュール
データベース接続と初期化を管理します
Supabase APIを使用してデータベース操作を行います
"""

import uuid
import datetime
import json
import os
from typing import Dict, List, Any, Optional
from fastapi import Depends
from .config import get_db_params
from .database_schema import SCHEMA, INITIAL_DATA
from supabase_adapter import get_supabase_client, insert_data, update_data, delete_data, select_data, execute_query

# データ型変換ユーティリティ関数
def ensure_string(value, for_db=False):
    """値を文字列に変換する。
    
    Args:
        value: 変換する値
        for_db: データベース操作用かどうか。Trueの場合、Noneはそのまま返す
    
    Returns:
        文字列に変換された値、またはNone
    """
    if value is None:
        if for_db:
            # データベース操作用の場合はNoneをそのまま返す（INTEGER型などのため）
            return None
        return ""
    return str(value)

# Supabaseクライアントを取得
supabase = get_supabase_client()

# データベース接続のモック（Supabaseを使用するため実際の接続は不要）
class SupabaseConnection:
    """Supabase接続を模倣するクラス"""
    def __init__(self):
        self.supabase = supabase
        
    def close(self):
        """接続を閉じる（Supabaseでは不要だが互換性のために残す）"""
        pass
        
    def commit(self):
        """変更をコミット（Supabaseでは不要だが互換性のために残す）"""
        pass
        
    def cursor(self, cursor_factory=None):
        """カーソルを返す（Supabaseでは不要だが互換性のために残す）"""
        # cursor_factoryパラメータを保存して、RealDictCursorのような動作を模倣する
        return SupabaseCursor(self, cursor_factory)
        
# Supabaseカーソルクラス
class SupabaseCursor:
    """Supabaseカーソルを模倣するクラス"""
    def __init__(self, connection, cursor_factory=None):
        self.connection = connection
        self.supabase = connection.supabase
        self.last_result = None
        self.last_query = None
        self.last_params = None
        self.table_name = None
        self.select_columns = "*"
        self.where_conditions = {}
        self.order_by = None
        self.order_direction = "asc"
        # RealDictCursorと同様の動作をするかどうか
        self.cursor_factory = cursor_factory
        # cursor_factoryがRealDictCursorかどうかを確認
        self.is_real_dict_cursor = False
        if cursor_factory:
            try:
                self.is_real_dict_cursor = cursor_factory.__name__ == "RealDictCursor"
            except AttributeError:
                # cursor_factoryに__name__属性がない場合
                self.is_real_dict_cursor = "RealDictCursor" in str(cursor_factory)
        
    # コンテキストマネージャプロトコルのサポート
    def __enter__(self):
        """withステートメントのサポート"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """withステートメント終了時の処理"""
        pass
        
    def execute(self, query, params=None):
        """クエリを実行する（Supabaseでは実際のSQLは実行せず、APIを使用）"""
        import re
        import json
        import os
        
        self.last_query = query
        
        # パラメータがある場合、すべての値を文字列に変換
        if params:
            # タプルの場合はリストに変換
            if isinstance(params, tuple):
                params = list(params)
                
            # リストの場合は各要素を処理
            if isinstance(params, list):
                for i in range(len(params)):
                    if params[i] is not None and not isinstance(params[i], (str, int, float, bool)):
                        params[i] = str(params[i])
                    # NULLはそのまま保持（INTEGER型などのために必要）
            
            # 辞書の場合は各値を処理
            elif isinstance(params, dict):
                for key in params:
                    if params[key] is not None and not isinstance(params[key], (str, int, float, bool)):
                        params[key] = str(params[key])
                    # NULLはそのまま保持（INTEGER型などのために必要）
        
        self.last_params = params
        
        # クエリを解析してSupabase API呼び出しに変換
        query = query.strip()
        
        # SELECTクエリの処理
        if query.upper().startswith("SELECT"):
            # テーブル名を抽出
            table_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
            if table_match:
                self.table_name = table_match.group(1)
            
            # 選択カラムを抽出
            select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query, re.IGNORECASE)
            if select_match and select_match.group(1) != "*":
                self.select_columns = select_match.group(1)
            
            # WHERE条件を抽出
            where_match = re.search(r'WHERE\s+(.*?)(?:ORDER BY|GROUP BY|$)', query, re.IGNORECASE)
            if where_match:
                where_clause = where_match.group(1).strip()
                
                # パラメータ置換
                if params:
                    # 単一パラメータの場合
                    if isinstance(params, (str, int, float, bool)):
                        where_clause = where_clause.replace("%s", str(params))
                    # タプルやリストの場合
                    elif isinstance(params, (list, tuple)):
                        for param in params:
                            where_clause = where_clause.replace("%s", str(param), 1)
                
                # 条件を解析
                conditions = where_clause.split("AND")
                for condition in conditions:
                    if "=" in condition:
                        col, val = condition.split("=", 1)
                        col = col.strip()
                        val = val.strip()
                        # 引用符を削除
                        if val.startswith("'") and val.endswith("'"):
                            val = val[1:-1]
                        self.where_conditions[col] = val
            
            # ORDER BY句を抽出
            order_match = re.search(r'ORDER BY\s+(.*?)(?:LIMIT|$)', query, re.IGNORECASE)
            if order_match:
                order_clause = order_match.group(1).strip()
                if "DESC" in order_clause.upper():
                    self.order_direction = "desc"
                    self.order_by = order_clause.replace("DESC", "").strip()
                else:
                    self.order_by = order_clause.replace("ASC", "").strip()
            
            # 実際のSupabase APIを呼び出すのはfetchone/fetchallで行う
            
        # INSERTクエリの処理
        elif query.upper().startswith("INSERT"):
            # テーブル名を抽出
            table_match = re.search(r'INTO\s+(\w+)', query, re.IGNORECASE)
            if not table_match:
                print("テーブル名が見つかりません")
                return
                
            self.table_name = table_match.group(1)
            
            # カラムと値を抽出
            columns_match = re.search(r'\(([^)]+)\)\s+VALUES\s+\(([^)]+)\)', query, re.IGNORECASE)
            if not columns_match:
                print("カラムと値が見つかりません")
                return
                
            columns = [col.strip() for col in columns_match.group(1).split(',')]
            values = [val.strip() if isinstance(val, str) else val for val in columns_match.group(2).split(',')]
            
            # パラメータ置換
            if params:
                if isinstance(params, (list, tuple)):
                    for i, param in enumerate(params):
                        if i < len(values):
                            if isinstance(values[i], str) and values[i].strip() == '%s':
                                values[i] = param
            
            # データを構築
            data = {}
            for i, col in enumerate(columns):
                if i < len(values):
                    # 値が文字列かどうかを確認
                    if isinstance(values[i], str):
                        val = values[i].strip()
                        # 引用符を削除
                        if val.startswith("'") and val.endswith("'"):
                            val = val[1:-1]
                    else:
                        # 文字列でない場合はそのまま使用
                        val = values[i]
                    data[col] = val
            
            # Supabase APIを呼び出す
            from supabase_adapter import insert_data
            result = insert_data(self.table_name, data)
            self.last_result = result.data
            
        # UPDATEクエリの処理
        elif query.upper().startswith("UPDATE"):
            # テーブル名を抽出
            table_match = re.search(r'UPDATE\s+(\w+)', query, re.IGNORECASE)
            if not table_match:
                print("テーブル名が見つかりません")
                return
                
            self.table_name = table_match.group(1)
            
            # SET句を抽出
            set_match = re.search(r'SET\s+(.*?)(?:WHERE|$)', query, re.IGNORECASE)
            if not set_match:
                print("SET句が見つかりません")
                return
                
            set_clause = set_match.group(1).strip()
            
            # WHERE句を抽出
            where_match = re.search(r'WHERE\s+(.*?)$', query, re.IGNORECASE)
            if not where_match:
                print("WHERE句が見つかりません")
                return
                
            where_clause = where_match.group(1).strip()
            
            # パラメータ置換
            if params:
                if isinstance(params, (list, tuple)):
                    # SET句のパラメータ置換
                    for param in params:
                        set_clause = set_clause.replace("%s", str(param), 1)
                    
                    # WHERE句のパラメータ置換
                    for param in params:
                        where_clause = where_clause.replace("%s", str(param), 1)
            
            # SET句を解析
            data = {}
            set_items = set_clause.split(',')
            for item in set_items:
                if '=' in item:
                    col, val = item.split('=', 1)
                    col = col.strip()
                    val = val.strip()
                    # 引用符を削除
                    if isinstance(val, str):
                        if val.startswith("'") and val.endswith("'"):
                            val = val[1:-1]
                    data[col] = val
            
            # WHERE句を解析
            match_column = None
            match_value = None
            if '=' in where_clause:
                col, val = where_clause.split('=', 1)
                match_column = col.strip()
                match_value = val.strip() if isinstance(val, str) else val
                # 引用符を削除
                if isinstance(match_value, str):
                    if match_value.startswith("'") and match_value.endswith("'"):
                        match_value = match_value[1:-1]
            
            # Supabase APIを呼び出す
            from supabase_adapter import update_data
            result = update_data(self.table_name, data, match_column, match_value)
            self.last_result = result.data
            
        # DELETEクエリの処理
        elif query.upper().startswith("DELETE"):
            # テーブル名を抽出
            table_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
            if not table_match:
                print("テーブル名が見つかりません")
                return
                
            self.table_name = table_match.group(1)
            
            # WHERE句を抽出
            where_match = re.search(r'WHERE\s+(.*?)$', query, re.IGNORECASE)
            if not where_match:
                print("WHERE句が見つかりません")
                return
                
            where_clause = where_match.group(1).strip()
            
            # パラメータ置換
            if params:
                if isinstance(params, (list, tuple)):
                    for param in params:
                        where_clause = where_clause.replace("%s", str(param), 1)
            
            # WHERE句を解析
            match_column = None
            match_value = None
            if '=' in where_clause:
                col, val = where_clause.split('=', 1)
                match_column = col.strip()
                match_value = val.strip() if isinstance(val, str) else val
                # 引用符を削除
                if isinstance(match_value, str):
                    if match_value.startswith("'") and match_value.endswith("'"):
                        match_value = match_value[1:-1]
            
            # Supabase APIを呼び出す
            from supabase_adapter import delete_data
            result = delete_data(self.table_name, match_column, match_value)
            self.last_result = result.data
            
        # 複雑なSQLクエリの場合は、Supabase RPCを使用
        elif "JOIN" in query.upper() or "GROUP BY" in query.upper() or "STRING_AGG" in query.upper() or "COALESCE" in query.upper():
            # Supabase RPCを使用して実行
            from supabase_adapter import execute_query
            try:
                # パラメータがある場合は置換
                if params:
                    if isinstance(params, (list, tuple)):
                        for param in params:
                            query = query.replace("%s", str(param), 1)
                    else:
                        query = query.replace("%s", str(params))
                
                print(f"Supabase RPCで実行: {query}")
                result = execute_query(query)
                self.last_result = result
                print(f"Supabase RPCで実行しました: {len(self.last_result) if self.last_result else 0}件")
            except Exception as e:
                print(f"Supabase RPC実行エラー: {e}")
                self.last_result = []
        
    def fetchone(self):
        """1行取得する"""
        if self.last_result is not None:
            # 既に結果がある場合は、その最初の要素を返す
            if isinstance(self.last_result, list) and len(self.last_result) > 0:
                # RealDictCursorの場合は辞書型の結果を返す
                return self.last_result[0]
            return None
            
        if not self.table_name:
            return None
            
        try:
            # Supabase APIを呼び出す
            query = select_data(
                self.table_name,
                columns=self.select_columns,
                filters=self.where_conditions
            )
            
            # 結果を取得
            result = query
            
            # ORDER BYが指定されている場合
            if self.order_by and hasattr(result, 'order'):
                result = result.order(self.order_by, ascending=(self.order_direction == "asc"))
            
            # result は既に実行済みのため、execute() を呼び出さない
            if result.data and len(result.data) > 0:
                self.last_result = result.data
                # RealDictCursorの場合は辞書型の結果を返す
                return result.data[0]
            return None
        except Exception as e:
            print(f"Supabase API error in fetchone: {e}")
            return None
        
    def fetchall(self):
        """全行取得する"""
        if self.last_result is not None:
            # 既に結果がある場合は、それを返す
            if isinstance(self.last_result, list):
                return self.last_result
            return []
            
        if not self.table_name:
            return []
            
        try:
            # Supabase APIを呼び出す
            query = select_data(
                self.table_name,
                columns=self.select_columns,
                filters=self.where_conditions
            )
            
            # 結果を取得
            result = query
            
            # ORDER BYが指定されている場合
            if self.order_by and hasattr(result, 'order'):
                result = result.order(self.order_by, ascending=(self.order_direction == "asc"))
            
            # result は既に実行済みのため、execute() を呼び出さない
            if result.data:
                self.last_result = result.data
                # RealDictCursorの場合は辞書型の結果を返す
                return result.data
            return []
        except Exception as e:
            print(f"Supabase API error in fetchall: {e}")
            return []

def get_db():
    """データベース接続を取得します（Supabase接続のモック）"""
    conn = SupabaseConnection()
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """データベースを初期化します（Supabaseテーブルの作成）"""
    print("Supabaseデータベースを初期化しています...")
    
    try:
        # テーブル存在確認のクエリ
        tables_query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """
        
        # RPCを使用してクエリを実行
        existing_tables = execute_query(tables_query)
        existing_table_names = [table.get('table_name') for table in existing_tables]
        print(f"既存のテーブル: {existing_table_names}")
        
        # 必要なテーブルを作成
        for table_name, create_statement in SCHEMA.items():
            if table_name not in existing_table_names:
                try:
                    # SQLクエリを実行してテーブルを作成
                    create_query = create_statement.strip()
                    execute_query(create_query)
                    print(f"テーブル {table_name} を作成しました")
                except Exception as e:
                    print(f"テーブル作成エラー ({table_name}): {e}")
            else:
                print(f"テーブル {table_name} は既に存在します")
        
        # 初期データの挿入
        for data_name, insert_statement in INITIAL_DATA.items():
            try:
                # SQLステートメントからテーブル名と値を抽出
                if "companies" in insert_statement:
                    # 既存のcompanyを確認
                    result = select_data("companies", filters={"id": "company_1"})
                    if not result.data:
                        insert_data("companies", {
                            "id": "company_1",
                            "name": "ヘルプ",
                            "created_at": datetime.datetime.now().isoformat()
                        })
                        print(f"{data_name} 初期データを挿入しました")
                    else:
                        print(f"{data_name} 初期データは既に存在します")
                        
                elif "users" in insert_statement and "admin" in insert_statement:
                    # 既存のadminユーザーを確認
                    result = select_data("users", filters={"id": "admin"})
                    if not result.data:
                        insert_data("users", {
                            "id": "admin",
                            "email": "queue@queuefood.co.jp",
                            "password": "John.Queue2025",
                            "name": "管理者",
                            "role": "admin",
                            "company_id": "company_1",
                            "created_at": datetime.datetime.now().isoformat()
                        })
                        print(f"{data_name} 初期データを挿入しました")
                    else:
                        print(f"{data_name} 初期データは既に存在します")
                        
                elif "usage_limits" in insert_statement:
                    # 既存の利用制限を確認
                    result = select_data("usage_limits", filters={"user_id": "admin"})
                    if not result.data:
                        insert_data("usage_limits", {
                            "user_id": "admin",
                            "is_unlimited": True
                        })
                        print(f"{data_name} 初期データを挿入しました")
                    else:
                        print(f"{data_name} 初期データは既に存在します")
            except Exception as e:
                print(f"初期データ挿入エラー ({data_name}): {e}")
                
        print("データベース初期化が完了しました")
    except Exception as e:
        print(f"データベース初期化エラー: {e}")
    
def check_user_exists(email: str, db: SupabaseConnection) -> bool:
    """ユーザーが存在するか確認します"""
    result = select_data("users", filters={"email": email})
    return len(result.data) > 0

def create_company(name: str, db: SupabaseConnection = None) -> str:
    """新しい会社を作成します"""
    company_id = str(uuid.uuid4())
    created_at = datetime.datetime.now().isoformat()
    
    company_data = {
        "id": company_id,
        "name": name,
        "created_at": created_at
    }
    
    insert_data("companies", company_data)
    return company_id

def get_company_by_id(company_id: str, db: SupabaseConnection) -> dict:
    """会社IDから会社情報を取得します"""
    result = select_data("companies", filters={"id": company_id})
    return result.data[0] if result.data else None

def get_all_companies(db: SupabaseConnection) -> list:
    """すべての会社を取得します"""
    result = select_data("companies")
    return result.data

def create_user(email: str, password: str, name: str, role: str = "user", company_id: str = None, db: SupabaseConnection = None) -> str:
    """新しいユーザーを作成します"""
    user_id = str(uuid.uuid4())
    created_at = datetime.datetime.now().isoformat()

    user_data = {
        "id": user_id,
        "email": email,
        "password": password,
        "name": name,
        "role": role,
        "company_id": company_id,
        "created_at": created_at
    }
    
    insert_data("users", user_data)

    is_unlimited = True if role == "admin" else False
    usage_limits_data = {
        "user_id": user_id,
        "is_unlimited": is_unlimited
    }
    
    insert_data("usage_limits", usage_limits_data)
    
    return user_id

def authenticate_user(email: str, password: str, db: SupabaseConnection) -> dict:
    """ユーザー認証を行います"""
    # Supabaseでは複雑なJOINクエリが難しいため、2つのクエリを実行
    user_result = select_data("users", filters={"email": email, "password": password})
    
    if not user_result.data:
        return None
        
    user = user_result.data[0]
    
    # 会社情報を取得
    if user.get("company_id"):
        company_result = select_data("companies", filters={"id": user["company_id"]})
        company_name = company_result.data[0]["name"] if company_result.data else None
        user["company_name"] = company_name
    else:
        user["company_name"] = None
        
    return user

def get_users_by_company(company_id: str, db: SupabaseConnection) -> list:
    """会社に所属するユーザーを取得します"""
    result = select_data("users", filters={"company_id": company_id})
    return result.data

def get_usage_limits(user_id: str, db: SupabaseConnection) -> dict:
    """ユーザーの利用制限を取得します"""
    result = select_data("usage_limits", filters={"user_id": user_id})
    return result.data[0] if result.data else None

def update_usage_count(user_id: str, field: str, db: SupabaseConnection) -> dict:
    """利用カウントを更新します"""
    # 現在の値を取得
    current_limits = get_usage_limits(user_id, db)
    
    if not current_limits:
        return None
        
    # 値を更新
    new_value = current_limits.get(field, 0) + 1
    update_data("usage_limits", {field: new_value}, "user_id", user_id)
    
    # 更新後の値を取得
    return get_usage_limits(user_id, db)

def get_all_users(db: SupabaseConnection) -> list:
    """すべてのユーザーを取得します"""
    # 管理者以外のユーザーを取得
    users_result = select_data("users")
    users = [user for user in users_result.data if user.get("role") != "admin"]
    
    # 会社情報を取得して結合
    companies_result = select_data("companies")
    companies = {company["id"]: company["name"] for company in companies_result.data}
    
    # ユーザーに会社名を追加
    for user in users:
        company_id = user.get("company_id")
        user["company_name"] = companies.get(company_id, "No Company")
    
    # 作成日時でソート
    users.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return users

def get_demo_usage_stats(db: SupabaseConnection, company_id: str = None) -> dict:
    """デモ利用状況の統計を取得します"""
    # ユーザー情報を取得
    users_result = select_data("users")
    users = users_result.data
    
    # 利用制限情報を取得
    usage_limits_result = select_data("usage_limits")
    usage_limits = usage_limits_result.data
    
    # ドキュメント情報を取得
    document_sources_result = select_data("document_sources")
    document_sources = document_sources_result.data
    
    # 会社情報を取得
    companies_result = select_data("companies")
    companies = companies_result.data
    
    # 一週間前の日時を計算
    one_week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
    
    # 会社IDでフィルタリング
    if company_id:
        filtered_users = [user for user in users if user.get("company_id") == company_id]
        filtered_user_ids = [user.get("id") for user in filtered_users]
        filtered_usage_limits = [limit for limit in usage_limits if limit.get("user_id") in filtered_user_ids]
        filtered_documents = [doc for doc in document_sources if doc.get("company_id") == company_id]
        
        # 会社に属するユーザーの一週間以内のチャット履歴を取得
        try:
            # 複雑なクエリの場合はSupabase RPCを使用
            query = f"""
                SELECT DISTINCT employee_id 
                FROM chat_history 
                WHERE timestamp >= '{one_week_ago}' 
                AND employee_id IN ({','.join([f"'{uid}'" for uid in filtered_user_ids if uid])})
            """ if filtered_user_ids else "SELECT DISTINCT employee_id FROM chat_history WHERE timestamp >= '{}' AND 1=0".format(one_week_ago)
            
            from supabase_adapter import execute_query
            recent_chat_users = execute_query(query)
            active_user_ids = [row.get("employee_id") for row in recent_chat_users if row.get("employee_id")]
        except Exception as e:
            print(f"一週間以内のチャット履歴取得エラー: {e}")
            # エラーの場合は従来のロジックにフォールバック
            active_user_ids = [
                limit.get("user_id") for limit in filtered_usage_limits
                if limit.get("questions_used", 0) > 0 and not limit.get("is_unlimited", False)
            ]
    else:
        filtered_users = users
        filtered_usage_limits = usage_limits
        filtered_documents = document_sources
        
        # 全ユーザーの一週間以内のチャット履歴を取得
        try:
            query = f"""
                SELECT DISTINCT employee_id 
                FROM chat_history 
                WHERE timestamp >= '{one_week_ago}'
            """
            
            from supabase_adapter import execute_query
            recent_chat_users = execute_query(query)
            active_user_ids = [row.get("employee_id") for row in recent_chat_users if row.get("employee_id")]
        except Exception as e:
            print(f"一週間以内のチャット履歴取得エラー: {e}")
            # エラーの場合は従来のロジックにフォールバック
            active_user_ids = [
                limit.get("user_id") for limit in filtered_usage_limits
                if limit.get("questions_used", 0) > 0 and not limit.get("is_unlimited", False)
            ]
    
    # 総ユーザー数（管理者以外）
    total_users = len([user for user in filtered_users if user.get("role") != "admin"])
    
    # アクティブユーザー数（一週間以内にチャットを使用したユーザー）
    # 管理者ユーザーも含める（実際に使用していればアクティブとみなす）
    active_users = len(set(active_user_ids))  # 重複を除去
    
    # ドキュメントアップロード数
    total_documents = len(filtered_documents)
    
    # 質問総数
    total_questions = sum(limit.get("questions_used", 0) for limit in filtered_usage_limits)
    
    # 制限に達したユーザー数
    limit_reached_users = len([
        limit for limit in filtered_usage_limits
        if limit.get("questions_used", 0) >= limit.get("questions_limit", 0) and not limit.get("is_unlimited", False)
    ])
    
    # 結果構築
    result = {
        "total_users": total_users,
        "active_users": active_users,
        "total_documents": total_documents,
        "total_questions": total_questions,
        "limit_reached_users": limit_reached_users
    }
    
    # 会社数（会社IDが指定されていない場合のみ）
    if not company_id:
        result["total_companies"] = len(companies)
    
    return result

def update_company_id_by_email(company_id: str, user_email: str, db: SupabaseConnection) -> bool:
    print(company_id)
    print(user_email)
    
    # ユーザーを検索
    user_result = select_data("users", filters={"email": user_email})
    
    if not user_result.data:
        return False
    
    # 会社IDを更新
    update_result = update_data("users", {"company_id": company_id}, "email", user_email)
    
    return len(update_result.data) > 0