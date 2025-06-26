"""
🚨 Quota Exhaustion Fix
Emergency fix for Google Gemini API quota exhaustion issues

This script patches the existing document processor to handle quota limits gracefully
and stops the infinite retry loop that's causing the 429 errors.
"""

import os
import sys
import logging
import asyncio
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_emergency_quota_fix():
    """Apply emergency quota management fix"""
    try:
        # Import the quota manager
        from modules.quota_manager import quota_manager
        
        # Import and patch the document processor
        from modules import document_processor
        
        # Store original method
        original_generate_embeddings = document_processor.DocumentProcessor._generate_embeddings_batch
        
        async def quota_aware_generate_embeddings(self, texts, failed_indices=None):
            """Quota-aware embedding generation with circuit breaker"""
            
            # Check quota manager status
            status = quota_manager.get_status()
            logger.info(f"🚦 Quota Status: {status['circuit_state']}, Success Rate: {status['success_rate']:.1f}%")
            
            # If circuit is open, return empty embeddings to prevent infinite retry
            if status['circuit_state'] == 'open':
                logger.warning("🚨 CIRCUIT BREAKER OPEN - Skipping embedding generation to prevent quota exhaustion")
                return [None] * len(texts)
            
            # If we have too many consecutive failures, open the circuit
            if status['consecutive_failures'] >= 10:
                logger.error("🚨 Too many consecutive failures - Opening circuit breaker")
                quota_manager.metrics.circuit_state = quota_manager.CircuitState.OPEN
                quota_manager.metrics.circuit_open_time = datetime.now()
                return [None] * len(texts)
            
            # Proceed with original method but with quota tracking
            try:
                result = await original_generate_embeddings(self, texts, failed_indices)
                
                # Record success if we got some embeddings
                if result and any(emb is not None for emb in result):
                    await quota_manager._record_success()
                
                return result
                
            except Exception as e:
                error_str = str(e)
                
                # Check for quota-related errors
                if any(keyword in error_str.lower() for keyword in ['429', 'quota', 'exhausted', 'rate limit']):
                    logger.error(f"🚨 Quota error detected: {error_str}")
                    
                    # Record the failure
                    from modules.quota_manager import QuotaErrorType
                    if '429' in error_str:
                        error_type = QuotaErrorType.RATE_LIMIT
                    elif 'exhausted' in error_str:
                        error_type = QuotaErrorType.RESOURCE_EXHAUSTED
                    else:
                        error_type = QuotaErrorType.QUOTA_EXCEEDED
                    
                    await quota_manager._record_failure(e, error_type, "EMBEDDING_BATCH")
                    
                    # Return empty embeddings to prevent infinite retry
                    logger.warning("🛑 Returning empty embeddings to prevent infinite retry loop")
                    return [None] * len(texts)
                else:
                    # Non-quota error, re-raise
                    raise
        
        # Apply the patch
        document_processor.DocumentProcessor._generate_embeddings_batch = quota_aware_generate_embeddings
        logger.info("✅ Emergency quota fix applied to document processor")
        
        # Also patch the file queue manager to stop infinite retries
        try:
            from modules import file_queue_manager
            
            original_retry_embeddings = file_queue_manager.FileQueueManager._retry_embeddings_unlimited
            
            async def quota_aware_retry_embeddings(self, retry_task):
                """Quota-aware embedding retry with circuit breaker"""
                
                # Check quota status before retrying
                status = quota_manager.get_status()
                
                if status['circuit_state'] == 'open':
                    logger.warning(f"🚨 Circuit breaker OPEN - Stopping retry for task {retry_task.task_id}")
                    # Remove from active retries
                    self.active_embedding_retries.pop(retry_task.task_id, None)
                    return
                
                # Limit retry attempts when quota issues are detected
                if status['quota_errors'] > 50:
                    logger.warning(f"🚨 Too many quota errors ({status['quota_errors']}) - Stopping retry for task {retry_task.task_id}")
                    self.active_embedding_retries.pop(retry_task.task_id, None)
                    return
                
                # Call original method with limited retries
                try:
                    await original_retry_embeddings(self, retry_task)
                except Exception as e:
                    logger.error(f"❌ Retry failed for task {retry_task.task_id}: {e}")
                    self.active_embedding_retries.pop(retry_task.task_id, None)
            
            file_queue_manager.FileQueueManager._retry_embeddings_unlimited = quota_aware_retry_embeddings
            logger.info("✅ Emergency quota fix applied to file queue manager")
            
        except ImportError:
            logger.warning("⚠️ File queue manager not found - skipping patch")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to apply emergency quota fix: {e}")
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

def main():
    """Main function to apply the emergency fix"""
    logger.info("🚨 Starting emergency quota exhaustion fix...")
    
    # Stop infinite retries first
    logger.info("🛑 Stopping infinite retry loops...")
    if stop_infinite_retries():
        logger.info("✅ Infinite retries stopped")
    else:
        logger.warning("⚠️ Could not stop infinite retries")
    
    # Apply quota management fix
    logger.info("🔧 Applying quota management fix...")
    if apply_emergency_quota_fix():
        logger.info("✅ Emergency quota fix applied successfully")
        
        # Print quota manager status
        try:
            from modules.quota_manager import quota_manager
            status = quota_manager.get_status()
            logger.info(f"📊 Current Quota Status:")
            logger.info(f"   Circuit State: {status['circuit_state']}")
            logger.info(f"   Total Requests: {status['total_requests']}")
            logger.info(f"   Success Rate: {status['success_rate']:.1f}%")
            logger.info(f"   Quota Errors: {status['quota_errors']}")
            logger.info(f"   Consecutive Failures: {status['consecutive_failures']}")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not get quota status: {e}")
        
        logger.info("🎉 Emergency fix completed. The application should now handle quota limits gracefully.")
        logger.info("💡 Recommendation: Wait for quota to reset before processing new documents.")
        
    else:
        logger.error("❌ Emergency quota fix failed")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)