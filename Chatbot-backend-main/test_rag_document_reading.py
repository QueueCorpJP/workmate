"""
RAGドキュメント読み込みテスト

このテストスクリプトは、RAGシステムがドキュメントソースを
最後まで正確に読み込めているかを検証します。
"""

import asyncio
import time
from typing import List, Dict
import sys
import os

# パスの設定
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.chat import (
    simple_rag_search, 
    chunk_knowledge_base,
    expand_query,
    _preprocess_query,
    _evaluate_rag_quality
)
from modules.rag_enhanced import EnhancedRAGSystem
from modules.rag_optimized import HighSpeedRAG


class RAGDocumentTester:
    """RAGドキュメント読み込みテスター"""
    
    def __init__(self):
        self.test_results = []
        self.enhanced_rag = EnhancedRAGSystem()
        self.speed_rag = HighSpeedRAG()
        
    def create_test_document(self, size: int = 1000000) -> str:
        """
        テストドキュメントを作成
        ドキュメントの各位置にマーカーを配置
        """
        sections = []
        chars_per_section = 10000
        num_sections = size // chars_per_section
        
        # ヘッダー
        sections.append("=== テストドキュメント開始 ===")
        sections.append(f"総文字数: {size:,}文字")
        sections.append(f"セクション数: {num_sections}個")
        sections.append("")
        
        # 各セクションを作成
        for i in range(num_sections):
            section_start = i * chars_per_section
            section_end = min((i + 1) * chars_per_section, size)
            
            section_content = []
            section_content.append(f"\n\n{'='*50}")
            section_content.append(f"セクション {i+1}/{num_sections}")
            section_content.append(f"位置: {section_start:,} - {section_end:,}文字")
            section_content.append(f"マーカー: SECTION_{i+1}_START")
            section_content.append("")
            
            # セクションの内容
            if i == 0:
                section_content.append("最初のセクションです。")
                section_content.append("重要情報A: システムの初期設定について")
            elif i == num_sections // 2:
                section_content.append("中央のセクションです。")
                section_content.append("重要情報B: システムの中核機能について")
            elif i == num_sections - 1:
                section_content.append("最後のセクションです。")
                section_content.append("重要情報C: システムの終了処理について")
                section_content.append("最終マーカー: DOCUMENT_END_MARKER")
            
            # パディングテキスト
            section_text = '\n'.join(section_content)
            padding_needed = chars_per_section - len(section_text) - 50
            if padding_needed > 0:
                padding_text = "テストデータ。" * (padding_needed // 14)
                section_content.append(padding_text[:padding_needed])
            
            section_content.append(f"\nマーカー: SECTION_{i+1}_END")
            sections.append('\n'.join(section_content))
        
        # フッター
        sections.append("\n\n=== テストドキュメント終了 ===")
        sections.append("最終確認マーカー: FINAL_CHECK_COMPLETE")
        
        return '\n'.join(sections)
    
    def test_chunking(self, document: str, chunk_size: int = 500000) -> Dict:
        """チャンク化のテスト"""
        print(f"\n🔪 チャンク化テスト開始 (チャンクサイズ: {chunk_size:,}文字)")
        
        chunks = chunk_knowledge_base(document, chunk_size)
        
        results = {
            'total_chunks': len(chunks),
            'chunk_sizes': [len(chunk) for chunk in chunks],
            'markers_found': {},
            'last_chunk_content': chunks[-1][-500:] if chunks else "",
            'document_end_found': False
        }
        
        # 各チャンクのマーカーを確認
        for i, chunk in enumerate(chunks):
            print(f"\n📦 チャンク {i+1}/{len(chunks)}: {len(chunk):,}文字")
            
            # マーカーの検索
            if "SECTION_1_START" in chunk:
                results['markers_found']['first_section'] = i + 1
                print("  ✅ 最初のセクションマーカー発見")
            
            if "重要情報B" in chunk:
                results['markers_found']['middle_info'] = i + 1
                print("  ✅ 中央の重要情報発見")
            
            if "DOCUMENT_END_MARKER" in chunk:
                results['markers_found']['document_end'] = i + 1
                results['document_end_found'] = True
                print("  ✅ ドキュメント終了マーカー発見")
            
            if "FINAL_CHECK_COMPLETE" in chunk:
                results['markers_found']['final_check'] = i + 1
                print("  ✅ 最終確認マーカー発見")
        
        # 最後のチャンクの内容を詳細確認
        if chunks:
            last_chunk = chunks[-1]
            print(f"\n📄 最後のチャンクの詳細:")
            print(f"  - サイズ: {len(last_chunk):,}文字")
            print(f"  - 最後の100文字: ...{last_chunk[-100:]}")
            
            # 重要なマーカーの存在確認
            if "DOCUMENT_END_MARKER" not in last_chunk and len(chunks) > 1:
                # 他のチャンクも確認
                for i in range(len(chunks)-2, -1, -1):
                    if "DOCUMENT_END_MARKER" in chunks[i]:
                        print(f"  ⚠️ ドキュメント終了マーカーはチャンク{i+1}にあります")
                        break
        
        return results
    
    def test_rag_search(self, document: str, queries: List[str]) -> Dict:
        """RAG検索のテスト"""
        print(f"\n🔍 RAG検索テスト開始")
        
        results = {
            'queries': {},
            'document_coverage': {}
        }
        
        for query in queries:
            print(f"\n📝 クエリ: '{query}'")
            
            # simple_rag_search のテスト
            start_time = time.time()
            rag_result = simple_rag_search(document, query, max_results=30)
            elapsed = time.time() - start_time
            
            query_results = {
                'result_length': len(rag_result),
                'elapsed_time': elapsed,
                'markers_found': []
            }
            
            # 結果の分析
            if "重要情報A" in rag_result:
                query_results['markers_found'].append('重要情報A（最初）')
            if "重要情報B" in rag_result:
                query_results['markers_found'].append('重要情報B（中央）')
            if "重要情報C" in rag_result:
                query_results['markers_found'].append('重要情報C（最後）')
            if "DOCUMENT_END_MARKER" in rag_result:
                query_results['markers_found'].append('ドキュメント終了マーカー')
            
            print(f"  - 結果サイズ: {len(rag_result):,}文字")
            print(f"  - 処理時間: {elapsed:.2f}秒")
            print(f"  - 発見マーカー: {', '.join(query_results['markers_found']) if query_results['markers_found'] else 'なし'}")
            
            # RAG品質評価
            quality_score = _evaluate_rag_quality(rag_result, query, 1)
            query_results['quality_score'] = quality_score
            print(f"  - 品質スコア: {quality_score:.2f}")
            
            results['queries'][query] = query_results
        
        return results
    
    async def test_enhanced_rag(self, document: str, queries: List[str]) -> Dict:
        """強化RAGのテスト"""
        print(f"\n🚀 強化RAG検索テスト開始")
        
        results = {
            'queries': {},
            'chunk_analysis': {}
        }
        
        # チャンク化テスト
        chunks = await self.enhanced_rag.smart_chunking(document, chunk_size=1000, overlap=200)
        print(f"  - スマートチャンク数: {len(chunks)}")
        
        # 最後のチャンクの確認
        if chunks:
            last_chunk = chunks[-1]
            print(f"  - 最後のチャンク内容: {last_chunk['content'][-200:]}")
            
            # ドキュメント終端の確認
            if "DOCUMENT_END_MARKER" in last_chunk['content']:
                print("  ✅ 最後のチャンクにドキュメント終了マーカー発見")
            else:
                # 他のチャンクを確認
                for i, chunk in enumerate(chunks):
                    if "DOCUMENT_END_MARKER" in chunk['content']:
                        print(f"  ⚠️ ドキュメント終了マーカーはチャンク{i+1}/{len(chunks)}にあります")
                        break
        
        # 各クエリでテスト
        for query in queries:
            print(f"\n📝 強化RAGクエリ: '{query}'")
            
            start_time = time.time()
            result = await self.enhanced_rag.iterative_search(
                query=query,
                knowledge_text=document,
                max_iterations=3,
                min_results=5
            )
            elapsed = time.time() - start_time
            
            query_results = {
                'result_length': len(result) if result else 0,
                'elapsed_time': elapsed,
                'markers_found': []
            }
            
            if result:
                if "重要情報C" in result or "DOCUMENT_END_MARKER" in result:
                    query_results['markers_found'].append('最後のセクション情報')
                    print("  ✅ 最後のセクションの情報を発見")
            
            results['queries'][query] = query_results
        
        return results
    
    async def test_speed_rag(self, document: str, queries: List[str]) -> Dict:
        """高速RAGのテスト"""
        print(f"\n⚡ 高速RAG検索テスト開始")
        
        results = {
            'queries': {},
            'performance': {}
        }
        
        # チャンク化テスト
        chunks = await self.speed_rag.fast_chunking(document, chunk_size=2000, overlap=200)
        print(f"  - 高速チャンク数: {len(chunks)}")
        
        # パフォーマンステスト
        for query in queries:
            print(f"\n📝 高速RAGクエリ: '{query}'")
            
            start_time = time.time()
            result = await self.speed_rag.lightning_search(
                query=query,
                knowledge_text=document,
                max_results=30
            )
            elapsed = time.time() - start_time
            
            query_results = {
                'result_length': len(result) if result else 0,
                'elapsed_time': elapsed,
                'found_end': False
            }
            
            if result and ("重要情報C" in result or "DOCUMENT_END_MARKER" in result):
                query_results['found_end'] = True
                print("  ✅ 最後のセクション情報を高速検索で発見")
            
            results['queries'][query] = query_results
        
        return results
    
    def run_comprehensive_test(self):
        """包括的なテストを実行"""
        print("=" * 80)
        print("🧪 RAGドキュメント読み込み包括テスト")
        print("=" * 80)
        
        # テストサイズのリスト
        test_sizes = [100000, 500000, 1000000]  # 10万、50万、100万文字
        
        all_results = {}
        
        for size in test_sizes:
            print(f"\n\n{'='*60}")
            print(f"📊 テストサイズ: {size:,}文字")
            print(f"{'='*60}")
            
            # テストドキュメントの作成
            document = self.create_test_document(size)
            
            # テストクエリ
            queries = [
                "最初のセクション",
                "中央のセクション", 
                "最後のセクション",
                "重要情報",
                "システムの終了処理",
                "DOCUMENT_END_MARKER"
            ]
            
            results = {
                'document_size': size,
                'chunking': self.test_chunking(document),
                'simple_rag': self.test_rag_search(document, queries)
            }
            
            # 非同期テストの実行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                results['enhanced_rag'] = loop.run_until_complete(
                    self.test_enhanced_rag(document, queries)
                )
                results['speed_rag'] = loop.run_until_complete(
                    self.test_speed_rag(document, queries)
                )
            finally:
                loop.close()
            
            all_results[f'size_{size}'] = results
            
            # 結果サマリー
            self.print_summary(results)
        
        # 最終レポート
        self.print_final_report(all_results)
    
    def print_summary(self, results: Dict):
        """テスト結果のサマリーを表示"""
        print(f"\n\n📊 テスト結果サマリー")
        print("=" * 60)
        
        # チャンク化結果
        chunking = results['chunking']
        print(f"\n📦 チャンク化:")
        print(f"  - 総チャンク数: {chunking['total_chunks']}")
        print(f"  - ドキュメント終端検出: {'✅ 成功' if chunking['document_end_found'] else '❌ 失敗'}")
        
        # RAG検索結果
        simple_rag = results['simple_rag']
        print(f"\n🔍 Simple RAG:")
        for query, query_result in simple_rag['queries'].items():
            found_end = any('最後' in marker or 'END' in marker for marker in query_result['markers_found'])
            print(f"  - '{query}': {'✅' if found_end else '❌'} (品質: {query_result.get('quality_score', 0):.2f})")
    
    def print_final_report(self, all_results: Dict):
        """最終レポートを表示"""
        print("\n\n" + "=" * 80)
        print("📊 最終レポート: RAGドキュメント読み込みテスト")
        print("=" * 80)
        
        success_count = 0
        total_tests = 0
        
        for size_key, results in all_results.items():
            size = results['document_size']
            print(f"\n📄 ドキュメントサイズ: {size:,}文字")
            
            # チャンク化の成功判定
            if results['chunking']['document_end_found']:
                print("  ✅ チャンク化: ドキュメント終端まで正常に処理")
                success_count += 1
            else:
                print("  ❌ チャンク化: ドキュメント終端の検出に失敗")
            total_tests += 1
            
            # RAG検索の成功判定
            end_query_results = results['simple_rag']['queries'].get('システムの終了処理', {})
            if any('最後' in marker for marker in end_query_results.get('markers_found', [])):
                print("  ✅ RAG検索: 最後のセクションの情報を正常に取得")
                success_count += 1
            else:
                print("  ❌ RAG検索: 最後のセクションの情報取得に失敗")
            total_tests += 1
        
        # 総合評価
        success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
        print(f"\n\n🎯 総合結果:")
        print(f"  - 成功率: {success_rate:.1f}% ({success_count}/{total_tests})")
        
        if success_rate == 100:
            print("\n✅ 結論: RAGシステムはドキュメントを最後まで正常に読み込めています")
        elif success_rate >= 50:
            print("\n⚠️ 結論: RAGシステムは部分的にドキュメントを読み込めていますが、改善が必要です")
        else:
            print("\n❌ 結論: RAGシステムはドキュメントの最後まで読み込めていません")
        
        print("\n💡 推奨事項:")
        if success_rate < 100:
            print("  1. チャンクサイズの調整を検討してください")
            print("  2. RAG検索のmax_results値を増やしてください")
            print("  3. チャンク境界の処理ロジックを改善してください")
            print("  4. ドキュメント終端の特別な処理を追加してください")


if __name__ == "__main__":
    tester = RAGDocumentTester()
    tester.run_comprehensive_test() 