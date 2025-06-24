"""
高速化RAGシステム
並列処理とキャッシュシステムによる超高速検索
"""
import asyncio
import time
import hashlib
import json
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)

@dataclass
class FastSearchResult:
    """高速検索結果クラス"""
    content: str
    score: float
    chunk_id: str
    processing_time: float = 0.0

class HighSpeedRAG:
    """超高速RAGシステム"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 3600  # 1時間
        self.max_workers = 5   # 並列処理数
        self.enable_cache = True
        
    def _get_cache_key(self, text: str, query: str) -> str:
        """キャッシュキーを生成"""
        content = f"{text[:100]}_{query}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """キャッシュの有効性をチェック"""
        if not cache_entry:
            return False
        return time.time() - cache_entry.get('timestamp', 0) < self.cache_ttl
    
    async def fast_chunking(self, text: str, chunk_size: int = 2000, overlap: int = 200) -> List[Dict]:
        """
        高速チャンク化 - 大きなチャンクサイズで処理数を削減
        """
        start_time = time.time()
        
        # 簡単な境界検出で高速分割
        chunks = []
        text_length = len(text)
        
        if text_length <= chunk_size:
            return [{
                'id': 'chunk_0',
                'content': text,
                'size': text_length
            }]
        
        chunk_id = 0
        start = 0
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            
            # 境界調整（高速版）
            if end < text_length:
                # 最後の改行を探す（限定範囲）
                boundary_search = max(0, end - 200)
                last_newline = text.rfind('\n', boundary_search, end)
                if last_newline > start:
                    end = last_newline + 1
            
            chunk_content = text[start:end].strip()
            if chunk_content:
                chunks.append({
                    'id': f'chunk_{chunk_id}',
                    'content': chunk_content,
                    'size': len(chunk_content)
                })
                chunk_id += 1
            
            start = max(start + chunk_size - overlap, end)
        
        elapsed = time.time() - start_time
        logger.info(f"⚡ 高速チャンク化完了: {len(chunks)}個 ({elapsed:.2f}秒)")
        
        return chunks
    
    async def parallel_bm25_search(self, query: str, chunks: List[Dict], top_k: int = 15) -> List[FastSearchResult]:
        """
        並列BM25検索 - 複数チャンクを同時処理
        """
        start_time = time.time()
        
        try:
            import bm25s
            
            # チャンクを小さなグループに分割して並列処理
            chunk_groups = self._split_chunks_for_parallel(chunks, self.max_workers)
            
            # 並列実行用タスクを作成
            tasks = []
            for group in chunk_groups:
                task = self._search_chunk_group(query, group, bm25s)
                tasks.append(task)
            
            # 並列実行
            all_results = []
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in completed_tasks:
                if isinstance(result, list):
                    all_results.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"並列検索でエラー: {result}")
            
            # スコア順でソート
            all_results.sort(key=lambda x: x.score, reverse=True)
            
            elapsed = time.time() - start_time
            logger.info(f"⚡ 並列BM25検索完了: {len(all_results)}件 ({elapsed:.2f}秒)")
            
            return all_results[:top_k]
            
        except Exception as e:
            logger.error(f"並列BM25検索エラー: {e}")
            return []
    
    def _split_chunks_for_parallel(self, chunks: List[Dict], num_groups: int) -> List[List[Dict]]:
        """チャンクを並列処理用にグループ分け"""
        chunk_size = max(1, len(chunks) // num_groups)
        groups = []
        
        for i in range(0, len(chunks), chunk_size):
            group = chunks[i:i + chunk_size]
            if group:
                groups.append(group)
        
        return groups
    
    async def _search_chunk_group(self, query: str, chunk_group: List[Dict], bm25s) -> List[FastSearchResult]:
        """チャンクグループでの検索実行"""
        try:
            # チャンクグループが空の場合は空のリストを返す
            if not chunk_group:
                logger.warning(f"チャンクグループが空のためスキップ")
                return []
            
            texts = [chunk['content'] for chunk in chunk_group]
            
            # 有効なテキストがない場合はスキップ
            if not texts or all(not text.strip() for text in texts):
                logger.warning(f"有効なテキストがないためスキップ")
                return []
            
            # BM25検索実行
            corpus_tokens = bm25s.tokenize(texts)
            retriever = bm25s.BM25()
            retriever.index(corpus_tokens)
            
            query_tokens = bm25s.tokenize([query])
            results, scores = retriever.retrieve(query_tokens, k=len(chunk_group))
            
            # 結果をFastSearchResultに変換
            search_results = []
            if results.shape[1] > 0:  # 結果が存在する場合のみ処理
                for i in range(min(results.shape[1], len(chunk_group))):
                    chunk_idx = results[0, i]
                    if chunk_idx < len(chunk_group):
                        chunk = chunk_group[chunk_idx]
                        score = float(scores[0, i]) if i < len(scores[0]) else 0.0
                        
                        search_results.append(FastSearchResult(
                            content=chunk['content'],
                            score=score,
                            chunk_id=chunk['id']
                        ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"チャンクグループ検索エラー: {e}")
            return []
    
    async def lightning_search(self, query: str, knowledge_text: str, max_results: int = 20) -> str:
        """雷速検索 - 最高速度でのRAG検索"""
        start_time = time.time()
        
        # キャッシュチェック
        cache_key = self._get_cache_key(knowledge_text, query)
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                logger.info(f"⚡ キャッシュヒット")
                return cache_entry['result']
        
        # 高速チャンク化
        chunks = self._fast_chunking(knowledge_text, chunk_size=3000)
        
        # 事前フィルタリング
        keywords = self._extract_keywords(query)
        filtered_chunks = self._pre_filter_chunks(chunks, keywords)
        
        # フィルタリング後にチャンクが空の場合は元のチャンクを使用
        if not filtered_chunks:
            logger.info(f"⚠️ フィルタリング後にチャンクが空のため、全チャンクを使用")
            filtered_chunks = chunks[:20]  # 最大20個のチャンク
        
        # BM25検索
        try:
            import bm25s
            
            # チャンクが存在することを確認
            if not filtered_chunks:
                logger.error(f"高速検索エラー: チャンクが空です")
                final_result = knowledge_text[:20000]
            else:
                texts = [chunk['content'] for chunk in filtered_chunks]
                
                # テキストが空でないことを確認
                if not texts or all(not text.strip() for text in texts):
                    logger.error(f"高速検索エラー: 有効なテキストがありません")
                    final_result = knowledge_text[:20000]
                else:
                    corpus_tokens = bm25s.tokenize(texts)
                    retriever = bm25s.BM25()
                    retriever.index(corpus_tokens)
                    
                    query_tokens = bm25s.tokenize([query])
                    results, scores = retriever.retrieve(query_tokens, k=min(max_results, len(filtered_chunks)))
                    
                    # 結果組み立て
                    relevant_content = []
                    if results.shape[1] > 0:  # 結果が存在する場合のみ処理
                        for i in range(min(results.shape[1], max_results)):
                            chunk_idx = results[0, i]
                            if chunk_idx < len(filtered_chunks):
                                relevant_content.append(filtered_chunks[chunk_idx]['content'])
                    
                    if relevant_content:
                        final_result = '\n\n'.join(relevant_content[:10])  # 最大10個のチャンク
                    else:
                        logger.info(f"⚠️ BM25検索で関連コンテンツが見つからず、フォールバック")
                        final_result = knowledge_text[:20000]
            
        except Exception as e:
            logger.error(f"高速検索エラー: {e}")
            final_result = knowledge_text[:20000]
        
        # キャッシュに保存
        self.cache[cache_key] = {
            'result': final_result,
            'timestamp': time.time()
        }
        
        elapsed = time.time() - start_time
        logger.info(f"⚡ 雷速検索完了: {elapsed:.2f}秒")
        
        return final_result
    
    def _fast_chunking(self, text: str, chunk_size: int = 3000) -> List[Dict]:
        """高速チャンク化"""
        chunks = []
        text_length = len(text)
        
        if text_length <= chunk_size:
            return [{'id': 'chunk_0', 'content': text}]
        
        chunk_id = 0
        start = 0
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            
            # 簡単な境界調整
            if end < text_length:
                boundary_search = max(0, end - 100)
                last_newline = text.rfind('\n', boundary_search, end)
                if last_newline > start:
                    end = last_newline + 1
            
            chunk_content = text[start:end].strip()
            if chunk_content:
                chunks.append({
                    'id': f'chunk_{chunk_id}',
                    'content': chunk_content
                })
                chunk_id += 1
            
            start = end
        
        return chunks
    
    def _extract_keywords(self, query: str) -> List[str]:
        """重要キーワード抽出"""
        stop_words = {'は', 'が', 'を', 'に', 'の', 'で', 'と', 'から', 'です', 'ます'}
        words = query.split()
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        return keywords[:5]
    
    def _pre_filter_chunks(self, chunks: List[Dict], keywords: List[str]) -> List[Dict]:
        """事前フィルタリング"""
        if not keywords or not chunks:
            return chunks[:20] if chunks else []  # 空の場合でも最大20個までを返す
        
        filtered = []
        for chunk in chunks:
            content_lower = chunk['content'].lower()
            matching_keywords = sum(1 for kw in keywords if kw.lower() in content_lower)
            
            if matching_keywords > 0:
                chunk['score'] = matching_keywords
                filtered.append(chunk)
        
        # フィルタリング結果が空の場合は、元のチャンクの一部を返す
        if not filtered:
            logger.info(f"⚠️ キーワードフィルタリングで結果が空のため、元のチャンクを使用")
            return chunks[:10]  # 最大10個のチャンク
        
        # スコア順でソート
        filtered.sort(key=lambda x: x.get('score', 0), reverse=True)
        return filtered[:20]  # 上位20チャンクのみ
    
    async def turbo_search(self, query: str, knowledge_text: str, max_results: int = 15) -> str:
        """
        ターボ検索 - 速度重視の簡易版
        """
        start_time = time.time()
        
        # 非常に大きなチャンクで分割数を最小化
        if len(knowledge_text) > 100000:
            chunks = await self.fast_chunking(knowledge_text, chunk_size=5000, overlap=500)
        else:
            chunks = await self.fast_chunking(knowledge_text, chunk_size=len(knowledge_text))
        
        # チャンクが空の場合はフォールバック
        if not chunks:
            logger.warning(f"ターボ検索: チャンクが空のためフォールバック")
            return knowledge_text[:20000]
        
        # 単一スレッドでの高速検索
        try:
            import bm25s
            
            texts = [chunk['content'] for chunk in chunks]
            
            # 有効なテキストがない場合はフォールバック
            if not texts or all(not text.strip() for text in texts):
                logger.warning(f"ターボ検索: 有効なテキストがないためフォールバック")
                return knowledge_text[:20000]
            
            corpus_tokens = bm25s.tokenize(texts)
            retriever = bm25s.BM25()
            retriever.index(corpus_tokens)
            
            query_tokens = bm25s.tokenize([query])
            results, scores = retriever.retrieve(query_tokens, k=min(max_results, len(chunks)))
            
            # 上位結果を結合
            relevant_content = []
            if results.shape[1] > 0:  # 結果が存在する場合のみ処理
                for i in range(min(results.shape[1], max_results)):
                    chunk_idx = results[0, i]
                    if chunk_idx < len(chunks):
                        relevant_content.append(chunks[chunk_idx]['content'])
            
            if relevant_content:
                final_result = '\n\n'.join(relevant_content)
            else:
                logger.info(f"⚠️ ターボ検索で関連コンテンツが見つからず、フォールバック")
                final_result = knowledge_text[:20000]
            
        except Exception as e:
            logger.error(f"ターボ検索エラー: {e}")
            final_result = knowledge_text[:20000]
        
        elapsed = time.time() - start_time
        logger.info(f"🚀 ターボ検索完了: {elapsed:.2f}秒")
        
        return final_result
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self.cache.clear()
        logger.info("⚡ キャッシュクリア完了")

# グローバルインスタンス
high_speed_rag = HighSpeedRAG()

# 高速化用のユーティリティ関数
@lru_cache(maxsize=100)
def cached_simple_search(text_hash: str, query: str, max_results: int = 10) -> str:
    """LRUキャッシュを使用した簡易検索"""
    # この関数は実際のテキストではなくハッシュをキーにしてキャッシュ
    return f"cached_result_for_{query[:20]}"

def get_text_hash(text: str) -> str:
    """テキストのハッシュ値を取得"""
    return hashlib.md5(text.encode()).hexdigest() 