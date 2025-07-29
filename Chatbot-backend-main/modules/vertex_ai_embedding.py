"""
✅ Vertex AI Embedding モジュール
text-multilingual-embedding-002を使用した3072次元ベクトル生成
"""

import os
import json
import logging
import tempfile
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
        self.model_name = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
        self.location = "us-central1"
        
        # 認証設定（3つの方法をサポート）
        self._setup_credentials()
        
        try:
            # Vertex AI初期化
            vertexai.init(project=self.project_id, location=self.location)
            
            # gemini-embedding-001 を含む全てのモデルで TextEmbeddingModel を使用
            self.model = TextEmbeddingModel.from_pretrained(self.model_name)
            
            self.use_vertex_ai = True
            # 次元数を動的に取得
            dimensions = 3072 if "gemini-embedding-001" in self.model_name else 3072
            logger.info(f"✅ Vertex AI Embedding初期化完了: {self.model_name} ({dimensions}次元)")
        except Exception as e:
            logger.error(f"❌ Vertex AI初期化エラー: {e}")
            self.use_vertex_ai = False
    
    def _setup_credentials(self):
        """認証情報を設定（3つの方法をサポート）"""
        # 方法1: JSON文字列を環境変数から読み込み（最優先）
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if credentials_json:
            try:
                # JSON文字列をパースしてテンポラリファイルに保存
                credentials_data = json.loads(credentials_json)
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                json.dump(credentials_data, temp_file, indent=2)
                temp_file.close()
                
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file.name
                logger.info(f"✅ サービスアカウント認証設定（環境変数JSON・最優先）: {temp_file.name}")
                return
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON環境変数の解析エラー: {e}")
        
        # 方法2: JSONファイルパス
        service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if service_account_path and os.path.exists(service_account_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path
            logger.info(f"✅ サービスアカウント認証設定（ファイルパス）: {service_account_path}")
            return
        
        # 方法3: 個別環境変数から構築
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        private_key = os.getenv("GOOGLE_CLOUD_PRIVATE_KEY")
        client_email = os.getenv("GOOGLE_CLOUD_CLIENT_EMAIL")
        
        if project_id and private_key and client_email:
            try:
                credentials_data = {
                    "type": "service_account",
                    "project_id": project_id,
                    "private_key_id": os.getenv("GOOGLE_CLOUD_PRIVATE_KEY_ID", ""),
                    "private_key": private_key,
                    "client_email": client_email,
                    "client_id": os.getenv("GOOGLE_CLOUD_CLIENT_ID", ""),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{client_email.replace('@', '%40')}",
                    "universe_domain": "googleapis.com"
                }
                
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                json.dump(credentials_data, temp_file, indent=2)
                temp_file.close()
                
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file.name
                logger.info(f"✅ サービスアカウント認証設定（個別環境変数）: {temp_file.name}")
                return
            except Exception as e:
                logger.error(f"❌ 個別環境変数からの認証情報構築エラー: {e}")
        
        logger.warning("⚠️ 認証情報が設定されていません")
    
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
        
        # gemini-embedding-001 はバッチサイズ1のみサポート
        if "gemini-embedding-001" in self.model_name:
            logger.info(f"📦 gemini-embedding-001: 個別処理モード ({len(texts)}件)")
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