#!/usr/bin/env python3
"""
並列ベクトル検索システムのAPI キー修正テスト
"""

import sys
import os
import logging

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.vector_search_parallel import get_parallel_vector_search_instance

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_parallel_vector_search_initialization():
    """並列ベクトル検索システムの初期化テスト"""
    logger.info("🚀 並列ベクトル検索システム初期化テスト開始")
    
    try:
        # インスタンス取得テスト
        search_system = get_parallel_vector_search_instance()
        
        if search_system is None:
            logger.error("❌ 並列ベクトル検索システムのインスタンス取得に失敗")
            return False
        
        logger.info("✅ 並列ベクトル検索システムのインスタンス取得成功")
        
        # API キーの確認
        if hasattr(search_system, 'api_key') and search_system.api_key:
            logger.info(f"✅ API キーが正常に設定されています: {search_system.api_key[:10]}...")
        else:
            logger.error("❌ API キーが設定されていません")
            return False
        
        # モデル設定の確認
        if hasattr(search_system, 'model'):
            logger.info(f"✅ モデル設定: {search_system.model}")
        
        # データベースURL設定の確認
        if hasattr(search_system, 'db_url') and search_system.db_url:
            logger.info("✅ データベースURL設定済み")
        else:
            logger.error("❌ データベースURLが設定されていません")
            return False
        
        logger.info("🎉 並列ベクトル検索システム初期化テスト完了")
        return True
        
    except Exception as e:
        logger.error(f"❌ 並列ベクトル検索システム初期化エラー: {e}")
        return False

def test_query_expansion():
    """クエリ拡張機能のテスト"""
    logger.info("🔍 クエリ拡張機能テスト開始")
    
    try:
        search_system = get_parallel_vector_search_instance()
        if search_system is None:
            logger.error("❌ 検索システムが初期化されていません")
            return False
        
        # テストクエリ
        test_query = "料金について教えて"
        
        # クエリ拡張テスト
        expanded_queries = search_system.expand_query_strategies(test_query)
        
        logger.info(f"✅ 元クエリ: {test_query}")
        logger.info(f"✅ 拡張クエリ数: {len(expanded_queries)}")
        
        for i, query in enumerate(expanded_queries):
            logger.info(f"  {i+1}. {query}")
        
        logger.info("🎉 クエリ拡張機能テスト完了")
        return True
        
    except Exception as e:
        logger.error(f"❌ クエリ拡張機能テストエラー: {e}")
        return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("並列ベクトル検索システム API キー修正テスト")
    logger.info("=" * 60)
    
    # テスト実行
    test_results = []
    
    # 1. 初期化テスト
    test_results.append(("初期化テスト", test_parallel_vector_search_initialization()))
    
    # 2. クエリ拡張テスト
    test_results.append(("クエリ拡張テスト", test_query_expansion()))
    
    # 結果サマリー
    logger.info("=" * 60)
    logger.info("テスト結果サマリー")
    logger.info("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n総合結果: {passed}/{total} テスト通過")
    
    if passed == total:
        logger.info("🎉 全てのテストが成功しました！")
        sys.exit(0)
    else:
        logger.error("❌ 一部のテストが失敗しました")
        sys.exit(1)