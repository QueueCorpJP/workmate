"""
チャット設定とインポート管理
チャット機能で使用する外部モジュールの設定とインポートを管理します
"""
import json
import re
import uuid
import sys
from datetime import datetime
import logging
from typing import Dict, List, Any
# PostgreSQL関連のインポート
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException, Depends
from .company import DEFAULT_COMPANY_NAME
from .models import ChatMessage, ChatResponse
from .database import get_db, update_usage_count, get_usage_limits, SupabaseConnection
from .knowledge_base import knowledge_base, get_active_resources
from .auth import check_usage_limits
from .resource import get_active_resources_by_company_id, get_active_resources_content_by_ids, get_active_resource_names_by_company_id
from .company import get_company_by_id
import os
import asyncio
import google.generativeai as genai
from .config import setup_gemini
from .utils import safe_print, safe_safe_print

# 使用制限設定
USAGE_LIMIT_ENABLED = False  # 使用量制限を無効化（無限）
USAGE_LIMIT_PER_HOUR = 999999  # 実質無制限
CONTEXT_CACHING_ENABLED = True

def get_db_cursor():
    """データベースカーソルを取得する"""
    try:
        # Supabase接続を作成
        conn = SupabaseConnection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        return cursor
    except Exception as e:
        safe_print(f"データベースカーソル取得エラー: {e}")
        return None

# 🔍 直接検索システム（削除済み）
DIRECT_SEARCH_AVAILABLE = False
async def direct_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    safe_print("直接検索システムは削除されました")
    return []

# ⚡ 並列検索システム（削除済み）
PARALLEL_SEARCH_AVAILABLE = False
async def parallel_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    safe_print("並列検索システムは削除されました")
    return []

# 🎯 完璧な検索システム（削除済み）
PERFECT_SEARCH_AVAILABLE = False

# 🇯🇵 日本語特化型検索システム（削除済み）
ENHANCED_JAPANESE_SEARCH_AVAILABLE = False
async def enhanced_japanese_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    safe_print("日本語特化型検索システムは削除されました")
    return []

# 🎯 超高精度検索システムは削除されました
ULTRA_ACCURATE_AVAILABLE = False
try:
    pass
except ImportError as e:
    ULTRA_ACCURATE_AVAILABLE = False
    safe_print(f"⚠️ 超高精度検索システムが利用できません: {e}")

# 🚀 新しいリアルタイムRAGシステムのインポートを追加（フォールバック用）
try:
    from .realtime_rag import process_question_realtime, realtime_rag_available
    REALTIME_RAG_AVAILABLE = realtime_rag_available()
    if REALTIME_RAG_AVAILABLE:
        safe_print("✅ リアルタイムRAGシステムが利用可能です（フォールバック用）")
    else:
        safe_print("⚠️ リアルタイムRAGシステムの設定が不完全です")
except ImportError as e:
    REALTIME_RAG_AVAILABLE = False
    safe_print(f"⚠️ リアルタイムRAGシステムが利用できません: {e}")

# 新しいRAGシステムのインポートを追加（フォールバック用）
try:
    from .rag_enhanced import enhanced_rag, SearchResult
    RAG_ENHANCED_AVAILABLE = True
except ImportError:
    RAG_ENHANCED_AVAILABLE = False
    safe_print("⚠️ 強化RAGシステムが利用できないため、従来のRAGを使用します")

# 高速化RAGシステムのインポートを追加（正確性重視のため無効化）
try:
    from .rag_optimized import high_speed_rag
    SPEED_RAG_AVAILABLE = False  # 正確性重視のため強制的に無効化
    safe_print("⚠️ 高速化RAGシステムは正確性重視のため無効化されています")
except ImportError:
    SPEED_RAG_AVAILABLE = False
    safe_print("⚠️ 高速化RAGシステムが利用できません")

# ベクトル検索システムのインポートを追加（フォールバック用）
try:
    from .vector_search import get_vector_search_instance, vector_search_available
    VECTOR_SEARCH_AVAILABLE = vector_search_available()
    if VECTOR_SEARCH_AVAILABLE:
        safe_print("✅ ベクトル検索システムが利用可能です")
        _vector_search_instance = get_vector_search_instance()
        if hasattr(_vector_search_instance, 'search'):
            vector_search = _vector_search_instance.search
        else:
            async def vector_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
                return _vector_search_instance(query, limit)
    else:
        safe_print("⚠️ ベクトル検索システムの設定が不完全です")
        async def vector_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
            safe_print("ベクトル検索システムが利用できません")
            return []
except ImportError as e:
    VECTOR_SEARCH_AVAILABLE = False
    async def vector_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        safe_print("ベクトル検索システムが利用できません")
        return []
    safe_print(f"⚠️ ベクトル検索システムが利用できません: {e}")

# 🎯 直接ベクトル検索システム（削除済み）
DIRECT_VECTOR_SEARCH_AVAILABLE = False

# 並列ベクトル検索システム（削除済み）
PARALLEL_VECTOR_SEARCH_AVAILABLE = False

logger = logging.getLogger(__name__)

# Geminiモデル（グローバル変数）
model = None

def set_model(gemini_model):
    """Geminiモデルを設定する"""
    global model
    model = gemini_model