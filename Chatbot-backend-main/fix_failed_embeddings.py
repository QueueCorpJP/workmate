#!/usr/bin/env python3
"""
🔧 失敗したEmbedding修復スクリプト
429エラーなどで失敗したembeddingを再生成
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

async def fix_failed_embeddings():
    """失敗したembeddingを修復"""
    try:
        logger.info("🔧 失敗したembedding修復開始")
        logger.info(f"⏰ 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 環境変数チェック
        required_env_vars = ["GOOGLE_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ 必要な環境変数が設定されていません: {missing_vars}")
            return False
        
        logger.info("✅ 環境変数チェック完了")
        
        # 失敗したembeddingを修復（最大10回リトライ）
        result = await document_processor.retry_failed_embeddings(max_retries=10)
        
        # 結果表示
        logger.info("\n" + "="*50)
        logger.info("📊 修復結果")
        logger.info("="*50)
        logger.info(f"🔍 失敗チャンク数: {result['total_failed']}")
        logger.info(f"⚙️ 処理完了数: {result['processed']}")
        logger.info(f"✅ 成功数: {result['successful']}")
        logger.info(f"❌ 依然失敗数: {result['still_failed']}")
        logger.info(f"🔄 最大再試行回数: {result['retry_attempts']}")
        
        if result['processed'] > 0:
            success_rate = (result['successful'] / result['processed']) * 100
            logger.info(f"📈 成功率: {success_rate:.1f}%")
        
        if result['still_failed'] > 0:
            logger.warning(f"⚠️ {result['still_failed']}件のembeddingが依然として失敗しています")
            logger.warning("   - API制限の可能性があります。時間をおいて再実行してください")
            logger.warning("   - または、GOOGLE_API_KEYの制限を確認してください")
        else:
            logger.info("🎉 全てのembeddingが正常に生成されました！")
        
        logger.info(f"⏰ 終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 修復処理エラー: {e}", exc_info=True)
        return False

async def fix_specific_document(doc_id: str):
    """特定ドキュメントの失敗したembeddingを修復"""
    try:
        logger.info(f"🔧 特定ドキュメントのembedding修復開始: {doc_id}")
        
        result = await document_processor.retry_failed_embeddings(
            doc_id=doc_id,
            max_retries=10
        )
        
        logger.info(f"📊 修復結果 (doc_id: {doc_id}):")
        logger.info(f"   - 失敗チャンク数: {result['total_failed']}")
        logger.info(f"   - 処理完了数: {result['processed']}")
        logger.info(f"   - 成功数: {result['successful']}")
        logger.info(f"   - 依然失敗数: {result['still_failed']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 特定ドキュメント修復エラー: {e}", exc_info=True)
        return False

async def fix_company_embeddings(company_id: str):
    """特定会社の失敗したembeddingを修復"""
    try:
        logger.info(f"🔧 特定会社のembedding修復開始: {company_id}")
        
        result = await document_processor.retry_failed_embeddings(
            company_id=company_id,
            max_retries=10
        )
        
        logger.info(f"📊 修復結果 (company_id: {company_id}):")
        logger.info(f"   - 失敗チャンク数: {result['total_failed']}")
        logger.info(f"   - 処理完了数: {result['processed']}")
        logger.info(f"   - 成功数: {result['successful']}")
        logger.info(f"   - 依然失敗数: {result['still_failed']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 特定会社修復エラー: {e}", exc_info=True)
        return False

async def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="失敗したembeddingを修復")
    parser.add_argument("--doc-id", help="特定のドキュメントIDを指定")
    parser.add_argument("--company-id", help="特定の会社IDを指定")
    parser.add_argument("--all", action="store_true", help="全ての失敗したembeddingを修復")
    
    args = parser.parse_args()
    
    try:
        if args.doc_id:
            success = await fix_specific_document(args.doc_id)
        elif args.company_id:
            success = await fix_company_embeddings(args.company_id)
        elif args.all:
            success = await fix_failed_embeddings()
        else:
            # デフォルト: 全体修復
            logger.info("オプションが指定されていません。全体修復を実行します。")
            logger.info("使用方法:")
            logger.info("  python fix_failed_embeddings.py --all                    # 全体修復")
            logger.info("  python fix_failed_embeddings.py --doc-id <document_id>  # 特定ドキュメント")
            logger.info("  python fix_failed_embeddings.py --company-id <company_id> # 特定会社")
            logger.info("")
            success = await fix_failed_embeddings()
        
        if success:
            logger.info("✅ 修復処理が正常に完了しました")
        else:
            logger.error("❌ 修復処理が失敗しました")
            
    except KeyboardInterrupt:
        logger.info("⏹️ ユーザーによって処理が中断されました")
    except Exception as e:
        logger.error(f"❌ 予期しないエラー: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())