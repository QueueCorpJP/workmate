#!/usr/bin/env python3
"""
Excel データ損失修正のテストスクリプト
Ultra Conservative cleaner を最優先にした修正が効果的かテスト
"""

import sys
import os
import logging
import asyncio
from modules.document_processor import DocumentProcessor
from fastapi import UploadFile
from io import BytesIO

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_excel_processing_fix():
    """修正されたExcel処理をテスト"""
    
    # Excel ファイルのパス
    excel_file_path = "01_ISP案件一覧.xlsx"
    
    if not os.path.exists(excel_file_path):
        logger.error(f"❌ Excelファイルが見つかりません: {excel_file_path}")
        return
    
    # ファイルを読み込み
    with open(excel_file_path, 'rb') as f:
        content = f.read()
    
    logger.info(f"📊 Excelファイル読み込み完了: {excel_file_path} ({len(content)} bytes)")
    
    # DocumentProcessorを初期化
    try:
        processor = DocumentProcessor()
        logger.info("✅ DocumentProcessor初期化完了")
    except Exception as e:
        logger.error(f"❌ DocumentProcessor初期化エラー: {e}")
        return
    
    # UploadFileオブジェクトを模擬
    class MockUploadFile:
        def __init__(self, filename: str, content: bytes):
            self.filename = filename
            self.content = content
            self.size = len(content)
    
    mock_file = MockUploadFile(excel_file_path, content)
    
    # Excel処理をテスト
    logger.info("\n=== Excel処理テスト（修正版） ===")
    try:
        extracted_text = await processor._extract_text_from_excel(content)
        
        logger.info(f"✅ Excel処理成功")
        logger.info(f"📊 抽出文字数: {len(extracted_text):,} 文字")
        line_count = extracted_text.count('\n') + 1
        logger.info(f"📊 抽出行数: {line_count} 行")
        
        # 特定のデータが含まれているかチェック
        test_data = [
            "ISP100001",
            "C商事", 
            "有限会社B",
            "株式会社A",
            "D工業",
            "案件一覧",
            "メタデータ",
            "統計"
        ]
        
        logger.info("\n=== データ存在確認 ===")
        found_data = []
        missing_data = []
        
        for data in test_data:
            if data in extracted_text:
                found_data.append(data)
                logger.info(f"✅ 発見: {data}")
            else:
                missing_data.append(data)
                logger.warning(f"❌ 未発見: {data}")
        
        # 結果サマリー
        logger.info(f"\n📊 データ存在確認結果:")
        logger.info(f"   発見: {len(found_data)}/{len(test_data)} ({len(found_data)/len(test_data)*100:.1f}%)")
        
        if missing_data:
            logger.warning(f"⚠️ 未発見データ: {missing_data}")
        else:
            logger.info("🎉 全てのテストデータが発見されました！")
        
        # 抽出テキストの一部を表示
        logger.info(f"\n=== 抽出テキストプレビュー（最初の1000文字） ===")
        preview = extracted_text[:1000].replace('\n', '\\\\n')
        logger.info(f"{preview}...")
        
        return {
            "success": True,
            "extracted_length": len(extracted_text),
            "found_data": found_data,
            "missing_data": missing_data,
            "data_completeness": len(found_data)/len(test_data)*100
        }
        
    except Exception as e:
        logger.error(f"❌ Excel処理エラー: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def test_chunking_process():
    """チャンク化処理もテスト"""
    
    excel_file_path = "01_ISP案件一覧.xlsx"
    
    if not os.path.exists(excel_file_path):
        logger.error(f"❌ Excelファイルが見つかりません: {excel_file_path}")
        return
    
    with open(excel_file_path, 'rb') as f:
        content = f.read()
    
    try:
        processor = DocumentProcessor()
        
        # テキスト抽出
        extracted_text = await processor._extract_text_from_excel(content)
        
        # チャンク化
        logger.info("\n=== チャンク化処理テスト ===")
        chunks = processor._split_text_into_chunks(extracted_text, excel_file_path)
        
        logger.info(f"✅ チャンク化完了")
        logger.info(f"📊 チャンク数: {len(chunks)}")
        
        # 各チャンクの情報を表示
        total_chunk_chars = 0
        for i, chunk in enumerate(chunks[:5]):  # 最初の5チャンクのみ表示
            chunk_content = chunk["content"]
            chunk_tokens = chunk["token_count"]
            total_chunk_chars += len(chunk_content)
            
            logger.info(f"   チャンク{i+1}: {len(chunk_content)} 文字, {chunk_tokens} トークン")
            preview_content = chunk_content[:100].replace('\n', ' ')
            logger.info(f"     内容プレビュー: {preview_content}...")
        
        if len(chunks) > 5:
            logger.info(f"   ... 他 {len(chunks) - 5} チャンク")
        
        # データ保持率を計算
        data_retention = total_chunk_chars / len(extracted_text) * 100
        logger.info(f"📊 データ保持率: {data_retention:.1f}% ({total_chunk_chars:,}/{len(extracted_text):,} 文字)")
        
        return {
            "success": True,
            "chunk_count": len(chunks),
            "total_chunk_chars": total_chunk_chars,
            "original_chars": len(extracted_text),
            "data_retention": data_retention
        }
        
    except Exception as e:
        logger.error(f"❌ チャンク化処理エラー: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def main():
    """メイン処理"""
    logger.info("🚀 Excel データ損失修正テスト開始")
    
    # Excel処理テスト
    excel_result = await test_excel_processing_fix()
    
    if excel_result["success"]:
        # チャンク化テスト
        chunk_result = await test_chunking_process()
        
        # 総合結果
        logger.info("\n=== 総合テスト結果 ===")
        logger.info(f"Excel処理: {'✅ 成功' if excel_result['success'] else '❌ 失敗'}")
        if excel_result["success"]:
            logger.info(f"  データ完全性: {excel_result['data_completeness']:.1f}%")
            logger.info(f"  抽出文字数: {excel_result['extracted_length']:,}")
        
        if chunk_result and chunk_result["success"]:
            logger.info(f"チャンク化: ✅ 成功")
            logger.info(f"  チャンク数: {chunk_result['chunk_count']}")
            logger.info(f"  データ保持率: {chunk_result['data_retention']:.1f}%")
        
        # 修正効果の評価
        if excel_result["success"] and excel_result["data_completeness"] >= 95:
            logger.info("🎉 修正が効果的です！データ損失が大幅に改善されました。")
        elif excel_result["success"] and excel_result["data_completeness"] >= 80:
            logger.info("✅ 修正が部分的に効果的です。さらなる改善の余地があります。")
        else:
            logger.warning("⚠️ まだデータ損失が発生しています。追加の修正が必要です。")
    
    logger.info("🏁 テスト完了")

if __name__ == "__main__":
    asyncio.run(main())