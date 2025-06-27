#!/usr/bin/env python3
"""
最終検証テスト - 並列ベクトル検索システムの動作確認
"""

import sys
import asyncio
import logging

sys.path.append('.')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_search():
    try:
        from modules.vector_search_parallel import get_parallel_vector_search_instance
        
        search_system = get_parallel_vector_search_instance()
        if search_system:
            print('✅ 並列ベクトル検索システム初期化成功')
            print(f'📋 使用モデル: {search_system.model_name}')
            print(f'🔧 埋め込み方法: {search_system.embedding_method}')
            print(f'🔑 API Key: {type(search_system.api_key)}')
            
            # 簡単な検索テスト
            result = await search_system.parallel_comprehensive_search(
                'WALLIOR PC 再レンタル料金 早見表', 
                '77acc2e2-ce67-458d-bd38-7af0476b297a', 
                5
            )
            print(f'🔍 検索結果: {len(result)}文字')
            return True
        else:
            print('❌ 並列ベクトル検索システム初期化失敗')
            return False
            
    except Exception as e:
        print(f'❌ エラー: {e}')
        return False

if __name__ == "__main__":
    success = asyncio.run(test_search())
    print(f'最終結果: {"成功" if success else "失敗"}')