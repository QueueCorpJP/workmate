#!/usr/bin/env python3
"""
🔄 Embedding再実行テストスクリプト
失敗したembeddingの修復機能をテスト
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.document_processor import document_processor

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_embedding_retry():
    """embedding再実行機能のテスト"""
    try:
        logger.info("🚀 embedding再実行テスト開始")
        
        # 環境変数チェック
        required_env_vars = ["GOOGLE_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ 必要な環境変数が設定されていません: {missing_vars}")
            return False
        
        logger.info("✅ 環境変数チェック完了")
        
        # 1. 全体の失敗したembeddingを検索・修復
        logger.info("\n" + "="*50)
        logger.info("📋 テスト1: 全体の失敗したembedding修復")
        logger.info("="*50)
        
        result1 = await document_processor.retry_failed_embeddings(max_retries=10)
        
        logger.info(f"📊 結果1:")
        logger.info(f"   - 失敗チャンク数: {result1['total_failed']}")
        logger.info(f"   - 処理完了数: {result1['processed']}")
        logger.info(f"   - 成功数: {result1['successful']}")
        logger.info(f"   - 依然失敗数: {result1['still_failed']}")
        logger.info(f"   - 再試行回数: {result1['retry_attempts']}")
        
        # 2. 特定の会社のembedding修復（例）
        logger.info("\n" + "="*50)
        logger.info("📋 テスト2: 特定会社のembedding修復")
        logger.info("="*50)
        
        # テスト用の会社ID（実際の値に置き換えてください）
        test_company_id = "test-company-001"
        
        result2 = await document_processor.retry_failed_embeddings(
            company_id=test_company_id,
            max_retries=10
        )
        
        logger.info(f"📊 結果2 (company_id: {test_company_id}):")
        logger.info(f"   - 失敗チャンク数: {result2['total_failed']}")
        logger.info(f"   - 処理完了数: {result2['processed']}")
        logger.info(f"   - 成功数: {result2['successful']}")
        logger.info(f"   - 依然失敗数: {result2['still_failed']}")
        logger.info(f"   - 再試行回数: {result2['retry_attempts']}")
        
        # 3. 統計情報の表示
        logger.info("\n" + "="*50)
        logger.info("📊 最終統計")
        logger.info("="*50)
        
        total_processed = result1['processed'] + result2['processed']
        total_successful = result1['successful'] + result2['successful']
        total_failed = result1['still_failed'] + result2['still_failed']
        
        logger.info(f"🎯 全体統計:")
        logger.info(f"   - 総処理数: {total_processed}")
        logger.info(f"   - 総成功数: {total_successful}")
        logger.info(f"   - 総失敗数: {total_failed}")
        
        if total_processed > 0:
            success_rate = (total_successful / total_processed) * 100
            logger.info(f"   - 成功率: {success_rate:.1f}%")
        
        logger.info("🎉 embedding再実行テスト完了")
        return True
        
    except Exception as e:
        logger.error(f"❌ テスト実行エラー: {e}", exc_info=True)
        return False

async def test_specific_document_retry():
    """特定ドキュメントのembedding再実行テスト"""
    try:
        logger.info("\n" + "="*50)
        logger.info("📋 特定ドキュメントのembedding再実行テスト")
        logger.info("="*50)
        
        # テスト用のドキュメントID（実際の値に置き換えてください）
        test_doc_id = input("テスト対象のdoc_idを入力してください（Enterでスキップ）: ").strip()
        
        if not test_doc_id:
            logger.info("⏭️ 特定ドキュメントテストをスキップ")
            return True
        
        result = await document_processor.retry_failed_embeddings(
            doc_id=test_doc_id,
            max_retries=10
        )
        
        logger.info(f"📊 結果 (doc_id: {test_doc_id}):")
        logger.info(f"   - 失敗チャンク数: {result['total_failed']}")
        logger.info(f"   - 処理完了数: {result['processed']}")
        logger.info(f"   - 成功数: {result['successful']}")
        logger.info(f"   - 依然失敗数: {result['still_failed']}")
        logger.info(f"   - 再試行回数: {result['retry_attempts']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 特定ドキュメントテストエラー: {e}", exc_info=True)
        return False

async def main():
    """メイン実行関数"""
    logger.info("🔄 Embedding再実行テストスクリプト開始")
    logger.info(f"⏰ 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 基本的な再実行テスト
        success1 = await test_embedding_retry()
        
        # 特定ドキュメントの再実行テスト
        success2 = await test_specific_document_retry()
        
        if success1 and success2:
            logger.info("✅ 全てのテストが正常に完了しました")
        else:
            logger.error("❌ 一部のテストが失敗しました")
            
    except KeyboardInterrupt:
        logger.info("⏹️ ユーザーによってテストが中断されました")
    except Exception as e:
        logger.error(f"❌ 予期しないエラー: {e}", exc_info=True)
    finally:
        logger.info(f"⏰ 終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("🔄 Embedding再実行テストスクリプト終了")

if __name__ == "__main__":
    asyncio.run(main())