"""
Supabase アダプター
Supabaseとの接続とCRUD操作を管理します
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid

# 環境変数を読み込み
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class SupabaseResult:
    """Supabase操作の結果を格納するクラス"""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    count: Optional[int] = None

# グローバルSupabaseクライアント
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """Supabaseクライアントのシングルトンインスタンスを取得"""
    global _supabase_client
    
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL と SUPABASE_KEY 環境変数が設定されていません")
        
        try:
            # HTTPクライアントの設定を明示的に指定
            from supabase import create_client, Client
            from supabase.client import ClientOptions
            
            # デフォルトの設定でクライアントを作成
            _supabase_client = create_client(
                url, 
                key,
                options=ClientOptions(
                    postgrest_client_timeout=10,
                    storage_client_timeout=10,
                )
            )
            logger.info("✅ Supabaseクライアント初期化完了")
        except Exception as e:
            logger.error(f"❌ Supabaseクライアント初期化エラー: {e}")
            # シンプルな初期化に戻す
            try:
                _supabase_client = create_client(url, key)
                logger.info("✅ Supabaseクライアント初期化完了（シンプル方法）")
            except Exception as e2:
                logger.error(f"❌ Supabaseクライアント初期化エラー（シンプル方法も失敗）: {e2}")
                raise
    
    return _supabase_client

def select_data(table: str, columns: str = "*", filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None, offset: Optional[int] = None, order: Optional[str] = None) -> SupabaseResult:
    """
    データを検索
    
    Args:
        table: テーブル名
        columns: 取得する列（デフォルト: "*"）
        filters: フィルタ条件のディクショナリ
        limit: 取得件数制限
        offset: オフセット（ページネーション用）
        order: ソート順（例: "timestamp desc"）
    
    Returns:
        SupabaseResult: 操作結果
    """
    try:
        client = get_supabase_client()
        query = client.table(table).select(columns)
        
        # フィルタを適用
        if filters:
            for key, value in filters.items():
                if value is not None:
                    query = query.eq(key, value)
        
        # ソート順を適用
        if order:
            # "timestamp desc" や "created_at asc" などの形式をパース
            order_parts = order.strip().split()
            if len(order_parts) >= 1:
                column = order_parts[0]
                ascending = len(order_parts) == 1 or order_parts[1].lower() != 'desc'
                query = query.order(column, desc=not ascending)
        
        # オフセットを適用
        if offset:
            query = query.range(offset, offset + (limit or 1000) - 1)
        elif limit:
            query = query.limit(limit)
        
        result = query.execute()
        
        return SupabaseResult(
            success=True,
            data=result.data,
            count=len(result.data) if result.data else 0
        )
        
    except Exception as e:
        logger.error(f"❌ SELECT操作エラー: {e}")
        return SupabaseResult(
            success=False,
            error=str(e)
        )

def insert_data(table: str, data: Dict[str, Any]) -> SupabaseResult:
    """
    データを挿入
    
    Args:
        table: テーブル名
        data: 挿入するデータ
    
    Returns:
        SupabaseResult: 操作結果
    """
    try:
        client = get_supabase_client()

        # usage_limits テーブルには id カラムが存在しないため自動付与しない
        if table != "usage_limits" and 'id' not in data:
            data['id'] = str(uuid.uuid4())

        try:
            result = client.table(table).insert(data).execute()
        except Exception as inner_e:
            # id カラムが無いと怒られた場合は id を外してリトライ
            err_msg = str(inner_e)
            if "Could not find the 'id' column" in err_msg and 'id' in data:
                _ = data.pop('id', None)
                result = client.table(table).insert(data).execute()
            else:
                raise

        return SupabaseResult(
            success=True,
            data=result.data,
            count=len(result.data) if result.data else 0
        )
        
    except Exception as e:
        logger.error(f"❌ INSERT操作エラー: {e}")
        return SupabaseResult(
            success=False,
            error=str(e)
        )

def update_data(table: str, filter_key: str, filter_value: Any, data: Dict[str, Any]) -> SupabaseResult:
    """
    データを更新
    
    Args:
        table: テーブル名
        filter_key: フィルタキー
        filter_value: フィルタ値
        data: 更新するデータ
    
    Returns:
        SupabaseResult: 操作結果
    """
    try:
        client = get_supabase_client()
        result = client.table(table).update(data).eq(filter_key, filter_value).execute()
        
        return SupabaseResult(
            success=True,
            data=result.data,
            count=len(result.data) if result.data else 0
        )
        
    except Exception as e:
        logger.error(f"❌ UPDATE操作エラー: {e}")
        return SupabaseResult(
            success=False,
            error=str(e)
        )

def delete_data(table: str, filter_key: str, filter_value: Any) -> SupabaseResult:
    """
    データを削除
    
    Args:
        table: テーブル名
        filter_key: フィルタキー
        filter_value: フィルタ値
    
    Returns:
        SupabaseResult: 操作結果
    """
    try:
        client = get_supabase_client()
        result = client.table(table).delete().eq(filter_key, filter_value).execute()
        
        return SupabaseResult(
            success=True,
            data=result.data,
            count=len(result.data) if result.data else 0
        )
        
    except Exception as e:
        logger.error(f"❌ DELETE操作エラー: {e}")
        return SupabaseResult(
            success=False,
            error=str(e)
        )

def execute_query(query: str, params: Optional[List[Any]] = None) -> SupabaseResult:
    """
    生のSQLクエリを実行
    
    Args:
        query: SQLクエリ
        params: クエリパラメータ
    
    Returns:
        SupabaseResult: 操作結果
    """
    try:
        client = get_supabase_client()
        
        # Supabase PostgREST APIを使用してSQLを実行
        # logger.warning("⚠️ execute_query: 生のSQL実行は推奨されません。基本的なCRUD操作を使用してください。")
        
        # SupabaseのrpcまたはPostgREST機能を使用してSQLを実行
        # この実装では基本的なSELECTクエリのみサポート
        if query.strip().upper().startswith('SELECT'):
            try:
                # PostgRESTを使用した生SQLの実行（制限的）
                # ここでは簡単な実装として、テーブル名を抽出してSELECT操作に変換
                # 実際の本格的な実装では、SQLパーサーが必要
                
                # より安全な実装：エラーを返して基本CRUD操作の使用を促す
                return SupabaseResult(
                    success=False,
                    error="生のSQL実行は制限されています。基本的なCRUD操作（select_data, insert_data等）を使用してください。",
                    data=[]
                )
                
            except Exception as inner_e:
                logger.error(f"❌ SQL実行エラー: {inner_e}")
                return SupabaseResult(
                    success=False,
                    error=f"SQL実行エラー: {str(inner_e)}",
                    data=[]
                )
        else:
            # SELECT以外のクエリは拒否
            return SupabaseResult(
                success=False,
                error="SELECT以外のクエリは実行できません",
                data=[]
            )
        
    except Exception as e:
        logger.error(f"❌ クエリ実行エラー: {e}")
        return SupabaseResult(
            success=False,
            error=str(e),
            data=[]
        )

def test_connection() -> bool:
    """
    Supabase接続をテスト
    
    Returns:
        bool: 接続成功の場合True
    """
    try:
        client = get_supabase_client()
        # 簡単なクエリでテスト
        result = client.table('users').select('id').limit(1).execute()
        logger.info("✅ Supabase接続テスト成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ Supabase接続テスト失敗: {e}")
        return False

# 後方互換性のためのエイリアス
def get_data(table: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """後方互換性のための関数"""
    result = select_data(table, filters=filters)
    return result.data if result.success else []

def create_data(table: str, data: Dict[str, Any]) -> Optional[str]:
    """後方互換性のための関数"""
    result = insert_data(table, data)
    if result.success and result.data:
        return result.data[0].get('id')
    return None 