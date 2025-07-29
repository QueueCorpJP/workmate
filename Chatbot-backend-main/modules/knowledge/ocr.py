"""
📷 OCR処理モジュール - Gemini REST API版
🔧 SDK不使用、純粋なHTTPリクエストでGemini APIを呼び出し
🖼️ 画像→テキスト変換（PDF含む）
"""

import os
import io
import base64
import json
import logging
import asyncio
import aiohttp
from typing import List, Optional
from pdf2image import convert_from_bytes
from PIL import Image

logger = logging.getLogger(__name__)

class GeminiOCRProcessor:
    """Gemini REST APIを使用したOCRプロセッサ"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY または GOOGLE_API_KEY 環境変数が設定されていません")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """PIL ImageをBase64エンコードされた文字列に変換"""
        buffered = io.BytesIO()
        # PNG形式で保存（透明度対応）
        image.save(buffered, format="PNG")
        img_data = buffered.getvalue()
        return base64.b64encode(img_data).decode('utf-8')
    
    async def _call_gemini_api(self, images_b64: List[str], prompt: str) -> str:
        """Gemini REST APIを直接呼び出し"""
        try:
            # リクエストペイロード構築
            contents = [{
                "parts": [
                    {"text": prompt}
                ]
            }]
            
            # 画像を追加
            for img_b64 in images_b64:
                contents[0]["parts"].append({
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": img_b64
                    }
                })
            
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 8192,
                }
            }
            
            url = f"{self.base_url}?key={self.api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ Gemini API エラー: {response.status} - {error_text}")
                        raise Exception(f"Gemini API failed: {response.status}")
                    
                    result = await response.json()
                    
                    if "candidates" not in result or not result["candidates"]:
                        logger.error("❌ Gemini API レスポンスにcandidatesがありません")
                        raise Exception("No candidates in response")
                    
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    return content.strip()
        
        except Exception as e:
            logger.error(f"❌ Gemini API呼び出しエラー: {e}")
            raise

async def ocr_with_gemini(images, instruction, chunk_size=8):
    """Gemini REST APIを使用して画像からテキストを抽出する（8ページずつ分割処理）"""
    
    processor = GeminiOCRProcessor()
    all_text = []
    
    # 画像を8枚ずつのチャンクに分割
    for i in range(0, len(images), chunk_size):
        chunk_images = images[i:i + chunk_size]
        logger.info(f"🔄 処理中: {i + 1}-{min(i + len(chunk_images), len(images))} / {len(images)} ページ")
        
        try:
            # PIL ImageをBase64に変換
            images_b64 = []
            for img in chunk_images:
                if isinstance(img, Image.Image):
                    img_b64 = processor._image_to_base64(img)
                    images_b64.append(img_b64)
                else:
                    logger.warning("⚠️ 無効な画像形式をスキップ")
                    continue
            
            if not images_b64:
                logger.warning("⚠️ 有効な画像がありません - チャンクをスキップ")
                continue
            
            # Gemini APIを呼び出し
            text = await processor._call_gemini_api(images_b64, instruction)
            
            if text and text.strip():
                all_text.append(text)
                logger.info(f"✅ チャンク処理完了: {len(text)}文字抽出")
            else:
                logger.warning("⚠️ 空のテキストが返されました")
        
        except Exception as e:
            logger.error(f"❌ チャンク処理エラー: {e}")
            continue
    
    if all_text:
        final_text = "\n\n".join(all_text)
        logger.info(f"✅ OCR完了: 総文字数 {len(final_text)}")
        return final_text
    else:
        logger.error("❌ 全チャンクでOCR失敗")
        return "OCR処理中にエラーが発生しました"

async def ocr_pdf_to_text_from_bytes(pdf_bytes: bytes) -> str:
    """PDFバイトデータからOCRでテキスト抽出（REST API版）"""
    logger.info("📄 PDF→OCR処理開始（REST API版）")
    
    try:
        # PDFを画像に変換
        logger.info("🔄 PDFを画像に変換中...")
        images = convert_from_bytes(pdf_bytes, dpi=200, fmt='PNG')
        logger.info(f"📄 {len(images)}ページの画像変換完了")
        
        if not images:
            logger.error("❌ PDF画像変換失敗")
            return "PDF画像変換に失敗しました"
        
        # OCR処理用の指示文
        instruction = """
        画像内のテキストを正確に読み取り、日本語として出力してください。
        レイアウトや表構造は可能な限り保持してください。
        読み取れない文字や不明瞭な部分は[?]で表示してください。
        """
        
        # Gemini OCR実行
        result = await ocr_with_gemini(images, instruction, chunk_size=8)
        
        if result and not result.startswith("OCR処理中にエラーが発生しました"):
            logger.info("✅ PDF OCR処理完了")
            return result
        else:
            logger.error("❌ PDF OCR処理失敗")
            return "PDF OCR処理に失敗しました"
    
    except Exception as e:
        logger.error(f"❌ PDF OCR処理エラー: {e}")
        return f"PDF OCR処理エラー: {str(e)}"

# 後方互換性のための関数エイリアス
async def ocr_image_with_gemini(image_data, instruction="画像内のテキストを抽出してください。"):
    """単一画像のOCR処理"""
    try:
        # バイトデータをPIL Imageに変換
        if isinstance(image_data, bytes):
            image = Image.open(io.BytesIO(image_data))
        else:
            image = image_data
        
        result = await ocr_with_gemini([image], instruction, chunk_size=1)
        return result
    except Exception as e:
        logger.error(f"❌ 画像OCRエラー: {e}")
        return f"画像OCR処理エラー: {str(e)}"