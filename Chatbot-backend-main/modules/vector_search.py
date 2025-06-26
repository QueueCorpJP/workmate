"""
ベクトル検索モジュール
Gemini Embeddingを使用した類似検索機能を提供
"""

import os
import logging
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
from google import genai
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class VectorSearchSystem:
    """ベクトル検索システム"""
    
    def __init__(self):
        """初期化"""
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-exp-03-07")
        self.db_url = self._get_db_url()
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
        
        # Gemini APIクライアントの初期化
        self.client = genai.Client(api_key=self.api_key)
        
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
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """クエリの埋め込みベクトルを生成"""
        try:
            logger.info(f"クエリの埋め込み生成中: {query[:50]}...")
            response = self.client.models.embed_content(
                model=self.model, 
                contents=query
            )
            
            if response.embeddings and len(response.embeddings) > 0:
                # 3072次元のベクトルを取得
                full_embedding = response.embeddings[0].values
                # MRL（次元削減）: 3072 → 1536次元に削減
                embedding = full_embedding[:1536]
                logger.info(f"埋め込み生成完了 (元次元: {len(full_embedding)} → 削減後: {len(embedding)})")
                return embedding
            else:
                logger.error("埋め込み生成に失敗しました")
                return []
        
        except Exception as e:
            logger.error(f"埋め込み生成エラー: {e}")
            return []
    
    def _extract_original_doc_id(self, chunk_id: str) -> str:
        """チャンクIDから元のドキュメントIDを抽出"""
        # doc123_chunk_0 -> doc123
        if '_chunk_' in chunk_id:
            return chunk_id.split('_chunk_')[0]
        return chunk_id
    
    def vector_similarity_search(self, query: str, company_id: str = None, limit: int = 5) -> List[Dict]:
        """ベクトル類似検索を実行"""
        try:
            # クエリの埋め込み生成
            query_vector = self.generate_query_embedding(query)
            if not query_vector:
                logger.error("クエリの埋め込み生成に失敗")
                return []
            
            # データベース接続
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # ベクトル類似検索のSQL（チャンク対応版）
                    sql = """
                    SELECT 
                        de.document_id as chunk_id,
                        CASE 
                            WHEN de.document_id LIKE '%_chunk_%' THEN 
                                SPLIT_PART(de.document_id, '_chunk_', 1)
                            ELSE de.document_id
                        END as original_doc_id,
                        ds.name,
                        ds.special,
                        ds.type,
                        de.snippet,
                        1 - (de.embedding <=> %s) as similarity_score
                    FROM document_embeddings de
                    LEFT JOIN document_sources ds ON ds.id = CASE 
                        WHEN de.document_id LIKE '%_chunk_%' THEN 
                            SPLIT_PART(de.document_id, '_chunk_', 1)
                        ELSE de.document_id
                    END
                    WHERE de.embedding IS NOT NULL
                    """
                    
                    params = [query_vector]
                    
                    # 🔍 デバッグ: company_idフィルタを一時的に無効化
                    logger.info(f"🔍 デバッグ: company_idフィルタを無効化してテスト")
                    # if company_id:
                    #     sql += " AND ds.company_id = %s"
                    #     params.append(company_id)
                    
                    # 類似度順でソート
                    sql += " ORDER BY de.embedding <=> %s LIMIT %s"
                    params.extend([query_vector, limit])
                    
                    logger.info(f"ベクトル検索実行中... (limit: {limit})")
                    cur.execute(sql, params)
                    results = cur.fetchall()
                    
                    # 結果を辞書のリストに変換
                    search_results = []
                    for row in results:
                        search_results.append({
                            'chunk_id': row['chunk_id'],
                            'document_id': row['original_doc_id'],
                            'document_name': row['name'],
                            'document_type': row['type'],
                            'special': row['special'],
                            'snippet': row['snippet'],
                            'similarity_score': float(row['similarity_score']),
                            'search_type': 'vector'
                        })
                    
                    logger.info(f"ベクトル検索完了: {len(search_results)}件の結果")
                    return search_results
        
        except Exception as e:
            logger.error(f"ベクトル検索エラー: {e}")
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
            max_total_length = 15000  # 最大文字数制限
            
            logger.info(f"類似度順に{len(search_results)}件のドキュメントを処理中...")
            
            for i, result in enumerate(search_results):
                doc_id = result['document_id']
                chunk_id = result['chunk_id']
                similarity = result['similarity_score']
                snippet = result['snippet'] or ""
                
                # チャンク情報を含むログ
                if chunk_id != doc_id:
                    logger.info(f"  {i+1}. {result['document_name']} [チャンク: {chunk_id}] (類似度: {similarity:.3f})")
                else:
                    logger.info(f"  {i+1}. {result['document_name']} (類似度: {similarity:.3f})")
                
                # 🔍 デバッグ: 類似度閾値を大幅に緩和（0.3 → 0.05）
                if similarity < 0.05:
                    logger.info(f"    - 類似度が低いため除外 ({similarity:.3f} < 0.05)")
                    continue
                
                # スニペットを追加
                if snippet and len(snippet.strip()) > 0:
                    content_piece = f"\n=== {result['document_name']} (類似度: {similarity:.3f}) ===\n{snippet}\n"
                    
                    if total_length + len(content_piece) <= max_total_length:
                        relevant_content.append(content_piece)
                        total_length += len(content_piece)
                        logger.info(f"    - 追加完了 ({len(content_piece)}文字)")
                    else:
                        logger.info(f"    - 文字数制限により除外")
                        break
            
            final_content = "\n".join(relevant_content)
            logger.info(f"最終的な関連コンテンツ: {len(final_content)}文字")
            
            return final_content
        
        except Exception as e:
            logger.error(f"ドキュメント内容取得エラー: {e}")
            return ""

    def hybrid_search(self, query: str, company_id: str = None, max_results: int = 10) -> str:
        """ハイブリッド検索（ベクトル検索 + 既存検索の組み合わせ）"""
        try:
            logger.info(f"ハイブリッド検索開始: {query}")
            
            # ベクトル検索を実行
            vector_results = self.get_document_content_by_similarity(
                query, company_id, max_results
            )
            
            if vector_results:
                logger.info("✅ ベクトル検索で関連コンテンツを取得")
                return vector_results
            else:
                logger.warning("⚠️ ベクトル検索で結果が見つからず、フォールバック")
                # ベクトル検索で結果がない場合の代替処理
                return ""
        
        except Exception as e:
            logger.error(f"ハイブリッド検索エラー: {e}")
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