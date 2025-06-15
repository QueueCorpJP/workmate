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

def check_text_corruption(text: str) -> bool:
    """テキストが文字化けしているかどうかを判定する"""
    if not text or len(text.strip()) == 0:
        return True
    
    # テキストの長さ
    text_length = len(text)
    
    # 文字化けパターンを検出
    corruption_indicators = [
        # 意味のない文字の連続
        '\ufffd' in text,  # 置換文字（文字化け）
        '��' in text,      # 文字化け記号
        
        # 極端に短いテキスト（画像や複雑なレイアウトの場合）
        text_length < 50 and not any(char.isalnum() for char in text),
        
        # アルファベット・ひらがな・カタカナ・漢字の比率が極端に低い
        len([char for char in text if char.isalpha() or 
             '\u3040' <= char <= '\u309F' or  # ひらがな
             '\u30A0' <= char <= '\u30FF' or  # カタカナ
             '\u4E00' <= char <= '\u9FAF'     # 漢字
            ]) / text_length < 0.05 if text_length > 0 else True,
        
        # 極端に多くの改行や空白
        text.count('\n') / text_length > 0.6 if text_length > 0 else False,
        text.count(' ') / text_length > 0.8 if text_length > 0 else False,
        
        # 制御文字が多い
        len([char for char in text if ord(char) < 32 and char not in '\n\r\t']) / text_length > 0.1 if text_length > 0 else False,
        
        # 高位Unicode文字が多い（文字化け可能性）
        len([char for char in text if ord(char) > 65535]) / text_length > 0.05 if text_length > 0 else False,
        
        # 意味のない文字列パターン
        text.count('�') > 10,  # 文字化け文字が多い
        
        # PDFからよく出る文字化けパターン
        text.count('(cid:') > 5,  # PDFのCIDエラー
        
        # 同じ文字の異常な繰り返し
        any(text.count(char) / text_length > 0.3 for char in set(text) if char.isprintable()) if text_length > 10 else False,
    ]
    
    corruption_count = sum(corruption_indicators)
    
    # 複数の指標で文字化けと判定
    if corruption_count >= 2:
        return True
    
    # 特に強い指標の場合は単独でも文字化けと判定
    strong_indicators = [
        '\ufffd' in text,
        '��' in text,
        text.count('(cid:') > 5,
        len([char for char in text if ord(char) > 65535]) / text_length > 0.1 if text_length > 0 else False,
    ]
    
    return any(strong_indicators)

def split_ocr_text_into_sections(text: str, filename: str) -> list:
    """OCR結果のテキストを適切なセクションに分割する"""
    sections = []
    
    # ページ区切りで分割
    page_parts = text.split('--- Page ')
    
    for i, part in enumerate(page_parts):
        if not part.strip():
            continue
            
        # ページ番号を抽出
        lines = part.split('\n')
        if i == 0:
            # 最初の部分（ページ区切りの前の部分）
            section_name = "概要"
            content = part.strip()
        else:
            # ページ番号を抽出
            page_line = lines[0] if lines else ""
            page_num = page_line.split('---')[0].strip() if '---' in page_line else str(i)
            section_name = f"ページ {page_num}"
            content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
        
        if content:
            sections.append({
                'section': str(section_name),
                'content': str(content),
                'source': 'PDF',
                'file': filename,
                'url': None
            })
    
    # セクションが空の場合は全体を一つのセクションとして返す
    if not sections:
        sections.append({
            'section': "全体",
            'content': str(text),
            'source': 'PDF', 
            'file': filename,
            'url': None
        })
    
    return sections

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
        
        corrupted_pages = []  # 文字化けしたページを記録
        
        for i, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                # Ensure page_text is not None and convert to string if needed
                if page_text is not None:
                    page_text = ensure_string(page_text).replace('\x00', '') # 🧼 Remove NUL characters
                    
                    # ページごとに文字化けをチェック
                    if check_text_corruption(page_text):
                        print(f"ページ {i+1} で文字化けを検出: {page_text[:100]}...")
                        corrupted_pages.append(i)
                        # 文字化けページのデータはsectionsに保存しない
                    else:
                        section_name = f"ページ {i+1}"
                        sections[section_name] = page_text
                        all_text += page_text + "\n"
                        extracted_text += f"=== {section_name} ===\n{page_text}\n\n"
                else:
                    print(f"ページ {i+1} にテキストがありません")
                    corrupted_pages.append(i)  # テキストなしも文字化けとして扱う
                    # テキストなしページのデータはsectionsに保存しない
            except Exception as page_error:
                print(f"ページ {i+1} の処理中にエラー: {str(page_error)}")
                corrupted_pages.append(i)  # エラーも文字化けとして扱う
                # エラーページのデータはsectionsに保存しない
        
        # 初期データを作成（OCRが必要でない場合のみ）
        all_data = []
        
        # 文字化けページがない場合のみ、通常のテキスト処理を行う
        # ただし、all_text全体も文字化けチェックを通過する必要がある
        if len(corrupted_pages) == 0 and all_text and not check_text_corruption(all_text):
            # テキストをセクションに分割
            # 見出しパターン
            heading_pattern = r'^(?:\d+[\.\s]+|第\d+[章節]\s+|[\*\#]+\s+)?([A-Za-z\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]{2,}[：:、。])'
            
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
        else:
            print("文字化けまたは問題のあるページが検出されたため、通常のテキスト処理をスキップします")
            # 文字化けが検出された場合は、all_data、sections、all_textをクリアしてOCR処理を確実に実行させる
            all_data = []
            sections = {}
            all_text = ""
        
        # Check if we need to use OCR (no text, corrupted text, or corrupted pages)
        needs_ocr = not all_text or check_text_corruption(all_text) or len(corrupted_pages) > 0
        
        if needs_ocr:
            if not all_text and len(corrupted_pages) > 0:
                print(f"文字化けページ検出: {len(corrupted_pages)}/{len(pdf_reader.pages)} ページでOCRを使用します")
            elif not all_text:
                print("テキストが抽出できないため、OCRを使用します")
            else:
                print("抽出されたテキストが文字化けしているため、OCRを使用します")
                print(f"文字化けテキスト例: {all_text[:100]}...")
                
            try:
                print("Gemini OCRでPDF全体を処理中...")
                ocr_result = await ocr_pdf_to_text_from_bytes(contents)
                # Ensure all_text is a string
                ocr_text = ensure_string(ocr_result)
                print(f"OCRによるテキスト抽出完了: {len(ocr_text)} 文字")
                
                # 文字化けしたデータを完全にクリアして、OCR結果のみを保存
                all_data = []
                sections = {}
                all_text = ""
                extracted_text = f"=== ファイル: {filename} ===\n\n"
                
                if ocr_text and ocr_text.strip():
                    print("OCR結果でデータを完全に再構築中...")
                    # OCR結果を適切にセクション分けする
                    ocr_sections = split_ocr_text_into_sections(ocr_text, filename)
                    all_data = ocr_sections  # 文字化けデータは含めず、OCR結果のみ
                    
                    # OCR結果でセクションと抽出テキストを構築
                    for section in ocr_sections:
                        section_name = section['section']
                        section_content = section['content']
                        sections[section_name] = section_content
                        extracted_text += f"=== {section_name} ===\n{section_content}\n\n"
                    
                    # all_textもOCR結果で更新
                    all_text = ocr_text
                    
                    print(f"OCR結果保存完了: {len(all_data)} セクション")
                else:
                    print("OCR結果が空でした")
                    # OCRが失敗した場合の最小限のデータ
                    all_data = [{
                        'section': "OCR処理結果",
                        'content': "OCRでテキストを抽出できませんでした",
                        'source': 'PDF',
                        'file': filename,
                        'url': None
                    }]
                    sections = {"OCR処理結果": "OCRでテキストを抽出できませんでした"}
                    all_text = "OCRでテキストを抽出できませんでした"
                    extracted_text += "=== OCR処理結果 ===\nOCRでテキストを抽出できませんでした\n\n"
                    
            except Exception as ocr_error:
                print(f"OCRエラー: {str(ocr_error)}")
                # OCRエラーの場合も文字化けデータは含めない
                error_message = f"OCRエラー: {str(ocr_error)}"
                all_data = [{
                    'section': "OCRエラー",
                    'content': error_message,
                    'source': 'PDF',
                    'file': filename,
                    'url': None
                }]
                sections = {"OCRエラー": error_message}
                all_text = error_message
                extracted_text = f"=== ファイル: {filename} ===\n\n=== OCRエラー ===\n{error_message}\n\n"
            
            result_df = pd.DataFrame(all_data) if all_data else pd.DataFrame({
                'section': ["一般情報"],
                'content': [str(all_text or "")],  # Ensure content is a string
                'source': ['PDF'],
                'file': [filename],
                'url': [None]
            })
            # OCR処理の場合はextracted_textは既に構築済みなので追加しない
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