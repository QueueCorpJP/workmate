"""
並列処理による高速ベクトル検索システム
- 双方向検索（上位・下位から同時検索）
- 間隙検索（マッチ間の候補も検索）
- 非同期並列処理による高速化
"""

import asyncio
import logging
from typing import List, Dict, Tuple, Optional, Set
from concurrent.futures import ThreadPoolExecutor
import time
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
import os

# Vertex AI インポート
try:
    from google.cloud import aiplatform
    from vertexai.language_models import TextEmbeddingModel
    import vertexai
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False

# フォールバック用のGemini API
try:
    import google.generativeai as genai
    GEMINI_API_AVAILABLE = True
except ImportError:
    GEMINI_API_AVAILABLE = False

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class ParallelVectorSearchSystem:
    """並列処理ベクトル検索システム"""
    
    def __init__(self):
        """初期化"""
        self.use_vertex_ai = os.getenv("USE_VERTEX_AI", "true").lower() == "true"
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "workmate-462302")
        self.location = "us-central1"
        
        # モデル設定
        if self.use_vertex_ai:
            self.model_name = os.getenv("EMBEDDING_MODEL", "text-multilingual-embedding-002")
        else:
            self.model_name = "models/gemini-embedding-001"
        
        self.db_url = self._get_db_url()
        
        # Vertex AI または Gemini API の初期化
        if self.use_vertex_ai and VERTEX_AI_AVAILABLE:
            self._init_vertex_ai()
        else:
            self._init_gemini_api()
        
        # 並列処理用のExecutor
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info(f"✅ 並列ベクトル検索システム初期化: {self.model_name}")
    
    def _init_vertex_ai(self):
        """Vertex AI の初期化"""
        try:
            # サービスアカウント認証の設定
            service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if service_account_path and os.path.exists(service_account_path):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path
                logger.info(f"✅ サービスアカウント認証設定: {service_account_path}")
            
            # Vertex AI初期化
            vertexai.init(project=self.project_id, location=self.location)
            self.model = TextEmbeddingModel.from_pretrained(self.model_name)
            self.embedding_method = "vertex_ai"
            self.api_key = None  # Vertex AIではAPI keyは不要
            logger.info(f"✅ Vertex AI 初期化完了: {self.model_name}")
            
        except Exception as e:
            logger.error(f"❌ Vertex AI 初期化失敗: {e}")
            logger.info("🔄 Gemini API にフォールバック")
            self._init_gemini_api()
    
    def _init_gemini_api(self):
        """Gemini API の初期化"""
        if not GEMINI_API_AVAILABLE:
            raise ValueError("Gemini API ライブラリが利用できません")
        
        # API キーの設定
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
        
        # Gemini APIクライアントの初期化
        genai.configure(api_key=self.api_key)
        self.model = None  # genai.embed_content を直接使用
        self.embedding_method = "gemini_api"
        logger.info(f"✅ Gemini API 初期化完了: {self.model_name}")
        
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

    async def generate_query_embeddings_parallel(self, queries: List[str]) -> List[List[float]]:
        """複数クエリの埋め込みを並列生成"""
        logger.info(f"📡 {len(queries)}個のクエリの埋め込みを並列生成中...")
        
        async def generate_single_embedding(query: str) -> List[float]:
            try:
                if self.embedding_method == "vertex_ai":
                    return await self._generate_vertex_ai_embedding(query)
                else:
                    return await self._generate_gemini_api_embedding(query)
            except Exception as e:
                logger.error(f"埋め込み生成エラー: {e}")
                return []
        
        # 並列実行
        tasks = [generate_single_embedding(query) for query in queries]
        embeddings = await asyncio.gather(*tasks)
        
        logger.info(f"✅ 並列埋め込み生成完了: {len([e for e in embeddings if e])}個成功")
        return embeddings
    
    async def _generate_vertex_ai_embedding(self, query: str) -> List[float]:
        """Vertex AI を使用した埋め込み生成"""
        try:
            # Vertex AI の埋め込み生成は同期的なので、非同期実行
            def _sync_generate():
                embeddings = self.model.get_embeddings([query])
                if embeddings and len(embeddings) > 0:
                    return embeddings[0].values
                return []
            
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(self.executor, _sync_generate)
            return embedding
            
        except Exception as e:
            logger.error(f"Vertex AI 埋め込み生成エラー: {e}")
            return []
    
    async def _generate_gemini_api_embedding(self, query: str) -> List[float]:
        """Gemini API を使用した埋め込み生成"""
        try:
            response = genai.embed_content(
                model=self.model_name,
                content=query
            )
            
            # レスポンスからエンベディングベクトルを取得
            embedding_vector = None
            
            if isinstance(response, dict) and 'embedding' in response:
                embedding_vector = response['embedding']
            elif hasattr(response, 'embedding') and response.embedding:
                embedding_vector = response.embedding
            
            if embedding_vector and len(embedding_vector) > 0:
                return embedding_vector
            else:
                logger.error(f"埋め込み生成失敗: {query}")
                return []
                
        except Exception as e:
            logger.error(f"Gemini API 埋め込み生成エラー: {e}")
            return []

    def expand_query_strategies(self, original_query: str) -> List[str]:
        """クエリ拡張戦略を生成"""
        strategies = [
            original_query,  # 元のクエリ
        ]
        
        # 類義語拡張
        synonyms_map = {
            '料金': ['価格', '費用', 'コスト', '値段', '料金表'],
            '方法': ['手順', 'やり方', 'プロセス', '手続き'],
            '設定': ['構成', 'コンフィグ', 'セットアップ', '設定方法'],
            '問題': ['課題', 'トラブル', 'エラー', '不具合'],
            '使い方': ['利用方法', '操作方法', '使用方法'],
        }
        
        # 類義語クエリを追加
        for word, synonyms in synonyms_map.items():
            if word in original_query:
                for synonym in synonyms[:2]:  # 上位2つの類義語
                    expanded = original_query.replace(word, synonym)
                    if expanded not in strategies:
                        strategies.append(expanded)
        
        # 部分クエリを追加
        words = original_query.split()
        if len(words) > 1:
            for word in words:
                if len(word) > 1 and word not in strategies:
                    strategies.append(word)
        
        logger.info(f"🔍 クエリ戦略生成: {len(strategies)}個 {strategies}")
        return strategies[:5]  # 最大5戦略

    async def dual_direction_search(self, query_vector: List[float], company_id: str = None, limit: int = 10) -> Tuple[List[Dict], List[Dict]]:
        """双方向検索（上位・下位から同時検索）"""
        
        async def search_top_similar(vector: List[float]) -> List[Dict]:
            """上位類似検索"""
            return await asyncio.get_event_loop().run_in_executor(
                self.executor, 
                self._execute_vector_search, 
                vector, company_id, limit, "similarity DESC"
            )
        
        async def search_bottom_similar(vector: List[float]) -> List[Dict]:
            """下位類似検索（非類似から）"""
            return await asyncio.get_event_loop().run_in_executor(
                self.executor, 
                self._execute_vector_search, 
                vector, company_id, limit, "similarity ASC"
            )
        
        logger.info("🔄 双方向並列検索実行中...")
        
        # 並列実行
        top_results, bottom_results = await asyncio.gather(
            search_top_similar(query_vector),
            search_bottom_similar(query_vector)
        )
        
        logger.info(f"📊 双方向検索完了: 上位{len(top_results)}件, 下位{len(bottom_results)}件")
        return top_results, bottom_results

    def _execute_vector_search(self, query_vector: List[float], company_id: str, limit: int, order_by: str) -> List[Dict]:
        """ベクトル検索の実行"""
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    sql = """
                    SELECT
                        c.id::text as chunk_id,
                        c.doc_id as original_doc_id,
                        ds.name,
                        ds.special,
                        ds.type,
                        c.content as snippet,
                        1 - (c.embedding <=> %s::vector) as similarity
                    FROM chunks c
                    LEFT JOIN document_sources ds ON ds.id = c.doc_id
                    WHERE c.embedding IS NOT NULL
                    """
                    
                    # Convert list to string format for PostgreSQL vector type
                    vector_str = '[' + ','.join(map(str, query_vector)) + ']'
                    params = [vector_str]
                    
                    if company_id:
                        sql += " AND c.company_id = %s"
                        params.append(company_id)
                    
                    sql += f" ORDER BY {order_by} LIMIT %s"
                    params.append(limit)
                    
                    cur.execute(sql, params)
                    results = cur.fetchall()
                    
                    return [{
                        'chunk_id': row['chunk_id'],
                        'document_id': row['original_doc_id'],
                        'document_name': row['name'] if row['name'] else 'Unknown Document',
                        'document_type': row['type'] if row['type'] else 'unknown',
                        'special': row['special'] if row['special'] else False,
                        'snippet': row['snippet'] if row['snippet'] else '',
                        'similarity_score': float(row['similarity']) if row['similarity'] else 0.0,
                        'search_type': 'vector_parallel'
                    } for row in results]
        
        except Exception as e:
            logger.error(f"ベクトル検索実行エラー: {e}")
            return []

    def find_gap_candidates(self, top_results: List[Dict], bottom_results: List[Dict]) -> List[str]:
        """マッチした結果の間にある候補を特定"""
        gap_candidates = []
        
        if not top_results or not bottom_results:
            return gap_candidates
        
        # 上位と下位の類似度の範囲を特定
        top_similarities = [r['similarity_score'] for r in top_results]
        bottom_similarities = [r['similarity_score'] for r in bottom_results]
        
        if top_similarities and bottom_similarities:
            min_top = min(top_similarities)
            max_bottom = max(bottom_similarities)
            
            # 間隙がある場合
            if min_top > max_bottom:
                gap_threshold_high = min_top - 0.05
                gap_threshold_low = max_bottom + 0.05
                gap_candidates.append(f"BETWEEN {gap_threshold_low} AND {gap_threshold_high}")
                logger.info(f"🔍 間隙検索範囲: {gap_threshold_low:.3f} - {gap_threshold_high:.3f}")
        
        return gap_candidates

    async def execute_gap_search(self, query_vector: List[float], gap_conditions: List[str], company_id: str = None) -> List[Dict]:
        """間隙検索を実行"""
        if not gap_conditions:
            return []
        
        gap_results = []
        
        for condition in gap_conditions:
            try:
                results = await asyncio.get_event_loop().run_in_executor(
                    self.executor, 
                    self._execute_gap_search_sync, 
                    query_vector, condition, company_id
                )
                gap_results.extend(results)
            except Exception as e:
                logger.error(f"間隙検索エラー: {e}")
        
        logger.info(f"🔍 間隙検索完了: {len(gap_results)}件の追加結果")
        return gap_results

    def _execute_gap_search_sync(self, query_vector: List[float], condition: str, company_id: str = None) -> List[Dict]:
        """間隙検索の同期実行"""
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # Convert list to string format for PostgreSQL vector type
                    vector_str = '[' + ','.join(map(str, query_vector)) + ']'
                    
                    # Use subquery to avoid repeating the vector calculation
                    sql = f"""
                    SELECT
                        chunk_id,
                        original_doc_id,
                        name,
                        special,
                        type,
                        snippet,
                        similarity
                    FROM (
                        SELECT
                            c.id::text as chunk_id,
                            c.doc_id as original_doc_id,
                            ds.name,
                            ds.special,
                            ds.type,
                            c.content as snippet,
                            1 - (c.embedding <=> %s::vector) as similarity
                        FROM chunks c
                        LEFT JOIN document_sources ds ON ds.id = c.doc_id
                        WHERE c.embedding IS NOT NULL
                    ) subq
                    WHERE similarity {condition}
                    """
                    
                    params = [vector_str]
                    
                    if company_id:
                        # Add company_id filter to the subquery
                        sql = f"""
                        SELECT
                            chunk_id,
                            original_doc_id,
                            name,
                            special,
                            type,
                            snippet,
                            similarity
                        FROM (
                            SELECT
                                c.id::text as chunk_id,
                                c.doc_id as original_doc_id,
                                ds.name,
                                ds.special,
                                ds.type,
                                c.content as snippet,
                                1 - (c.embedding <=> %s::vector) as similarity
                            FROM chunks c
                            LEFT JOIN document_sources ds ON ds.id = c.doc_id
                            WHERE c.embedding IS NOT NULL
                              AND c.company_id = %s
                        ) subq
                        WHERE similarity {condition}
                        """
                        params = [vector_str, company_id]
                    
                    sql += " ORDER BY similarity DESC LIMIT 5"
                    
                    cur.execute(sql, params)
                    results = cur.fetchall()
                    
                    return [{
                        'chunk_id': row['chunk_id'],
                        'document_id': row['original_doc_id'],
                        'document_name': row['name'] if row['name'] else 'Unknown Document',
                        'document_type': row['type'] if row['type'] else 'unknown',
                        'special': row['special'] if row['special'] else False,
                        'snippet': row['snippet'] if row['snippet'] else '',
                        'similarity_score': float(row['similarity']) if row['similarity'] else 0.0,
                        'search_type': 'vector_gap'
                    } for row in results]
        
        except Exception as e:
            logger.error(f"間隙検索同期実行エラー: {e}")
            return []

    def merge_and_deduplicate_results(self, *result_lists: List[List[Dict]]) -> List[Dict]:
        """結果をマージして重複を除去"""
        seen_chunks: Set[str] = set()
        merged_results = []
        
        # 全ての結果リストを統合
        all_results = []
        for result_list in result_lists:
            all_results.extend(result_list)
        
        # 類似度順でソート
        all_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # 重複除去
        for result in all_results:
            chunk_id = result['chunk_id']
            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                merged_results.append(result)
        
        logger.info(f"🔄 結果マージ完了: {len(all_results)}件 → {len(merged_results)}件（重複除去後）")
        return merged_results

    async def parallel_comprehensive_search(self, query: str, company_id: str = None, max_results: int = 15) -> str:
        """包括的並列検索のメイン処理"""
        start_time = time.time()
        logger.info(f"🚀 並列包括検索開始: '{query}'")
        
        try:
            # 1. クエリ戦略の生成
            query_strategies = self.expand_query_strategies(query)
            
            # 2. 並列エンベディング生成
            embeddings = await self.generate_query_embeddings_parallel(query_strategies)
            
            # 有効なエンベディングのみを使用
            valid_embeddings = [(q, e) for q, e in zip(query_strategies, embeddings) if e]
            
            if not valid_embeddings:
                logger.error("有効なエンベディングが生成されませんでした")
                return ""
            
            # 3. 複数戦略での並列検索
            search_tasks = []
            for query_text, embedding in valid_embeddings:
                task = self.dual_direction_search(embedding, company_id, max_results // len(valid_embeddings))
                search_tasks.append(task)
            
            # 並列実行
            all_search_results = await asyncio.gather(*search_tasks)
            
            # 4. 結果の統合
            all_top_results = []
            all_bottom_results = []
            
            for top_results, bottom_results in all_search_results:
                all_top_results.extend(top_results)
                all_bottom_results.extend(bottom_results)
            
            # 5. 間隙検索
            if valid_embeddings:
                primary_embedding = valid_embeddings[0][1]
                gap_conditions = self.find_gap_candidates(all_top_results, all_bottom_results)
                gap_results = await self.execute_gap_search(primary_embedding, gap_conditions, company_id)
            else:
                gap_results = []
            
            # 6. 結果のマージと重複除去
            final_results = self.merge_and_deduplicate_results(
                all_top_results, all_bottom_results, gap_results
            )
            
            # 7. コンテンツの組み立て
            if not final_results:
                logger.warning("関連するドキュメントが見つかりませんでした")
                return ""
            
            relevant_content = []
            total_length = 0
            max_total_length = 20000  # 最大文字数を増加
            
            logger.info(f"📊 最終結果処理: {len(final_results)}件")
            
            for i, result in enumerate(final_results[:max_results]):
                similarity = result['similarity_score']
                snippet = result['snippet'] or ""
                search_type = result['search_type']
                
                logger.info(f"  {i+1}. {result['document_name']} (類似度: {similarity:.3f}, 種類: {search_type})")
                
                # 閾値以下の類似度の結果は除外
                if similarity < 0.2:
                    logger.info(f"    - 類似度が低いため除外 ({similarity:.3f} < 0.2)")
                    continue
                
                # スニペットを追加
                if snippet and len(snippet.strip()) > 0:
                    content_piece = f"\n=== {result['document_name']} (類似度: {similarity:.3f}, {search_type}) ===\n{snippet}\n"
                    
                    if total_length + len(content_piece) <= max_total_length:
                        relevant_content.append(content_piece)
                        total_length += len(content_piece)
                        logger.info(f"    - 追加完了 ({len(content_piece)}文字)")
                    else:
                        logger.info(f"    - 文字数制限により除外")
                        break
            
            final_content = "\n".join(relevant_content)
            elapsed_time = time.time() - start_time
            
            logger.info(f"🎉 並列包括検索完了: {len(final_content)}文字 ({elapsed_time:.2f}秒)")
            logger.info(f"📊 検索統計: 戦略{len(query_strategies)}個, 結果{len(final_results)}件, 採用{len(relevant_content)}件")
            
            return final_content
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"並列包括検索エラー: {e} ({elapsed_time:.2f}秒)")
            return ""

# グローバルインスタンス
_parallel_vector_search_instance = None

def get_parallel_vector_search_instance() -> Optional[ParallelVectorSearchSystem]:
    """並列ベクトル検索インスタンスを取得"""
    global _parallel_vector_search_instance
    
    if _parallel_vector_search_instance is None:
        try:
            _parallel_vector_search_instance = ParallelVectorSearchSystem()
            logger.info("✅ 並列ベクトル検索システム初期化完了")
        except Exception as e:
            logger.error(f"❌ 並列ベクトル検索システム初期化エラー: {e}")
            return None
    
    return _parallel_vector_search_instance 