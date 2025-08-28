"""
🚀 Gemini API キュー管理システム
複数質問の同時処理とレート制限対応
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

class RequestStatus(Enum):
    """リクエストの状態"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class QueuedRequest:
    """キューに入っているリクエスト"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str = ""
    generation_config: Dict[str, Any] = field(default_factory=dict)
    user_id: str = ""
    company_id: str = ""
    created_at: float = field(default_factory=time.time)
    status: RequestStatus = RequestStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_start: Optional[float] = None
    processing_end: Optional[float] = None
    assigned_client: Optional[str] = None

class GeminiQueueManager:
    """Gemini API キュー管理クラス"""
    
    def __init__(self, multi_gemini_client, max_concurrent_requests: int = 3):
        """
        初期化
        
        Args:
            multi_gemini_client: MultiGeminiClientインスタンス
            max_concurrent_requests: 最大同時処理数
        """
        self.multi_client = multi_gemini_client
        self.max_concurrent_requests = max_concurrent_requests
        
        # キューとプール管理
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.processing_requests: Dict[str, QueuedRequest] = {}
        self.completed_requests: Dict[str, QueuedRequest] = {}
        
        # 統計情報
        self.stats = {
            "total_requests": 0,
            "completed_requests": 0,
            "failed_requests": 0,
            "current_queue_size": 0,
            "avg_processing_time": 0.0,
            "last_reset": time.time()
        }
        
        # 制御用フラグ
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        
        # スレッドセーフ用ロック
        self._lock = asyncio.Lock()
        
        logger.info(f"✅ Gemini Queue Manager初期化完了 (最大同時処理数: {max_concurrent_requests})")
    
    async def start(self):
        """キュー処理を開始"""
        if self.is_running:
            logger.warning("⚠️ Queue Manager は既に動作中です")
            return
        
        self.is_running = True
        
        # ワーカータスクを起動（同時処理数分）
        for i in range(self.max_concurrent_requests):
            task = asyncio.create_task(self._worker(f"worker_{i+1}"))
            self.worker_tasks.append(task)
        
        logger.info(f"🚀 Queue Manager開始 - {self.max_concurrent_requests}個のワーカーで並列処理")
    
    async def stop(self):
        """キュー処理を停止"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 全てのワーカータスクをキャンセル
        for task in self.worker_tasks:
            task.cancel()
        
        # 完了を待つ
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        
        logger.info("🛑 Queue Manager停止完了")
    
    async def submit_request(
        self, 
        prompt: str, 
        generation_config: Optional[Dict[str, Any]] = None,
        user_id: str = "",
        company_id: str = "",
        timeout: float = 300.0  # 5分タイムアウト
    ) -> str:
        """
        リクエストをキューに追加
        
        Args:
            prompt: 生成プロンプト
            generation_config: 生成設定
            user_id: ユーザーID
            company_id: 企業ID
            timeout: タイムアウト時間（秒）
            
        Returns:
            str: リクエストID
        """
        if generation_config is None:
            generation_config = {
                "temperature": 0.1,
                "maxOutputTokens": 1048576,
                "topP": 0.8,
                "topK": 40
            }
        
        request = QueuedRequest(
            prompt=prompt,
            generation_config=generation_config,
            user_id=user_id,
            company_id=company_id
        )
        
        async with self._lock:
            await self.request_queue.put(request)
            self.stats["total_requests"] += 1
            self.stats["current_queue_size"] = self.request_queue.qsize()
        
        logger.info(f"📥 リクエスト追加: {request.id[:8]} (キューサイズ: {self.stats['current_queue_size']})")
        return request.id
    
    async def get_result(self, request_id: str, timeout: float = 300.0) -> Optional[Dict[str, Any]]:
        """
        リクエスト結果を取得（非同期待機）
        
        Args:
            request_id: リクエストID
            timeout: タイムアウト時間（秒）
            
        Returns:
            Optional[Dict[str, Any]]: 生成結果またはNone
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 完了済みリクエストをチェック
            if request_id in self.completed_requests:
                request = self.completed_requests[request_id]
                if request.status == RequestStatus.COMPLETED:
                    logger.info(f"✅ 結果取得成功: {request_id[:8]}")
                    return request.result
                elif request.status == RequestStatus.FAILED:
                    logger.error(f"❌ 処理失敗: {request_id[:8]} - {request.error}")
                    return None
            
            # 処理中かキュー待ちの場合は少し待つ
            await asyncio.sleep(0.1)
        
        # タイムアウト
        logger.warning(f"⏰ 結果取得タイムアウト: {request_id[:8]}")
        return None
    
    async def _worker(self, worker_name: str):
        """ワーカープロセス（並列実行）"""
        logger.info(f"🔧 {worker_name} 開始")
        
        while self.is_running:
            try:
                # キューからリクエストを取得（タイムアウト付き）
                try:
                    request = await asyncio.wait_for(self.request_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue  # タイムアウトの場合は次のループへ
                
                # 処理開始
                request.status = RequestStatus.PROCESSING
                request.processing_start = time.time()
                
                async with self._lock:
                    self.processing_requests[request.id] = request
                    self.stats["current_queue_size"] = self.request_queue.qsize()
                
                logger.info(f"🔄 {worker_name} 処理開始: {request.id[:8]}")
                
                try:
                    # Gemini API 呼び出し
                    result = await self.multi_client.generate_content(
                        request.prompt, 
                        request.generation_config
                    )
                    
                    # 成功
                    request.result = result
                    request.status = RequestStatus.COMPLETED
                    request.processing_end = time.time()
                    
                    processing_time = request.processing_end - request.processing_start
                    logger.info(f"✅ {worker_name} 処理完了: {request.id[:8]} ({processing_time:.2f}秒)")
                    
                    # 統計更新
                    async with self._lock:
                        self.stats["completed_requests"] += 1
                        self.stats["avg_processing_time"] = (
                            (self.stats["avg_processing_time"] * (self.stats["completed_requests"] - 1) + processing_time) 
                            / self.stats["completed_requests"]
                        )
                
                except Exception as e:
                    # エラー
                    request.error = str(e)
                    request.status = RequestStatus.FAILED
                    request.processing_end = time.time()
                    
                    logger.error(f"❌ {worker_name} 処理失敗: {request.id[:8]} - {e}")
                    
                    # 統計更新
                    async with self._lock:
                        self.stats["failed_requests"] += 1
                
                # 完了済みに移動
                async with self._lock:
                    if request.id in self.processing_requests:
                        del self.processing_requests[request.id]
                    self.completed_requests[request.id] = request
                
                # キューのタスク完了をマーク
                self.request_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info(f"🛑 {worker_name} キャンセルされました")
                break
            except Exception as e:
                logger.error(f"❌ {worker_name} 予期しないエラー: {e}")
                await asyncio.sleep(1)  # エラー後は少し待つ
    
    def get_status(self) -> Dict[str, Any]:
        """現在の状態を取得"""
        return {
            "is_running": self.is_running,
            "queue_size": self.stats["current_queue_size"],
            "processing_count": len(self.processing_requests),
            "completed_count": self.stats["completed_requests"],
            "failed_count": self.stats["failed_requests"],
            "total_requests": self.stats["total_requests"],
            "avg_processing_time": self.stats["avg_processing_time"],
            "max_concurrent": self.max_concurrent_requests,
            "worker_count": len(self.worker_tasks)
        }
    
    async def clear_completed_requests(self, older_than_seconds: float = 3600):
        """完了済みリクエストをクリア（1時間以上古いもの）"""
        current_time = time.time()
        to_remove = []
        
        for request_id, request in self.completed_requests.items():
            if request.processing_end and (current_time - request.processing_end > older_than_seconds):
                to_remove.append(request_id)
        
        for request_id in to_remove:
            del self.completed_requests[request_id]
        
        if to_remove:
            logger.info(f"🧹 完了済みリクエストクリア: {len(to_remove)}件")

# グローバルキューマネージャー（シングルトン）
_queue_manager: Optional[GeminiQueueManager] = None

async def get_queue_manager(multi_gemini_client) -> GeminiQueueManager:
    """キューマネージャーのシングルトンインスタンスを取得"""
    global _queue_manager
    
    if _queue_manager is None:
        _queue_manager = GeminiQueueManager(multi_gemini_client, max_concurrent_requests=3)
        await _queue_manager.start()
    
    return _queue_manager

async def shutdown_queue_manager():
    """キューマネージャーをシャットダウン"""
    global _queue_manager
    
    if _queue_manager is not None:
        await _queue_manager.stop()
        _queue_manager = None

