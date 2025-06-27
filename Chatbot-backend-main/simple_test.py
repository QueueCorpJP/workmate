#!/usr/bin/env python3
import sys
sys.path.append('.')
from modules.parallel_vector_search import ParallelVectorSearchSystem
import logging
logging.basicConfig(level=logging.INFO)

print('🔧 並列ベクトル検索システム初期化テスト...')
try:
    search_system = ParallelVectorSearchSystem()
    print('✅ 初期化成功')
    print(f'   モデル: {search_system.model}')
    print(f'   Vertex AI使用: {search_system.use_vertex_ai}')
    has_api_key = hasattr(search_system, 'api_key') and search_system.api_key
    print(f'   API Key: {"設定済み" if has_api_key else "なし（Vertex AI使用）"}')
    print('🎉 api_key エラーは修正されました')
except Exception as e:
    print(f'❌ エラー: {e}')
    if 'api_key' in str(e):
        print('⚠️ api_key エラーが依然として発生しています')