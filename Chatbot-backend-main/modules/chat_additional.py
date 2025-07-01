"""
追加のRAGバリエーションとヘルパー関数
特殊なRAG検索機能と補助的な機能を管理します
"""
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from .chat_config import safe_print, HTTPException, model, get_db_cursor
from .chat_rag import rag_search, enhanced_rag_search
from .chat_search_systems import smart_search_system
from .chat_utils import expand_query

async def rag_search_with_fallback(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    フォールバック機能付きRAG検索
    """
    try:
        safe_print(f"Starting RAG search with fallback for: {query}")
        
        # 主要検索を試行
        results = await enhanced_rag_search(query, limit)
        
        if results and len(results) >= 3:
            safe_print(f"Primary search successful with {len(results)} results")
            return results
        
        # フォールバック1: 基本RAG検索
        safe_print("Trying fallback 1: basic RAG search")
        fallback_results = await rag_search(query, limit)
        
        if fallback_results and len(fallback_results) >= 2:
            safe_print(f"Fallback 1 successful with {len(fallback_results)} results")
            return fallback_results
        
        # フォールバック2: クエリ拡張
        safe_print("Trying fallback 2: expanded query search")
        expanded_query = expand_query(query)
        if expanded_query != query:
            expanded_results = await rag_search(expanded_query, limit)
            if expanded_results:
                safe_print(f"Fallback 2 successful with {len(expanded_results)} results")
                return expanded_results
        
        # フォールバック3: 部分マッチ検索
        safe_print("Trying fallback 3: partial match search")
        partial_results = await partial_match_search(query, limit)
        
        if partial_results:
            safe_print(f"Fallback 3 successful with {len(partial_results)} results")
            return partial_results
        
        safe_print("All fallback methods failed")
        return []
        
    except Exception as e:
        safe_print(f"Error in RAG search with fallback: {e}")
        return []

async def partial_match_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    部分マッチ検索
    """
    try:
        cursor = get_db_cursor()
        if not cursor:
            return []
        
        # クエリを単語に分割
        query_words = query.split()
        
        if not query_words:
            return []
        
        # 各単語での部分マッチ検索
        search_conditions = []
        params = []
        
        for word in query_words:
            if len(word) > 2:  # 2文字以上の単語のみ
                search_conditions.append("(title ILIKE %s OR content ILIKE %s)")
                params.extend([f"%{word}%", f"%{word}%"])
        
        if not search_conditions:
            return []
        
        # SQL クエリを構築
        sql_query = f"""
        SELECT id, title, content, url,
               (CASE 
                WHEN title ILIKE %s THEN 3
                WHEN content ILIKE %s THEN 2
                ELSE 1
               END) as relevance_score
        FROM knowledge_base
        WHERE {' OR '.join(search_conditions)}
        ORDER BY relevance_score DESC, id
        LIMIT %s
        """
        
        # パラメータを準備
        full_params = [f"%{query}%", f"%{query}%"] + params + [limit]
        
        cursor.execute(sql_query, full_params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'url': row[3],
                'score': float(row[4])
            })
        
        safe_print(f"Partial match search returned {len(results)} results")
        return results
        
    except Exception as e:
        safe_print(f"Error in partial match search: {e}")
        return []

async def semantic_similarity_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    セマンティック類似度検索（簡易版）
    """
    try:
        safe_print(f"Starting semantic similarity search for: {query}")
        
        # 類義語マッピング
        semantic_expansions = {
            '方法': ['手順', 'やり方', 'プロセス', '手続き', 'ステップ'],
            '問題': ['課題', 'トラブル', 'エラー', '不具合', 'バグ'],
            '設定': ['構成', 'コンフィグ', '設定値', 'セットアップ', '初期化'],
            '使い方': ['利用方法', '操作方法', '使用方法', '操作手順', '利用手順'],
            'エラー': ['問題', 'トラブル', '不具合', 'バグ', '障害'],
            '機能': ['特徴', '仕様', '性能', '能力', 'フィーチャー'],
        }
        
        # クエリを拡張
        expanded_terms = [query]
        query_words = query.split()
        
        for word in query_words:
            if word in semantic_expansions:
                expanded_terms.extend(semantic_expansions[word])
        
        # 拡張されたクエリで検索
        all_results = []
        seen_ids = set()
        
        for term in expanded_terms[:5]:  # 最大5つの用語で検索
            results = await smart_search_system(term, limit=5)
            
            for result in results:
                if result.get('id') not in seen_ids:
                    seen_ids.add(result['id'])
                    # セマンティック距離に基づくスコア調整
                    if term != query:
                        if 'score' in result:
                            result['score'] *= 0.8  # 類義語の場合はスコアを下げる
                    all_results.append(result)
        
        # スコア順でソート
        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        final_results = all_results[:limit]
        safe_print(f"Semantic similarity search returned {len(final_results)} results")
        return final_results
        
    except Exception as e:
        safe_print(f"Error in semantic similarity search: {e}")
        return []

async def multi_modal_rag_search(query: str, context_type: str = "general", limit: int = 10) -> List[Dict[str, Any]]:
    """
    マルチモーダルRAG検索
    """
    try:
        safe_print(f"Starting multi-modal RAG search for: {query} (context: {context_type})")
        
        # コンテキストタイプに応じた検索戦略
        if context_type == "technical":
            # 技術的なコンテキスト
            results = await technical_focused_search(query, limit)
        elif context_type == "tutorial":
            # チュートリアル・手順系
            results = await tutorial_focused_search(query, limit)
        elif context_type == "troubleshooting":
            # トラブルシューティング
            results = await troubleshooting_focused_search(query, limit)
        else:
            # 一般的な検索
            results = await enhanced_rag_search(query, limit)
        
        safe_print(f"Multi-modal RAG search returned {len(results)} results")
        return results
        
    except Exception as e:
        safe_print(f"Error in multi-modal RAG search: {e}")
        return await rag_search(query, limit)  # フォールバック

async def technical_focused_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    技術的な内容に特化した検索
    """
    # 技術キーワードを強調
    technical_keywords = ['API', 'SQL', 'Python', 'JavaScript', 'HTML', 'CSS', 'JSON', 'XML']
    enhanced_query = query
    
    for keyword in technical_keywords:
        if keyword.lower() in query.lower():
            enhanced_query += f" {keyword}"
    
    return await enhanced_rag_search(enhanced_query, limit)

async def tutorial_focused_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    チュートリアル・手順に特化した検索
    """
    # 手順関連のキーワードを追加
    tutorial_keywords = ['手順', 'ステップ', 'やり方', '方法', 'チュートリアル']
    enhanced_query = f"{query} {' '.join(tutorial_keywords[:2])}"
    
    return await enhanced_rag_search(enhanced_query, limit)

async def troubleshooting_focused_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    トラブルシューティングに特化した検索
    """
    # トラブルシューティング関連のキーワードを追加
    troubleshooting_keywords = ['エラー', '問題', 'トラブル', '解決', '対処法']
    enhanced_query = f"{query} {' '.join(troubleshooting_keywords[:2])}"
    
    return await enhanced_rag_search(enhanced_query, limit)

def calculate_relevance_score(query: str, result: Dict[str, Any]) -> float:
    """
    関連度スコアを計算
    """
    try:
        title = result.get('title', '').lower()
        content = result.get('content', '').lower()
        query_lower = query.lower()
        
        score = 0.0
        
        # タイトルマッチ（高い重み）
        if query_lower in title:
            score += 3.0
        
        # コンテンツマッチ
        if query_lower in content:
            score += 1.0
        
        # 単語レベルマッチ
        query_words = query_lower.split()
        for word in query_words:
            if len(word) > 2:
                if word in title:
                    score += 0.5
                if word in content:
                    score += 0.2
        
        # 長さによる正規化
        content_length = len(content)
        if content_length > 0:
            score = score / (1 + content_length / 1000)
        
        return score
        
    except Exception as e:
        safe_print(f"Error calculating relevance score: {e}")
        return 0.0

async def hybrid_search_strategy(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    ハイブリッド検索戦略
    """
    try:
        safe_print(f"Starting hybrid search strategy for: {query}")
        
        # 複数の検索手法を並列実行
        search_tasks = [
            enhanced_rag_search(query, limit=5),
            semantic_similarity_search(query, limit=5),
            partial_match_search(query, limit=5)
        ]
        
        results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # 結果をマージ
        merged_results = []
        seen_ids = set()
        
        for i, results in enumerate(results_list):
            if isinstance(results, Exception):
                safe_print(f"Search method {i} failed: {results}")
                continue
            
            if isinstance(results, list):
                for result in results:
                    if isinstance(result, dict) and 'id' in result:
                        if result['id'] not in seen_ids:
                            seen_ids.add(result['id'])
                            # 検索手法に応じてスコア調整
                            if 'score' in result:
                                if i == 1:  # semantic similarity
                                    result['score'] *= 0.9
                                elif i == 2:  # partial match
                                    result['score'] *= 0.8
                            merged_results.append(result)
        
        # 関連度スコアを再計算
        for result in merged_results:
            relevance = calculate_relevance_score(query, result)
            if 'score' in result:
                result['score'] = (result['score'] + relevance) / 2
            else:
                result['score'] = relevance
        
        # スコア順でソート
        merged_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        final_results = merged_results[:limit]
        safe_print(f"Hybrid search strategy returned {len(final_results)} results")
        return final_results
        
    except Exception as e:
        safe_print(f"Error in hybrid search strategy: {e}")
        return await rag_search(query, limit)

async def adaptive_search_with_learning(query: str, user_feedback: Dict[str, Any] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    学習機能付き適応検索
    """
    try:
        safe_print(f"Starting adaptive search with learning for: {query}")
        
        # ユーザーフィードバックを分析
        preferred_strategy = "enhanced"  # デフォルト
        
        if user_feedback:
            # フィードバックに基づいて戦略を調整
            if user_feedback.get('preferred_results') == 'technical':
                preferred_strategy = "technical"
            elif user_feedback.get('preferred_results') == 'tutorial':
                preferred_strategy = "tutorial"
            elif user_feedback.get('search_quality') == 'low':
                preferred_strategy = "hybrid"
        
        # 選択された戦略で検索
        if preferred_strategy == "technical":
            results = await technical_focused_search(query, limit)
        elif preferred_strategy == "tutorial":
            results = await tutorial_focused_search(query, limit)
        elif preferred_strategy == "hybrid":
            results = await hybrid_search_strategy(query, limit)
        else:
            results = await enhanced_rag_search(query, limit)
        
        # 学習データを保存（簡易版）
        if user_feedback:
            await save_search_feedback(query, preferred_strategy, user_feedback)
        
        safe_print(f"Adaptive search returned {len(results)} results using {preferred_strategy} strategy")
        return results
        
    except Exception as e:
        safe_print(f"Error in adaptive search with learning: {e}")
        return await rag_search(query, limit)

async def save_search_feedback(query: str, strategy: str, feedback: Dict[str, Any]):
    """
    検索フィードバックを保存
    """
    try:
        cursor = get_db_cursor()
        if cursor:
            cursor.execute("""
                INSERT INTO search_feedback (query, strategy, feedback, timestamp)
                VALUES (%s, %s, %s, NOW())
            """, (query, strategy, json.dumps(feedback)))
            cursor.connection.commit()
            safe_print("Search feedback saved")
    except Exception as e:
        safe_print(f"Error saving search feedback: {e}")