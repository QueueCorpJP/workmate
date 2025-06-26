#!/usr/bin/env python3
"""
🧠 バッチエンベディング処理スクリプト
チャンクを10件ずつまとめてバッチで送信し、エラー回復機能付きでembeddingを生成

使用方法:
  python batch_embedding_processor.py                    # 全ての未処理チャンクを処理
  python batch_embedding_processor.py --limit 100       # 最大100チャンクまで処理
  python batch_embedding_processor.py --doc-id <ID>     # 特定のドキュメントのみ処理
  python batch_embedding_processor.py --retry-only      # 失敗したチャンクのみ再処理
"""

import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv
from modules.batch_embedding import batch_generate_embeddings_for_document, batch_generate_embeddings_for_all_pending
from supabase_adapter import get_supabase_client, select_data

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('batch_embedding.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()

async def process_specific_document(doc_id: str) -> bool:
    """特定のドキュメントを処理"""
    try:
        logger.info(f"🎯 特定ドキュメント処理開始: {doc_id}")
        
        # ドキュメント情報を取得
        doc_result = select_data(
            "document_sources",
            columns="id,name,type",
            filters={"id": doc_id}
        )
        
        if not doc_result.data:
            logger.error(f"❌ ドキュメントが見つかりません: {doc_id}")
            return False
        
        doc_info = doc_result.data[0]
        doc_name = doc_info.get('name', 'Unknown')
        doc_type = doc_info.get('type', 'Unknown')
        
        logger.info(f"📄 ドキュメント: {doc_name} ({doc_type})")
        
        # 未処理チャンク数を確認
        chunks_result = select_data(
            "chunks",
            columns="id",
            filters={
                "doc_id": doc_id,
                "embedding": None
            }
        )
        
        if not chunks_result.data:
            logger.info(f"✅ {doc_name}: 処理済み")
            return True
        
        chunk_count = len(chunks_result.data)
        logger.info(f"📊 未処理チャンク数: {chunk_count}")
        
        # バッチエンベディング生成実行
        success = await batch_generate_embeddings_for_document(doc_id, chunk_count)
        
        if success:
            logger.info(f"🎉 ドキュメント処理完了: {doc_name}")
        else:
            logger.warning(f"⚠️ ドキュメント処理で一部エラー: {doc_name}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ ドキュメント処理エラー: {e}")
        return False

async def process_all_pending(limit: int = None) -> bool:
    """全ての未処理チャンクを処理"""
    try:
        logger.info("🌐 全未処理チャンク処理開始")
        
        if limit:
            logger.info(f"📋 処理制限: {limit}チャンク")
        
        # 未処理チャンク数を確認
        chunks_result = select_data(
            "chunks",
            columns="id",
            filters={"embedding": None},
            limit=limit or 1000  # 確認用の制限
        )
        
        if not chunks_result.data:
            logger.info("✅ 処理すべきチャンクはありません")
            return True
        
        total_pending = len(chunks_result.data)
        logger.info(f"📊 未処理チャンク数: {total_pending}件")
        
        # バッチエンベディング生成実行
        success = await batch_generate_embeddings_for_all_pending(limit)
        
        if success:
            logger.info("🎉 全チャンク処理完了")
        else:
            logger.warning("⚠️ 全チャンク処理で一部エラー")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 全チャンク処理エラー: {e}")
        return False

async def retry_failed_chunks() -> bool:
    """失敗したチャンクのみ再処理"""
    try:
        logger.info("🔄 失敗チャンク再処理開始")
        
        # 未処理チャンクを取得（これらが失敗したチャンク）
        chunks_result = select_data(
            "chunks",
            columns="id,doc_id",
            filters={"embedding": None},
            limit=100  # 一度に処理する制限
        )
        
        if not chunks_result.data:
            logger.info("✅ 再処理すべきチャンクはありません")
            return True
        
        # ドキュメントごとにグループ化
        doc_chunks = {}
        for chunk in chunks_result.data:
            doc_id = chunk['doc_id']
            if doc_id not in doc_chunks:
                doc_chunks[doc_id] = []
            doc_chunks[doc_id].append(chunk['id'])
        
        logger.info(f"📊 再処理対象: {len(doc_chunks)}ドキュメント, {len(chunks_result.data)}チャンク")
        
        # ドキュメントごとに再処理
        total_success = True
        for doc_id, chunk_ids in doc_chunks.items():
            logger.info(f"🔄 ドキュメント {doc_id} 再処理: {len(chunk_ids)}チャンク")
            
            success = await batch_generate_embeddings_for_document(doc_id, len(chunk_ids))
            if not success:
                total_success = False
            
            # ドキュメント間で待機
            await asyncio.sleep(2)
        
        if total_success:
            logger.info("🎉 失敗チャンク再処理完了")
        else:
            logger.warning("⚠️ 失敗チャンク再処理で一部エラー")
        
        return total_success
        
    except Exception as e:
        logger.error(f"❌ 失敗チャンク再処理エラー: {e}")
        return False

async def show_status():
    """処理状況を表示"""
    try:
        logger.info("📊 処理状況確認中...")
        
        # 総チャンク数
        total_result = select_data("chunks", columns="id")
        total_chunks = len(total_result.data) if total_result.data else 0
        
        # 処理済みチャンク数
        processed_result = select_data(
            "chunks", 
            columns="id", 
            filters={"embedding": "NOT NULL"}
        )
        processed_chunks = len(processed_result.data) if processed_result.data else 0
        
        # 未処理チャンク数
        pending_result = select_data(
            "chunks", 
            columns="id", 
            filters={"embedding": None}
        )
        pending_chunks = len(pending_result.data) if pending_result.data else 0
        
        # 進捗率計算
        progress_rate = (processed_chunks / total_chunks * 100) if total_chunks > 0 else 0
        
        logger.info("=" * 50)
        logger.info("📊 エンベディング処理状況")
        logger.info("=" * 50)
        logger.info(f"📋 総チャンク数: {total_chunks}")
        logger.info(f"✅ 処理済み: {processed_chunks}")
        logger.info(f"⏳ 未処理: {pending_chunks}")
        logger.info(f"📈 進捗率: {progress_rate:.1f}%")
        logger.info("=" * 50)
        
        return pending_chunks == 0
        
    except Exception as e:
        logger.error(f"❌ 状況確認エラー: {e}")
        return False

def parse_arguments():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(
        description="バッチエンベディング処理スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python batch_embedding_processor.py                    # 全ての未処理チャンクを処理
  python batch_embedding_processor.py --limit 100       # 最大100チャンクまで処理
  python batch_embedding_processor.py --doc-id abc123   # 特定のドキュメントのみ処理
  python batch_embedding_processor.py --retry-only      # 失敗したチャンクのみ再処理
  python batch_embedding_processor.py --status          # 処理状況のみ表示
        """
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        help="処理するチャンクの最大数"
    )
    
    parser.add_argument(
        "--doc-id",
        type=str,
        help="処理する特定のドキュメントID"
    )
    
    parser.add_argument(
        "--retry-only",
        action="store_true",
        help="失敗したチャンクのみ再処理"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="処理状況のみ表示"
    )
    
    return parser.parse_args()

async def main():
    """メイン処理"""
    args = parse_arguments()
    
    logger.info("🚀 バッチエンベディング処理スクリプト開始")
    logger.info(f"⏰ 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 環境変数チェック
        auto_embed = os.getenv("AUTO_GENERATE_EMBEDDINGS", "false").lower()
        if auto_embed != "true":
            logger.warning("⚠️ AUTO_GENERATE_EMBEDDINGS=false です。処理を続行しますか？")
            logger.info("💡 環境変数を設定するか、.envファイルでAUTO_GENERATE_EMBEDDINGS=trueに設定してください")
        
        success = False
        
        if args.status:
            # 状況表示のみ
            success = await show_status()
        elif args.doc_id:
            # 特定ドキュメント処理
            success = await process_specific_document(args.doc_id)
        elif args.retry_only:
            # 失敗チャンク再処理
            success = await retry_failed_chunks()
        else:
            # 全チャンク処理
            success = await process_all_pending(args.limit)
        
        # 最終状況表示
        if not args.status:
            await show_status()
        
        if success:
            logger.info("✅ 処理完了")
            sys.exit(0)
        else:
            logger.error("❌ 処理失敗")
            sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("⏹️ ユーザーによる処理中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())