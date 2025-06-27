#!/usr/bin/env python3
"""
並列ベクトル検索システムのAPI key属性修正の検証テスト
"""

import sys
import os
import logging

# プロジェクトルートをパスに追加
sys.path.append('.')

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_parallel_vector_search_api_key_attribute():
    """並列ベクトル検索システムのapi_key属性テスト"""
    logger.info("🧪 並列ベクトル検索システムのapi_key属性テスト開始")
    
    try:
        # モジュールインポート
        from modules.vector_search_parallel import ParallelVectorSearchSystem
        logger.info("✅ モジュールインポート成功")
        
        # インスタンス作成
        search_system = ParallelVectorSearchSystem()
        logger.info("✅ インスタンス作成成功")
        
        # api_key属性の存在確認
        if hasattr(search_system, 'api_key'):
            logger.info(f"✅ api_key属性が存在します: {type(search_system.api_key)}")
            
            # Vertex AI使用時はapi_keyがNone、Gemini API使用時は文字列
            if search_system.use_vertex_ai:
                if search_system.api_key is None:
                    logger.info("✅ Vertex AI使用時: api_key = None (正常)")
                else:
                    logger.warning(f"⚠️ Vertex AI使用時: api_key = {search_system.api_key} (予期しない値)")
            else:
                if isinstance(search_system.api_key, str) and search_system.api_key:
                    logger.info("✅ Gemini API使用時: api_keyが設定されています")
                else:
                    logger.error("❌ Gemini API使用時: api_keyが設定されていません")
                    return False
        else:
            logger.error("❌ api_key属性が存在しません")
            return False
        
        # その他の重要な属性の確認
        required_attributes = ['use_vertex_ai', 'model_name', 'db_url', 'embedding_method']
        for attr in required_attributes:
            if hasattr(search_system, attr):
                logger.info(f"✅ {attr}属性が存在: {getattr(search_system, attr)}")
            else:
                logger.error(f"❌ {attr}属性が存在しません")
                return False
        
        logger.info("✅ 並列ベクトル検索システムのapi_key属性テスト成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 並列ベクトル検索システムのapi_key属性テスト失敗: {e}")
        return False

def test_singleton_instance_api_key():
    """シングルトンインスタンスのapi_key属性テスト"""
    logger.info("🧪 シングルトンインスタンスのapi_key属性テスト開始")
    
    try:
        from modules.vector_search_parallel import get_parallel_vector_search_instance
        
        # インスタンス取得
        search_system = get_parallel_vector_search_instance()
        
        if search_system is None:
            logger.error("❌ シングルトンインスタンスの取得に失敗")
            return False
        
        # api_key属性の確認
        if hasattr(search_system, 'api_key'):
            logger.info(f"✅ シングルトンインスタンスにapi_key属性が存在: {type(search_system.api_key)}")
            return True
        else:
            logger.error("❌ シングルトンインスタンスにapi_key属性が存在しません")
            return False
            
    except Exception as e:
        logger.error(f"❌ シングルトンインスタンスのapi_key属性テスト失敗: {e}")
        return False

def test_embedding_generation():
    """エンベディング生成テスト（api_key属性使用確認）"""
    logger.info("🧪 エンベディング生成テスト開始")
    
    try:
        from modules.vector_search_parallel import get_parallel_vector_search_instance
        import asyncio
        
        # インスタンス取得
        search_system = get_parallel_vector_search_instance()
        
        if search_system is None:
            logger.error("❌ インスタンスの取得に失敗")
            return False
        
        # 簡単なクエリでエンベディング生成テスト
        async def test_embedding():
            try:
                queries = ["テスト", "料金"]
                embeddings = await search_system.generate_query_embeddings_parallel(queries)
                
                if embeddings and len(embeddings) > 0:
                    logger.info(f"✅ エンベディング生成成功: {len(embeddings)}個")
                    return True
                else:
                    logger.warning("⚠️ エンベディング生成結果が空です")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ エンベディング生成エラー: {e}")
                return False
        
        # 非同期実行
        result = asyncio.run(test_embedding())
        return result
        
    except Exception as e:
        logger.error(f"❌ エンベディング生成テスト失敗: {e}")
        return False

def main():
    """メイン実行関数"""
    logger.info("🚀 並列ベクトル検索システムAPI key修正検証テスト開始")
    
    test_results = []
    
    # 1. 基本的なapi_key属性テスト
    api_key_test = test_parallel_vector_search_api_key_attribute()
    test_results.append(("API key属性テスト", api_key_test))
    
    # 2. シングルトンインスタンスのapi_key属性テスト
    singleton_test = test_singleton_instance_api_key()
    test_results.append(("シングルトンAPI keyテスト", singleton_test))
    
    # 3. エンベディング生成テスト（api_key属性が正常に動作するか）
    if api_key_test and singleton_test:
        embedding_test = test_embedding_generation()
        test_results.append(("エンベディング生成テスト", embedding_test))
    else:
        logger.warning("⚠️ 前提テストが失敗したため、エンベディング生成テストをスキップ")
        test_results.append(("エンベディング生成テスト", False))
    
    # 結果サマリー
    logger.info("\n" + "="*60)
    logger.info("📊 テスト結果サマリー")
    logger.info("="*60)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 成功" if result else "❌ 失敗"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    logger.info("="*60)
    if all_passed:
        logger.info("🎉 全てのテストが成功しました！API key属性の修正が正常に動作しています。")
    else:
        logger.error("💥 一部のテストが失敗しました。修正が必要です。")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)