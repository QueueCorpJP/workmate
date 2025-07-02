"""
チャットモジュール - メインエントリーポイント
リファクタリングされたチャット機能の統合インターフェース
"""

# メイン処理関数をエクスポート
from .chat_processing import (
    process_chat_message,
    get_usage_stats,
    check_usage_limit,
    record_usage
)

# RAG検索機能をエクスポート
from .chat_rag import (
    rag_search,
    enhanced_rag_search,
    parallel_rag_search,
    adaptive_rag_search,
    contextual_rag_search,
    format_search_results
)

# チャンキング機能をエクスポート
from .chat_chunking import (
    process_chunked_chat,
    process_knowledge_base_chunking,
    store_chunked_knowledge,
    retrieve_chunked_knowledge,
    calculate_optimal_chunk_size,
    analyze_chunk_quality
)

# 会話検出機能をエクスポート
from .chat_conversation import (
    is_casual_conversation,
    detect_conversation_intent,
    generate_casual_response,
    should_use_rag_search,
    extract_search_query
)

# 検索システムをエクスポート
from .chat_search_systems import (
    smart_search_system,
    multi_system_search,
    fallback_search_system,
    database_search_fallback
)

# 追加機能をエクスポート
from .chat_additional import (
    rag_search_with_fallback,
    semantic_similarity_search,
    multi_modal_rag_search,
    hybrid_search_strategy,
    adaptive_search_with_learning
)

# ユーティリティ関数をエクスポート
from .chat_utils import (
    chunk_knowledge_base,
    expand_query
)

# 設定とモデルをエクスポート
from .chat_config import (
    model,
    set_model,
    safe_print,
    get_db_cursor
)

# バージョン情報
__version__ = "2.0.0"
__author__ = "Chatbot Team"
__description__ = "Refactored chat module with modular architecture"

# 主要な関数のエイリアス（後方互換性のため）
chat = process_chat_message
chunked_chat = process_chunked_chat

# モジュールの公開API
__all__ = [
    # メイン処理
    'process_chat_message',
    'chat',  # エイリアス
    'get_usage_stats',
    'check_usage_limit',
    'record_usage',
    
    # RAG検索
    'rag_search',
    'enhanced_rag_search',
    'parallel_rag_search',
    'adaptive_rag_search',
    'contextual_rag_search',
    'format_search_results',
    
    # チャンキング
    'process_chunked_chat',
    'chunked_chat',  # エイリアス
    'process_knowledge_base_chunking',
    'store_chunked_knowledge',
    'retrieve_chunked_knowledge',
    'calculate_optimal_chunk_size',
    'analyze_chunk_quality',
    
    # 会話検出
    'is_casual_conversation',
    'detect_conversation_intent',
    'generate_casual_response',
    'should_use_rag_search',
    'extract_search_query',
    
    # 検索システム
    'smart_search_system',
    'multi_system_search',
    'fallback_search_system',
    'database_search_fallback',
    
    # 追加機能
    'rag_search_with_fallback',
    'semantic_similarity_search',
    'multi_modal_rag_search',
    'hybrid_search_strategy',
    'adaptive_search_with_learning',
    
    # ユーティリティ
    'chunk_knowledge_base',
    'expand_query',
    
    # 設定
    'model',
    'set_model',
    'safe_print',
    'get_db_cursor',
]

def get_module_info():
    """
    モジュール情報を取得
    
    Returns:
        モジュール情報の辞書
    """
    return {
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'submodules': [
            'chat_config',
            'chat_utils', 
            'chat_search_systems',
            'chat_rag',
            'chat_conversation',
            'chat_processing',
            'chat_chunking',
            'chat_additional'
        ],
        'main_functions': [
            'process_chat_message',
            'process_chunked_chat',
            'rag_search',
            'enhanced_rag_search'
        ]
    }

def health_check():
    """
    モジュールのヘルスチェック
    
    Returns:
        ヘルスチェック結果
    """
    try:
        from .chat_config import model, get_db_cursor
        
        health_status = {
            'status': 'healthy',
            'model_available': model is not None,
            'database_available': get_db_cursor() is not None,
            'modules_loaded': True,
            'timestamp': None
        }
        
        # タイムスタンプを追加
        import datetime
        health_status['timestamp'] = datetime.datetime.now().isoformat()
        
        return health_status

    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.datetime.now().isoformat()
        }

# モジュール初期化時のログ出力
try:
    safe_print(f"Chat module v{__version__} loaded successfully")
    safe_print(f"Available functions: {len(__all__)} public APIs")
except:
    print(f"Chat module v{__version__} loaded successfully")