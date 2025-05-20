"""
OCR処理モジュール
PDFからのテキスト抽出とOCR処理を行います
"""
import asyncio
import traceback
from pdf2image import convert_from_bytes
from ..config import setup_gemini
from ..database import ensure_string

# Geminiモデルをセットアップ
model = setup_gemini()

async def ocr_with_gemini(images, instruction):
    """Geminiを使用して画像からテキストを抽出する"""
    prompt_base = f"""
    {instruction}
    This is a page from a PDF document. Extract all text content while preserving the structure.
    Pay special attention to tables, columns, headers, and any structured content.
    Maintain paragraph breaks and formatting.
    """

    async def process_page(idx, image):
        def sync_call():
            try:
                prompt = f"{prompt_base}\n\nPage {idx + 1}:"
                response = model.generate_content([prompt, image])
                result_text = ""
                for part in response.parts:
                    # 必ず文字列に変換
                    if hasattr(part, 'text'):
                        part_text = ensure_string(part.text)
                    else:
                        part_text = ""
                    result_text += part_text
                return f"\n\n--- Page {idx + 1} ---\n{result_text}"
            except Exception as e:
                print(f"Error processing page {idx + 1}: {str(e)}")
                return f"\n\n[Error processing page {idx + 1}]: {str(e)}\n"

        try:
            return await asyncio.to_thread(sync_call)
        except Exception as e:
            print(f"Async error processing page {idx + 1}: {str(e)}")
            return f"\n\n[Error processing page {idx + 1}]: {str(e)}\n"

    tasks = [process_page(idx, img) for idx, img in enumerate(images)]
    results = await asyncio.gather(*tasks)

    # Combine results and ensure it's a string
    combined_text = ""
    for result in results:
        if result is not None:
            combined_text += ensure_string(result)

    return combined_text

async def ocr_pdf_to_text_from_bytes(pdf_content: bytes):
    """PDFをOCRでテキストに変換する"""
    try:
        # Convert PDF to images directly from bytes
        images = convert_pdf_to_images_from_bytes(pdf_content)
        
        if not images:
            print("PDFから画像を抽出できませんでした")
            return "PDFから画像を抽出できませんでした。"

        # Define instruction for Gemini OCR
        instruction = """
        Extract ALL text content from these document pages.
        For tables:
        1. Maintain the table structure using markdown table format.
        2. Preserve all column headers and row labels.
        3. Ensure numerical data is accurately captured.
        For multi-column layouts:
        1. Process columns from left to right.
        2. Clearly separate content from different columns.
        For charts and graphs:
        1. Describe the chart type.
        2. Extract any visible axis labels, legends, and data points.
        3. Extract any title or caption.
        Preserve all headers, footers, page numbers, and footnotes.
        """

        # Extract text using Gemini OCR
        extracted_text = await ocr_with_gemini(images, instruction)
        
        # Ensure extracted_text is not None and is a string
        if extracted_text is None:
            return "OCRでテキストを抽出できませんでした。"
            
        return ensure_string(extracted_text)
    except Exception as e:
        print(f"OCR処理エラー: {str(e)}")
        print(traceback.format_exc())
        return f"OCR処理中にエラーが発生しました: {str(e)}"

def convert_pdf_to_images_from_bytes(pdf_content, dpi=200):
    """PDFをPIL画像オブジェクトのリストに変換する"""
    try:
        # Check if pdf_content is valid
        if not pdf_content or len(pdf_content) == 0:
            print("空のPDFコンテンツ")
            return []
        
        # Ensure pdf_content is bytes
        if not isinstance(pdf_content, bytes):
            print(f"無効なPDFコンテンツ型: {type(pdf_content)}")
            return []
            
        # Convert PDF to images
        try:
            # pdf2imageを使用してPDFを画像に変換
            try:
                images = convert_from_bytes(pdf_content, dpi=dpi)
            except Exception as e:
                print(f"PDF変換エラー (convert_from_bytes): {str(e)}")
                # 代替方法を試みる（dpiを下げる）
                try:
                    print("代替方法を試行: dpiを下げて変換")
                    images = convert_from_bytes(pdf_content, dpi=100)
                except Exception as e2:
                    print(f"代替PDF変換も失敗: {str(e2)}")
                    print(traceback.format_exc())
                    return []
        except Exception as e:
            print(f"PDF変換エラー: {str(e)}")
            print(traceback.format_exc())
            return []
        
        if not images:
            print("PDFから画像を抽出できませんでした")
            return []
            
        valid_images = []
        for img in images:
            if img is not None:
                valid_images.append(img)
                
        print(f"PDFから{len(valid_images)}ページの有効な画像を抽出しました")
        return valid_images  # This will return a list of PIL Image objects
    except Exception as e:
        print(f"PDF画像変換エラー: {str(e)}")
        print(traceback.format_exc())
        return [] 