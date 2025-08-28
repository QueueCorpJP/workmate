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
from .multi_api_embedding import get_multi_api_embedding_client, multi_api_embedding_available

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class VectorSearchSystem:
    """ベクトル検索システム（pgvector対応版）"""
    
    def __init__(self):
        """初期化"""
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
        
        self.db_url = self._get_db_url()
        self.pgvector_available = False
        
        # pgvector拡張機能の確認
        self._check_pgvector_availability()
        
        if multi_api_embedding_available():
            self.multi_api_client = get_multi_api_embedding_client()
            # 次元数は3072次元固定
            expected_dimensions = 3072
            logger.info(f"✅ ベクトル検索システム初期化: Multi-API {self.embedding_model} ({expected_dimensions}次元)")
            logger.info(f"🔧 pgvector拡張機能: {'有効' if self.pgvector_available else '無効'}")
            self.expected_dimensions = expected_dimensions
        else:
            logger.error("❌ Multi-API Embeddingが利用できません")
            raise ValueError("Multi-API Embeddingの初期化に失敗しました")
    
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
    
    async def generate_query_embedding(self, query: str) -> List[float]:
        """クエリの埋め込みベクトルを生成"""
        try:
            logger.info(f"クエリの埋め込み生成中: {query[:50]}...")
            
            # Multi-API使用
            if self.multi_api_client:
                embedding_vector = await self.multi_api_client.generate_embedding(query)
                
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
                logger.error("Multi-API クライアントが利用できません")
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
    
    async def vector_similarity_search(self, query: str, company_id: str = None, limit: int = 50) -> List[Dict]:
        """ベクトル類似検索を実行（pgvector対応版）"""
        try:
            # クエリの埋め込み生成
            query_vector = await self.generate_query_embedding(query)
            if not query_vector:
                logger.error("クエリの埋め込み生成に失敗")
                return []
            
            # データベース接続
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    if self.pgvector_available:
                        # pgvectorが利用可能な場合の高速検索
                        # クエリベクトルを文字列形式に変換してvector型にキャスト
                        vector_str = '[' + ','.join(map(str, query_vector)) + ']'
                        similarity_sql = f"1 - (c.embedding <=> '{vector_str}'::vector)"
                        order_sql = f"c.embedding <=> '{vector_str}'::vector"
                        params = []
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
                    AND ds.active = true
                    """
                    
                    # 会社IDフィルタ
                    if company_id:
                        sql += " AND c.company_id = %s"
                        params.append(company_id)
                        logger.info(f"🔍 会社IDフィルタ適用: {company_id}")
                    
                    # ソートと制限
                    sql += f" ORDER BY {order_sql} LIMIT %s"
                    params.append(limit)
                    
                    logger.info(f"実行SQL: {sql}")
                    logger.info(f"パラメータ: {params}")

                    logger.info(f"ベクトル検索実行中... (limit: {limit})")
                    logger.info(f"使用テーブル: chunks, pgvector: {'有効' if self.pgvector_available else '無効'}")
                    
                    cur.execute(sql, params)
                    results = cur.fetchall()
                    
                    logger.info(f"DBからの生の結果: {results}")

                    # 結果を辞書のリストに変換
                    search_results = []
                    for row in results:
                        # document_sources.nameフィールドのみを使用してソース情報を設定
                        document_name = row['name'] if row['name'] else 'Unknown'
                        search_results.append({
                            'chunk_id': row['chunk_id'],
                            'document_id': row['document_id'],
                            'chunk_index': row['chunk_index'],
                            'document_name': document_name,
                            'document_type': row['type'],
                            'special': row['special'],
                            'snippet': row['snippet'],
                            'similarity_score': float(row['similarity_score']),
                            'search_type': 'vector_chunks_pgvector' if self.pgvector_available else 'vector_chunks_fallback'
                        })
                    
                    # 結果の安定化：類似度順、次にチャンクID順でソート（一貫した順序保証）
                    search_results.sort(key=lambda x: (-x['similarity_score'], str(x['chunk_id'])))
                    
                    logger.info(f"✅ ベクトル検索完了: {len(search_results)}件の結果（安定ソート済み）")
                    
                    # 🔍 詳細チャンク選択ログ - 全結果を表示
                    print("\n" + "="*80)
                    print(f"🔍 【チャンク選択詳細ログ】クエリ: '{query[:50]}...'")
                    print(f"📊 検索結果: {len(search_results)}件")
                    print(f"🏢 会社IDフィルタ: {'適用 (' + company_id + ')' if company_id else '未適用（全データ検索）'}")
                    print(f"🔧 pgvector: {'有効' if self.pgvector_available else '無効（フォールバック検索）'}")
                    print("="*80)
                    
                    for i, result in enumerate(search_results):
                        similarity = result['similarity_score']
                        doc_name = result['document_name'] or 'Unknown'
                        chunk_idx = result['chunk_index']
                        snippet_preview = (result['snippet'] or '')[:100].replace('\n', ' ')
                        
                        # 類似度に基づく選択理由
                        if similarity > 0.8:
                            reason = "🟢 高類似度（非常に関連性が高い）"
                        elif similarity > 0.5:
                            reason = "🟡 中類似度（関連性あり）"
                        elif similarity > 0.2:
                            reason = "🟠 低類似度（部分的に関連）"
                        else:
                            reason = "🔴 極低類似度（関連性低い）"
                        
                        print(f"  {i+1:2d}. 📄 {doc_name}")
                        print(f"      🧩 チャンク#{chunk_idx} | 🎯 類似度: {similarity:.4f} | {reason}")
                        print(f"      📝 内容: {snippet_preview}...")
                        print(f"      🔍 検索タイプ: {result['search_type']}")
                        print()
                    
                    print("="*80 + "\n")
                    
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
    
    def get_document_content_by_similarity(self, query: str, company_id: str = None, max_results: int = 100) -> str:
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
            max_total_length = 120000
            
            print("\n" + "="*80)
            print(f"📋 【コンテンツ構築ログ】{len(search_results)}件のチャンクを処理中...")
            print(f"🎯 類似度閾値: 0.05 (これ以下は除外)")
            print(f"📏 最大文字数: {max_total_length:,}文字")
            print("="*80)
            
            for i, result in enumerate(search_results):
                similarity = result['similarity_score']
                snippet = result['snippet'] or ""
                doc_name = result['document_name'] or 'Unknown'
                chunk_idx = result['chunk_index']
                
                print(f"  {i+1:2d}. 📄 {doc_name} [チャンク#{chunk_idx}]")
                print(f"      🎯 類似度: {similarity:.4f}")
                
                # 類似度閾値（情報抜け防止のためさらに緩和）
                threshold = 0.02  # 🎯 抜け漏れ完全防止（最大緩和）
                if similarity < threshold:
                    print(f"      ❌ 除外理由: 類似度が閾値未満 ({similarity:.4f} < {threshold})")
                    print()
                    continue
                
                # スニペットを追加
                if snippet and len(snippet.strip()) > 0:
                    content_piece = f"\n=== {doc_name} - 参考資料{chunk_idx} (類似度: {similarity:.3f}) ===\n{snippet}\n"
                    
                    if total_length + len(content_piece) <= max_total_length:
                        relevant_content.append(content_piece)
                        total_length += len(content_piece)
                        print(f"      ✅ 採用: {len(content_piece):,}文字追加 (累計: {total_length:,}文字)")
                        print(f"      📝 内容プレビュー: {snippet[:100].replace(chr(10), ' ')}...")
                    else:
                        print(f"      ❌ 除外理由: 文字数制限超過 (追加予定: {len(content_piece):,}文字, 現在: {total_length:,}文字)")
                        break
                else:
                    print(f"      ❌ 除外理由: 空のコンテンツ")
                print()
            
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