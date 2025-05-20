"""
PDFファイル処理モジュール
PDFファイルの読み込みと処理を行います
"""
import pandas as pd
import PyPDF2
from io import BytesIO
import re
import traceback
from .ocr import ocr_pdf_to_text_from_bytes
from ..database import ensure_string

async def process_pdf_file(contents, filename):
    """PDFファイルを処理してデータフレーム、セクション、テキストを返す"""
    try:
        # BytesIOオブジェクトを作成
        pdf_file = BytesIO(contents)
        
        # PDFファイルを読み込む
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # テキストを抽出
        all_text = ""
        sections = {}
        extracted_text = f"=== ファイル: {filename} ===\n\n"
        
        for i, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                # Ensure page_text is not None and convert to string if needed
                if page_text is not None:
                    page_text = ensure_string(page_text).replace('\x00', '') # 🧼 Remove NUL characters
                    section_name = f"ページ {i+1}"
                    sections[section_name] = page_text
                    all_text += page_text + "\n"
                    extracted_text += f"=== {section_name} ===\n{page_text}\n\n"
                else:
                    print(f"ページ {i+1} にテキストがありません")
                    section_name = f"ページ {i+1}"
                    sections[section_name] = ""
                    extracted_text += f"=== {section_name} ===\n[テキストなし]\n\n"
            except Exception as page_error:
                print(f"ページ {i+1} の処理中にエラー: {str(page_error)}")
                section_name = f"ページ {i+1}"
                sections[section_name] = f"[エラー: {str(page_error)}]"
                extracted_text += f"=== {section_name} ===\n[エラー: {str(page_error)}]\n\n"
        
        # テキストをセクションに分割
        # 見出しパターン
        heading_pattern = r'^(?:\d+[\.\s]+|第\d+[章節]\s+|[\*\#]+\s+)?([A-Za-z\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]{2,}[：:、。])'
        
        # データを作成
        all_data = []
        current_section = "一般情報"
        current_content = []
        
        # Ensure all_text is not empty and is a string
        all_text_str = str(all_text) if all_text is not None else ""
        if all_text_str:
            for line in all_text_str.split("\n"):
                line = str(line).strip()
                if not line:
                    continue
                
                # 見出しかどうかを判定
                if re.search(heading_pattern, line):
                    # 前のセクションを保存
                    if current_content:
                        # 必ず文字列に変換してから結合
                        content_text = "\n".join([ensure_string(item) for item in current_content])
                        all_data.append({
                            'section': str(current_section),
                            'content': content_text,
                            'source': 'PDF',
                            'file': filename,
                            'url': None
                        })
                    
                    # 新しいセクションを開始
                    current_section = str(line)
                    current_content = []
                else:
                    current_content.append(str(line))
            
            # 最後のセクションを保存
            if current_content:
                # 必ず文字列に変換してから結合
                content_text = "\n".join([ensure_string(item) for item in current_content])
                all_data.append({
                    'section': str(current_section),
                    'content': content_text,
                    'source': 'PDF',
                    'file': filename,
                    'url': None
                })
        
        # Check if we need to use OCR
        if not all_text:
            print("テキストが抽出できないため、OCRを使用します")
            try:
                ocr_result = await ocr_pdf_to_text_from_bytes(contents)
                # Ensure all_text is a string
                all_text = ensure_string(ocr_result)
                print(f"OCRによるテキスト抽出完了: {len(all_text)} 文字")
            except Exception as ocr_error:
                print(f"OCRエラー: {str(ocr_error)}")
                all_text = f"[OCRエラー: {str(ocr_error)}]"
            
            result_df = pd.DataFrame(all_data) if all_data else pd.DataFrame({
                'section': ["一般情報"],
                'content': [str(all_text or "")],  # Ensure content is a string
                'source': ['PDF'],
                'file': [filename],
                'url': [None]
            })
            extracted_text += str(all_text or "")  # Ensure extracted_text is a string
        else: 
            # データフレームを作成
            result_df = pd.DataFrame(all_data) if all_data else pd.DataFrame({
                'section': ["一般情報"],
                'content': [str(all_text)],  # Ensure content is a string
                'source': ['PDF'],
                'file': [filename],
                'url': [None]
            })
        
        # すべての列の値を文字列に変換
        for col in result_df.columns:
            result_df[col] = result_df[col].apply(ensure_string)
        
        return result_df, sections, extracted_text
    except Exception as e:
        print(f"PDFファイル処理エラー: {str(e)}")
        print(traceback.format_exc())
        
        # エラーが発生しても最低限のデータを返す
        empty_df = pd.DataFrame({
            'section': ["エラー"],
            'content': [f"PDFファイル処理中にエラーが発生しました: {str(e)}"],
            'source': ['PDF'],
            'file': [filename],
            'url': [None]
        })
        empty_sections = {"エラー": f"PDFファイル処理中にエラーが発生しました: {str(e)}"}
        error_text = f"=== ファイル: {filename} ===\n\n=== エラー ===\nPDFファイル処理中にエラーが発生しました: {str(e)}\n\n"
        
        return empty_df, empty_sections, error_text 