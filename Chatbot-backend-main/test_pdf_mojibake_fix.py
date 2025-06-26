#!/usr/bin/env python3
"""
PDF文字化け修復機能のテストスクリプト
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

from modules.knowledge.pdf_enhanced import (
    fix_mojibake_text,
    check_text_corruption,
    process_pdf_file_enhanced
)

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mojibake_fix():
    """文字化け修復機能のテスト"""
    print("=== 文字化け修復機能テスト ===")
    
    # テスト用の文字化けテキスト
    test_cases = [
        {
            "name": "基本的な文字化け",
            "input": "縺薙ｌ縺ｯ繝?繧ｹ繝医〒縺吶?",
            "expected_contains": ["テスト"]
        },
        {
            "name": "システム関連の文字化け",
            "input": "繧ｳ繝ｳ繝斐Η繝ｼ繧ｿ繧ｷ繧ｹ繝ｃ繝?縺ｮ險ｭ螳?",
            "expected_contains": ["コンピュータ", "システム", "設定"]
        },
        {
            "name": "ユーザー関連の文字化け",
            "input": "繝ｦ繝ｼ繧ｶ繝ｼ縺ｮ繝ｭ繧ｰ繧､繝ｳ縺ｨ繝代せ繝ｯ繝ｼ繝?",
            "expected_contains": ["ユーザー", "ログイン", "パスワード"]
        },
        {
            "name": "CIDエラーパターン",
            "input": "これは(cid:123)テスト(cid:456)です",
            "expected_contains": ["これは", "テスト", "です"]
        },
        {
            "name": "置換文字パターン",
            "input": "これは\ufffdテスト\ufffdです",
            "expected_contains": ["これは", "テスト", "です", "[文字化け]"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- テスト {i}: {test_case['name']} ---")
        print(f"入力: {test_case['input']}")
        
        # 文字化け検出テスト
        is_corrupted = check_text_corruption(test_case['input'])
        print(f"文字化け検出: {'✅ 検出' if is_corrupted else '❌ 未検出'}")
        
        # 文字化け修復テスト
        fixed_text = fix_mojibake_text(test_case['input'])
        print(f"修復後: {fixed_text}")
        
        # 期待される文字列が含まれているかチェック
        success = True
        for expected in test_case['expected_contains']:
            if expected not in fixed_text:
                print(f"❌ 期待される文字列 '{expected}' が見つかりません")
                success = False
        
        if success:
            print("✅ テスト成功")
        else:
            print("❌ テスト失敗")
    
    print("\n=== 文字化け修復機能テスト完了 ===")

async def test_pdf_processing():
    """PDF処理機能のテスト（サンプルファイルがある場合）"""
    print("\n=== PDF処理機能テスト ===")
    
    # テスト用PDFファイルのパスを探す
    test_pdf_paths = [
        "test_files/sample.pdf",
        "sample.pdf",
        "../sample.pdf"
    ]
    
    test_pdf_path = None
    for path in test_pdf_paths:
        if os.path.exists(path):
            test_pdf_path = path
            break
    
    if not test_pdf_path:
        print("⚠️ テスト用PDFファイルが見つかりません")
        print("テスト用PDFファイルを以下のいずれかの場所に配置してください:")
        for path in test_pdf_paths:
            print(f"  - {path}")
        return
    
    print(f"テスト用PDFファイル: {test_pdf_path}")
    
    try:
        # PDFファイルを読み込み
        with open(test_pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        print(f"PDFファイルサイズ: {len(pdf_content)} bytes")
        
        # PDF処理を実行
        result_df, sections, extracted_text = await process_pdf_file_enhanced(
            pdf_content, 
            os.path.basename(test_pdf_path)
        )
        
        print(f"✅ PDF処理成功")
        print(f"セクション数: {len(result_df)}")
        print(f"抽出テキスト長: {len(extracted_text)} 文字")
        
        # 結果の一部を表示
        if extracted_text:
            print(f"\n--- 抽出テキスト（最初の500文字） ---")
            print(extracted_text[:500])
            print("...")
        
        # セクション情報を表示
        print(f"\n--- セクション情報 ---")
        for index, row in result_df.iterrows():
            print(f"セクション {index + 1}: {row['section']} ({len(row['content'])} 文字)")
        
    except Exception as e:
        print(f"❌ PDF処理エラー: {e}")
        logger.error(f"PDF処理エラー詳細: {e}", exc_info=True)
    
    print("=== PDF処理機能テスト完了 ===")

def main():
    """メイン関数"""
    print("🔧 PDF文字化け修復機能テストスクリプト")
    print("=" * 50)
    
    # 文字化け修復機能のテスト
    test_mojibake_fix()
    
    # PDF処理機能のテスト（非同期）
    asyncio.run(test_pdf_processing())
    
    print("\n🎉 すべてのテストが完了しました")
    print("\n📝 使用方法:")
    print("1. 文字化けしたPDFファイルをアップロードしてください")
    print("2. システムが自動的に文字化けを検出し、修復を試行します")
    print("3. Gemini文字抽出 → PyPDF2+修復 → OCR+修復の順で処理されます")

if __name__ == "__main__":
    main()