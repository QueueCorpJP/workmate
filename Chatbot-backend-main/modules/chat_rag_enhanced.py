"""
拡張RAGシステム (Enhanced RAG System)
PDF後半の重要情報も確実に取得するための拡張チャット用RAGシステム

従来の問題点:
1. 固定LIMIT (10件) でPDF後半のチャンクが除外される
2. 同一文書からの情報が限定的
3. 位置による偏向が修正されない

拡張機能:
1. 動的LIMIT調整 - クエリの複雑さに応じて検索数を調整
2. ドキュメント全体カバレッジ - PDF全体から関連情報を収集
3. 意味的関連性再評価 - LLMを使った関連性スコアリング
4. 結果の多様性保証 - 異なる文書・位置からバランス良く取得
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from .comprehensive_search_system import comprehensive_search
from .chat_rag import format_search_results

logger = logging.getLogger(__name__)

class EnhancedRAGSystem:
    """拡張RAGシステム"""
    
    def __init__(self):
        self.default_initial_limit = 60  # 初期検索の上限を大幅に増加
        self.default_final_limit = 20    # 最終結果数も増加
        self.min_document_diversity = 4  # 最低4つの異なる文書から取得
        
    async def enhanced_rag_search(self,
                                query: str,
                                context: str = "",
                                company_id: str = None,
                                adaptive_limits: bool = True) -> List[Dict[str, Any]]:
        """
        拡張RAG検索の実行
        
        Args:
            query: 検索クエリ
            context: 会話コンテキスト
            company_id: 会社IDフィルタ
            adaptive_limits: 適応的LIMIT調整を使用するか
        """
        try:
            logger.info(f"🔍 拡張RAG検索開始: '{query}'")
            
            # 1. クエリ複雑さ分析による動的LIMIT調整
            initial_limit, final_limit = self._calculate_adaptive_limits(
                query, context
            ) if adaptive_limits else (self.default_initial_limit, self.default_final_limit)
            
            logger.info(f"動的LIMIT設定: 初期={initial_limit}, 最終={final_limit}")
            
            # 2. 包括的検索の実行
            search_results = await comprehensive_search(
                query=query,
                company_id=company_id,
                initial_limit=initial_limit,
                final_limit=final_limit
            )
            
            if not search_results:
                logger.warning("拡張RAG検索: 結果が見つかりませんでした")
                return []
            
            # 3. コンテキスト考慮の関連性再評価
            if context:
                search_results = self._rerank_with_context(search_results, query, context)
            
            # 4. 文書カバレッジ分析とログ出力
            coverage_info = self._analyze_document_coverage(search_results)
            self._log_enhanced_rag_summary(search_results, coverage_info, query)
            
            logger.info(f"✅ 拡張RAG検索完了: {len(search_results)}件の高品質結果")
            return search_results
            
        except Exception as e:
            logger.error(f"❌ 拡張RAG検索エラー: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _calculate_adaptive_limits(self, query: str, context: str = "") -> Tuple[int, int]:
        """クエリの複雑さに基づく動的LIMIT計算"""
        
        # 基本計算要素
        query_length = len(query)
        query_words = len(query.split())
        context_length = len(context) if context else 0
        
        # 複雑さ指標の計算
        complexity_score = 0
        
        # 1. クエリ長による調整
        if query_length > 100:
            complexity_score += 3  # 長いクエリは詳細な回答が必要
        elif query_length > 50:
            complexity_score += 2
        elif query_length > 20:
            complexity_score += 1
        
        # 2. 単語数による調整
        if query_words > 15:
            complexity_score += 2  # 多くの概念を含む複雑なクエリ
        elif query_words > 8:
            complexity_score += 1
        
        # 3. 専門用語・技術用語の検出
        technical_keywords = [
            '手順', '方法', '仕組み', '原理', '詳細', '比較', '違い', '効果',
            'API', 'システム', '実装', '設計', '開発', '運用', '管理',
            '分析', '評価', '改善', '最適', '戦略', '計画'
        ]
        
        technical_count = sum(1 for keyword in technical_keywords if keyword in query)
        complexity_score += min(technical_count, 3)  # 最大3点
        
        # 4. 疑問詞による調整（詳細な説明が必要）
        question_words = ['どのように', 'なぜ', 'どうして', 'いつ', 'どこで', 'だれが', '何を']
        question_count = sum(1 for qword in question_words if qword in query)
        complexity_score += min(question_count, 2)  # 最大2点
        
        # 5. コンテキストの長さによる調整
        if context_length > 500:
            complexity_score += 2  # 長いコンテキストは継続的な議論
        elif context_length > 200:
            complexity_score += 1
        
        # 複雑さスコアに基づくLIMIT計算
        base_initial = self.default_initial_limit
        base_final = self.default_final_limit
        
        # 複雑さに応じた倍率
        if complexity_score >= 8:
            multiplier = 2.0  # 非常に複雑
        elif complexity_score >= 6:
            multiplier = 1.7  # 複雑
        elif complexity_score >= 4:
            multiplier = 1.4  # やや複雑
        elif complexity_score >= 2:
            multiplier = 1.2  # 標準より少し複雑
        else:
            multiplier = 1.0  # 標準
        
        initial_limit = min(int(base_initial * multiplier), 100)  # 最大100件
        final_limit = min(int(base_final * multiplier), 30)       # 最大30件
        
        logger.info(f"複雑さ分析: スコア={complexity_score}, 倍率={multiplier:.1f}")
        
        return initial_limit, final_limit
    
    def _rerank_with_context(self, 
                           results: List[Dict[str, Any]], 
                           query: str, 
                           context: str) -> List[Dict[str, Any]]:
        """コンテキストを考慮した関連性再評価"""
        
        # コンテキストから重要キーワードを抽出
        context_keywords = self._extract_context_keywords(context)
        query_keywords = set(query.lower().split())
        
        # 各結果のコンテキスト関連性スコアを計算
        for result in results:
            content = result.get('content', '').lower()
            content_words = set(content.split())
            
            # コンテキストとの関連性
            context_relevance = 0
            for keyword in context_keywords:
                if keyword in content:
                    context_relevance += 0.1
            
            # クエリとの直接関連性
            query_relevance = len(query_keywords & content_words) / max(len(query_keywords), 1)
            
            # 総合関連性スコア
            context_bonus = context_relevance + query_relevance * 0.2
            
            # 既存スコアに追加
            original_score = result.get('score', 0)
            result['score'] = original_score + context_bonus
            
            # メタデータに詳細を記録
            if 'metadata' not in result:
                result['metadata'] = {}
            result['metadata']['context_bonus'] = context_bonus
            result['metadata']['context_relevance'] = context_relevance
            result['metadata']['query_relevance'] = query_relevance
        
        # 更新されたスコアで再ソート
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return results
    
    def _extract_context_keywords(self, context: str) -> List[str]:
        """コンテキストから重要キーワードを抽出"""
        if not context:
            return []
        
        # 基本的なキーワード抽出
        import re
        
        keywords = []
        
        # 名詞句の抽出（カタカナ・漢字・英語）
        kanji_katakana = re.findall(r'[一-龠々〆〤ァ-ヶー]{2,}', context)
        keywords.extend(kanji_katakana)
        
        english_words = re.findall(r'[a-zA-Z]{3,}', context)
        keywords.extend(english_words)
        
        # 重複除去と頻度順ソート
        keyword_freq = {}
        for keyword in keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        # 頻度順でソートして上位を返す
        sorted_keywords = sorted(keyword_freq.keys(), 
                               key=lambda x: keyword_freq[x], 
                               reverse=True)
        
        return sorted_keywords[:10]  # 上位10個のキーワード
    
    def _analyze_document_coverage(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """文書カバレッジの分析"""
        if not results:
            return {}
        
        document_stats = {}
        position_distribution = {"前半": 0, "中盤": 0, "後半": 0}
        
        for result in results:
            doc_name = result.get('document_name', 'Unknown')
            doc_coverage = result.get('document_coverage', 0)
            
            # 文書別統計
            if doc_name not in document_stats:
                document_stats[doc_name] = {
                    'count': 0,
                    'min_coverage': 1.0,
                    'max_coverage': 0.0,
                    'avg_score': 0.0,
                    'total_score': 0.0
                }
            
            stats = document_stats[doc_name]
            stats['count'] += 1
            stats['min_coverage'] = min(stats['min_coverage'], doc_coverage)
            stats['max_coverage'] = max(stats['max_coverage'], doc_coverage)
            stats['total_score'] += result.get('score', 0)
            stats['avg_score'] = stats['total_score'] / stats['count']
            
            # 位置分布
            if doc_coverage <= 0.33:
                position_distribution["前半"] += 1
            elif doc_coverage <= 0.66:
                position_distribution["中盤"] += 1
            else:
                position_distribution["後半"] += 1
        
        return {
            'document_stats': document_stats,
            'position_distribution': position_distribution,
            'total_documents': len(document_stats),
            'total_results': len(results)
        }
    
    def _log_enhanced_rag_summary(self, 
                                results: List[Dict[str, Any]], 
                                coverage_info: Dict[str, Any], 
                                query: str):
        """拡張RAG検索結果のサマリーログ"""
        
        logger.info("📊 拡張RAG検索サマリー:")
        logger.info(f"  クエリ: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        logger.info(f"  総結果数: {coverage_info.get('total_results', 0)}")
        logger.info(f"  対象文書数: {coverage_info.get('total_documents', 0)}")
        
        # 位置分布
        pos_dist = coverage_info.get('position_distribution', {})
        logger.info("  位置分布:")
        for position, count in pos_dist.items():
            percentage = (count / coverage_info.get('total_results', 1)) * 100
            logger.info(f"    {position}: {count}件 ({percentage:.1f}%)")
        
        # 文書別統計（上位5文書）
        doc_stats = coverage_info.get('document_stats', {})
        sorted_docs = sorted(doc_stats.items(), 
                           key=lambda x: x[1]['count'], 
                           reverse=True)
        
        logger.info("  主要文書（上位5文書）:")
        for doc_name, stats in sorted_docs[:5]:
            coverage_range = f"{stats['min_coverage']:.1%}-{stats['max_coverage']:.1%}"
            logger.info(f"    {doc_name}: {stats['count']}件, "
                       f"カバレッジ範囲: {coverage_range}, "
                       f"平均スコア: {stats['avg_score']:.3f}")
        
        # 高スコア結果の詳細（上位3件）
        logger.info("  高スコア結果（上位3件）:")
        for i, result in enumerate(results[:3], 1):
            score = result.get('score', 0)
            doc_name = result.get('document_name', 'Unknown')
            coverage = result.get('document_coverage', 0)
            content_preview = result.get('content', '')[:100] + '...'
            
            logger.info(f"    {i}. {doc_name} (スコア: {score:.3f}, "
                       f"位置: {coverage:.1%})")
            logger.info(f"       内容: {content_preview}")

# グローバルインスタンス
enhanced_rag_system = EnhancedRAGSystem()

async def enhanced_rag_search(query: str, 
                            context: str = "", 
                            company_id: str = None,
                            adaptive_limits: bool = True) -> List[Dict[str, Any]]:
    """拡張RAG検索の実行（外部インターフェース）"""
    return await enhanced_rag_system.enhanced_rag_search(
        query, context, company_id, adaptive_limits
    )

def enhanced_format_search_results(results: List[Dict[str, Any]], 
                                 max_length: int = 3000) -> str:
    """拡張された検索結果フォーマット（従来より多くの情報を含む）"""
    if not results:
        return "関連する情報が見つかりませんでした。"
    
    formatted_results = []
    current_length = 0
    
    for i, result in enumerate(results, 1):
        # 文書情報の取得
        doc_name = result.get('document_name', 'タイトルなし')
        content = result.get('content', '')
        score = result.get('score', 0)
        chunk_index = result.get('chunk_index', 0)
        doc_coverage = result.get('document_coverage', 0)
        
        # メタデータの取得
        metadata = result.get('metadata', {})
        search_methods = result.get('search_methods', [])
        
        # 結果フォーマット（詳細版）
        formatted_result = f"【結果 {i}】\n"
        formatted_result += f"文書: {doc_name}\n"
        formatted_result += f"チャンク: #{chunk_index} (文書内位置: {doc_coverage:.1%})\n"
        
        # 検索方法の表示
        if search_methods:
            methods_str = ', '.join(search_methods) if isinstance(search_methods, list) else str(search_methods)
            formatted_result += f"検索方法: {methods_str}\n"
        
        # 内容
        content_length = min(600, max_length - current_length - 200)  # より多くの内容を含む
        if content_length > 0:
            formatted_result += f"内容: {content[:content_length]}{'...' if len(content) > content_length else ''}\n"
        
        # 関連度スコア
        if score > 0:
            formatted_result += f"関連度: {score:.3f}\n"
        
        formatted_result += "\n"
        
        # 長さチェック
        if current_length + len(formatted_result) > max_length:
            break
        
        formatted_results.append(formatted_result)
        current_length += len(formatted_result)
    
    result_text = ''.join(formatted_results)
    
    # サマリー情報を追加
    doc_count = len(set(r.get('document_name', 'Unknown') for r in results))
    summary = f"\n📊 検索サマリー: {len(results)}件の結果を{doc_count}個の文書から取得\n"
    
    return result_text + summary 