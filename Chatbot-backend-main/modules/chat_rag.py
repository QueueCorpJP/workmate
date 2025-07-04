"""
RAG (Retrieval-Augmented Generation) 検索実装
RAG検索の各種バリエーションを管理します
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from .chat_config import safe_print, HTTPException, get_db_cursor, model
from .chat_search_systems import (
    smart_search_system, multi_system_search, fallback_search_system,
    database_search_fallback
)
from .chat_utils import expand_query

async def rag_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    基本的なRAG検索
    """
    try:
        safe_print(f"Starting RAG search for query: {query}")
        
        # 🎯 まずSQL検索を試行（エンベディングなしでも動作）
        safe_print("Trying SQL database search first...")
        results = await database_search_fallback(query, limit)
        
        if results:
            safe_print(f"SQL search succeeded with {len(results)} results")
            return results
        
        safe_print("SQL search returned no results, trying smart search system")
        # スマート検索システムを使用
        results = await smart_search_system(query, limit)
        
        if not results:
            safe_print("Smart search returned no results, trying fallback")
            results = await fallback_search_system(query, limit)
        
        safe_print(f"RAG search completed with {len(results)} results")
        return results
        
    except Exception as e:
        safe_print(f"Error in RAG search: {e}")
        raise HTTPException(status_code=500, detail=f"RAG search failed: {str(e)}")

async def enhanced_rag_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    拡張RAG検索 - クエリ拡張と複数検索戦略を組み合わせ
    """
    try:
        safe_print(f"Starting enhanced RAG search for query: {query}")
        
        # 🎯 まずSQL検索を試行（エンベディングなしでも動作）
        safe_print("Trying SQL database search first...")
        sql_results = await database_search_fallback(query, limit)
        
        if sql_results:
            safe_print(f"SQL search succeeded with {len(sql_results)} results")
            return sql_results
        
        safe_print("SQL search returned no results, trying enhanced vector search")
        
        # クエリ拡張
        expanded_query = expand_query(query)
        safe_print(f"Expanded query: {expanded_query}")
        
        # 元のクエリと拡張クエリの両方で検索
        original_results = await smart_search_system(query, limit)
        expanded_results = await smart_search_system(expanded_query, limit) if expanded_query != query else []
        
        # 結果をマージして重複除去
        merged_results = []
        seen_ids = set()
        
        # 元のクエリの結果を優先
        for result in original_results:
            if result.get('id') not in seen_ids:
                seen_ids.add(result['id'])
                merged_results.append(result)
        
        # 拡張クエリの結果を追加
        for result in expanded_results:
            if result.get('id') not in seen_ids:
                seen_ids.add(result['id'])
                # スコアを少し下げる（元のクエリの結果を優先）
                if 'score' in result:
                    result['score'] *= 0.9
                merged_results.append(result)
        
        # スコア順でソート
        merged_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # 制限数まで切り詰め
        final_results = merged_results[:limit]
        
        safe_print(f"Enhanced RAG search completed with {len(final_results)} results")
        return final_results
        
    except Exception as e:
        safe_print(f"Error in enhanced RAG search: {e}")
        # フォールバックとして基本RAG検索を実行
        return await rag_search(query, limit)

async def parallel_rag_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    並列RAG検索 - 複数の検索戦略を並列実行
    """
    try:
        safe_print(f"Starting parallel RAG search for query: {query}")
        
        # 🎯 まずSQL検索を試行（エンベディングなしでも動作）
        safe_print("Trying SQL database search first...")
        sql_results = await database_search_fallback(query, limit)
        
        if sql_results:
            safe_print(f"SQL search succeeded with {len(sql_results)} results")
            return sql_results
        
        safe_print("SQL search returned no results, trying parallel vector search")
        
        # 複数の検索戦略を並列実行
        search_tasks = [
            smart_search_system(query, limit),
            multi_system_search(query, limit),
        ]
        
        # クエリ拡張版も追加
        expanded_query = expand_query(query)
        if expanded_query != query:
            search_tasks.append(smart_search_system(expanded_query, limit))
        
        # 並列実行
        results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # 結果をマージ
        merged_results = []
        seen_ids = set()
        
        for i, results in enumerate(results_list):
            if isinstance(results, Exception):
                safe_print(f"Search task {i} failed: {results}")
                continue
            
            if isinstance(results, list):
                for result in results:
                    if isinstance(result, dict) and 'id' in result:
                        if result['id'] not in seen_ids:
                            seen_ids.add(result['id'])
                            # 検索戦略に応じてスコア調整
                            if i == 2 and 'score' in result:  # 拡張クエリの結果
                                result['score'] *= 0.9
                            merged_results.append(result)
        
        # スコア順でソート
        merged_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # 制限数まで切り詰め
        final_results = merged_results[:limit]
        
        safe_print(f"Parallel RAG search completed with {len(final_results)} results")
        return final_results
        
    except Exception as e:
        safe_print(f"Error in parallel RAG search: {e}")
        # フォールバックとして基本RAG検索を実行
        return await rag_search(query, limit)

async def adaptive_rag_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    適応的RAG検索 - クエリの特性に応じて検索戦略を動的に選択
    """
    try:
        safe_print(f"Starting adaptive RAG search for query: {query}")
        
        # クエリの特性を分析
        query_length = len(query)
        has_japanese = any('\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FAF' for char in query)
        word_count = len(query.split())
        
        safe_print(f"Query analysis: length={query_length}, japanese={has_japanese}, words={word_count}")
        
        # 特性に応じて検索戦略を選択
        if query_length > 100 or word_count > 15:
            # 長いクエリには並列検索
            safe_print("Using parallel RAG search for long query")
            return await parallel_rag_search(query, limit)
        elif has_japanese and word_count <= 5:
            # 短い日本語クエリには拡張検索
            safe_print("Using enhanced RAG search for short Japanese query")
            return await enhanced_rag_search(query, limit)
        else:
            # その他は基本検索
            safe_print("Using basic RAG search")
            return await rag_search(query, limit)
            
    except Exception as e:
        safe_print(f"Error in adaptive RAG search: {e}")
        # フォールバックとして基本RAG検索を実行
        return await rag_search(query, limit)

async def contextual_rag_search(query: str, context: str = "", limit: int = 10) -> List[Dict[str, Any]]:
    """
    コンテキスト考慮RAG検索 - 会話履歴を考慮した検索
    """
    try:
        safe_print(f"Starting contextual RAG search for query: {query}")
        
        # コンテキストがある場合はクエリを拡張
        enhanced_query = query
        if context:
            # コンテキストから重要なキーワードを抽出
            context_words = context.split()[-20:]  # 最後の20単語を使用
            context_keywords = [word for word in context_words if len(word) > 2]
            
            if context_keywords:
                # クエリにコンテキストキーワードを追加
                enhanced_query = f"{query} {' '.join(context_keywords[:5])}"
                safe_print(f"Enhanced query with context: {enhanced_query}")
        
        # 拡張クエリで検索
        results = await adaptive_rag_search(enhanced_query, limit)
        
        # コンテキストとの関連性でスコア調整
        if context and results:
            context_lower = context.lower()
            for result in results:
                if 'content' in result and 'score' in result:
                    content_lower = result['content'].lower()
                    # コンテキストとの共通単語数でボーナススコア
                    common_words = set(context_lower.split()) & set(content_lower.split())
                    bonus = len(common_words) * 0.1
                    result['score'] += bonus
            
            # 再ソート
            results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        safe_print(f"Contextual RAG search completed with {len(results)} results")
        return results
        
    except Exception as e:
        safe_print(f"Error in contextual RAG search: {e}")
        # フォールバックとして基本RAG検索を実行
        return await rag_search(query, limit)

def format_search_results(results: List[Dict[str, Any]], max_length: int = 2000) -> str:
    """
    検索結果をフォーマットしてプロンプト用のテキストに変換
    """
    if not results:
        return "関連する情報が見つかりませんでした。"
    
    formatted_results = []
    current_length = 0
    
    for i, result in enumerate(results, 1):
        # document_sources.nameフィールドまたはdocument_nameフィールドを優先使用
        title = result.get('document_name') or result.get('title', 'タイトルなし')
        content = result.get('content', '')
        url = result.get('url', '')
        score = result.get('score', 0)
        
        # 結果をフォーマット
        formatted_result = f"【結果 {i}】\n"
        formatted_result += f"タイトル: {title}\n"
        if url:
            formatted_result += f"URL: {url}\n"
        formatted_result += f"内容: {content[:500]}{'...' if len(content) > 500 else ''}\n"
        if score > 0:
            formatted_result += f"関連度: {score:.3f}\n"
        formatted_result += "\n"
        
        # 長さチェック
        if current_length + len(formatted_result) > max_length:
            break
        
        formatted_results.append(formatted_result)
        current_length += len(formatted_result)
    
    return ''.join(formatted_results)