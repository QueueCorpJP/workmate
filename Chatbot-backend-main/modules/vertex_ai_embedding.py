"""
🧠 Vertex AI Embedding モジュール
Vertex AI の gemini-embedding-001 モデルを使用したエンベディング生成
"""

import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class VertexAIEmbeddingClient:
    """Vertex AI Embedding クライアント"""
    
    def __init__(self):
        """初期化"""
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = "global"  # グローバルエンドポイント使用
        self.model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
        self.use_vertex_ai = os.getenv("USE_VERTEX_AI", "false").lower() == "true"
        
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT 環境変数が設定されていません")
        
        if self.use_vertex_ai:
            try:
                # Vertex AI初期化テスト
                import vertexai
                from vertexai.language_models import TextEmbeddingModel
                vertexai.init(project=self.project_id, location=self.location)
                
                # 認証テスト用の簡単なリクエスト
                try:
                    model = TextEmbeddingModel.from_pretrained(self.model_name)
                    # 小さなテストテキストで認証確認
                    test_embeddings = model.get_embeddings(["test"])
                    logger.info(f"✅ Vertex AI Embedding初期化完了: {self.model_name} (global endpoint)")
                except Exception as auth_error:
                    logger.warning(f"⚠️ Vertex AI認証エラー: {auth_error}")
                    logger.info("🔄 標準Gemini APIにフォールバック")
                    self.use_vertex_ai = False
                    
            except ImportError:
                logger.error("❌ google-cloud-aiplatform ライブラリがインストールされていません")
                self.use_vertex_ai = False
            except Exception as e:
                logger.error(f"❌ Vertex AI初期化エラー: {e}")
                self.use_vertex_ai = False
        else:
            logger.info("🔄 USE_VERTEX_AI=false のため、Vertex AI Embeddingは無効")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """テキストのエンベディングを生成"""
        if not self.use_vertex_ai:
            logger.warning("Vertex AI Embeddingが無効のため、None を返します")
            return None
        
        try:
            # Vertex AI Generative AI API を使用
            import vertexai
            from vertexai.language_models import TextEmbeddingModel
            
            # Vertex AI初期化
            vertexai.init(project=self.project_id, location=self.location)
            
            # テキストエンベディングモデルを取得
            model = TextEmbeddingModel.from_pretrained(self.model_name)
            
            # エンベディング生成
            embeddings = model.get_embeddings([text])
            
            if embeddings and len(embeddings) > 0:
                embedding_values = embeddings[0].values
                logger.info(f"✅ Vertex AI Embedding生成完了: {len(embedding_values)}次元")
                return embedding_values
            
            logger.error("❌ Vertex AI Embeddingレスポンスが無効です")
            return None
            
        except Exception as e:
            logger.error(f"❌ Vertex AI Embedding生成エラー: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """複数テキストのエンベディングをバッチ生成"""
        if not self.use_vertex_ai:
            logger.warning("Vertex AI Embeddingが無効のため、空のリストを返します")
            return [None] * len(texts)
        
        try:
            # Vertex AI Generative AI API を使用
            import vertexai
            from vertexai.language_models import TextEmbeddingModel
            
            # Vertex AI初期化
            vertexai.init(project=self.project_id, location=self.location)
            
            # テキストエンベディングモデルを取得
            model = TextEmbeddingModel.from_pretrained(self.model_name)
            
            # バッチでエンベディング生成
            embeddings_response = model.get_embeddings(texts)
            
            # レスポンスからエンベディングリストを取得
            embeddings = []
            for embedding in embeddings_response:
                if embedding and hasattr(embedding, 'values'):
                    embeddings.append(embedding.values)
                else:
                    embeddings.append(None)
            
            logger.info(f"✅ Vertex AI バッチEmbedding生成完了: {len(embeddings)}件")
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Vertex AI バッチEmbedding生成エラー: {e}")
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
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        use_vertex_ai = os.getenv("USE_VERTEX_AI", "false").lower() == "true"
        
        return bool(project_id and use_vertex_ai)
    except Exception:
        return False