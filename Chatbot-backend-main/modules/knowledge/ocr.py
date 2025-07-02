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

async def ocr_with_gemini(images, instruction, chunk_size=8):
    """Geminiを使用して画像からテキストを抽出する（8ページずつ分割処理）"""
    prompt_base = f"""
{instruction}

このページはPDF文書の1ページです。上記の指針に従って、このページから全てのテキストを抽出してください。
元の文書構造を維持し、表・リスト・見出しなどの構造化されたコンテンツに特に注意を払ってください。
段落の区切りやフォーマットを維持してください。
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
            # 処理速度を制御するため少し待機
            await asyncio.sleep(0.5)
            return await asyncio.to_thread(sync_call)
        except Exception as e:
            print(f"Async error processing page {idx + 1}: {str(e)}")
            return f"\n\n[Error processing page {idx + 1}]: {str(e)}\n"

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
            chunk_results = await asyncio.gather(*tasks)
            all_results.extend(chunk_results)
            
            # チャンク間で少し待機（APIレート制限対策）
            if i + chunk_size < len(images):
                print(f"次のチャンク処理前に待機中...")
                await asyncio.sleep(2.0)
        
        results = all_results
    else:
        # 通常処理（8ページ以下）
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