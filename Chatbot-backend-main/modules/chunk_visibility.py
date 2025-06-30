"""
🔍 チャンク可視化システム
質問時の参照チャンク情報を表示し、どのチャンクが選ばれ、なぜそれが選ばれたのかを確認できる機能
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ChunkReference:
    """参照チャンク情報"""
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    chunk_index: int
    similarity_score: float
    relevance_score: float
    confidence_score: float
    query_match_score: float
    semantic_score: float
    context_score: float
    search_method: str
    selection_reason: str
    metadata: Dict = None

@dataclass
class ChunkSelectionAnalysis:
    """チャンク選択分析"""
    total_chunks_found: int
    chunks_after_filtering: int
    selection_criteria: Dict[str, Any]
    dynamic_threshold: float
    query_analysis: Dict[str, Any]
    selection_summary: str

class ChunkVisibilitySystem:
    """チャンク可視化システム"""
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
    
    def analyze_chunk_selection(self, 
                              search_results: List,
                              query: str,
                              dynamic_threshold: float,
                              intent_analysis: Dict = None) -> ChunkSelectionAnalysis:
        """チャンク選択の分析"""
        try:
            # 基本統計
            total_chunks = len(search_results) if search_results else 0
            filtered_chunks = len([r for r in search_results if r.similarity_score >= dynamic_threshold]) if search_results else 0
            
            # 選択基準の分析
            selection_criteria = {
                "dynamic_threshold": dynamic_threshold,
                "min_confidence": 0.1,
                "max_results_per_document": 4,
                "context_diversity_enabled": True
            }
            
            # クエリ分析
            query_analysis = {
                "query_length": len(query),
                "is_japanese": bool(any(ord(c) > 127 for c in query)),
                "contains_company_name": any(term in query.lower() for term in ['ほっとらいふ', 'ホットライフ', 'hotlife']),
                "intent_analysis": intent_analysis or {}
            }
            
            # 選択サマリーの生成
            selection_summary = self._generate_selection_summary(
                total_chunks, filtered_chunks, dynamic_threshold, query_analysis
            )
            
            return ChunkSelectionAnalysis(
                total_chunks_found=total_chunks,
                chunks_after_filtering=filtered_chunks,
                selection_criteria=selection_criteria,
                dynamic_threshold=dynamic_threshold,
                query_analysis=query_analysis,
                selection_summary=selection_summary
            )
        
        except Exception as e:
            self.logger.error(f"チャンク選択分析エラー: {e}")
            return ChunkSelectionAnalysis(
                total_chunks_found=0,
                chunks_after_filtering=0,
                selection_criteria={},
                dynamic_threshold=0.0,
                query_analysis={},
                selection_summary="分析に失敗しました"
            )
    
    def _generate_selection_summary(self, 
                                   total_chunks: int,
                                   filtered_chunks: int,
                                   threshold: float,
                                   query_analysis: Dict) -> str:
        """選択サマリーの生成"""
        summary_parts = []
        
        # 基本情報
        summary_parts.append(f"検索結果: {total_chunks}個のチャンクが見つかりました")
        summary_parts.append(f"動的閾値: {threshold:.3f}により{filtered_chunks}個のチャンクが選択されました")
        
        # クエリ特性
        if query_analysis.get("is_japanese"):
            summary_parts.append("日本語クエリのため閾値が調整されました")
        
        if query_analysis.get("contains_company_name"):
            summary_parts.append("会社名が含まれるため特別な処理が適用されました")
        
        # 選択率
        if total_chunks > 0:
            selection_rate = (filtered_chunks / total_chunks) * 100
            summary_parts.append(f"選択率: {selection_rate:.1f}%")
        
        return "。".join(summary_parts) + "。"
    
    def create_chunk_references(self, search_results: List, query: str) -> List[ChunkReference]:
        """検索結果からチャンク参照情報を作成"""
        chunk_references = []
        
        try:
            for i, result in enumerate(search_results):
                # 選択理由の生成
                selection_reason = self._generate_selection_reason(result, query, i)
                
                chunk_ref = ChunkReference(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    document_name=result.document_name,
                    content=result.content,
                    chunk_index=result.chunk_index,
                    similarity_score=result.similarity_score,
                    relevance_score=result.relevance_score,
                    confidence_score=result.confidence_score,
                    query_match_score=getattr(result, 'query_match_score', 0.0),
                    semantic_score=getattr(result, 'semantic_score', 0.0),
                    context_score=getattr(result, 'context_score', 0.0),
                    search_method=result.search_method,
                    selection_reason=selection_reason,
                    metadata=getattr(result, 'metadata', {})
                )
                
                chunk_references.append(chunk_ref)
        
        except Exception as e:
            self.logger.error(f"チャンク参照情報作成エラー: {e}")
        
        return chunk_references
    
    def _generate_selection_reason(self, result, query: str, rank: int) -> str:
        """チャンク選択理由の生成"""
        reasons = []
        
        # ランキング
        reasons.append(f"検索順位: {rank + 1}位")
        
        # 類似度スコア
        if result.similarity_score >= 0.7:
            reasons.append(f"高い類似度 ({result.similarity_score:.3f})")
        elif result.similarity_score >= 0.4:
            reasons.append(f"中程度の類似度 ({result.similarity_score:.3f})")
        else:
            reasons.append(f"低い類似度 ({result.similarity_score:.3f})")
        
        # 信頼度スコア
        if result.confidence_score >= 0.5:
            reasons.append(f"高い信頼度 ({result.confidence_score:.3f})")
        elif result.confidence_score >= 0.3:
            reasons.append(f"中程度の信頼度 ({result.confidence_score:.3f})")
        
        # クエリマッチ
        query_match = getattr(result, 'query_match_score', 0.0)
        if query_match >= 0.3:
            reasons.append(f"クエリとの直接マッチ ({query_match:.3f})")
        
        # 文書タイプ
        if hasattr(result, 'document_type') and result.document_type:
            reasons.append(f"文書タイプ: {result.document_type}")
        
        return "、".join(reasons)
    
    def format_chunk_visibility_info(self, 
                                   chunk_references: List[ChunkReference],
                                   selection_analysis: ChunkSelectionAnalysis) -> Dict[str, Any]:
        """チャンク可視化情報のフォーマット"""
        return {
            "chunk_references": [
                {
                    "chunk_id": ref.chunk_id,
                    "document_name": ref.document_name,
                    "chunk_index": ref.chunk_index,
                    "content_preview": ref.content[:200] + "..." if len(ref.content) > 200 else ref.content,
                    "scores": {
                        "similarity": ref.similarity_score,
                        "relevance": ref.relevance_score,
                        "confidence": ref.confidence_score,
                        "query_match": ref.query_match_score,
                        "semantic": ref.semantic_score
                    },
                    "selection_reason": ref.selection_reason,
                    "search_method": ref.search_method
                }
                for ref in chunk_references
            ],
            "selection_analysis": {
                "total_chunks_found": selection_analysis.total_chunks_found,
                "chunks_selected": selection_analysis.chunks_after_filtering,
                "dynamic_threshold": selection_analysis.dynamic_threshold,
                "selection_criteria": selection_analysis.selection_criteria,
                "query_analysis": selection_analysis.query_analysis,
                "summary": selection_analysis.selection_summary
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "system_version": "chunk_visibility_v1.0"
            }
        }

# インスタンス取得関数
def get_chunk_visibility_system() -> ChunkVisibilitySystem:
    """チャンク可視化システムのインスタンスを取得"""
    return ChunkVisibilitySystem()

def chunk_visibility_available() -> bool:
    """チャンク可視化システムが利用可能かチェック"""
    try:
        system = ChunkVisibilitySystem()
        return True
    except Exception as e:
        logger.error(f"チャンク可視化システムの初期化に失敗: {e}")
        return False