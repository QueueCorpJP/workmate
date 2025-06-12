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
                    result = select_data("companies", filters={"name": "ヘルプ"})
                    if not result.data:
                        # UUIDで会社IDを生成
                        company_id = str(uuid.uuid4())
                        insert_data("companies", {
                            "id": company_id,
                            "name": "ヘルプ",
                            "created_at": datetime.datetime.now().isoformat()
                        })
                        print(f"{data_name} 初期データを挿入しました (ID: {company_id})")
                    else:
                        print(f"{data_name} 初期データは既に存在します")
                        company_id = result.data[0]["id"]
                        
                elif "users" in insert_statement and "admin" in insert_statement:
                    # 既存のadminユーザーを確認
                    result = select_data("users", filters={"email": "queue@queueu-tech.jp"})
                    if not result.data:
                        # ヘルプ会社のIDを取得
                        company_result = select_data("companies", filters={"name": "ヘルプ"})
                        if company_result and company_result.data:
                            help_company_id = company_result.data[0]["id"]
                            admin_user_id = str(uuid.uuid4())
                            insert_data("users", {
                                "id": admin_user_id,
                                "email": "queue@queueu-tech.jp",
                                "password": "John.Queue2025",
                                "name": "管理者",
                                "role": "admin",
                                "company_id": help_company_id,
                                "created_at": datetime.datetime.now().isoformat()
                            })
                            print(f"{data_name} 初期データを挿入しました (ID: {admin_user_id})")
                        else:
                            print(f"ヘルプ会社が見つからないため、管理者ユーザーを作成できませんでした")
                    else:
                        print(f"{data_name} 初期データは既に存在します")
                        admin_user_id = result.data[0]["id"]
                        
                elif "usage_limits" in insert_statement:
                    # 既存の利用制限を確認
                    admin_result = select_data("users", filters={"email": "queue@queueu-tech.jp"})
                    if admin_result and admin_result.data:
                        admin_user_id = admin_result.data[0]["id"]
                        result = select_data("usage_limits", filters={"user_id": admin_user_id})
                        if not result.data:
                            insert_data("usage_limits", {
                                "user_id": admin_user_id,
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

def get_all_companies(db: SupabaseConnection = None) -> List[dict]:
    """全会社一覧を取得する（特別管理者用）"""
    try:
        from supabase_adapter import select_data
        
        # 会社テーブルから全ての会社を取得
        companies_result = select_data("companies", columns="id, name, created_at")
        
        if companies_result and companies_result.data:
            return companies_result.data
        else:
            return []
            
    except Exception as e:
        print(f"会社一覧取得エラー: {str(e)}")
        return []

def create_user(email: str, password: str, name: str, role: str = "user", company_id: str = None, db: SupabaseConnection = None, creator_user_id: str = None) -> str:
    """新しいユーザーを作成します（作成者ステータス継承機能強化版）"""
    user_id = str(uuid.uuid4())
    created_at = datetime.datetime.now().isoformat()

    print(f"=== ユーザー作成開始 ===")
    print(f"新規ユーザー: {email} ({name}) - ロール: {role}")
    print(f"作成者ID: {creator_user_id}")
    print(f"指定会社ID: {company_id}")

    # company_idの自動生成または継承
    final_company_id = company_id
    if not final_company_id:
        if creator_user_id:
            # 作成者の会社IDを取得して継承
            try:
                creator_result = select_data("users", columns="company_id", filters={"id": creator_user_id})
                if creator_result and creator_result.data and len(creator_result.data) > 0:
                    creator_company_id = creator_result.data[0].get("company_id")
                    if creator_company_id:
                        final_company_id = creator_company_id
                        print(f"✓ 作成者の会社ID {final_company_id} を継承")
                    else:
                        print("作成者に会社IDが設定されていません")
            except Exception as e:
                print(f"作成者の会社ID取得エラー: {e}")
        
        # 会社IDが設定されていない場合は新規生成
        if not final_company_id:
            final_company_id = str(uuid.uuid4())
            print(f"✓ 新しい会社ID {final_company_id} を生成")
            
            # 新しい会社レコードをcompaniesテーブルに作成
            try:
                company_data = {
                    "id": final_company_id,
                    "name": f"会社_{name}",  # ユーザー名を使用したデフォルト会社名
                    "created_at": created_at
                }
                company_result = insert_data("companies", company_data)
                if company_result:
                    print(f"✓ 新しい会社レコード作成完了: {company_data['name']} (ID: {final_company_id})")
                else:
                    print(f"✗ 会社レコード作成失敗: {final_company_id}")
                    raise Exception(f"会社レコードの作成に失敗しました: {final_company_id}")
            except Exception as e:
                print(f"✗ 会社レコード作成エラー: {e}")
                raise Exception(f"会社レコードの作成中にエラーが発生しました: {str(e)}")

    user_data = {
        "id": user_id,
        "email": email,
        "password": password,
        "name": name,
        "role": role,
        "company_id": final_company_id,
        "created_by": creator_user_id,  # 作成者IDを記録
        "created_at": created_at
    }
    
    insert_data("users", user_data)
    print(f"✓ ユーザーレコード作成完了: {user_id}")

    # 利用制限の設定：作成者のステータスに基づく
    is_unlimited = False
    questions_limit = 10
    uploads_limit = 2
    
    if role == "admin" or email == "queue@queueu-tech.jp":
        # adminロールまたは特別管理者は常に無制限
        is_unlimited = True
        questions_limit = 999999
        uploads_limit = 999999
        print(f"管理者ロールのため本番版（無制限）を適用")
    elif creator_user_id:
        # 作成者がいる場合、作成者の利用制限を確認
        try:
            print(f"作成者（{creator_user_id}）の利用制限を確認中...")
            creator_limits_result = select_data("usage_limits", filters={"user_id": creator_user_id})
            if creator_limits_result and creator_limits_result.data and len(creator_limits_result.data) > 0:
                creator_limits = creator_limits_result.data[0]
                creator_is_unlimited = bool(creator_limits.get("is_unlimited", False))
                creator_questions_limit = creator_limits.get("questions_limit", 10)
                creator_uploads_limit = creator_limits.get("document_uploads_limit", 2)
                
                print(f"作成者の現在の制限:")
                print(f"  - 無制限: {creator_is_unlimited}")
                print(f"  - 質問制限: {creator_questions_limit}")
                print(f"  - アップロード制限: {creator_uploads_limit}")
                
                # 作成者が本番版（無制限）なら新しいアカウントも本番版
                # 作成者がデモ版（制限あり）なら新しいアカウントもデモ版
                is_unlimited = creator_is_unlimited
                
                if is_unlimited:
                    questions_limit = 999999
                    uploads_limit = 999999
                else:
                    questions_limit = 10
                    uploads_limit = 2
                
                print(f"✓ 作成者のステータスを継承:")
                print(f"  - 新規アカウントステータス: {'本番版' if is_unlimited else 'デモ版'}")
                print(f"  - 質問制限: {questions_limit}")
                print(f"  - アップロード制限: {uploads_limit}")
            else:
                print(f"⚠ 作成者（{creator_user_id}）の利用制限情報が見つかりません。")
                
                # 作成者の利用制限が見つからない場合、同じ会社の他のユーザーのステータスを確認
                try:
                    # 作成者の会社IDを取得
                    creator_user_result = select_data("users", columns="company_id", filters={"id": creator_user_id})
                    if creator_user_result and creator_user_result.data:
                        creator_company_id = creator_user_result.data[0].get("company_id")
                        if creator_company_id:
                            print(f"作成者の会社ID: {creator_company_id} から他のユーザーのステータスを確認します")
                            
                            # 同じ会社の他のユーザーを取得
                            company_users_result = select_data("users", columns="id", filters={"company_id": creator_company_id})
                            if company_users_result and company_users_result.data:
                                # 最初に見つかったユーザーのステータスを確認
                                for company_user in company_users_result.data:
                                    if company_user.get("id") != creator_user_id:
                                        company_user_limits_result = select_data("usage_limits", filters={"user_id": company_user.get("id")})
                                        if company_user_limits_result and company_user_limits_result.data:
                                            company_user_limits = company_user_limits_result.data[0]
                                            company_is_unlimited = bool(company_user_limits.get("is_unlimited", False))
                                            
                                            is_unlimited = company_is_unlimited
                                            if is_unlimited:
                                                questions_limit = 999999
                                                uploads_limit = 999999
                                            else:
                                                questions_limit = 10
                                                uploads_limit = 2
                                            
                                            print(f"✓ 会社の他のユーザーのステータスを継承: {'本番版' if is_unlimited else 'デモ版'}")
                                            break
                                else:
                                    # 同じ会社のユーザーのステータスも見つからない場合はデフォルト
                                    print("同じ会社のユーザーのステータスも見つからないため、デフォルト（デモ版）を適用します。")
                                    is_unlimited = False
                                    questions_limit = 10
                                    uploads_limit = 2
                            else:
                                print("同じ会社のユーザーが見つからないため、デフォルト（デモ版）を適用します。")
                                is_unlimited = False
                                questions_limit = 10
                                uploads_limit = 2
                        else:
                            print("作成者に会社IDが設定されていないため、デフォルト（デモ版）を適用します。")
                            is_unlimited = False
                            questions_limit = 10
                            uploads_limit = 2
                    else:
                        print("作成者の情報が見つからないため、デフォルト（デモ版）を適用します。")
                        is_unlimited = False
                        questions_limit = 10
                        uploads_limit = 2
                except Exception as company_check_error:
                    print(f"会社ユーザーステータス確認エラー: {company_check_error}")
                    print("デフォルト（デモ版）を適用します。")
                is_unlimited = False
                questions_limit = 10
                uploads_limit = 2
        except Exception as e:
            print(f"✗ 作成者の利用制限確認エラー: {e}")
            print("デフォルト（デモ版）を適用します。")
            is_unlimited = False
            questions_limit = 10
            uploads_limit = 2
    else:
        # 作成者が指定されていない場合はデフォルト（デモ版）
        print(f"作成者が指定されていないため、デフォルト（デモ版）を適用")
        is_unlimited = False
        questions_limit = 10
        uploads_limit = 2
    
    # 利用制限レコードを作成
    limit_data = {
        "user_id": user_id,
        "document_uploads_used": 0,
        "document_uploads_limit": uploads_limit,
        "questions_used": 0,
        "questions_limit": questions_limit,
        "is_unlimited": is_unlimited
    }
    
    limit_result = insert_data("usage_limits", limit_data)
    if not limit_result:
        print("✗ 利用制限レコード作成失敗")
        return None
    else:
        print(f"✓ 利用制限レコード作成完了: {'本番版' if is_unlimited else 'デモ版'}")
        print(f"  - 質問制限: {questions_limit}")
        print(f"  - アップロード制限: {uploads_limit}")
    
    # 新規ユーザー作成完了後、同じ会社の他のユーザーとステータスを同期
    if company_id and role in ["user", "employee"]:
        try:
            print("新規ユーザー作成後の会社レベル同期を開始...")
            
            # 同じ会社の他のユーザーを確認
            company_users_result = select_data("users", columns="id, email, role", filters={"company_id": company_id})
            if company_users_result and company_users_result.data:
                # 新規作成したユーザー以外の同じ会社のユーザーを取得
                other_users = [u for u in company_users_result.data if u.get("id") != user_id]
                
                if other_users:
                    # 他のユーザーのステータスを確認して統一
                    for other_user in other_users:
                        other_user_id = other_user.get("id")
                        other_role = other_user.get("role")
                        
                        # adminロールは無視
                        if other_role == "admin":
                            continue
                        
                        # 他のユーザーの利用制限を確認
                        other_limits_result = select_data("usage_limits", filters={"user_id": other_user_id})
                        if other_limits_result and other_limits_result.data:
                            other_limits = other_limits_result.data[0]
                            other_is_unlimited = bool(other_limits.get("is_unlimited", False))
                            
                            # ステータスが異なる場合、新規ユーザーを既存ユーザーに合わせる
                            if other_is_unlimited != is_unlimited:
                                print(f"会社内のステータス不整合を検出。新規ユーザーを {other_user.get('email')} のステータスに合わせます")
                                
                                # 新規ユーザーのステータスを更新
                                new_questions_limit = 999999 if other_is_unlimited else 10
                                new_uploads_limit = 999999 if other_is_unlimited else 2
                                
                                update_result = update_data("usage_limits", {
                                    "is_unlimited": other_is_unlimited,
                                    "questions_limit": new_questions_limit,
                                    "document_uploads_limit": new_uploads_limit
                                }, "user_id", user_id)
                                
                                if update_result:
                                    print(f"✓ 新規ユーザーのステータスを{'本番版' if other_is_unlimited else 'デモ版'}に統一しました")
                                else:
                                    print("✗ 新規ユーザーのステータス統一に失敗しました")
                                break
        except Exception as sync_error:
            print(f"新規ユーザー作成後の同期エラー: {sync_error}")
            # エラーが発生してもユーザー作成は成功とする
    
    print(f"=== ユーザー作成完了 ===")
    print(f"ユーザーID: {user_id}")
    print(f"ステータス: {'本番版' if is_unlimited else 'デモ版'}")
    
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
    print(f"update_usage_count開始 - user_id: {user_id}, field: {field}")
    
    # 現在の値を取得
    current_limits = get_usage_limits(user_id, db)
    print(f"現在の利用制限: {current_limits}")
    
    if not current_limits:
        print("利用制限が見つかりません")
        return None
        
    # 値を更新
    old_value = current_limits.get(field, 0)
    new_value = old_value + 1
    print(f"{field}を{old_value}から{new_value}に更新")
    
    update_data("usage_limits", {field: new_value}, "user_id", user_id)
    
    # 更新後の値を取得
    updated_limits = get_usage_limits(user_id, db)
    print(f"更新後の利用制限: {updated_limits}")
    
    return updated_limits

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

def update_created_accounts_status(creator_user_id: str, new_is_unlimited: bool, db: SupabaseConnection = None) -> int:
    """作成者のステータス変更時に、その人が作成したアカウントも同期する（強化版）"""
    try:
        print(f"=== 作成者ステータス同期開始 ===")
        print(f"作成者ID: {creator_user_id}")
        print(f"新しいステータス: {'本番版' if new_is_unlimited else 'デモ版'}")
        
        # 作成者の詳細な利用制限を取得
        creator_limits_result = select_data("usage_limits", filters={"user_id": creator_user_id})
        if not creator_limits_result or not creator_limits_result.data:
            print("作成者の利用制限情報が見つかりません")
            return 0
        
        creator_limits = creator_limits_result.data[0]
        creator_questions_limit = creator_limits.get("questions_limit", 10 if not new_is_unlimited else 999999)
        creator_uploads_limit = creator_limits.get("document_uploads_limit", 2 if not new_is_unlimited else 999999)
        
        print(f"作成者の利用制限: 質問={creator_questions_limit}, アップロード={creator_uploads_limit}")
        
        # 作成者が作成したユーザーを取得
        created_users_result = select_data("users", columns="id, email, name, role, created_by", filters={"created_by": creator_user_id})
        
        if not created_users_result or not created_users_result.data:
            print("作成したアカウントが見つかりません")
            return 0
        
        print(f"更新対象の子アカウント数: {len(created_users_result.data)}")
        
        updated_count = 0
        failed_updates = []
        
        for user in created_users_result.data:
            child_user_id = user.get("id")
            child_email = user.get("email")
            child_name = user.get("name")
            child_role = user.get("role")
            
            if not child_user_id:
                continue
                
            try:
                # 管理者ロールは常に本番版のため、スキップ
                if child_role == "admin":
                    print(f"管理者アカウントはスキップ: {child_email}")
                    continue
                
                # 子アカウントの現在の利用制限を取得
                current_child_limits_result = select_data("usage_limits", filters={"user_id": child_user_id})
                
                if current_child_limits_result and current_child_limits_result.data:
                    current_child_limits = current_child_limits_result.data[0]
                    current_questions_used = current_child_limits.get("questions_used", 0)
                    current_uploads_used = current_child_limits.get("document_uploads_used", 0)
                else:
                    current_questions_used = 0
                    current_uploads_used = 0
                
                # 新しい利用制限を計算
                if new_is_unlimited:
                    # 本番版に変更する場合
                    new_questions_limit = 999999
                    new_uploads_limit = 999999
                else:
                    # デモ版に変更する場合
                    new_questions_limit = 10
                    new_uploads_limit = 2
                    
                    # 使用済み数が新しい制限を超える場合は制限値に合わせる
                    if current_questions_used > new_questions_limit:
                        current_questions_used = new_questions_limit
                    if current_uploads_used > new_uploads_limit:
                        current_uploads_used = new_uploads_limit
                
                # 子アカウントの利用制限を更新
                update_data_payload = {
                    "is_unlimited": new_is_unlimited,
                    "questions_limit": new_questions_limit,
                    "questions_used": current_questions_used,
                    "document_uploads_limit": new_uploads_limit,
                    "document_uploads_used": current_uploads_used
                }
                
                update_result = update_data("usage_limits", update_data_payload, "user_id", child_user_id)
                
                if update_result:
                    updated_count += 1
                    print(f"✓ 子アカウント更新成功: {child_email} ({child_name})")
                    print(f"  - ステータス: {'本番版' if new_is_unlimited else 'デモ版'}")
                    print(f"  - 質問制限: {new_questions_limit} (使用済み: {current_questions_used})")
                    print(f"  - アップロード制限: {new_uploads_limit} (使用済み: {current_uploads_used})")
                    
                    # さらに、この子アカウントが作成したアカウントも再帰的に更新
                    recursive_updates = update_created_accounts_status(child_user_id, new_is_unlimited, db)
                    if recursive_updates > 0:
                        print(f"  - 再帰的更新: {recursive_updates} 個の孫アカウントを更新")
                        updated_count += recursive_updates
                        
                else:
                    failed_updates.append(child_email)
                    print(f"✗ 子アカウント更新失敗: {child_email}")
                    
            except Exception as child_error:
                failed_updates.append(child_email)
                print(f"✗ 子アカウント更新エラー: {child_email} - {str(child_error)}")
        
        print(f"=== 作成者ステータス同期完了 ===")
        print(f"更新成功: {updated_count} 個")
        if failed_updates:
            print(f"更新失敗: {len(failed_updates)} 個 - {failed_updates}")
        
        return updated_count
        
    except Exception as e:
        print(f"✗ 子アカウントのステータス同期エラー: {e}")
        import traceback
        print(traceback.format_exc())
        return 0

def update_company_users_status(user_id: str, new_is_unlimited: bool, db: SupabaseConnection = None) -> int:
    """userロールの変更をemployeeロールに一方向同期する（シンプル版）"""
    try:
        print(f"=== 会社レベル同期処理開始 ===")
        print(f"対象ユーザーID: {user_id}")
        print(f"新しいステータス: {'本番版' if new_is_unlimited else 'デモ版'}")
        
        # 変更されたユーザーの情報を取得
        user_result = select_data("users", columns="company_id, email, name, role", filters={"id": user_id})
        if not user_result or not user_result.data:
            print("✗ 対象ユーザーが見つかりません")
            return 0
        
        user_data = user_result.data[0]
        company_id = user_data.get("company_id")
        user_email = user_data.get("email")
        user_name = user_data.get("name")
        user_role = user_data.get("role")
        
        print(f"対象ユーザー: {user_email} ({user_name})")
        print(f"ロール: {user_role}")
        print(f"会社ID: {company_id}")
        
        # 会社IDが設定されていない場合は処理しない
        if not company_id:
            print("✗ ユーザーに会社IDが設定されていません")
            return 0
        
        # userロールの変更のみemployeeロールに反映
        if user_role != "user":
            print(f"✗ {user_role}ロールの変更はemployeeロールに反映されません（userロールのみ対象）")
            return 0
        
        print("✓ userロールの変更を同じ会社のemployeeロールに反映します")
        
        # 同じ会社のemployeeロールユーザーを取得
        company_employees_result = select_data("users", 
                                             columns="id, email, name, role", 
                                             filters={"company_id": company_id, "role": "employee"})
        
        if not company_employees_result or not company_employees_result.data:
            print("✗ 同じ会社にemployeeロールのユーザーが見つかりません")
            return 0
        
        employee_users = company_employees_result.data
        print(f"✓ 同期対象のemployeeユーザー: {len(employee_users)}人")
        
        for employee in employee_users:
            print(f"  - {employee.get('email')} ({employee.get('name')})")
        
        # 新しい制限値を計算
        if new_is_unlimited:
            new_questions_limit = 999999
            new_uploads_limit = 999999
        else:
            new_questions_limit = 10
            new_uploads_limit = 2
        
        updated_count = 0
        failed_updates = []
        
        # 各employeeユーザーのステータスを更新
        for employee in employee_users:
            employee_id = employee.get("id")
            employee_email = employee.get("email")
            employee_name = employee.get("name")
            
            if not employee_id:
                continue
            
            try:
                print(f"--- {employee_email} の同期処理開始 ---")
                
                # 現在の利用制限を取得
                current_limits_result = select_data("usage_limits", filters={"user_id": employee_id})
                
                if current_limits_result and current_limits_result.data:
                    current_limits = current_limits_result.data[0]
                    current_questions_used = current_limits.get("questions_used", 0)
                    current_uploads_used = current_limits.get("document_uploads_used", 0)
                    current_is_unlimited = bool(current_limits.get("is_unlimited", False))
                    
                    print(f"現在のステータス: {'本番版' if current_is_unlimited else 'デモ版'}")
                    print(f"現在の使用状況: 質問={current_questions_used}, アップロード={current_uploads_used}")
                else:
                    # usage_limitsレコードが存在しない場合は作成
                    print("⚠ usage_limitsレコードが存在しないため作成します")
                    current_questions_used = 0
                    current_uploads_used = 0
                    current_is_unlimited = False
                    
                    # 新しいusage_limitsレコードを作成
                    limit_data = {
                        "user_id": employee_id,
                        "document_uploads_used": 0,
                        "document_uploads_limit": new_uploads_limit,
                        "questions_used": 0,
                        "questions_limit": new_questions_limit,
                        "is_unlimited": new_is_unlimited
                    }
                    
                    insert_result = insert_data("usage_limits", limit_data)
                    if insert_result:
                        updated_count += 1
                        print(f"✓ usage_limitsレコード作成完了: {'本番版' if new_is_unlimited else 'デモ版'}")
                    else:
                        failed_updates.append(employee_email)
                        print(f"✗ usage_limitsレコード作成失敗")
                    continue
                
                # 既に同じステータスの場合はスキップ
                if current_is_unlimited == new_is_unlimited:
                    print(f"→ 既に同じステータス({'本番版' if new_is_unlimited else 'デモ版'})のためスキップ")
                    continue
                
                # デモ版に変更する場合、使用済み数が制限を超えないよう調整
                adjusted_questions_used = current_questions_used
                adjusted_uploads_used = current_uploads_used
                
                if not new_is_unlimited:
                    if current_questions_used > new_questions_limit:
                        adjusted_questions_used = new_questions_limit
                        print(f"質問使用数を {current_questions_used} → {adjusted_questions_used} に調整")
                    if current_uploads_used > new_uploads_limit:
                        adjusted_uploads_used = new_uploads_limit
                        print(f"アップロード使用数を {current_uploads_used} → {adjusted_uploads_used} に調整")
                
                # 利用制限を更新
                update_result = update_data("usage_limits", {
                    "is_unlimited": new_is_unlimited,
                    "questions_limit": new_questions_limit,
                    "questions_used": adjusted_questions_used,
                    "document_uploads_limit": new_uploads_limit,
                    "document_uploads_used": adjusted_uploads_used
                }, "user_id", employee_id)
                
                if update_result:
                    updated_count += 1
                    print(f"✓ employeeユーザー同期完了: {employee_email}")
                    print(f"  ステータス変更: {'デモ版' if current_is_unlimited else '本番版'} → {'本番版' if new_is_unlimited else 'デモ版'}")
                    print(f"  新しい制限: 質問={new_questions_limit}({adjusted_questions_used}使用済み), アップロード={new_uploads_limit}({adjusted_uploads_used}使用済み)")
                else:
                    failed_updates.append(employee_email)
                    print(f"✗ employeeユーザー同期失敗: {employee_email}")
                    
            except Exception as e:
                failed_updates.append(employee_email)
                print(f"✗ employeeユーザー同期エラー: {employee_email} - {str(e)}")
        
        print(f"=== 会社レベル同期処理完了 ===")
        print(f"同期成功: {updated_count}個のemployeeアカウント")
        if failed_updates:
            print(f"同期失敗: {len(failed_updates)}個 - {failed_updates}")
        
        return updated_count
        
    except Exception as e:
        print(f"✗ 会社レベル同期処理エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return 0

def fix_company_status_inconsistency(company_id: str, db: SupabaseConnection = None) -> int:
    """会社内のユーザーステータス不整合を自動修正する"""
    try:
        print(f"=== 会社ステータス不整合修正開始 ===")
        print(f"会社ID: {company_id}")
        
        # 会社の全ユーザーを取得
        company_users_result = select_data("users", columns="id, email, name, role", filters={"company_id": company_id})
        
        if not company_users_result or not company_users_result.data:
            print("会社のユーザーが見つかりません")
            return 0
        
        # adminロール以外のユーザーを取得
        non_admin_users = [user for user in company_users_result.data if user.get("role") != "admin"]
        
        if not non_admin_users:
            print("修正対象のユーザーがいません")
            return 0
        
        # 各ユーザーのステータスを確認
        user_statuses = {}
        for user in non_admin_users:
            user_id = user.get("id")
            if user_id:
                limits_result = select_data("usage_limits", filters={"user_id": user_id})
                if limits_result and limits_result.data:
                    is_unlimited = bool(limits_result.data[0].get("is_unlimited", False))
                    user_statuses[user_id] = {
                        "email": user.get("email"),
                        "role": user.get("role"),
                        "is_unlimited": is_unlimited
                    }
        
        # ステータスの分布を確認
        unlimited_users = [uid for uid, info in user_statuses.items() if info["is_unlimited"]]
        limited_users = [uid for uid, info in user_statuses.items() if not info["is_unlimited"]]
        
        print(f"本番版ユーザー: {len(unlimited_users)}人")
        print(f"デモ版ユーザー: {len(limited_users)}人")
        
        if len(unlimited_users) == 0 and len(limited_users) == 0:
            print("修正対象のユーザーがいません")
            return 0
        
        # 多数派のステータスに統一
        target_status = len(unlimited_users) >= len(limited_users)
        target_users = limited_users if target_status else unlimited_users
        
        if not target_users:
            print("すべてのユーザーが既に統一されています")
            return 0
        
        print(f"{'本番版' if target_status else 'デモ版'}に統一します ({len(target_users)}人を修正)")
        
        # 制限値を計算
        new_questions_limit = 999999 if target_status else 10
        new_uploads_limit = 999999 if target_status else 2
        
        fixed_count = 0
        for user_id in target_users:
            try:
                # 現在の使用数を取得
                current_limits_result = select_data("usage_limits", filters={"user_id": user_id})
                if current_limits_result and current_limits_result.data:
                    current_limits = current_limits_result.data[0]
                    current_questions_used = current_limits.get("questions_used", 0)
                    current_uploads_used = current_limits.get("document_uploads_used", 0)
                else:
                    current_questions_used = 0
                    current_uploads_used = 0
                
                # デモ版に変更する場合、使用済み数が制限を超える場合は調整
                if not target_status:
                    if current_questions_used > new_questions_limit:
                        current_questions_used = new_questions_limit
                    if current_uploads_used > new_uploads_limit:
                        current_uploads_used = new_uploads_limit
                
                # ステータスを更新
                update_result = update_data("usage_limits", {
                    "is_unlimited": target_status,
                    "questions_limit": new_questions_limit,
                    "questions_used": current_questions_used,
                    "document_uploads_limit": new_uploads_limit,
                    "document_uploads_used": current_uploads_used
                }, "user_id", user_id)
                
                if update_result:
                    fixed_count += 1
                    user_info = user_statuses[user_id]
                    print(f"✓ ステータス修正完了: {user_info['email']} ({user_info['role']})")
                else:
                    print(f"✗ ステータス修正失敗: {user_statuses[user_id]['email']}")
                    
            except Exception as e:
                print(f"✗ ステータス修正エラー: {user_statuses[user_id]['email']} - {str(e)}")
        
        print(f"=== 会社ステータス不整合修正完了 ===")
        print(f"修正成功: {fixed_count} 個のアカウント")
        
        return fixed_count
        
    except Exception as e:
        print(f"会社ステータス不整合修正エラー: {str(e)}")
        return 0

def ensure_usage_limits_integrity(db: SupabaseConnection = None) -> int:
    """データベースの整合性を確保：usage_limitsレコードが存在しないユーザーを修正"""
    try:
        print("=== データベース整合性チェック開始 ===")
        
        # 全ユーザーを取得
        all_users_result = select_data("users", columns="id, email, name, role")
        if not all_users_result or not all_users_result.data:
            print("ユーザーが見つかりません")
            return 0
        
        all_users = all_users_result.data
        print(f"総ユーザー数: {len(all_users)}人")
        
        # 全usage_limitsを取得
        all_limits_result = select_data("usage_limits", columns="user_id")
        existing_user_ids = set()
        if all_limits_result and all_limits_result.data:
            existing_user_ids = {limit.get("user_id") for limit in all_limits_result.data}
        
        print(f"usage_limitsレコード数: {len(existing_user_ids)}件")
        
        # usage_limitsが存在しないユーザーを特定
        missing_users = []
        for user in all_users:
            user_id = user.get("id")
            if user_id and user_id not in existing_user_ids:
                missing_users.append(user)
        
        if not missing_users:
            print("✓ 全ユーザーにusage_limitsレコードが存在します")
            return 0
        
        print(f"⚠ usage_limitsレコードが欠損しているユーザー: {len(missing_users)}人")
        
        fixed_count = 0
        for user in missing_users:
            user_id = user.get("id")
            user_email = user.get("email")
            user_name = user.get("name")
            user_role = user.get("role")
            
            try:
                print(f"--- {user_email} ({user_name}) のusage_limitsレコード作成 ---")
                
                # デフォルトの利用制限を設定
                if user_role == "admin" or user_email == "queue@queueu-tech.jp":
                    # 管理者は無制限
                    is_unlimited = True
                    questions_limit = 999999
                    uploads_limit = 999999
                else:
                    # 一般ユーザーはデモ版
                    is_unlimited = False
                    questions_limit = 10
                    uploads_limit = 2
                
                limit_data = {
                    "user_id": user_id,
                    "document_uploads_used": 0,
                    "document_uploads_limit": uploads_limit,
                    "questions_used": 0,
                    "questions_limit": questions_limit,
                    "is_unlimited": is_unlimited
                }
                
                insert_result = insert_data("usage_limits", limit_data)
                if insert_result:
                    fixed_count += 1
                    print(f"✓ usage_limitsレコード作成完了: {'本番版' if is_unlimited else 'デモ版'}")
                else:
                    print(f"✗ usage_limitsレコード作成失敗")
                    
            except Exception as e:
                print(f"✗ {user_email} のusage_limitsレコード作成エラー: {str(e)}")
        
        print(f"=== データベース整合性チェック完了 ===")
        print(f"修正完了: {fixed_count}個のusage_limitsレコードを作成")
        
        return fixed_count
        
    except Exception as e:
        print(f"✗ データベース整合性チェックエラー: {str(e)}")
        return 0

def record_plan_change(user_id: str, from_plan: str, to_plan: str, db: SupabaseConnection = None, duration_days: int = None) -> bool:
    """プラン変更履歴を記録する"""
    try:
        print(f"=== プラン履歴記録開始 ===")
        print(f"ユーザーID: {user_id}")
        print(f"変更: {from_plan} → {to_plan}")
        
        # プラン名を正規化（unlimited -> production, demo -> demo）
        normalized_from_plan = "production" if from_plan == "unlimited" else from_plan
        normalized_to_plan = "production" if to_plan == "unlimited" else to_plan
        
        print(f"正規化後: {normalized_from_plan} → {normalized_to_plan}")
        
        # 履歴レコードを挿入
        plan_history_data = {
            "user_id": user_id,
            "from_plan": normalized_from_plan,
            "to_plan": normalized_to_plan,
            "changed_at": datetime.datetime.now().isoformat(),
            "duration_days": duration_days
        }
        
        result = insert_data("plan_history", plan_history_data)
        
        if result:
            print(f"✓ プラン履歴記録完了")
            return True
        else:
            print(f"✗ プラン履歴記録失敗")
            return False
            
    except Exception as e:
        print(f"✗ プラン履歴記録エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def get_plan_history(user_id: str = None, db: SupabaseConnection = None) -> List[dict]:
    """プラン履歴を人単位でグループ化して取得する"""
    try:
        print(f"=== プラン履歴取得開始 ===")
        
        # ユーザー情報とプラン履歴を結合して取得
        if user_id:
            print(f"特定ユーザーの履歴を取得: {user_id}")
            history_result = select_data("plan_history", 
                                       columns="id, user_id, from_plan, to_plan, changed_at, duration_days",
                                       filters={"user_id": user_id})
        else:
            print("全ユーザーの履歴を取得")
            history_result = select_data("plan_history", 
                                       columns="id, user_id, from_plan, to_plan, changed_at, duration_days")
        
        if not history_result or not history_result.data:
            print("プラン履歴が見つかりません")
            return []
        
        history_list = history_result.data
        print(f"取得した履歴件数: {len(history_list)}")
        
        # ユーザー別でグループ化して整理
        user_histories = {}
        
        for history in history_list:
            user_id_key = history.get("user_id")
            
            # ユーザー情報を取得（初回のみ）
            if user_id_key not in user_histories:
                user_result = select_data("users", 
                                            columns="email, name, company_id", 
                                            filters={"id": user_id_key})
            
                if user_result and user_result.data:
                    user_info = user_result.data[0]
                    user_histories[user_id_key] = {
                        "user_id": user_id_key,
                        "user_email": user_info.get("email"),
                        "user_name": user_info.get("name"),
                        "company_id": user_info.get("company_id"),
                        "changes": []
                    }
                else:
                    user_histories[user_id_key] = {
                        "user_id": user_id_key,
                        "user_email": "不明",
                        "user_name": "不明", 
                        "company_id": None,
                        "changes": []
                    }
            
            # 履歴情報を追加
            change_info = {
                "id": history.get("id"),
                "from_plan": history.get("from_plan"),
                "to_plan": history.get("to_plan"),
                "changed_at": history.get("changed_at"),
                "duration_days": history.get("duration_days")
            }
            user_histories[user_id_key]["changes"].append(change_info)
        
        # 各ユーザーの変更履歴を時系列で並び替え（新しいものが上）
        for user_id_key in user_histories:
            user_histories[user_id_key]["changes"].sort(
                key=lambda x: x.get("changed_at", ""), reverse=True
            )
            
            # 最新の変更情報をユーザー情報に追加
            if user_histories[user_id_key]["changes"]:
                latest_change = user_histories[user_id_key]["changes"][0]
                user_histories[user_id_key]["latest_change"] = latest_change.get("changed_at")
                user_histories[user_id_key]["current_plan"] = latest_change.get("to_plan")
                user_histories[user_id_key]["total_changes"] = len(user_histories[user_id_key]["changes"])
            else:
                user_histories[user_id_key]["latest_change"] = None
                user_histories[user_id_key]["current_plan"] = "不明"
                user_histories[user_id_key]["total_changes"] = 0
        
        # ユーザーリストを最新変更日時でソート（新しく変更されたユーザーが上）
        sorted_users = sorted(
            user_histories.values(), 
            key=lambda x: x.get("latest_change", ""), 
            reverse=True
        )
        
        print(f"✓ プラン履歴取得完了: {len(sorted_users)}人の履歴")
        return sorted_users
        
    except Exception as e:
        print(f"✗ プラン履歴取得エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []

def save_application(application_data: dict, db: SupabaseConnection = None) -> str:
    """申請データをデータベースに保存する"""
    try:
        print(f"=== 申請データ保存開始 ===")
        print(f"会社名: {application_data.get('company_name')}")
        print(f"担当者: {application_data.get('contact_name')}")
        print(f"メール: {application_data.get('email')}")
        
        # 一意のIDを生成
        import uuid
        application_id = str(uuid.uuid4())
        
        # 保存用データを準備
        save_data = {
            "id": application_id,
            "company_name": application_data.get("company_name", ""),
            "contact_name": application_data.get("contact_name", ""),
            "email": application_data.get("email", ""),
            "phone": application_data.get("phone", ""),
            "expected_users": application_data.get("expected_users", ""),
            "current_usage": application_data.get("current_usage", ""),
            "message": application_data.get("message", ""),
            "application_type": application_data.get("application_type", "production-upgrade"),
            "status": "pending",
            "submitted_at": datetime.datetime.now().isoformat()
        }
        
        # データベースに挿入
        result = insert_data("applications", save_data)
        
        if result:
            print(f"✓ 申請データ保存完了: ID={application_id}")
            return application_id
        else:
            print(f"✗ 申請データ保存失敗")
            return None
            
    except Exception as e:
        print(f"✗ 申請データ保存エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def get_applications(status: str = None, db: SupabaseConnection = None) -> List[dict]:
    """申請データを取得する"""
    try:
        print(f"=== 申請データ取得開始 ===")
        
        # フィルター条件を設定
        filters = {}
        if status:
            filters["status"] = status
            print(f"ステータスフィルター: {status}")
        
        # 申請データを取得
        applications_result = select_data("applications", 
                                        columns="*",
                                        filters=filters if filters else None)
        
        if not applications_result or not applications_result.data:
            print("申請データが見つかりません")
            return []
        
        applications = applications_result.data
        print(f"取得した申請件数: {len(applications)}")
        
        # submitted_atで降順にソート（新しいものが上）
        applications.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)
        
        print(f"✓ 申請データ取得完了: {len(applications)}件")
        return applications
        
    except Exception as e:
        print(f"✗ 申請データ取得エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []

def update_application_status(application_id: str, status: str, processed_by: str = None, notes: str = None, db: SupabaseConnection = None) -> bool:
    """申請のステータスを更新する"""
    try:
        print(f"=== 申請ステータス更新開始 ===")
        print(f"申請ID: {application_id}")
        print(f"新ステータス: {status}")
        
        # 更新データを準備
        update_data = {
            "status": status,
            "processed_at": datetime.datetime.now().isoformat()
        }
        
        if processed_by:
            update_data["processed_by"] = processed_by
        
        if notes:
            update_data["notes"] = notes
        
        # データベースを更新
        result = update_data_by_id("applications", update_data, "id", application_id)
        
        if result:
            print(f"✓ 申請ステータス更新完了")
            return True
        else:
            print(f"✗ 申請ステータス更新失敗")
            return False
            
    except Exception as e:
        print(f"✗ 申請ステータス更新エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False