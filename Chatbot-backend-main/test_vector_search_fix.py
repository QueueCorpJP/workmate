#!/usr/bin/env python3
"""
ベクトル検索修正のテストスクリプト
chunksテーブル対応版の動作確認
"""

import os
import sys
import logging
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_vector_search_availability():
    """ベクトル検索の利用可能性をテスト"""
    print("🔍 ベクトル検索利用可能性テスト開始")
    
    try:
        from modules.vector_search import vector_search_available, get_vector_search_instance
        
        # 利用可能性チェック
        is_available = vector_search_available()
        print(f"✅ ベクトル検索利用可能: {is_available}")
        
        if is_available:
            # インスタンス取得テスト
            instance = get_vector_search_instance()
            if instance:
                print("✅ ベクトル検索インスタンス取得成功")
                return instance
            else:
                print("❌ ベクトル検索インスタンス取得失敗")
                return None
        else:
            print("❌ ベクトル検索が利用できません")
            return None
            
    except Exception as e:
        print(f"❌ ベクトル検索テストエラー: {e}")
        return None

def test_embedding_generation(instance):
    """エンベディング生成テスト"""
    print("\n🧠 エンベディング生成テスト開始")
    
    try:
        test_query = "7100円"
        print(f"テストクエリ: '{test_query}'")
        
        embedding = instance.generate_query_embedding(test_query)
        
        if embedding and len(embedding) > 0:
            print(f"✅ エンベディング生成成功: {len(embedding)}次元")
            return embedding
        else:
            print("❌ エンベディング生成失敗")
            return None
            
    except Exception as e:
        print(f"❌ エンベディング生成エラー: {e}")
        return None

def test_vector_similarity_search(instance):
    """ベクトル類似検索テスト"""
    print("\n🔍 ベクトル類似検索テスト開始")
    
    try:
        test_query = "7100円"
        company_id = "77acc2e2-ce67-458d-bd38-7af0476b297a"  # ログから取得した会社ID
        
        print(f"テストクエリ: '{test_query}'")
        print(f"会社ID: {company_id}")
        
        # 会社IDありでテスト
        results_with_company = instance.vector_similarity_search(test_query, company_id, limit=5)
        print(f"✅ 会社IDありの検索結果: {len(results_with_company)}件")
        
        for i, result in enumerate(results_with_company[:3]):
            print(f"  {i+1}. {result['document_name']} [チャンク{result.get('chunk_index', 'N/A')}] 類似度: {result['similarity_score']:.3f}")
        
        # 会社IDなしでもテスト
        results_without_company = instance.vector_similarity_search(test_query, None, limit=5)
        print(f"✅ 会社IDなしの検索結果: {len(results_without_company)}件")
        
        return len(results_with_company) > 0 or len(results_without_company) > 0
        
    except Exception as e:
        print(f"❌ ベクトル類似検索エラー: {e}")
        import traceback
        print(f"詳細エラー: {traceback.format_exc()}")
        return False

def test_document_content_retrieval(instance):
    """ドキュメント内容取得テスト"""
    print("\n📖 ドキュメント内容取得テスト開始")
    
    try:
        test_query = "7100円"
        company_id = "77acc2e2-ce67-458d-bd38-7af0476b297a"
        
        content = instance.get_document_content_by_similarity(test_query, company_id, max_results=10)
        
        if content and len(content.strip()) > 0:
            print(f"✅ ドキュメント内容取得成功: {len(content)}文字")
            print(f"内容プレビュー: {content[:200]}...")
            return True
        else:
            print("❌ ドキュメント内容取得失敗（空の結果）")
            return False
            
    except Exception as e:
        print(f"❌ ドキュメント内容取得エラー: {e}")
        return False

def test_parallel_vector_search():
    """並列ベクトル検索テスト"""
    print("\n⚡ 並列ベクトル検索テスト開始")
    
    try:
        from modules.parallel_vector_search import get_parallel_vector_search_instance_sync
        
        instance = get_parallel_vector_search_instance_sync()
        if not instance:
            print("❌ 並列ベクトル検索インスタンス取得失敗")
            return False
        
        print("✅ 並列ベクトル検索インスタンス取得成功")
        
        test_query = "7100円"
        company_id = "77acc2e2-ce67-458d-bd38-7af0476b297a"
        
        content = instance.parallel_comprehensive_search_sync(test_query, company_id, max_results=10)
        
        if content and len(content.strip()) > 0:
            print(f"✅ 並列ベクトル検索成功: {len(content)}文字")
            print(f"内容プレビュー: {content[:200]}...")
            return True
        else:
            print("❌ 並列ベクトル検索失敗（空の結果）")
            return False
            
    except Exception as e:
        print(f"❌ 並列ベクトル検索エラー: {e}")
        import traceback
        print(f"詳細エラー: {traceback.format_exc()}")
        return False

def test_realtime_rag():
    """リアルタイムRAGテスト"""
    print("\n🚀 リアルタイムRAGテスト開始")
    
    try:
        from modules.realtime_rag import realtime_rag_available, get_realtime_rag_processor
        import asyncio
        
        # 利用可能性チェック
        is_available = realtime_rag_available()
        print(f"リアルタイムRAG利用可能: {is_available}")
        
        if not is_available:
            print("❌ リアルタイムRAGが利用できません")
            return False
        
        # プロセッサ取得
        processor = get_realtime_rag_processor()
        if not processor:
            print("❌ リアルタイムRAGプロセッサ取得失敗")
            return False
        
        print("✅ リアルタイムRAGプロセッサ取得成功")
        
        # 非同期テスト実行
        async def run_realtime_test():
            test_query = "7100円"
            company_id = "77acc2e2-ce67-458d-bd38-7af0476b297a"
            company_name = "NTT AT"
            
            result = await processor.process_realtime_rag(test_query, company_id, company_name, top_k=10)
            
            if result and result.get("answer"):
                print(f"✅ リアルタイムRAG成功: {len(result['answer'])}文字の回答")
                print(f"ステータス: {result.get('status', 'unknown')}")
                print(f"使用チャンク数: {result.get('chunks_used', 0)}")
                print(f"最高類似度: {result.get('top_similarity', 0.0):.3f}")
                print(f"回答プレビュー: {result['answer'][:200]}...")
                return True
            else:
                print("❌ リアルタイムRAG失敗（空の結果）")
                return False
        
        # イベントループで実行
        try:
            loop = asyncio.get_running_loop()
            print("⚠️ 既存のイベントループが検出されました")
            return False
        except RuntimeError:
            return asyncio.run(run_realtime_test())
            
    except Exception as e:
        print(f"❌ リアルタイムRAGエラー: {e}")
        import traceback
        print(f"詳細エラー: {traceback.format_exc()}")
        return False

def main():
    """メインテスト実行"""
    print("🔧 ベクトル検索修正テスト開始")
    print("=" * 50)
    
    # 環境変数チェック
    required_vars = ["GOOGLE_API_KEY", "SUPABASE_URL", "SUPABASE_KEY", "DB_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 必要な環境変数が不足: {missing_vars}")
        return False
    
    print("✅ 環境変数チェック完了")
    
    # テスト実行
    test_results = []
    
    # 1. ベクトル検索利用可能性テスト
    instance = test_vector_search_availability()
    test_results.append(("ベクトル検索利用可能性", instance is not None))
    
    if instance:
        # 2. エンベディング生成テスト
        embedding = test_embedding_generation(instance)
        test_results.append(("エンベディング生成", embedding is not None))
        
        # 3. ベクトル類似検索テスト
        search_success = test_vector_similarity_search(instance)
        test_results.append(("ベクトル類似検索", search_success))
        
        # 4. ドキュメント内容取得テスト
        content_success = test_document_content_retrieval(instance)
        test_results.append(("ドキュメント内容取得", content_success))
    
    # 5. 並列ベクトル検索テスト
    parallel_success = test_parallel_vector_search()
    test_results.append(("並列ベクトル検索", parallel_success))
    
    # 6. リアルタイムRAGテスト
    realtime_success = test_realtime_rag()
    test_results.append(("リアルタイムRAG", realtime_success))
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📊 テスト結果サマリー")
    print("=" * 50)
    
    success_count = 0
    for test_name, success in test_results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{test_name}: {status}")
        if success:
            success_count += 1
    
    print(f"\n総合結果: {success_count}/{len(test_results)} テスト成功")
    
    if success_count == len(test_results):
        print("🎉 全てのテストが成功しました！ベクトル検索修正完了")
        return True
    else:
        print("⚠️ 一部のテストが失敗しました。ログを確認してください。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)