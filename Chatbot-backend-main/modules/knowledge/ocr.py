"""
📷 OCR処理モジュール - Google GenAI SDK版
🔧 最新のgoogle-genai SDKを使用
🖼️ 画像→テキスト変換（PDF含む）

環境変数:
- POPPLER_PATH: Popplerの独自パス指定（従来のOCR使用時のみ）

注意: Gemini 2.5 Flash OCRが利用可能な場合は、こちらの従来OCRは非推奨です。
新しいgemini_flash_ocr.pyを使用することを強く推奨します。
"""

import os
import io
import base64
import logging
import asyncio
import subprocess
import sys
from typing import List, Optional
from PIL import Image

logger = logging.getLogger(__name__)

# pdf2imageとpopplerの可用性チェック
try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
    
    # Popplerの可用性を事前チェック
    def check_poppler_availability():
        """Popplerが利用可能かチェック"""
        try:
            import pdf2image.exceptions
            # カスタムPopplerパスが指定されている場合
            poppler_path = os.getenv("POPPLER_PATH")
            if poppler_path:
                logger.info(f"🔧 カスタムPopplerパス使用: {poppler_path}")
                # 実際のテストは省略（パス設定のみ）
                return True
            
            # 小さなテストPDFでpopplerの動作確認
            test_result = subprocess.run(['pdftoppm', '-h'], 
                                       capture_output=True, 
                                       text=True, 
                                       timeout=5)
            return test_result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False
    
    POPPLER_AVAILABLE = check_poppler_availability()
    if not POPPLER_AVAILABLE:
        logger.warning("⚠️ Poppler is not available. PDF to image conversion will be limited.")
        logger.info("💡 推奨: Gemini 2.5 Flash OCR (gemini_flash_ocr.py) を使用してください")
        
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    POPPLER_AVAILABLE = False
    logger.warning("⚠️ pdf2image not available. PDF OCR functionality will be limited.")
    logger.info("💡 推奨: Gemini 2.5 Flash OCR (gemini_flash_ocr.py) を使用してください")

# 直接API呼び出し用のライブラリをインポート
try:
    import requests
    import json
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.error("❌ requests library not available. Please install: pip install requests")

class GeminiOCRProcessor:
    """新しいGoogle GenAI SDKを使用したOCRプロセッサ"""
    
    def __init__(self):
        if not GENAI_AVAILABLE:
            raise ValueError("requests library is not available. Please install it with: pip install requests")
        
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY または GOOGLE_API_KEY 環境変数が設定されていません")
        
        # Gemini API の直接呼び出し用URL
        self.api_base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """PIL ImageをBase64エンコードされた文字列に変換"""
        buffered = io.BytesIO()
        # PNG形式で保存（透明度対応）
        image.save(buffered, format="PNG")
        img_data = buffered.getvalue()
        return base64.b64encode(img_data).decode('utf-8')
    
    async def _call_gemini_api(self, images_b64: List[str], prompt: str) -> str:
        """Gemini APIを直接呼び出し"""
        try:
            # API URL
            api_url = f"{self.api_base_url}/models/gemini-2.5-flash:generateContent"
            
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }
            
            # コンテンツを構築
            parts = [{"text": prompt}]
            
            # 画像を追加
            for img_b64 in images_b64:
                parts.append({
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": img_b64
                    }
                })
            
            request_data = {
                "contents": [
                    {
                        "parts": parts
                    }
                ],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 8192
                }
            }
            
            # 非同期でAPIを呼び出し
            def make_request():
                return requests.post(api_url, headers=headers, json=request_data, timeout=120)
            
            response = await asyncio.to_thread(make_request)
            response.raise_for_status()
            
            response_data = response.json()
            
            if "candidates" in response_data and response_data["candidates"]:
                candidate = response_data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
            
            logger.error("❌ Gemini API レスポンスが空です")
            raise Exception("Empty response from Gemini API")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API リクエストエラー: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Gemini API呼び出しエラー: {e}")
            raise

async def ocr_with_gemini(images, instruction, chunk_size=8):
    """直接API呼び出しを使用して画像からテキストを抽出する"""
    
    if not GENAI_AVAILABLE:
        raise ValueError("requests library is not available. Please install it with: pip install requests")
    
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
        
        # チャンク間で少し待機（APIレート制限対策）
        if i + chunk_size < len(images):
            await asyncio.sleep(1.0)
    
    if all_text:
        final_text = "\n\n".join(all_text)
        logger.info(f"✅ OCR完了: 総文字数 {len(final_text)}")
        return final_text
    else:
        logger.error("❌ 全チャンクでOCR失敗")
        return "OCR処理中にエラーが発生しました"

async def ocr_pdf_to_text_from_bytes(pdf_bytes: bytes) -> str:
    """PDFバイトデータからOCRでテキスト抽出（従来版）
    
    注意: この関数は非推奨です。代わりにgemini_flash_ocr.pyのocr_pdf_with_gemini_flashを使用してください。
    """
    
    logger.warning("⚠️ 従来のOCR処理が呼び出されました。Gemini 2.5 Flash OCRの使用を推奨します。")
    
    logger.info("📄 PDF→OCR処理開始（従来版・非推奨）")
    
    # 事前チェック
    if not PDF2IMAGE_AVAILABLE:
        error_msg = "pdf2image library is not available. Please install it: pip install pdf2image"
        logger.error(f"❌ {error_msg}")
        return f"PDF OCR処理エラー: {error_msg}"
    
    if not POPPLER_AVAILABLE:
        error_msg = """Poppler is not installed or not in PATH. 

推奨解決策: Gemini 2.5 Flash OCRを使用（Poppler不要）
- gemini_flash_ocr.pyのocr_pdf_with_gemini_flashを使用してください

従来のPoppler使用方法:
- Windows: conda install -c conda-forge poppler OR choco install poppler
- Ubuntu/Debian: sudo apt-get install poppler-utils  
- macOS: brew install poppler

Custom Poppler Path:
Set environment variable: POPPLER_PATH=/path/to/poppler/bin

Download from: https://github.com/oschwartz10612/poppler-windows/releases/"""
        logger.error(f"❌ {error_msg}")
        return f"PDF OCR処理エラー: Poppler not available. {error_msg}"
    
    try:
        # PDFを画像に変換
        logger.info("🔄 PDFを画像に変換中...")
        try:
            images = convert_from_bytes(pdf_bytes, dpi=200, fmt='PNG')
            logger.info(f"📄 {len(images)}ページの画像変換完了")
        except Exception as pdf_convert_error:
            error_msg = f"PDF to image conversion failed: {str(pdf_convert_error)}"
            logger.error(f"❌ {error_msg}")
            
            # より詳細なエラー情報を提供
            if "poppler" in str(pdf_convert_error).lower():
                detailed_error = f"""Poppler error detected. Please ensure Poppler is properly installed and in PATH.
                
Installation instructions:
- Windows: conda install -c conda-forge poppler
- Ubuntu/Debian: sudo apt-get install poppler-utils
- macOS: brew install poppler

Error details: {str(pdf_convert_error)}"""
                logger.error(detailed_error)
                return f"PDF OCR処理エラー: {detailed_error}"
            
            return f"PDF OCR処理エラー: {error_msg}"
        
        if not images:
            logger.error("❌ PDF画像変換失敗")
            return "PDF画像変換に失敗しました"
        
        # OCR処理用の指示文
        instruction = """
        画像内のテキストを正確に読み取り、日本語として出力してください。
        
        抽出方針：
        • 全ての文字・数字・情報を漏れなく読み取る
        • 不鮮明でも推測して抽出（空白より推測が有用）
        • 表・リスト・見出しの構造を維持
        
        形式：
        • 見出し: # ## ###
        • 表: markdown形式（| 列1 | 列2 |）
        • 不鮮明: [推測]を付けて抽出
        
        推測指針：
        • 文脈・形状から合理的に推測
        • 型番・金額・日付は特に重要
        • 読めない場合は[判読困難]
        
        全ての情報を抽出してください。推測でも情報があることが重要です。
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