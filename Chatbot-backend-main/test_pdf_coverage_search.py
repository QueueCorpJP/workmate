"""
PDF全体カバレッジ検索テスト
PDFの後半にある重要情報も確実に取得できているかをテストするスクリプト

テスト項目:
1. 文書の位置分布（前半・中盤・後半）
2. 同一文書からの複数チャンク取得
3. 検索システム別の性能比較
4. 動的LIMIT調整の効果測定
"""

import asyncio
import sys
import os
from typing import List, Dict, Any
import logging

# モジュールパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.comprehensive_search_system import comprehensive_search
from modules.chat_rag_enhanced import enhanced_rag_search
from modules.chat_rag import adaptive_rag_search
from modules.enhanced_postgresql_search import enhanced_search_chunks

# ログ設定
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFCoverageTestSuite:
    """PDF全体カバレッジテストスイート"""
    
    def __init__(self):
        self.test_queries = [
            # 一般的な業務質問
            "会議の進行方法について教えてください",
            "プロジェクトの最終段階で注意すべき点は何ですか",
            "品質管理の具体的な手順を説明してください",
            
            # 詳細な技術質問
            "システムの実装において後半フェーズで発生しやすい問題とその対策方法を詳しく教えてください",
            "文書の最後の章や結論部分に記載されている重要なポイントはありますか",
            
            # 分析・比較質問
            "導入前と導入後の比較結果について詳しく知りたいです",
            "最終的な評価や成果についてまとめて教えてください"
        ]
    
    async def run_comprehensive_test(self, company_id: str = None):
        """包括的テストの実行"""
        logger.info("🧪 PDF全体カバレッジテスト開始")
        
        results = {
            'enhanced_rag': [],
            'comprehensive_search': [],
            'adaptive_rag': [],
            'enhanced_postgresql': []
        }
        
        for i, query in enumerate(self.test_queries, 1):
            logger.info(f"\n📝 テストクエリ {i}/{len(self.test_queries)}: '{query}'")
            
            # 各検索システムでテスト実行
            enhanced_result = await self._test_enhanced_rag(query, company_id)
            comprehensive_result = await self._test_comprehensive_search(query, company_id)
            adaptive_result = await self._test_adaptive_rag(query, company_id)
            postgresql_result = await self._test_enhanced_postgresql(query, company_id)
            
            results['enhanced_rag'].append({
                'query': query,
                'result': enhanced_result
            })
            results['comprehensive_search'].append({
                'query': query,
                'result': comprehensive_result
            })
            results['adaptive_rag'].append({
                'query': query,
                'result': adaptive_result
            })
            results['enhanced_postgresql'].append({
                'query': query,
                'result': postgresql_result
            })
        
        # 結果分析とレポート生成
        await self._generate_coverage_report(results)
        
        logger.info("✅ PDF全体カバレッジテスト完了")
    
    async def _test_enhanced_rag(self, query: str, company_id: str = None) -> Dict[str, Any]:
        """拡張RAGシステムのテスト"""
        try:
            logger.info("  🔍 拡張RAGシステムテスト中...")
            results = await enhanced_rag_search(
                query=query,
                context="",
                company_id=company_id,
                adaptive_limits=True
            )
            
            analysis = self._analyze_search_results(results, "enhanced_rag")
            logger.info(f"    結果: {len(results)}件, 文書数: {analysis['document_count']}, "
                       f"後半比率: {analysis['rear_percentage']:.1f}%")
            
            return {
                'results': results,
                'analysis': analysis,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"    拡張RAGテストエラー: {e}")
            return {
                'results': [],
                'analysis': {},
                'status': 'error',
                'error': str(e)
            }
    
    async def _test_comprehensive_search(self, query: str, company_id: str = None) -> Dict[str, Any]:
        """包括的検索システムのテスト"""
        try:
            logger.info("  🔍 包括的検索システムテスト中...")
            results = await comprehensive_search(
                query=query,
                company_id=company_id,
                initial_limit=50,
                final_limit=15
            )
            
            analysis = self._analyze_search_results(results, "comprehensive_search")
            logger.info(f"    結果: {len(results)}件, 文書数: {analysis['document_count']}, "
                       f"後半比率: {analysis['rear_percentage']:.1f}%")
            
            return {
                'results': results,
                'analysis': analysis,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"    包括的検索テストエラー: {e}")
            return {
                'results': [],
                'analysis': {},
                'status': 'error',
                'error': str(e)
            }
    
    async def _test_adaptive_rag(self, query: str, company_id: str = None) -> Dict[str, Any]:
        """従来の適応的RAGのテスト"""
        try:
            logger.info("  🔍 従来適応的RAGテスト中...")
            results = await adaptive_rag_search(query, limit=10)
            
            analysis = self._analyze_search_results(results, "adaptive_rag")
            logger.info(f"    結果: {len(results)}件, 文書数: {analysis['document_count']}, "
                       f"後半比率: {analysis['rear_percentage']:.1f}%")
            
            return {
                'results': results,
                'analysis': analysis,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"    適応的RAGテストエラー: {e}")
            return {
                'results': [],
                'analysis': {},
                'status': 'error',
                'error': str(e)
            }
    
    async def _test_enhanced_postgresql(self, query: str, company_id: str = None) -> Dict[str, Any]:
        """Enhanced PostgreSQL検索のテスト"""
        try:
            logger.info("  🔍 Enhanced PostgreSQLテスト中...")
            results = await enhanced_search_chunks(
                query=query,
                company_id=company_id,
                limit=10,
                threshold=0.2
            )
            
            analysis = self._analyze_search_results(results, "enhanced_postgresql")
            logger.info(f"    結果: {len(results)}件, 文書数: {analysis['document_count']}, "
                       f"後半比率: {analysis['rear_percentage']:.1f}%")
            
            return {
                'results': results,
                'analysis': analysis,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"    Enhanced PostgreSQLテストエラー: {e}")
            return {
                'results': [],
                'analysis': {},
                'status': 'error',
                'error': str(e)
            }
    
    def _analyze_search_results(self, results: List[Dict[str, Any]], system_name: str) -> Dict[str, Any]:
        """検索結果の分析"""
        if not results:
            return {
                'total_results': 0,
                'document_count': 0,
                'position_distribution': {'前半': 0, '中盤': 0, '後半': 0},
                'rear_percentage': 0.0,
                'avg_score': 0.0,
                'document_diversity_score': 0.0
            }
        
        # 基本統計
        total_results = len(results)
        unique_documents = set()
        position_distribution = {'前半': 0, '中盤': 0, '後半': 0}
        total_score = 0
        
        for result in results:
            # 文書名の取得
            doc_name = result.get('document_name', result.get('file_name', 'Unknown'))
            unique_documents.add(doc_name)
            
            # スコアの累計
            score = result.get('score', 0)
            total_score += score
            
            # 位置分布の計算
            coverage = result.get('document_coverage', 0)
            if coverage is None:
                # document_coverageがない場合はchunk_indexから推定
                chunk_index = result.get('chunk_index', 0)
                if chunk_index < 5:
                    position_distribution['前半'] += 1
                elif chunk_index < 15:
                    position_distribution['中盤'] += 1
                else:
                    position_distribution['後半'] += 1
            else:
                if coverage <= 0.33:
                    position_distribution['前半'] += 1
                elif coverage <= 0.66:
                    position_distribution['中盤'] += 1
                else:
                    position_distribution['後半'] += 1
        
        # 後半比率の計算
        rear_percentage = (position_distribution['後半'] / total_results) * 100 if total_results > 0 else 0
        
        # 平均スコア
        avg_score = total_score / total_results if total_results > 0 else 0
        
        # 文書多様性スコア（文書数/結果数）
        document_diversity_score = len(unique_documents) / total_results if total_results > 0 else 0
        
        return {
            'total_results': total_results,
            'document_count': len(unique_documents),
            'position_distribution': position_distribution,
            'rear_percentage': rear_percentage,
            'avg_score': avg_score,
            'document_diversity_score': document_diversity_score,
            'unique_documents': list(unique_documents)
        }
    
    async def _generate_coverage_report(self, results: Dict[str, List[Dict]]):
        """カバレッジレポートの生成"""
        logger.info("\n📊 PDF全体カバレッジテスト レポート")
        logger.info("=" * 60)
        
        systems = ['enhanced_rag', 'comprehensive_search', 'adaptive_rag', 'enhanced_postgresql']
        system_names = {
            'enhanced_rag': '拡張RAGシステム',
            'comprehensive_search': '包括的検索システム',
            'adaptive_rag': '従来適応的RAG',
            'enhanced_postgresql': 'Enhanced PostgreSQL'
        }
        
        # システム別集計
        system_stats = {}
        
        for system in systems:
            system_results = results[system]
            
            total_results = 0
            total_documents = 0
            total_rear_percentage = 0
            total_avg_score = 0
            total_diversity_score = 0
            success_count = 0
            
            for query_result in system_results:
                if query_result['result']['status'] == 'success':
                    analysis = query_result['result']['analysis']
                    total_results += analysis.get('total_results', 0)
                    total_documents += analysis.get('document_count', 0)
                    total_rear_percentage += analysis.get('rear_percentage', 0)
                    total_avg_score += analysis.get('avg_score', 0)
                    total_diversity_score += analysis.get('document_diversity_score', 0)
                    success_count += 1
            
            if success_count > 0:
                system_stats[system] = {
                    'avg_results_per_query': total_results / success_count,
                    'avg_documents_per_query': total_documents / success_count,
                    'avg_rear_percentage': total_rear_percentage / success_count,
                    'avg_score': total_avg_score / success_count,
                    'avg_diversity_score': total_diversity_score / success_count,
                    'success_rate': (success_count / len(system_results)) * 100
                }
            else:
                system_stats[system] = {
                    'avg_results_per_query': 0,
                    'avg_documents_per_query': 0,
                    'avg_rear_percentage': 0,
                    'avg_score': 0,
                    'avg_diversity_score': 0,
                    'success_rate': 0
                }
        
        # レポート出力
        for system, stats in system_stats.items():
            logger.info(f"\n📈 {system_names[system]}:")
            logger.info(f"  平均結果数/クエリ: {stats['avg_results_per_query']:.1f}件")
            logger.info(f"  平均文書数/クエリ: {stats['avg_documents_per_query']:.1f}文書")
            logger.info(f"  平均後半比率: {stats['avg_rear_percentage']:.1f}%")
            logger.info(f"  平均関連スコア: {stats['avg_score']:.3f}")
            logger.info(f"  平均文書多様性: {stats['avg_diversity_score']:.3f}")
            logger.info(f"  成功率: {stats['success_rate']:.1f}%")
        
        # 比較分析
        logger.info(f"\n🏆 性能比較:")
        
        # 後半比率の比較
        rear_ratios = {system: stats['avg_rear_percentage'] for system, stats in system_stats.items()}
        best_rear = max(rear_ratios.items(), key=lambda x: x[1])
        logger.info(f"  📍 後半チャンク取得率が最高: {system_names[best_rear[0]]} ({best_rear[1]:.1f}%)")
        
        # 文書多様性の比較
        diversity_scores = {system: stats['avg_diversity_score'] for system, stats in system_stats.items()}
        best_diversity = max(diversity_scores.items(), key=lambda x: x[1])
        logger.info(f"  📚 文書多様性が最高: {system_names[best_diversity[0]]} ({best_diversity[1]:.3f})")
        
        # 結果数の比較
        result_counts = {system: stats['avg_results_per_query'] for system, stats in system_stats.items()}
        best_results = max(result_counts.items(), key=lambda x: x[1])
        logger.info(f"  📊 平均結果数が最多: {system_names[best_results[0]]} ({best_results[1]:.1f}件)")
        
        logger.info("\n✅ PDF全体カバレッジテスト完了")

async def main():
    """メイン実行関数"""
    logger.info("PDF全体カバレッジテスト開始")
    
    test_suite = PDFCoverageTestSuite()
    await test_suite.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main()) 