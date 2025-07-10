#!/usr/bin/env python3
"""
エンベディング機能のテストスクリプト
エンベディング生成からデータベース保存まで各段階をテスト
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import List, Dict, Any

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_multi_api_embedding_client():
    """MultiAPIEmbeddingClientの動作テスト"""
    logger.info("🧪 MultiAPIEmbeddingClientのテスト開始")
    
    try:
        from modules.multi_api_embedding import MultiAPIEmbeddingClient, multi_api_embedding_available
        
        # 利用可能性チェック
        if not multi_api_embedding_available():
            logger.error("❌ MultiAPIEmbeddingClientが利用できません")
            return False
        
        # クライアント初期化
        client = MultiAPIEmbeddingClient()
        logger.info(f"✅ クライアント初期化成功: {len(client.api_keys)}個のAPIキー")
        logger.info(f"📊 期待される次元数: {client.expected_dimensions}")
        
        # テストテキスト
        test_texts = [
            "これはテスト用のテキストです。",
            "日本語のエンベディング生成をテストします。",
            "This is a test text for embedding generation."
        ]
        
        # 単一テキストのエンベディング生成テスト
        logger.info("🔍 単一テキストのエンベディング生成テスト")
        for i, text in enumerate(test_texts):
            try:
                embedding = await client.generate_embedding(text)
                if embedding and len(embedding) == client.expected_dimensions:
                    logger.info(f"✅ テキスト {i+1}: エンベディング生成成功 ({len(embedding)}次元)")
                else:
                    logger.error(f"❌ テキスト {i+1}: エンベディング生成失敗 - 結果: {type(embedding)} 長さ: {len(embedding) if embedding else 'None'}")
                    return False
            except Exception as e:
                logger.error(f"❌ テキスト {i+1}: エンベディング生成エラー - {e}")
                return False
        
        # バッチエンベディング生成テスト
        logger.info("🔍 バッチエンベディング生成テスト")
        try:
            batch_embeddings = await client.generate_embeddings_batch(test_texts)
            if len(batch_embeddings) == len(test_texts):
                success_count = sum(1 for emb in batch_embeddings if emb and len(emb) == client.expected_dimensions)
                logger.info(f"✅ バッチ処理成功: {success_count}/{len(test_texts)} 成功")
                
                if success_count < len(test_texts):
                    logger.warning(f"⚠️ 一部のエンベディング生成が失敗しました")
                    for i, emb in enumerate(batch_embeddings):
                        if not emb:
                            logger.warning(f"  - テキスト {i+1}: 失敗")
                        else:
                            logger.info(f"  - テキスト {i+1}: 成功 ({len(emb)}次元)")
                
                return success_count > 0
            else:
                logger.error(f"❌ バッチ処理失敗: 期待 {len(test_texts)}, 実際 {len(batch_embeddings)}")
                return False
                
        except Exception as e:
            logger.error(f"❌ バッチエンベディング生成エラー: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ MultiAPIEmbeddingClientテストエラー: {e}")
        return False

async def test_document_processor_embedding():
    """DocumentProcessorのエンベディング生成テスト"""
    logger.info("🧪 DocumentProcessorのエンベディング生成テスト開始")
    
    try:
        from modules.document_processor import DocumentProcessor
        
        # プロセッサ初期化
        processor = DocumentProcessor()
        logger.info("✅ DocumentProcessor初期化成功")
        
        # テストテキスト
        test_texts = [
            "これはDocumentProcessorのテストです。",
            "エンベディング生成機能をテストします。",
            "複数のテキストを処理してエンベディングを生成します。"
        ]
        
        # エンベディング生成テスト
        logger.info("🔍 DocumentProcessorエンベディング生成テスト")
        try:
            embeddings = await processor._generate_embeddings_batch(test_texts)
            
            if len(embeddings) == len(test_texts):
                success_count = sum(1 for emb in embeddings if emb is not None)
                logger.info(f"✅ DocumentProcessor処理成功: {success_count}/{len(test_texts)} 成功")
                
                for i, emb in enumerate(embeddings):
                    if emb:
                        logger.info(f"  - テキスト {i+1}: 成功 ({len(emb)}次元)")
                    else:
                        logger.warning(f"  - テキスト {i+1}: 失敗")
                
                return success_count > 0
            else:
                logger.error(f"❌ DocumentProcessor処理失敗: 期待 {len(test_texts)}, 実際 {len(embeddings)}")
                return False
                
        except Exception as e:
            logger.error(f"❌ DocumentProcessorエンベディング生成エラー: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ DocumentProcessorテストエラー: {e}")
        return False

async def test_database_connection():
    """データベース接続テスト"""
    logger.info("🧪 データベース接続テスト開始")
    
    try:
        from supabase_adapter import get_supabase_client
        
        supabase = get_supabase_client()
        logger.info("✅ Supabaseクライアント取得成功")
        
        # chunksテーブルの構造確認
        logger.info("🔍 chunksテーブル構造確認")
        try:
            # テーブル存在確認（簡単なクエリ）
            result = supabase.table("chunks").select("id").limit(1).execute()
            logger.info("✅ chunksテーブルアクセス成功")
            
            # embeddingコラムの存在確認
            result = supabase.table("chunks").select("id, embedding").limit(1).execute()
            logger.info("✅ embeddingコラムアクセス成功")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ chunksテーブルアクセスエラー: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ データベース接続エラー: {e}")
        return False

async def test_embedding_save_simulation():
    """エンベディング保存のシミュレーションテスト"""
    logger.info("🧪 エンベディング保存シミュレーションテスト開始")
    
    try:
        from supabase_adapter import get_supabase_client
        from modules.multi_api_embedding import MultiAPIEmbeddingClient, multi_api_embedding_available
        
        # 必要なコンポーネントの確認
        if not multi_api_embedding_available():
            logger.error("❌ MultiAPIEmbeddingClientが利用できません")
            return False
        
        supabase = get_supabase_client()
        client = MultiAPIEmbeddingClient()
        
        # テストデータ
        test_text = "これはエンベディング保存テスト用のテキストです。"
        test_doc_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        test_company_id = "test-company"
        
        logger.info(f"📝 テストデータ: doc_id={test_doc_id}")
        
        # エンベディング生成
        logger.info("🔍 エンベディング生成中...")
        embedding = await client.generate_embedding(test_text)
        
        if not embedding:
            logger.error("❌ エンベディング生成失敗")
            return False
        
        logger.info(f"✅ エンベディング生成成功: {len(embedding)}次元")
        
        # データベース保存テスト
        logger.info("🔍 データベース保存テスト中...")
        try:
            test_record = {
                "doc_id": test_doc_id,
                "chunk_index": 0,
                "content": test_text,
                "embedding": embedding,
                "company_id": test_company_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # 保存実行
            result = supabase.table("chunks").insert(test_record).execute()
            
            if result.data:
                logger.info(f"✅ データベース保存成功: {len(result.data)}件")
                
                # 保存されたデータの確認
                saved_id = result.data[0]["id"]
                logger.info(f"📊 保存されたレコードID: {saved_id}")
                
                # 保存されたエンベディングの確認
                check_result = supabase.table("chunks").select("id, embedding").eq("id", saved_id).execute()
                
                if check_result.data and check_result.data[0]["embedding"]:
                    saved_embedding = check_result.data[0]["embedding"]
                    logger.info(f"✅ エンベディング保存確認成功: {len(saved_embedding)}次元")
                    
                    # テストデータクリーンアップ
                    supabase.table("chunks").delete().eq("id", saved_id).execute()
                    logger.info("🧹 テストデータクリーンアップ完了")
                    
                    return True
                else:
                    logger.error("❌ 保存されたエンベディングが見つかりません")
                    return False
                    
            else:
                logger.error(f"❌ データベース保存失敗: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ データベース保存エラー: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ エンベディング保存シミュレーションエラー: {e}")
        return False

async def test_existing_null_embeddings():
    """既存のNULLエンベディングの確認"""
    logger.info("🧪 既存のNULLエンベディング確認テスト開始")
    
    try:
        from supabase_adapter import get_supabase_client
        
        supabase = get_supabase_client()
        
        # NULLエンベディングの数を確認
        null_result = supabase.table("chunks").select("id, doc_id, content").is_("embedding", "null").limit(5).execute()
        
        if null_result.data:
            logger.info(f"🔍 NULLエンベディング発見: {len(null_result.data)}件（最初の5件を表示）")
            
            for i, chunk in enumerate(null_result.data):
                logger.info(f"  {i+1}. ID: {chunk['id']}, DOC_ID: {chunk['doc_id']}")
                logger.info(f"     Content: {chunk['content'][:50]}...")
            
            return True
        else:
            logger.info("✅ NULLエンベディングは見つかりませんでした")
            return True
            
    except Exception as e:
        logger.error(f"❌ 既存NULLエンベディング確認エラー: {e}")
        return False

async def main():
    """メインテスト実行"""
    logger.info("🚀 エンベディング機能テスト開始")
    
    test_results = {}
    
    # 各テストを実行
    tests = [
        ("データベース接続", test_database_connection),
        ("MultiAPIEmbeddingClient", test_multi_api_embedding_client),
        ("DocumentProcessor", test_document_processor_embedding),
        ("エンベディング保存シミュレーション", test_embedding_save_simulation),
        ("既存NULLエンベディング確認", test_existing_null_embeddings)
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
    logger.info("📊 テスト結果サマリー")
    logger.info(f"{'='*60}")
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info(f"\n🎯 総合結果: {passed}/{total} テスト成功")
    
    if passed == total:
        logger.info("🎉 すべてのテストが成功しました！")
    else:
        logger.error("⚠️ 一部のテストが失敗しました。上記の詳細を確認してください。")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)