"""
Enhanced RAG (Retrieval-Augmented Generation) System
統合検索システムを使用した高精度RAG検索機能

s.mdの内容を参考にした統合検索システムを活用
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from .chat_config import safe_print, HTTPException, model
from .unified_search_system import unified_search, UnifiedSearchSystem
from .best_score_search import search_with_best_score
from .chat_utils import expand_query

class EnhancedRAGSystem:
    """拡張RAGシステム"""
    
    def __init__(self):
        self.unified_search = UnifiedSearchSystem()
    
    async def enhanced_rag_search(self, 
                                 query: str, 
                                 company_id: str = None,
                                 limit: int = 10,
                                 use_advanced_features: bool = True,
                                 search_mode: str = "unified") -> List[Dict[str, Any]]:
        """
        統合検索システムを使用した高精度RAG検索
        
        Args:
            query: 検索クエリ
            company_id: 会社ID
            limit: 結果数制限
            use_advanced_features: 高度な機能を使用するか
            search_mode: 検索モード ("unified" または "best_score")
        """
        try:
            safe_print(f"Enhanced RAG検索開始: クエリ='{query}', 会社ID={company_id}, モード={search_mode}")
            start_time = time.time()
            
            # 検索モードに応じて検索を実行
            if search_mode == "best_score":
                # 最高スコア選択型検索
                search_results = await search_with_best_score(
                    query=query,
                    company_id=company_id,
                    limit=limit
                )
            else:
                # 統合検索（デフォルト）
                search_results = await unified_search(
                    query=query,
                    company_id=company_id,
                    limit=limit,
                    use_cache=True,
                    enable_rerank=use_advanced_features
                )
            
            # 検索結果を処理
            processed_results = await self._process_search_results(search_results, query)
            
            execution_time = int((time.time() - start_time) * 1000)
            safe_print(f"Enhanced RAG検索完了: {len(processed_results)}件の結果を{execution_time}msで取得")
            
            return processed_results
            
        except Exception as e:
            safe_print(f"Enhanced RAG検索エラー: {e}")
            return []
    
    async def contextual_enhanced_rag_search(self, 
                                           query: str, 
                                           context: str = "",
                                           company_id: str = None,
                                           limit: int = 10) -> List[Dict[str, Any]]:
        """
        コンテキスト考慮型の拡張RAG検索
        
        Args:
            query: 検索クエリ
            context: 会話コンテキスト
            company_id: 会社ID
            limit: 結果数制限
        """
        try:
            safe_print(f"コンテキスト考慮型RAG検索開始: クエリ='{query}'")
            
            # コンテキストを考慮したクエリ拡張
            enhanced_query = await self._enhance_query_with_context(query, context)
            
            # 複数のクエリで検索
            search_tasks = []
            
            # 元のクエリ
            search_tasks.append(self.enhanced_rag_search(query, company_id, limit // 2, True))
            
            # 拡張クエリ
            if enhanced_query != query:
                search_tasks.append(self.enhanced_rag_search(enhanced_query, company_id, limit // 2, True))
            
            # コンテキストキーワードによる検索
            context_keywords = self._extract_context_keywords(context)
            if context_keywords:
                keyword_query = f"{query} {' '.join(context_keywords[:3])}"
                search_tasks.append(self.enhanced_rag_search(keyword_query, company_id, limit // 3, False))
            
            # 並列実行
            results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # 結果を統合
            all_results = []
            for results in results_list:
                if isinstance(results, Exception):
                    safe_print(f"コンテキスト検索エラー: {results}")
                    continue
                if isinstance(results, list):
                    all_results.extend(results)
            
            # 重複除去とコンテキスト関連度による再スコアリング
            final_results = await self._merge_and_rescore_with_context(all_results, context, limit)
            
            safe_print(f"コンテキスト考慮型RAG検索完了: {len(final_results)}件の結果")
            return final_results
            
        except Exception as e:
            safe_print(f"コンテキスト考慮型RAG検索エラー: {e}")
            return await self.enhanced_rag_search(query, company_id, limit)
    
    async def adaptive_enhanced_rag_search(self, 
                                         query: str, 
                                         company_id: str = None,
                                         limit: int = 10,
                                         context: str = "") -> List[Dict[str, Any]]:
        """
        適応的拡張RAG検索 - クエリの特性に応じて検索戦略を動的に選択
        
        Args:
            query: 検索クエリ
            company_id: 会社ID
            limit: 結果数制限
            context: 会話コンテキスト
        """
        try:
            safe_print(f"適応的拡張RAG検索開始: クエリ='{query}'")
            
            # クエリの特性を分析
            query_analysis = await self._analyze_query_characteristics(query)
            
            # 特性に応じて検索戦略を選択
            if query_analysis['has_context'] and context:
                # コンテキストがある場合
                return await self.contextual_enhanced_rag_search(query, context, company_id, limit)
            elif query_analysis['is_complex']:
                # 複雑なクエリの場合
                return await self._complex_query_search(query, company_id, limit)
            elif query_analysis['is_simple']:
                # シンプルなクエリの場合
                return await self._simple_query_search(query, company_id, limit)
            else:
                # 標準的な検索
                return await self.enhanced_rag_search(query, company_id, limit)
                
        except Exception as e:
            safe_print(f"適応的拡張RAG検索エラー: {e}")
            return await self.enhanced_rag_search(query, company_id, limit)
    
    async def _process_search_results(self, search_results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """検索結果を処理"""
        processed_results = []
        
        for result in search_results:
            # 結果を統一フォーマットに変換
            processed_result = {
                'id': result.get('id', ''),
                'title': result.get('title', 'Unknown'),
                'content': result.get('content', ''),
                'score': result.get('score', 0.0),
                'search_type': result.get('search_type', 'unknown'),
                'metadata': result.get('metadata', {}),
                'url': result.get('metadata', {}).get('url', ''),
                'similarity': result.get('score', 0.0),  # 後方互換性のため
                'snippet': result.get('content', '')  # 後方互換性のため
            }
            
            # ハイライト情報を追加
            processed_result['highlight'] = self._highlight_query_in_content(
                processed_result['content'], query
            )
            
            processed_results.append(processed_result)
        
        return processed_results
    
    async def _enhance_query_with_context(self, query: str, context: str) -> str:
        """コンテキストを考慮したクエリ拡張"""
        if not context:
            return query
        
        try:
            # コンテキストから重要なキーワードを抽出
            context_keywords = self._extract_context_keywords(context)
            
            if context_keywords:
                # 上位3つのキーワードを追加
                enhanced_query = f"{query} {' '.join(context_keywords[:3])}"
                return enhanced_query
            
            return query
            
        except Exception as e:
            safe_print(f"クエリ拡張エラー: {e}")
            return query
    
    def _extract_context_keywords(self, context: str) -> List[str]:
        """コンテキストから重要なキーワードを抽出"""
        if not context:
            return []
        
        import re
        
        # 基本的なキーワード抽出
        keywords = []
        
        # 日本語の重要語を抽出
        # カタカナ語（3文字以上）
        katakana_words = re.findall(r'[ァ-ヶー]{3,}', context)
        keywords.extend(katakana_words)
        
        # 漢字を含む単語（2文字以上）
        kanji_words = re.findall(r'[一-龠]{2,}', context)
        keywords.extend(kanji_words)
        
        # アルファベット（2文字以上）
        alphabet_words = re.findall(r'[a-zA-Z]{2,}', context)
        keywords.extend(alphabet_words)
        
        # 重複を除去し、頻度順でソート
        from collections import Counter
        keyword_counts = Counter(keywords)
        
        # 上位キーワードを返す
        return [keyword for keyword, count in keyword_counts.most_common(5)]
    
    async def _merge_and_rescore_with_context(self, 
                                            results: List[Dict[str, Any]], 
                                            context: str, 
                                            limit: int) -> List[Dict[str, Any]]:
        """コンテキストを考慮した結果の統合と再スコアリング"""
        # 重複除去
        seen_ids = set()
        unique_results = []
        
        for result in results:
            result_id = result.get('id')
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        # コンテキストとの関連度による再スコアリング
        if context:
            context_keywords = self._extract_context_keywords(context)
            context_lower = context.lower()
            
            for result in unique_results:
                content_lower = result.get('content', '').lower()
                
                # コンテキストとの共通キーワード数
                common_keywords = sum(1 for keyword in context_keywords 
                                    if keyword.lower() in content_lower)
                
                # ボーナススコアを追加
                context_bonus = common_keywords * 0.1
                result['score'] = result.get('score', 0) + context_bonus
        
        # スコア順でソート
        unique_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return unique_results[:limit]
    
    async def _analyze_query_characteristics(self, query: str) -> Dict[str, bool]:
        """クエリの特性を分析"""
        analysis = {
            'has_context': False,
            'is_complex': False,
            'is_simple': False,
            'has_japanese': False,
            'is_technical': False
        }
        
        # 長さチェック
        query_length = len(query)
        word_count = len(query.split())
        
        analysis['is_complex'] = query_length > 100 or word_count > 15
        analysis['is_simple'] = query_length <= 20 and word_count <= 5
        
        # 日本語チェック
        analysis['has_japanese'] = any(
            '\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FAF' 
            for char in query
        )
        
        # 技術的キーワードチェック
        technical_keywords = ['API', 'SQL', 'Python', 'JavaScript', 'HTML', 'CSS', 'JSON']
        analysis['is_technical'] = any(keyword.lower() in query.lower() for keyword in technical_keywords)
        
        return analysis
    
    async def _complex_query_search(self, query: str, company_id: str, limit: int) -> List[Dict[str, Any]]:
        """複雑なクエリの検索"""
        # クエリを分割して複数の検索を実行
        query_parts = query.split('。')  # 日本語の文区切り
        
        search_tasks = []
        for part in query_parts:
            if len(part.strip()) > 5:
                search_tasks.append(self.enhanced_rag_search(part.strip(), company_id, limit // 2, True))
        
        # 元のクエリでも検索
        search_tasks.append(self.enhanced_rag_search(query, company_id, limit, True))
        
        results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # 結果を統合
        all_results = []
        for results in results_list:
            if isinstance(results, list):
                all_results.extend(results)
        
        # 重複除去とスコア調整
        seen_ids = set()
        unique_results = []
        
        for result in all_results:
            result_id = result.get('id')
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        # スコア順でソート
        unique_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return unique_results[:limit]
    
    async def _simple_query_search(self, query: str, company_id: str, limit: int) -> List[Dict[str, Any]]:
        """シンプルなクエリの検索"""
        # シンプルなクエリには高速な検索を使用
        return await self.enhanced_rag_search(query, company_id, limit, False)
    
    def _highlight_query_in_content(self, content: str, query: str) -> str:
        """コンテンツ内のクエリをハイライト"""
        if not content or not query:
            return content
        
        try:
            # 基本的なハイライト
            highlighted = content.replace(query, f"<mark>{query}</mark>")
            
            # クエリの一部もハイライト
            for word in query.split():
                if len(word) > 2:
                    highlighted = highlighted.replace(word, f"<mark>{word}</mark>")
            
            return highlighted
            
        except Exception:
            return content
    
    def format_enhanced_search_results(self, results: List[Dict[str, Any]], max_length: int = 3000) -> str:
        """拡張検索結果をフォーマット"""
        if not results:
            return "関連する情報が見つかりませんでした。"
        
        formatted_results = []
        current_length = 0
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'タイトルなし')
            content = result.get('content', '')
            score = result.get('score', 0)
            search_type = result.get('search_type', 'unknown')
            
            # 検索タイプに応じた信頼度表示
            confidence_level = self._get_confidence_level(search_type, score)
            
            # 結果をフォーマット
            formatted_result = f"【結果 {i} - {confidence_level}】\n"
            formatted_result += f"タイトル: {title}\n"
            formatted_result += f"内容: {content[:400]}{'...' if len(content) > 400 else ''}\n"
            formatted_result += f"関連度: {score:.3f} (検索タイプ: {search_type})\n\n"
            
            # 長さチェック
            if current_length + len(formatted_result) > max_length:
                break
            
            formatted_results.append(formatted_result)
            current_length += len(formatted_result)
        
        return ''.join(formatted_results)
    
    def _get_confidence_level(self, search_type: str, score: float) -> str:
        """検索タイプとスコアから信頼度レベルを取得"""
        if search_type == 'exact_match':
            return "完全一致"
        elif search_type == 'llm_rerank':
            return "AI推奨"
        elif search_type == 'vector_search' and score > 0.8:
            return "高関連"
        elif search_type == 'fuzzy_search' and score > 0.6:
            return "部分一致"
        elif score > 0.5:
            return "関連あり"
        else:
            return "参考情報"

# グローバルインスタンス
enhanced_rag_system = EnhancedRAGSystem()

async def enhanced_rag_search(query: str, 
                             company_id: str = None,
                             limit: int = 10,
                             context: str = "",
                             adaptive: bool = True,
                             search_mode: str = "best_score") -> List[Dict[str, Any]]:
    """
    拡張RAG検索のエントリーポイント
    
    Args:
        query: 検索クエリ
        company_id: 会社ID
        limit: 結果数制限
        context: 会話コンテキスト
        adaptive: 適応的検索を使用するか
        search_mode: 検索モード ("unified" または "best_score")
    """
    if adaptive:
        return await enhanced_rag_system.adaptive_enhanced_rag_search(query, company_id, limit, context)
    elif context:
        return await enhanced_rag_system.contextual_enhanced_rag_search(query, context, company_id, limit)
    else:
        return await enhanced_rag_system.enhanced_rag_search(query, company_id, limit, True, search_mode)

def format_enhanced_search_results(results: List[Dict[str, Any]], max_length: int = 3000) -> str:
    """拡張検索結果をフォーマット"""
    return enhanced_rag_system.format_enhanced_search_results(results, max_length) 