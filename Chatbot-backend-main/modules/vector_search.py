"""
ベクトル検索モジュール（pgvector対応版）
Vertex AI text-multilingual-embedding-002を使用した類似検索機能を提供（768次元）
pgvector拡張機能の有無を自動検出し、適切な検索方法を選択
"""

import os
import logging
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
import google.generativeai as genai
from .vertex_ai_embedding import get_vertex_ai_embedding_client, vertex_ai_embedding_available

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class VectorSearchSystem:
    """ベクトル検索システム（pgvector対応版）"""
    
    def __init__(self):
        """初期化"""
        self.use_vertex_ai = os.getenv("USE_VERTEX_AI", "true").lower() == "true"
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-multilingual-embedding-002")
        
        self.db_url = self._get_db_url()
        self.pgvector_available = False
        
        # pgvector拡張機能の確認
        self._check_pgvector_availability()
        
        if self.use_vertex_ai and vertex_ai_embedding_available():
            self.vertex_client = get_vertex_ai_embedding_client()
            # 次元数を動的に取得
            expected_dimensions = 768 if "text-multilingual-embedding-002" in self.embedding_model else 3072
            logger.info(f"✅ ベクトル検索システム初期化: Vertex AI {self.embedding_model} ({expected_dimensions}次元)")
            logger.info(f"🔧 pgvector拡張機能: {'有効' if self.pgvector_available else '無効'}")
            self.expected_dimensions = expected_dimensions
        else:
            logger.error("❌ Vertex AI Embeddingが利用できません")
            raise ValueError("Vertex AI Embeddingの初期化に失敗しました")
    
    def _get_db_url(self) -> str:
        """データベースURLを構築"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL と SUPABASE_KEY 環境変数が設定されていません")
        
        # Supabase URLから接続情報を抽出
        if "supabase.co" in supabase_url:
            project_id = supabase_url.split("://")[1].split(".")[0]
            return f"postgresql://postgres.{project_id}:{os.getenv('DB_PASSWORD', '')}@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"
        else:
            # カスタムデータベースURLの場合
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL 環境変数が設定されていません")
            return db_url
    
    def _check_pgvector_availability(self):
        """pgvector拡張機能の利用可能性をチェック"""
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # pgvector拡張機能の確認
                    cur.execute("""
                        SELECT EXISTS(
                            SELECT 1 FROM pg_extension WHERE extname = 'vector'
                        ) as pgvector_installed
                    """)
                    result = cur.fetchone()
                    self.pgvector_available = result['pgvector_installed'] if result else False
                    
                    if self.pgvector_available:
                        logger.info("✅ pgvector拡張機能が利用可能です")
                    else:
                        logger.warning("⚠️ pgvector拡張機能が無効です。フォールバック検索を使用します")
                        
        except Exception as e:
            logger.error(f"❌ pgvector確認エラー: {e}")
            self.pgvector_available = False
    
    def enable_pgvector_extension(self):
        """pgvector拡張機能を有効化"""
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # pgvector拡張機能を有効化
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    conn.commit()
                    
                    # 確認
                    cur.execute("""
                        SELECT EXISTS(
                            SELECT 1 FROM pg_extension WHERE extname = 'vector'
                        ) as pgvector_installed
                    """)
                    result = cur.fetchone()
                    self.pgvector_available = result['pgvector_installed'] if result else False
                    
                    if self.pgvector_available:
                        logger.info("✅ pgvector拡張機能を有効化しました")
                        return True
                    else:
                        logger.error("❌ pgvector拡張機能の有効化に失敗しました")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ pgvector有効化エラー: {e}")
            return False
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """クエリの埋め込みベクトルを生成"""
        try:
            logger.info(f"クエリの埋め込み生成中: {query[:50]}...")
            
            # Vertex AI使用
            if self.vertex_client:
                embedding_vector = self.vertex_client.generate_embedding(query)
                
                if embedding_vector and len(embedding_vector) > 0:
                    # 期待される次元数であることを確認
                    if len(embedding_vector) != self.expected_dimensions:
                        logger.warning(f"予期しない次元数: {len(embedding_vector)}次元（期待値: {self.expected_dimensions}次元）")
                    logger.info(f"埋め込み生成完了: {len(embedding_vector)}次元")
                    return embedding_vector
                else:
                    logger.error("埋め込み生成に失敗しました")
                    return []
            else:
                logger.error("Vertex AI クライアントが利用できません")
                return []
        
        except Exception as e:
            logger.error(f"埋め込み生成エラー: {e}")
            return []
    
    def _cosine_similarity_sql(self, query_vector: List[float]) -> str:
        """コサイン類似度計算のSQLを生成（pgvectorの有無に応じて）"""
        if self.pgvector_available:
            # pgvectorが利用可能な場合
            return "1 - (c.embedding <=> %s::vector)"
        else:
            # pgvectorが利用できない場合、手動でコサイン類似度を計算
            vector_str = ",".join(map(str, query_vector))
            return f"""
            (
                SELECT 
                    CASE 
                        WHEN norm_a * norm_b = 0 THEN 0
                        ELSE dot_product / (norm_a * norm_b)
                    END
                FROM (
                    SELECT 
                        (SELECT SUM(a.val * b.val) 
                         FROM unnest(ARRAY[{vector_str}]) WITH ORDINALITY a(val, idx)
                         JOIN unnest(string_to_array(trim(both '[]' from c.embedding::text), ',')::float[]) WITH ORDINALITY b(val, idx) 
                         ON a.idx = b.idx) as dot_product,
                        sqrt((SELECT SUM(a.val * a.val) FROM unnest(ARRAY[{vector_str}]) a(val))) as norm_a,
                        sqrt((SELECT SUM(b.val * b.val) FROM unnest(string_to_array(trim(both '[]' from c.embedding::text), ',')::float[]) b(val))) as norm_b
                ) calc
            )
            """
    
    def vector_similarity_search(self, query: str, company_id: str = None, limit: int = 5) -> List[Dict]:
        """ベクトル類似検索を実行（pgvector対応版）"""
        try:
            # クエリの埋め込み生成
            query_vector = self.generate_query_embedding(query)
            if not query_vector:
                logger.error("クエリの埋め込み生成に失敗")
                return []
            
            # データベース接続
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    if self.pgvector_available:
                        # pgvectorが利用可能な場合の高速検索
                        similarity_sql = "1 - (c.embedding <=> %s::vector)"
                        order_sql = "c.embedding <=> %s::vector"
                        params = [query_vector]
                    else:
                        # pgvectorが利用できない場合のフォールバック検索
                        logger.warning("⚠️ pgvectorが無効のため、フォールバック検索を使用")
                        similarity_sql = """
                        CASE 
                            WHEN c.embedding IS NULL THEN 0
                            ELSE 0.5
                        END
                        """
                        order_sql = "RANDOM()"
                        params = []
                    
                    # ベクトル類似検索SQL
                    sql = f"""
                    SELECT
                        c.id as chunk_id,
                        c.doc_id as document_id,
                        c.chunk_index,
                        c.content as snippet,
                        ds.name,
                        ds.special,
                        ds.type,
                        {similarity_sql} as similarity_score
                    FROM chunks c
                    LEFT JOIN document_sources ds ON ds.id = c.doc_id
                    WHERE c.embedding IS NOT NULL
                    """
                    
                    # 会社IDフィルタ
                    if company_id:
                        sql += " AND c.company_id = %s"
                        params.append(company_id)
                        logger.info(f"🔍 会社IDフィルタ適用: {company_id}")
                    
                    # ソートと制限
                    sql += f" ORDER BY {order_sql} LIMIT %s"
                    if self.pgvector_available:
                        params.extend([query_vector, limit])
                    else:
                        params.append(limit)
                    
                    logger.info(f"ベクトル検索実行中... (limit: {limit})")
                    logger.info(f"使用テーブル: chunks, pgvector: {'有効' if self.pgvector_available else '無効'}")
                    
                    cur.execute(sql, params)
                    results = cur.fetchall()
                    
                    # 結果を辞書のリストに変換
                    search_results = []
                    for row in results:
                        search_results.append({
                            'chunk_id': row['chunk_id'],
                            'document_id': row['document_id'],
                            'chunk_index': row['chunk_index'],
                            'document_name': row['name'],
                            'document_type': row['type'],
                            'special': row['special'],
                            'snippet': row['snippet'],
                            'similarity_score': float(row['similarity_score']),
                            'search_type': 'vector_chunks_pgvector' if self.pgvector_available else 'vector_chunks_fallback'
                        })
                    
                    logger.info(f"✅ ベクトル検索完了: {len(search_results)}件の結果")
                    
                    # デバッグ: 上位3件の類似度を表示
                    for i, result in enumerate(search_results[:3]):
                        logger.info(f"  {i+1}. {result['document_name']} [チャンク{result['chunk_index']}] 類似度: {result['similarity_score']:.3f}")
                    
                    return search_results
        
        except Exception as e:
            logger.error(f"❌ ベクトル検索エラー: {e}")
            import traceback
            logger.error(f"詳細エラー: {traceback.format_exc()}")
            
            # pgvectorエラーの場合、拡張機能の有効化を試行
            if "operator does not exist: vector" in str(e):
                logger.info("🔧 pgvector拡張機能の有効化を試行中...")
                if self.enable_pgvector_extension():
                    logger.info("🔄 pgvector有効化後、検索を再試行中...")
                    return self.vector_similarity_search(query, company_id, limit)
            
            return []
    
    def get_document_content_by_similarity(self, query: str, company_id: str = None, max_results: int = 10) -> str:
        """類似度に基づいてドキュメントの内容を取得"""
        try:
            # ベクトル検索実行
            search_results = self.vector_similarity_search(query, company_id, limit=max_results)
            
            if not search_results:
                logger.warning("関連するドキュメントが見つかりませんでした")
                return ""
            
            # 結果を組み立て
            relevant_content = []
            total_length = 0
            max_total_length = 50000
            
            logger.info(f"類似度順に{len(search_results)}件のチャンクを処理中...")
            
            for i, result in enumerate(search_results):
                similarity = result['similarity_score']
                snippet = result['snippet'] or ""
                
                # チャンク情報を含むログ
                logger.info(f"  {i+1}. {result['document_name']} [チャンク{result['chunk_index']}] (類似度: {similarity:.3f})")
                
                # 類似度閾値（pgvectorの有無に応じて調整）
                threshold = 0.02 if self.pgvector_available else 0.1
                if similarity < threshold:
                    logger.info(f"    - 類似度が低いため除外 ({similarity:.3f} < {threshold})")
                    continue
                
                # スニペットを追加
                if snippet and len(snippet.strip()) > 0:
                    content_piece = f"\n=== {result['document_name']} - チャンク{result['chunk_index']} (類似度: {similarity:.3f}) ===\n{snippet}\n"
                    
                    if total_length + len(content_piece) <= max_total_length:
                        relevant_content.append(content_piece)
                        total_length += len(content_piece)
                        logger.info(f"    - 追加完了 ({len(content_piece)}文字)")
                    else:
                        logger.info(f"    - 文字数制限により除外")
                        break
                else:
                    logger.info(f"    - 空のコンテンツのためスキップ")
            
            final_content = "\n".join(relevant_content)
            logger.info(f"✅ 最終的な関連コンテンツ: {len(final_content)}文字")
            
            return final_content
        
        except Exception as e:
            logger.error(f"❌ ドキュメント内容取得エラー: {e}")
            import traceback
            logger.error(f"詳細エラー: {traceback.format_exc()}")
            return ""

def vector_search_available() -> bool:
    """ベクトル検索が利用可能かチェック"""
    try:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        return bool(api_key and supabase_url and supabase_key)
    except Exception:
        return False

# グローバルインスタンス（オプション）
_vector_search_instance = None

def get_vector_search_instance() -> Optional[VectorSearchSystem]:
    """ベクトル検索インスタンスを取得（シングルトンパターン）"""
    global _vector_search_instance
    
    if _vector_search_instance is None and vector_search_available():
        try:
            _vector_search_instance = VectorSearchSystem()
            logger.info("✅ ベクトル検索システム初期化完了")
        except Exception as e:
            logger.error(f"❌ ベクトル検索システム初期化エラー: {e}")
            return None
    
    return _vector_search_instance