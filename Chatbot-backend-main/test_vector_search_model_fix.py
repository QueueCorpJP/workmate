#!/usr/bin/env python3
"""
ベクトル検索モデル名修正のテストスクリプト
"""

import os
import sys
import logging
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_vector_search_initialization():
    """ベクトル検索システムの初期化テスト"""
    try:
        logger.info("🧪 ベクトル検索システム初期化テスト開始")
        
        # vector_search.py のテスト
        from modules.vector_search import VectorSearchSystem
        
        logger.info("📋 VectorSearchSystem 初期化中...")
        vector_search = VectorSearchSystem()
        logger.info(f"✅ VectorSearchSystem 初期化成功: モデル={vector_search.model}")
        
        # parallel_vector_search.py のテスト
        from modules.parallel_vector_search import ParallelVectorSearchSystem
        
        logger.info("📋 ParallelVectorSearchSystem 初期化中...")
        parallel_search = ParallelVectorSearchSystem()
        logger.info(f"✅ ParallelVectorSearchSystem 初期化成功: モデル={parallel_search.model}")
        
        # vector_search_parallel.py のテスト
        from modules.vector_search_parallel import ParallelVectorSearchSystem as ParallelVectorSearchSystem2
        
        logger.info("📋 ParallelVectorSearchSystem2 初期化中...")
        parallel_search2 = ParallelVectorSearchSystem2()
        logger.info(f"✅ ParallelVectorSearchSystem2 初期化成功: モデル={parallel_search2.model}")
        
        # realtime_rag.py のテスト
        from modules.realtime_rag import RealtimeRAGProcessor
        
        logger.info("📋 RealtimeRAGProcessor 初期化中...")
        rag_processor = RealtimeRAGProcessor()
        logger.info(f"✅ RealtimeRAGProcessor 初期化成功: モデル={rag_processor.embedding_model}")
        
        # auto_embedding.py のテスト
        from modules.auto_embedding import AutoEmbeddingGenerator
        
        logger.info("📋 AutoEmbeddingGenerator 初期化中...")
        auto_embedding = AutoEmbeddingGenerator()
        logger.info(f"✅ AutoEmbeddingGenerator 初期化成功: モデル={auto_embedding.embedding_model}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 初期化テストエラー: {e}")
        import traceback
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        return False

def test_embedding_generation():
    """エンベディング生成テスト"""
    try:
        logger.info("🧪 エンベディング生成テスト開始")
        
        from modules.vector_search import VectorSearchSystem
        
        vector_search = VectorSearchSystem()
        
        # テスト用クエリ
        test_query = "テスト用のクエリです"
        
        logger.info(f"📝 テストクエリでエンベディング生成: '{test_query}'")
        embedding = vector_search.generate_query_embedding(test_query)
        
        if embedding and len(embedding) > 0:
            logger.info(f"✅ エンベディング生成成功: {len(embedding)}次元")
            return True
        else:
            logger.error("❌ エンベディング生成失敗: 空のベクトル")
            return False
            
    except Exception as e:
        logger.error(f"❌ エンベディング生成テストエラー: {e}")
        import traceback
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        return False

def test_model_name_validation():
    """モデル名の検証テスト"""
    logger.info("🧪 モデル名検証テスト開始")
    
    # 環境変数の現在の値を確認
    embedding_model = os.getenv("EMBEDDING_MODEL")
    logger.info(f"📋 環境変数 EMBEDDING_MODEL: {embedding_model}")
    
    # モデル名が正しい形式かチェック
    if embedding_model and embedding_model.startswith(("models/", "tunedModels/")):
        logger.info("✅ モデル名は正しい形式です")
        return True
    else:
        logger.error(f"❌ モデル名が正しくない形式: {embedding_model}")
        return False

def main():
    """メイン実行関数"""
    logger.info("🚀 ベクトル検索モデル名修正テスト開始")
    
    # テスト実行
    tests = [
        ("モデル名検証", test_model_name_validation),
        ("システム初期化", test_vector_search_initialization),
        ("エンベディング生成", test_embedding_generation),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 {test_name}テスト実行中...")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name}テスト: 成功")
            else:
                logger.error(f"❌ {test_name}テスト: 失敗")
                
        except Exception as e:
            logger.error(f"❌ {test_name}テスト: 例外発生 - {e}")
            results.append((test_name, False))
    
    # 結果サマリー
    logger.info(f"\n{'='*50}")
    logger.info("📊 テスト結果サマリー")
    logger.info(f"{'='*50}")
    
    success_count = 0
    for test_name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        logger.info(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    logger.info(f"\n🎯 総合結果: {success_count}/{len(results)} テスト成功")
    
    if success_count == len(results):
        logger.info("🎉 すべてのテストが成功しました！")
        return True
    else:
        logger.error("⚠️ 一部のテストが失敗しました")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)