"""
🔄 複数API対応エンベディング生成モジュール
4つのAPIキーを使用してレート制限に対応
gemini-embedding-001モデルのみ使用（3072次元）
"""

import os
import logging
import asyncio
import time
from typing import List, Optional, Dict, Any
from enum import Enum
from dotenv import load_dotenv
import google.generativeai as genai

# 環境変数読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class APIKeyStatus(Enum):
    """APIキーの状態"""
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"
    ERROR = "error"

class MultiAPIEmbeddingClient:
    """複数API対応エンベディングクライアント"""
    
    def __init__(self):
        # モデル・次元数を絶対固定（ユーザー要望）
        self.embedding_model = "models/gemini-embedding-001"
        self.expected_dimensions = 3072
        
        # 10個のAPIキーを設定
        self.api_keys = [
            os.getenv("GOOGLE_API_KEY_1") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
            os.getenv("GOOGLE_API_KEY_2"),
            os.getenv("GOOGLE_API_KEY_3"),
            os.getenv("GOOGLE_API_KEY_4"),
            os.getenv("GOOGLE_API_KEY_5"),
            os.getenv("GOOGLE_API_KEY_6"),
            os.getenv("GOOGLE_API_KEY_7"),
            os.getenv("GOOGLE_API_KEY_8"),
            os.getenv("GOOGLE_API_KEY_9"),
            os.getenv("GOOGLE_API_KEY_10")
        ]
        
        # 有効なAPIキーのみ保持
        self.api_keys = [key for key in self.api_keys if key]
        
        if not self.api_keys:
            raise ValueError("少なくとも1つのAPIキーが必要です (GOOGLE_API_KEY_1～10)")
        
        # 各APIキーの状態管理
        self.api_status = {}
        self.api_clients = {}
        self.api_last_error = {}
        self.api_rate_limit_reset = {}
        
        # APIキーごとのクライアントを初期化
        for i, api_key in enumerate(self.api_keys):
            client_name = f"client_{i+1}"
            try:
                # google.generativeai.Client は存在しないため、APIキーを直接保存
                self.api_clients[client_name] = api_key
                self.api_status[client_name] = APIKeyStatus.ACTIVE
                self.api_last_error[client_name] = None
                self.api_rate_limit_reset[client_name] = 0
                logger.info(f"✅ APIクライアント {client_name} 初期化完了")
            except Exception as e:
                logger.error(f"❌ APIクライアント {client_name} 初期化失敗: {e}")
                self.api_status[client_name] = APIKeyStatus.ERROR
                self.api_last_error[client_name] = str(e)
        
        # 現在使用中のクライアントインデックス
        self.current_client_index = 0
        
        logger.info(f"🧠 複数API対応エンベディングクライアント初期化完了")
        logger.info(f"📊 使用可能APIキー: {len(self.api_keys)}個")
        logger.info(f"🎯 モデル: {self.embedding_model} ({self.expected_dimensions}次元)")
    
    def _get_active_client(self) -> Optional[tuple]:
        """アクティブなクライアントを取得"""
        current_time = time.time()
        
        # 現在のクライアントから開始して、利用可能なクライアントを探す
        for attempt in range(len(self.api_clients)):
            client_name = f"client_{(self.current_client_index + attempt) % len(self.api_clients) + 1}"
            
            if client_name not in self.api_clients:
                continue
            
            status = self.api_status.get(client_name, APIKeyStatus.ERROR)
            
            # レート制限のリセット時間をチェック
            if status == APIKeyStatus.RATE_LIMITED:
                reset_time = self.api_rate_limit_reset.get(client_name, 0)
                if current_time > reset_time:
                    self.api_status[client_name] = APIKeyStatus.ACTIVE
                    status = APIKeyStatus.ACTIVE
                    logger.info(f"🔄 {client_name} レート制限リセット")
            
            if status == APIKeyStatus.ACTIVE:
                # APIキーを返す
                return client_name, self.api_clients[client_name]
        
        return None
    
    def _is_rate_limit_error(self, error_message: str) -> bool:
        """レート制限エラーかどうかを判定"""
        rate_limit_indicators = [
            "429",
            "rate limit",
            "quota exceeded",
            "too many requests",
            "requests per minute",
            "requests per day",
            "API quota exceeded"
        ]
        
        error_lower = error_message.lower()
        return any(indicator in error_lower for indicator in rate_limit_indicators)
    
    def _is_quota_exceeded_error(self, error_message: str) -> bool:
        """クォータ超過エラーかどうかを判定"""
        quota_indicators = [
            "quota exceeded",
            "billing quota exceeded",
            "daily quota exceeded",
            "monthly quota exceeded",
            "usage limit exceeded"
        ]
        
        error_lower = error_message.lower()
        return any(indicator in error_lower for indicator in quota_indicators)
    
    def _handle_api_error(self, client_name: str, error: Exception):
        """APIエラーを処理してクライアントの状態を更新"""
        error_message = str(error)
        self.api_last_error[client_name] = error_message
        
        if self._is_rate_limit_error(error_message):
            self.api_status[client_name] = APIKeyStatus.RATE_LIMITED
            # レート制限の場合、60秒後にリセット
            self.api_rate_limit_reset[client_name] = time.time() + 60
            logger.warning(f"⚠️ {client_name} レート制限エラー: {error_message}")
            
        elif self._is_quota_exceeded_error(error_message):
            self.api_status[client_name] = APIKeyStatus.QUOTA_EXCEEDED
            logger.error(f"❌ {client_name} クォータ超過エラー: {error_message}")
            
        else:
            self.api_status[client_name] = APIKeyStatus.ERROR
            logger.error(f"❌ {client_name} 一般エラー: {error_message}")
    
    def _switch_to_next_client(self):
        """次のクライアントに切り替え"""
        self.current_client_index = (self.current_client_index + 1) % len(self.api_clients)
        next_client_name = f"client_{self.current_client_index + 1}"
        logger.info(f"🔄 {next_client_name} に切り替え")
    
    async def generate_embedding(self, text: str, max_retries: int = 3) -> Optional[List[float]]:
        """単一テキストのエンベディング生成（全APIキーでリトライ）"""
        if not text or not text.strip():
            logger.warning("⚠️ 空のテキストをスキップ")
            return None
        
        # 全クライアントを試行
        for attempt in range(len(self.api_clients)):
            client_info = self._get_active_client()
            if not client_info:
                logger.error("❌ 利用可能なAPIクライアントがありません")
                break
            
            client_name, api_key = client_info
            
            for retry in range(max_retries):
                try:
                    logger.debug(f"🧠 {client_name} でembedding生成中 (試行 {retry + 1}/{max_retries})")
                    
                    # APIキーを設定してリクエスト
                    genai.configure(api_key=api_key)
                    response = await asyncio.to_thread(
                        genai.embed_content,
                        model=self.embedding_model,
                        content=text.strip()
                    )
                    
                    # レスポンスからembeddingを取得
                    embedding_vector = None
                    if isinstance(response, dict) and 'embedding' in response:
                        embedding_vector = response['embedding']
                    elif hasattr(response, 'embedding') and response.embedding:
                        embedding_vector = response.embedding
                    else:
                        logger.error(f"🔍 予期しないレスポンス形式: {type(response)}")
                        continue
                    
                    if embedding_vector and len(embedding_vector) > 0:
                        # 取得したベクトル次元が想定と異なる場合は調整（切り捨て or 0 埋め）
                        if len(embedding_vector) != self.expected_dimensions:
                            logger.warning(
                                f"🔧 取得した次元数 {len(embedding_vector)} が想定 {self.expected_dimensions} と異なります。サイズを調整します"
                            )
                            if len(embedding_vector) > self.expected_dimensions:
                                embedding_vector = embedding_vector[: self.expected_dimensions]
                            else:
                                # 足りない場合はゼロパディング
                                embedding_vector.extend([0.0] * (self.expected_dimensions - len(embedding_vector)))

                        logger.debug(
                            f"✅ {client_name} embedding生成成功: {len(embedding_vector)}次元 ({self.embedding_model})"
                        )
                        return embedding_vector
                    else:
                        logger.warning(f"⚠️ 無効なembedding: {len(embedding_vector) if embedding_vector else 0}次元")
                        continue
                        
                except Exception as e:
                    self._handle_api_error(client_name, e)
                    
                    if retry < max_retries - 1:
                        wait_time = 2 ** retry  # 指数バックオフ
                        logger.info(f"⏳ {client_name} {wait_time}秒待機後リトライ...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"❌ {client_name} 最大リトライ回数に達しました")
                        break
            
            # 次のクライアントに切り替え
            self._switch_to_next_client()
        
        logger.error("❌ 全APIクライアントでembedding生成に失敗しました")
        return None
    
    async def generate_embeddings_batch(self, texts: List[str], max_retries: int = 3) -> List[Optional[List[float]]]:
        """複数テキストのエンベディング生成（個別処理）"""
        results = []
        
        for i, text in enumerate(texts):
            logger.debug(f"📦 バッチ処理 {i+1}/{len(texts)}")
            embedding = await self.generate_embedding(text, max_retries)
            results.append(embedding)
            
            # API制限対策：少し待機
            if i < len(texts) - 1:
                await asyncio.sleep(0.1)
        
        return results
    
    def get_api_status(self) -> Dict[str, Any]:
        """APIクライアントの状態を取得"""
        status_info = {}
        current_time = time.time()
        
        for client_name in self.api_clients.keys():
            status = self.api_status.get(client_name, APIKeyStatus.ERROR)
            last_error = self.api_last_error.get(client_name)
            reset_time = self.api_rate_limit_reset.get(client_name, 0)
            
            status_info[client_name] = {
                "status": status.value,
                "last_error": last_error,
                "rate_limit_reset_in": max(0, reset_time - current_time) if reset_time > current_time else 0,
                "is_current": client_name == f"client_{self.current_client_index + 1}"
            }
        
        return {
            "total_clients": len(self.api_clients),
            "active_clients": len([s for s in self.api_status.values() if s == APIKeyStatus.ACTIVE]),
            "current_client": f"client_{self.current_client_index + 1}",
            "clients": status_info
        }

# グローバルインスタンス
_multi_api_client = None

def get_multi_api_embedding_client() -> Optional[MultiAPIEmbeddingClient]:
    """複数API対応エンベディングクライアントを取得（シングルトンパターン）"""
    global _multi_api_client
    
    if _multi_api_client is None:
        try:
            _multi_api_client = MultiAPIEmbeddingClient()
            logger.info("✅ 複数API対応エンベディングクライアント初期化完了")
        except Exception as e:
            logger.error(f"❌ 複数API対応エンベディングクライアント初期化エラー: {e}")
            return None
    
    return _multi_api_client

def multi_api_embedding_available() -> bool:
    """複数API対応エンベディングが利用可能かチェック"""
    client = get_multi_api_embedding_client()
    return client is not None and len(client.api_clients) > 0