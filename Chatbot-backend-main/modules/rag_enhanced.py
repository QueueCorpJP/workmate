"""
強化されたRAGシステム
ハイブリッド検索とセマンティック検索を組み合わせた高精度検索システム
"""
import json
import re
import asyncio
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """検索結果を格納するデータクラス"""
    content: str
    score: float
    source: str
    chunk_id: str
    metadata: Dict = None

class EnhancedRAGSystem:
    """強化されたRAGシステム"""
    
    def __init__(self):
        self.embeddings_cache = {}
        self.chunk_cache = {}
        self.search_history = []
        
    async def smart_chunking(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        """
        インテリジェントなチャンク化
        - セマンティックな境界を考慮
        - オーバーラップによる文脈保持
        - 階層的構造の認識
        """
        chunks = []
        
        # 1. 文書構造の分析
        sections = self._identify_document_structure(text)
        
        # 2. セクションごとにチャンク化
        chunk_id = 0
        for section in sections:
            section_chunks = self._chunk_section(
                section, chunk_size, overlap, chunk_id
            )
            chunks.extend(section_chunks)
            chunk_id += len(section_chunks)
        
        return chunks
    
    def _identify_document_structure(self, text: str) -> List[Dict]:
        """文書構造を特定してセクションに分割"""
        sections = []
        lines = text.split('\n')
        
        current_section = {'title': '', 'content': '', 'level': 0}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 見出しパターンの検出
            heading_level = self._detect_heading_level(line)
            
            if heading_level > 0:
                # 前のセクションを保存
                if current_section['content']:
                    sections.append(current_section.copy())
                
                # 新しいセクションを開始
                current_section = {
                    'title': line,
                    'content': '',
                    'level': heading_level
                }
            else:
                current_section['content'] += line + '\n'
        
        # 最後のセクションを追加
        if current_section['content']:
            sections.append(current_section)
        
        return sections
    
    def _detect_heading_level(self, line: str) -> int:
        """見出しレベルを検出"""
        # Markdownスタイル見出し
        if line.startswith('#'):
            return len(line) - len(line.lstrip('#'))
        
        # 数字付き見出し
        if re.match(r'^\d+\.', line):
            return 1
        
        # 大文字のみの行
        if line.isupper() and len(line) > 3:
            return 2
        
        # 特定のキーワードで始まる行
        heading_keywords = ['第', '章', '節', '項', '概要', '詳細', '手順', '方法']
        if any(line.startswith(kw) for kw in heading_keywords):
            return 2
        
        return 0
    
    def _chunk_section(self, section: Dict, chunk_size: int, overlap: int, start_id: int) -> List[Dict]:
        """セクションを適切なサイズのチャンクに分割"""
        chunks = []
        content = section['content']
        title = section['title']
        
        if len(content) <= chunk_size:
            # セクション全体が1チャンクに収まる場合
            chunks.append({
                'id': f"chunk_{start_id}",
                'content': f"{title}\n{content}" if title else content,
                'title': title,
                'section_level': section['level'],
                'metadata': {
                    'section_title': title,
                    'section_level': section['level'],
                    'chunk_type': 'complete_section'
                }
            })
        else:
            # セクションを複数のチャンクに分割
            sentences = self._split_into_sentences(content)
            current_chunk = title + '\n' if title else ''
            current_size = len(current_chunk)
            chunk_count = 0
            
            for sentence in sentences:
                sentence_size = len(sentence)
                
                if current_size + sentence_size > chunk_size and current_chunk.strip():
                    # 現在のチャンクを保存
                    chunks.append({
                        'id': f"chunk_{start_id + chunk_count}",
                        'content': current_chunk.strip(),
                        'title': title,
                        'section_level': section['level'],
                        'metadata': {
                            'section_title': title,
                            'section_level': section['level'],
                            'chunk_type': 'partial_section',
                            'chunk_index': chunk_count
                        }
                    })
                    
                    # 新しいチャンクを開始（オーバーラップを考慮）
                    overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                    current_chunk = overlap_text + sentence
                    current_size = len(current_chunk)
                    chunk_count += 1
                else:
                    current_chunk += sentence
                    current_size += sentence_size
            
            # 最後のチャンクを追加
            if current_chunk.strip():
                chunks.append({
                    'id': f"chunk_{start_id + chunk_count}",
                    'content': current_chunk.strip(),
                    'title': title,
                    'section_level': section['level'],
                    'metadata': {
                        'section_title': title,
                        'section_level': section['level'],
                        'chunk_type': 'partial_section',
                        'chunk_index': chunk_count
                    }
                })
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """テキストを文単位で分割"""
        # 日本語の句読点を考慮した文分割
        sentences = re.split(r'[。！？\n]', text)
        result = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                result.append(sentence + '。')
        
        return result
    
    async def hybrid_search(self, query: str, chunks: List[Dict], top_k: int = 20) -> List[SearchResult]:
        """
        ハイブリッド検索の実行
        BM25とセマンティック検索を組み合わせ
        """
        # 1. BM25検索
        bm25_results = await self._bm25_search(query, chunks, top_k * 2)
        
        # 2. セマンティック検索（仮想的な実装）
        semantic_results = await self._semantic_search(query, chunks, top_k * 2)
        
        # 3. スコアの組み合わせと再ランキング
        combined_results = self._combine_and_rerank(
            query, bm25_results, semantic_results, top_k
        )
        
        return combined_results
    
    async def _bm25_search(self, query: str, chunks: List[Dict], top_k: int) -> List[SearchResult]:
        """BM25検索の実行"""
        try:
            import bm25s
            
            # チャンクからテキストを抽出
            texts = [chunk['content'] for chunk in chunks]
            
            # BM25インデックスの作成
            corpus_tokens = bm25s.tokenize(texts)
            retriever = bm25s.BM25()
            retriever.index(corpus_tokens)
            
            # 検索実行
            query_tokens = bm25s.tokenize([query])
            results, scores = retriever.retrieve(query_tokens, k=min(top_k, len(chunks)))
            
            # 結果をSearchResultオブジェクトに変換
            search_results = []
            for i in range(min(results.shape[1], len(chunks))):
                chunk_idx = results[0, i]
                if chunk_idx < len(chunks):
                    chunk = chunks[chunk_idx]
                    score = float(scores[0, i]) if i < len(scores[0]) else 0.0
                    
                    search_results.append(SearchResult(
                        content=chunk['content'],
                        score=score,
                        source='bm25',
                        chunk_id=chunk['id'],
                        metadata=chunk.get('metadata', {})
                    ))
            
            return search_results
        
        except Exception as e:
            logger.error(f"BM25検索エラー: {e}")
            return []
    
    async def _semantic_search(self, query: str, chunks: List[Dict], top_k: int) -> List[SearchResult]:
        """
        セマンティック検索の実行
        注意: 実際の実装では埋め込みモデル（OpenAI, Sentence-BERT等）が必要
        """
        try:
            # ここでは簡単なキーワードマッチングで代替
            # 実際の実装では埋め込みベクトルを使用
            results = []
            query_terms = set(query.lower().split())
            
            for chunk in chunks:
                content_terms = set(chunk['content'].lower().split())
                
                # Jaccard係数でスコア計算
                intersection = len(query_terms & content_terms)
                union = len(query_terms | content_terms)
                score = intersection / union if union > 0 else 0.0
                
                if score > 0:
                    results.append(SearchResult(
                        content=chunk['content'],
                        score=score,
                        source='semantic',
                        chunk_id=chunk['id'],
                        metadata=chunk.get('metadata', {})
                    ))
            
            # スコア順でソート
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
        
        except Exception as e:
            logger.error(f"セマンティック検索エラー: {e}")
            return []
    
    def _combine_and_rerank(self, query: str, bm25_results: List[SearchResult], 
                           semantic_results: List[SearchResult], top_k: int) -> List[SearchResult]:
        """BM25とセマンティック検索の結果を組み合わせて再ランキング"""
        
        # 結果をチャンクIDでグループ化
        combined_scores = {}
        all_results = {}
        
        # BM25結果を処理
        for result in bm25_results:
            chunk_id = result.chunk_id
            combined_scores[chunk_id] = combined_scores.get(chunk_id, 0) + result.score * 0.6  # BM25の重み
            all_results[chunk_id] = result
        
        # セマンティック結果を処理
        for result in semantic_results:
            chunk_id = result.chunk_id
            combined_scores[chunk_id] = combined_scores.get(chunk_id, 0) + result.score * 0.4  # セマンティックの重み
            if chunk_id not in all_results:
                all_results[chunk_id] = result
        
        # 追加の再ランキング要素
        for chunk_id, result in all_results.items():
            # セクションレベルボーナス
            section_level = result.metadata.get('section_level', 0)
            if section_level > 0:
                combined_scores[chunk_id] += 0.1 * (3 - section_level)  # より高いレベルの見出しにボーナス
            
            # タイトルマッチボーナス
            title = result.metadata.get('section_title', '')
            if title and any(term in title.lower() for term in query.lower().split()):
                combined_scores[chunk_id] += 0.2
        
        # 最終結果を作成
        final_results = []
        for chunk_id in sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True):
            result = all_results[chunk_id]
            result.score = combined_scores[chunk_id]
            final_results.append(result)
        
        return final_results[:top_k]
    
    async def iterative_search(self, query: str, knowledge_text: str, 
                              max_iterations: int = 3, min_results: int = 5) -> str:
        """
        反復検索システム
        満足な結果が得られるまで検索戦略を変更して繰り返し実行
        """
        # 最初のチャンク化
        chunks = await self.smart_chunking(knowledge_text)
        logger.info(f"初期チャンク数: {len(chunks)}")
        
        best_results = []
        iteration = 0
        
        # 検索戦略のリスト
        search_strategies = [
            {'top_k': 10, 'chunk_size': 1000, 'overlap': 200},
            {'top_k': 20, 'chunk_size': 1500, 'overlap': 300},
            {'top_k': 30, 'chunk_size': 800, 'overlap': 150}
        ]
        
        while iteration < max_iterations and len(best_results) < min_results:
            strategy = search_strategies[iteration] if iteration < len(search_strategies) else search_strategies[-1]
            
            logger.info(f"検索反復 {iteration + 1}: {strategy}")
            
            # チャンク化の調整（必要に応じて）
            if iteration > 0:
                chunks = await self.smart_chunking(
                    knowledge_text, 
                    strategy['chunk_size'], 
                    strategy['overlap']
                )
            
            # ハイブリッド検索実行
            results = await self.hybrid_search(query, chunks, strategy['top_k'])
            
            # 結果の品質評価
            quality_results = self._evaluate_results_quality(query, results)
            
            if quality_results:
                best_results.extend(quality_results)
                # 重複削除
                best_results = self._deduplicate_results(best_results)
            
            iteration += 1
            
            # 十分な高品質結果が得られた場合は早期終了
            if len([r for r in best_results if r.score > 0.5]) >= min_results:
                break
        
        # 最終結果の組み立て
        return self._format_final_results(best_results, query)
    
    def _evaluate_results_quality(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """検索結果の品質を評価"""
        quality_results = []
        query_terms = set(query.lower().split())
        
        for result in results:
            content_terms = set(result.content.lower().split())
            
            # 品質指標の計算
            term_coverage = len(query_terms & content_terms) / len(query_terms)
            content_length = len(result.content)
            
            # 品質スコアの調整
            quality_score = result.score
            
            # 長すぎず短すぎないコンテンツを優先
            if 100 <= content_length <= 2000:
                quality_score += 0.1
            
            # クエリ用語の適切な含有率
            if term_coverage >= 0.3:
                quality_score += 0.2
            
            # 最小品質閾値
            if quality_score > 0.2:
                result.score = quality_score
                quality_results.append(result)
        
        return sorted(quality_results, key=lambda x: x.score, reverse=True)
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """結果の重複を除去"""
        seen_content = set()
        deduplicated = []
        
        for result in results:
            # コンテンツの先頭100文字で重複チェック
            content_key = result.content[:100]
            if content_key not in seen_content:
                seen_content.add(content_key)
                deduplicated.append(result)
        
        return deduplicated
    
    def _format_final_results(self, results: List[SearchResult], query: str) -> str:
        """最終結果をフォーマット"""
        if not results:
            return ""
        
        # スコア順でソート
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)
        
        # 上位結果を結合
        formatted_content = []
        total_length = 0
        max_length = 100000  # 最大文字数制limit
        
        for i, result in enumerate(sorted_results):
            if total_length + len(result.content) > max_length:
                break
            
            section_title = result.metadata.get('section_title', '')
            content = result.content
            
            if section_title and not content.startswith(section_title):
                content = f"{section_title}\n{content}"
            
            formatted_content.append(f"=== 関連情報 {i+1} (スコア: {result.score:.3f}) ===\n{content}")
            total_length += len(result.content)
        
        return "\n\n".join(formatted_content)

# グローバルインスタンス
enhanced_rag = EnhancedRAGSystem() 