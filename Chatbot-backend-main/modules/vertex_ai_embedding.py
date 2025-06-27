"""
✅ Vertex AI Embedding モジュール
text-multilingual-embedding-002を使用した768次元ベクトル生成
"""

import os
import json
import logging
from typing import List, Optional
from dotenv import load_dotenv

try:
    from google.cloud import aiplatform
    from vertexai.language_models import TextEmbeddingModel
    import vertexai
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False

# 環境変数読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class VertexAIEmbeddingClient:
    """Vertex AI Embedding クライアント"""
    
    def __init__(self):
        """初期化"""
        if not VERTEX_AI_AVAILABLE:
            logger.error("❌ Vertex AI ライブラリがインストールされていません")
            self.use_vertex_ai = False
            return
            
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "workmate-462302")
        self.model_name = os.getenv("EMBEDDING_MODEL", "text-multilingual-embedding-002")
        self.location = "us-central1"
        
        # サービスアカウント認証の設定
        service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if service_account_path and os.path.exists(service_account_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path
            logger.info(f"✅ サービスアカウント認証設定: {service_account_path}")
        
        try:
            # Vertex AI初期化
            vertexai.init(project=self.project_id, location=self.location)
            
            # gemini-embedding-001 を含む全てのモデルで TextEmbeddingModel を使用
            self.model = TextEmbeddingModel.from_pretrained(self.model_name)
            
            self.use_vertex_ai = True
            # 次元数を動的に取得
            dimensions = 768 if "text-multilingual-embedding-002" in self.model_name else 3072
            logger.info(f"✅ Vertex AI Embedding初期化完了: {self.model_name} ({dimensions}次元)")
        except Exception as e:
            logger.error(f"❌ Vertex AI初期化エラー: {e}")
            self.use_vertex_ai = False
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """テキストのエンベディングを生成"""
        if not self.use_vertex_ai:
            logger.warning("❌ Vertex AI Embeddingが利用できません")
            return None
            
        try:
            # 全てのモデルで get_embeddings を使用
            embeddings = self.model.get_embeddings([text])
            if embeddings and len(embeddings) > 0:
                embedding_vector = embeddings[0].values
                logger.debug(f"✅ Embedding生成成功: {len(embedding_vector)}次元")
                return embedding_vector
            else:
                logger.error("❌ Embedding生成失敗: 空の結果")
                return None
        except Exception as e:
            logger.error(f"❌ Embedding生成エラー: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """複数テキストのエンベディングをバッチ生成"""
        if not self.use_vertex_ai:
            logger.warning("❌ Vertex AI Embeddingが利用できません")
            return [None] * len(texts)
        
        # text-multilingual-embedding-002 はバッチサイズ1のみサポート
        if "text-multilingual-embedding-002" in self.model_name:
            logger.info(f"📦 text-multilingual-embedding-002: 個別処理モード ({len(texts)}件)")
            results = []
            for i, text in enumerate(texts):
                embedding = self.generate_embedding(text)
                results.append(embedding)
                logger.debug(f"✅ Embedding {i+1}/{len(texts)} 生成完了")
            return results
        
        # その他のモデルは従来のバッチ処理
        try:
            embeddings = self.model.get_embeddings(texts)
            results = []
            for i, embedding in enumerate(embeddings):
                if embedding and hasattr(embedding, 'values'):
                    results.append(embedding.values)
                    logger.debug(f"✅ Embedding {i+1}/{len(texts)} 生成成功: {len(embedding.values)}次元")
                else:
                    results.append(None)
                    logger.error(f"❌ Embedding {i+1}/{len(texts)} 生成失敗")
            return results
        except Exception as e:
            logger.error(f"❌ バッチEmbedding生成エラー: {e}")
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
    """Vertex AI Embeddingが利用可能かチェック"""
    if not VERTEX_AI_AVAILABLE:
        return False
    
    client = get_vertex_ai_embedding_client()
    return client is not None and client.use_vertex_ai