"""
画像ファイル処理モジュール
画像ファイルからGemini OCRでテキストを抽出します
"""
import asyncio
import traceback
import pandas as pd
from io import BytesIO
from PIL import Image
from ..config import setup_gemini
from ..database import ensure_string

# Geminiモデルをセットアップ
model = setup_gemini()

def is_image_file(filename: str) -> bool:
    """ファイルが画像形式かどうかを判定する"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
    return any(filename.lower().endswith(ext) for ext in image_extensions)

async def extract_text_from_image_with_gemini(image_content: bytes, filename: str) -> str:
    """Geminiを使用して画像からテキストを抽出する"""
    try:
        # バイトデータからPIL Imageオブジェクトを作成
        image = Image.open(BytesIO(image_content))
        
        # 画像が有効かどうかを確認
        image.verify()
        
        # 再度開く（verifyの後は再度開く必要がある）
        image = Image.open(BytesIO(image_content))
        
        # OCR用のプロンプト
        prompt = """
        この画像からすべてのテキストを抽出してください。以下の点に注意してください：
        
        1. 表がある場合：
           - 表の構造をマークダウン形式で保持する
           - すべての列ヘッダーと行ラベルを保持する
           - 数値データを正確に抽出する
        
        2. 複数列のレイアウトの場合：
           - 左から右の順序で処理する
           - 異なる列のコンテンツを明確に分離する
        
        3. グラフやチャートの場合：
           - チャートの種類を説明する
           - 軸ラベル、凡例、データポイントを抽出する
           - タイトルやキャプションを抽出する
        
        4. その他：
           - ヘッダー、フッター、ページ番号、脚注をすべて保持する
           - 段落の区切りや書式を保持する
           - 読み取れない文字がある場合は [不明] と記載する
        
        画像ファイル名: {filename}
        
        抽出したテキストのみを返してください：
        """.format(filename=filename)
        
        def sync_ocr():
            try:
                response = model.generate_content([prompt, image])
                result_text = ""
                for part in response.parts:
                    if hasattr(part, 'text'):
                        part_text = ensure_string(part.text)
                    else:
                        part_text = ""
                    result_text += part_text
                return result_text
            except Exception as e:
                print(f"Gemini OCRエラー: {str(e)}")
                return f"[OCRエラー: {str(e)}]"
        
        # 非同期でGemini APIを呼び出す
        extracted_text = await asyncio.to_thread(sync_ocr)
        
        if not extracted_text or extracted_text.strip() == "":
            return f"[画像からテキストを抽出できませんでした: {filename}]"
        
        return ensure_string(extracted_text)
        
    except Exception as e:
        print(f"画像OCR処理エラー: {str(e)}")
        print(traceback.format_exc())
        return f"[画像処理エラー: {str(e)}]"

async def process_image_file(contents: bytes, filename: str):
    """画像ファイルを処理してデータフレーム、セクション、テキストを返す"""
    try:
        print(f"画像ファイル処理開始: {filename}")
        
        # Gemini OCRでテキストを抽出
        extracted_text = await extract_text_from_image_with_gemini(contents, filename)
        
        # セクション情報を作成
        sections = {
            "画像内容": extracted_text
        }
        
        # 抽出したテキストをフォーマット
        formatted_text = f"=== ファイル: {filename} ===\n\n=== 画像内容 ===\n{extracted_text}\n\n"
        
        # データフレームを作成
        df = pd.DataFrame({
            'section': ["画像内容"],
            'content': [extracted_text],
            'source': ['画像'],
            'file': [filename],
            'url': [None]
        })
        
        # すべての列の値を文字列に変換
        for col in df.columns:
            df[col] = df[col].apply(ensure_string)
        
        print(f"画像OCR処理完了: {len(extracted_text)} 文字")
        return df, sections, formatted_text
        
    except Exception as e:
        print(f"画像ファイル処理エラー: {str(e)}")
        print(traceback.format_exc())
        
        # エラーが発生しても最低限のデータを返す
        error_message = f"画像ファイル処理中にエラーが発生しました: {str(e)}"
        empty_df = pd.DataFrame({
            'section': ["エラー"],
            'content': [error_message],
            'source': ['画像'],
            'file': [filename],
            'url': [None]
        })
        empty_sections = {"エラー": error_message}
        error_text = f"=== ファイル: {filename} ===\n\n=== エラー ===\n{error_message}\n\n"
        
        return empty_df, empty_sections, error_text

def check_text_corruption(text: str) -> bool:
    """テキストが文字化けしているかどうかを判定する"""
    if not text or len(text.strip()) == 0:
        return True
    
    # 文字化けパターンを検出
    corruption_indicators = [
        # 意味のない文字の連続
        '\ufffd',  # 置換文字（文字化け）
        # 極端に短いテキスト（画像や複雑なレイアウトの場合）
        len(text.strip()) < 50 and not any(char.isalnum() for char in text),
        # 数字や記号のみで構成されている
        len([char for char in text if char.isalpha()]) / len(text) < 0.1 if len(text) > 0 else True,
        # 極端に多くの改行や空白
        text.count('\n') / len(text) > 0.5 if len(text) > 0 else False,
    ]
    
    return any(corruption_indicators)