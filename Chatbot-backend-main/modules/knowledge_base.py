"""
知識ベースモジュール
知識ベースの管理と処理を行います
"""

# データ型変換ユーティリティ関数をインポート
from .database import ensure_string

# 新しいモジュール構造からインポート
from .knowledge import (
    KnowledgeBase,
    knowledge_base,
    get_active_resources,
    get_knowledge_base_info,
    process_file,
    process_url,
    toggle_resource_active,
    get_uploaded_resources
)

# 後方互換性のために元の関数をエクスポート
__all__ = [
    'KnowledgeBase',
    'knowledge_base',
    'get_active_resources',
    'get_knowledge_base_info',
    'process_file',
    'process_url',
    'toggle_resource_active',
    'get_uploaded_resources'
] 