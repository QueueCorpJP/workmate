#!/usr/bin/env python3
"""
🔧 欠落エンベディング修復スクリプト
アップロード済みだがエンベディングが未生成のチャンクを処理
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from modules.batch_embedding import batch_generate_embeddings_for_document
from supabase_adapter import get_supabase_client, select_data

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()

async def fix_missing_embeddings():
    """欠落エンベディングを修復"""
    try:
        logger.info("🔧 欠落エンベディング修復開始")
        
        # 環境変数チェック
        auto_embed = os.getenv("AUTO_GENERATE_EMBEDDINGS", "false").lower()
        logger.info(f"📋 AUTO_GENERATE_EMBEDDINGS設定: {auto_embed}")
        
        # Supabaseクライアント取得
        supabase = get_supabase_client()
        logger.info("✅ Supabaseクライアント取得完了")
        
        # エンベディング未生成のチャンクを持つドキュメントを検索
        logger.info("🔍 エンベディング未生成のドキュメントを検索中...")
        
        # 未処理チャンクを持つドキュメントIDを取得
        chunks_result = select_data(
            "chunks",
            columns="doc_id",
            filters={"embedding": None},
            limit=100
        )
        
        if not chunks_result.data:
            logger.info("✅ 処理が必要なチャンクはありません")
            return True
        
        # ユニークなドキュメントIDを取得
        doc_ids = list(set(chunk['doc_id'] for chunk in chunks_result.data))
        logger.info(f"📋 処理対象ドキュメント数: {len(doc_ids)}")
        
        # 各ドキュメントの詳細情報を取得
        for i, doc_id in enumerate(doc_ids, 1):
            try:
                logger.info(f"🔄 [{i}/{len(doc_ids)}] ドキュメント処理開始: {doc_id}")
                
                # ドキュメント情報を取得
                doc_result = select_data(
                    "document_sources",
                    columns="id,name,type",
                    filters={"id": doc_id}
                )
                
                doc_name = "Unknown"
                if doc_result.data:
                    doc_name = doc_result.data[0].get('name', 'Unknown')
                    doc_type = doc_result.data[0].get('type', 'Unknown')
                    logger.info(f"  📄 ドキュメント: {doc_name} ({doc_type})")
                
                # 該当ドキュメントの未処理チャンク数を確認
                doc_chunks_result = select_data(
                    "chunks",
                    columns="id,chunk_index",
                    filters={
                        "doc_id": doc_id,
                        "embedding": None
                    }
                )
                
                if not doc_chunks_result.data:
                    logger.info(f"  ✅ {doc_name}: 処理済み")
                    continue
                
                chunk_count = len(doc_chunks_result.data)
                logger.info(f"  📊 未処理チャンク数: {chunk_count}")
                
                # バッチエンベディング生成実行
                logger.info(f"  🧠 バッチエンベディング生成開始: {doc_name}")
                success = await batch_generate_embeddings_for_document(doc_id, chunk_count)
                
                if success:
                    logger.info(f"  🎉 エンベディング生成完了: {doc_name}")
                else:
                    logger.warning(f"  ⚠️ エンベディング生成で一部エラー: {doc_name}")
                
                # 処理間隔を設ける（API制限対策）
                if i < len(doc_ids):
                    await asyncio.sleep(1)
                    
            except Exception as doc_error:
                logger.error(f"  ❌ ドキュメント {doc_id} 処理エラー: {doc_error}")
                continue
        
        # 最終結果確認
        logger.info("🔍 修復結果を確認中...")
        
        final_chunks_result = select_data(
            "chunks",
            columns="doc_id",
            filters={"embedding": None},
            limit=10
        )
        
        remaining_count = len(final_chunks_result.data) if final_chunks_result.data else 0
        logger.info(f"📊 修復後の未処理チャンク数: {remaining_count}")
        
        if remaining_count == 0:
            logger.info("🎉 すべてのエンベディング修復完了")
            return True
        else:
            logger.warning(f"⚠️ {remaining_count}個のチャンクが未処理のまま残っています")
            return False
        
    except Exception as e:
        logger.error(f"❌ 修復処理エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メイン処理"""
    logger.info("🚀 欠落エンベディング修復スクリプト開始")
    
    success = await fix_missing_embeddings()
    
    if success:
        logger.info("✅ 修復処理完了")
        sys.exit(0)
    else:
        logger.error("❌ 修復処理失敗")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())