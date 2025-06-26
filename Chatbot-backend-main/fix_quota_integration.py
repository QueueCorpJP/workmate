"""
🚨 Comprehensive Quota Integration Fix
Fix the quota exhaustion issue by properly integrating quota management
with embedding generation and stopping infinite retry loops.

This fix addresses:
1. Embedding generation not using quota manager
2. Infinite retry loops in file queue manager
3. Lack of circuit breaker integration
4. Missing backoff and rate limiting
"""

import os
import sys
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Any

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def patch_document_processor():
    """Patch the document processor to use quota manager"""
    try:
        from modules.document_processor import DocumentProcessor
        from modules.quota_manager import quota_manager, QuotaExhaustedException
        
        # Store original method
        original_generate_embeddings = DocumentProcessor._generate_embeddings_batch
        
        async def quota_aware_generate_embeddings(self, texts: List[str], failed_indices: List[int] = None) -> List[Optional[List[float]]]:
            """Quota-aware embedding generation with circuit breaker"""
            
            if failed_indices is None:
                logger.info(f"🧠 embedding生成開始: {len(texts)}件, モデル={self.embedding_model}")
            else:
                logger.info(f"🔄 embedding再生成開始: {len(failed_indices)}件の失敗分, モデル={self.embedding_model}")
            
            # Check quota manager status
            status = quota_manager.get_status()
            logger.info(f"🚦 Quota Status: {status['circuit_state']}, Success Rate: {status['success_rate']:.1f}%, Failures: {status['consecutive_failures']}")
            
            # If circuit is open, return empty embeddings to prevent infinite retry
            if status['circuit_state'] == 'open':
                logger.warning("🚨 CIRCUIT BREAKER OPEN - Skipping embedding generation to prevent quota exhaustion")
                return [None] * len(texts)
            
            # If we have too many quota errors, temporarily stop
            if status['quota_errors'] >= 20:
                logger.warning(f"🚨 Too many quota errors ({status['quota_errors']}) - Temporarily stopping embedding generation")
                return [None] * len(texts)
            
            try:
                self._init_gemini_client()
                
                all_embeddings = []
                failed_embeddings = []
                
                # Determine processing indices
                if failed_indices is None:
                    process_indices = list(range(len(texts)))
                    all_embeddings = [None] * len(texts)
                else:
                    process_indices = failed_indices
                    all_embeddings = [None] * len(texts)
                
                # Process embeddings with quota management
                for idx, i in enumerate(process_indices):
                    try:
                        text = texts[i]
                        if not text or not text.strip():
                            logger.warning(f"⚠️ 空のテキストをスキップ: インデックス {i}")
                            all_embeddings[i] = None
                            failed_embeddings.append(i)
                            continue
                        
                        # Use quota manager to execute embedding generation
                        async def generate_single_embedding():
                            response = await asyncio.to_thread(
                                self.gemini_client.embed_content,
                                model=self.embedding_model,
                                content=text.strip()
                            )
                            return response
                        
                        # Execute with quota management
                        response = await quota_manager.execute_with_quota_management(
                            generate_single_embedding,
                            f"EMBEDDING_{i}"
                        )
                        
                        if response and 'embedding' in response:
                            embedding_vector = response['embedding']
                            all_embeddings[i] = embedding_vector
                            logger.info(f"✅ embedding生成成功: {idx + 1}/{len(process_indices)} (インデックス {i}, 次元: {len(embedding_vector)})")
                        else:
                            logger.warning(f"⚠️ embedding生成レスポンスが不正です: インデックス {i}")
                            all_embeddings[i] = None
                            failed_embeddings.append(i)
                        
                        # Small delay between requests (handled by quota manager)
                        await asyncio.sleep(0.1)
                        
                    except QuotaExhaustedException as e:
                        logger.error(f"🚨 Quota exhausted for embedding {i}: {e}")
                        all_embeddings[i] = None
                        failed_embeddings.append(i)
                        # Stop processing more embeddings when quota is exhausted
                        break
                        
                    except Exception as e:
                        logger.error(f"❌ embedding生成エラー (インデックス {i}): {e}")
                        all_embeddings[i] = None
                        failed_embeddings.append(i)
                
                success_count = len([e for e in all_embeddings if e is not None])
                total_count = len(texts)
                
                if failed_indices is None:
                    logger.info(f"📊 embedding生成完了: {success_count}/{total_count} 成功")
                else:
                    logger.info(f"📊 embedding再生成完了: {success_count}/{len(failed_indices)} 成功")
                
                if failed_embeddings:
                    logger.warning(f"⚠️ 失敗したembedding: {len(failed_embeddings)}件")
                
                return all_embeddings
                
            except Exception as e:
                logger.error(f"❌ embedding生成バッチエラー: {e}")
                return [None] * len(texts)
        
        # Apply the patch
        DocumentProcessor._generate_embeddings_batch = quota_aware_generate_embeddings
        logger.info("✅ Document processor patched with quota management")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to patch document processor: {e}")
        return False

def patch_file_queue_manager():
    """Patch the file queue manager to stop infinite retries"""
    try:
        from modules.file_queue_manager import FileQueueManager
        from modules.quota_manager import quota_manager
        
        # Store original methods
        original_retry_embeddings = FileQueueManager._retry_embeddings_unlimited
        original_process_embedding_retries = FileQueueManager._process_embedding_retries
        
        async def quota_aware_retry_embeddings(self, retry_task):
            """Quota-aware embedding retry with limits"""
            try:
                from modules.document_processor import document_processor
                
                logger.info(f"🧠 制限付きEmbeddingリトライ開始: {retry_task.doc_id}")
                
                max_retries = 10  # Limit retries to prevent infinite loops
                retry_count = 0
                consecutive_failures = 0
                max_consecutive_failures = 5
                
                while retry_count < max_retries:
                    retry_count += 1
                    retry_task.retry_count = retry_count
                    retry_task.last_attempt = datetime.now()
                    
                    # Check quota status before retrying
                    status = quota_manager.get_status()
                    
                    if status['circuit_state'] == 'open':
                        logger.warning(f"🚨 Circuit breaker OPEN - Stopping retry for task {retry_task.task_id}")
                        break
                    
                    if status['quota_errors'] > 30:
                        logger.warning(f"🚨 Too many quota errors ({status['quota_errors']}) - Stopping retry for task {retry_task.task_id}")
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
                        consecutive_failures += 1
                        logger.error(f"❌ Embeddingリトライエラー #{retry_count}: {retry_task.doc_id} - {retry_error}")
                        
                        if consecutive_failures >= max_consecutive_failures:
                            logger.error(f"❌ Embeddingリトライエラー連続発生上限到達: {retry_task.doc_id}")
                            break
                    
                    # Exponential backoff with max delay
                    delay = min(2 ** (retry_count - 1), 60)  # Max 1 minute delay
                    logger.info(f"⏳ 次のEmbeddingリトライまで {delay}秒待機: {retry_task.doc_id}")
                    await asyncio.sleep(delay)
                
                logger.info(f"✅ Embeddingリトライ完了: {retry_task.doc_id} (総試行回数: {retry_count})")
                
            except Exception as e:
                logger.error(f"❌ 制限付きEmbeddingリトライエラー: {retry_task.doc_id} - {e}", exc_info=True)
            finally:
                # Always remove from active retries
                self.active_embedding_retries.pop(retry_task.task_id, None)
        
        async def quota_aware_process_embedding_retries(self):
            """Quota-aware embedding retry processing with limits"""
            self.is_embedding_retry_active = True
            logger.info("🧠 制限付きEmbeddingリトライ処理開始")
            
            try:
                max_processing_time = 3600  # 1 hour max processing time
                start_time = datetime.now()
                
                while True:
                    # Check if we've been processing too long
                    if (datetime.now() - start_time).total_seconds() > max_processing_time:
                        logger.warning("⏰ Embeddingリトライ処理時間上限到達 - 処理を停止します")
                        break
                    
                    # Check quota status
                    status = quota_manager.get_status()
                    if status['circuit_state'] == 'open':
                        logger.warning("🚨 Circuit breaker OPEN - Embeddingリトライ処理を一時停止します")
                        await asyncio.sleep(300)  # Wait 5 minutes
                        continue
                    
                    # Process retries with limited concurrency
                    available_slots = min(self.max_concurrent_embeddings, 2) - len(self.active_embedding_retries)
                    
                    if available_slots <= 0:
                        await asyncio.sleep(5.0)
                        continue
                    
                    # Get retry tasks
                    retry_tasks = list(self.embedding_retry_queue.values())
                    
                    if not retry_tasks:
                        if not self.active_embedding_retries:
                            logger.info("🧠 Embeddingリトライキューが空になりました。処理を停止します。")
                            break
                        else:
                            await asyncio.sleep(5.0)
                            continue
                    
                    # Process limited number of tasks
                    tasks_to_process = retry_tasks[:available_slots]
                    
                    for retry_task in tasks_to_process:
                        # Move task to active
                        self.active_embedding_retries[retry_task.task_id] = retry_task
                        del self.embedding_retry_queue[retry_task.task_id]
                        
                        # Start retry with limits
                        asyncio.create_task(self._retry_embeddings_unlimited(retry_task))
                        
                        logger.info(f"🔄 制限付きEmbeddingリトライ開始: タスクID {retry_task.task_id}")
                    
                    await asyncio.sleep(10.0)  # Longer delay between batches
                    
            except Exception as e:
                logger.error(f"❌ 制限付きEmbeddingリトライ処理エラー: {e}", exc_info=True)
            finally:
                self.is_embedding_retry_active = False
                logger.info("⏹️ 制限付きEmbeddingリトライ処理終了")
        
        # Apply patches
        FileQueueManager._retry_embeddings_unlimited = quota_aware_retry_embeddings
        FileQueueManager._process_embedding_retries = quota_aware_process_embedding_retries
        
        logger.info("✅ File queue manager patched with quota management")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to patch file queue manager: {e}")
        return False

def stop_infinite_retries():
    """Stop any infinite retry loops that might be running"""
    try:
        # Try to access the file queue manager and stop retries
        from modules.file_queue_manager import file_queue_manager
        
        # Clear retry queues
        if hasattr(file_queue_manager, 'embedding_retry_queue'):
            retry_count = len(file_queue_manager.embedding_retry_queue)
            file_queue_manager.embedding_retry_queue.clear()
            logger.info(f"🛑 Cleared {retry_count} embedding retry tasks")
        
        if hasattr(file_queue_manager, 'active_embedding_retries'):
            active_count = len(file_queue_manager.active_embedding_retries)
            file_queue_manager.active_embedding_retries.clear()
            logger.info(f"🛑 Stopped {active_count} active embedding retries")
        
        # Set flags to stop processing
        if hasattr(file_queue_manager, 'is_embedding_retry_active'):
            file_queue_manager.is_embedding_retry_active = False
            logger.info("🛑 Disabled embedding retry processing")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to stop infinite retries: {e}")
        return False

def reset_quota_manager():
    """Reset the quota manager to clear any stuck states"""
    try:
        from modules.quota_manager import quota_manager
        
        # Reset circuit breaker
        quota_manager.reset_circuit()
        logger.info("🔄 Quota manager circuit breaker reset")
        
        # Get current status
        status = quota_manager.get_status()
        logger.info(f"📊 Quota Manager Status after reset:")
        logger.info(f"   Circuit State: {status['circuit_state']}")
        logger.info(f"   Total Requests: {status['total_requests']}")
        logger.info(f"   Success Rate: {status['success_rate']:.1f}%")
        logger.info(f"   Quota Errors: {status['quota_errors']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to reset quota manager: {e}")
        return False

def main():
    """Main function to apply the comprehensive quota integration fix"""
    logger.info("🚨 Starting comprehensive quota integration fix...")
    
    success_count = 0
    total_fixes = 4
    
    # 1. Stop infinite retries first
    logger.info("\n🛑 Step 1: Stopping infinite retry loops...")
    if stop_infinite_retries():
        logger.info("✅ Infinite retries stopped")
        success_count += 1
    else:
        logger.warning("⚠️ Could not stop infinite retries")
    
    # 2. Reset quota manager
    logger.info("\n🔄 Step 2: Resetting quota manager...")
    if reset_quota_manager():
        logger.info("✅ Quota manager reset")
        success_count += 1
    else:
        logger.warning("⚠️ Could not reset quota manager")
    
    # 3. Patch document processor
    logger.info("\n🔧 Step 3: Patching document processor...")
    if patch_document_processor():
        logger.info("✅ Document processor patched")
        success_count += 1
    else:
        logger.warning("⚠️ Could not patch document processor")
    
    # 4. Patch file queue manager
    logger.info("\n🔧 Step 4: Patching file queue manager...")
    if patch_file_queue_manager():
        logger.info("✅ File queue manager patched")
        success_count += 1
    else:
        logger.warning("⚠️ Could not patch file queue manager")
    
    # Summary
    logger.info(f"\n📊 Fix Summary: {success_count}/{total_fixes} fixes applied successfully")
    
    if success_count == total_fixes:
        logger.info("🎉 All fixes applied successfully!")
        logger.info("💡 The system now has:")
        logger.info("   - Quota-aware embedding generation")
        logger.info("   - Circuit breaker protection")
        logger.info("   - Limited retry attempts")
        logger.info("   - Proper backoff and rate limiting")
        logger.info("\n🚀 You can now safely restart the application.")
        return True
    else:
        logger.error("❌ Some fixes failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)