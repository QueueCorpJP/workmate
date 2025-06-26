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
import google.generativeai as genai
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import concurrent.futures

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class ParallelVectorSearchSystem:
    """並列処理ベクトル検索システム"""
    
    def __init__(self):
        """初期化"""
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model = "models/text-embedding-004"  # 固定でtext-embedding-004を使用（768次元）
        
        self.db_url = self._get_db_url()
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
        
        # Gemini APIクライアントの初期化
        genai.configure(api_key=self.api_key)
        
        # 並列処理用のExecutor
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info(f"✅ 並列ベクトル検索システム初期化: {self.model} (768次元)")
        
        logger.info(f"✅ 並列ベクトル検索システム初期化: モデル={self.model}")
        
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

    async def parallel_comprehensive_search(self, query: str, company_id: str = None, max_results: int = 15) -> str:
        """包括的並列検索のメイン処理"""
        start_time = time.time()
        logger.info(f"🚀 並列包括検索開始: '{query}'")
        
        try:
            # 1. 複数のクエリ戦略を生成
            query_strategies = self.expand_query_strategies(query)
            
            # 2. 並列でエンベディング生成
            embeddings = await self.generate_query_embeddings_parallel(query_strategies)
            
            # 3. 有効なエンベディングで並列検索
            search_tasks = []
            for i, (q, embedding) in enumerate(zip(query_strategies, embeddings)):
                if embedding:
                    task = self.dual_direction_search(embedding, company_id, max_results // len(query_strategies))
                    search_tasks.append(task)
            
            # 並列実行
            all_results = await asyncio.gather(*search_tasks)
            
            # 4. 結果をマージして最適化
            final_results = self.merge_and_optimize_results(all_results)
            
            # 5. コンテンツ組み立て
            content = self.build_content_from_results(final_results, max_results)
            
            elapsed_time = time.time() - start_time
            logger.info(f"🎉 並列検索完了: {len(content)}文字 ({elapsed_time:.2f}秒)")
            
            return content
        
        except Exception as e:
            logger.error(f"並列検索エラー: {e}")
            return ""

    def expand_query_strategies(self, original_query: str) -> List[str]:
        """クエリ拡張戦略を生成"""
        strategies = [original_query]
        
        # 類義語マッピング
        synonyms_map = {
            '料金': ['価格', '費用', 'コスト'],
            '方法': ['手順', 'やり方'],
            '設定': ['構成', 'セットアップ'],
            '問題': ['課題', 'トラブル'],
        }
        
        # 類義語戦略
        for word, synonyms in synonyms_map.items():
            if word in original_query:
                for synonym in synonyms[:2]:
                    expanded = original_query.replace(word, synonym)
                    strategies.append(expanded)
        
        # 部分語戦略
        words = original_query.split()
        if len(words) > 1:
            strategies.extend(words[:2])
        
        return strategies[:4]  # 最大4戦略

    async def generate_query_embeddings_parallel(self, queries: List[str]) -> List[List[float]]:
        """複数クエリの埋め込みを並列生成"""
        async def generate_single(query: str) -> List[float]:
            try:
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
                    return embedding_vector  # 次元削減なし
                return []
            except Exception as e:
                logger.error(f"埋め込み生成エラー: {e}")
                return []
        
        tasks = [generate_single(q) for q in queries]
        return await asyncio.gather(*tasks)

    async def dual_direction_search(self, query_vector: List[float], company_id: str = None, limit: int = 10) -> Tuple[List[Dict], List[Dict]]:
        """双方向検索（上位・下位から同時検索）"""
        
        async def search_direction(direction: str) -> List[Dict]:
            return await asyncio.get_event_loop().run_in_executor(
                self.executor, 
                self._execute_vector_search, 
                query_vector, company_id, limit, direction
            )
        
        # 上位と下位を並列実行
        top_task = search_direction("DESC")
        bottom_task = search_direction("ASC")
        
        top_results, bottom_results = await asyncio.gather(top_task, bottom_task)
        return top_results, bottom_results

    def _execute_vector_search(self, query_vector: List[float], company_id: str, limit: int, order: str) -> List[Dict]:
        """ベクトル検索の実行（chunksテーブル対応版）"""
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # 新しいchunksテーブルを使用したSQL
                    sql = """
                    SELECT
                        c.id as chunk_id,
                        c.doc_id as document_id,
                        c.chunk_index,
                        c.content as snippet,
                        ds.name,
                        ds.special,
                        ds.type,
                        1 - (c.embedding <=> %s::vector) as similarity
                    FROM chunks c
                    LEFT JOIN document_sources ds ON ds.id = c.doc_id
                    WHERE c.embedding IS NOT NULL
                    """
                    
                    params = [query_vector]
                    
                    # 会社IDフィルタ（有効化）
                    if company_id:
                        sql += " AND c.company_id = %s"
                        params.append(company_id)
                        logger.info(f"🔍 並列検索: 会社IDフィルタ適用 - {company_id}")
                    else:
                        logger.info(f"🔍 並列検索: 会社IDフィルタなし（全データ検索）")
                    
                    sql += f" ORDER BY similarity {order} LIMIT %s"
                    params.append(limit)
                    
                    logger.info(f"並列ベクトル検索実行: {order} order, limit={limit}")
                    cur.execute(sql, params)
                    results = cur.fetchall()
                    
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
                            'similarity_score': float(row['similarity']),
                            'search_type': f'vector_parallel_{order.lower()}'
                        })
                    
                    logger.info(f"✅ 並列ベクトル検索完了: {len(search_results)}件 ({order})")
                    return search_results
        
        except Exception as e:
            logger.error(f"❌ 並列ベクトル検索実行エラー: {e}")
            import traceback
            logger.error(f"詳細エラー: {traceback.format_exc()}")
            return []

    def merge_and_optimize_results(self, all_results: List[Tuple[List[Dict], List[Dict]]]) -> List[Dict]:
        """結果をマージして最適化"""
        seen_chunks: Set[str] = set()
        merged_results = []
        
        # 全結果を統合
        for top_results, bottom_results in all_results:
            merged_results.extend(top_results)
            # 下位結果から有用なものを選別
            for result in bottom_results:
                # 🔍 デバッグ: 閾値を緩和（0.3 → 0.05）
                if result['similarity_score'] > 0.05:  # 閾値以上のもののみ
                    merged_results.append(result)
        
        # 重複除去
        unique_results = []
        for result in merged_results:
            chunk_id = result['chunk_id']
            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                unique_results.append(result)
        
        # 類似度順でソート
        unique_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return unique_results

    def build_content_from_results(self, results: List[Dict], max_results: int) -> str:
        """結果からコンテンツを構築（chunksテーブル対応版）"""
        if not results:
            return ""
        
        relevant_content = []
        total_length = 0
        max_total_length = 50000  # 制限を拡大（20000 → 50000）
        
        logger.info(f"📝 コンテンツ構築開始: {len(results)}件の結果から最大{max_results}件を処理")
        
        for i, result in enumerate(results[:max_results]):
            similarity = result['similarity_score']
            snippet = result['snippet'] or ""
            chunk_index = result.get('chunk_index', 'N/A')
            
            # 類似度閾値を緩和（0.05 → 0.02）
            if similarity < 0.02:
                logger.info(f"  {i+1}. 類似度が低いためスキップ: {similarity:.3f}")
                continue
            
            if snippet and len(snippet.strip()) > 0:
                content_piece = f"\n=== {result['document_name']} - チャンク{chunk_index} (類似度: {similarity:.3f}) ===\n{snippet}\n"
                
                if total_length + len(content_piece) <= max_total_length:
                    relevant_content.append(content_piece)
                    total_length += len(content_piece)
                    logger.info(f"  {i+1}. 追加: {result['document_name']} [チャンク{chunk_index}] ({len(content_piece)}文字)")
                else:
                    logger.info(f"  {i+1}. 文字数制限により終了")
                    break
            else:
                logger.info(f"  {i+1}. 空のコンテンツのためスキップ")
        
        final_content = "\n".join(relevant_content)
        logger.info(f"✅ 並列検索コンテンツ構築完了: {len(relevant_content)}個のチャンク、{len(final_content)}文字")
        
        return final_content

    def parallel_comprehensive_search_sync(self, query: str, company_id: str = None, max_results: int = 15) -> str:
        """包括的並列検索の同期版 - イベントループ問題を回避"""
        start_time = time.time()
        logger.info(f"🚀 同期並列包括検索開始: '{query}'")
        
        try:
            # 1. 複数のクエリ戦略を生成
            query_strategies = self.expand_query_strategies(query)
            
            # 2. 並列でエンベディング生成（ThreadPoolExecutorを使用）
            embeddings = self._generate_query_embeddings_sync(query_strategies)
            
            # 3. 有効なエンベディングで並列検索
            valid_embeddings = [(q, e) for q, e in zip(query_strategies, embeddings) if e]
            
            if not valid_embeddings:
                logger.error("有効なエンベディングが生成されませんでした")
                return ""
            
            # 4. 並列検索の実行（ThreadPoolExecutorを使用）
            all_top_results = []
            all_bottom_results = []
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                # 各エンベディングで双方向検索を並列実行
                future_to_embedding = {}
                
                for query_text, embedding in valid_embeddings:
                    # 上位検索のFuture
                    future_top = executor.submit(
                        self._execute_vector_search,
                        embedding, company_id, max_results // len(valid_embeddings), "DESC"
                    )
                    future_to_embedding[future_top] = (query_text, embedding, "top")
                    
                    # 下位検索のFuture
                    future_bottom = executor.submit(
                        self._execute_vector_search,
                        embedding, company_id, max_results // len(valid_embeddings), "ASC"
                    )
                    future_to_embedding[future_bottom] = (query_text, embedding, "bottom")
                
                # 結果を収集
                for future in concurrent.futures.as_completed(future_to_embedding):
                    query_text, embedding, search_type = future_to_embedding[future]
                    try:
                        results = future.result(timeout=30)  # 30秒タイムアウト
                        if search_type == "top":
                            all_top_results.extend(results)
                        else:
                            all_bottom_results.extend(results)
                    except Exception as e:
                        logger.error(f"並列検索エラー: {e}")
            
            # 5. 間隙検索（主要エンベディングを使用）
            gap_results = []
            if valid_embeddings:
                primary_embedding = valid_embeddings[0][1]
                gap_conditions = self._find_gap_candidates_sync(all_top_results, all_bottom_results)
                
                # 間隙検索も並列実行
                with ThreadPoolExecutor(max_workers=2) as executor:
                    gap_futures = []
                    for condition in gap_conditions:
                        future = executor.submit(
                            self._execute_gap_search_sync, 
                            primary_embedding, condition, company_id
                        )
                        gap_futures.append(future)
                    
                    for future in concurrent.futures.as_completed(gap_futures):
                        try:
                            results = future.result(timeout=15)
                            gap_results.extend(results)
                        except Exception as e:
                            logger.error(f"間隙検索エラー: {e}")
            
            # 6. 結果のマージと重複除去
            final_results = self.merge_and_optimize_results([(all_top_results, all_bottom_results)])
            final_results.extend(gap_results)
            
            # 重複除去
            seen_chunks = set()
            unique_results = []
            for result in final_results:
                chunk_id = result['chunk_id']
                if chunk_id not in seen_chunks:
                    seen_chunks.add(chunk_id)
                    unique_results.append(result)
            
            # 類似度順でソート
            unique_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # 7. コンテンツ組み立て
            content = self.build_content_from_results(unique_results, max_results)
            
            elapsed_time = time.time() - start_time
            logger.info(f"🎉 同期並列検索完了: {len(content)}文字 ({elapsed_time:.2f}秒)")
            
            return content
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"同期並列検索エラー: {e} ({elapsed_time:.2f}秒)")
            return ""

    def _generate_query_embeddings_sync(self, queries: List[str]) -> List[List[float]]:
        """複数クエリの埋め込みを同期並列生成"""
        def generate_single_embedding(query: str) -> List[float]:
            try:
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
                    return embedding_vector  # 次元削減なし
                else:
                    logger.error(f"埋め込み生成失敗: {query}")
                    return []
            except Exception as e:
                logger.error(f"埋め込み生成エラー: {e}")
                return []
        
        # ThreadPoolExecutorで並列実行（順序を保証）
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(generate_single_embedding, query) for query in queries]
            embeddings = []
            
            for i, future in enumerate(futures):
                try:
                    embedding = future.result(timeout=30)
                    embeddings.append(embedding)
                except Exception as e:
                    logger.error(f"埋め込み生成タイムアウト: {queries[i]} - {e}")
                    embeddings.append([])
        
        logger.info(f"✅ 同期並列埋め込み生成完了: {len([e for e in embeddings if e])}個成功")
        return embeddings

    def _find_gap_candidates_sync(self, top_results: List[Dict], bottom_results: List[Dict]) -> List[str]:
        """マッチした結果の間にある候補を特定（同期版）"""
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

    def _execute_gap_search_sync(self, query_vector: List[float], condition: str, company_id: str = None) -> List[Dict]:
        """間隙検索の同期実行"""
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    sql = f"""
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
                        1 - (de.embedding <=> %s) as similarity
                    FROM document_embeddings de
                    LEFT JOIN document_sources ds ON ds.id = CASE 
                        WHEN de.document_id LIKE '%_chunk_%' THEN 
                            SPLIT_PART(de.document_id, '_chunk_', 1)
                        ELSE de.document_id
                    END
                    WHERE de.embedding IS NOT NULL
                      AND (1 - (de.embedding <=> %s)) {condition}
                    """
                    
                    params = [query_vector, query_vector]
                    
                    # 🔍 デバッグ: 間隙検索でもcompany_idフィルタを無効化
                    # if company_id:
                    #     sql += " AND ds.company_id = %s"
                    #     params.append(company_id)
                    
                    sql += " ORDER BY similarity DESC LIMIT 5"
                    
                    cur.execute(sql, params)
                    results = cur.fetchall()
                    
                    return [{
                        'chunk_id': row['chunk_id'],
                        'document_id': row['original_doc_id'],
                        'document_name': row['name'],
                        'document_type': row['type'],
                        'special': row['special'],
                        'snippet': row['snippet'],
                        'similarity_score': float(row['similarity']),
                        'search_type': 'vector_gap_sync'
                    } for row in results]
        
        except Exception as e:
            logger.error(f"間隙検索同期実行エラー: {e}")
            return []

# グローバルインスタンス
_parallel_vector_search_instance = None

async def get_parallel_vector_search_instance() -> Optional[ParallelVectorSearchSystem]:
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

def get_parallel_vector_search_instance_sync() -> Optional[ParallelVectorSearchSystem]:
    """並列ベクトル検索インスタンスを同期取得"""
    global _parallel_vector_search_instance
    
    if _parallel_vector_search_instance is None:
        try:
            _parallel_vector_search_instance = ParallelVectorSearchSystem()
            logger.info("✅ 並列ベクトル検索システム初期化完了（同期版）")
        except Exception as e:
            logger.error(f"❌ 並列ベクトル検索システム初期化エラー: {e}")
            return None
    
    return _parallel_vector_search_instance 