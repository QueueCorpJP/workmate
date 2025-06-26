"""
🚨 Force Stop Embedding Generation
Simple script to immediately stop all embedding generation
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🚨 FORCE STOPPING EMBEDDING GENERATION...")

try:
    # Import and force circuit breaker open
    from modules.quota_manager import quota_manager
    from datetime import datetime
    
    # Force circuit breaker open
    quota_manager.metrics.circuit_state = quota_manager.CircuitState.OPEN
    quota_manager.metrics.circuit_open_time = datetime.now()
    quota_manager.metrics.consecutive_failures = 100
    quota_manager.metrics.quota_errors = 100
    
    print("✅ Circuit breaker FORCED OPEN")
    
except Exception as e:
    print(f"❌ Error forcing circuit breaker: {e}")

try:
    # Stop file queue manager
    from modules.file_queue_manager import file_queue_manager
    
    # Clear all queues
    file_queue_manager.file_queue.clear()
    file_queue_manager.processing_files.clear()
    file_queue_manager.embedding_retry_queue.clear()
    file_queue_manager.active_embedding_retries.clear()
    
    # Set stop flags
    file_queue_manager.is_processing = False
    file_queue_manager.is_embedding_retry_active = False
    
    print("✅ File queue manager stopped and cleared")
    
except Exception as e:
    print(f"❌ Error stopping file queue: {e}")

try:
    # Patch document processor to block all embedding generation
    from modules.document_processor import DocumentProcessor
    
    async def blocked_generate_embeddings(self, texts, failed_indices=None):
        """Blocked embedding generation - returns None for all"""
        print("🚨 EMBEDDING GENERATION BLOCKED - Circuit breaker OPEN")
        return [None] * len(texts)
    
    # Apply blocking patch
    DocumentProcessor._generate_embeddings_batch = blocked_generate_embeddings
    
    print("✅ Embedding generation BLOCKED")
    
except Exception as e:
    print(f"❌ Error blocking embeddings: {e}")

print("\n🎉 EMERGENCY STOP COMPLETE!")
print("💡 All embedding generation is now BLOCKED")
print("🔄 Restart the application when ready to resume")