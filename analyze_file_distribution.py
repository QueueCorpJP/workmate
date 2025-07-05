import asyncio
import os
import sys
import logging
from typing import List, Dict, Any

# パス設定
sys.path.append(os.path.join(os.path.dirname(__file__), 'Chatbot-backend-main'))

from modules.gemini_question_analyzer import GeminiQuestionAnalyzer
import psycopg2
from psycopg2.extras import RealDictCursor

# ログレベルを設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_file_distribution():
    """ファイル参照の固定化問題を分析"""
    print("🔍 ファイル参照の固定化問題を分析します...")
    
    try:
        analyzer = GeminiQuestionAnalyzer()
        
        # 1. データベースのファイル別チャンク分布を確認
        print("\n📊 1. ファイル別チャンク分布の分析...")
        with psycopg2.connect(analyzer.db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        ds.name as document_name,
                        ds.type as document_type,
                        COUNT(c.id) as chunk_count,
                        AVG(LENGTH(c.content)) as avg_content_length,
                        MIN(c.chunk_index) as min_chunk_index,
                        MAX(c.chunk_index) as max_chunk_index
                    FROM document_sources ds
                    LEFT JOIN chunks c ON ds.id = c.doc_id
                    WHERE c.content IS NOT NULL
                    GROUP BY ds.id, ds.name, ds.type
                    ORDER BY chunk_count DESC;
                """)
                
                results = cur.fetchall()
                print(f"📈 総ファイル数: {len(results)}件")
                print("\n📋 ファイル別チャンク統計:")
                
                total_chunks = sum(r['chunk_count'] for r in results)
                
                for i, result in enumerate(results, 1):
                    percentage = (result['chunk_count'] / total_chunks) * 100
                    print(f"  {i:2d}. {result['document_name']}")
                    print(f"      📄 タイプ: {result['document_type']}")
                    print(f"      🧩 チャンク数: {result['chunk_count']:,}件 ({percentage:.1f}%)")
                    print(f"      📏 平均文字数: {result['avg_content_length']:.0f}文字")
                    print(f"      📑 チャンク範囲: {result['min_chunk_index']} - {result['max_chunk_index']}")
                    print()
                
                # 上位3ファイルのチャンク数割合
                top3_chunks = sum(r['chunk_count'] for r in results[:3])
                top3_percentage = (top3_chunks / total_chunks) * 100
                print(f"🎯 上位3ファイルのチャンク占有率: {top3_percentage:.1f}%")
        
        # 2. 実際の検索でファイル別の登場頻度を確認
        print("\n📊 2. 検索でのファイル登場頻度分析...")
        
        # 様々なキーワードで検索テスト
        test_queries = [
            "会社名", "連絡先", "電話番号", "住所", "料金", "価格", 
            "サービス", "契約", "申込", "レンタル", "期間", "故障",
            "WALLIOR", "PC", "パソコン", "業務", "マニュアル", "手順"
        ]
        
        file_appearance_count = {}
        total_searches = len(test_queries)
        
        for query in test_queries:
            print(f"  🔍 検索テスト: '{query}'")
            
            analysis = await analyzer.analyze_question(query)
            results = await analyzer.execute_sql_search(analysis, limit=10)
            
            # ファイル別の登場回数をカウント
            appeared_files = set()
            for result in results[:5]:  # 上位5件のみカウント
                file_name = result.document_name
                if file_name not in appeared_files:
                    appeared_files.add(file_name)
                    file_appearance_count[file_name] = file_appearance_count.get(file_name, 0) + 1
        
        print(f"\n📈 {total_searches}回の検索での登場頻度:")
        sorted_files = sorted(file_appearance_count.items(), key=lambda x: x[1], reverse=True)
        
        for file_name, count in sorted_files:
            percentage = (count / total_searches) * 100
            print(f"  📁 {file_name}")
            print(f"    🎯 登場回数: {count}/{total_searches}回 ({percentage:.1f}%)")
        
        # 3. チャンク内容の多様性を確認
        print("\n📊 3. チャンク内容の多様性分析...")
        with psycopg2.connect(analyzer.db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                # ファイル別のユニークキーワード数を推定
                cur.execute("""
                    SELECT 
                        ds.name as document_name,
                        ds.type as document_type,
                        COUNT(DISTINCT SUBSTRING(c.content, 1, 100)) as content_diversity,
                        COUNT(c.id) as total_chunks
                    FROM document_sources ds
                    LEFT JOIN chunks c ON ds.id = c.doc_id
                    WHERE c.content IS NOT NULL
                    GROUP BY ds.id, ds.name, ds.type
                    ORDER BY total_chunks DESC;
                """)
                
                diversity_results = cur.fetchall()
                print("📋 ファイル別内容多様性:")
                
                for result in diversity_results:
                    if result['total_chunks'] > 0:
                        diversity_ratio = result['content_diversity'] / result['total_chunks']
                        print(f"  📁 {result['document_name']}")
                        print(f"    🎨 多様性: {result['content_diversity']}/{result['total_chunks']} ({diversity_ratio:.2f})")
        
        # 4. 検索結果のスコア分布を確認
        print("\n📊 4. 検索スコア分布の分析...")
        
        # 代表的な検索でスコア分布を確認
        analysis = await analyzer.analyze_question("WALLIOR PCについて教えて")
        results = await analyzer.execute_sql_search(analysis, limit=20)
        
        print(f"📈 検索結果のスコア分布 (クエリ: 'WALLIOR PCについて教えて'):")
        file_scores = {}
        
        for i, result in enumerate(results, 1):
            file_name = result.document_name
            if file_name not in file_scores:
                file_scores[file_name] = []
            file_scores[file_name].append(result.score)
            
            print(f"  {i:2d}. {result.document_name} (スコア: {result.score:.3f})")
        
        print(f"\n📊 ファイル別スコア統計:")
        for file_name, scores in file_scores.items():
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            count = len(scores)
            print(f"  📁 {file_name}")
            print(f"    📊 平均スコア: {avg_score:.3f}, 最高スコア: {max_score:.3f}, 登場回数: {count}")
        
    except Exception as e:
        print(f"❌ 分析エラー: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ ファイル分布分析完了")

if __name__ == "__main__":
    asyncio.run(analyze_file_distribution()) 