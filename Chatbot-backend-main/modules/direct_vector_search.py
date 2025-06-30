"""
直接ベクトル検索システム
ベクトルデータベースに直接アクセスする高速検索システム
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DirectVectorSearchSystem:
    """直接ベクトル検索システムクラス"""
    
    def __init__(self):
        self.available = False
        logger.info("直接ベクトル検索システムを初期化しました（フォールバック版）")
    
    async def search(self, query: str, company_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        直接ベクトル検索を実行
        
        Args:
            query: 検索クエリ
            company_id: 会社ID
            limit: 結果の最大数
            
        Returns:
            検索結果のリスト
        """
        logger.warning("直接ベクトル検索システムは利用できません（フォールバック版）")
        return []
    
    def search_sync(self, query: str, company_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        同期版直接ベクトル検索を実行
        
        Args:
            query: 検索クエリ
            company_id: 会社ID
            limit: 結果の最大数
            
        Returns:
            検索結果のリスト
        """
        logger.warning("直接ベクトル検索システムは利用できません（フォールバック版）")
        return []

def direct_vector_search_available() -> bool:
    """直接ベクトル検索システムが利用可能かチェック"""
    return False  # フォールバック版では常にFalse

# グローバルインスタンス
_direct_vector_search_instance = None

def get_direct_vector_search_instance() -> Optional[DirectVectorSearchSystem]:
    """直接ベクトル検索システムのインスタンスを取得"""
    global _direct_vector_search_instance
    if _direct_vector_search_instance is None:
        _direct_vector_search_instance = DirectVectorSearchSystem()
    return _direct_vector_search_instance

async def get_direct_vector_search_instance_async() -> Optional[DirectVectorSearchSystem]:
    """非同期版直接ベクトル検索システムのインスタンスを取得"""
    return get_direct_vector_search_instance()