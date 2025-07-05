"""
Enhanced PostgreSQL Search のテストスクリプト
日本語形態素解析機能と検索精度の改善をテストします
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.enhanced_postgresql_search import (
    EnhancedJapaneseTextProcessor, 
    enhanced_search_chunks,
    initialize_enhanced_postgresql_search
)

async def test_japanese_text_processor():
    """日本語テキスト処理のテスト"""
    print("=== 日本語テキスト処理テスト ===")
    
    processor = EnhancedJapaneseTextProcessor()
    
    test_texts = [
        "株式会社あいう",
        "株式会社　あいう",
        "カブシキガイシャテスト",
        "有限会社サンプル",
        "(株)テストカンパニー",
        "これは日本語のテキストです",
        "APIの使い方について",
        "プログラミング言語Python",
    ]
    
    for text in test_texts:
        tokens = processor.tokenize_japanese_text(text)
        normalized = processor.normalize_company_terms(text)
        print(f"原文: {text}")
        print(f"  正規化: {normalized}")
        print(f"  分割結果: {tokens[:5]}...")  # 最初の5つのみ表示
        print()

async def test_search_comparison():
    """検索精度の比較テスト"""
    print("=== 検索精度比較テスト ===")
    
    # 初期化
    await initialize_enhanced_postgresql_search()
    
    test_queries = [
        "株式会社あいう",        # スペースなし会社名
        "株式会社　あいう",      # スペースあり会社名
        "(株)テスト",           # 略称
        "カブシキガイシャ",       # カタカナ
        "パソコンの価格",        # 一般的な質問
        "システム開発費用",      # 専門用語
    ]
    
    for query in test_queries:
        print(f"クエリ: '{query}'")
        
        try:
            # Enhanced PostgreSQL Search
            enhanced_results = await enhanced_search_chunks(query, limit=5)
            print(f"  Enhanced PostgreSQL Search: {len(enhanced_results)}件")
            
            for i, result in enumerate(enhanced_results[:3]):  # 上位3件のみ表示
                print(f"    {i+1}. スコア: {result.get('score', 0):.3f}")
                print(f"       ファイル: {result.get('file_name', 'Unknown')}")
                print(f"       内容: {result.get('content', '')[:100]}...")
                print()
                
        except Exception as e:
            print(f"  エラー: {e}")
        
        print("-" * 50)

async def test_edge_cases():
    """エッジケースのテスト"""
    print("=== エッジケーステスト ===")
    
    edge_cases = [
        "",                     # 空文字
        "a",                    # 1文字
        "あ",                   # 日本語1文字
        "123",                  # 数字のみ
        "？？？",               # 記号のみ
        "これは非常に長いテストクエリでたくさんの単語が含まれているため形態素解析や検索処理がどのように動作するかを確認するためのものです",  # 長いクエリ
    ]
    
    for query in edge_cases:
        print(f"クエリ: '{query}'")
        
        try:
            results = await enhanced_search_chunks(query, limit=3)
            print(f"  結果: {len(results)}件")
        except Exception as e:
            print(f"  エラー: {e}")
        print()

async def main():
    """メイン関数"""
    print("Enhanced PostgreSQL Search テスト開始")
    print("=" * 60)
    
    try:
        # 1. 日本語テキスト処理のテスト
        await test_japanese_text_processor()
        
        # 2. 検索精度の比較テスト
        await test_search_comparison()
        
        # 3. エッジケースのテスト
        await test_edge_cases()
        
        print("=" * 60)
        print("✅ すべてのテストが完了しました")
        
    except Exception as e:
        print(f"❌ テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 