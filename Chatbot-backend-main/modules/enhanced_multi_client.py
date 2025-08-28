"""
🚀 拡張版Multi Gemini Client
複数質問同時処理対応・キュー管理統合版
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from .multi_gemini_client import MultiGeminiClient
from .gemini_queue_manager import GeminiQueueManager, get_queue_manager

logger = logging.getLogger(__name__)

class EnhancedMultiGeminiClient:
    """拡張版Multi Gemini Client（キュー管理付き）"""
    
    def __init__(self, max_concurrent_requests: int = 3):
        """
        初期化
        
        Args:
            max_concurrent_requests: 最大同時処理数
        """
        self.base_client = MultiGeminiClient()
        self.queue_manager: Optional[GeminiQueueManager] = None
        self.max_concurrent_requests = max_concurrent_requests
        self.is_initialized = False
        
        logger.info(f"✅ Enhanced Multi Gemini Client初期化完了 (並列数: {max_concurrent_requests})")
    
    async def initialize(self):
        """非同期初期化"""
        if self.is_initialized:
            return
        
        self.queue_manager = await get_queue_manager(self.base_client)
        self.is_initialized = True
        logger.info("🚀 Enhanced Multi Gemini Client 非同期初期化完了")
    
    async def generate_content_async(
        self, 
        prompt: str, 
        generation_config: Optional[Dict[str, Any]] = None,
        user_id: str = "",
        company_id: str = "",
        timeout: float = 300.0
    ) -> Optional[Dict[str, Any]]:
        """
        非同期コンテンツ生成（キュー管理付き）
        
        Args:
            prompt: 生成プロンプト
            generation_config: 生成設定
            user_id: ユーザーID
            company_id: 企業ID
            timeout: タイムアウト時間（秒）
            
        Returns:
            Optional[Dict[str, Any]]: 生成結果
        """
        await self.initialize()
        
        # リクエストをキューに追加
        request_id = await self.queue_manager.submit_request(
            prompt=prompt,
            generation_config=generation_config,
            user_id=user_id,
            company_id=company_id,
            timeout=timeout
        )
        
        # 結果を待機
        result = await self.queue_manager.get_result(request_id, timeout)
        return result
    
    async def generate_multiple_content(
        self, 
        requests: List[Dict[str, Any]],
        timeout: float = 300.0
    ) -> List[Optional[Dict[str, Any]]]:
        """
        複数コンテンツの並列生成
        
        Args:
            requests: リクエストリスト
                例: [{"prompt": "質問1", "user_id": "user1"}, {"prompt": "質問2", "user_id": "user2"}]
            timeout: タイムアウト時間（秒）
            
        Returns:
            List[Optional[Dict[str, Any]]]: 生成結果リスト
        """
        await self.initialize()
        
        if not requests:
            return []
        
        logger.info(f"🚀 複数リクエスト処理開始: {len(requests)}件")
        
        # 全てのリクエストをキューに追加
        request_ids = []
        for req in requests:
            request_id = await self.queue_manager.submit_request(
                prompt=req.get("prompt", ""),
                generation_config=req.get("generation_config"),
                user_id=req.get("user_id", ""),
                company_id=req.get("company_id", ""),
                timeout=timeout
            )
            request_ids.append(request_id)
        
        # 全ての結果を並列で待機
        tasks = [
            self.queue_manager.get_result(request_id, timeout)
            for request_id in request_ids
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 例外を処理
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ リクエスト {i+1} でエラー: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        completed_count = sum(1 for r in processed_results if r is not None)
        logger.info(f"✅ 複数リクエスト処理完了: {completed_count}/{len(requests)}件成功")
        
        return processed_results
    
    def generate_content_sync(
        self, 
        prompt: str, 
        generation_config: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        同期コンテンツ生成（従来互換）
        
        Args:
            prompt: 生成プロンプト
            generation_config: 生成設定
            
        Returns:
            Optional[Dict[str, Any]]: 生成結果
        """
        # 新しいイベントループで実行
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.generate_content_async(prompt, generation_config)
        )
    
    async def get_status(self) -> Dict[str, Any]:
        """現在の状態を取得"""
        await self.initialize()
        
        queue_status = self.queue_manager.get_status()
        base_status = self.base_client.get_status()
        
        return {
            "enhanced_client": {
                "max_concurrent_requests": self.max_concurrent_requests,
                "is_initialized": self.is_initialized
            },
            "queue_manager": queue_status,
            "base_client": base_status
        }
    
    async def reset_all_api_keys(self):
        """全APIキーをリセット"""
        self.base_client.reset_all_api_keys()
        logger.info("🔄 全APIキーリセット完了")

# グローバルインスタンス
_enhanced_client: Optional[EnhancedMultiGeminiClient] = None

def get_enhanced_multi_gemini_client(max_concurrent_requests: int = 3) -> EnhancedMultiGeminiClient:
    """Enhanced Multi Gemini Clientのシングルトンインスタンスを取得"""
    global _enhanced_client
    
    if _enhanced_client is None:
        _enhanced_client = EnhancedMultiGeminiClient(max_concurrent_requests)
    
    return _enhanced_client

def enhanced_multi_gemini_available() -> bool:
    """Enhanced Multi Gemini Clientが利用可能かチェック"""
    try:
        client = get_enhanced_multi_gemini_client()
        return client.base_client is not None and len(client.base_client.api_keys) > 0
    except Exception as e:
        logger.error(f"Enhanced Multi Gemini Client利用可能性チェックエラー: {e}")
        return False

