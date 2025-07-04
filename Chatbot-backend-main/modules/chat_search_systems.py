"""
チャット検索システム
各種検索システムの実装を管理します
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from .chat_config import (
    safe_print, HTTPException, get_db_cursor,
    DIRECT_SEARCH_AVAILABLE, PARALLEL_SEARCH_AVAILABLE, 
    ENHANCED_JAPANESE_SEARCH_AVAILABLE, VECTOR_SEARCH_AVAILABLE,
    direct_search, parallel_search, enhanced_japanese_search, vector_search
)

async def direct_search_system(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    直接検索システム
    """
    if not DIRECT_SEARCH_AVAILABLE:
        safe_print("Direct search is not available")
        return []
    
    try:
        results = await direct_search(query, limit)
        safe_print(f"Direct search returned {len(results)} results")
        return results
    except Exception as e:
        safe_print(f"Error in direct search: {e}")
        return []

async def parallel_search_system(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    並列検索システム
    """
    if not PARALLEL_SEARCH_AVAILABLE:
        safe_print("Parallel search is not available")
        return []
    
    try:
        results = await parallel_search(query, limit)
        safe_print(f"Parallel search returned {len(results)} results")
        return results
    except Exception as e:
        safe_print(f"Error in parallel search: {e}")
        return []

async def enhanced_japanese_search_system(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    拡張日本語検索システム
    """
    if not ENHANCED_JAPANESE_SEARCH_AVAILABLE:
        safe_print("Enhanced Japanese search is not available")
        return []
    
    try:
        results = await enhanced_japanese_search(query, limit)
        safe_print(f"Enhanced Japanese search returned {len(results)} results")
        return results
    except Exception as e:
        safe_print(f"Error in enhanced Japanese search: {e}")
        return []

async def vector_search_system(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    ベクトル検索システム
    """
    if not VECTOR_SEARCH_AVAILABLE:
        safe_print("Vector search is not available")
        return []
    
    try:
        results = await vector_search(query, limit)
        safe_print(f"Vector search returned {len(results)} results")
        return results
    except Exception as e:
        safe_print(f"Error in vector search: {e}")
        return []

async def fallback_search_system(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    フォールバック検索システム - 複数の検索システムを順次試行
    """
    search_systems = [
        ("Enhanced Japanese Search", enhanced_japanese_search_system),
        ("Vector Search", vector_search_system),
        ("Parallel Search", parallel_search_system),
        ("Direct Search", direct_search_system),
        ("Database Fallback Search", database_search_fallback),
    ]
    
    for system_name, search_func in search_systems:
        try:
            safe_print(f"Trying {system_name}...")
            results = await search_func(query, limit)
            if results:
                safe_print(f"{system_name} succeeded with {len(results)} results")
                return results
            else:
                safe_print(f"{system_name} returned no results")
        except Exception as e:
            safe_print(f"{system_name} failed: {e}")
            continue
    
    safe_print("All search systems failed")
    return []

async def multi_system_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    複数システム検索 - 複数の検索システムを並列実行して結果をマージ
    """
    search_tasks = []
    
    if ENHANCED_JAPANESE_SEARCH_AVAILABLE:
        search_tasks.append(enhanced_japanese_search_system(query, limit))
    if VECTOR_SEARCH_AVAILABLE:
        search_tasks.append(vector_search_system(query, limit))
    if PARALLEL_SEARCH_AVAILABLE:
        search_tasks.append(parallel_search_system(query, limit))
    if DIRECT_SEARCH_AVAILABLE:
        search_tasks.append(direct_search_system(query, limit))
    
    if not search_tasks:
        safe_print("No search systems available")
        return []
    
    try:
        # 並列実行
        results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # 結果をマージ（重複除去）
        merged_results = []
        seen_ids = set()
        
        for results in results_list:
            if isinstance(results, Exception):
                safe_print(f"Search system error: {results}")
                continue
            
            if isinstance(results, list):
                for result in results:
                    if isinstance(result, dict) and 'id' in result:
                        if result['id'] not in seen_ids:
                            seen_ids.add(result['id'])
                            merged_results.append(result)
        
        # スコア順でソート（スコアがある場合）
        merged_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # 制限数まで切り詰め
        final_results = merged_results[:limit]
        safe_print(f"Multi-system search returned {len(final_results)} unique results")
        
        return final_results
        
    except Exception as e:
        safe_print(f"Error in multi-system search: {e}")
        return await fallback_search_system(query, limit)

async def database_search_fallback(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    データベース直接検索フォールバック（バリエーション対応）
    """
    try:
        cursor = get_db_cursor()
        if not cursor:
            safe_print("Database cursor not available")
            return []
        
        # 🔄 バリエーション生成を組み込み
        try:
            from .question_variants_generator import generate_question_variants
            safe_print(f"Generating query variants for: {query}")
            variants_result = await generate_question_variants(query)
            search_terms = variants_result.all_variants
            safe_print(f"Generated {len(search_terms)} query variants")
        except Exception as e:
            safe_print(f"Variant generation failed, using original query: {e}")
            search_terms = [query]
        
        # 最大10個のバリエーションに制限（パフォーマンス考慮）
        search_terms = search_terms[:10]
        
        if not search_terms:
            search_terms = [query]
        
        # 🎯 OR条件でSQL検索を構築
        where_conditions = []
        params = []
        
        for term in search_terms:
            if term and term.strip():
                where_conditions.append("c.content ILIKE %s")
                params.append(f"%{term.strip()}%")
        
        if not where_conditions:
            where_conditions.append("c.content ILIKE %s")
            params.append(f"%{query}%")
        
        # OR条件を結合
        or_conditions = " OR ".join(where_conditions)
        
        # スコアリングを改善（複数条件マッチでスコア向上）
        score_cases = []
        for i, term in enumerate(search_terms):
            if term and term.strip():
                score_cases.append(f"CASE WHEN c.content ILIKE %s THEN 1.0 ELSE 0 END")
                params.append(f"%{term.strip()}%")
        
        if not score_cases:
            score_cases.append(f"CASE WHEN c.content ILIKE %s THEN 1.0 ELSE 0 END")
            params.append(f"%{query}%")
        
        score_calculation = " + ".join(score_cases)
        
        # 検索クエリ構築
        search_query = f"""
        SELECT c.id, ds.name as title, c.content, '' as url, 
               ({score_calculation}) as rank
        FROM chunks c
        LEFT JOIN document_sources ds ON c.doc_id = ds.id
        WHERE c.content IS NOT NULL 
          AND LENGTH(c.content) > 10
          AND ({or_conditions})
        ORDER BY rank DESC, LENGTH(c.content) DESC
        LIMIT %s
        """
        
        # LIMIT パラメータを追加
        params.append(limit)
        
        safe_print(f"Executing SQL search with {len(search_terms)} variants: {search_terms}")
        cursor.execute(search_query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            # document_sources.nameフィールドのみを使用してソース情報を設定
            title = row[1] if row[1] else 'Unknown'
            results.append({
                'id': row[0],
                'title': title,
                'content': row[2],
                'url': row[3],
                'score': float(row[4]) if row[4] else 0.0
            })
        
        safe_print(f"Database fallback search with variants returned {len(results)} results")
        return results
        
    except Exception as e:
        safe_print(f"Database fallback search error: {e}")
        return []

async def smart_search_system(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    スマート検索システム - クエリの特性に応じて最適な検索システムを選択
    """
    safe_print(f"Starting smart search for query: {query}")

    # 日本語が含まれているかチェック
    has_japanese = any('\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FAF' for char in query)
    
    # クエリの長さをチェック
    is_long_query = len(query) > 50
    
    # 技術的なキーワードが含まれているかチェック
    technical_keywords = ['API', 'SQL', 'Python', 'JavaScript', 'HTML', 'CSS', 'JSON', 'XML', 'HTTP', 'HTTPS']
    has_technical_terms = any(keyword.lower() in query.lower() for keyword in technical_keywords)
    
    safe_print(f"Query analysis: Japanese={has_japanese}, Long={is_long_query}, Technical={has_technical_terms}")
    
    # 最適な検索システムを選択
    if has_japanese and ENHANCED_JAPANESE_SEARCH_AVAILABLE:
        safe_print("Using Enhanced Japanese Search for Japanese query")
        return await enhanced_japanese_search_system(query, limit)
    elif is_long_query and VECTOR_SEARCH_AVAILABLE:
        safe_print("Using Vector Search for long query")
        return await vector_search_system(query, limit)
    elif has_technical_terms and PARALLEL_SEARCH_AVAILABLE:
        safe_print("Using Parallel Search for technical query")
        return await parallel_search_system(query, limit)
    else:
        safe_print("Using multi-system search as default")
        return await multi_system_search(query, limit)