#!/usr/bin/env python3
"""
🧪 バッチエンベディングシステムのテストスクリプト
新しいバッチ処理システムの動作を検証
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from modules.batch_embedding import BatchEmbeddingGenerator, batch_generate_embeddings_for_all_pending
from supabase_adapter import get_supabase_client, select_data, insert_data

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()

async def test_batch_embedding_system():
    """バッチエンベディングシステムのテスト"""
    try:
        logger.info("🧪 バッチエンベディングシステムテスト開始")
        
        # 1. 環境変数チェック
        logger.info("📋 環境変数チェック...")
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        auto_embed = os.getenv("AUTO_GENERATE_EMBEDDINGS", "false").lower()
        
        if not api_key:
            logger.error("❌ GOOGLE_API_KEY または GEMINI_API_KEY が設定されていません")
            return False
        
        logger.info(f"✅ API Key: 設定済み")
        logger.info(f"✅ AUTO_GENERATE_EMBEDDINGS: {auto_embed}")
        
        # 2. バッチエンベディング生成器の初期化テスト
        logger.info("🔧 バッチエンベディング生成器初期化テスト...")
        generator = BatchEmbeddingGenerator()
        
        if not generator._init_clients():
            logger.error("❌ バッチエンベディング生成器の初期化に失敗")
            return False
        
        logger.info("✅ バッチエンベディング生成器初期化成功")
        
        # 3. 未処理チャンクの確認
        logger.info("📊 未処理チャンク確認...")
        pending_chunks = generator._get_pending_chunks(limit=20)
        
        if not pending_chunks:
            logger.info("✅ 未処理チャンクはありません")
            
            # テスト用のダミーチャンクを作成
            logger.info("🔧 テスト用ダミーチャンクを作成...")
            await create_test_chunks()
            
            # 再度確認
            pending_chunks = generator._get_pending_chunks(limit=5)
        
        if pending_chunks:
            logger.info(f"📋 未処理チャンク数: {len(pending_chunks)}")
            
            # 4. 小規模バッチテスト（最大5チャンク）
            logger.info("🧪 小規模バッチテスト開始...")
            test_chunks = pending_chunks[:5]  # 最大5チャンクでテスト
            
            success_count = 0
            for chunk in test_chunks:
                try:
                    chunk_id = chunk['id']
                    content = chunk['content']
                    
                    # embedding生成テスト
                    embedding = await generator._generate_embedding_with_retry(content, chunk_id)
                    
                    if embedding:
                        logger.info(f"  ✅ チャンク {chunk_id}: embedding生成成功 ({len(embedding)}次元)")
                        success_count += 1
                    else:
                        logger.warning(f"  ⚠️ チャンク {chunk_id}: embedding生成失敗")
                        
                except Exception as e:
                    logger.error(f"  ❌ チャンク {chunk['id']} テストエラー: {e}")
            
            logger.info(f"📊 小規模テスト結果: {success_count}/{len(test_chunks)} 成功")
            
            if success_count > 0:
                logger.info("✅ バッチエンベディングシステム動作確認完了")
                return True
            else:
                logger.error("❌ バッチエンベディングシステムでエラーが発生")
                return False
        else:
            logger.info("✅ 処理すべきチャンクがないため、システムは正常です")
            return True
        
    except Exception as e:
        logger.error(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def create_test_chunks():
    """テスト用のダミーチャンクを作成"""
    try:
        logger.info("🔧 テスト用チャンク作成中...")
        
        # テスト用ドキュメントID
        test_doc_id = "test-batch-embedding-doc"
        
        # 既存のテストチャンクを削除
        from supabase_adapter import delete_data
        try:
            delete_data("chunks", "doc_id", test_doc_id)
            delete_data("document_sources", "id", test_doc_id)
        except:
            pass  # エラーは無視
        
        # テスト用ドキュメントソースを作成
        doc_data = {
            "id": test_doc_id,
            "name": "バッチエンベディングテスト用ドキュメント",
            "type": "test",
            "page_count": 1,
            "uploaded_by": "test-user",
            "company_id": "test-company",
            "uploaded_at": datetime.now().isoformat()
        }
        
        insert_data("document_sources", doc_data)
        
        # テスト用チャンクを作成
        test_contents = [
            "これはバッチエンベディングのテスト用チャンク1です。",
            "バッチ処理システムの動作を確認するためのテストデータです。",
            "10件ずつまとめて処理する新しいシステムをテストしています。",
            "APIの負荷軽減とレート制限対策が目的です。",
            "エラー回復機能も含まれています。"
        ]
        
        for i, content in enumerate(test_contents):
            chunk_data = {
                "doc_id": test_doc_id,
                "chunk_index": i,
                "content": content,
                "company_id": "test-company"
            }
            
            insert_data("chunks", chunk_data)
        
        logger.info(f"✅ テスト用チャンク作成完了: {len(test_contents)}件")
        
    except Exception as e:
        logger.error(f"❌ テスト用チャンク作成エラー: {e}")

async def test_full_batch_processing():
    """完全なバッチ処理のテスト"""
    try:
        logger.info("🚀 完全バッチ処理テスト開始")
        
        # 未処理チャンク数を確認
        chunks_result = select_data(
            "chunks",
            columns="id",
            filters={"embedding": None},
            limit=50  # テスト用制限
        )
        
        if not chunks_result.data:
            logger.info("✅ 処理すべきチャンクはありません")
            return True
        
        pending_count = len(chunks_result.data)
        logger.info(f"📊 未処理チャンク数: {pending_count}")
        
        # バッチ処理実行（制限付き）
        success = await batch_generate_embeddings_for_all_pending(limit=20)
        
        if success:
            logger.info("✅ 完全バッチ処理テスト成功")
        else:
            logger.warning("⚠️ 完全バッチ処理テストで一部エラー")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 完全バッチ処理テストエラー: {e}")
        return False

async def cleanup_test_data():
    """テストデータのクリーンアップ"""
    try:
        logger.info("🧹 テストデータクリーンアップ...")
        
        from supabase_adapter import delete_data
        
        # テスト用チャンクとドキュメントを削除
        delete_data("chunks", "doc_id", "test-batch-embedding-doc")
        delete_data("document_sources", "id", "test-batch-embedding-doc")
        
        logger.info("✅ テストデータクリーンアップ完了")
        
    except Exception as e:
        logger.warning(f"⚠️ テストデータクリーンアップエラー: {e}")

async def main():
    """メイン処理"""
    logger.info("🧪 バッチエンベディングシステムテスト開始")
    logger.info(f"⏰ 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 基本システムテスト
        basic_test_success = await test_batch_embedding_system()
        
        if not basic_test_success:
            logger.error("❌ 基本システムテストに失敗")
            sys.exit(1)
        
        # 完全バッチ処理テスト
        full_test_success = await test_full_batch_processing()
        
        if not full_test_success:
            logger.warning("⚠️ 完全バッチ処理テストで一部エラー")
        
        # テストデータクリーンアップ
        await cleanup_test_data()
        
        if basic_test_success and full_test_success:
            logger.info("🎉 全てのテストが成功しました")
            sys.exit(0)
        else:
            logger.warning("⚠️ 一部のテストで問題が発生しました")
            sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("⏹️ ユーザーによるテスト中断")
        await cleanup_test_data()
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 予期しないテストエラー: {e}")
        import traceback
        traceback.print_exc()
        await cleanup_test_data()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())