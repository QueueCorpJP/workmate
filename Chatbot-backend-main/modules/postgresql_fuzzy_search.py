"""
PostgreSQL Fuzzy Search Implementation
既存のPostgreSQLでFuzzy Search機能を実装
Elasticsearchは不要！
"""

import logging
from typing import List, Dict, Any, Optional
from .database import get_db
from supabase_adapter import get_supabase_client, execute_query

logger = logging.getLogger(__name__)

class PostgreSQLFuzzySearch:
    def __init__(self):
        self.supabase = get_supabase_client()
        
    async def initialize(self):
        """PostgreSQL Fuzzy Search拡張を初期化"""
        try:
            # pg_trgm拡張を有効化（trigram検索用）
            await self._execute_sql("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            
            # 日本語対応のためのインデックス作成
            await self._execute_sql("""
                CREATE INDEX IF NOT EXISTS idx_chunks_content_trgm 
                ON chunks USING gin (content gin_trgm_ops);
            """)
            
            await self._execute_sql("""
                CREATE INDEX IF NOT EXISTS idx_chunks_content_fulltext 
                ON chunks USING gin (to_tsvector('japanese', content));
            """)
            
            logger.info("PostgreSQL Fuzzy Search初期化完了")
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL Fuzzy Search初期化エラー: {e}")
            return False
            
    async def _execute_sql(self, sql: str):
        """SQLを実行"""
        try:
            result = execute_query(sql)
            return result
        except Exception as e:
            logger.warning(f"SQL実行エラー（継続）: {e}")
            # エラーでも継続（既に拡張が有効な場合など）
            return None
            
    async def fuzzy_search(self, query: str, limit: int = 25, threshold: float = 0.2) -> List[Dict[str, Any]]:
        """
        Fuzzy Search実行
        
        Args:
            query: 検索クエリ
            limit: 結果数制限
            threshold: 類似度閾値（0.0-1.0）
        """
        try:
            # 複数の検索手法を組み合わせ
            sql = """
            WITH fuzzy_results AS (
                -- 1. Trigram類似度検索
                SELECT 
                    chunk_id,
                    content,
                    file_name,
                    similarity(content, $1) as similarity_score,
                    'trigram' as search_type
                FROM chunks 
                WHERE similarity(content, $1) > $3
                
                UNION ALL
                
                -- 2. 全文検索
                SELECT 
                    chunk_id,
                    content,
                    file_name,
                    ts_rank(to_tsvector('japanese', content), plainto_tsquery('japanese', $1)) as similarity_score,
                    'fulltext' as search_type
                FROM chunks 
                WHERE to_tsvector('japanese', content) @@ plainto_tsquery('japanese', $1)
                
                UNION ALL
                
                -- 3. LIKE検索（部分一致）
                SELECT 
                    chunk_id,
                    content,
                    file_name,
                    0.5 as similarity_score,
                    'like' as search_type
                FROM chunks 
                WHERE content ILIKE '%' || $1 || '%'
            )
            SELECT DISTINCT
                chunk_id,
                content,
                file_name,
                MAX(similarity_score) as max_score,
                array_agg(DISTINCT search_type) as search_types
            FROM fuzzy_results
            GROUP BY chunk_id, content, file_name
            ORDER BY max_score DESC
            LIMIT $2;
            """
            
            # パラメータをSQLに埋め込み（Supabase用）
            formatted_sql = sql.replace('$1', f"'{query}'").replace('$2', str(limit)).replace('$3', str(threshold))
            
            rows = execute_query(formatted_sql)
            
            results = []
            for row in rows:
                results.append({
                    'chunk_id': row.get('chunk_id'),
                    'content': row.get('content'),
                    'file_name': row.get('file_name'),
                    'score': float(row.get('max_score', 0)),
                    'search_types': row.get('search_types', []),
                    'highlight': self._highlight_matches(row.get('content', ''), query)
                })
                
            logger.info(f"Fuzzy Search実行: クエリ='{query}', 結果数={len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"Fuzzy Search実行エラー: {e}")
            return []
            
    def _highlight_matches(self, content: str, query: str) -> str:
        """検索結果をハイライト"""
        try:
            # 簡単なハイライト実装
            highlighted = content.replace(query, f"<mark>{query}</mark>")
            return highlighted
        except:
            return content
            
    async def close(self):
        """接続を閉じる（Supabaseでは不要）"""
        pass

# グローバルインスタンス
postgresql_fuzzy = PostgreSQLFuzzySearch()

async def initialize_postgresql_fuzzy():
    """PostgreSQL Fuzzy Search初期化"""
    return await postgresql_fuzzy.initialize()

async def fuzzy_search_chunks(query: str, limit: int = 25, threshold: float = 0.2) -> List[Dict[str, Any]]:
    """Fuzzy Search実行"""
    return await postgresql_fuzzy.fuzzy_search(query, limit, threshold) 