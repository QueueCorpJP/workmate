"""
包括的検索システム (Comprehensive Search System)
PDFの後半や低頻度な重要情報も確実に取得するための高度な検索システム

主な機能:
1. 動的LIMIT調整 - 検索品質に応じて結果数を調整
2. 多段階検索 - 広範囲検索 → 重要度フィルタリング
3. 位置バイアス補正 - チャンク位置による偏りを修正
4. ドキュメント多様性確保 - 同じ文書から複数の関連チャンクを取得
5. セマンティック再ランキング - 意味的関連性で再評価
"""

import asyncio
import logging
import math
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict
from supabase_adapter import execute_query
from .enhanced_postgresql_search import enhanced_search_chunks
from .advanced_fuzzy_search import AdvancedFuzzySearchSystem
from .vector_search import get_vector_search_instance

logger = logging.getLogger(__name__)

@dataclass
class ComprehensiveSearchResult:
    """包括的検索結果"""
    chunk_id: str
    content: str
    document_name: str
    document_id: str
    chunk_index: int
    relevance_score: float
    position_bias_score: float
    final_score: float
    search_methods: List[str]
    document_coverage: float  # 文書内での位置（0.0-1.0）
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.chunk_id,
            'content': self.content,
            'document_name': self.document_name,
            'score': self.final_score,
            'chunk_index': self.chunk_index,
            'search_methods': self.search_methods,
            'document_coverage': self.document_coverage,
            'metadata': {
                'relevance_score': self.relevance_score,
                'position_bias_score': self.position_bias_score,
                'document_id': self.document_id
            }
        }

class ComprehensiveSearchSystem:
    """包括的検索システム"""
    
    def __init__(self):
        self.advanced_fuzzy = AdvancedFuzzySearchSystem()
        self.vector_search = get_vector_search_instance()
        
    async def initialize(self):
        """システム初期化"""
        try:
            await self.advanced_fuzzy.initialize()
            logger.info("✅ 包括的検索システム初期化完了")
            return True
        except Exception as e:
            logger.error(f"❌ 包括的検索システム初期化エラー: {e}")
            return False
    
    async def comprehensive_search(self,
                                 query: str,
                                 company_id: str = None,
                                 initial_limit: int = 50,
                                 final_limit: int = 15,
                                 min_document_diversity: int = 3) -> List[ComprehensiveSearchResult]:
        """
        包括的検索の実行
        
        Args:
            query: 検索クエリ
            company_id: 会社ID
            initial_limit: 初期検索での結果数上限
            final_limit: 最終的に返す結果数
            min_document_diversity: 最小文書多様性（異なる文書からの結果数）
        """
        try:
            logger.info(f"🔍 包括的検索開始: '{query}' (初期限界: {initial_limit}, 最終: {final_limit})")
            
            # 1. 多段階検索の実行
            all_results = await self._execute_multi_stage_search(query, company_id, initial_limit)
            
            if not all_results:
                logger.warning("❌ 検索結果が見つかりませんでした")
                return []
            
            # 2. 文書別チャンク分析
            document_analysis = self._analyze_document_chunks(all_results)
            
            # 3. 位置バイアス補正
            corrected_results = self._apply_position_bias_correction(all_results, document_analysis)
            
            # 4. ドキュメント多様性確保
            diverse_results = self._ensure_document_diversity(
                corrected_results, 
                min_document_diversity, 
                final_limit
            )
            
            # 5. 最終スコアリング・ランキング
            final_results = self._final_ranking(diverse_results, query)[:final_limit]
            
            logger.info(f"✅ 包括的検索完了: {len(final_results)}件の結果")
            self._log_search_summary(final_results, document_analysis)
            
            return final_results
            
        except Exception as e:
            logger.error(f"❌ 包括的検索エラー: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def _execute_multi_stage_search(self,
                                        query: str,
                                        company_id: str,
                                        limit: int) -> List[Dict[str, Any]]:
        """多段階検索の実行"""
        all_results = []
        search_methods = []
        
        try:
            # Stage 1: Enhanced PostgreSQL Search（高い閾値で広範囲検索）
            logger.info("📊 Stage 1: Enhanced PostgreSQL 広範囲検索")
            enhanced_results = await enhanced_search_chunks(
                query, company_id, limit=limit*2, threshold=0.1
            )
            all_results.extend(self._normalize_search_results(enhanced_results, "enhanced_postgresql"))
            search_methods.append(f"enhanced_postgresql({len(enhanced_results)})")
            
            # Stage 2: Advanced Fuzzy Search（閾値を下げて網羅的に）
            logger.info("📊 Stage 2: Advanced Fuzzy 網羅的検索")
            fuzzy_results = await self.advanced_fuzzy.advanced_fuzzy_search(
                query, company_id, threshold=0.3, limit=limit
            )
            fuzzy_normalized = [r.to_dict() for r in fuzzy_results]
            all_results.extend(self._normalize_search_results(fuzzy_normalized, "advanced_fuzzy"))
            search_methods.append(f"advanced_fuzzy({len(fuzzy_results)})")
            
            # Stage 3: ベクトル検索（セマンティック類似性）
            if self.vector_search:
                logger.info("📊 Stage 3: Vector セマンティック検索")
                try:
                    vector_results = self.vector_search.vector_similarity_search(
                        query, company_id, limit=limit//2
                    )
                    all_results.extend(self._normalize_search_results(vector_results, "vector_semantic"))
                    search_methods.append(f"vector_semantic({len(vector_results)})")
                except Exception as e:
                    logger.warning(f"⚠️ ベクトル検索エラー: {e}")
            
            # Stage 4: キーワード分割検索（重要語句での個別検索）
            logger.info("📊 Stage 4: キーワード分割検索")
            keyword_results = await self._keyword_based_search(query, company_id, limit//3)
            all_results.extend(keyword_results)
            search_methods.append(f"keyword_split({len(keyword_results)})")
            
            logger.info(f"多段階検索完了: 総結果数 {len(all_results)}, 手法: {search_methods}")
            return all_results
            
        except Exception as e:
            logger.error(f"多段階検索エラー: {e}")
            return all_results
    
    def _normalize_search_results(self, results: List[Dict], search_method: str) -> List[Dict[str, Any]]:
        """検索結果の正規化"""
        normalized = []
        for result in results:
            normalized_result = {
                'chunk_id': str(result.get('id', result.get('chunk_id', ''))),
                'content': result.get('content', ''),
                'document_name': result.get('document_name', result.get('file_name', 'Unknown')),
                'document_id': str(result.get('doc_id', result.get('document_id', ''))),
                'chunk_index': int(result.get('chunk_index', 0)),
                'score': float(result.get('score', result.get('final_score', 0))),
                'search_method': search_method,
                'metadata': result.get('metadata', {})
            }
            normalized.append(normalized_result)
        return normalized
    
    async def _keyword_based_search(self, query: str, company_id: str, limit: int) -> List[Dict[str, Any]]:
        """キーワード分割に基づく検索"""
        results = []
        
        # 重要キーワードを抽出
        keywords = self._extract_important_keywords(query)
        
        for keyword in keywords[:3]:  # 上位3つのキーワード
            try:
                # キーワード単体での検索
                keyword_results = await enhanced_search_chunks(
                    keyword, company_id, limit=limit//3, threshold=0.15
                )
                
                # スコア調整（分割検索のため少し下げる）
                for result in keyword_results:
                    if 'score' in result:
                        result['score'] *= 0.8
                
                normalized = self._normalize_search_results(keyword_results, f"keyword_{keyword}")
                results.extend(normalized)
                
            except Exception as e:
                logger.warning(f"キーワード検索エラー ({keyword}): {e}")
        
        return results
    
    def _extract_important_keywords(self, query: str) -> List[str]:
        """重要キーワードの抽出"""
        # 基本的なキーワード抽出（今後より高度な手法に置き換え可能）
        import re
        
        keywords = []
        
        # 漢字・カタカナの連続（2文字以上）
        kanji_katakana = re.findall(r'[一-龠々〆〤ァ-ヶー]{2,}', query)
        keywords.extend(kanji_katakana)
        
        # 英数字の連続（2文字以上）
        alphanumeric = re.findall(r'[a-zA-Z0-9]{2,}', query)
        keywords.extend(alphanumeric)
        
        # 重複除去・長さ順ソート
        unique_keywords = list(set(keywords))
        unique_keywords.sort(key=len, reverse=True)
        
        return unique_keywords
    
    def _analyze_document_chunks(self, results: List[Dict[str, Any]]) -> Dict[str, Dict]:
        """文書別チャンク分析"""
        analysis = defaultdict(lambda: {
            'chunks': [],
            'max_chunk_index': 0,
            'min_chunk_index': float('inf'),
            'total_chunks': 0,
            'coverage': 0.0
        })
        
        # 文書ごとの情報集計
        for result in results:
            doc_id = result.get('document_id', 'unknown')
            chunk_index = result.get('chunk_index', 0)
            
            analysis[doc_id]['chunks'].append(result)
            analysis[doc_id]['max_chunk_index'] = max(
                analysis[doc_id]['max_chunk_index'], chunk_index
            )
            analysis[doc_id]['min_chunk_index'] = min(
                analysis[doc_id]['min_chunk_index'], chunk_index
            )
        
        # 各文書の総チャンク数を取得（データベースから）
        for doc_id in analysis.keys():
            try:
                chunk_count_sql = f"""
                    SELECT MAX(chunk_index) + 1 as total_chunks
                    FROM chunks 
                    WHERE doc_id = '{doc_id}'
                """
                result = execute_query(chunk_count_sql)
                if result and len(result) > 0:
                    analysis[doc_id]['total_chunks'] = result[0].get('total_chunks', 1)
                else:
                    analysis[doc_id]['total_chunks'] = analysis[doc_id]['max_chunk_index'] + 1
                
                # カバレッジ計算
                covered_range = analysis[doc_id]['max_chunk_index'] - analysis[doc_id]['min_chunk_index'] + 1
                analysis[doc_id]['coverage'] = covered_range / analysis[doc_id]['total_chunks']
                
            except Exception as e:
                logger.warning(f"文書分析エラー ({doc_id}): {e}")
                analysis[doc_id]['total_chunks'] = analysis[doc_id]['max_chunk_index'] + 1
                analysis[doc_id]['coverage'] = 0.5  # デフォルト値
        
        return dict(analysis)
    
    def _apply_position_bias_correction(self, 
                                      results: List[Dict[str, Any]], 
                                      doc_analysis: Dict) -> List[ComprehensiveSearchResult]:
        """位置バイアス補正の適用"""
        corrected_results = []
        
        for result in results:
            doc_id = result.get('document_id', 'unknown')
            chunk_index = result.get('chunk_index', 0)
            original_score = result.get('score', 0)
            
            # 文書内での位置計算（0.0-1.0）
            doc_info = doc_analysis.get(doc_id, {})
            total_chunks = doc_info.get('total_chunks', 1)
            document_coverage = chunk_index / max(total_chunks - 1, 1)
            
            # 位置バイアス補正スコア計算
            position_bias_score = self._calculate_position_bias_correction(
                chunk_index, total_chunks, document_coverage
            )
            
            # 最終スコア計算
            final_score = original_score + position_bias_score
            
            corrected_result = ComprehensiveSearchResult(
                chunk_id=result.get('chunk_id', ''),
                content=result.get('content', ''),
                document_name=result.get('document_name', 'Unknown'),
                document_id=doc_id,
                chunk_index=chunk_index,
                relevance_score=original_score,
                position_bias_score=position_bias_score,
                final_score=final_score,
                search_methods=[result.get('search_method', 'unknown')],
                document_coverage=document_coverage
            )
            
            corrected_results.append(corrected_result)
        
        return corrected_results
    
    def _calculate_position_bias_correction(self, 
                                          chunk_index: int, 
                                          total_chunks: int, 
                                          coverage: float) -> float:
        """位置バイアス補正値の計算"""
        if total_chunks <= 1:
            return 0.0
        
        # 後半チャンクにボーナスを付与（前半偏重を補正）
        if coverage > 0.7:  # 文書の後半70%以降
            position_bonus = 0.15 * (coverage - 0.7) / 0.3  # 最大0.15のボーナス
        elif coverage > 0.5:  # 中盤
            position_bonus = 0.05 * (coverage - 0.5) / 0.2  # 最大0.05のボーナス
        else:  # 前半
            position_bonus = 0.0
        
        # 文書の分散具合に応じた調整
        if total_chunks > 10:  # 長文書の場合
            position_bonus *= 1.5  # より強い補正
        
        return position_bonus
    
    def _ensure_document_diversity(self, 
                                 results: List[ComprehensiveSearchResult],
                                 min_diversity: int,
                                 final_limit: int) -> List[ComprehensiveSearchResult]:
        """ドキュメント多様性の確保"""
        # 文書別グループ化
        doc_groups = defaultdict(list)
        for result in results:
            doc_groups[result.document_id].append(result)
        
        # 各文書グループ内でスコア順ソート
        for doc_id in doc_groups:
            doc_groups[doc_id].sort(key=lambda x: x.final_score, reverse=True)
        
        # 多様性確保アルゴリズム
        diverse_results = []
        used_documents = set()
        
        # Phase 1: 各文書から最低1つずつ取得
        for doc_id, group in doc_groups.items():
            if len(diverse_results) < final_limit and group:
                diverse_results.append(group[0])
                used_documents.add(doc_id)
        
        # Phase 2: 残り枠を高スコア順で埋める（ただし同じ文書から3つまで）
        doc_counts = defaultdict(int)
        all_remaining = []
        
        for doc_id, group in doc_groups.items():
            for result in group[1:]:  # 最初の1つは既に追加済み
                all_remaining.append(result)
        
        # スコア順でソート
        all_remaining.sort(key=lambda x: x.final_score, reverse=True)
        
        for result in all_remaining:
            if len(diverse_results) >= final_limit:
                break
            
            doc_id = result.document_id
            if doc_counts[doc_id] < 2:  # 同じ文書から最大3つまで（最初の1つ＋追加2つ）
                diverse_results.append(result)
                doc_counts[doc_id] += 1
        
        logger.info(f"多様性確保完了: {len(diverse_results)}件, {len(used_documents)}文書から取得")
        return diverse_results
    
    def _final_ranking(self, 
                      results: List[ComprehensiveSearchResult], 
                      query: str) -> List[ComprehensiveSearchResult]:
        """最終ランキング"""
        # クエリとの意味的関連性を再評価
        for result in results:
            semantic_bonus = self._calculate_semantic_relevance(result.content, query)
            result.final_score += semantic_bonus
        
        # 最終スコア順でソート
        results.sort(key=lambda x: x.final_score, reverse=True)
        
        return results
    
    def _calculate_semantic_relevance(self, content: str, query: str) -> float:
        """意味的関連性の計算"""
        # 簡易版: キーワードの共起頻度に基づく計算
        # 将来的にはより高度なセマンティック分析に置き換え可能
        
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words or not content_words:
            return 0.0
        
        # ジャカード係数ベースの類似度
        intersection = len(query_words & content_words)
        union = len(query_words | content_words)
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        semantic_bonus = jaccard * 0.1  # 最大0.1のボーナス
        
        return semantic_bonus
    
    def _log_search_summary(self, 
                          results: List[ComprehensiveSearchResult], 
                          doc_analysis: Dict):
        """検索サマリーのログ出力"""
        if not results:
            return
        
        logger.info("📊 包括的検索サマリー:")
        logger.info(f"  総結果数: {len(results)}")
        
        # 文書別分布
        doc_distribution = defaultdict(int)
        for result in results:
            doc_distribution[result.document_name] += 1
        
        logger.info("  文書別分布:")
        for doc_name, count in sorted(doc_distribution.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"    {doc_name}: {count}件")
        
        # チャンク位置分布
        position_ranges = {"前半(0-33%)": 0, "中盤(33-66%)": 0, "後半(66-100%)": 0}
        for result in results:
            coverage = result.document_coverage
            if coverage <= 0.33:
                position_ranges["前半(0-33%)"] += 1
            elif coverage <= 0.66:
                position_ranges["中盤(33-66%)"] += 1
            else:
                position_ranges["後半(66-100%)"] += 1
        
        logger.info("  位置分布:")
        for range_name, count in position_ranges.items():
            logger.info(f"    {range_name}: {count}件")

# グローバルインスタンス
comprehensive_search_system = ComprehensiveSearchSystem()

async def initialize_comprehensive_search():
    """包括的検索システムの初期化"""
    return await comprehensive_search_system.initialize()

async def comprehensive_search(query: str, 
                             company_id: str = None,
                             initial_limit: int = 50,
                             final_limit: int = 15) -> List[Dict[str, Any]]:
    """包括的検索の実行（外部インターフェース）"""
    results = await comprehensive_search_system.comprehensive_search(
        query, company_id, initial_limit, final_limit
    )
    return [result.to_dict() for result in results] 