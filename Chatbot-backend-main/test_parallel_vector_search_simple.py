#!/usr/bin/env python3
"""
並列ベクトル検索システムの簡単なテスト
"""

import sys
import os
import logging

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_import_and_initialization():
    """インポートと初期化のテスト"""
    logger.info("🚀 並列ベクトル検索システム インポート・初期化テスト開始")
    
    try:
        # インポートテスト
        from modules.vector_search_parallel import get_parallel_vector_search_instance
        logger.info("✅ モジュールインポート成功")
        
        # インスタンス取得テスト
        search_system = get_parallel_vector_search_instance()
        
        if search_system is None:
            logger.error("❌ 並列ベクトル検索システムのインスタンス取得に失敗")
            return False
        
        logger.info("✅ 並列ベクトル検索システムのインスタンス取得成功")
        
        # 属性確認
        if hasattr(search_system, 'embedding_method'):
            logger.info(f"✅ 埋め込み方法: {search_system.embedding_method}")
        
        if hasattr(search_system, 'model_name'):
            logger.info(f"✅ モデル名: {search_system.model_name}")
        
        if hasattr(search_system, 'use_vertex_ai'):
            logger.info(f"✅ Vertex AI使用: {search_system.use_vertex_ai}")
        
        logger.info("🎉 並列ベクトル検索システム初期化テスト完了")
        return True
        
    except Exception as e:
        logger.error(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("並列ベクトル検索システム 簡単テスト")
    logger.info("=" * 60)
    
    success = test_import_and_initialization()
    
    if success:
        logger.info("🎉 テスト成功！")
        sys.exit(0)
    else:
        logger.error("❌ テスト失敗")
        sys.exit(1)