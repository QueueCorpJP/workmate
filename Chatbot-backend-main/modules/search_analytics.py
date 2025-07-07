"""
検索分析システム (Search Analytics System)
検索パフォーマンスの監視と分析機能を提供
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .timezone_utils import now_jst, now_jst_simple
from supabase_adapter import execute_query, get_supabase_client
from .chat_config import safe_print

logger = logging.getLogger(__name__)

class SearchAnalytics:
    """検索分析システム"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def get_search_performance_report(self, 
                                          company_id: str = None,
                                          days: int = 7) -> Dict[str, Any]:
        """
        検索パフォーマンスレポートを取得
        
        Args:
            company_id: 会社ID
            days: 分析期間（日数）
        """
        try:
            end_date = now_jst().replace(tzinfo=None)
            start_date = end_date - timedelta(days=days)
            
            # 基本統計
            basic_stats = await self._get_basic_search_stats(start_date, end_date, company_id)
            
            # 検索タイプ別統計
            search_type_stats = await self._get_search_type_stats(start_date, end_date, company_id)
            
            # パフォーマンス統計
            performance_stats = await self._get_performance_stats(start_date, end_date, company_id)
            
            # 人気検索クエリ
            popular_queries = await self._get_popular_queries(start_date, end_date, company_id)
            
            # スコア分布
            score_distribution = await self._get_score_distribution(company_id)
            
            report = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'basic_stats': basic_stats,
                'search_type_stats': search_type_stats,
                'performance_stats': performance_stats,
                'popular_queries': popular_queries,
                'score_distribution': score_distribution,
                'company_id': company_id
            }
            
            return report
            
        except Exception as e:
            logger.error(f"検索パフォーマンスレポート取得エラー: {e}")
            return {}
    
    async def _get_basic_search_stats(self, start_date: datetime, end_date: datetime, company_id: str) -> Dict[str, Any]:
        """基本的な検索統計を取得"""
        try:
            sql = """
                SELECT 
                    COUNT(*) as total_searches,
                    AVG(execution_time_ms) as avg_execution_time,
                    AVG(result_count) as avg_result_count,
                    COUNT(DISTINCT user_id) as unique_users
                FROM search_performance_log
                WHERE created_at >= %s AND created_at <= %s
            """
            params = [start_date, end_date]
            
            if company_id:
                sql += " AND company_id = %s"
                params.append(company_id)
            
            result = execute_query(sql, params)
            
            if result and len(result) > 0:
                return {
                    'total_searches': result[0].get('total_searches', 0),
                    'avg_execution_time_ms': float(result[0].get('avg_execution_time', 0)),
                    'avg_result_count': float(result[0].get('avg_result_count', 0)),
                    'unique_users': result[0].get('unique_users', 0)
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"基本検索統計取得エラー: {e}")
            return {}
    
    async def _get_search_type_stats(self, start_date: datetime, end_date: datetime, company_id: str) -> List[Dict[str, Any]]:
        """検索タイプ別統計を取得"""
        try:
            sql = """
                SELECT 
                    unnest(search_types) as search_type,
                    COUNT(*) as usage_count,
                    AVG(execution_time_ms) as avg_execution_time,
                    AVG(result_count) as avg_result_count
                FROM search_performance_log
                WHERE created_at >= %s AND created_at <= %s
            """
            params = [start_date, end_date]
            
            if company_id:
                sql += " AND company_id = %s"
                params.append(company_id)
            
            sql += " GROUP BY search_type ORDER BY usage_count DESC"
            
            result = execute_query(sql, params)
            
            return [
                {
                    'search_type': row.get('search_type', ''),
                    'usage_count': row.get('usage_count', 0),
                    'avg_execution_time_ms': float(row.get('avg_execution_time', 0)),
                    'avg_result_count': float(row.get('avg_result_count', 0))
                }
                for row in result
            ]
            
        except Exception as e:
            logger.error(f"検索タイプ別統計取得エラー: {e}")
            return []
    
    async def _get_performance_stats(self, start_date: datetime, end_date: datetime, company_id: str) -> Dict[str, Any]:
        """パフォーマンス統計を取得"""
        try:
            sql = """
                SELECT 
                    MIN(execution_time_ms) as min_execution_time,
                    MAX(execution_time_ms) as max_execution_time,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY execution_time_ms) as median_execution_time,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms) as p95_execution_time,
                    MIN(result_count) as min_result_count,
                    MAX(result_count) as max_result_count
                FROM search_performance_log
                WHERE created_at >= %s AND created_at <= %s
            """
            params = [start_date, end_date]
            
            if company_id:
                sql += " AND company_id = %s"
                params.append(company_id)
            
            result = execute_query(sql, params)
            
            if result and len(result) > 0:
                return {
                    'min_execution_time_ms': result[0].get('min_execution_time', 0),
                    'max_execution_time_ms': result[0].get('max_execution_time', 0),
                    'median_execution_time_ms': float(result[0].get('median_execution_time', 0)),
                    'p95_execution_time_ms': float(result[0].get('p95_execution_time', 0)),
                    'min_result_count': result[0].get('min_result_count', 0),
                    'max_result_count': result[0].get('max_result_count', 0)
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"パフォーマンス統計取得エラー: {e}")
            return {}
    
    async def _get_popular_queries(self, start_date: datetime, end_date: datetime, company_id: str) -> List[Dict[str, Any]]:
        """人気検索クエリを取得"""
        try:
            sql = """
                SELECT 
                    query_text,
                    COUNT(*) as search_count,
                    AVG(execution_time_ms) as avg_execution_time,
                    AVG(result_count) as avg_result_count
                FROM search_performance_log
                WHERE created_at >= %s AND created_at <= %s
                  AND LENGTH(query_text) > 0
            """
            params = [start_date, end_date]
            
            if company_id:
                sql += " AND company_id = %s"
                params.append(company_id)
            
            sql += " GROUP BY query_text ORDER BY search_count DESC LIMIT 10"
            
            result = execute_query(sql, params)
            
            return [
                {
                    'query': row.get('query_text', ''),
                    'search_count': row.get('search_count', 0),
                    'avg_execution_time_ms': float(row.get('avg_execution_time', 0)),
                    'avg_result_count': float(row.get('avg_result_count', 0))
                }
                for row in result
            ]
            
        except Exception as e:
            logger.error(f"人気検索クエリ取得エラー: {e}")
            return []
    
    async def _get_score_distribution(self, company_id: str) -> List[Dict[str, Any]]:
        """スコア分布を取得"""
        try:
            sql = """
                SELECT 
                    search_type,
                    score_min,
                    score_max,
                    score_avg,
                    score_std,
                    sample_count
                FROM search_score_stats
                WHERE 1=1
            """
            params = []
            
            if company_id:
                sql += " AND company_id = %s"
                params.append(company_id)
            else:
                sql += " AND company_id IS NULL"
            
            sql += " ORDER BY sample_count DESC"
            
            result = execute_query(sql, params)
            
            return [
                {
                    'search_type': row.get('search_type', ''),
                    'score_min': float(row.get('score_min', 0)),
                    'score_max': float(row.get('score_max', 0)),
                    'score_avg': float(row.get('score_avg', 0)),
                    'score_std': float(row.get('score_std', 0)),
                    'sample_count': row.get('sample_count', 0)
                }
                for row in result
            ]
            
        except Exception as e:
            logger.error(f"スコア分布取得エラー: {e}")
            return []
    
    async def cleanup_old_cache(self, days: int = 1) -> int:
        """古いキャッシュをクリーンアップ"""
        try:
            sql = """
                DELETE FROM search_cache 
                WHERE created_at < %s OR expires_at < NOW()
            """
            
            cleanup_date = now_jst().replace(tzinfo=None) - timedelta(days=days)
            result = execute_query(sql, [cleanup_date])
            
            safe_print(f"検索キャッシュクリーンアップ完了: {cleanup_date}以前のデータを削除")
            return 1  # 成功
            
        except Exception as e:
            logger.error(f"キャッシュクリーンアップエラー: {e}")
            return 0
    
    async def get_search_cache_stats(self) -> Dict[str, Any]:
        """検索キャッシュの統計を取得"""
        try:
            sql = """
                SELECT 
                    COUNT(*) as total_cached_queries,
                    COUNT(DISTINCT company_id) as companies_with_cache,
                    COUNT(DISTINCT search_type) as search_types_cached,
                    MIN(created_at) as oldest_cache,
                    MAX(created_at) as newest_cache
                FROM search_cache
                WHERE expires_at > NOW()
            """
            
            result = execute_query(sql)
            
            if result and len(result) > 0:
                return {
                    'total_cached_queries': result[0].get('total_cached_queries', 0),
                    'companies_with_cache': result[0].get('companies_with_cache', 0),
                    'search_types_cached': result[0].get('search_types_cached', 0),
                    'oldest_cache': result[0].get('oldest_cache'),
                    'newest_cache': result[0].get('newest_cache')
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"キャッシュ統計取得エラー: {e}")
            return {}
    
    def format_performance_report(self, report: Dict[str, Any]) -> str:
        """パフォーマンスレポートをフォーマット"""
        if not report:
            return "パフォーマンスレポートを取得できませんでした。"
        
        formatted_report = []
        
        # 基本統計
        basic_stats = report.get('basic_stats', {})
        formatted_report.append("=== 検索パフォーマンスレポート ===")
        formatted_report.append(f"期間: {report.get('period', {}).get('days', 0)}日間")
        formatted_report.append(f"総検索数: {basic_stats.get('total_searches', 0):,}")
        formatted_report.append(f"平均実行時間: {basic_stats.get('avg_execution_time_ms', 0):.1f}ms")
        formatted_report.append(f"平均結果数: {basic_stats.get('avg_result_count', 0):.1f}")
        formatted_report.append(f"ユニークユーザー数: {basic_stats.get('unique_users', 0)}")
        formatted_report.append("")
        
        # 検索タイプ別統計
        search_type_stats = report.get('search_type_stats', [])
        if search_type_stats:
            formatted_report.append("=== 検索タイプ別統計 ===")
            for stat in search_type_stats:
                formatted_report.append(
                    f"{stat.get('search_type', '')}: {stat.get('usage_count', 0)}回 "
                    f"(平均実行時間: {stat.get('avg_execution_time_ms', 0):.1f}ms)"
                )
            formatted_report.append("")
        
        # パフォーマンス統計
        performance_stats = report.get('performance_stats', {})
        if performance_stats:
            formatted_report.append("=== パフォーマンス統計 ===")
            formatted_report.append(f"最短実行時間: {performance_stats.get('min_execution_time_ms', 0)}ms")
            formatted_report.append(f"最長実行時間: {performance_stats.get('max_execution_time_ms', 0)}ms")
            formatted_report.append(f"中央値実行時間: {performance_stats.get('median_execution_time_ms', 0):.1f}ms")
            formatted_report.append(f"95パーセンタイル実行時間: {performance_stats.get('p95_execution_time_ms', 0):.1f}ms")
            formatted_report.append("")
        
        # 人気検索クエリ
        popular_queries = report.get('popular_queries', [])
        if popular_queries:
            formatted_report.append("=== 人気検索クエリ Top 5 ===")
            for i, query in enumerate(popular_queries[:5], 1):
                formatted_report.append(
                    f"{i}. 「{query.get('query', '')}」 - {query.get('search_count', 0)}回検索"
                )
            formatted_report.append("")
        
        return "\n".join(formatted_report)

# グローバルインスタンス
search_analytics = SearchAnalytics()

async def get_search_performance_report(company_id: str = None, days: int = 7) -> Dict[str, Any]:
    """検索パフォーマンスレポートを取得"""
    return await search_analytics.get_search_performance_report(company_id, days)

async def cleanup_old_search_cache(days: int = 1) -> int:
    """古い検索キャッシュをクリーンアップ"""
    return await search_analytics.cleanup_old_cache(days)

def format_search_performance_report(report: Dict[str, Any]) -> str:
    """検索パフォーマンスレポートをフォーマット"""
    return search_analytics.format_performance_report(report) 