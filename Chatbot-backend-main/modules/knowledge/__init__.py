"""
知識ベースモジュール
知識ベースの管理と処理を行います
"""

from .base import KnowledgeBase, knowledge_base, get_active_resources, get_knowledge_base_info
from .api import process_file, process_url, toggle_resource_active, get_uploaded_resources

__all__ = [
    'KnowledgeBase',
    'knowledge_base',
    'get_active_resources',
    'get_knowledge_base_info',
    'process_file',
    'process_url',
    'toggle_resource_active',
    'get_uploaded_resources',
] 