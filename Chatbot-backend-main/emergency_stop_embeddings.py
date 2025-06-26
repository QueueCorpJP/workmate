"""
🚨 Emergency Stop Embedding Generation
Immediately stop all embedding generation and apply aggressive rate limiting
"""

import os
import sys
import logging
import asyncio
import time
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def emergency_stop_all_processing():
    """Emergency stop all embedding processing"""
    try:
        logger.info("🚨 EMERGENCY STOP: Stopping all embedding processing")
        
        # Stop file queue manager
        try:
            from modules.file_queue_manager import file_queue_manager
            
            # Clear all queues
            if hasattr(file_queue_manager, 'file_queue'):
                queue_count = len(file_queue_manager.file_queue)
                file_queue_manager.file_queue.clear()
                logger.info(f"🛑 Cleared file queue: {queue_count} files")
            
            if hasattr(file_queue_manager, 'processing_files'):
                processing_count = len(file_queue_manager.processing_files)
                file_queue_manager.processing_files.clear()
                logger.info(f"🛑 Cleared processing files: {processing_count} files")
            
            if hasattr(file_queue_manager, 'embedding_retry_queue'):
                retry_count = len(file_queue_manager.embedding_retry_queue)
                file_queue_manager.embedding_retry_queue.clear()
                logger.info(f"🛑 Cleared embedding retry queue: {retry_count} tasks")
            
            if hasattr(file_queue_manager, 'active_embedding_retries'):
                active_count = len(file_queue_manager.active_embedding_retries)
                file_queue_manager.active_embedding_retries.clear()
                logger.info(f"🛑 Cleared active embedding retries: {active_count} tasks")
            
            # Set stop flags
            file_queue_manager.is_processing = False
            file_queue_manager.is_embedding_retry_active = False
            
            logger.info("✅ File queue manager stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping file queue manager: {e}")
        
        # Force circuit breaker open
        try:
            from modules.quota_manager import quota_manager
            
            # Force circuit breaker open
            quota_manager.metrics.circuit_state = quota_manager.CircuitState.OPEN
            quota_manager.metrics.circuit_open_time = datetime.now()
            quota_manager.metrics.consecutive_failures = 100  # Force high failure count
            
            logger.info("🚨 Circuit breaker FORCED OPEN")
            
        except Exception as e:
            logger.error(f"❌ Error forcing circuit breaker: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Emergency stop failed: {e}")
        return False

def patch_embedding_generation_with_aggressive_limits():
    """Patch embedding generation with aggressive rate limiting"""
    try:
        from modules.document_processor import DocumentProcessor
        
        # Store original method
        original_generate_embeddings = DocumentProcessor._generate_embeddings_batch
        
        async def emergency_limited_generate_embeddings(self, texts, failed_indices=None):
            """Emergency limited embedding generation - VERY aggressive limits"""
            
            logger.warning("🚨 EMERGENCY MODE: Embedding generation with aggressive limits")
            
            # Check circuit breaker first
            try:
                from modules.quota_manager import quota_manager
                status = quota_manager.get_status()
                
                if status['circuit_state'] == 'open':
                    logger.error("🚨 Circuit breaker OPEN - Blocking all embedding generation")
                    return [None] * len(texts)
                
                # Very aggressive quota error limit
                if status['quota_errors'] >= 5:
                    logger.error(f"🚨 Quota errors too high ({status['quota_errors']}) - Blocking embedding generation")
                    # Force circuit breaker open
                    quota_manager.metrics.circuit_state = quota_manager.CircuitState.OPEN
                    quota_manager.metrics.circuit_open_time = datetime.now()
                    return [None] * len(texts)
                    
            except Exception as e:
                logger.error(f"❌ Error checking quota status: {e}")
                return [None] * len(texts)
            
            # Limit batch size to 1
            if len(texts) > 1:
                logger.warning(f"🚨 EMERGENCY: Limiting batch size from {len(texts)} to 1")
                texts = texts[:1]
                if failed_indices:
                    failed_indices = failed_indices[:1]
            
            # Very long delay between requests
            logger.info("⏳ EMERGENCY: Applying 10-second delay before embedding generation")
            await asyncio.sleep(10.0)
            
            try:
                # Call original method with limited input
                result = await original_generate_embeddings(self, texts, failed_indices)
                
                # Add delay after successful generation
                logger.info("⏳ EMERGENCY: Applying 5-second delay after embedding generation")
                await asyncio.sleep(5.0)
                
                return result
                
            except Exception as e:
                error_str = str(e)
                
                # If it's a 429 error, force circuit breaker open
                if "429" in error_str or "exhausted" in error_str.lower():
                    logger.error("🚨 429 ERROR DETECTED - Forcing circuit breaker OPEN")
                    try:
                        from modules.quota_manager import quota_manager
                        quota_manager.metrics.circuit_state = quota_manager.CircuitState.OPEN
                        quota_manager.metrics.circuit_open_time = datetime.now()
                        quota_manager.metrics.consecutive_failures = 100
                    except:
                        pass
                
                logger.error(f"❌ Emergency embedding generation failed: {e}")
                return [None] * len(texts)
        
        # Apply emergency patch
        DocumentProcessor._generate_embeddings_batch = emergency_limited_generate_embeddings
        
        logger.info("✅ Emergency embedding generation patch applied")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to apply emergency embedding patch: {e}")
        return False

def set_aggressive_rate_limits():
    """Set very aggressive rate limits"""
    try:
        # Patch quota manager with aggressive settings
        from modules.quota_manager import quota_manager
        
        # Set very conservative limits
        quota_manager.failure_threshold = 2  # Open circuit after just 2 failures
        quota_manager.recovery_timeout = 600  # 10 minutes recovery time
        quota_manager.base_delay = 10.0  # 10 second base delay
        quota_manager.backoff_multiplier = 3.0  # Aggressive backoff
        
        logger.info("✅ Aggressive rate limits set")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to set aggressive rate limits: {e}")
        return False

def main():
    """Main emergency stop function"""
    logger.info("🚨 EMERGENCY STOP: Starting immediate embedding halt")
    
    success_count = 0
    total_steps = 3
    
    # 1. Emergency stop all processing
    logger.info("\n🛑 Step 1: Emergency stop all processing...")
    if emergency_stop_all_processing():
        logger.info("✅ All processing stopped")
        success_count += 1
    else:
        logger.error("❌ Failed to stop all processing")
    
    # 2. Apply emergency embedding patch
    logger.info("\n🚨 Step 2: Applying emergency embedding patch...")
    if patch_embedding_generation_with_aggressive_limits():
        logger.info("✅ Emergency embedding patch applied")
        success_count += 1
    else:
        logger.error("❌ Failed to apply emergency patch")
    
    # 3. Set aggressive rate limits
    logger.info("\n⚡ Step 3: Setting aggressive rate limits...")
    if set_aggressive_rate_limits():
        logger.info("✅ Aggressive rate limits set")
        success_count += 1
    else:
        logger.error("❌ Failed to set aggressive rate limits")
    
    # Summary
    logger.info(f"\n📊 Emergency Stop Summary: {success_count}/{total_steps} steps completed")
    
    if success_count >= 2:
        logger.info("🎉 Emergency stop successful!")
        logger.info("💡 System is now in emergency mode:")
        logger.info("   🚨 Circuit breaker FORCED OPEN")
        logger.info("   🛑 All queues cleared")
        logger.info("   ⏳ 10-second delays between embedding requests")
        logger.info("   🔒 Batch size limited to 1")
        logger.info("   ⚡ Aggressive rate limits active")
        logger.info("\n🔄 Wait 10 minutes before attempting any embedding generation")
        logger.info("🔍 Monitor logs for '🚨 Circuit breaker OPEN' messages")
        return True
    else:
        logger.error("❌ Emergency stop failed. Manual intervention required.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)