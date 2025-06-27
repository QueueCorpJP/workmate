"""
強化されたベクトル検索システム
- 適応的類似度閾値
- インテリジェントな結果フィルタリング
- 改善されたスコアリングアルゴリズム
- 文脈を考慮したチャンク統合
"""

import os
import logging
import asyncio
from typing import List, Dict, Tuple, Optional, Set
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from datetime import datetime
import re
from dataclasses import dataclass
from collections import defaultdict

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class EnhancedSearchResult:
    """強化された検索結果"""
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    similarity_score: float
    relevance_score: float  # 総合関連度スコア
    chunk_index: int
    document_type: str
    search_method: str
    context_bonus: float = 0.0
    quality_score: float = 0.0
    metadata: Dict = None

class EnhancedVectorSearchSystem:
    """強化されたベクトル検索システム"""
    
    def __init__(self):
        """初期化"""
        self.use_vertex_ai = os.getenv("USE_VERTEX_AI", "true").lower() == "true"
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-multilingual-embedding-002")
        self.expected_dimensions = 768 if "text-multilingual-embedding-002" in self.embedding_model else 3072
        
        self.db_url = self._get_db_url()
        self.pgvector_available = False
        
        # 検索品質パラメータ
        self.min_similarity_threshold = 0.3  # 最小類似度閾値を上げる
        self.adaptive_threshold_enabled = True
        self.context_window_size = 3  # 前後のチャンクを考慮
        self.quality_weight = 0.3
        self.similarity_weight = 0.4
        self.context_weight = 0.3
        
        # pgvector拡張機能の確認
        self._check_pgvector_availability()
        
        # Vertex AI Embeddingクライアントの初期化
        if self.use_vertex_ai:
            from .vertex_ai_embedding import get_vertex_ai_embedding_client, vertex_ai_embedding_available
            if vertex_ai_embedding_available():
                self.vertex_client = get_vertex_ai_embedding_client()
                logger.info(f"✅ 強化ベクトル検索システム初期化: {self.embedding_model} ({self.expected_dimensions}次元)")
            else:
                logger.error("❌ Vertex AI Embeddingが利用できません")
                raise ValueError("Vertex AI Embeddingの初期化に失敗しました")
        else:
            self.vertex_client = None
    
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
    
    def _check_pgvector_availability(self):
        """pgvector拡張機能の利用可能性をチェック"""
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
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
                        logger.warning("⚠️ pgvector拡張機能が無効です")
                        
        except Exception as e:
            logger.error(f"❌ pgvector確認エラー: {e}")
            self.pgvector_available = False
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """クエリの埋め込みベクトルを生成"""
        try:
            logger.info(f"🧠 クエリの埋め込み生成中: {query[:50]}...")
            
            if self.vertex_client:
                embedding_vector = self.vertex_client.generate_embedding(query)
                
                if embedding_vector and len(embedding_vector) > 0:
                    if len(embedding_vector) != self.expected_dimensions:
                        logger.warning(f"予期しない次元数: {len(embedding_vector)}次元（期待値: {self.expected_dimensions}次元）")
                    logger.info(f"✅ 埋め込み生成完了: {len(embedding_vector)}次元")
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
    
    def calculate_adaptive_threshold(self, similarities: List[float]) -> float:
        """適応的類似度閾値を計算"""
        if not similarities or not self.adaptive_threshold_enabled:
            return self.min_similarity_threshold
        
        # 統計的分析による閾値計算
        similarities = sorted(similarities, reverse=True)
        
        if len(similarities) < 3:
            return self.min_similarity_threshold
        
        # 上位25%の平均から動的閾値を計算
        top_quarter = similarities[:max(1, len(similarities) // 4)]
        avg_top = sum(top_quarter) / len(top_quarter)
        
        # 最小閾値と動的閾値の最大値を使用
        adaptive_threshold = max(self.min_similarity_threshold, avg_top * 0.6)
        
        logger.info(f"📊 適応的閾値: {adaptive_threshold:.3f} (最小: {self.min_similarity_threshold}, 上位平均: {avg_top:.3f})")
        return adaptive_threshold
    
    def calculate_quality_score(self, content: str, query: str) -> float:
        """コンテンツの品質スコアを計算"""
        if not content or not query:
            return 0.0
        
        quality_score = 0.0
        content_lower = content.lower()
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        # 1. 長さによる品質評価
        content_length = len(content)
        if 100 <= content_length <= 2000:
            quality_score += 0.3
        elif 50 <= content_length <= 3000:
            quality_score += 0.2
        elif content_length > 3000:
            quality_score += 0.1
        
        # 2. クエリ用語の含有率
        content_terms = set(content_lower.split())
        term_overlap = len(query_terms & content_terms)
        term_coverage = term_overlap / len(query_terms) if query_terms else 0
        quality_score += term_coverage * 0.4
        
        # 3. 構造的要素の存在
        structural_patterns = [
            r'\d+\.',  # 番号付きリスト
            r'・',     # 箇条書き
            r'【.*?】', # セクション見出し
            r'■.*?■', # 強調見出し
            r'手順|方法|やり方|プロセス',  # 手順関連
            r'連絡先|電話|メール|問い合わせ',  # 連絡先情報
        ]
        
        for pattern in structural_patterns:
            if re.search(pattern, content):
                quality_score += 0.05
        
        # 4. 情報密度（句読点の適切な使用）
        sentences = content.split('。')
        if len(sentences) > 1:
            avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
            if 20 <= avg_sentence_length <= 100:
                quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    def get_context_chunks(self, target_chunk_index: int, document_id: str, company_id: str = None) -> List[Dict]:
        """前後のチャンクを取得してコンテキストを構築"""
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # 前後のチャンクを取得
                    sql = """
                    SELECT 
                        c.id,
                        c.chunk_index,
                        c.content,
                        c.doc_id
                    FROM chunks c
                    WHERE c.doc_id = %s
                      AND c.chunk_index BETWEEN %s AND %s
                      AND c.content IS NOT NULL
                    """
                    
                    params = [
                        document_id,
                        max(0, target_chunk_index - self.context_window_size),
                        target_chunk_index + self.context_window_size
                    ]
                    
                    if company_id:
                        sql += " AND c.company_id = %s"
                        params.append(company_id)
                    
                    sql += " ORDER BY c.chunk_index"
                    
                    cur.execute(sql, params)
                    results = cur.fetchall()
                    
                    return [dict(row) for row in results]
        
        except Exception as e:
            logger.error(f"コンテキストチャンク取得エラー: {e}")
            return []
    
    def calculate_context_bonus(self, target_chunk: Dict, context_chunks: List[Dict], query: str) -> float:
        """コンテキストボーナススコアを計算"""
        if not context_chunks or len(context_chunks) <= 1:
            return 0.0
        
        context_bonus = 0.0
        query_terms = set(query.lower().split())
        
        # 前後のチャンクでのクエリ用語の出現をチェック
        for chunk in context_chunks:
            if chunk['id'] != target_chunk.get('chunk_id', ''):
                chunk_terms = set(chunk['content'].lower().split())
                term_overlap = len(query_terms & chunk_terms)
                if term_overlap > 0:
                    context_bonus += 0.1 * (term_overlap / len(query_terms))
        
        # 連続性ボーナス（前後のチャンクが連続している場合）
        chunk_indices = sorted([chunk['chunk_index'] for chunk in context_chunks])
        consecutive_count = 0
        for i in range(1, len(chunk_indices)):
            if chunk_indices[i] - chunk_indices[i-1] == 1:
                consecutive_count += 1
        
        if consecutive_count > 0:
            context_bonus += 0.05 * consecutive_count
        
        return min(context_bonus, 0.3)  # 最大30%のボーナス
    
    async def enhanced_vector_search(self, query: str, company_id: str = None, max_results: int = 15) -> List[EnhancedSearchResult]:
        """強化されたベクトル検索を実行"""
        try:
            logger.info(f"🔍 強化ベクトル検索開始: '{query[:50]}...'")
            
            # クエリの埋め込み生成
            query_vector = self.generate_query_embedding(query)
            if not query_vector:
                logger.error("クエリの埋め込み生成に失敗")
                return []
            
            # 初期検索（より多くの候補を取得）
            initial_results = await self._execute_initial_search(query_vector, company_id, max_results * 3)
            
            if not initial_results:
                logger.warning("初期検索で結果が見つかりませんでした")
                return []
            
            # 適応的閾値の計算
            similarities = [r['similarity_score'] for r in initial_results]
            adaptive_threshold = self.calculate_adaptive_threshold(similarities)
            
            # 結果の強化処理
            enhanced_results = []
            for result in initial_results:
                if result['similarity_score'] >= adaptive_threshold:
                    enhanced_result = await self._enhance_search_result(result, query, company_id)
                    if enhanced_result:
                        enhanced_results.append(enhanced_result)
            
            # 総合スコアによるソート
            enhanced_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # 重複除去と最終選択
            final_results = self._deduplicate_and_select(enhanced_results, max_results)
            
            logger.info(f"✅ 強化ベクトル検索完了: {len(final_results)}件の高品質結果")
            
            # デバッグ情報
            for i, result in enumerate(final_results[:5]):
                logger.info(f"  {i+1}. {result.document_name} [チャンク{result.chunk_index}]")
                logger.info(f"     類似度: {result.similarity_score:.3f}, 関連度: {result.relevance_score:.3f}")
                logger.info(f"     品質: {result.quality_score:.3f}, コンテキスト: {result.context_bonus:.3f}")
            
            return final_results
        
        except Exception as e:
            logger.error(f"❌ 強化ベクトル検索エラー: {e}")
            import traceback
            logger.error(f"詳細エラー: {traceback.format_exc()}")
            return []
    
    async def _execute_initial_search(self, query_vector: List[float], company_id: str = None, limit: int = 45) -> List[Dict]:
        """初期ベクトル検索を実行"""
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    if self.pgvector_available:
                        # pgvectorを使用した高速検索
                        sql = """
                        SELECT
                            c.id as chunk_id,
                            c.doc_id as document_id,
                            c.chunk_index,
                            c.content as snippet,
                            ds.name,
                            ds.type,
                            ds.special,
                            1 - (c.embedding <=> %s::vector) as similarity_score
                        FROM chunks c
                        LEFT JOIN document_sources ds ON ds.id = c.doc_id
                        WHERE c.embedding IS NOT NULL
                        """
                        
                        params = [query_vector]
                        
                        if company_id:
                            sql += " AND c.company_id = %s"
                            params.append(company_id)
                        
                        sql += " ORDER BY c.embedding <=> %s::vector LIMIT %s"
                        params.extend([query_vector, limit])
                        
                    else:
                        # フォールバック検索
                        logger.warning("⚠️ pgvectorが無効のため、フォールバック検索を使用")
                        sql = """
                        SELECT
                            c.id as chunk_id,
                            c.doc_id as document_id,
                            c.chunk_index,
                            c.content as snippet,
                            ds.name,
                            ds.type,
                            ds.special,
                            0.5 as similarity_score
                        FROM chunks c
                        LEFT JOIN document_sources ds ON ds.id = c.doc_id
                        WHERE c.embedding IS NOT NULL
                        """
                        
                        params = []
                        
                        if company_id:
                            sql += " AND c.company_id = %s"
                            params.append(company_id)
                        
                        sql += " ORDER BY RANDOM() LIMIT %s"
                        params.append(limit)
                    
                    cur.execute(sql, params)
                    results = cur.fetchall()
                    
                    return [dict(row) for row in results]
        
        except Exception as e:
            logger.error(f"初期検索実行エラー: {e}")
            return []
    
    async def _enhance_search_result(self, result: Dict, query: str, company_id: str = None) -> Optional[EnhancedSearchResult]:
        """検索結果を強化"""
        try:
            # 品質スコアの計算
            quality_score = self.calculate_quality_score(result['snippet'] or '', query)
            
            # コンテキストチャンクの取得
            context_chunks = self.get_context_chunks(
                result['chunk_index'], 
                result['document_id'], 
                company_id
            )
            
            # コンテキストボーナスの計算
            context_bonus = self.calculate_context_bonus(result, context_chunks, query)
            
            # 総合関連度スコアの計算
            relevance_score = (
                result['similarity_score'] * self.similarity_weight +
                quality_score * self.quality_weight +
                context_bonus * self.context_weight
            )
            
            return EnhancedSearchResult(
                chunk_id=result['chunk_id'],
                document_id=result['document_id'],
                document_name=result['name'] or 'Unknown',
                content=result['snippet'] or '',
                similarity_score=result['similarity_score'],
                relevance_score=relevance_score,
                chunk_index=result['chunk_index'],
                document_type=result['type'] or 'document',
                search_method='enhanced_vector',
                context_bonus=context_bonus,
                quality_score=quality_score,
                metadata={
                    'special': result.get('special'),
                    'context_chunks_count': len(context_chunks)
                }
            )
        
        except Exception as e:
            logger.error(f"検索結果強化エラー: {e}")
            return None
    
    def _deduplicate_and_select(self, results: List[EnhancedSearchResult], max_results: int) -> List[EnhancedSearchResult]:
        """重複除去と最終選択"""
        seen_content = set()
        seen_documents = defaultdict(int)
        final_results = []
        
        for result in results:
            # コンテンツの重複チェック（先頭100文字）
            content_key = result.content[:100].strip()
            if content_key in seen_content:
                continue
            
            # 同一文書からの結果数制限（最大3件）
            if seen_documents[result.document_id] >= 3:
                continue
            
            # 最小品質閾値チェック
            if result.quality_score < 0.2:
                continue
            
            seen_content.add(content_key)
            seen_documents[result.document_id] += 1
            final_results.append(result)
            
            if len(final_results) >= max_results:
                break
        
        return final_results
    
    async def get_enhanced_document_content(self, query: str, company_id: str = None, max_results: int = 10) -> str:
        """強化された文書内容取得"""
        try:
            # 強化ベクトル検索実行
            search_results = await self.enhanced_vector_search(query, company_id, max_results)
            
            if not search_results:
                logger.warning("関連するドキュメントが見つかりませんでした")
                return ""
            
            # 結果を組み立て
            relevant_content = []
            total_length = 0
            max_total_length = 50000
            
            logger.info(f"📊 強化検索結果を処理中: {len(search_results)}件")
            
            for i, result in enumerate(search_results):
                logger.info(f"  {i+1}. {result.document_name} [チャンク{result.chunk_index}]")
                logger.info(f"     関連度: {result.relevance_score:.3f} (類似度: {result.similarity_score:.3f})")
                
                if result.content and len(result.content.strip()) > 0:
                    content_piece = f"\n=== {result.document_name} - チャンク{result.chunk_index} (関連度: {result.relevance_score:.3f}) ===\n{result.content}\n"
                    
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
            logger.error(f"❌ 強化文書内容取得エラー: {e}")
            import traceback
            logger.error(f"詳細エラー: {traceback.format_exc()}")
            return ""

# グローバルインスタンス
_enhanced_vector_search_instance = None

def get_enhanced_vector_search_instance() -> Optional[EnhancedVectorSearchSystem]:
    """強化ベクトル検索インスタンスを取得（シングルトンパターン）"""
    global _enhanced_vector_search_instance
    
    if _enhanced_vector_search_instance is None:
        try:
            _enhanced_vector_search_instance = EnhancedVectorSearchSystem()
            logger.info("✅ 強化ベクトル検索システム初期化完了")
        except Exception as e:
            logger.error(f"❌ 強化ベクトル検索システム初期化エラー: {e}")
            return None
    
    return _enhanced_vector_search_instance

def enhanced_vector_search_available() -> bool:
    """強化ベクトル検索が利用可能かチェック"""
    try:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        use_vertex_ai = os.getenv("USE_VERTEX_AI", "true").lower() == "true"
        
        return bool(api_key and supabase_url and supabase_key and use_vertex_ai)
    except Exception:
        return False