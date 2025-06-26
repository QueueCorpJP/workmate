"""
PDFファイル処理モジュール（文字化け対応強化版）
PDFファイルの読み込みと処理を行います
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
from typing import List, Optional, Tuple
from .ocr import ocr_pdf_to_text_from_bytes
from ..database import ensure_string
from .unnamed_column_handler import UnnamedColumnHandler

logger = logging.getLogger(__name__)

# 文字化け修復マッピング（日本語PDF特有の問題）
MOJIBAKE_MAPPING = {
    # 完全な文字化けパターン（長いものから先に処理）
    '縺薙ｌ縺ｯ繝?繧ｹ繝医〒縺吶?': 'これはテストです',
    '繧ｳ繝ｳ繝斐Η繝ｼ繧ｿ繧ｷ繧ｹ繝ｃ繝?縺ｮ險ｭ螳?': 'コンピュータシステムの設定',
    '繝ｦ繝ｼ繧ｶ繝ｼ縺ｮ繝ｭ繧ｰ繧､繝ｳ縺ｨ繝代せ繝ｯ繝ｼ繝?': 'ユーザーのログインとパスワード',
    
    # 単語レベルの文字化けパターン
    '繧ｳ繝ｳ繝斐Η繝ｼ繧ｿ': 'コンピュータ',
    '繧ｷ繧ｹ繝ｃ繝': 'システム',
    '繝ｦ繝ｼ繧ｶ繝ｼ': 'ユーザー',
    '繝ｭ繧ｰ繧､繝ｳ': 'ログイン',
    '繝代せ繝ｯ繝ｼ繝': 'パスワード',
    '繝｡繝ｼ繝ｫ': 'メール',
    '繧｢繝峨Ξ繧ｹ': 'アドレス',
    '繝輔ぃ繧､繝ｫ': 'ファイル',
    '繝輔か繝ｫ繝': 'フォルダ',
    '繝ｩ繧､繧ｻ繝ｳ繧ｹ': 'ライセンス',
    '繧ｵ繝ｼ繝薙せ': 'サービス',
    '繧｢繝励Μ繧ｱ繝ｼ繧ｷ繝ｧ繝ｳ': 'アプリケーション',
    '繝ｭ繧ｰ': 'ログ',
    '繧ｨ繝ｩ繝ｼ': 'エラー',
    '繝ｪ繧ｹ繝': 'リスト',
    '繝舌ャ繧ｯ繧｢繝': 'バックアップ',
    '繝?繧ｹ繝': 'テスト',
    '險ｭ螳': '設定',
    
    # 個別文字の文字化けパターン
    '縺': 'い',
    '縺ゅ→': 'あと',
    '縺ｨ': 'と',
    '縺ｪ': 'な',
    '縺ｫ': 'に',
    '縺ｮ': 'の',
    '縺ｯ': 'は',
    '縺ｾ': 'ま',
    '縺ｿ': 'み',
    '縺ｧ': 'で',
    '縺ｩ': 'ど',
    '縺ｰ': 'ば',
    '縺ｱ': 'ぱ',
    '縺ｲ': 'ひ',
    '縺ｳ': 'び',
    '縺ｴ': 'ぴ',
    '縺ｵ': 'ふ',
    '縺ｶ': 'ぶ',
    '縺ｷ': 'ぷ',
    '縺ｸ': 'へ',
    '縺ｹ': 'べ',
    '縺ｺ': 'ぺ',
    '縺ｻ': 'ほ',
    '縺ｼ': 'ぼ',
    '縺ｽ': 'ぽ',
    '繧': 'ア',
    '繧ｦ': 'ウ',
    '繧ｨ': 'エ',
    '繧ｪ': 'オ',
    '繧ｫ': 'カ',
    '繧ｬ': 'ガ',
    '繧ｭ': 'キ',
    '繧ｮ': 'ギ',
    '繧ｯ': 'ク',
    '繧ｰ': 'グ',
    '繧ｱ': 'ケ',
    '繧ｲ': 'ゲ',
    '繧ｳ': 'コ',
    '繧ｴ': 'ゴ',
    '繧ｵ': 'サ',
    '繧ｶ': 'ザ',
    '繧ｷ': 'シ',
    '繧ｸ': 'ジ',
    '繧ｹ': 'ス',
    '繧ｺ': 'ズ',
    '繧ｻ': 'セ',
    '繧ｼ': 'ゼ',
    '繧ｽ': 'ソ',
    '繧ｾ': 'ゾ',
    '繧ｿ': 'タ',
    '繝': 'ダ',
    
    # 漢字の文字化けパターン
    '迺ｾ遶': '環境',
    '荳?蟋': '会社',
    '蜿ｯ閭ｽ': '可能',
    '蠢?隕': '必要',
    '繝ｻ繝ｻ繝ｻ': '...',
}

def fix_mojibake_text(text: str) -> str:
    """文字化けテキストを修復する"""
    if not text:
        return text
    
    fixed_text = text
    
    # 文字化けマッピングを適用（長いパターンから先に処理）
    # 辞書を長さでソートして、長いパターンから先に置換
    sorted_mapping = sorted(MOJIBAKE_MAPPING.items(), key=lambda x: len(x[0]), reverse=True)
    
    for mojibake, correct in sorted_mapping:
        if mojibake in fixed_text:
            fixed_text = fixed_text.replace(mojibake, correct)
    
    # CIDエラーパターンを除去
    fixed_text = re.sub(r'\(cid:\d+\)', '', fixed_text)
    
    # 連続する未修復の文字化け文字のみを処理（修復済みの正常な文字は触らない）
    fixed_text = re.sub(r'[縺繝繧]{3,}', '[文字化け]', fixed_text)
    
    # 置換文字を除去
    fixed_text = fixed_text.replace('\ufffd', '[文字化け]')
    # 空文字の置換は削除（これが問題の原因）
    # fixed_text = fixed_text.replace('', '[文字化け]')
    
    # 余分な空白を整理
    fixed_text = re.sub(r'\s+', ' ', fixed_text)
    fixed_text = re.sub(r'\n\s*\n\s*\n', '\n\n', fixed_text)
    
    return fixed_text.strip()

def check_text_corruption(text: str) -> bool:
    """テキストが文字化けしているかどうかを判定する（強化版）"""
    if not text or len(text.strip()) == 0:
        return True
    
    # 基本的な文字化け検出
    corruption_indicators = [
        # 文字化け文字の存在
        '縺' in text,
        '繝' in text,
        '繧' in text,
        '\ufffd' in text,
        '' in text,
        '(cid:' in text,
        
        # 文字化け文字の比率
        len(re.findall(r'[縺繝繧]', text)) / len(text) > 0.1 if len(text) > 0 else False,
        
        # 意味のある文字の比率が低い
        len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\w]', text)) / len(text) < 0.3 if len(text) > 0 else True,
        
        # 極端に短いテキスト
        len(text.strip()) < 10,
    ]
    
    corruption_count = sum(corruption_indicators)
    
    # 複数の指標で文字化けと判定
    if corruption_count >= 2:
        logger.info(f"PDF文字化け検出: {corruption_count}個の指標が該当")
        return True
    
    # 強い指標の場合は単独でも文字化けと判定
    strong_indicators = [
        '縺' in text and len(re.findall(r'縺', text)) > 5,
        '繝' in text and len(re.findall(r'繝', text)) > 5,
        '(cid:' in text and len(re.findall(r'\(cid:', text)) > 3,
        '\ufffd' in text,
    ]
    
    if any(strong_indicators):
        logger.info("PDF強い文字化け指標を検出")
        return True
    
    return False

async def process_pdf_with_gemini_enhanced(contents: bytes, filename: str):
    """Gemini生ファイル処理を使用してPDFから文字を抽出する（強化版）"""
    try:
        from ..config import setup_gemini
        
        logger.info(f"PDF文字抽出開始（Gemini強化版）: {filename}")
        
        # Geminiモデルをセットアップ
        model = setup_gemini()
        if not model:
            logger.error("Geminiモデルの初期化に失敗")
            return None
        
        # 生のPDFファイルを一時ファイルとして保存
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(contents)
            tmp_file_path = tmp_file.name
        
        # Gemini用プロンプト（PDF文字抽出特化・強化版）
        prompt = """
        このPDFファイルからテキストを正確に抽出してください。

        **重要な指示：**
        1. PDFファイルを直接解析し、すべてのテキストを正確に抽出してください
        2. 文字化け文字（「?」「縺」「繧」「繝」「(cid:」など）が見つかった場合は、文脈から推測して正しい日本語に復元してください
        3. PDFの構造（見出し、段落、表、リストなど）を正確に保持してください
        4. ページ番号や章構成があれば適切に識別してください
        5. 図表のキャプションや注釈も含めて抽出してください
        6. 表がある場合は、行と列の構造を保持してください
        7. 料金表や価格情報は特に正確に抽出してください

        **PDF特有の文字化けパターン復元例：**
        - (cid:XXX) → 対応する文字に復元
        - 縺ゅ→縺 → あと
        - 迺ｾ遶 → 環境  
        - 荳?蟋 → 会社
        - 繧ｳ繝ｳ繝斐Η繝ｼ繧ｿ → コンピュータ
        - 繧ｷ繧ｹ繝ｃ繝 → システム
        - 繝ｦ繝ｼ繧ｶ繝ｼ → ユーザー

        **出力形式：**
        元のPDF構造を保った形で、抽出されたテキストを出力してください。
        各ページや章節が分かるように見出しを付けてください。
        復元できない文字化けは [文字化け] と明記してください。
        
        **特に注意：**
        - 数字や価格は正確に抽出してください
        - 表の構造は崩さないでください
        - 日本語の文字化けは積極的に修復してください
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
                for page_num in range(min(len(doc), 20)):  # 最大20ページまで
                    try:
                        page = doc[page_num]
                        # ページを高解像度画像に変換
                        pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))  # 高解像度
                        img_data = pix.tobytes("png")
                        
                        # PILイメージとして読み込み
                        img = Image.open(io.BytesIO(img_data))
                        
                        # ページ専用のプロンプト
                        page_prompt = f"{prompt}\n\nこれはPDFの{page_num + 1}ページ目です。特に文字化けに注意して正確に抽出してください。"
                        
                        # Geminiで画像を解析
                        response = model.generate_content([page_prompt, img])
                        page_text = response.text if response.text else ""
                        
                        if page_text:
                            # 抽出されたテキストの文字化けを修復
                            fixed_page_text = fix_mojibake_text(page_text)
                            all_text += f"\n\n=== ページ {page_num + 1} ===\n{fixed_page_text}"
                        
                        logger.info(f"ページ {page_num + 1} の処理完了: {len(page_text)}文字")
                        
                        # API制限対策（同期関数内なので削除）
                        import time
                        time.sleep(1)
                        
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
                        'source': 'PDF (Gemini強化文字抽出)',
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
                'source': 'PDF (Gemini強化文字抽出)',
                'file': filename,
                'url': None
            })
        
        # データフレームが空の場合の対応
        if not all_data:
            all_data.append({
                'section': "抽出されたPDFテキスト",
                'content': ensure_string(extracted_text),
                'source': 'PDF (Gemini強化文字抽出)',
                'file': filename,
                'url': None
            })
            sections["抽出されたPDFテキスト"] = ensure_string(extracted_text)
        
        result_df = pd.DataFrame(all_data)
        
        # すべての列の値を文字列に変換
        for col in result_df.columns:
            result_df[col] = result_df[col].apply(ensure_string)
        
        # 完全なテキスト情報
        full_text = f"=== ファイル: {filename} (Gemini強化PDF文字抽出) ===\n\n"
        for section_name, content in sections.items():
            full_text += f"=== {section_name} ===\n{content}\n\n"
        
        logger.info(f"PDF文字抽出完了（Gemini強化版）: {len(result_df)} セクション")
        return result_df, sections, full_text
        
    except Exception as e:
        logger.error(f"GeminiPDF強化処理エラー: {str(e)}")
        return None

async def process_pdf_file_enhanced(contents, filename):
    """PDFファイルを処理してデータフレーム、セクション、テキストを返す（文字化け対応強化版）"""
    try:
        logger.info(f"PDF処理開始（強化版）: {filename}")
        
        # まずGemini強化文字抽出を試行（最も精度が高い）
        logger.info("Gemini強化文字抽出を最優先で実行")
        gemini_result = await process_pdf_with_gemini_enhanced(contents, filename)
        if gemini_result:
            logger.info("✅ Gemini強化文字抽出が成功しました")
            return gemini_result
        
        logger.warning("Gemini強化文字抽出失敗 - PyPDF2+修復処理にフォールバック")
        
        # BytesIOオブジェクトを作成
        pdf_file = BytesIO(contents)
        
        # PDFファイルを読み込む
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # テキストを抽出
        all_text = ""
        sections = {}
        extracted_text = f"=== ファイル: {filename} ===\n\n"
        
        corrupted_pages = []  # 文字化けしたページを記録
        fixed_pages = []      # 修復されたページを記録
        
        for i, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                # Ensure page_text is not None and convert to string if needed
                if page_text is not None:
                    page_text = ensure_string(page_text).replace('\x00', '') # 🧼 Remove NUL characters
                    
                    # ページごとに文字化けをチェック
                    if check_text_corruption(page_text):
                        logger.info(f"ページ {i+1} で文字化けを検出: {page_text[:100]}...")
                        corrupted_pages.append(i)
                        
                        # 文字化け修復を試行
                        fixed_text = fix_mojibake_text(page_text)
                        if fixed_text and not check_text_corruption(fixed_text):
                            logger.info(f"✅ ページ {i+1} の文字化けを修復しました")
                            section_name = f"ページ {i+1} (修復済み)"
                            sections[section_name] = fixed_text
                            all_text += fixed_text + "\n"
                            extracted_text += f"=== {section_name} ===\n{fixed_text}\n\n"
                            fixed_pages.append(i)
                        else:
                            logger.warning(f"❌ ページ {i+1} の文字化け修復に失敗")
                    else:
                        section_name = f"ページ {i+1}"
                        sections[section_name] = page_text
                        all_text += page_text + "\n"
                        extracted_text += f"=== {section_name} ===\n{page_text}\n\n"
                else:
                    logger.warning(f"ページ {i+1} にテキストがありません")
                    corrupted_pages.append(i)  # テキストなしも文字化けとして扱う
            except Exception as page_error:
                logger.error(f"ページ {i+1} の処理中にエラー: {str(page_error)}")
                corrupted_pages.append(i)  # エラーも文字化けとして扱う
        
        # 修復不可能なページが多い場合はOCR処理を試行
        unfixed_pages = len(corrupted_pages) - len(fixed_pages)
        if unfixed_pages > len(pdf_reader.pages) * 0.3:  # 30%以上のページで修復不可能な場合
            logger.info(f"多数のページで修復不可能な文字化け検出 ({unfixed_pages}/{len(pdf_reader.pages)}) - OCR処理を実行")
            
            try:
                ocr_text = await ocr_pdf_to_text_from_bytes(contents)
                
                if ocr_text:
                    # OCR結果の文字化けも修復
                    fixed_ocr_text = fix_mojibake_text(ocr_text)
                    
                    # OCR結果をセクションに分割
                    ocr_sections_list = []
                    
                    # ページ区切りで分割
                    page_parts = fixed_ocr_text.split('--- Page ')
                    
                    for i, part in enumerate(page_parts):
                        if not part.strip():
                            continue
                            
                        # ページ番号を抽出
                        lines = part.split('\n')
                        if i == 0:
                            section_name = "概要"
                            content = part.strip()
                        else:
                            page_line = lines[0] if lines else ""
                            page_num = page_line.split('---')[0].strip() if '---' in page_line else str(i)
                            section_name = f"ページ {page_num}"
                            content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""
                        
                        if content:
                            ocr_sections_list.append({
                                'section': str(section_name),
                                'content': str(content),
                                'source': 'PDF (OCR+修復)',
                                'file': filename,
                                'url': None
                            })
                    
                    # データフレームを作成
                    result_df = pd.DataFrame(ocr_sections_list) if ocr_sections_list else pd.DataFrame({
                        'section': ["OCR結果"],
                        'content': [ensure_string(fixed_ocr_text)],
                        'source': ['PDF (OCR+修復)'],
                        'file': [filename],
                        'url': [None]
                    })
                    
                    # セクション辞書を作成
                    ocr_sections = {item['section']: item['content'] for item in ocr_sections_list} if ocr_sections_list else {"OCR結果": ensure_string(fixed_ocr_text)}
                    
                    # 抽出テキストを作成
                    ocr_extracted_text = f"=== ファイル: {filename} (OCR+修復処理) ===\n\n"
                    for section_name, content in ocr_sections.items():
                        ocr_extracted_text += f"=== {section_name} ===\n{content}\n\n"
                    
                    logger.info("✅ OCR+修復処理が成功しました")
                    return result_df, ocr_sections, ocr_extracted_text
                else:
                    raise Exception("OCRからテキストを抽出できませんでした")
            except Exception as ocr_error:
                logger.error(f"OCR処理失敗: {str(ocr_error)}")
                # OCR失敗時は通常のテキスト抽出処理を続行
        
        # 通常のテキスト処理（PyPDF2結果を使用）
        all_data = []
        
        if all_text:
            # テキストをセクションに分割
            heading_pattern = r'^(?:\d+[\.\s]+|第\d+[章節]\s+|[\*\#]+\s+)?([A-Za-z\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]{2,}[：:、。])'
            
            current_section = "一般情報"
            current_content = []
            
            for line in all_text.split("\n"):
                line = str(line).strip()
                if not line:
                    continue
                
                # 見出しかどうかを判定
                if re.search(heading_pattern, line):
                    # 前のセクションを保存
                    if current_content:
                        content_text = "\n".join([ensure_string(item) for item in current_content])
                        all_data.append({
                            'section': str(current_section),
                            'content': content_text,
                            'source': 'PDF (修復済み)',
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
                content_text = "\n".join([ensure_string(item) for item in current_content])
                all_data.append({
                    'section': str(current_section),
                    'content': content_text,
                    'source': 'PDF (修復済み)',
                    'file': filename,
                    'url': None
                })
        
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
        
        logger.info(f"✅ PDF処理完了（強化版）: {len(result_df)} セクション, 修復ページ: {len(fixed_pages)}")
        return result_df, sections, extracted_text
        
    except Exception as e:
        logger.error(f"❌ PDF強化処理エラー: {str(e)}")
        logger.error(traceback.format_exc())
        
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