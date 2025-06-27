#!/usr/bin/env python3
"""
🧪 Vertex AI text-multilingual-embedding-002 テストスクリプト
新しい768次元エンベディングシステムの動作確認
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
        
        # テストテキスト（多言語）
        test_texts = [
            "これはVertex AI text-multilingual-embedding-002のテストです。",
            "This is a test for Vertex AI text-multilingual-embedding-002.",
            "Ceci est un test pour Vertex AI text-multilingual-embedding-002.",
            "これは多言語対応のテストです。"
        ]
        
        for i, test_text in enumerate(test_texts, 1):
            logger.info(f"📝 テストテキスト {i}: {test_text}")
            embedding = client.generate_embedding(test_text)
            
            if embedding:
                logger.info(f"✅ Embedding生成成功: {len(embedding)}次元")
                if len(embedding) == 768:
                    logger.info("✅ 次元数確認: 768次元 (正常)")
                else:
                    logger.warning(f"⚠️ 予期しない次元数: {len(embedding)}次元")
            else:
                logger.error(f"❌ Embedding生成失敗")
                return False
        
        return True
            
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
        
        # テストクエリ（多言語）
        test_queries = [
            "Vertex AIの使い方について教えてください",
            "How to use Vertex AI?",
            "Comment utiliser Vertex AI?"
        ]
        
        for i, test_query in enumerate(test_queries, 1):
            logger.info(f"🔍 テストクエリ {i}: {test_query}")
            embedding = search_system.generate_query_embedding(test_query)
            
            if embedding:
                logger.info(f"✅ クエリEmbedding生成成功: {len(embedding)}次元")
                if len(embedding) == 768:
                    logger.info("✅ 次元数確認: 768次元 (正常)")
                else:
                    logger.warning(f"⚠️ 予期しない次元数: {len(embedding)}次元")
            else:
                logger.error(f"❌ クエリEmbedding生成失敗")
                return False
        
        return True
            
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
        
        # テストテキスト（多言語バッチ）
        test_texts = [
            "これは最初のテストテキストです。",
            "This is the second test text.",
            "Ceci est le troisième texte de test.",
            "これは4番目のテストテキストです。"
        ]
        
        logger.info(f"📦 バッチテスト: {len(test_texts)}件のテキスト（多言語）")
        embeddings = client.generate_embeddings_batch(test_texts)
        
        success_count = 0
        for i, embedding in enumerate(embeddings):
            if embedding and len(embedding) == 768:
                logger.info(f"✅ テキスト{i+1}: {len(embedding)}次元")
                success_count += 1
            else:
                logger.error(f"❌ テキスト{i+1}: 生成失敗または次元数異常")
        
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
            elif var == "EMBEDDING_MODEL":
                if value == "text-multilingual-embedding-002":
                    logger.info(f"✅ {var}: {value} (正しい設定)")
                else:
                    logger.error(f"❌ {var}: {value} (text-multilingual-embedding-002 に設定してください)")
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
    logger.info("🚀 text-multilingual-embedding-002 テスト開始")
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
        logger.info("🎉 全テスト成功！text-multilingual-embedding-002 移行完了")
        sys.exit(0)
    else:
        logger.error("❌ 一部テストが失敗しました")
        sys.exit(1)

if __name__ == "__main__":
    main()