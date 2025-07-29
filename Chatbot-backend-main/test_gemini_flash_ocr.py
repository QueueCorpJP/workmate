#!/usr/bin/env python3
"""
🧪 Gemini 2.5 Flash OCR テストスクリプト
🎯 PyMuPDF + Gemini 2.5 Flash Vision APIによるOCR処理をテスト

使用方法:
python test_gemini_flash_ocr.py [pdf_file_path]

例:
python test_gemini_flash_ocr.py sample.pdf
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_gemini_flash_ocr(pdf_path: str):
    """Gemini 2.5 Flash OCRのテスト実行"""
    
    try:
        # 1. ファイル存在確認
        if not os.path.exists(pdf_path):
            logger.error(f"❌ ファイルが見つかりません: {pdf_path}")
            return False
        
        # 2. PDFファイル読み込み
        logger.info(f"📄 PDFファイル読み込み: {pdf_path}")
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        file_size = len(pdf_bytes)
        logger.info(f"📊 ファイルサイズ: {file_size:,} バイト ({file_size/1024/1024:.2f} MB)")
        
        # 3. 環境変数確認
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("❌ GEMINI_API_KEY または GOOGLE_API_KEY 環境変数が設定されていません")
            logger.info("💡 .envファイルまたは環境変数で設定してください:")
            logger.info("   export GEMINI_API_KEY='your_api_key_here'")
            return False
        
        logger.info("✅ Gemini API Key設定済み")
        
        # 4. PyMuPDF可用性確認
        try:
            import fitz
            logger.info("✅ PyMuPDF (fitz) が利用可能")
        except ImportError:
            logger.error("❌ PyMuPDF (fitz) が利用できません")
            logger.info("💡 インストールしてください: pip install PyMuPDF")
            return False
        
        # 5. Gemini 2.5 Flash OCR実行
        logger.info("🚀 Gemini 2.5 Flash OCR処理開始")
        
        from modules.knowledge.gemini_flash_ocr import ocr_pdf_with_gemini_flash
        
        start_time = asyncio.get_event_loop().time()
        result_text = await ocr_pdf_with_gemini_flash(pdf_bytes)
        end_time = asyncio.get_event_loop().time()
        
        processing_time = end_time - start_time
        
        # 6. 結果確認
        if result_text and not result_text.startswith("OCR処理エラー"):
            logger.info("✅ Gemini 2.5 Flash OCR処理成功!")
            logger.info(f"⏱️ 処理時間: {processing_time:.2f}秒")
            logger.info(f"📝 抽出文字数: {len(result_text):,}文字")
            
            # ページ数カウント
            page_count = result_text.count("--- ページ")
            if page_count > 0:
                logger.info(f"📄 抽出ページ数: {page_count}ページ")
                logger.info(f"📊 平均文字/ページ: {len(result_text)/page_count:.1f}文字")
            
            # 結果プレビュー
            preview_length = 500
            preview_text = result_text[:preview_length]
            logger.info(f"📖 抽出テキストプレビュー (最初の{preview_length}文字):")
            print("=" * 50)
            print(preview_text)
            if len(result_text) > preview_length:
                print(f"\n... (残り {len(result_text) - preview_length:,} 文字)")
            print("=" * 50)
            
            # 結果をファイルに保存
            output_path = f"{Path(pdf_path).stem}_ocr_result.txt"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result_text)
            logger.info(f"💾 結果をファイルに保存: {output_path}")
            
            return True
        else:
            logger.error("❌ Gemini 2.5 Flash OCR処理失敗")
            logger.error(f"エラー内容: {result_text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    
    # コマンドライン引数確認
    if len(sys.argv) != 2:
        print("使用方法: python test_gemini_flash_ocr.py [pdf_file_path]")
        print("例: python test_gemini_flash_ocr.py sample.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    logger.info("🧪 Gemini 2.5 Flash OCR テスト開始")
    logger.info(f"📁 対象ファイル: {pdf_path}")
    
    # 環境変数読み込み
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("✅ .envファイル読み込み完了")
    except ImportError:
        logger.warning("⚠️ python-dotenvが利用できません。環境変数は手動設定してください。")
    except Exception as e:
        logger.warning(f"⚠️ .envファイル読み込みエラー: {e}")
    
    # 非同期実行
    success = asyncio.run(test_gemini_flash_ocr(pdf_path))
    
    if success:
        logger.info("🎉 テスト完了 - Gemini 2.5 Flash OCR正常動作!")
        sys.exit(0)
    else:
        logger.error("💥 テスト失敗 - 上記エラーを確認してください")
        sys.exit(1)

if __name__ == "__main__":
    main() 