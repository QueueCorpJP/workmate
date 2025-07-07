"""
統合検索システム (Unified Search System)
s.mdの内容を参考に、複数の検索手法を統合した高精度な検索システムを実装

検索手法の統合:
1. 完全一致 / 部分一致（SQL）
2. Fuzzy検索（pg_trgm）
3. ベクトル検索（Embedding）
4. LLM rerank（再スコアリング）
"""

import asyncio
import time
import hashlib
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import numpy as np
from supabase_adapter import execute_query, get_supabase_client
from .chat_config import safe_print, model
from .vector_search import VectorSearchSystem, get_vector_search_instance
from .enhanced_postgresql_search import EnhancedPostgreSQLSearch

logger = logging.getLogger(__name__)

class SearchType(Enum):
    """検索タイプの定義"""
    EXACT_MATCH = "exact_match"
    FUZZY_SEARCH = "fuzzy_search"
    VECTOR_SEARCH = "vector_search"
    LLM_RERANK = "llm_rerank"
    UNIFIED = "unified"

@dataclass
class SearchResult:
    """検索結果の統一データ構造"""
    id: str
    content: str
    title: str
    score: float
    search_type: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'title': self.title,
            'score': self.score,
            'search_type': self.search_type,
            'metadata': self.metadata
        }

class ScoreNormalizer:
    """スコア正規化システム"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.score_cache = {}
    
    async def normalize_scores(self, results: List[SearchResult], search_type: str, company_id: str = None) -> List[SearchResult]:
        """スコアを正規化"""
        if not results:
            return results
        
        try:
            # 統計情報を取得
            stats = await self.get_score_stats(search_type, company_id)
            
            # Min-Max正規化を適用
            normalized_results = []
            for result in results:
                normalized_score = self._min_max_normalize(result.score, stats['min'], stats['max'])
                result.score = normalized_score
                normalized_results.append(result)
            
            # 統計情報を更新
            await self.update_score_stats(search_type, company_id, [r.score for r in results])
            
            return normalized_results
            
        except Exception as e:
            logger.error(f"スコア正規化エラー: {e}")
            return results
    
    async def get_score_stats(self, search_type: str, company_id: str = None) -> Dict[str, float]:
        """スコア統計を取得"""
        cache_key = f"{search_type}_{company_id or 'all'}"
        
        if cache_key in self.score_cache:
            return self.score_cache[cache_key]
        
        try:
            sql = """
                SELECT score_min, score_max, score_avg, score_std
                FROM search_score_stats
                WHERE search_type = %s
            """
            params = [search_type]
            
            if company_id:
                sql += " AND company_id = %s"
                params.append(company_id)
            else:
                sql += " AND company_id IS NULL"
            
            sql += " ORDER BY updated_at DESC LIMIT 1"
            
            result = execute_query(sql, params)
            
            if result and len(result) > 0:
                stats = {
                    'min': result[0].get('score_min', 0.0),
                    'max': result[0].get('score_max', 1.0),
                    'avg': result[0].get('score_avg', 0.5),
                    'std': result[0].get('score_std', 0.2)
                }
            else:
                # デフォルト値
                stats = {'min': 0.0, 'max': 1.0, 'avg': 0.5, 'std': 0.2}
            
            self.score_cache[cache_key] = stats
            return stats
            
        except Exception as e:
            logger.error(f"スコア統計取得エラー: {e}")
            return {'min': 0.0, 'max': 1.0, 'avg': 0.5, 'std': 0.2}
    
    async def update_score_stats(self, search_type: str, company_id: str, scores: List[float]):
        """スコア統計を更新"""
        if not scores:
            return
        
        try:
            scores_array = np.array(scores)
            stats = {
                'min': float(np.min(scores_array)),
                'max': float(np.max(scores_array)),
                'avg': float(np.mean(scores_array)),
                'std': float(np.std(scores_array))
            }
            
            sql = """
                INSERT INTO search_score_stats (search_type, company_id, score_min, score_max, score_avg, score_std, sample_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (search_type, company_id) DO UPDATE SET
                    score_min = LEAST(search_score_stats.score_min, EXCLUDED.score_min),
                    score_max = GREATEST(search_score_stats.score_max, EXCLUDED.score_max),
                    score_avg = (search_score_stats.score_avg * search_score_stats.sample_count + EXCLUDED.score_avg * EXCLUDED.sample_count) / (search_score_stats.sample_count + EXCLUDED.sample_count),
                    score_std = EXCLUDED.score_std,
                    sample_count = search_score_stats.sample_count + EXCLUDED.sample_count,
                    updated_at = NOW()
            """
            
            execute_query(sql, [search_type, company_id, stats['min'], stats['max'], 
                              stats['avg'], stats['std'], len(scores)])
            
            # キャッシュを更新
            cache_key = f"{search_type}_{company_id or 'all'}"
            self.score_cache[cache_key] = stats
            
        except Exception as e:
            logger.error(f"スコア統計更新エラー: {e}")
    
    def _min_max_normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Min-Max正規化"""
        if max_val == min_val:
            return 0.5
        return (value - min_val) / (max_val - min_val)

class SearchCache:
    """検索キャッシュシステム"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def _generate_cache_key(self, query: str, search_type: str, company_id: str = None) -> str:
        """キャッシュキーを生成"""
        cache_data = f"{query}_{search_type}_{company_id or 'all'}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    async def get_cached_results(self, query: str, search_type: str, company_id: str = None) -> Optional[List[SearchResult]]:
        """キャッシュから結果を取得"""
        try:
            cache_key = self._generate_cache_key(query, search_type, company_id)
            
            sql = """
                SELECT results
                FROM search_cache
                WHERE query_hash = %s AND expires_at > NOW()
                ORDER BY created_at DESC
                LIMIT 1
            """
            
            result = execute_query(sql, [cache_key])
            
            if result and len(result) > 0:
                results_data = result[0]['results']
                return [SearchResult(**r) for r in results_data]
                
            return None
            
        except Exception as e:
            logger.error(f"キャッシュ取得エラー: {e}")
            return None
    
    async def cache_results(self, query: str, search_type: str, results: List[SearchResult], company_id: str = None):
        """結果をキャッシュ"""
        try:
            cache_key = self._generate_cache_key(query, search_type, company_id)
            results_data = [r.to_dict() for r in results]
            
            sql = """
                INSERT INTO search_cache (query_hash, query_text, company_id, search_type, results)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (query_hash) DO UPDATE SET
                    results = EXCLUDED.results,
                    created_at = NOW(),
                    expires_at = NOW() + INTERVAL '1 hour'
            """
            
            execute_query(sql, [cache_key, query, company_id, search_type, json.dumps(results_data)])
            
        except Exception as e:
            logger.error(f"キャッシュ保存エラー: {e}")

class UnifiedSearchSystem:
    """統合検索システム"""
    
    def __init__(self):
        self.vector_search = get_vector_search_instance()
        self.enhanced_postgresql = EnhancedPostgreSQLSearch()
        self.score_normalizer = ScoreNormalizer()
        self.search_cache = SearchCache()
    
    async def search(self, 
                    query: str, 
                    company_id: str = None,
                    limit: int = 10,
                    use_cache: bool = True,
                    enable_rerank: bool = True) -> List[SearchResult]:
        """
        統合検索を実行
        
        Args:
            query: 検索クエリ
            company_id: 会社ID
            limit: 結果数制限
            use_cache: キャッシュを使用するか
            enable_rerank: LLM rerankを使用するか
        """
        start_time = time.time()
        
        try:
            # キャッシュから結果を取得
            if use_cache:
                cached_results = await self.search_cache.get_cached_results(query, SearchType.UNIFIED.value, company_id)
                if cached_results:
                    safe_print(f"キャッシュから結果を取得: {len(cached_results)}件")
                    return cached_results[:limit]
            
            # 複数の検索手法を並列実行
            search_tasks = [
                self._exact_match_search(query, company_id, limit),
                self._fuzzy_search(query, company_id, limit),
                self._vector_search(query, company_id, limit)
            ]
            
            results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # 結果を統合
            all_results = []
            for i, results in enumerate(results_list):
                if isinstance(results, Exception):
                    logger.error(f"検索エラー: {results}")
                    continue
                
                if isinstance(results, list):
                    all_results.extend(results)
            
            # 重複を除去
            unique_results = self._deduplicate_results(all_results)
            
            # スコアを正規化
            normalized_results = await self._normalize_all_scores(unique_results, company_id)
            
            # LLM rerankを実行
            if enable_rerank and len(normalized_results) > 3:
                reranked_results = await self._llm_rerank(query, normalized_results[:20])
                final_results = reranked_results
            else:
                # スコア順でソート
                final_results = sorted(normalized_results, key=lambda x: x.score, reverse=True)
            
            # 結果を制限
            final_results = final_results[:limit]
            
            # キャッシュに保存
            if use_cache:
                await self.search_cache.cache_results(query, SearchType.UNIFIED.value, final_results, company_id)
            
            # パフォーマンスログを記録
            execution_time = int((time.time() - start_time) * 1000)
            await self._log_performance(query, ["exact_match", "fuzzy_search", "vector_search", "llm_rerank"], 
                                      company_id, execution_time, len(final_results))
            
            safe_print(f"統合検索完了: {len(final_results)}件の結果を{execution_time}msで取得")
            return final_results
            
        except Exception as e:
            logger.error(f"統合検索エラー: {e}")
            return []
    
    async def _exact_match_search(self, query: str, company_id: str, limit: int) -> List[SearchResult]:
        """完全一致検索"""
        try:
            sql = """
                SELECT c.id, c.content, ds.name as title, 1.0 as score
                FROM chunks c
                LEFT JOIN document_sources ds ON c.doc_id = ds.id
                WHERE c.content ILIKE %s
            """
            params = [f"%{query}%"]
            
            if company_id:
                sql += " AND c.company_id = %s"
                params.append(company_id)
            
            sql += " ORDER BY LENGTH(c.content) ASC LIMIT %s"
            params.append(limit)
            
            results = execute_query(sql, params)
            
            return [
                SearchResult(
                    id=r['id'],
                    content=r['content'],
                    title=r['title'] or 'Unknown',
                    score=1.0,
                    search_type=SearchType.EXACT_MATCH.value,
                    metadata={'query': query}
                )
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"完全一致検索エラー: {e}")
            return []
    
    async def _fuzzy_search(self, query: str, company_id: str, limit: int) -> List[SearchResult]:
        """Fuzzy検索"""
        try:
            sql = """
                SELECT c.id, c.content, ds.name as title, 
                       similarity(c.content, %s) as score
                FROM chunks c
                LEFT JOIN document_sources ds ON c.doc_id = ds.id
                WHERE similarity(c.content, %s) > 0.1
            """
            params = [query, query]
            
            if company_id:
                sql += " AND c.company_id = %s"
                params.append(company_id)
            
            sql += " ORDER BY similarity(c.content, %s) DESC LIMIT %s"
            params.extend([query, limit])
            
            results = execute_query(sql, params)
            
            return [
                SearchResult(
                    id=r['id'],
                    content=r['content'],
                    title=r['title'] or 'Unknown',
                    score=float(r['score']),
                    search_type=SearchType.FUZZY_SEARCH.value,
                    metadata={'query': query}
                )
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"Fuzzy検索エラー: {e}")
            return []
    
    async def _vector_search(self, query: str, company_id: str, limit: int) -> List[SearchResult]:
        """ベクトル検索"""
        try:
            if not self.vector_search:
                return []
            
            results = self.vector_search.vector_similarity_search(query, company_id, limit)
            
            return [
                SearchResult(
                    id=r['chunk_id'],
                    content=r['snippet'],
                    title=r['document_name'],
                    score=r['similarity_score'],
                    search_type=SearchType.VECTOR_SEARCH.value,
                    metadata={'query': query, 'document_type': r.get('document_type', '')}
                )
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"ベクトル検索エラー: {e}")
            return []
    
    async def _llm_rerank(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """LLMによる再ランキング"""
        try:
            if not model or len(results) < 2:
                return results
            
            # 結果を文字列に変換
            results_text = []
            for i, result in enumerate(results):
                text = f"{i+1}. {result.title}\n{result.content[:300]}..."
                results_text.append(text)
            
            prompt = f"""
以下の検索結果を、クエリ「{query}」に対する関連度順にランキングしてください。
最も関連度の高いものから順に番号のみを出力してください。

検索結果:
{chr(10).join(results_text)}

関連度順のランキング（番号のみ、カンマ区切り）:
"""
            
            response = model.generate_content(prompt)
            
            if response and response.text:
                # ランキングを解析
                ranking_text = response.text.strip()
                try:
                    ranking_numbers = [int(x.strip()) for x in ranking_text.split(',')]
                    
                    # ランキングに基づいて結果を並び替え
                    reranked_results = []
                    for rank, num in enumerate(ranking_numbers):
                        if 1 <= num <= len(results):
                            result = results[num - 1]
                            # rerankスコアを適用
                            rerank_score = 1.0 - (rank / len(ranking_numbers))
                            result.score = result.score * 0.7 + rerank_score * 0.3
                            result.search_type = SearchType.LLM_RERANK.value
                            reranked_results.append(result)
                    
                    return reranked_results
                    
                except (ValueError, IndexError) as e:
                    logger.error(f"ランキング解析エラー: {e}")
                    return results
            
            return results
            
        except Exception as e:
            logger.error(f"LLM rerankエラー: {e}")
            return results
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """重複を除去"""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            if result.id not in seen_ids:
                seen_ids.add(result.id)
                unique_results.append(result)
        
        return unique_results
    
    async def _normalize_all_scores(self, results: List[SearchResult], company_id: str) -> List[SearchResult]:
        """全てのスコアを正規化"""
        # 検索タイプごとにグループ化
        grouped_results = {}
        for result in results:
            if result.search_type not in grouped_results:
                grouped_results[result.search_type] = []
            grouped_results[result.search_type].append(result)
        
        # 各グループのスコアを正規化
        normalized_results = []
        for search_type, group_results in grouped_results.items():
            normalized_group = await self.score_normalizer.normalize_scores(group_results, search_type, company_id)
            normalized_results.extend(normalized_group)
        
        return normalized_results
    
    async def _log_performance(self, query: str, search_types: List[str], company_id: str, 
                             execution_time: int, result_count: int):
        """パフォーマンスログを記録"""
        try:
            sql = """
                INSERT INTO search_performance_log (query_text, search_types, company_id, execution_time_ms, result_count)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            execute_query(sql, [query, search_types, company_id, execution_time, result_count])
            
        except Exception as e:
            logger.error(f"パフォーマンスログエラー: {e}")

# グローバルインスタンス
unified_search_system = UnifiedSearchSystem()

async def unified_search(query: str, 
                        company_id: str = None,
                        limit: int = 10,
                        use_cache: bool = True,
                        enable_rerank: bool = True) -> List[Dict[str, Any]]:
    """
    統合検索のエントリーポイント
    
    Returns:
        検索結果のリスト（辞書形式）
    """
    results = await unified_search_system.search(query, company_id, limit, use_cache, enable_rerank)
    return [result.to_dict() for result in results] 