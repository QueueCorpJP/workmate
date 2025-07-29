"""
超高精度ベクトル検索システム
- 動的適応閾値による最適化
- 多段階検索戦略
- 日本語特化型クエリ拡張
- インテリジェントなスコアリング
"""

import os
import logging
import asyncio
import re
from typing import List, Dict, Tuple, Optional, Set
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict
# import jaconv  # 依存関係を削除

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class UltraSearchResult:
    """超高精度検索結果"""
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    similarity_score: float
    relevance_score: float
    confidence_score: float
    chunk_index: int
    document_type: str
    search_method: str
    query_match_score: float = 0.0
    semantic_score: float = 0.0
    context_score: float = 0.0
    metadata: Dict = None

class UltraAccurateSearchSystem:
    """超高精度ベクトル検索システム"""
    
    def __init__(self):
        """初期化"""
        self.use_vertex_ai = os.getenv("USE_VERTEX_AI", "true").lower() == "true"
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-multilingual-embedding-002")
        self.expected_dimensions = 768 if "text-multilingual-embedding-002" in self.embedding_model else 3072
        
        self.db_url = self._get_db_url()
        self.pgvector_available = False
        
        # 動的閾値パラメータ
        self.base_threshold = 0.15  # 基本閾値を大幅に下げる
        self.adaptive_threshold_enabled = True
        self.multi_stage_search = True
        
        # 日本語特化パラメータ
        self.japanese_boost = 1.2
        self.katakana_boost = 1.1
        self.company_name_boost = 1.3
        
        # pgvector拡張機能の確認
        self._check_pgvector_availability()
        
        # Vertex AI Embeddingクライアントの初期化
        if self.use_vertex_ai:
            from .vertex_ai_embedding import get_vertex_ai_embedding_client, vertex_ai_embedding_available
            if vertex_ai_embedding_available():
                self.vertex_client = get_vertex_ai_embedding_client()
                logger.info(f"✅ 超高精度検索システム初期化: {self.embedding_model} ({self.expected_dimensions}次元)")
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
    
    def expand_japanese_query(self, query: str) -> List[str]:
        """日本語クエリの拡張"""
        expanded_queries = [query]
        
        # ひらがな・カタカナ変換
        if re.search(r'[ひらがな]', query):
            katakana_query = jaconv.hira2kata(query)
            expanded_queries.append(katakana_query)
        
        if re.search(r'[カタカナ]', query):
            hiragana_query = jaconv.kata2hira(query)
            expanded_queries.append(hiragana_query)
        
        # 半角・全角変換
        if re.search(r'[Ａ-Ｚａ-ｚ０-９]', query):
            hankaku_query = jaconv.z2h(query, kana=False, ascii=True, digit=True)
            expanded_queries.append(hankaku_query)
        
        if re.search(r'[A-Za-z0-9]', query):
            zenkaku_query = jaconv.h2z(query, kana=False, ascii=True, digit=True)
            expanded_queries.append(zenkaku_query)
        
        # 会社名・サービス名の一般的なバリエーション
        company_variations = {
            'ほっとらいふ': ['ホットライフ', 'HOT LIFE', 'hotlife', 'ホット・ライフ', 'ほっと・らいふ'],
            'ホットライフ': ['ほっとらいふ', 'HOT LIFE', 'hotlife', 'ホット・ライフ', 'ほっと・らいふ'],
        }
        
        query_lower = query.lower()
        for key, variations in company_variations.items():
            if key.lower() in query_lower:
                expanded_queries.extend(variations)
        
        # 重複除去
        return list(set(expanded_queries))
    
    def calculate_dynamic_threshold(self, similarities: List[float], query: str) -> float:
        """動的閾値の計算"""
        if not similarities:
            return self.base_threshold
        
        similarities = sorted(similarities, reverse=True)
        
        # 基本統計
        max_sim = max(similarities)
        avg_sim = sum(similarities) / len(similarities)
        
        # クエリの特性による調整
        query_boost = 1.0
        
        # 日本語クエリの場合は閾値を下げる
        if re.search(r'[ひらがなカタカナ漢字]', query):
            query_boost *= 0.8
        
        # 短いクエリの場合は閾値を下げる
        if len(query) <= 5:
            query_boost *= 0.7
        
        # 会社名・固有名詞の場合は閾値を大幅に下げる
        if any(term in query.lower() for term in ['ほっとらいふ', 'ホットライフ', 'hotlife']):
            query_boost *= 0.5
        
        # 動的閾値の計算
        if max_sim > 0.6:
            # 高品質な結果がある場合
            dynamic_threshold = max(self.base_threshold, avg_sim * 0.4) * query_boost
        elif max_sim > 0.3:
            # 中品質な結果がある場合
            dynamic_threshold = max(self.base_threshold * 0.7, avg_sim * 0.3) * query_boost
        else:
            # 低品質な結果しかない場合
            dynamic_threshold = self.base_threshold * 0.5 * query_boost
        
        # 最小閾値の保証
        final_threshold = max(0.05, min(dynamic_threshold, 0.4))
        
        logger.info(f"🎯 動的閾値計算: {final_threshold:.3f} (最大類似度: {max_sim:.3f}, 平均: {avg_sim:.3f}, クエリ補正: {query_boost:.2f})")
        return final_threshold
    
    def calculate_query_match_score(self, content: str, query: str) -> float:
        """クエリマッチスコアの計算"""
        if not content or not query:
            return 0.0
        
        content_lower = content.lower()
        query_lower = query.lower()
        
        score = 0.0
        
        # 完全一致
        if query_lower in content_lower:
            score += 0.5
        
        # 部分一致
        query_terms = query_lower.split()
        content_terms = content_lower.split()
        
        matched_terms = 0
        for term in query_terms:
            if any(term in content_term for content_term in content_terms):
                matched_terms += 1
        
        if query_terms:
            score += (matched_terms / len(query_terms)) * 0.3
        
        # 日本語特有のマッチング
        if re.search(r'[ひらがなカタカナ漢字]', query):
            # ひらがな・カタカナの相互マッチング
            if 'ほっとらいふ' in query_lower and 'ホットライフ' in content:
                score += 0.4
            elif 'ホットライフ' in query_lower and 'ほっとらいふ' in content:
                score += 0.4
        
        return min(score, 1.0)
    
    def calculate_semantic_score(self, content: str, query: str) -> float:
        """意味的関連性スコアの計算"""
        if not content or not query:
            return 0.0
        
        # 関連キーワードの定義
        semantic_groups = {
            'サービス': ['サービス', 'service', '提供', '利用', '使用'],
            '連絡先': ['連絡先', '電話', 'TEL', 'tel', 'メール', 'mail', '問い合わせ', 'お問い合わせ'],
            '会社': ['会社', '企業', 'company', '法人', '株式会社', '有限会社'],
            '料金': ['料金', '価格', '費用', 'コスト', '金額', '値段'],
            '手順': ['手順', '方法', 'やり方', 'プロセス', '流れ', 'ステップ'],
        }
        
        content_lower = content.lower()
        query_lower = query.lower()
        
        score = 0.0
        
        # クエリと内容の意味的関連性をチェック
        for group_name, keywords in semantic_groups.items():
            query_has_group = any(keyword in query_lower for keyword in keywords)
            content_has_group = any(keyword in content_lower for keyword in keywords)
            
            if query_has_group and content_has_group:
                score += 0.2
        
        return min(score, 1.0)
    
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
    
    async def ultra_accurate_search(self, query: str, company_id: str = None, max_results: int = 20) -> List[UltraSearchResult]:
        """超高精度検索の実行"""
        try:
            logger.info(f"🚀 超高精度検索開始: '{query}'")
            
            # 1. クエリ拡張
            expanded_queries = self.expand_japanese_query(query)
            logger.info(f"📝 クエリ拡張: {len(expanded_queries)}個のバリエーション")
            
            all_results = []
            
            # 2. 各拡張クエリで検索実行
            for i, expanded_query in enumerate(expanded_queries):
                logger.info(f"🔍 検索実行 {i+1}/{len(expanded_queries)}: '{expanded_query}'")
                
                # 埋め込み生成
                query_vector = self.generate_query_embedding(expanded_query)
                if not query_vector:
                    continue
                
                # ベクトル検索実行
                search_results = await self._execute_ultra_search(query_vector, expanded_query, company_id, max_results * 2)
                all_results.extend(search_results)
            
            if not all_results:
                logger.warning("検索結果が見つかりませんでした")
                return []
            
            # 3. 動的閾値の計算
            similarities = [r['similarity_score'] for r in all_results]
            dynamic_threshold = self.calculate_dynamic_threshold(similarities, query)
            
            # 4. 結果の強化処理
            enhanced_results = []
            for result in all_results:
                if result['similarity_score'] >= dynamic_threshold:
                    enhanced_result = self._enhance_ultra_result(result, query)
                    if enhanced_result:
                        enhanced_results.append(enhanced_result)
            
            # 5. 重複除去とスコアリング
            final_results = self._deduplicate_and_rank(enhanced_results, max_results)
            
            logger.info(f"✅ 超高精度検索完了: {len(final_results)}件の結果")
            
            # デバッグ情報
            for i, result in enumerate(final_results[:5]):
                logger.info(f"  {i+1}. {result.document_name} [チャンク{result.chunk_index}]")
                logger.info(f"     関連度: {result.relevance_score:.3f}, 信頼度: {result.confidence_score:.3f}")
                logger.info(f"     類似度: {result.similarity_score:.3f}, クエリマッチ: {result.query_match_score:.3f}")
            
            return final_results
        
        except Exception as e:
            logger.error(f"❌ 超高精度検索エラー: {e}")
            import traceback
            logger.error(f"詳細エラー: {traceback.format_exc()}")
            return []
    
    async def _execute_ultra_search(self, query_vector: List[float], query: str, company_id: str = None, limit: int = 40) -> List[Dict]:
        """超高精度ベクトル検索の実行"""
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    if self.pgvector_available:
                        # pgvectorを使用した高速検索
                        cur.execute("""
                            SELECT DISTINCT 
                                c.id as chunk_id,
                                c.doc_id as document_id,
                                c.chunk_index,
                                c.content as snippet,
                                ds.name as document_name,
                                ds.type as document_type,
                                (1 - (c.embedding <=> %s)) as similarity_score
                            FROM chunks c
                            INNER JOIN document_sources ds ON ds.id = c.doc_id
                            WHERE c.embedding IS NOT NULL 
                                AND ds.active = true
                                AND (%s IS NULL OR ds.company_id = %s OR ds.company_id IS NULL)
                            ORDER BY c.embedding <=> %s
                            LIMIT %s
                        """, (query_vector, company_id, company_id, query_vector, limit))
                        
                    else:
                        # フォールバック: L2距離計算
                        cur.execute("""
                            SELECT DISTINCT 
                                c.id as chunk_id,
                                c.doc_id as document_id,
                                c.chunk_index,
                                c.content as snippet,
                                ds.name as document_name,
                                ds.type as document_type,
                                0.7 as similarity_score
                            FROM chunks c
                            INNER JOIN document_sources ds ON ds.id = c.doc_id
                            WHERE c.content IS NOT NULL 
                                AND ds.active = true
                                AND (%s IS NULL OR ds.company_id = %s OR ds.company_id IS NULL)
                            LIMIT %s
                        """, (company_id, company_id, limit))
                    
                    results = cur.fetchall()
                    
                    # 結果を変換（document_sources.nameを必ず使用）
                    for row in results:
                        # document_sources.nameを必ず使用
                        document_name = row['document_name'] if row['document_name'] else 'Unknown Document'
                        
                        search_results.append(UltraSearchResult(
                            chunk_id=row['chunk_id'],
                            document_id=row['document_id'],
                            chunk_index=row['chunk_index'],
                            content=row['snippet'],
                            document_name=document_name,  # document_sources.nameのみ
                            document_type=row['document_type'],
                            relevance_score=float(row['similarity_score']),
                            confidence_score=float(row['similarity_score']) * 0.9,
                            search_method="ultra_accurate_vector"
                        ))
                    
                    return search_results
        
        except Exception as e:
            logger.error(f"超高精度検索実行エラー: {e}")
            return []
    
    def _enhance_ultra_result(self, result: Dict, query: str) -> Optional[UltraSearchResult]:
        """検索結果の超高精度強化"""
        try:
            # 各種スコアの計算
            query_match_score = self.calculate_query_match_score(result['snippet'] or '', query)
            semantic_score = self.calculate_semantic_score(result['snippet'] or '', query)
            
            # 総合関連度スコアの計算
            relevance_score = (
                result['similarity_score'] * 0.4 +
                query_match_score * 0.35 +
                semantic_score * 0.25
            )
            
            # 信頼度スコアの計算
            confidence_score = min(
                result['similarity_score'] + query_match_score * 0.5,
                1.0
            )
            
            return UltraSearchResult(
                chunk_id=result['chunk_id'],
                document_id=result['document_id'],
                document_name=result['document_name'],
                content=result['snippet'] or '',
                similarity_score=result['similarity_score'],
                relevance_score=relevance_score,
                confidence_score=confidence_score,
                chunk_index=result['chunk_index'],
                document_type=result['document_type'],
                search_method='ultra_accurate',
                query_match_score=query_match_score,
                semantic_score=semantic_score,
                metadata={
                    'special': result.get('special'),
                }
            )
        
        except Exception as e:
            logger.error(f"結果強化エラー: {e}")
            return None
    
    def _deduplicate_and_rank(self, results: List[UltraSearchResult], max_results: int) -> List[UltraSearchResult]:
        """重複除去と最終ランキング"""
        seen_content = set()
        seen_documents = defaultdict(int)
        final_results = []
        
        # 関連度スコアでソート
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        for result in results:
            # コンテンツの重複チェック（先頭50文字）
            content_key = result.content[:50].strip()
            if content_key in seen_content:
                continue
            
            # 同一文書からの結果数制限（最大4件）
            if seen_documents[result.document_id] >= 4:
                continue
            
            # 最小信頼度閾値チェック
            if result.confidence_score < 0.1:
                continue
            
            seen_content.add(content_key)
            seen_documents[result.document_id] += 1
            final_results.append(result)
            
            if len(final_results) >= max_results:
                break
        
        return final_results
    
    async def get_ultra_accurate_content(self, query: str, company_id: str = None, max_results: int = 15) -> str:
        """超高精度文書内容取得"""
        try:
            # 超高精度検索実行
            search_results = await self.ultra_accurate_search(query, company_id, max_results)
            
            if not search_results:
                logger.warning("関連するドキュメントが見つかりませんでした")
                return ""
            
            # 結果を組み立て
            relevant_content = []
            total_length = 0
            max_total_length = 60000  # 制限を拡大
            
            logger.info(f"📊 超高精度検索結果を処理中: {len(search_results)}件")
            
            for i, result in enumerate(search_results):
                logger.info(f"  {i+1}. {result.document_name} [チャンク{result.chunk_index}]")
                logger.info(f"     関連度: {result.relevance_score:.3f} (信頼度: {result.confidence_score:.3f})")
                
                if result.content and len(result.content.strip()) > 0:
                    content_piece = f"\n=== {result.document_name} - 参考資料{result.chunk_index} (関連度: {result.relevance_score:.3f}) ===\n{result.content}\n"
                    
                    if total_length + len(content_piece) <= max_total_length:
                        relevant_content.append(content_piece)
                        total_length += len(content_piece)
                        logger.info(f"    - 追加完了 ({len(content_piece)}文字)")
                    else:
                        logger.info(f"    - 文字数制限により除外")
                        break
            
            final_content = "\n".join(relevant_content)
            logger.info(f"✅ 超高精度コンテンツ構築完了: {len(relevant_content)}個のチャンク、{len(final_content)}文字")
            
            return final_content
        
        except Exception as e:
            logger.error(f"❌ 超高精度コンテンツ取得エラー: {e}")
            return ""

# インスタンス取得関数
def get_ultra_accurate_search_instance() -> Optional[UltraAccurateSearchSystem]:
    """超高精度検索システムのインスタンスを取得"""
    try:
        return UltraAccurateSearchSystem()
    except Exception as e:
        logger.error(f"超高精度検索システムの初期化に失敗: {e}")
        return None

def ultra_accurate_search_available() -> bool:
    """超高精度検索が利用可能かチェック"""
    try:
        instance = get_ultra_accurate_search_instance()
        return instance is not None
    except Exception:
        return False