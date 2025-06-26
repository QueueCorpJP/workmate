"""
ベクトル検索モジュール
Gemini Embeddingを使用した類似検索機能を提供
"""

import os
import logging
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
import google.generativeai as genai
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
        model_name = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
        
        # モデル名が正しい形式かチェックし、必要に応じて修正
        if not model_name.startswith(("models/", "tunedModels/")):
            if model_name in ["gemini-embedding-exp-03-07", "text-embedding-004"]:
                model_name = f"models/{model_name}"
            else:
                model_name = "models/text-embedding-004"  # デフォルトにフォールバック
        
        self.model = model_name
        self.db_url = self._get_db_url()
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
        
        # Gemini APIクライアントの初期化
        genai.configure(api_key=self.api_key)
        
        logger.info(f"✅ ベクトル検索システム初期化: モデル={self.model}")
        
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
            response = genai.embed_content(
                model=self.model,
                content=query
            )
            
            # レスポンスからエンベディングベクトルを取得
            embedding_vector = None
            
            if isinstance(response, dict) and 'embedding' in response:
                embedding_vector = response['embedding']
            elif hasattr(response, 'embedding') and response.embedding:
                embedding_vector = response.embedding
            else:
                logger.error(f"予期しないレスポンス形式: {type(response)}")
                return []
            
            if embedding_vector and len(embedding_vector) > 0:
                # 3072次元のベクトルをそのまま使用（次元削減なし）
                logger.info(f"埋め込み生成完了: {len(embedding_vector)}次元")
                return embedding_vector
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
        """ベクトル類似検索を実行（chunksテーブル対応版）"""
        try:
            # クエリの埋め込み生成
            query_vector = self.generate_query_embedding(query)
            if not query_vector:
                logger.error("クエリの埋め込み生成に失敗")
                return []
            
            # データベース接続
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # 新しいchunksテーブルを使用したベクトル類似検索SQL
                    sql = """
                    SELECT
                        c.id as chunk_id,
                        c.doc_id as document_id,
                        c.chunk_index,
                        c.content as snippet,
                        ds.name,
                        ds.special,
                        ds.type,
                        1 - (c.embedding <=> %s) as similarity_score
                    FROM chunks c
                    LEFT JOIN document_sources ds ON ds.id = c.doc_id
                    WHERE c.embedding IS NOT NULL
                    """
                    
                    params = [query_vector]
                    
                    # 会社IDフィルタ（有効化）
                    if company_id:
                        sql += " AND c.company_id = %s"
                        params.append(company_id)
                        logger.info(f"🔍 会社IDフィルタ適用: {company_id}")
                    else:
                        logger.info(f"🔍 会社IDフィルタなし（全データ検索）")
                    
                    # 類似度順でソート
                    sql += " ORDER BY c.embedding <=> %s LIMIT %s"
                    params.extend([query_vector, limit])
                    
                    logger.info(f"ベクトル検索実行中... (limit: {limit})")
                    logger.info(f"使用テーブル: chunks")
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
                            'search_type': 'vector_chunks'
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
            return []
    
    def get_document_content_by_similarity(self, query: str, company_id: str = None, max_results: int = 10) -> str:
        """類似度に基づいてドキュメントの内容を取得（chunksテーブル対応版）"""
        try:
            # ベクトル検索実行
            search_results = self.vector_similarity_search(query, company_id, limit=max_results)
            
            if not search_results:
                logger.warning("関連するドキュメントが見つかりませんでした")
                return ""
            
            # 結果を組み立て
            relevant_content = []
            total_length = 0
            max_total_length = 50000  # 最大文字数制限を拡大（15000 → 50000）
            
            logger.info(f"類似度順に{len(search_results)}件のチャンクを処理中...")
            
            for i, result in enumerate(search_results):
                doc_id = result['document_id']
                chunk_id = result['chunk_id']
                chunk_index = result.get('chunk_index', 'N/A')
                similarity = result['similarity_score']
                snippet = result['snippet'] or ""
                
                # チャンク情報を含むログ
                logger.info(f"  {i+1}. {result['document_name']} [チャンク{chunk_index}] (類似度: {similarity:.3f})")
                
                # 類似度閾値を緩和（0.05 → 0.02）
                if similarity < 0.02:
                    logger.info(f"    - 類似度が低いため除外 ({similarity:.3f} < 0.02)")
                    continue
                
                # スニペットを追加
                if snippet and len(snippet.strip()) > 0:
                    content_piece = f"\n=== {result['document_name']} - チャンク{chunk_index} (類似度: {similarity:.3f}) ===\n{snippet}\n"
                    
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