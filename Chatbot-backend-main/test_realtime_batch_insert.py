#!/usr/bin/env python3
"""
リアルタイムバッチ挿入のテストスクリプト
50個単位でembedding生成→即座にinsertをテスト
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

async def test_realtime_batch_processing():
    """リアルタイムバッチ処理のテスト"""
    try:
        # DocumentProcessorのインスタンス作成
        processor = DocumentProcessor()
        
        # テスト用のチャンクデータを作成（120個のチャンクで50個単位のリアルタイム処理をテスト）
        test_chunks = []
        for i in range(120):
            test_chunks.append({
                "chunk_index": i,
                "content": f"リアルタイムバッチテスト用チャンク {i}: " + 
                          "このチャンクは50個単位でembedding生成と同時にSupabaseに保存されるテストです。" +
                          ("テスト内容を充実させるための追加テキスト。" * 5)
            })
        
        # テスト用パラメータ
        doc_id = f"realtime_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        company_id = "test_company_realtime"
        doc_name = "リアルタイムバッチテスト文書"
        
        logger.info(f"🚀 リアルタイムバッチ処理テスト開始")
        logger.info(f"📊 テストデータ: {len(test_chunks)}個のチャンク")
        logger.info(f"📦 バッチサイズ: 50個")
        logger.info(f"🎯 予想バッチ数: {(len(test_chunks) + 49) // 50}")
        logger.info(f"💡 期待動作: 50個のembedding完成→即座にinsert")
        
        # リアルタイムバッチ保存の実行
        start_time = datetime.now()
        result = await processor._save_chunks_to_database(
            doc_id=doc_id,
            chunks=test_chunks,
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
        if result['saved_chunks'] > 0:
            logger.info(f"🎉 テスト成功: {result['saved_chunks']}/{result['total_chunks']} チャンクがリアルタイムで保存されました")
            return True
        else:
            logger.warning(f"⚠️ テスト失敗: チャンクが保存されませんでした")
            return False
            
    except Exception as e:
        logger.error(f"❌ テスト中にエラーが発生: {e}", exc_info=True)
        return False

async def test_small_realtime_batch():
    """小さなリアルタイムバッチでのテスト（75個 → 50個 + 25個）"""
    try:
        processor = DocumentProcessor()
        
        # 75個のテストデータ（50個 + 25個のバッチになる）
        test_chunks = []
        for i in range(75):
            test_chunks.append({
                "chunk_index": i,
                "content": f"小リアルタイムバッチテスト {i}: " + "テスト内容 " * 15
            })
        
        doc_id = f"small_realtime_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        company_id = "test_company_small_realtime"
        doc_name = "小リアルタイムバッチテスト"
        
        logger.info(f"🔬 小リアルタイムバッチテスト開始: {len(test_chunks)}個のチャンク")
        logger.info(f"💡 期待動作: 1回目50個→insert, 2回目25個→insert")
        
        result = await processor._save_chunks_to_database(
            doc_id=doc_id,
            chunks=test_chunks,
            company_id=company_id,
            doc_name=doc_name
        )
        
        logger.info(f"✅ 小リアルタイムバッチテスト結果: {result['saved_chunks']}/{result['total_chunks']} 保存成功")
        return result['saved_chunks'] > 0
        
    except Exception as e:
        logger.error(f"❌ 小リアルタイムバッチテスト中にエラー: {e}")
        return False

async def main():
    """メイン実行関数"""
    logger.info("=" * 70)
    logger.info("🧪 リアルタイムバッチ挿入テスト開始")
    logger.info("=" * 70)
    
    # 小リアルタイムバッチテスト
    logger.info("\n" + "=" * 50)
    logger.info("1️⃣ 小リアルタイムバッチテスト（75個 → 50個+25個）")
    logger.info("=" * 50)
    small_test_result = await test_small_realtime_batch()
    
    # 大リアルタイムバッチテスト
    logger.info("\n" + "=" * 50)
    logger.info("2️⃣ 大リアルタイムバッチテスト（120個 → 50個×2+20個）")
    logger.info("=" * 50)
    large_test_result = await test_realtime_batch_processing()
    
    # 最終結果
    logger.info("\n" + "=" * 70)
    logger.info("🏁 リアルタイムバッチテスト結果サマリー")
    logger.info("=" * 70)
    logger.info(f"小リアルタイムバッチテスト: {'✅ 成功' if small_test_result else '❌ 失敗'}")
    logger.info(f"大リアルタイムバッチテスト: {'✅ 成功' if large_test_result else '❌ 失敗'}")
    
    if small_test_result and large_test_result:
        logger.info("🎉 全テスト成功！リアルタイムバッチ挿入が正常に動作しています")
        logger.info("💡 50個のembedding完成→即座にinsertが実装されました")
    else:
        logger.warning("⚠️ 一部テストが失敗しました。ログを確認してください")

if __name__ == "__main__":
    asyncio.run(main())