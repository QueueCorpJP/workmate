#!/usr/bin/env python3
"""
バッチ挿入修正のテストスクリプト
50個単位でのチャンク+embedding保存をテスト
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.document_processor import DocumentProcessor

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_batch_insert():
    """バッチ挿入のテスト"""
    try:
        # DocumentProcessorのインスタンス作成
        processor = DocumentProcessor()
        
        # テスト用のチャンクデータを作成（120個のチャンクで50個単位のバッチ処理をテスト）
        test_chunks = []
        for i in range(120):
            test_chunks.append({
                "chunk_index": i,
                "content": f"これはテスト用のチャンク内容です。チャンク番号: {i}。" +
                          "このチャンクには十分な長さのテキストが含まれており、" +
                          ("embeddingの生成とデータベースへの保存をテストするために使用されます。" * 3)
            })
        
        # テスト用パラメータ
        doc_id = f"test_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        company_id = "test_company_001"
        doc_name = "バッチ挿入テスト文書"
        
        logger.info(f"🚀 バッチ挿入テスト開始")
        logger.info(f"📊 テストデータ: {len(test_chunks)}個のチャンク")
        logger.info(f"📦 バッチサイズ: 50個")
        logger.info(f"🎯 予想バッチ数: {(len(test_chunks) + 49) // 50}")
        
        # バッチ保存の実行
        start_time = datetime.now()
        result = await processor._save_chunks_to_database(
            chunks=test_chunks,
            doc_id=doc_id,
            company_id=company_id,
            doc_name=doc_name
        )
        end_time = datetime.now()
        
        # 結果の表示
        processing_time = (end_time - start_time).total_seconds()
        logger.info(f"⏱️ 処理時間: {processing_time:.2f}秒")
        logger.info(f"📈 処理結果:")
        logger.info(f"  - 総チャンク数: {result['total_chunks']}")
        logger.info(f"  - 保存成功: {result['saved_chunks']}")
        logger.info(f"  - embedding成功: {result['successful_embeddings']}")
        logger.info(f"  - embedding失敗: {result['failed_embeddings']}")
        logger.info(f"  - 再試行回数: {result['retry_attempts']}")
        
        # 成功率の計算
        if result['total_chunks'] > 0:
            save_rate = (result['saved_chunks'] / result['total_chunks']) * 100
            embedding_rate = (result['successful_embeddings'] / result['total_chunks']) * 100
            logger.info(f"📊 成功率:")
            logger.info(f"  - 保存成功率: {save_rate:.1f}%")
            logger.info(f"  - embedding成功率: {embedding_rate:.1f}%")
        
        # テスト結果の判定
        if result['saved_chunks'] == result['total_chunks']:
            logger.info("🎉 テスト成功: 全てのチャンクが正常に保存されました")
            return True
        else:
            logger.warning(f"⚠️ テスト部分成功: {result['saved_chunks']}/{result['total_chunks']} チャンクが保存されました")
            return False
            
    except Exception as e:
        logger.error(f"❌ テスト中にエラーが発生: {e}", exc_info=True)
        return False

async def test_small_batch():
    """小さなバッチでのテスト（10個）"""
    try:
        processor = DocumentProcessor()
        
        # 小さなテストデータ
        test_chunks = []
        for i in range(10):
            test_chunks.append({
                "chunk_index": i,
                "content": f"小さなバッチテスト用チャンク {i}: " + "テスト内容 " * 10
            })
        
        doc_id = f"small_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        company_id = "test_company_002"
        doc_name = "小バッチテスト"
        
        logger.info(f"🔬 小バッチテスト開始: {len(test_chunks)}個のチャンク")
        
        result = await processor._save_chunks_to_database(
            chunks=test_chunks,
            doc_id=doc_id,
            company_id=company_id,
            doc_name=doc_name
        )
        
        logger.info(f"✅ 小バッチテスト結果: {result['saved_chunks']}/{result['total_chunks']} 保存成功")
        return result['saved_chunks'] == result['total_chunks']
        
    except Exception as e:
        logger.error(f"❌ 小バッチテスト中にエラー: {e}")
        return False

async def main():
    """メイン実行関数"""
    logger.info("=" * 60)
    logger.info("🧪 バッチ挿入修正テスト開始")
    logger.info("=" * 60)
    
    # 小バッチテスト
    logger.info("\n" + "=" * 40)
    logger.info("1️⃣ 小バッチテスト（10個）")
    logger.info("=" * 40)
    small_test_result = await test_small_batch()
    
    # 大バッチテスト
    logger.info("\n" + "=" * 40)
    logger.info("2️⃣ 大バッチテスト（120個 → 50個単位）")
    logger.info("=" * 40)
    large_test_result = await test_batch_insert()
    
    # 最終結果
    logger.info("\n" + "=" * 60)
    logger.info("🏁 テスト結果サマリー")
    logger.info("=" * 60)
    logger.info(f"小バッチテスト: {'✅ 成功' if small_test_result else '❌ 失敗'}")
    logger.info(f"大バッチテスト: {'✅ 成功' if large_test_result else '❌ 失敗'}")
    
    if small_test_result and large_test_result:
        logger.info("🎉 全テスト成功！バッチ挿入修正が正常に動作しています")
    else:
        logger.warning("⚠️ 一部テストが失敗しました。ログを確認してください")

if __name__ == "__main__":
    asyncio.run(main())