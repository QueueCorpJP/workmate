#!/usr/bin/env python3
"""
NULLエンベディング修復テスト
既存のNULLエンベディングを検出し、修復する
"""

import asyncio
import sys
import logging
from datetime import datetime

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_null_embedding_fix():
    """既存のNULLエンベディングを修復するテスト"""
    logger.info("🔧 NULLエンベディング修復テスト開始")
    
    try:
        from supabase_adapter import get_supabase_client
        from modules.multi_api_embedding import MultiAPIEmbeddingClient, multi_api_embedding_available
        
        # 必要なコンポーネントの確認
        if not multi_api_embedding_available():
            logger.error("❌ MultiAPIEmbeddingClientが利用できません")
            return False
        
        supabase = get_supabase_client()
        client = MultiAPIEmbeddingClient()
        
        # NULLエンベディングを検索
        logger.info("🔍 NULLエンベディングを検索中...")
        null_result = supabase.table("chunks").select("id, doc_id, content").is_("embedding", "null").limit(3).execute()
        
        if not null_result.data:
            logger.info("✅ 修復が必要なNULLエンベディングは見つかりませんでした")
            return True
        
        null_chunks = null_result.data
        logger.info(f"📊 修復対象: {len(null_chunks)}件のNULLエンベディング")
        
        success_count = 0
        failed_count = 0
        
        # 各NULLエンベディングを修復
        for i, chunk in enumerate(null_chunks):
            chunk_id = chunk["id"]
            content = chunk["content"]
            doc_id = chunk["doc_id"]
            
            logger.info(f"🔧 修復中 {i+1}/{len(null_chunks)}: {chunk_id}")
            logger.info(f"   Content: {content[:100]}...")
            
            try:
                # エンベディング生成
                embedding = await client.generate_embedding(content)
                
                if embedding and len(embedding) == client.expected_dimensions:
                    # データベース更新
                    update_result = supabase.table("chunks").update({
                        "embedding": embedding,
                        "updated_at": datetime.now().isoformat()
                    }).eq("id", chunk_id).execute()
                    
                    if update_result.data:
                        success_count += 1
                        logger.info(f"✅ 修復成功: {chunk_id} ({len(embedding)}次元)")
                    else:
                        failed_count += 1
                        logger.error(f"❌ DB更新失敗: {chunk_id}")
                else:
                    failed_count += 1
                    logger.error(f"❌ エンベディング生成失敗: {chunk_id}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ 修復エラー {chunk_id}: {e}")
            
            # API制限対策
            if i < len(null_chunks) - 1:
                await asyncio.sleep(1.0)
        
        # 結果サマリー
        logger.info(f"🎯 修復完了: 成功 {success_count}, 失敗 {failed_count}")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"❌ NULLエンベディング修復テストエラー: {e}")
        return False

async def test_document_processor_fix():
    """DocumentProcessorの修復テスト"""
    logger.info("🔧 DocumentProcessor修復テスト開始")
    
    try:
        from modules.document_processor import DocumentProcessor
        
        # DocumentProcessor初期化
        processor = DocumentProcessor()
        logger.info("✅ DocumentProcessor初期化成功")
        
        # テストテキスト
        test_texts = [
            "DocumentProcessor修復テスト用のテキストです。",
            "エンベディング生成機能が正常に動作するかテストします。"
        ]
        
        # エンベディング生成テスト
        logger.info("🔍 DocumentProcessorエンベディング生成テスト")
        embeddings = await processor._generate_embeddings_batch(test_texts)
        
        if len(embeddings) == len(test_texts):
            success_count = sum(1 for emb in embeddings if emb is not None)
            logger.info(f"✅ DocumentProcessor修復成功: {success_count}/{len(test_texts)} 成功")
            
            for i, emb in enumerate(embeddings):
                if emb:
                    logger.info(f"  - テキスト {i+1}: 成功 ({len(emb)}次元)")
                else:
                    logger.warning(f"  - テキスト {i+1}: 失敗")
            
            return success_count > 0
        else:
            logger.error(f"❌ DocumentProcessor修復失敗: 期待 {len(test_texts)}, 実際 {len(embeddings)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ DocumentProcessor修復テストエラー: {e}")
        return False

async def main():
    """メイン修復テスト実行"""
    logger.info("🚀 NULLエンベディング修復テスト開始")
    
    test_results = {}
    
    # 各テストを実行
    tests = [
        ("DocumentProcessor修復", test_document_processor_fix),
        ("NULLエンベディング修復", test_null_embedding_fix)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 {test_name} テスト開始")
        logger.info(f"{'='*60}")
        
        try:
            result = await test_func()
            test_results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name} テスト成功")
            else:
                logger.error(f"❌ {test_name} テスト失敗")
                
        except Exception as e:
            logger.error(f"❌ {test_name} テスト中にエラー: {e}")
            test_results[test_name] = False
    
    # 結果サマリー
    logger.info(f"\n{'='*60}")
    logger.info("📊 修復テスト結果サマリー")
    logger.info(f"{'='*60}")
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info(f"\n🎯 総合結果: {passed}/{total} テスト成功")
    
    if passed == total:
        logger.info("🎉 すべての修復テストが成功しました！")
    else:
        logger.error("⚠️ 一部の修復テストが失敗しました。")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)