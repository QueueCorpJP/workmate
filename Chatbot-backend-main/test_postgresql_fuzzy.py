"""
PostgreSQL Fuzzy Search テストスクリプト
Elasticsearchなしで動作するFuzzy Search機能のテスト
"""

import asyncio
import sys
import os

# パス設定
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_postgresql_fuzzy_search():
    """PostgreSQL Fuzzy Search機能をテスト"""
    print("🧪 PostgreSQL Fuzzy Search テスト開始")
    
    try:
        # 1. 初期化テスト
        print("\n1. 初期化テスト...")
        from modules.postgresql_fuzzy_search import initialize_postgresql_fuzzy
        success = await initialize_postgresql_fuzzy()
        if success:
            print("✅ 初期化成功")
        else:
            print("❌ 初期化失敗")
            return
        
        # 2. 基本検索テスト
        print("\n2. 基本検索テスト...")
        from modules.postgresql_fuzzy_search import fuzzy_search_chunks
        
        test_queries = [
            "安いパソコン",
            "価格",
            "料金",
            "コスト",
            "やすい PC",  # 表記ゆれテスト
            "価格表",      # 部分一致テスト
        ]
        
        for query in test_queries:
            print(f"\n📝 クエリ: '{query}'")
            results = await fuzzy_search_chunks(query, limit=5)
            print(f"   結果数: {len(results)}")
            
            for i, result in enumerate(results[:3]):  # 最大3件表示
                print(f"   [{i+1}] スコア: {result['score']:.3f}")
                print(f"       ファイル: {result['file_name']}")
                print(f"       内容: {result['content'][:100]}...")
                print(f"       検索タイプ: {result.get('search_types', [])}")
        
        # 3. 検索システム統合テスト
        print("\n3. 検索システム統合テスト...")
        from modules.chat_search_systems import postgresql_fuzzy_search_system
        
        query = "安いパソコン"
        print(f"\n📝 統合検索クエリ: '{query}'")
        results = await postgresql_fuzzy_search_system(query, limit=3)
        print(f"   統合検索結果数: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"   [{i+1}] タイトル: {result.get('title', 'N/A')}")
            print(f"       類似度: {result.get('similarity', 0):.3f}")
            print(f"       メタデータ: {result.get('metadata', {})}")
        
        # 4. フォールバック検索テスト
        print("\n4. フォールバック検索テスト...")
        from modules.chat_search_systems import fallback_search_system
        
        query = "価格"
        print(f"\n📝 フォールバック検索クエリ: '{query}'")
        results = await fallback_search_system(query, limit=3)
        print(f"   フォールバック検索結果数: {len(results)}")
        
        print("\n✅ PostgreSQL Fuzzy Search テスト完了")
        
    except Exception as e:
        print(f"\n❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()

async def test_search_comparison():
    """Elasticsearch vs PostgreSQL検索比較テスト"""
    print("\n🔍 検索システム比較テスト")
    
    try:
        test_query = "安いパソコン"
        print(f"\n📝 比較クエリ: '{test_query}'")
        
        # PostgreSQL Fuzzy Search
        print("\n--- PostgreSQL Fuzzy Search ---")
        from modules.chat_search_systems import postgresql_fuzzy_search_system
        pg_results = await postgresql_fuzzy_search_system(test_query, limit=3)
        print(f"PostgreSQL結果数: {len(pg_results)}")
        
        # Elasticsearch（利用可能な場合）
        print("\n--- Elasticsearch Fuzzy Search ---")
        try:
            from modules.chat_search_systems import elasticsearch_fuzzy_search_system
            es_results = await elasticsearch_fuzzy_search_system(test_query, limit=3)
            print(f"Elasticsearch結果数: {len(es_results)}")
        except Exception as e:
            print(f"Elasticsearch利用不可: {e}")
        
        # マルチシステム検索
        print("\n--- Multi-System Search ---")
        from modules.chat_search_systems import multi_system_search
        multi_results = await multi_system_search(test_query, limit=3)
        print(f"マルチシステム結果数: {len(multi_results)}")
        
        print("\n✅ 検索システム比較テスト完了")
        
    except Exception as e:
        print(f"\n❌ 比較テストエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 PostgreSQL Fuzzy Search テスト実行")
    print("=" * 50)
    
    # 基本テスト実行
    asyncio.run(test_postgresql_fuzzy_search())
    
    # 比較テスト実行
    asyncio.run(test_search_comparison())
    
    print("\n🎉 全テスト完了！")
    print("\n💡 使用方法:")
    print("   1. python main.py でサーバー起動")
    print("   2. チャットで「安いパソコン」などを検索")
    print("   3. PostgreSQL Fuzzy Searchが自動で動作します") 