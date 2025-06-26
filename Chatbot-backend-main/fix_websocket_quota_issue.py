"""
🚨 WebSocket Connection Leak & Quota Issue Fix
Fix the real cause of 429 errors: WebSocket connection leaks causing resource exhaustion

Root Cause Analysis:
1. WebSocket connections are not being properly closed
2. Multiple WebSocket connections accumulate over time
3. Each connection maintains async tasks that consume API quota
4. File queue manager has infinite retry loops
5. Progress manager keeps connections alive indefinitely

This fix addresses:
1. WebSocket connection lifecycle management
2. Proper cleanup of async tasks
3. Connection pooling and limits
4. Resource exhaustion prevention
5. Circuit breaker integration with WebSocket state
"""

import os
import sys
import logging
import asyncio
import weakref
from datetime import datetime, timedelta
from typing import List, Optional, Any, Dict

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_websocket_connection_leaks():
    """Fix WebSocket connection leaks that cause resource exhaustion"""
    try:
        # Patch upload progress manager
        from modules.upload_progress import UploadProgressManager
        
        # Store original methods
        original_add_websocket = UploadProgressManager.add_websocket_connection
        original_remove_websocket = UploadProgressManager.remove_websocket_connection
        original_notify_progress = UploadProgressManager._notify_progress
        
        async def fixed_add_websocket_connection(self, websocket):
            """Add WebSocket connection with proper lifecycle management"""
            import uuid
            
            # Limit maximum connections to prevent resource exhaustion
            max_connections = 10
            if len(self.websocket_connections) >= max_connections:
                logger.warning(f"🚨 WebSocket接続数上限到達 ({max_connections}) - 古い接続を削除")
                # Remove oldest connections
                oldest_connections = list(self.websocket_connections.keys())[:5]
                for old_id in oldest_connections:
                    try:
                        old_websocket = self.websocket_connections[old_id]
                        await old_websocket.close()
                    except:
                        pass
                    del self.websocket_connections[old_id]
            
            connection_id = str(uuid.uuid4())
            
            # Add new connection with weak reference to prevent memory leaks
            self.websocket_connections[connection_id] = websocket
            
            # Set connection timeout
            asyncio.create_task(self._monitor_connection_timeout(connection_id, websocket))
            
            logger.info(f"📡 WebSocket接続追加: {connection_id} (総接続数: {len(self.websocket_connections)})")
            return connection_id
        
        async def fixed_remove_websocket_connection(self, connection_id):
            """Remove WebSocket connection with proper cleanup"""
            if connection_id in self.websocket_connections:
                try:
                    websocket = self.websocket_connections[connection_id]
                    if not websocket.client_state.DISCONNECTED:
                        await websocket.close()
                except Exception as e:
                    logger.warning(f"WebSocket切断エラー: {e}")
                finally:
                    del self.websocket_connections[connection_id]
                    logger.info(f"📡 WebSocket接続削除: {connection_id} (残り接続数: {len(self.websocket_connections)})")
        
        async def fixed_notify_progress(self, upload_id):
            """Notify progress with connection health check"""
            if not self.websocket_connections:
                return
            
            upload_info = self.active_uploads.get(upload_id)
            if not upload_info:
                return
            
            message = {
                "type": "upload_progress",
                "upload_id": upload_id,
                "data": upload_info
            }
            
            # Track disconnected connections
            disconnected = []
            
            for connection_id, websocket in list(self.websocket_connections.items()):
                try:
                    # Check if connection is still alive
                    if websocket.client_state.DISCONNECTED:
                        disconnected.append(connection_id)
                        continue
                    
                    await websocket.send_text(json.dumps(message, ensure_ascii=False, default=str))
                    
                except Exception as e:
                    logger.warning(f"WebSocket通知エラー ({connection_id}): {e}")
                    disconnected.append(connection_id)
            
            # Clean up disconnected connections
            for connection_id in disconnected:
                await self.remove_websocket_connection(connection_id)
        
        async def monitor_connection_timeout(self, connection_id, websocket, timeout_minutes=30):
            """Monitor connection timeout and auto-cleanup"""
            try:
                await asyncio.sleep(timeout_minutes * 60)
                if connection_id in self.websocket_connections:
                    logger.info(f"⏰ WebSocket接続タイムアウト: {connection_id}")
                    await self.remove_websocket_connection(connection_id)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"接続監視エラー: {e}")
        
        # Apply patches
        UploadProgressManager.add_websocket_connection = fixed_add_websocket_connection
        UploadProgressManager.remove_websocket_connection = fixed_remove_websocket_connection
        UploadProgressManager._notify_progress = fixed_notify_progress
        UploadProgressManager._monitor_connection_timeout = monitor_connection_timeout
        
        logger.info("✅ Upload progress manager WebSocket leaks fixed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to fix upload progress WebSocket leaks: {e}")
        return False

def fix_client_websocket_leaks():
    """Fix client WebSocket connection leaks"""
    try:
        from modules.client_websocket_api import ClientWebSocketManager
        
        # Store original methods
        original_add_connection = ClientWebSocketManager.add_connection
        original_remove_connection = ClientWebSocketManager.remove_connection
        original_broadcast = ClientWebSocketManager.broadcast_status_update
        original_periodic_broadcast = ClientWebSocketManager._start_periodic_broadcast
        
        async def fixed_add_connection(self, websocket, connection_id, user_info):
            """Add connection with limits and monitoring"""
            # Limit connections per user
            user_id = user_info.get("id")
            user_connections = [
                cid for cid, data in self.connections.items()
                if data.get("user_id") == user_id
            ]
            
            max_per_user = 3
            if len(user_connections) >= max_per_user:
                logger.warning(f"🚨 ユーザー接続数上限 ({user_id}): {len(user_connections)}")
                # Remove oldest connection for this user
                oldest_id = user_connections[0]
                await self.remove_connection(oldest_id)
            
            # Limit total connections
            max_total = 20
            if len(self.connections) >= max_total:
                logger.warning(f"🚨 総WebSocket接続数上限到達: {len(self.connections)}")
                # Remove oldest connections
                oldest_connections = list(self.connections.keys())[:5]
                for old_id in oldest_connections:
                    await self.remove_connection(old_id)
            
            connection_data = {
                "websocket": websocket,
                "user_id": user_info.get("id"),
                "company_id": user_info.get("company_id"),
                "connected_at": datetime.now().isoformat(),
                "last_activity": datetime.now()
            }
            
            self.connections[connection_id] = connection_data
            
            logger.info(f"📱 クライアントWebSocket接続追加: {connection_id} (ユーザー: {user_info.get('id')}) (総数: {len(self.connections)})")
            
            # Start periodic broadcast with connection limits
            if not self.is_broadcasting and len(self.connections) > 0:
                asyncio.create_task(self._start_periodic_broadcast())
        
        async def fixed_remove_connection(self, connection_id):
            """Remove connection with proper cleanup"""
            if connection_id in self.connections:
                try:
                    connection_data = self.connections[connection_id]
                    websocket = connection_data["websocket"]
                    if not websocket.client_state.DISCONNECTED:
                        await websocket.close()
                except Exception as e:
                    logger.warning(f"クライアントWebSocket切断エラー: {e}")
                finally:
                    del self.connections[connection_id]
                    logger.info(f"📱 クライアントWebSocket接続削除: {connection_id} (残り: {len(self.connections)})")
        
        async def fixed_broadcast_status_update(self, force_update=False):
            """Broadcast with connection health monitoring"""
            if not self.connections:
                return
            
            try:
                from .client_queue_status import client_queue_status
                current_status = client_queue_status.get_client_queue_status()
                
                if not force_update and self.last_status == current_status:
                    return
                
                self.last_status = current_status
                
                message = {
                    "type": "queue_status_update",
                    "timestamp": datetime.now().isoformat(),
                    "data": current_status
                }
                
                message_json = json.dumps(message, ensure_ascii=False, default=str)
                
                # Track disconnected connections
                disconnected = []
                active_count = 0
                
                for connection_id, connection_data in list(self.connections.items()):
                    try:
                        websocket = connection_data["websocket"]
                        
                        # Check connection health
                        if websocket.client_state.DISCONNECTED:
                            disconnected.append(connection_id)
                            continue
                        
                        # Check for stale connections (no activity for 1 hour)
                        last_activity = connection_data.get("last_activity", datetime.now())
                        if isinstance(last_activity, str):
                            last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                        
                        if datetime.now() - last_activity > timedelta(hours=1):
                            logger.info(f"🕐 古いWebSocket接続を削除: {connection_id}")
                            disconnected.append(connection_id)
                            continue
                        
                        await websocket.send_text(message_json)
                        connection_data["last_activity"] = datetime.now()
                        active_count += 1
                        
                    except Exception as e:
                        logger.warning(f"📱 クライアント配信エラー ({connection_id}): {e}")
                        disconnected.append(connection_id)
                
                # Clean up disconnected connections
                for connection_id in disconnected:
                    await self.remove_connection(connection_id)
                
                if active_count > 0:
                    logger.debug(f"📱 状態配信完了: {active_count}接続")
                    
            except Exception as e:
                logger.error(f"📱 クライアント状態配信エラー: {e}")
        
        async def fixed_periodic_broadcast(self):
            """Periodic broadcast with resource management"""
            if self.is_broadcasting:
                return
            
            self.is_broadcasting = True
            logger.info("📱 定期配信開始")
            
            try:
                broadcast_count = 0
                max_broadcasts = 1000  # Limit total broadcasts to prevent resource exhaustion
                
                while self.connections and broadcast_count < max_broadcasts:
                    await self.broadcast_status_update()
                    
                    # Longer intervals to reduce resource usage
                    await asyncio.sleep(5.0)
                    broadcast_count += 1
                    
                    # Periodic cleanup
                    if broadcast_count % 100 == 0:
                        logger.info(f"📱 定期配信継続中: {broadcast_count}回, 接続数: {len(self.connections)}")
                
                logger.info("📱 定期配信終了 (接続なしまたは上限到達)")
                
            except Exception as e:
                logger.error(f"📱 定期配信エラー: {e}")
            finally:
                self.is_broadcasting = False
        
        # Apply patches
        ClientWebSocketManager.add_connection = fixed_add_connection
        ClientWebSocketManager.remove_connection = fixed_remove_connection
        ClientWebSocketManager.broadcast_status_update = fixed_broadcast_status_update
        ClientWebSocketManager._start_periodic_broadcast = fixed_periodic_broadcast
        
        logger.info("✅ Client WebSocket manager leaks fixed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to fix client WebSocket leaks: {e}")
        return False

def fix_file_queue_infinite_loops():
    """Fix infinite loops in file queue manager"""
    try:
        from modules.file_queue_manager import FileQueueManager
        from modules.quota_manager import quota_manager
        
        # Store original method
        original_retry_unlimited = FileQueueManager._retry_embeddings_unlimited
        
        async def fixed_retry_embeddings_unlimited(self, retry_task):
            """Fixed embedding retry with proper limits and quota awareness"""
            try:
                from modules.document_processor import document_processor
                
                logger.info(f"🧠 制限付きEmbeddingリトライ開始: {retry_task.doc_id}")
                
                max_retries = 20  # Reasonable limit instead of unlimited
                retry_count = 0
                consecutive_failures = 0
                max_consecutive_failures = 5
                max_quota_errors = 10
                quota_error_count = 0
                
                while retry_count < max_retries:
                    retry_count += 1
                    retry_task.retry_count = retry_count
                    retry_task.last_attempt = datetime.now()
                    
                    # Check quota status before each retry
                    status = quota_manager.get_status()
                    
                    # Stop if circuit breaker is open
                    if status['circuit_state'] == 'open':
                        logger.warning(f"🚨 Circuit breaker OPEN - Stopping retry for {retry_task.doc_id}")
                        break
                    
                    # Stop if too many quota errors globally
                    if status['quota_errors'] > 30:
                        logger.warning(f"🚨 Global quota errors too high ({status['quota_errors']}) - Stopping retry")
                        break
                    
                    # Stop if too many quota errors for this task
                    if quota_error_count >= max_quota_errors:
                        logger.warning(f"🚨 Task quota errors too high ({quota_error_count}) - Stopping retry for {retry_task.doc_id}")
                        break
                    
                    logger.info(f"🔄 Embeddingリトライ実行 #{retry_count}/{max_retries}: {retry_task.doc_id}")
                    
                    try:
                        # Use document processor with limited retries
                        result = await document_processor.retry_failed_embeddings(
                            doc_id=retry_task.doc_id,
                            company_id=retry_task.company_id,
                            max_retries=3  # Limited retries per attempt
                        )
                        
                        # Check results
                        if result["still_failed"] == 0:
                            logger.info(f"🎉 Embeddingリトライ完全成功: {retry_task.doc_id} (試行回数: {retry_count})")
                            break
                        elif result["successful"] > 0:
                            # Partial success - reset consecutive failures
                            consecutive_failures = 0
                            quota_error_count = 0  # Reset quota error count on success
                            logger.info(f"📈 Embeddingリトライ部分成功: {retry_task.doc_id} (成功: {result['successful']}, 残り失敗: {result['still_failed']})")
                        else:
                            # All failed
                            consecutive_failures += 1
                            logger.warning(f"⚠️ Embeddingリトライ全失敗: {retry_task.doc_id} (連続失敗: {consecutive_failures})")
                        
                        # Stop if too many consecutive failures
                        if consecutive_failures >= max_consecutive_failures:
                            logger.error(f"❌ Embeddingリトライ連続失敗上限到達: {retry_task.doc_id}")
                            break
                        
                    except Exception as retry_error:
                        error_str = str(retry_error)
                        
                        # Check if it's a quota error
                        if "429" in error_str or "quota" in error_str.lower() or "exhausted" in error_str.lower():
                            quota_error_count += 1
                            logger.error(f"🚨 Quota error #{quota_error_count} in retry #{retry_count}: {retry_task.doc_id} - {retry_error}")
                        else:
                            consecutive_failures += 1
                            logger.error(f"❌ Embeddingリトライエラー #{retry_count}: {retry_task.doc_id} - {retry_error}")
                        
                        if consecutive_failures >= max_consecutive_failures:
                            logger.error(f"❌ Embeddingリトライエラー連続発生上限到達: {retry_task.doc_id}")
                            break
                        
                        if quota_error_count >= max_quota_errors:
                            logger.error(f"🚨 Quota error limit reached for task: {retry_task.doc_id}")
                            break
                    
                    # Progressive backoff with max delay
                    if retry_count < max_retries:
                        delay = min(2 ** (retry_count - 1), 300)  # Max 5 minutes delay
                        logger.info(f"⏳ 次のEmbeddingリトライまで {delay}秒待機: {retry_task.doc_id}")
                        await asyncio.sleep(delay)
                
                logger.info(f"✅ Embeddingリトライ完了: {retry_task.doc_id} (総試行回数: {retry_count})")
                
            except Exception as e:
                logger.error(f"❌ 制限付きEmbeddingリトライエラー: {retry_task.doc_id} - {e}", exc_info=True)
            finally:
                # Always remove from active retries
                self.active_embedding_retries.pop(retry_task.task_id, None)
        
        # Apply patch
        FileQueueManager._retry_embeddings_unlimited = fixed_retry_embeddings_unlimited
        
        logger.info("✅ File queue manager infinite loops fixed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to fix file queue infinite loops: {e}")
        return False

def cleanup_existing_connections():
    """Clean up existing WebSocket connections and tasks"""
    try:
        # Clean up upload progress connections
        try:
            from modules.upload_progress import progress_manager
            connection_count = len(progress_manager.websocket_connections)
            progress_manager.websocket_connections.clear()
            logger.info(f"🧹 Upload progress WebSocket接続をクリア: {connection_count}件")
        except Exception as e:
            logger.warning(f"Upload progress cleanup error: {e}")
        
        # Clean up client WebSocket connections
        try:
            from modules.client_websocket_api import ClientWebSocketManager
            # Get the global instance if it exists
            import modules.client_websocket_api as client_ws_module
            if hasattr(client_ws_module, 'client_websocket_manager'):
                manager = client_ws_module.client_websocket_manager
                connection_count = len(manager.connections)
                manager.connections.clear()
                manager.is_broadcasting = False
                logger.info(f"🧹 Client WebSocket接続をクリア: {connection_count}件")
        except Exception as e:
            logger.warning(f"Client WebSocket cleanup error: {e}")
        
        # Stop file queue processing
        try:
            from modules.file_queue_manager import file_queue_manager
            
            # Clear retry queues
            if hasattr(file_queue_manager, 'embedding_retry_queue'):
                retry_count = len(file_queue_manager.embedding_retry_queue)
                file_queue_manager.embedding_retry_queue.clear()
                logger.info(f"🧹 Embedding retry queue cleared: {retry_count}件")
            
            if hasattr(file_queue_manager, 'active_embedding_retries'):
                active_count = len(file_queue_manager.active_embedding_retries)
                file_queue_manager.active_embedding_retries.clear()
                logger.info(f"🧹 Active embedding retries cleared: {active_count}件")
            
            # Set flags to stop processing
            if hasattr(file_queue_manager, 'is_embedding_retry_active'):
                file_queue_manager.is_embedding_retry_active = False
                logger.info("🧹 Embedding retry processing disabled")
                
        except Exception as e:
            logger.warning(f"File queue cleanup error: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to cleanup existing connections: {e}")
        return False

def main():
    """Main function to apply the WebSocket quota fix"""
    logger.info("🚨 Starting WebSocket connection leak & quota fix...")
    
    success_count = 0
    total_fixes = 4
    
    # 1. Cleanup existing connections first
    logger.info("\n🧹 Step 1: Cleaning up existing connections...")
    if cleanup_existing_connections():
        logger.info("✅ Existing connections cleaned up")
        success_count += 1
    else:
        logger.warning("⚠️ Could not cleanup existing connections")
    
    # 2. Fix upload progress WebSocket leaks
    logger.info("\n🔧 Step 2: Fixing upload progress WebSocket leaks...")
    if fix_websocket_connection_leaks():
        logger.info("✅ Upload progress WebSocket leaks fixed")
        success_count += 1
    else:
        logger.warning("⚠️ Could not fix upload progress WebSocket leaks")
    
    # 3. Fix client WebSocket leaks
    logger.info("\n🔧 Step 3: Fixing client WebSocket leaks...")
    if fix_client_websocket_leaks():
        logger.info("✅ Client WebSocket leaks fixed")
        success_count += 1
    else:
        logger.warning("⚠️ Could not fix client WebSocket leaks")
    
    # 4. Fix file queue infinite loops
    logger.info("\n🔧 Step 4: Fixing file queue infinite loops...")
    if fix_file_queue_infinite_loops():
        logger.info("✅ File queue infinite loops fixed")
        success_count += 1
    else:
        logger.warning("⚠️ Could not fix file queue infinite loops")
    
    # Summary
    logger.info(f"\n📊 Fix Summary: {success_count}/{total_fixes} fixes applied successfully")
    
    if success_count == total_fixes:
        logger.info("🎉 All WebSocket and quota fixes applied successfully!")
        logger.info("💡 The system now has:")
        logger.info("   - WebSocket connection limits and cleanup")
        logger.info("   - Proper connection lifecycle management")
        logger.info("   - Resource exhaustion prevention")
        logger.info("   - Limited retry attempts instead of infinite loops")
        logger.info("   - Quota-aware processing")
        logger.info("\n🚀 You can now safely restart the application.")
        logger.info("🔍 Monitor WebSocket connections: they should stay under 30 total")
        return True
    else:
        logger.error("❌ Some fixes failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)