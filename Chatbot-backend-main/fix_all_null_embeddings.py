#!/usr/bin/env python3
"""
全てのNULLエンベディングを修復するスクリプト
"""

import asyncio
import logging
from datetime import datetime

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def fix_all_null_embeddings():
    """すべてのNULLエンベディングを修復"""
    logger.info("🔧 全NULLエンベディング修復開始")
    
    try:
        from modules.document_processor import DocumentProcessor
        
        # DocumentProcessorを使用してNULLエンベディングを修復
        processor = DocumentProcessor()
        
        # 全てのNULLエンベディングを修復
        stats = await processor.retry_failed_embeddings()
        
        logger.info(f"🎯 修復完了:")
        logger.info(f"   - 処理対象: {stats['total_failed']}件")
        logger.info(f"   - 成功: {stats['successful']}件")
        logger.info(f"   - 失敗: {stats['still_failed']}件")
        
        return stats['successful'] > 0
        
    except Exception as e:
        logger.error(f"❌ 全NULLエンベディング修復エラー: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(fix_all_null_embeddings())
    if success:
        print("✅ 修復完了")
    else:
        print("❌ 修復失敗")