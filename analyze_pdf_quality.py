import asyncio
import os
import sys
import logging
import re
from typing import List, Dict, Any

# パス設定
sys.path.append(os.path.join(os.path.dirname(__file__), 'Chatbot-backend-main'))

from modules.gemini_question_analyzer import GeminiQuestionAnalyzer
import psycopg2
from psycopg2.extras import RealDictCursor

# ログレベルを設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_pdf_quality():
    """WALLIOR PC業務マニュアル.pdfの品質問題を分析"""
    print("🔍 WALLIOR PC業務マニュアル.pdfの品質問題を分析します...")
    
    try:
        analyzer = GeminiQuestionAnalyzer()
        
        # 1. WALLIOR PC業務マニュアル.pdfのチャンク内容を詳細確認
        print("\n📄 1. WALLIOR PC業務マニュアル.pdfのチャンク内容分析...")
        with psycopg2.connect(analyzer.db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                # 業務マニュアルのドキュメントIDを取得
                cur.execute("""
                    SELECT id, name, type, uploaded_at
                    FROM document_sources
                    WHERE name LIKE '%業務マニュアル%'
                    ORDER BY uploaded_at DESC;
                """)
                
                manual_docs = cur.fetchall()
                if not manual_docs:
                    print("❌ 業務マニュアルが見つかりませんでした")
                    return
                
                print(f"📚 見つかった業務マニュアル: {len(manual_docs)}件")
                for doc in manual_docs:
                    print(f"  📁 {doc['name']} (ID: {doc['id'][:8]}...)")
                
                # 最新の業務マニュアルを分析対象とする
                target_doc = manual_docs[0]
                doc_id = target_doc['id']
                doc_name = target_doc['name']
                
                print(f"\n🎯 分析対象: {doc_name}")
                
                # チャンク数と基本統計を確認
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_chunks,
                        AVG(LENGTH(content)) as avg_length,
                        MIN(LENGTH(content)) as min_length,
                        MAX(LENGTH(content)) as max_length,
                        MIN(chunk_index) as min_index,
                        MAX(chunk_index) as max_index
                    FROM chunks
                    WHERE doc_id = %s AND content IS NOT NULL;
                """, (doc_id,))
                
                stats = cur.fetchone()
                print(f"📊 チャンク統計:")
                print(f"  🧩 総チャンク数: {stats['total_chunks']}件")
                print(f"  📏 平均文字数: {stats['avg_length']:.1f}文字")
                print(f"  📐 文字数範囲: {stats['min_length']} - {stats['max_length']}文字")
                print(f"  📑 インデックス範囲: {stats['min_index']} - {stats['max_index']}")
                
                # サンプルチャンクの内容を確認
                print(f"\n📝 チャンクサンプル分析:")
                cur.execute("""
                    SELECT 
                        id,
                        chunk_index,
                        content,
                        LENGTH(content) as content_length
                    FROM chunks
                    WHERE doc_id = %s AND content IS NOT NULL
                    ORDER BY chunk_index
                    LIMIT 10;
                """, (doc_id,))
                
                sample_chunks = cur.fetchall()
                
                for i, chunk in enumerate(sample_chunks, 1):
                    print(f"\n  📄 チャンク#{chunk['chunk_index']} ({chunk['content_length']}文字)")
                    content = chunk['content']
                    
                    # 文字化けや異常なパターンをチェック
                    issues = []
                    
                    # 文字化けパターンをチェック
                    if re.search(r'[?]{3,}', content):
                        issues.append("連続した?マーク（文字化けの可能性）")
                    
                    # 異常に短いコンテンツ
                    if len(content.strip()) < 20:
                        issues.append("内容が短すぎる")
                    
                    # 意味のある日本語が含まれているかチェック
                    japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', content))
                    if japanese_chars / len(content) < 0.1:
                        issues.append("日本語の割合が低い")
                    
                    # 特殊文字が多すぎる
                    special_chars = len(re.findall(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', content))
                    if special_chars / len(content) > 0.3:
                        issues.append("特殊文字が多すぎる")
                    
                    # ページ境界マーカーの確認
                    if "===" in content and "ページ" in content:
                        issues.append("ページ境界マーカーが含まれている")
                    
                    if issues:
                        print(f"    ⚠️ 問題: {', '.join(issues)}")
                    else:
                        print(f"    ✅ 正常")
                    
                    # 内容のプレビュー（最初の200文字）
                    preview = content.replace('\n', ' ').replace('\r', ' ')[:200]
                    print(f"    📖 内容: {preview}...")
        
        # 2. 検索での問題を具体的に確認
        print(f"\n🔍 2. 業務マニュアル関連の検索テスト...")
        
        # 業務マニュアルに含まれるであろうキーワードでテスト
        manual_keywords = [
            "WALLIOR PC",
            "業務マニュアル", 
            "レンタル",
            "契約",
            "申込",
            "故障",
            "撤去",
            "再レンタル",
            "解約"
        ]
        
        for keyword in manual_keywords:
            print(f"\n  🔍 キーワード: '{keyword}'")
            
            # 直接SQL検索でPDFからの結果を確認
            with psycopg2.connect(analyzer.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            c.id,
                            c.chunk_index,
                            c.content,
                            ds.name as document_name
                        FROM chunks c
                        LEFT JOIN document_sources ds ON ds.id = c.doc_id
                        WHERE c.content ILIKE %s
                          AND ds.name LIKE '%業務マニュアル%'
                        ORDER BY c.chunk_index
                        LIMIT 3;
                    """, (f"%{keyword}%",))
                    
                    results = cur.fetchall()
                    print(f"    📊 業務マニュアルからの検索結果: {len(results)}件")
                    
                    for result in results:
                        content = result['content']
                        # キーワードの前後50文字を抽出
                        keyword_pos = content.lower().find(keyword.lower())
                        if keyword_pos >= 0:
                            start = max(0, keyword_pos - 50)
                            end = min(len(content), keyword_pos + len(keyword) + 50)
                            context = content[start:end].replace('\n', ' ')
                            print(f"      📄 チャンク#{result['chunk_index']}: ...{context}...")
                        else:
                            print(f"      📄 チャンク#{result['chunk_index']}: {content[:100]}...")
            
            # Gemini検索システムでの結果も確認
            analysis = await analyzer.analyze_question(f"{keyword}について教えて")
            gemini_results = await analyzer.execute_sql_search(analysis, limit=10)
            
            manual_results = [r for r in gemini_results if '業務マニュアル' in r.document_name]
            print(f"    🤖 Gemini検索での業務マニュアル結果: {len(manual_results)}件")
            
            if manual_results:
                for result in manual_results[:2]:
                    print(f"      🎯 スコア: {result.score:.3f}")
                    print(f"      📝 内容: {result.content[:100]}...")
        
        # 3. 他のPDFファイルとの比較
        print(f"\n📊 3. 他のPDFファイルとの品質比較...")
        with psycopg2.connect(analyzer.db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        ds.name as document_name,
                        COUNT(c.id) as chunk_count,
                        AVG(LENGTH(c.content)) as avg_length,
                        AVG(CASE 
                            WHEN c.content ~ '[ひらがなカタカナ漢字]' THEN 1 
                            ELSE 0 
                        END) as japanese_ratio
                    FROM document_sources ds
                    LEFT JOIN chunks c ON ds.id = c.doc_id
                    WHERE ds.type = 'pdf' AND c.content IS NOT NULL
                    GROUP BY ds.id, ds.name
                    ORDER BY chunk_count DESC;
                """)
                
                pdf_comparison = cur.fetchall()
                print("📋 PDFファイル品質比較:")
                
                for pdf in pdf_comparison:
                    print(f"  📁 {pdf['document_name']}")
                    print(f"    🧩 チャンク数: {pdf['chunk_count']}件")
                    print(f"    📏 平均文字数: {pdf['avg_length']:.1f}文字")
                    print(f"    🇯🇵 日本語含有率: {pdf['japanese_ratio']:.1%}")
                    
                    # 業務マニュアルかどうかを判定
                    if '業務マニュアル' in pdf['document_name']:
                        if pdf['avg_length'] < 100:
                            print(f"    ⚠️ 平均文字数が少なすぎる可能性")
                        if pdf['japanese_ratio'] < 0.5:
                            print(f"    ⚠️ 日本語含有率が低すぎる可能性")
                    print()
        
    except Exception as e:
        print(f"❌ 分析エラー: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ PDF品質分析完了")

if __name__ == "__main__":
    asyncio.run(analyze_pdf_quality()) 