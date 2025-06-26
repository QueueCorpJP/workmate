"""
🧪 Vertex AI Embedding テストスクリプト
Vertex AI gemini-embedding-001 の動作確認用
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.vertex_ai_embedding import get_vertex_ai_embedding_client, vertex_ai_embedding_available
from modules.auto_embedding import AutoEmbeddingGenerator
from modules.realtime_rag import RealtimeRAGProcessor
from modules.vector_search import VectorSearchSystem

# 環境変数読み込み
load_dotenv()

def test_vertex_ai_client():
    """Vertex AI クライアントの基本テスト"""
    print("=" * 60)
    print("🧪 Vertex AI Embedding クライアント テスト")
    print("=" * 60)
    
    # 利用可能性チェック
    if not vertex_ai_embedding_available():
        print("❌ Vertex AI Embedding が利用できません")
        print("   - GOOGLE_CLOUD_PROJECT が設定されているか確認してください")
        print("   - USE_VERTEX_AI=true が設定されているか確認してください")
        return False
    
    # クライアント取得
    client = get_vertex_ai_embedding_client()
    if not client:
        print("❌ Vertex AI クライアントの初期化に失敗")
        return False
    
    print("✅ Vertex AI クライアント初期化成功")
    
    # テスト用テキスト
    test_texts = [
        "これはテスト用のテキストです。",
        "Vertex AI embedding test text.",
        "日本語と英語の混在テキスト mixed language text."
    ]
    
    # 単一テキストのテスト
    print("\n📝 単一テキスト エンベディング テスト:")
    for i, text in enumerate(test_texts, 1):
        print(f"  {i}. テキスト: {text}")
        embedding = client.generate_embedding(text)
        
        if embedding:
            print(f"     ✅ 成功: {len(embedding)}次元")
            print(f"     最初の5要素: {embedding[:5]}")
        else:
            print(f"     ❌ 失敗")
    
    # バッチテストの実行
    print(f"\n📦 バッチ エンベディング テスト:")
    batch_embeddings = client.generate_embeddings_batch(test_texts)
    
    for i, (text, embedding) in enumerate(zip(test_texts, batch_embeddings), 1):
        print(f"  {i}. テキスト: {text[:30]}...")
        if embedding:
            print(f"     ✅ 成功: {len(embedding)}次元")
        else:
            print(f"     ❌ 失敗")
    
    return True

def test_auto_embedding_integration():
    """AutoEmbeddingGenerator との統合テスト"""
    print("\n" + "=" * 60)
    print("🔄 AutoEmbeddingGenerator 統合テスト")
    print("=" * 60)
    
    try:
        generator = AutoEmbeddingGenerator()
        print("✅ AutoEmbeddingGenerator 初期化成功")
        
        # Vertex AI使用状況の確認
        if generator.use_vertex_ai:
            print("🧠 Vertex AI モード有効")
        else:
            print("🔄 標準 Gemini API モード")
        
        print(f"📋 エンベディングモデル: {generator.embedding_model}")
        
        return True
        
    except Exception as e:
        print(f"❌ AutoEmbeddingGenerator 初期化エラー: {e}")
        return False

async def test_realtime_rag_integration():
    """RealtimeRAGProcessor との統合テスト"""
    print("\n" + "=" * 60)
    print("⚡ RealtimeRAGProcessor 統合テスト")
    print("=" * 60)
    
    try:
        processor = RealtimeRAGProcessor()
        print("✅ RealtimeRAGProcessor 初期化成功")
        
        # Vertex AI使用状況の確認
        if processor.use_vertex_ai:
            print("🧠 Vertex AI モード有効")
        else:
            print("🔄 標準 Gemini API モード")
        
        print(f"📋 エンベディングモデル: {processor.embedding_model}")
        
        # エンベディング生成テスト
        test_question = "テスト用の質問です"
        print(f"\n📝 エンベディング生成テスト: {test_question}")
        
        try:
            embedding = await processor.step2_generate_embedding(test_question)
            print(f"✅ エンベディング生成成功: {len(embedding)}次元")
            return True
        except Exception as e:
            print(f"❌ エンベディング生成エラー: {e}")
            return False
        
    except Exception as e:
        print(f"❌ RealtimeRAGProcessor 初期化エラー: {e}")
        return False

def test_vector_search_integration():
    """VectorSearchSystem との統合テスト"""
    print("\n" + "=" * 60)
    print("🔍 VectorSearchSystem 統合テスト")
    print("=" * 60)
    
    try:
        search_system = VectorSearchSystem()
        print("✅ VectorSearchSystem 初期化成功")
        
        # Vertex AI使用状況の確認
        if search_system.use_vertex_ai:
            print("🧠 Vertex AI モード有効")
        else:
            print("🔄 標準 Gemini API モード")
        
        print(f"📋 エンベディングモデル: {search_system.model}")
        
        # クエリエンベディング生成テスト
        test_query = "テスト用のクエリです"
        print(f"\n📝 クエリエンベディング生成テスト: {test_query}")
        
        embedding = search_system.generate_query_embedding(test_query)
        if embedding:
            print(f"✅ クエリエンベディング生成成功: {len(embedding)}次元")
            return True
        else:
            print(f"❌ クエリエンベディング生成失敗")
            return False
        
    except Exception as e:
        print(f"❌ VectorSearchSystem 初期化エラー: {e}")
        return False

def print_environment_info():
    """環境情報の表示"""
    print("=" * 60)
    print("🔧 環境設定情報")
    print("=" * 60)
    
    print(f"EMBEDDING_MODEL: {os.getenv('EMBEDDING_MODEL', 'Not set')}")
    print(f"USE_VERTEX_AI: {os.getenv('USE_VERTEX_AI', 'Not set')}")
    print(f"GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT', 'Not set')}")
    print(f"GOOGLE_API_KEY: {'Set' if os.getenv('GOOGLE_API_KEY') else 'Not set'}")
    print(f"AUTO_GENERATE_EMBEDDINGS: {os.getenv('AUTO_GENERATE_EMBEDDINGS', 'Not set')}")

async def main():
    """メインテスト実行"""
    print("🚀 Vertex AI Embedding 統合テスト開始")
    
    # 環境情報表示
    print_environment_info()
    
    # テスト実行
    tests = [
        ("Vertex AI Client", test_vertex_ai_client),
        ("AutoEmbedding Integration", test_auto_embedding_integration),
        ("RealtimeRAG Integration", test_realtime_rag_integration),
        ("VectorSearch Integration", test_vector_search_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} でエラー: {e}")
            results.append((test_name, False))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 結果: {passed}/{len(results)} テスト成功")
    
    if passed == len(results):
        print("🎉 すべてのテストが成功しました！")
    else:
        print("⚠️  一部のテストが失敗しました。設定を確認してください。")

if __name__ == "__main__":
    # タイポ修正
    def vector_ai_embedding_available():
        return vertex_ai_embedding_available()
    
    asyncio.run(main())