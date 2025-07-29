"""
🚀 Gemini 2.5 Flash OCR処理モジュール - PyMuPDF版
🎯 Popplerに依存しない完璧なOCR処理システム
🖼️ PyMuPDFでPDF→画像変換 + Gemini 2.5 Flash Vision API

特徴:
- ✅ Popplerが不要（PyMuPDFのみ使用）
- ✅ Gemini 2.5 Flash Vision APIで高精度OCR
- ✅ バッチ処理による高速化
- ✅ 画像品質の自動最適化
- ✅ エラーハンドリングとリトライ機能
"""

import os
import io
import base64
import logging
import asyncio
import time
from typing import List, Optional, Tuple
from PIL import Image
import requests
import json

logger = logging.getLogger(__name__)

class GeminiFlashOCRProcessor:
    """Gemini 2.5 Flash APIを使用した高性能OCRプロセッサ"""
    
    def __init__(self):
        """初期化"""
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY または GOOGLE_API_KEY 環境変数が設定されていません")
        
        # Gemini 2.5 Flash Vision API設定
        self.model_name = "gemini-2.5-flash"
        self.api_base_url = "https://generativelanguage.googleapis.com/v1beta"
        
        # OCR設定
        self.max_batch_size = 4  # バッチサイズ（API制限に合わせて調整）
        self.max_retries = 3     # リトライ回数
        self.retry_delay = 2.0   # リトライ間隔
        
        logger.info(f"✅ Gemini 2.5 Flash OCRプロセッサ初期化完了")
    
    def _check_pymupdf_availability(self) -> bool:
        """PyMuPDFの可用性をチェック"""
        try:
            import fitz
            return True
        except ImportError:
            logger.error("❌ PyMuPDF (fitz) が利用できません。インストールしてください: pip install PyMuPDF")
            return False
    
    def _extract_pages_as_images(self, pdf_bytes: bytes, dpi: int = 300) -> List[Image.Image]:
        """PyMuPDFを使用してPDFページを画像として抽出"""
        if not self._check_pymupdf_availability():
            raise Exception("PyMuPDFが利用できません")
        
        import fitz
        
        images = []
        logger.info(f"🔄 PyMuPDFでPDFページを画像に変換中（DPI: {dpi}）...")
        
        try:
            # PDFを開く
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                total_pages = len(doc)
                logger.info(f"📄 PDF総ページ数: {total_pages}")
                
                for page_num in range(total_pages):
                    page = doc[page_num]
                    
                    # 高品質設定でページを画像に変換
                    mat = fitz.Matrix(dpi/72, dpi/72)  # DPI設定
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    
                    # PIL Imageに変換
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # 画像品質の最適化
                    img = self._optimize_image_for_ocr(img)
                    images.append(img)
                    
                    logger.info(f"📄 ページ {page_num + 1}/{total_pages} 変換完了 ({img.size[0]}x{img.size[1]})")
                
                logger.info(f"✅ 全ページの画像変換完了: {len(images)}枚")
                return images
                
        except Exception as e:
            logger.error(f"❌ PDF→画像変換エラー: {e}")
            raise Exception(f"PDF→画像変換に失敗: {e}")
    
    def _optimize_image_for_ocr(self, img: Image.Image) -> Image.Image:
        """OCR処理に最適化された画像に変換"""
        try:
            # RGBモードに変換
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 画像サイズの最適化（大きすぎる場合は縮小）
            max_dimension = 4096  # Gemini APIの推奨最大サイズ
            if max(img.size) > max_dimension:
                ratio = max_dimension / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.debug(f"🔧 画像サイズ最適化: {new_size}")
            
            return img
            
        except Exception as e:
            logger.warning(f"⚠️ 画像最適化エラー: {e}")
            return img
    
    def _image_to_base64(self, img: Image.Image) -> str:
        """PIL ImageをBase64エンコード"""
        buffer = io.BytesIO()
        # 高品質PNG形式で保存
        img.save(buffer, format="PNG", optimize=True)
        img_data = buffer.getvalue()
        return base64.b64encode(img_data).decode('utf-8')
    
    async def _call_gemini_vision_api(self, images_b64: List[str], prompt: str) -> str:
        """Gemini 2.5 Flash Vision APIを呼び出し"""
        api_url = f"{self.api_base_url}/models/{self.model_name}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        # 画像データをpartsに変換
        parts = [{"text": prompt}]
        for img_b64 in images_b64:
            parts.append({
                "inline_data": {
                    "mime_type": "image/png",
                    "data": img_b64
                }
            })
        
        request_data = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": 0.1,  # 精度重視で低温度
                "maxOutputTokens": 8192,
                "topP": 0.8,
                "topK": 40
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        }
        
        # リトライ機能付きでAPI呼び出し
        for attempt in range(self.max_retries):
            try:
                logger.info(f"🤖 Gemini 2.5 Flash Vision API呼び出し (試行 {attempt + 1}/{self.max_retries})")
                
                response = requests.post(
                    api_url, 
                    headers=headers, 
                    json=request_data, 
                    timeout=120  # 2分のタイムアウト
                )
                response.raise_for_status()
                
                result = response.json()
                
                if "candidates" in result and len(result["candidates"]) > 0:
                    text_content = result["candidates"][0]["content"]["parts"][0]["text"]
                    logger.info(f"✅ Gemini Vision API成功 ({len(text_content)}文字)")
                    return text_content
                else:
                    raise Exception("APIレスポンスにテキストコンテンツが含まれていません")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ API呼び出しエラー (試行 {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise Exception(f"API呼び出しが{self.max_retries}回失敗しました: {e}")
            except Exception as e:
                logger.error(f"❌ 予期しないエラー: {e}")
                raise
    
    async def _process_image_batch(self, images: List[Image.Image], start_page: int) -> str:
        """画像バッチのOCR処理"""
        logger.info(f"🔄 バッチ処理開始: ページ {start_page + 1}～{start_page + len(images)}")
        
        # 画像をBase64に変換
        images_b64 = []
        for i, img in enumerate(images):
            try:
                b64_data = self._image_to_base64(img)
                images_b64.append(b64_data)
                logger.debug(f"📄 ページ {start_page + i + 1} Base64変換完了")
            except Exception as e:
                logger.warning(f"⚠️ ページ {start_page + i + 1} Base64変換エラー: {e}")
                continue
        
        if not images_b64:
            logger.warning("⚠️ 有効な画像がバッチに含まれていません")
            return ""
        
        # 高精度OCR用プロンプト
        ocr_prompt = f"""
以下の{len(images_b64)}枚の画像に含まれるすべてのテキストを正確に抽出してください。

**抽出指針:**
• 日本語・英語・数字・記号を全て漏れなく抽出
• 表やリストの構造を可能な限り維持
• 見出し・本文・注釈を区別して抽出
• ページ番号や図表番号も含めて抽出

**出力形式:**
各ページのテキストを以下の形式で出力：

--- ページ {start_page + 1} ---
[ページ内容]

--- ページ {start_page + 2} ---
[ページ内容]

**品質要求:**
• 誤字・脱字を最小限に抑制
• 文脈から判断して曖昧な文字を推測
• レイアウトを考慮した読み順で抽出
• 表は可能な限りMarkdown形式で構造化

すべてのテキストを正確に抽出してください。
"""
        
        # Gemini Vision API呼び出し
        try:
            result_text = await self._call_gemini_vision_api(images_b64, ocr_prompt)
            logger.info(f"✅ バッチOCR完了: {len(result_text)}文字抽出")
            return result_text
        except Exception as e:
            logger.error(f"❌ バッチOCR失敗: {e}")
            return f"[ページ {start_page + 1}～{start_page + len(images)} OCR処理エラー: {e}]"
    
    async def process_pdf_with_gemini_flash_ocr(self, pdf_bytes: bytes) -> str:
        """PDFからGemini 2.5 Flash OCRでテキスト抽出（完璧版）"""
        logger.info("🚀 Gemini 2.5 Flash OCR処理開始（完璧版）")
        
        try:
            # 1. PDFページを画像として抽出
            images = self._extract_pages_as_images(pdf_bytes, dpi=300)
            
            if not images:
                raise Exception("PDFから画像を抽出できませんでした")
            
            # 2. バッチ処理でOCR実行
            all_results = []
            total_batches = (len(images) + self.max_batch_size - 1) // self.max_batch_size
            
            logger.info(f"📊 OCR処理計画: {len(images)}ページを{total_batches}バッチで処理")
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * self.max_batch_size
                end_idx = min(start_idx + self.max_batch_size, len(images))
                batch_images = images[start_idx:end_idx]
                
                logger.info(f"🔄 バッチ {batch_idx + 1}/{total_batches} 処理中...")
                
                try:
                    batch_result = await self._process_image_batch(batch_images, start_idx)
                    all_results.append(batch_result)
                    
                    # API制限を考慮した待機
                    if batch_idx < total_batches - 1:
                        await asyncio.sleep(1.0)
                        
                except Exception as batch_error:
                    logger.error(f"❌ バッチ {batch_idx + 1} 処理エラー: {batch_error}")
                    all_results.append(f"[バッチ {batch_idx + 1} 処理エラー: {batch_error}]")
            
            # 3. 結果統合
            final_text = "\n\n".join(all_results)
            
            # 4. 品質チェック
            total_chars = len(final_text)
            pages_processed = len(images)
            avg_chars_per_page = total_chars / pages_processed if pages_processed > 0 else 0
            
            logger.info(f"✅ Gemini 2.5 Flash OCR処理完了:")
            logger.info(f"   - 処理ページ数: {pages_processed}")
            logger.info(f"   - 抽出文字数: {total_chars:,}")
            logger.info(f"   - 平均文字/ページ: {avg_chars_per_page:.1f}")
            logger.info(f"   - 成功バッチ数: {len([r for r in all_results if not r.startswith('[') or not r.endswith(']')])}/{total_batches}")
            
            return final_text
            
        except Exception as e:
            logger.error(f"❌ Gemini 2.5 Flash OCR処理エラー: {e}")
            raise Exception(f"OCR処理に失敗しました: {e}")

# インスタンス作成用の関数
def get_gemini_flash_ocr_processor() -> Optional[GeminiFlashOCRProcessor]:
    """Gemini 2.5 Flash OCRプロセッサのインスタンスを取得"""
    try:
        return GeminiFlashOCRProcessor()
    except Exception as e:
        logger.error(f"❌ Gemini Flash OCRプロセッサの初期化に失敗: {e}")
        return None

# エントリーポイント関数
async def ocr_pdf_with_gemini_flash(pdf_bytes: bytes) -> str:
    """PDFバイトデータからGemini 2.5 Flash OCRでテキスト抽出"""
    processor = get_gemini_flash_ocr_processor()
    if processor is None:
        return "Gemini 2.5 Flash OCRプロセッサの初期化に失敗しました"
    
    try:
        return await processor.process_pdf_with_gemini_flash_ocr(pdf_bytes)
    except Exception as e:
        logger.error(f"❌ OCR処理エラー: {e}")
        return f"OCR処理エラー: {e}" 