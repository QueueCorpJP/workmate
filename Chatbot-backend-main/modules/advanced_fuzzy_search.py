"""
Advanced Fuzzy Search Implementation
高度なファジー検索システム（normalize_text関数と文字数差を考慮したスコア計算）

ご質問のような高度なPostgreSQLクエリを実装：
SELECT *,
  similarity(normalize_text(content), normalize_text(:query)) AS sim,
  abs(length(normalize_text(content)) - length(normalize_text(:query))) AS len_diff,
  (similarity(normalize_text(content), normalize_text(:query)) - 0.02 * len_diff) AS final_score
FROM chunks
WHERE similarity(normalize_text(content), normalize_text(:query)) > 0.45
ORDER BY final_score DESC
LIMIT 20;
"""

import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor
from supabase_adapter import execute_query

logger = logging.getLogger(__name__)

@dataclass
class AdvancedFuzzyResult:
    """高度ファジー検索結果"""
    chunk_id: str
    doc_id: str
    content: str
    document_name: str
    document_type: str
    similarity_score: float
    length_diff: int
    final_score: float
    normalized_content: str
    normalized_query: str
    chunk_index: int = 0
    company_id: str = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'chunk_id': self.chunk_id,
            'doc_id': self.doc_id,
            'content': self.content,
            'document_name': self.document_name,
            'document_type': self.document_type,
            'similarity_score': self.similarity_score,
            'length_diff': self.length_diff,
            'final_score': self.final_score,
            'normalized_content': self.normalized_content,
            'normalized_query': self.normalized_query,
            'chunk_index': self.chunk_index,
            'company_id': self.company_id,
            'search_method': 'advanced_fuzzy_search'
        }

class AdvancedFuzzySearchSystem:
    """高度ファジー検索システム"""
    
    def __init__(self):
        self.db_url = self._get_db_url()
        self.initialized = False
        
    def _get_db_url(self) -> str:
        """データベースURLを構築"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL と SUPABASE_KEY 環境変数が設定されていません")
        
        if "supabase.co" in supabase_url:
            project_id = supabase_url.split("://")[1].split(".")[0]
            return f"postgresql://postgres.{project_id}:{os.getenv('DB_PASSWORD', '')}@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"
        else:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL 環境変数が設定されていません")
            return db_url
    
    async def initialize(self) -> bool:
        """高度ファジー検索システムを初期化"""
        if self.initialized:
            return True
            
        try:
            logger.info("🔧 高度ファジー検索システムの初期化開始")
            
            # PostgreSQL関数とインデックスを作成
            await self._execute_initialization_sql()
            
            self.initialized = True
            logger.info("✅ 高度ファジー検索システム初期化完了")
            return True
            
        except Exception as e:
            logger.error(f"❌ 高度ファジー検索システム初期化エラー: {e}")
            return False
    
    async def _execute_initialization_sql(self):
        """初期化SQLを実行"""
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # pg_trgm拡張を有効化
                    cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
                    
                    # 注意: normalize_text関数とcalculate_advanced_fuzzy_score関数は
                    # Supabase側に既に定義されているため、重複定義を削除
                    
                    # パフォーマンス向上用インデックスを作成
                    try:
                        cur.execute("""
                            CREATE INDEX IF NOT EXISTS idx_chunks_normalized_content_trgm 
                            ON chunks USING gin (normalize_text(content) gin_trgm_ops);
                        """)
                    except Exception as e:
                        logger.warning(f"インデックス作成警告: {e}")
                    
                    try:
                        cur.execute("""
                            CREATE INDEX IF NOT EXISTS idx_chunks_content_length 
                            ON chunks (length(content));
                        """)
                    except Exception as e:
                        logger.warning(f"インデックス作成警告: {e}")
                    
                    conn.commit()
                    logger.info("✅ PostgreSQL拡張とインデックスの作成完了")
                    
        except Exception as e:
            logger.error(f"❌ 初期化SQL実行エラー: {e}")
            raise
    
    async def advanced_fuzzy_search(self, 
                                  query: str, 
                                  company_id: str = None,
                                  threshold: float = 0.45,
                                  length_penalty: float = 0.012,
                                  limit: int = 50) -> List[AdvancedFuzzyResult]:
        """
        高度ファジー検索を実行
        
        Args:
            query: 検索クエリ
            company_id: 会社ID（オプション）
            threshold: 最終スコアの閾値（デフォルト: 0.45）
            length_penalty: 文字数差のペナルティ係数（デフォルト: 0.012）
            limit: 結果数制限（デフォルト: 50）
        
        Returns:
            高度ファジー検索結果のリスト
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            logger.info(f"🔍 高度ファジー検索開始: '{query}' (閾値: {threshold}, ペナルティ: {length_penalty})")
            
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # ユーザー指定の精度改良版クエリ
                    sql = """
                    WITH normalized AS (
                        SELECT
                            c.id as chunk_id,
                            c.doc_id,
                            c.content,
                            c.chunk_index,
                            c.company_id,
                            ds.name as document_name,
                            ds.type as document_type,
                            normalize_text(c.content) AS norm_content,
                            normalize_text(%s) AS norm_query
                        FROM chunks c
                        LEFT JOIN document_sources ds ON c.doc_id = ds.id
                        WHERE c.content IS NOT NULL
                          AND length(c.content) > 10
                    """
                    
                    params = [query]
                    
                    # 会社IDフィルターを追加
                    if company_id:
                        sql += " AND c.company_id = %s"
                        params.append(company_id)
                    
                    sql += """
                    )
                    SELECT *,
                        similarity(norm_content, norm_query) AS sim,
                        abs(length(norm_content) - length(norm_query)) AS len_diff,
                        (
                            similarity(norm_content, norm_query)
                            - %s * abs(length(norm_content) - length(norm_query))  -- 減点弱めに修正
                            + CASE
                                WHEN norm_content = norm_query THEN 0.4               -- 完全一致ブースト控えめに
                                WHEN norm_content LIKE norm_query || '%%' THEN 0.2     -- 前方一致も調整
                                ELSE 0
                              END
                        ) AS final_score,
                        norm_content as normalized_content,
                        norm_query as normalized_query
                    FROM normalized
                    WHERE similarity(norm_content, norm_query) > %s
                    ORDER BY final_score DESC
                    LIMIT %s
                    """
                    
                    params.extend([length_penalty, threshold, limit])
                    
                    cur.execute(sql, params)
                    rows = cur.fetchall()
                    
                    results = []
                    for row in rows:
                        result = AdvancedFuzzyResult(
                            chunk_id=str(row['chunk_id']),
                            doc_id=str(row['doc_id']),
                            content=row['content'] or '',
                            document_name=row['document_name'] or 'Unknown',
                            document_type=row['document_type'] or 'unknown',
                            similarity_score=float(row['sim']),
                            length_diff=int(row['len_diff']),
                            final_score=float(row['final_score']),
                            normalized_content=row['normalized_content'] or '',
                            normalized_query=row['normalized_query'] or '',
                            chunk_index=int(row['chunk_index']) if row['chunk_index'] else 0,
                            company_id=row['company_id']
                        )
                        results.append(result)
                    
                    logger.info(f"✅ 高度ファジー検索完了: {len(results)}件の結果")
                    
                    # 結果の詳細ログ
                    if results:
                        logger.info("📊 検索結果詳細:")
                        for i, result in enumerate(results[:5]):  # 上位5件
                            logger.info(f"  {i+1}. {result.document_name} - 最終スコア: {result.final_score:.4f}")
                            logger.info(f"      類似度: {result.similarity_score:.4f}, 文字数差: {result.length_diff}")
                            logger.info(f"      内容: {result.content[:100]}...")
                    
                    return results
                    
        except Exception as e:
            logger.error(f"❌ 高度ファジー検索エラー: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def test_normalize_function(self, test_text: str) -> Dict[str, str]:
        """normalize_text関数のテスト"""
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT normalize_text(%s) as normalized", [test_text])
                    result = cur.fetchone()
                    
                    return {
                        'original': test_text,
                        'normalized': result['normalized']
                    }
                    
        except Exception as e:
            logger.error(f"normalize_text関数テストエラー: {e}")
            return {'original': test_text, 'normalized': 'エラー'}
    
    async def get_similarity_distribution(self, query: str, company_id: str = None) -> Dict[str, Any]:
        """類似度分布の分析"""
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    sql = """
                    SELECT 
                        COUNT(*) as total_chunks,
                        AVG(similarity(normalize_text(content), normalize_text(%s))) as avg_similarity,
                        MIN(similarity(normalize_text(content), normalize_text(%s))) as min_similarity,
                        MAX(similarity(normalize_text(content), normalize_text(%s))) as max_similarity,
                        STDDEV(similarity(normalize_text(content), normalize_text(%s))) as std_similarity
                    FROM chunks
                    WHERE content IS NOT NULL AND length(content) > 10
                    """
                    
                    params = [query, query, query, query]
                    
                    if company_id:
                        sql += " AND company_id = %s"
                        params.append(company_id)
                    
                    cur.execute(sql, params)
                    result = cur.fetchone()
                    
                    return {
                        'query': query,
                        'total_chunks': result['total_chunks'],
                        'avg_similarity': float(result['avg_similarity']) if result['avg_similarity'] else 0.0,
                        'min_similarity': float(result['min_similarity']) if result['min_similarity'] else 0.0,
                        'max_similarity': float(result['max_similarity']) if result['max_similarity'] else 0.0,
                        'std_similarity': float(result['std_similarity']) if result['std_similarity'] else 0.0
                    }
                    
        except Exception as e:
            logger.error(f"類似度分布分析エラー: {e}")
            return {}


# グローバルインスタンス
_advanced_fuzzy_search_system = None

def get_advanced_fuzzy_search_instance() -> Optional[AdvancedFuzzySearchSystem]:
    """高度ファジー検索システムのインスタンスを取得（シングルトンパターン）"""
    global _advanced_fuzzy_search_system
    
    if _advanced_fuzzy_search_system is None:
        try:
            _advanced_fuzzy_search_system = AdvancedFuzzySearchSystem()
            logger.info("✅ 高度ファジー検索システムインスタンス作成完了")
        except Exception as e:
            logger.error(f"❌ 高度ファジー検索システムインスタンス作成エラー: {e}")
            return None
    
    return _advanced_fuzzy_search_system

async def advanced_fuzzy_search(query: str, 
                              company_id: str = None,
                              threshold: float = 0.45,
                              length_penalty: float = 0.012,
                              limit: int = 50) -> List[Dict[str, Any]]:
    """
    高度ファジー検索のエントリーポイント
    
    Returns:
        検索結果のリスト（辞書形式）
    """
    instance = get_advanced_fuzzy_search_instance()
    if not instance:
        logger.error("❌ 高度ファジー検索システムが利用できません")
        return []
    
    results = await instance.advanced_fuzzy_search(query, company_id, threshold, length_penalty, limit)
    return [result.to_dict() for result in results]

def advanced_fuzzy_search_available() -> bool:
    """高度ファジー検索が利用可能かチェック"""
    try:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        return bool(api_key and supabase_url and supabase_key)
    except Exception:
        return False 