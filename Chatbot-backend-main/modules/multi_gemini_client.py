"""
🔄 複数Gemini APIキー対応チャット生成モジュール
レート制限に対応してAPIキーを自動切り替え
"""

import os
import logging
import time
import requests
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class APIKeyStatus(Enum):
    """APIキーの状態"""
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"
    ERROR = "error"

class MultiGeminiClient:
    """複数Gemini APIキー対応チャットクライアント"""
    
    def __init__(self):
        # APIキーの設定（既存のGOOGLE_API_KEY_*を活用）
        self.api_keys = [
            os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY_1"),
            os.getenv("GEMINI_API_KEY_2") or os.getenv("GOOGLE_API_KEY_2"),
            os.getenv("GEMINI_API_KEY_3") or os.getenv("GOOGLE_API_KEY_4"),
            os.getenv("GEMINI_API_KEY_4") or os.getenv("GOOGLE_API_KEY_5"),
            os.getenv("GEMINI_API_KEY_5") or os.getenv("GOOGLE_API_KEY_6"),
            # 追加のAPIキー（既存の設定を活用）
            os.getenv("GOOGLE_API_KEY_7"),
            os.getenv("GOOGLE_API_KEY_8"),
            os.getenv("GOOGLE_API_KEY_9"),
            os.getenv("GOOGLE_API_KEY_11"),
            os.getenv("GOOGLE_API_KEY_12")
        ]
        
        # 有効なAPIキーのみ保持
        self.api_keys = [key for key in self.api_keys if key]
        
        if not self.api_keys:
            raise ValueError("少なくとも1つのGemini APIキーが必要です (GEMINI_API_KEY, GEMINI_API_KEY_2～5)")
        
        # 各APIキーの状態管理
        self.api_status = {}
        self.api_last_error = {}
        self.api_rate_limit_reset = {}
        self.api_retry_count = {}
        
        # APIキーごとの状態を初期化
        for i, api_key in enumerate(self.api_keys):
            client_name = f"gemini_client_{i+1}"
            self.api_status[client_name] = APIKeyStatus.ACTIVE
            self.api_last_error[client_name] = None
            self.api_rate_limit_reset[client_name] = 0
            self.api_retry_count[client_name] = 0
            logger.info(f"✅ Gemini APIクライアント {client_name} 初期化完了")
        
        # 現在使用中のクライアントインデックス
        self.current_client_index = 0
        
        # API設定
        self.api_base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.chat_model = "gemini-2.5-flash"
        self.max_retries = 3
        self.retry_delay_base = 2  # 基本待機時間（秒）
        
        logger.info(f"🧠 複数Gemini APIキー対応クライアント初期化完了")
        logger.info(f"📊 使用可能APIキー: {len(self.api_keys)}個")
        logger.info(f"🎯 モデル: {self.chat_model}")
    
    def _get_active_client(self) -> Optional[Tuple[str, str]]:
        """アクティブなクライアントを取得"""
        current_time = time.time()
        
        # 現在のクライアントから開始して、利用可能なクライアントを探す
        for attempt in range(len(self.api_keys)):
            client_index = (self.current_client_index + attempt) % len(self.api_keys)
            client_name = f"gemini_client_{client_index + 1}"
            api_key = self.api_keys[client_index]
            
            status = self.api_status.get(client_name, APIKeyStatus.ERROR)
            
            # レート制限のリセット時間をチェック
            if status == APIKeyStatus.RATE_LIMITED:
                reset_time = self.api_rate_limit_reset.get(client_name, 0)
                if current_time > reset_time:
                    self.api_status[client_name] = APIKeyStatus.ACTIVE
                    self.api_retry_count[client_name] = 0
                    status = APIKeyStatus.ACTIVE
                    logger.info(f"🔄 {client_name} レート制限リセット")
            
            if status == APIKeyStatus.ACTIVE:
                # 現在のクライアントインデックスを更新
                self.current_client_index = client_index
                return client_name, api_key
        
        logger.error("❌ 利用可能なGemini APIキーがありません")
        return None
    
    def _is_rate_limit_error(self, error_message: str, status_code: int = None) -> bool:
        """レート制限エラーかどうかを判定"""
        if status_code == 429:
            return True
        
        rate_limit_indicators = [
            "429",
            "rate limit",
            "quota exceeded",
            "too many requests",
            "rate_limit_exceeded",
            "quota_limit_exceeded"
        ]
        
        if not error_message:
            return False
        
        error_lower = error_message.lower()
        return any(indicator in error_lower for indicator in rate_limit_indicators)
    
    def _handle_api_error(self, client_name: str, error_message: str, status_code: int = None):
        """APIエラーの処理"""
        current_time = time.time()
        
        if self._is_rate_limit_error(error_message, status_code):
            self.api_status[client_name] = APIKeyStatus.RATE_LIMITED
            # レート制限の場合、60秒後にリセット
            self.api_rate_limit_reset[client_name] = current_time + 60
            logger.warning(f"⚠️ {client_name} レート制限エラー: {error_message}")
        else:
            self.api_status[client_name] = APIKeyStatus.ERROR
            self.api_last_error[client_name] = error_message
            logger.error(f"❌ {client_name} APIエラー: {error_message}")
    
    def _switch_to_next_client(self):
        """次のクライアントに切り替え"""
        self.current_client_index = (self.current_client_index + 1) % len(self.api_keys)
        next_client_name = f"gemini_client_{self.current_client_index + 1}"
        logger.info(f"🔄 APIキー切り替え: {next_client_name}")
    
    async def generate_content(self, prompt: str, generation_config: Dict = None) -> Dict[str, Any]:
        """
        Gemini APIでコンテンツ生成（複数APIキー対応）
        
        Args:
            prompt: 生成プロンプト
            generation_config: 生成設定
            
        Returns:
            Dict: API応答データ
        """
        if generation_config is None:
            generation_config = {
                "temperature": 0.1,
                "maxOutputTokens": 1048576,
                "topP": 0.8,
                "topK": 40
            }
        
        request_data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": generation_config
        }
        
        last_error = None
        
        # 全てのAPIキーを試行
        for attempt in range(len(self.api_keys)):
            client_info = self._get_active_client()
            if not client_info:
                break
            
            client_name, api_key = client_info
            
            # リトライ回数をチェック
            retry_count = self.api_retry_count.get(client_name, 0)
            if retry_count >= self.max_retries:
                logger.warning(f"⚠️ {client_name} 最大リトライ回数に達したため次のキーに切り替え")
                self._switch_to_next_client()
                continue
            
            try:
                api_url = f"{self.api_base_url}/models/{self.chat_model}:generateContent"
                headers = {
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key
                }
                
                logger.info(f"⏱️ API呼び出し (試行 {retry_count + 1}/{self.max_retries}): {client_name}")
                
                response = requests.post(
                    api_url, 
                    headers=headers, 
                    json=request_data, 
                    timeout=600  # 10分タイムアウト
                )
                
                # 成功した場合
                if response.status_code == 200:
                    logger.info(f"✅ {client_name} API呼び出し成功")
                    # リトライカウントをリセット
                    self.api_retry_count[client_name] = 0
                    return response.json()
                
                # レート制限エラーの場合
                elif response.status_code == 429:
                    error_msg = f"API Rate Limit (429): {response.text}"
                    logger.warning(f"⚠️ {client_name} {error_msg}")
                    
                    # リトライ回数を増加
                    self.api_retry_count[client_name] = retry_count + 1
                    
                    if retry_count < self.max_retries - 1:
                        wait_time = self.retry_delay_base ** (retry_count + 1)
                        logger.info(f"⏳ {wait_time}秒待機後にリトライ (試行 {retry_count + 1})")
                        time.sleep(wait_time)
                        continue
                    else:
                        # 最大リトライ回数に達した場合、このキーを制限状態にして次のキーに切り替え
                        self._handle_api_error(client_name, error_msg, 429)
                        self._switch_to_next_client()
                        continue
                
                # その他のエラー
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"❌ {client_name} {error_msg}")
                    self._handle_api_error(client_name, error_msg, response.status_code)
                    self._switch_to_next_client()
                    last_error = error_msg
                    continue
                    
            except requests.exceptions.Timeout as e:
                error_msg = f"API タイムアウトエラー: {e}"
                logger.error(f"❌ {client_name} {error_msg}")
                self._handle_api_error(client_name, error_msg)
                self._switch_to_next_client()
                last_error = error_msg
                continue
                
            except requests.exceptions.RequestException as e:
                error_msg = f"API リクエストエラー: {e}"
                logger.error(f"❌ {client_name} {error_msg}")
                self._handle_api_error(client_name, error_msg)
                self._switch_to_next_client()
                last_error = error_msg
                continue
                
            except Exception as e:
                error_msg = f"予期しないエラー: {e}"
                logger.error(f"❌ {client_name} {error_msg}")
                self._handle_api_error(client_name, error_msg)
                self._switch_to_next_client()
                last_error = error_msg
                continue
        
        # 全てのAPIキーで失敗した場合
        logger.error("❌ 最大リトライ回数に達しました")
        raise Exception(f"LLM回答生成失敗 - {last_error or 'API制限のため、しばらく待ってから再度お試しください'}")
    
    def get_status_info(self) -> Dict[str, Any]:
        """APIキーの状態情報を取得"""
        current_time = time.time()
        status_info = {}
        
        for i, api_key in enumerate(self.api_keys):
            client_name = f"gemini_client_{i+1}"
            status = self.api_status.get(client_name, APIKeyStatus.ERROR)
            last_error = self.api_last_error.get(client_name)
            reset_time = self.api_rate_limit_reset.get(client_name, 0)
            retry_count = self.api_retry_count.get(client_name, 0)
            
            status_info[client_name] = {
                "status": status.value,
                "last_error": last_error,
                "rate_limit_reset_in": max(0, reset_time - current_time) if reset_time > current_time else 0,
                "retry_count": retry_count,
                "is_current": i == self.current_client_index,
                "api_key_suffix": api_key[-8:] if api_key else "None"  # セキュリティのため末尾8文字のみ
            }
        
        return status_info

# グローバルインスタンス
_multi_gemini_client = None

def get_multi_gemini_client() -> MultiGeminiClient:
    """MultiGeminiClientのシングルトンインスタンスを取得"""
    global _multi_gemini_client
    if _multi_gemini_client is None:
        _multi_gemini_client = MultiGeminiClient()
    return _multi_gemini_client

def multi_gemini_available() -> bool:
    """Multi Gemini APIが利用可能かチェック"""
    try:
        client = get_multi_gemini_client()
        return len(client.api_keys) > 0
    except Exception as e:
        logger.error(f"Multi Gemini API利用可能性チェック失敗: {e}")
        return False