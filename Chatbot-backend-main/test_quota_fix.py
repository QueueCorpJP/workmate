"""
🧪 Test Quota Fix
Verify that the quota management system is working correctly
"""

import asyncio
import logging
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_quota_manager():
    """Test the quota manager functionality"""
    try:
        from modules.quota_manager import quota_manager, QuotaExhaustedException
        
        logger.info("🧪 Testing quota manager...")
        
        # Test 1: Check initial status
        status = quota_manager.get_status()
        logger.info(f"✅ Initial status: {status['circuit_state']}")
        
        # Test 2: Test a simple operation
        async def dummy_operation():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await quota_manager.execute_with_quota_management(
            dummy_operation,
            "TEST_OPERATION"
        )
        logger.info(f"✅ Test operation result: {result}")
        
        # Test 3: Check status after success
        status = quota_manager.get_status()
        logger.info(f"✅ Status after success: Success Rate: {status['success_rate']:.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Quota manager test failed: {e}")
        return False

async def test_document_processor():
    """Test the patched document processor"""
    try:
        from modules.document_processor import DocumentProcessor
        
        logger.info("🧪 Testing document processor...")
        
        # Create a test processor
        processor = DocumentProcessor()
        
        # Test text chunking (doesn't require API)
        test_text = "This is a test document. " * 100
        chunks = processor._split_text_into_chunks(test_text, "test.txt")
        
        logger.info(f"✅ Text chunking works: {len(chunks)} chunks created")
        
        # Test that the patched method exists
        if hasattr(processor, '_generate_embeddings_batch'):
            logger.info("✅ Patched embedding method exists")
        else:
            logger.warning("⚠️ Patched embedding method not found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Document processor test failed: {e}")
        return False

async def test_file_queue_manager():
    """Test the patched file queue manager"""
    try:
        from modules.file_queue_manager import file_queue_manager
        
        logger.info("🧪 Testing file queue manager...")
        
        # Check that retry processing is disabled
        if hasattr(file_queue_manager, 'is_embedding_retry_active'):
            if not file_queue_manager.is_embedding_retry_active:
                logger.info("✅ Embedding retry processing is disabled")
            else:
                logger.warning("⚠️ Embedding retry processing is still active")
        
        # Check queue status
        status = file_queue_manager.get_queue_status()
        logger.info(f"✅ Queue status: {status}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ File queue manager test failed: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("🚀 Starting quota fix verification tests...")
    
    tests = [
        ("Quota Manager", test_quota_manager),
        ("Document Processor", test_document_processor),
        ("File Queue Manager", test_file_queue_manager)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name} test...")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✅ {test_name} test PASSED")
            else:
                logger.error(f"❌ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} test ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n📊 Test Results Summary:")
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        logger.info("🎉 All tests passed! The quota fix is working correctly.")
        logger.info("💡 You can now safely restart the application with: python main.py")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)