#!/usr/bin/env python3
"""
🧪 Vertex AI gemini-embedding-001 テストスクリプト
新しい3072次元エンベディングシステムの動作確認
"""

import os
import sys
import logging
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_vertex_ai_embedding():
    """Vertex AI Embedding テスト"""
    try:
        from modules.vertex_ai_embedding import get_vertex_ai_embedding_client, vertex_ai_embedding_available
        
        logger.info("🧪 Vertex AI Embedding テスト開始")
        
        # 利用可能性チェック
        if not vertex_ai_embedding_available():
            logger.error("❌ Vertex AI Embeddingが利用できません")
            return False
        
        # クライアント取得
        client = get_vertex_ai_embedding_client()
        if not client:
            logger.error("❌ Vertex AI クライアントの取得に失敗")
            return False
        
        # テストテキスト
        test_text = "これはVertex AI gemini-embedding-001のテストです。"
        
        # 単一テキストのembedding生成
        logger.info(f"📝 テストテキスト: {test_text}")
        embedding = client.generate_embedding(test_text)
        
        if embedding:
            logger.info(f"✅ Embedding生成成功: {len(embedding)}次元")
            if len(embedding) == 3072:
                logger.info("✅ 次元数確認: 3072次元 (正常)")
            else:
                logger.warning(f"⚠️ 予期しない次元数: {len(embedding)}次元")
            return True
        else:
            logger.error("❌ Embedding生成失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ Vertex AI Embeddingテストエラー: {e}")
        return False

def test_vector_search_system():
    """ベクトル検索システムテスト"""
    try:
        from modules.vector_search import VectorSearchSystem
        
        logger.info("🔍 ベクトル検索システムテスト開始")
        
        # システム初期化
        search_system = VectorSearchSystem()
        
        # テストクエリ
        test_query = "Vertex AIの使い方について教えてください"
        
        # クエリembedding生成
        logger.info(f"🔍 テストクエリ: {test_query}")
        embedding = search_system.generate_query_embedding(test_query)
        
        if embedding:
            logger.info(f"✅ クエリEmbedding生成成功: {len(embedding)}次元")
            if len(embedding) == 3072:
                logger.info("✅ 次元数確認: 3072次元 (正常)")
            else:
                logger.warning(f"⚠️ 予期しない次元数: {len(embedding)}次元")
            return True
        else:
            logger.error("❌ クエリEmbedding生成失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ ベクトル検索システムテストエラー: {e}")
        return False

def test_batch_embedding():
    """バッチEmbeddingテスト"""
    try:
        from modules.vertex_ai_embedding import get_vertex_ai_embedding_client
        
        logger.info("📦 バッチEmbeddingテスト開始")
        
        client = get_vertex_ai_embedding_client()
        if not client:
            logger.error("❌ Vertex AI クライアントが利用できません")
            return False
        
        # テストテキスト（複数）
        test_texts = [
            "これは最初のテストテキストです。",
            "これは2番目のテストテキストです。",
            "これは3番目のテストテキストです。"
        ]
        
        logger.info(f"📦 バッチテスト: {len(test_texts)}件のテキスト")
        embeddings = client.generate_embeddings_batch(test_texts)
        
        success_count = 0
        for i, embedding in enumerate(embeddings):
            if embedding:
                logger.info(f"✅ テキスト{i+1}: {len(embedding)}次元")
                success_count += 1
            else:
                logger.error(f"❌ テキスト{i+1}: 生成失敗")
        
        if success_count == len(test_texts):
            logger.info(f"✅ バッチEmbedding成功: {success_count}/{len(test_texts)}")
            return True
        else:
            logger.warning(f"⚠️ 部分的成功: {success_count}/{len(test_texts)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ バッチEmbeddingテストエラー: {e}")
        return False

def check_environment():
    """環境設定チェック"""
    logger.info("🔧 環境設定チェック")
    
    required_vars = [
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "USE_VERTEX_AI",
        "EMBEDDING_MODEL"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == "GOOGLE_APPLICATION_CREDENTIALS":
                if os.path.exists(value):
                    logger.info(f"✅ {var}: {value} (ファイル存在)")
                else:
                    logger.error(f"❌ {var}: {value} (ファイル不存在)")
                    missing_vars.append(var)
            else:
                logger.info(f"✅ {var}: {value}")
        else:
            logger.error(f"❌ {var}: 未設定")
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ 不足している環境変数: {missing_vars}")
        return False
    else:
        logger.info("✅ 環境設定確認完了")
        return True

def main():
    """メイン実行関数"""
    logger.info("🚀 gemini-embedding-001 テスト開始")
    logger.info("=" * 50)
    
    # 環境設定チェック
    if not check_environment():
        logger.error("❌ 環境設定に問題があります")
        sys.exit(1)
    
    logger.info("=" * 50)
    
    # テスト実行
    tests = [
        ("Vertex AI Embedding", test_vertex_ai_embedding),
        ("ベクトル検索システム", test_vector_search_system),
        ("バッチEmbedding", test_batch_embedding)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"🧪 {test_name} テスト実行中...")
        result = test_func()
        results.append((test_name, result))
        logger.info("=" * 50)
    
    # 結果サマリー
    logger.info("📊 テスト結果サマリー")
    success_count = 0
    for test_name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        logger.info(f"  {test_name}: {status}")
        if result:
            success_count += 1
    
    logger.info(f"📈 成功率: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    
    if success_count == len(results):
        logger.info("🎉 全テスト成功！gemini-embedding-001 移行完了")
        sys.exit(0)
    else:
        logger.error("❌ 一部テストが失敗しました")
        sys.exit(1)

if __name__ == "__main__":
    main()