#!/usr/bin/env python3
"""
並列ベクトル検索システムの修正テスト
api_key属性エラーの修正を検証
"""

import logging
import os
import sys
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.parallel_vector_search import get_parallel_vector_search_instance_sync, ParallelVectorSearchSystem

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_parallel_vector_search_initialization():
    """並列ベクトル検索システム初期化テスト"""
    print("🔧 並列ベクトル検索システム初期化テスト...")
    
    # 環境変数の読み込み
    load_dotenv()
    
    try:
        # 直接インスタンス化テスト
        search_system = ParallelVectorSearchSystem()
        
        print("✅ 並列ベクトル検索システム直接初期化成功")
        print(f"   モデル: {search_system.model}")
        print(f"   Vertex AI使用: {search_system.use_vertex_ai}")
        print(f"   API Key設定: {'あり' if hasattr(search_system, 'api_key') and search_system.api_key else 'なし（Vertex AI使用）'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 直接初期化エラー: {e}")
        
        # api_key エラーをチェック
        if "api_key" in str(e):
            print("⚠️  api_key 属性エラーが依然として発生しています")
            return False
        
        return False

def test_parallel_vector_search_singleton():
    """シングルトンインスタンス取得テスト"""
    print("\n🔧 シングルトンインスタンス取得テスト...")
    
    try:
        # シングルトンインスタンス取得テスト
        search_system = get_parallel_vector_search_instance_sync()
        
        if search_system:
            print("✅ シングルトンインスタンス取得成功")
            print(f"   モデル: {search_system.model}")
            print(f"   Vertex AI使用: {search_system.use_vertex_ai}")
            return True
        else:
            print("❌ シングルトンインスタンス取得失敗")
            return False
            
    except Exception as e:
        print(f"❌ シングルトンインスタンス取得エラー: {e}")
        
        # api_key エラーをチェック
        if "api_key" in str(e):
            print("⚠️  api_key 属性エラーが依然として発生しています")
            return False
        
        return False

def test_parallel_vector_search_functionality():
    """並列ベクトル検索機能テスト"""
    print("\n🔍 並列ベクトル検索機能テスト...")
    
    try:
        search_system = get_parallel_vector_search_instance_sync()
        
        if not search_system:
            print("❌ 検索システムインスタンスが取得できません")
            return False
        
        # 簡単な検索テスト
        test_query = "テスト質問"
        print(f"テスト質問: {test_query}")
        
        result = search_system.parallel_comprehensive_search_sync(
            query=test_query,
            company_id=None,  # テスト用
            max_results=3
        )
        
        print(f"✅ 検索結果: {len(result)}文字")
        if result:
            print(f"   結果プレビュー: {result[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 検索機能テストエラー: {e}")
        
        # api_key エラーをチェック
        if "api_key" in str(e):
            print("⚠️  api_key 属性エラーが依然として発生しています")
            return False
        
        return False

def main():
    """メイン実行関数"""
    print("=" * 60)
    print("🧪 並列ベクトル検索システム修正テスト")
    print("=" * 60)
    
    # 必要な環境変数をチェック
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 必要な環境変数が設定されていません: {missing_vars}")
        return
    
    # テスト実行
    test_results = []
    
    # 1. 初期化テスト
    init_success = test_parallel_vector_search_initialization()
    test_results.append(("初期化テスト", init_success))
    
    # 2. シングルトンテスト
    singleton_success = test_parallel_vector_search_singleton()
    test_results.append(("シングルトンテスト", singleton_success))
    
    # 3. 機能テスト（初期化が成功した場合のみ）
    if init_success and singleton_success:
        functionality_success = test_parallel_vector_search_functionality()
        test_results.append(("機能テスト", functionality_success))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    all_success = True
    for test_name, success in test_results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{test_name}: {status}")
        if not success:
            all_success = False
    
    print("\n" + "=" * 60)
    if all_success:
        print("🎉 全テスト成功: api_key エラーは修正されました")
    else:
        print("❌ テスト失敗: 修正が必要です")
    print("=" * 60)

if __name__ == "__main__":
    main()