"""
🔄 複数API対応エンベディング生成モジュール
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
        
        # 環境変数から全てのGemini APIキーを取得
        self.api_keys = []
        
        # 主要なAPIキーを追加
        primary_keys = [
            os.getenv("GEMINI_API_KEY"),
            os.getenv("GOOGLE_API_KEY"),
            os.getenv("GOOGLE_API_KEY_1")
        ]
        
        # 番号付きAPIキーを追加（1-33まで）
        for i in range(1, 34):
            key = os.getenv(f"GOOGLE_API_KEY_{i}")
            if key:
                self.api_keys.append(key)
        
        # 主要キーで重複していないものを先頭に追加
        for key in primary_keys:
            if key and key not in self.api_keys:
                self.api_keys.insert(0, key)
        
        # 有効なAPIキーのみ保持
        self.api_keys = [key for key in self.api_keys if key]
        
        if not self.api_keys:
            raise ValueError("少なくとも1つのAPIキーが必要です (GOOGLE_API_KEY_1～3)")
        
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
    
    async def generate_embedding(self, text: str, max_retries: int = 3, raise_on_failure: bool = False) -> Optional[List[float]]:
        """単一テキストのエンベディング生成（全APIキーでリトライ）"""
        if not text or not text.strip():
            logger.warning("⚠️ 空のテキストをスキップ")
            if raise_on_failure:
                raise ValueError("空のテキストが提供されました")
            return None
        
        # 全クライアントを試行
        for attempt in range(len(self.api_clients)):
            client_info = self._get_active_client()
            if not client_info:
                error_msg = "利用可能なAPIクライアントがありません"
                logger.error(f"❌ {error_msg}")
                if raise_on_failure:
                    raise RuntimeError(error_msg)
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
                        wait_time = min(1.0, 2 ** (retry * 0.5))  # 短縮された指数バックオフ
                        logger.info(f"⏳ {client_name} {wait_time:.1f}秒待機後リトライ...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"❌ {client_name} 最大リトライ回数に達しました")
                        break
            
            # 次のクライアントに切り替え
            self._switch_to_next_client()
        
        error_msg = f"全APIクライアント({len(self.api_clients)}個)でembedding生成に失敗しました"
        logger.error(f"❌ {error_msg}")
        
        if raise_on_failure:
            raise RuntimeError(error_msg)
        
        return None
    
    async def generate_embeddings_batch(self, texts: List[str], max_retries: int = 3, fail_fast: bool = False) -> List[Optional[List[float]]]:
        """複数テキストのエンベディング生成（個別処理）"""
        results = []
        failed_indices = []
        
        for i, text in enumerate(texts):
            logger.debug(f"📦 バッチ処理 {i+1}/{len(texts)}")
            
            try:
                embedding = await self.generate_embedding(text, max_retries, raise_on_failure=fail_fast)
                
                if embedding is None and fail_fast:
                    error_msg = f"バッチ処理中にembedding生成に失敗しました (インデックス: {i})"
                    logger.error(f"❌ {error_msg}")
                    raise RuntimeError(error_msg)
                
                results.append(embedding)
                
                if embedding is None:
                    failed_indices.append(i)
                    logger.warning(f"⚠️ インデックス {i} のembedding生成に失敗しました")
                
            except Exception as e:
                if fail_fast:
                    logger.error(f"❌ バッチ処理中断: {e}")
                    raise
                else:
                    logger.error(f"❌ インデックス {i} でエラー: {e}")
                    results.append(None)
                    failed_indices.append(i)
            
            # API制限対策：最小限の待機
            if i < len(texts) - 1:
                await asyncio.sleep(0.01)  # 0.1→0.01秒に大幅短縮
        
        # 失敗した項目の統計を出力
        if failed_indices:
            success_count = len(texts) - len(failed_indices)
            logger.warning(f"📊 バッチ処理完了: 成功 {success_count}/{len(texts)}, 失敗 {len(failed_indices)} 件")
            logger.warning(f"🔍 失敗したインデックス: {failed_indices}")
        else:
            logger.info(f"✅ バッチ処理完了: 全 {len(texts)} 件成功")
        
        return results
    
    async def generate_embeddings_batch_safe(self, texts: List[str], max_retries: int = 3,
                                           allow_partial_failure: bool = False) -> tuple[List[Optional[List[float]]], List[int]]:
        """
        安全なバッチ処理：失敗した項目を明確に追跡し、部分的失敗を制御
        
        Returns:
            tuple: (embeddings_list, failed_indices)
        """
        results = []
        failed_indices = []
        
        logger.info(f"🚀 安全バッチ処理開始: {len(texts)} 件のテキスト処理")
        
        for i, text in enumerate(texts):
            logger.debug(f"📦 処理中 {i+1}/{len(texts)}: {text[:50]}...")
            
            try:
                embedding = await self.generate_embedding(text, max_retries, raise_on_failure=not allow_partial_failure)
                
                if embedding is None:
                    failed_indices.append(i)
                    if not allow_partial_failure:
                        error_msg = f"必須embedding生成に失敗 (インデックス: {i})"
                        logger.error(f"❌ {error_msg}")
                        raise RuntimeError(error_msg)
                    else:
                        logger.warning(f"⚠️ インデックス {i} のembedding生成に失敗（部分的失敗許可）")
                
                results.append(embedding)
                
            except Exception as e:
                failed_indices.append(i)
                if not allow_partial_failure:
                    logger.error(f"❌ バッチ処理中断 (インデックス {i}): {e}")
                    raise RuntimeError(f"バッチ処理失敗: {e}")
                else:
                    logger.error(f"❌ インデックス {i} でエラー（続行）: {e}")
                    results.append(None)
            
            # API制限対策：最小限の待機
            if i < len(texts) - 1:
                await asyncio.sleep(0.01)  # 0.1→0.01秒に大幅短縮
        
        # 結果統計
        success_count = len(texts) - len(failed_indices)
        if failed_indices:
            logger.warning(f"📊 バッチ処理完了: 成功 {success_count}/{len(texts)}, 失敗 {len(failed_indices)} 件")
            logger.warning(f"🔍 失敗インデックス: {failed_indices}")
            
            if not allow_partial_failure and failed_indices:
                raise RuntimeError(f"部分的失敗が許可されていないため処理を中断: {len(failed_indices)} 件失敗")
        else:
            logger.info(f"✅ バッチ処理完了: 全 {len(texts)} 件成功")
        
        return results, failed_indices
    
    def validate_embeddings_for_save(self, embeddings: List[Optional[List[float]]],
                                   texts: List[str], strict_mode: bool = True) -> tuple[bool, List[int]]:
        """
        保存前のembedding検証
        
        Args:
            embeddings: 生成されたembeddingリスト
            texts: 元のテキストリスト
            strict_mode: True=失敗があれば保存拒否, False=成功分のみ保存許可
            
        Returns:
            tuple: (is_valid_for_save, invalid_indices)
        """
        if len(embeddings) != len(texts):
            logger.error(f"❌ embeddingとテキストの数が不一致: {len(embeddings)} vs {len(texts)}")
            return False, list(range(len(texts)))
        
        invalid_indices = []
        
        for i, (embedding, text) in enumerate(zip(embeddings, texts)):
            if embedding is None:
                invalid_indices.append(i)
                logger.warning(f"⚠️ インデックス {i} のembeddingがNULL")
            elif len(embedding) != self.expected_dimensions:
                invalid_indices.append(i)
                logger.warning(f"⚠️ インデックス {i} のembedding次元数が不正: {len(embedding)}")
            elif not text or not text.strip():
                invalid_indices.append(i)
                logger.warning(f"⚠️ インデックス {i} のテキストが空")
        
        valid_count = len(embeddings) - len(invalid_indices)
        
        if invalid_indices:
            logger.warning(f"📊 検証結果: 有効 {valid_count}/{len(embeddings)}, 無効 {len(invalid_indices)} 件")
            
            if strict_mode:
                logger.error(f"❌ 厳密モード: 無効なembeddingがあるため保存を拒否")
                return False, invalid_indices
            else:
                logger.warning(f"⚠️ 寛容モード: 有効な {valid_count} 件のみ保存許可")
                return valid_count > 0, invalid_indices
        else:
            logger.info(f"✅ 検証完了: 全 {len(embeddings)} 件が有効")
            return True, []
    
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

# 新しい安全なAPI関数
async def generate_embeddings_safe(texts: List[str], max_retries: int = 3, 
                                 allow_partial_failure: bool = False) -> tuple[List[Optional[List[float]]], List[int]]:
    """
    安全なembedding生成（推奨）
    
    Args:
        texts: 処理するテキストリスト
        max_retries: 最大リトライ回数
        allow_partial_failure: 部分的失敗を許可するか
        
    Returns:
        tuple: (embeddings, failed_indices)
        
    Raises:
        RuntimeError: allow_partial_failure=Falseで失敗があった場合
    """
    client = get_multi_api_embedding_client()
    if not client:
        raise RuntimeError("複数API対応エンベディングクライアントが利用できません")
    
    return await client.generate_embeddings_batch_safe(texts, max_retries, allow_partial_failure)

def validate_embeddings_before_save(embeddings: List[Optional[List[float]]], 
                                  texts: List[str], strict_mode: bool = True) -> tuple[bool, List[int]]:
    """
    保存前のembedding検証（推奨）
    
    Args:
        embeddings: 検証するembeddingリスト
        texts: 対応するテキストリスト
        strict_mode: 厳密モード（失敗があれば保存拒否）
        
    Returns:
        tuple: (is_valid_for_save, invalid_indices)
    """
    client = get_multi_api_embedding_client()
    if not client:
        raise RuntimeError("複数API対応エンベディングクライアントが利用できません")
    
    return client.validate_embeddings_for_save(embeddings, texts, strict_mode)

# 後方互換性のための既存API（非推奨）
async def generate_embeddings_batch_legacy(texts: List[str], max_retries: int = 3) -> List[Optional[List[float]]]:
    """
    レガシーバッチ処理（非推奨：generate_embeddings_safeを使用してください）
    """
    client = get_multi_api_embedding_client()
    if not client:
        return [None] * len(texts)
    
    logger.warning("⚠️ レガシーAPI使用中。generate_embeddings_safeへの移行を推奨します")
    return await client.generate_embeddings_batch(texts, max_retries, fail_fast=False)