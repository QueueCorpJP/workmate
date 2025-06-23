"""
RAGシステム設定ファイル
各種パラメータと動作モードを管理
"""
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class RAGConfig:
    """RAGシステムの設定クラス"""
    
    # チャンク化設定
    default_chunk_size: int = 1000
    default_overlap: int = 200
    max_chunk_size: int = 2000
    min_chunk_size: int = 500
    
    # 検索設定
    default_top_k: int = 20
    max_top_k: int = 50
    min_score_threshold: float = 0.1
    
    # 反復検索設定
    max_iterations: int = 3
    min_results_threshold: int = 5
    early_stop_threshold: float = 0.7
    
    # パフォーマンス設定
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    max_concurrent_searches: int = 5
    
    # 品質制御設定
    enable_quality_filter: bool = True
    min_content_length: int = 100
    max_content_length: int = 5000
    
    # 検索戦略設定
    bm25_weight: float = 0.6
    semantic_weight: float = 0.4
    title_match_bonus: float = 0.2
    section_level_bonus: float = 0.1
    
    # デバッグとロギング
    enable_debug_logging: bool = False
    log_search_performance: bool = True
    
    @classmethod
    def from_env(cls) -> 'RAGConfig':
        """環境変数から設定を読み込み"""
        return cls(
            default_chunk_size=int(os.getenv('RAG_CHUNK_SIZE', 1000)),
            default_overlap=int(os.getenv('RAG_OVERLAP', 200)),
            default_top_k=int(os.getenv('RAG_TOP_K', 20)),
            max_iterations=int(os.getenv('RAG_MAX_ITERATIONS', 3)),
            enable_caching=os.getenv('RAG_ENABLE_CACHING', 'true').lower() == 'true',
            enable_debug_logging=os.getenv('RAG_DEBUG', 'false').lower() == 'true',
            bm25_weight=float(os.getenv('RAG_BM25_WEIGHT', 0.6)),
            semantic_weight=float(os.getenv('RAG_SEMANTIC_WEIGHT', 0.4)),
        )
    
    def get_search_strategy(self, text_length: int) -> Dict:
        """テキスト長に応じた検索戦略を返す"""
        if text_length <= 50000:
            return {
                'method': 'simple',
                'chunk_size': self.min_chunk_size,
                'top_k': self.default_top_k // 2,
                'iterations': 1
            }
        elif text_length <= 200000:
            return {
                'method': 'adaptive',
                'chunk_size': self.default_chunk_size,
                'top_k': self.default_top_k,
                'iterations': 2
            }
        elif text_length <= 500000:
            return {
                'method': 'multi_pass',
                'chunk_size': self.default_chunk_size,
                'top_k': self.default_top_k,
                'iterations': self.max_iterations
            }
        else:
            return {
                'method': 'enhanced',
                'chunk_size': self.max_chunk_size,
                'top_k': self.max_top_k,
                'iterations': self.max_iterations
            }

# グローバル設定インスタンス
rag_config = RAGConfig.from_env()

# 各種設定値を取得する便利関数
def get_chunk_size(text_length: int = None) -> int:
    """適切なチャンクサイズを取得"""
    if text_length is None:
        return rag_config.default_chunk_size
    
    if text_length > 1000000:
        return rag_config.max_chunk_size
    elif text_length < 100000:
        return rag_config.min_chunk_size
    else:
        return rag_config.default_chunk_size

def get_search_params(query_complexity: str = 'normal') -> Dict:
    """クエリの複雑さに応じた検索パラメータを取得"""
    base_params = {
        'top_k': rag_config.default_top_k,
        'score_threshold': rag_config.min_score_threshold,
        'max_iterations': rag_config.max_iterations
    }
    
    if query_complexity == 'simple':
        base_params['top_k'] //= 2
        base_params['max_iterations'] = 1
    elif query_complexity == 'complex':
        base_params['top_k'] = min(base_params['top_k'] * 2, rag_config.max_top_k)
        base_params['score_threshold'] *= 0.8
    
    return base_params

def should_use_enhanced_rag(text_length: int, query_length: int) -> bool:
    """強化RAGを使用すべきかどうかを判定"""
    # 大きなテキストまたは複雑なクエリの場合は強化RAGを使用
    return (text_length > 500000 or 
            query_length > 100 or 
            rag_config.enable_debug_logging)

# パフォーマンス最適化のための設定
PERFORMANCE_SETTINGS = {
    'small_text_threshold': 10000,      # 小さなテキストの閾値
    'medium_text_threshold': 100000,    # 中程度のテキストの閾値
    'large_text_threshold': 500000,     # 大きなテキストの閾値
    'max_concurrent_chunks': 10,        # 同時処理可能なチャンク数
    'memory_limit_mb': 1024,           # メモリ使用量制限（MB）
    'timeout_seconds': 30,             # 検索タイムアウト（秒）
}

# デバッグ用の設定
DEBUG_SETTINGS = {
    'log_chunk_details': rag_config.enable_debug_logging,
    'log_search_scores': rag_config.enable_debug_logging,
    'save_search_history': rag_config.enable_debug_logging,
    'performance_profiling': rag_config.log_search_performance,
} 