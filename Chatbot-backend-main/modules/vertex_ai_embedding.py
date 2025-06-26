"""
🚫 Vertex AI Embedding モジュール（無効化済み）
このモジュールは使用されません。text-embedding-004を直接使用してください。
"""

import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class VertexAIEmbeddingClient:
    """Vertex AI Embedding クライアント（無効化済み）"""
    
    def __init__(self):
        """初期化（常に無効）"""
        logger.info("🚫 Vertex AI Embeddingは無効化されています。text-embedding-004を使用してください。")
        self.use_vertex_ai = False
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """テキストのエンベディングを生成（無効化済み）"""
        logger.warning("🚫 Vertex AI Embeddingは無効化されています。text-embedding-004を使用してください。")
        return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """複数テキストのエンベディングをバッチ生成（無効化済み）"""
        logger.warning("🚫 Vertex AI Embeddingは無効化されています。text-embedding-004を使用してください。")
        return [None] * len(texts)

# グローバルインスタンス
_vertex_ai_client = None

def get_vertex_ai_embedding_client() -> Optional[VertexAIEmbeddingClient]:
    """Vertex AI Embeddingクライアントを取得（シングルトンパターン）"""
    global _vertex_ai_client
    
    if _vertex_ai_client is None:
        try:
            _vertex_ai_client = VertexAIEmbeddingClient()
            logger.info("✅ Vertex AI Embeddingクライアント初期化完了")
        except Exception as e:
            logger.error(f"❌ Vertex AI Embeddingクライアント初期化エラー: {e}")
            return None
    
    return _vertex_ai_client

def vertex_ai_embedding_available() -> bool:
    """Vertex AI Embeddingが利用可能かチェック（常にFalse）"""
    logger.info("🚫 Vertex AI Embeddingは無効化されています。")
    return False