"""
OCR処理モジュール
PDFからのテキスト抽出とOCR処理を行います
"""
import asyncio
import traceback
import os
import tempfile
from ..database import ensure_string

# Handle optional dependencies gracefully
try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("⚠️ pdf2image not available - PDF to image conversion will be disabled")

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("⚠️ google.generativeai not available - Gemini OCR will be disabled")

async def ocr_with_gemini(images, instruction, chunk_size=8):
    """Geminiを使用して画像からテキストを抽出する（8ページずつ分割処理）"""
    
    if not GENAI_AVAILABLE:
        raise ValueError("google.generativeai module is not available. Please install it with: pip install google-generativeai")
    
    # Gemini APIキーを取得
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY または GOOGLE_API_KEY 環境変数が設定されていません")
    
    # Gemini APIを設定
    genai.configure(api_key=api_key)
    
    prompt_base = f"""
{instruction}

このページはPDF文書の1ページです。上記の指針に従って、このページから全てのテキストを抽出してください。
元の文書構造を維持し、表・リスト・見出しなどの構造化されたコンテンツに特に注意を払ってください。
段落の区切りやフォーマットを維持してください。
"""

    async def process_page(idx, image):
        try:
            prompt = f"{prompt_base}\n\nPage {idx + 1}:"
            
            # Gemini 1.5 Flash モデルを使用
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # 生成設定を辞書形式で作成（新しいSDKに対応）
            generation_config = {
                "temperature": 0.3,
                "max_output_tokens": 8192,
            }
            
            # 画像とプロンプトでコンテンツ生成
            response = await asyncio.to_thread(
                model.generate_content,
                [prompt, image],
                generation_config=generation_config
            )
            
            if response and response.text:
                result_text = ensure_string(response.text)
                return f"\n\n--- Page {idx + 1} ---\n{result_text}"
            else:
                print(f"Warning: No text extracted from page {idx + 1}")
                return f"\n\n--- Page {idx + 1} ---\n[テキスト抽出できませんでした]"
                
        except Exception as e:
            print(f"Error processing page {idx + 1}: {str(e)}")
            return f"\n\n--- Page {idx + 1} ---\n[Error processing page {idx + 1}]: {str(e)}"

    # ページ数が多い場合は分割処理
    if len(images) > chunk_size:
        print(f"大きなPDFファイル検出: {len(images)}ページ。{chunk_size}ページずつ分割して処理します。")
        all_results = []
        
        for i in range(0, len(images), chunk_size):
            chunk_images = images[i:i + chunk_size]
            chunk_start = i + 1
            chunk_end = min(i + chunk_size, len(images))
            
            print(f"PDFページ {chunk_start}-{chunk_end} を処理中...")
            
            # チャンクごとにタスクを作成して実行
            tasks = [process_page(i + idx, img) for idx, img in enumerate(chunk_images)]
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 例外処理
            for j, result in enumerate(chunk_results):
                if isinstance(result, Exception):
                    page_num = i + j + 1
                    print(f"Page {page_num} processing failed: {result}")
                    all_results.append(f"\n\n--- Page {page_num} ---\n[処理エラー: {str(result)}]")
                else:
                    all_results.append(result)
            
            # チャンク間で少し待機（APIレート制限対策）
            if i + chunk_size < len(images):
                print(f"次のチャンク処理前に待機中...")
                await asyncio.sleep(2.0)
        
        results = all_results
    else:
        # 通常処理（8ページ以下）
        tasks = [process_page(idx, img) for idx, img in enumerate(images)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 例外処理
        processed_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Page {idx + 1} processing failed: {result}")
                processed_results.append(f"\n\n--- Page {idx + 1} ---\n[処理エラー: {str(result)}]")
            else:
                processed_results.append(result)
        results = processed_results

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
このページから全ての文字・数字・情報を抽出してください。

抽出方針：
• 全ての文字を漏れなく読み取る
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
        if not PDF2IMAGE_AVAILABLE:
            print("⚠️ pdf2image not available - cannot convert PDF to images")
            return []
            
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