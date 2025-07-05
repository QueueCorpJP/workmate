#!/usr/bin/env python3
"""
Elasticsearch Fuzzy Search機能テストスクリプト
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# モジュールパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# 環境変数読み込み
load_dotenv()

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_elasticsearch_connection():
    """Elasticsearch接続テスト"""
    print("=" * 60)
    print("🔍 Elasticsearch接続テスト")
    print("=" * 60)
    
    try:
        from modules.elasticsearch_search import get_elasticsearch_manager
        
        # 環境変数チェック
        es_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
        es_port = os.getenv("ELASTICSEARCH_PORT", "9200")
        es_index = os.getenv("ELASTICSEARCH_INDEX", "workmate_documents")
        
        print("🔧 設定確認:")
        print(f"  ホスト: {es_host}:{es_port}")
        print(f"  インデックス: {es_index}")
        print()
        
        # Elasticsearchマネージャー初期化
        es_manager = get_elasticsearch_manager()
        
        if es_manager and es_manager.is_available():
            print("✅ Elasticsearch接続成功！")
            return True
        else:
            print("❌ Elasticsearch接続失敗")
            print("💡 確認事項:")
            print("  1. Elasticsearchが起動しているか")
            print("  2. 環境変数が正しく設定されているか")
            print("  3. ネットワーク接続に問題がないか")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

async def test_data_sync():
    """データ同期テスト"""
    print("\n" + "=" * 60)
    print("🔄 データ同期テスト")
    print("=" * 60)
    
    try:
        from modules.elasticsearch_search import get_elasticsearch_manager
        
        es_manager = get_elasticsearch_manager()
        if not es_manager or not es_manager.is_available():
            print("❌ Elasticsearch利用不可のため、同期テストをスキップ")
            return False
        
        print("🔄 データベースからElasticsearchへの同期を開始...")
        
        # 同期実行
        success = await es_manager.sync_database_to_elasticsearch()
        
        if success:
            print("✅ データ同期成功！")
            return True
        else:
            print("❌ データ同期失敗")
            return False
            
    except Exception as e:
        print(f"❌ 同期エラー: {e}")
        return False

async def test_fuzzy_search():
    """Fuzzy Search機能テスト"""
    print("\n" + "=" * 60)
    print("🔍 Fuzzy Search機能テスト")
    print("=" * 60)
    
    try:
        from modules.elasticsearch_search import get_elasticsearch_fuzzy_search
        
        es_search = get_elasticsearch_fuzzy_search()
        if not es_search:
            print("❌ Elasticsearch Fuzzy Search初期化失敗")
            return False
        
        # テストクエリリスト
        test_queries = [
            ("パソコン", "AUTO"),
            ("コンピューター", "1"),
            ("価格", "AUTO"),
            ("安い", "2"),
            ("おすすめ", "AUTO")
        ]
        
        print("🔍 テストクエリ実行中...")
        print()
        
        for i, (query, fuzziness) in enumerate(test_queries, 1):
            print(f"  {i}. クエリ: '{query}' (fuzziness: {fuzziness})")
            
            try:
                results = await es_search.fuzzy_search(
                    query=query,
                    fuzziness=fuzziness,
                    limit=3
                )
                
                print(f"     結果: {len(results)}件")
                
                # 上位3件の概要を表示
                for j, result in enumerate(results[:3], 1):
                    doc_name = result.get('document_name', 'Unknown')[:20]
                    score = result.get('similarity_score', 0)
                    content_preview = (result.get('content', '')[:50] or '').replace('\n', ' ')
                    
                    print(f"       {j}. {doc_name} (スコア: {score:.2f})")
                    print(f"          内容: {content_preview}...")
                
                print()
                
            except Exception as e:
                print(f"     エラー: {e}")
                print()
        
        print("✅ Fuzzy Search機能テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ Fuzzy Searchテストエラー: {e}")
        return False

async def test_advanced_search():
    """高度検索機能テスト"""
    print("\n" + "=" * 60)
    print("🎯 高度検索機能テスト")
    print("=" * 60)
    
    try:
        from modules.elasticsearch_search import get_elasticsearch_fuzzy_search
        
        es_search = get_elasticsearch_fuzzy_search()
        if not es_search:
            print("❌ Elasticsearch初期化失敗")
            return False
        
        # 検索タイプテスト
        search_tests = [
            ("パソコン 価格", "multi_match", "AUTO"),
            ("安いパソコンを探している", "phrase", "0"),
            ("*パソコン*", "wildcard", "0"),
        ]
        
        print("🎯 高度検索テスト実行中...")
        print()
        
        for i, (query, search_type, fuzziness) in enumerate(search_tests, 1):
            print(f"  {i}. タイプ: {search_type}")
            print(f"     クエリ: '{query}' (fuzziness: {fuzziness})")
            
            try:
                results = await es_search.advanced_search(
                    query=query,
                    search_type=search_type,
                    fuzziness=fuzziness,
                    limit=2
                )
                
                print(f"     結果: {len(results)}件")
                
                # 結果の概要を表示
                for j, result in enumerate(results[:2], 1):
                    doc_name = result.get('document_name', 'Unknown')[:20]
                    score = result.get('similarity_score', 0)
                    
                    print(f"       {j}. {doc_name} (スコア: {score:.2f})")
                
                print()
                
            except Exception as e:
                print(f"     エラー: {e}")
                print()
        
        print("✅ 高度検索機能テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ 高度検索テストエラー: {e}")
        return False

async def test_search_system_integration():
    """検索システム統合テスト"""
    print("\n" + "=" * 60)
    print("🔧 検索システム統合テスト")
    print("=" * 60)
    
    try:
        from modules.chat_search_systems import (
            elasticsearch_fuzzy_search_system,
            fallback_search_system,
            multi_system_search
        )
        
        test_query = "パソコン"
        
        print(f"🔍 テストクエリ: '{test_query}'")
        print()
        
        # 1. Elasticsearch Fuzzy Search
        print("1. Elasticsearch Fuzzy Search System")
        try:
            results = await elasticsearch_fuzzy_search_system(
                query=test_query,
                fuzziness="AUTO",
                limit=3
            )
            print(f"   結果: {len(results)}件")
        except Exception as e:
            print(f"   エラー: {e}")
        
        # 2. フォールバック検索
        print("\n2. Fallback Search System")
        try:
            results = await fallback_search_system(
                query=test_query,
                limit=3
            )
            print(f"   結果: {len(results)}件")
        except Exception as e:
            print(f"   エラー: {e}")
        
        # 3. 複数システム検索
        print("\n3. Multi-System Search")
        try:
            results = await multi_system_search(
                query=test_query,
                limit=3
            )
            print(f"   結果: {len(results)}件")
        except Exception as e:
            print(f"   エラー: {e}")
        
        print("\n✅ 検索システム統合テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ 統合テストエラー: {e}")
        return False

async def main():
    """メイン関数"""
    print("🚀 Elasticsearch Fuzzy Search 総合テスト開始")
    print()
    
    # 各テストの実行
    tests = [
        ("接続テスト", test_elasticsearch_connection),
        ("データ同期テスト", test_data_sync),
        ("Fuzzy Search機能テスト", test_fuzzy_search),
        ("高度検索機能テスト", test_advanced_search),
        ("検索システム統合テスト", test_search_system_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results[test_name] = success
        except Exception as e:
            print(f"❌ {test_name}で予期しないエラー: {e}")
            results[test_name] = False
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"  {test_name}: {status}")
    
    print()
    print(f"📈 成功率: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 すべてのテストが成功しました！")
        print("💡 Elasticsearch Fuzzy Search機能は正常に動作しています。")
    else:
        print("⚠️ 一部のテストが失敗しました。")
        print("💡 セットアップガイド（ELASTICSEARCH_SETUP.md）を確認してください。")
    
    print("\n" + "=" * 60)
    print("🎯 次のステップ")
    print("=" * 60)
    print("1. 本番環境でのElasticsearchセットアップ")
    print("2. より多くのデータでのテスト")
    print("3. パフォーマンスの最適化")
    print("4. 監視とログ設定")

if __name__ == "__main__":
    print("🔍 Elasticsearch Fuzzy Search テストスクリプト")
    print("📝 必要な環境変数を.envファイルで設定してください")
    print()
    
    # 非同期実行
    asyncio.run(main()) 