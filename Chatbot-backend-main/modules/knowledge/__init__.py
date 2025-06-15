"""
知識ベースモジュール
知識ベースの管理と処理を行います
"""

from .base import KnowledgeBase, knowledge_base, get_active_resources, get_knowledge_base_info
from .api import process_file, process_url, toggle_resource_active, get_uploaded_resources
from .image import process_image_file, is_image_file
from .csv_processor import process_csv_file, is_csv_file, check_csv_dependencies
from .word_processor import process_word_file, is_word_file, check_word_dependencies
from .file_detector import detect_file_type

__all__ = [
    'KnowledgeBase',
    'knowledge_base',
    'get_active_resources',
    'get_knowledge_base_info',
    'process_file',
    'process_url',
    'toggle_resource_active',
    'get_uploaded_resources',
    'process_image_file',
    'is_image_file',
    'process_csv_file',
    'is_csv_file',
    'check_csv_dependencies',
    'process_word_file',
    'is_word_file',
    'check_word_dependencies',
    'detect_file_type',
] 