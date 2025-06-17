"""
PDFファイル処理モジュール
PDFファイルの読み込みと処理を行います（文字化け対応強化版）
"""
import pandas as pd
import PyPDF2
from io import BytesIO
import re
import traceback
import asyncio
import logging
import tempfile
import os
from .ocr import ocr_pdf_to_text_from_bytes
from ..database import ensure_string

logger = logging.getLogger(__name__)

def check_text_corruption(text: str) -> bool:
    """テキストが文字化けしているかどうかを判定する（強化版）"""
    if not text or len(text.strip()) == 0:
        return True
    
    # CSV処理の文字化け検出機能を利用
    from .csv_processor import detect_mojibake_in_text
    
    # 既存の検出結果
    legacy_corruption = _check_legacy_corruption(text)
    
    # CSV処理の高度な文字化け検出
    advanced_corruption = detect_mojibake_in_text(text)
    
    # どちらかで文字化けが検出された場合
    if legacy_corruption or advanced_corruption:
        logger.info(f"PDF文字化け検出: legacy={legacy_corruption}, advanced={advanced_corruption}")
        return True
    
    return False

def _check_legacy_corruption(text: str) -> bool:
    """従来のPDF文字化け検出ロジック"""
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
        
        # 文字化けが検出された場合のみGemini文字抽出を実行
        if len(corrupted_pages) > 0 or (all_text and check_text_corruption(all_text)):
            logger.info(f"PDF文字化け検出 (ページ: {corrupted_pages}) - Gemini文字抽出を実行: {filename}")
            
            # Gemini文字抽出を実行
            gemini_result = await process_pdf_with_gemini(contents, filename)
            if gemini_result:
                logger.info("Gemini文字抽出が成功しました")
                return gemini_result
            
            logger.warning("Gemini文字抽出失敗 - 古いOCR処理にフォールバック")
            
            # Gemini文字抽出が失敗した場合は古いOCR処理を試行
            try:
                print(f"文字化けを検出しました。OCRを使用してテキストを抽出します...")
                ocr_text = await ocr_pdf_to_text_from_bytes(contents)
                
                if ocr_text:
                    # OCR結果をセクションに分割
                    ocr_sections_list = split_ocr_text_into_sections(ocr_text, filename)
                    
                    # データフレームを作成
                    result_df = pd.DataFrame(ocr_sections_list) if ocr_sections_list else pd.DataFrame({
                        'section': ["OCR結果"],
                        'content': [ensure_string(ocr_text)],
                        'source': ['PDF (OCR)'],
                        'file': [filename],
                        'url': [None]
                    })
                    
                    # セクション辞書を作成
                    ocr_sections = {item['section']: item['content'] for item in ocr_sections_list} if ocr_sections_list else {"OCR結果": ensure_string(ocr_text)}
                    
                    # 抽出テキストを作成
                    ocr_extracted_text = f"=== ファイル: {filename} (OCR処理) ===\n\n"
                    for section_name, content in ocr_sections.items():
                        ocr_extracted_text += f"=== {section_name} ===\n{content}\n\n"
                    
                    return result_df, ocr_sections, ocr_extracted_text
                else:
                    raise Exception("OCRからテキストを抽出できませんでした")
            except Exception as ocr_error:
                logger.error(f"OCR処理失敗: {str(ocr_error)}")
                # OCR失敗時は通常のテキスト抽出処理を続行
                pass
        
        # Gemini処理が失敗した場合、通常のテキスト抽出を試行
        # 文字化けページがない場合のみ、通常のテキスト処理を行う
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
        
        # Gemini処理失敗後の最終フォールバック: 従来のテキスト抽出のみ 
        # データフレームを作成
        result_df = pd.DataFrame(all_data) if all_data else pd.DataFrame({
            'section': ["エラー"],
            'content': ["PDFからテキストを抽出できませんでした"],
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

async def process_pdf_with_gemini(contents: bytes, filename: str):
    """Gemini生ファイル処理を使用してPDFから文字を抽出する"""
    try:
        from ..config import setup_gemini
        
        logger.info(f"PDFファイル処理開始（Gemini文字抽出使用）: {filename}")
        
        # Geminiモデルをセットアップ
        model = setup_gemini()
        if not model:
            logger.error("Geminiモデルの初期化に失敗")
            return None
        
        # 生のPDFファイルを一時ファイルとして保存
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(contents)
            tmp_file_path = tmp_file.name
        
        # Gemini用プロンプト（PDF文字抽出特化）
        prompt = """
        このPDFファイルからテキストを正確に抽出してください。
        
        **重要な指示：**
        1. PDFファイルを直接解析し、すべてのテキストを正確に抽出してください
        2. 文字化け文字（「?」「縺」「繧」「讒」「(cid:」など）が見つかった場合は、文脈から推測して正しい日本語に復元してください
        3. PDFの構造（見出し、段落、表、リストなど）を正確に保持してください
        4. ページ番号や章構成があれば適切に識別してください
        5. 図表のキャプションや注釈も含めて抽出してください
        6. 表がある場合は、行と列の構造を保持してください

        **PDF特有の文字化けパターン復元例：**
        - (cid:XXX) → 対応する文字に復元
        - 縺ゅ→縺 → あと
        - 迺ｾ遶 → 環境  
        - 荳?蟋 → 会社
        - 繧ｳ繝ｳ繝斐Η繝ｼ繧ｿ → コンピュータ

        **出力形式：**
        元のPDF構造を保った形で、抽出されたテキストを出力してください。
        各ページや章節が分かるように見出しを付けてください。
        復元できない文字化けは [文字化け] と明記してください。
        """
        
        def sync_gemini_call():
            try:
                # PDFをページごとに画像に変換してGeminiで処理
                from PIL import Image
                import io
                import fitz  # PyMuPDF
                
                logger.info("PyMuPDFを使用してPDFを画像に変換")
                doc = fitz.open(tmp_file_path)
                all_text = ""
                
                # 各ページを画像として処理
                for page_num in range(min(len(doc), 10)):  # 最大10ページまで
                    try:
                        page = doc[page_num]
                        # ページを画像に変換
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 高解像度
                        img_data = pix.tobytes("png")
                        
                        # PILイメージとして読み込み
                        img = Image.open(io.BytesIO(img_data))
                        
                        # ページ専用のプロンプト
                        page_prompt = f"{prompt}\n\nこれはPDFの{page_num + 1}ページ目です。"
                        
                        # Geminiで画像を解析
                        response = model.generate_content([page_prompt, img])
                        page_text = response.text if response.text else ""
                        
                        if page_text:
                            all_text += f"\n\n=== ページ {page_num + 1} ===\n{page_text}"
                        
                        logger.info(f"ページ {page_num + 1} の処理完了: {len(page_text)}文字")
                        
                    except Exception as page_error:
                        logger.error(f"ページ {page_num + 1} の処理エラー: {str(page_error)}")
                        all_text += f"\n\n=== ページ {page_num + 1} (エラー) ===\n[ページ処理エラー: {str(page_error)}]"
                
                doc.close()
                return all_text if all_text else ""
                    
            except Exception as e:
                logger.error(f"Gemini PDF処理エラー: {str(e)}")
                return ""
            finally:
                # 一時ファイルを削除
                try:
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
                except:
                    pass
        
        extracted_text = await asyncio.to_thread(sync_gemini_call)
        
        if not extracted_text:
            logger.warning("Gemini文字抽出からテキストを取得できませんでした")
            return None
        
        logger.info(f"Gemini文字抽出結果（最初の500文字）: {extracted_text[:500]}...")
        
        # 抽出したテキストからDataFrameを作成
        sections = {}
        all_data = []
        
        # テキストをページや章節でセクション分割
        # ページパターンや見出しパターンを検出
        section_patterns = [
            r'^(?:ページ\s*\d+|Page\s*\d+|\d+\s*ページ)',  # ページ番号
            r'^(?:第\s*\d+\s*[章節]|Chapter\s*\d+|\d+[\.\s]*[章節])',  # 章節
            r'^(?:■|●|▲|◆|【[^】]*】|\d+[\.\)]\s*)',  # 見出し記号
        ]
        
        current_section = "復元されたPDFテキスト"
        current_content = []
        
        for line in extracted_text.split("\n"):
            line = ensure_string(line).strip()
            if not line:
                continue
            
            # セクション区切りかどうかを判定
            is_section_break = False
            for pattern in section_patterns:
                if re.search(pattern, line):
                    is_section_break = True
                    break
            
            if is_section_break:
                # 前のセクションを保存
                if current_content:
                    content_text = "\n".join([ensure_string(item) for item in current_content])
                    sections[ensure_string(current_section)] = content_text
                    all_data.append({
                        'section': ensure_string(current_section),
                        'content': content_text,
                        'source': 'PDF (Gemini文字抽出)',
                        'file': filename,
                        'url': None
                    })
                
                # 新しいセクションを開始
                current_section = ensure_string(line)
                current_content = []
            else:
                current_content.append(ensure_string(line))
        
        # 最後のセクションを保存
        if current_content:
            content_text = "\n".join([ensure_string(item) for item in current_content])
            sections[ensure_string(current_section)] = content_text
            all_data.append({
                'section': ensure_string(current_section),
                'content': content_text,
                'source': 'PDF (Gemini文字抽出)',
                'file': filename,
                'url': None
            })
        
        # データフレームが空の場合の対応
        if not all_data:
            all_data.append({
                'section': "抽出されたPDFテキスト",
                'content': ensure_string(extracted_text),
                'source': 'PDF (Gemini文字抽出)',
                'file': filename,
                'url': None
            })
            sections["抽出されたPDFテキスト"] = ensure_string(extracted_text)
        
        result_df = pd.DataFrame(all_data)
        
        # すべての列の値を文字列に変換
        for col in result_df.columns:
            result_df[col] = result_df[col].apply(ensure_string)
        
        # 完全なテキスト情報
        full_text = f"=== ファイル: {filename} (Gemini PDF文字抽出) ===\n\n"
        for section_name, content in sections.items():
            full_text += f"=== {section_name} ===\n{content}\n\n"
        
        logger.info(f"PDFファイル処理完了（Gemini文字抽出）: {len(result_df)} セクション")
        return result_df, sections, full_text
        
    except Exception as e:
        logger.error(f"GeminiPDFファイル処理エラー: {str(e)}")
        return None 