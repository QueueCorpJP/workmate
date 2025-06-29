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
from typing import List, Optional, Tuple
from .ocr import ocr_pdf_to_text_from_bytes
from ..database import ensure_string
from .unnamed_column_handler import UnnamedColumnHandler

logger = logging.getLogger(__name__)

# 文字化け修復マッピング（日本語PDF特有の問題）
MOJIBAKE_MAPPING = {
    # PyPDF2でよく発生する文字化けパターン
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
    '縺ｾ': 'ま',
    '縺ｿ': 'み',
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
    '繝ａ': 'チ',
    '繝ｂ': 'ヂ',
    '繝ｃ': 'ッ',
    '繝ｄ': 'ヅ',
    '繝ｅ': 'テ',
    '繝ｆ': 'デ',
    '繝ｇ': 'ト',
    '繝ｈ': 'ド',
    '繝ｉ': 'ナ',
    '繝ｊ': 'ニ',
    '繝ｋ': 'ヌ',
    '繝ｌ': 'ネ',
    '繝ｍ': 'ノ',
    '繝ｮ': 'ハ',
    '繝ｯ': 'バ',
    '繝ｰ': 'パ',
    '繝ｱ': 'ヒ',
    '繝ｲ': 'ビ',
    '繝ｳ': 'ピ',
    '繝ｴ': 'フ',
    '繝ｵ': 'ブ',
    '繝ｶ': 'プ',
    '繝ｷ': 'ヘ',
    '繝ｸ': 'ベ',
    '繝ｹ': 'ペ',
    '繝ｺ': 'ホ',
    '繝ｻ': 'ボ',
    '繝ｼ': 'ポ',
    '繝ｽ': 'マ',
    '繝ｾ': 'ミ',
    '繝ｿ': 'ム',
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
    '繝ｪ繧ｹ繝医い繝': 'リストア',
    '繝舌ャ繧ｯ繧｢繝': 'バックアップ',
    '繝ｪ繧ｹ繝医い': 'リストア',
    '繝舌ャ繧ｯ繧｢繝': 'バックアップ',
    # 漢字の文字化けパターン
    '迺ｾ遶': '環境',
    '荳?蟋': '会社',
    '蜿ｯ閭ｽ': '可能',
    '蠢?隕': '必要',
    '險ｭ螳': '設定',
    '繝ｻ繝ｻ繝ｻ': '...',
    # CIDエラーパターン
    '(cid:': '',
    ')': '',
}

def fix_mojibake_text(text: str) -> str:
    """文字化けテキストを修復する"""
    if not text:
        return text
    
    fixed_text = text
    
    # 文字化けマッピングを適用
    for mojibake, correct in MOJIBAKE_MAPPING.items():
        fixed_text = fixed_text.replace(mojibake, correct)
    
    # CIDエラーパターンを除去
    fixed_text = re.sub(r'\(cid:\d+\)', '', fixed_text)
    
    # 連続する文字化け文字を除去
    fixed_text = re.sub(r'[縺繝繧]{3,}', '[文字化け]', fixed_text)
    
    # 置換文字を除去
    fixed_text = fixed_text.replace('\ufffd', '[文字化け]')
    fixed_text = fixed_text.replace('', '[文字化け]')
    
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

def extract_tables_from_text(text: str) -> List[pd.DataFrame]:
    """テキストからテーブルを抽出してDataFrameに変換"""
    tables = []
    try:
        # マークダウンテーブル形式を検出
        lines = text.split('\n')
        table_lines = []
        in_table = False
        
        for line in lines:
            line = line.strip()
            if '|' in line and len(line.split('|')) >= 3:
                # テーブル行の可能性
                table_lines.append(line)
                in_table = True
            elif in_table and not line:
                # 空行でテーブル終了
                if len(table_lines) >= 2:  # ヘッダー + 少なくとも1行のデータ
                    df = _parse_markdown_table(table_lines)
                    if df is not None and not df.empty:
                        tables.append(df)
                table_lines = []
                in_table = False
            elif in_table and '|' not in line:
                # テーブル以外の行でテーブル終了
                if len(table_lines) >= 2:
                    df = _parse_markdown_table(table_lines)
                    if df is not None and not df.empty:
                        tables.append(df)
                table_lines = []
                in_table = False
        
        # 最後のテーブルを処理
        if table_lines and len(table_lines) >= 2:
            df = _parse_markdown_table(table_lines)
            if df is not None and not df.empty:
                tables.append(df)
        
        # 改良された検出: 縦に並んだデータからテーブルを推測
        if not tables:
            tables.extend(_extract_tabular_data_from_lines(lines))
        
    except Exception as e:
        logger.warning(f"テーブル抽出エラー: {str(e)}")
    
    return tables

def _parse_markdown_table(table_lines: List[str]) -> Optional[pd.DataFrame]:
    """マークダウンテーブル形式の行をDataFrameに変換"""
    try:
        if len(table_lines) < 2:
            return None
        
        # ヘッダー行を抽出
        header_line = table_lines[0]
        headers = [cell.strip() for cell in header_line.split('|') if cell.strip()]
        
        # 区切り行をスキップ（---などが含まれる行）
        data_start = 1
        if len(table_lines) > 1 and re.search(r'[-:]+', table_lines[1]):
            data_start = 2
        
        # データ行を抽出
        data_rows = []
        for line in table_lines[data_start:]:
            cells = [cell.strip() for cell in line.split('|') if cell.strip() or True]
            # 空のセルも保持しつつ、行全体が空でないことを確認
            if any(cell.strip() for cell in cells):
                # ヘッダー数に合わせて行を調整
                while len(cells) < len(headers):
                    cells.append('')
                data_rows.append(cells[:len(headers)])
        
        if not data_rows:
            return None
        
        df = pd.DataFrame(data_rows, columns=headers)
        return df
        
    except Exception as e:
        logger.warning(f"マークダウンテーブル解析エラー: {str(e)}")
        return None

def _extract_tabular_data_from_lines(lines: List[str]) -> List[pd.DataFrame]:
    """行リストから表形式データを推測して抽出"""
    tables = []
    try:
        # 連続する行で同じパターンの区切り文字を持つ行を探す
        potential_tables = []
        current_table_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if len(current_table_lines) >= 3:  # 最低3行でテーブルとみなす
                    potential_tables.append(current_table_lines.copy())
                current_table_lines = []
                continue
            
            # タブ、複数スペース、コロンなどの区切り文字パターンを検出
            separators = ['\t', '  ', ':', ',', ';']
            found_separator = None
            max_splits = 0
            
            for sep in separators:
                splits = len(line.split(sep))
                if splits > max_splits and splits >= 2:
                    max_splits = splits
                    found_separator = sep
            
            if found_separator and max_splits >= 2:
                current_table_lines.append((line, found_separator, max_splits))
            else:
                if len(current_table_lines) >= 3:
                    potential_tables.append(current_table_lines.copy())
                current_table_lines = []
        
        # 最後のテーブルを処理
        if len(current_table_lines) >= 3:
            potential_tables.append(current_table_lines.copy())
        
        # 各候補をDataFrameに変換
        for table_lines in potential_tables:
            df = _convert_lines_to_dataframe(table_lines)
            if df is not None and not df.empty and len(df.columns) >= 2:
                tables.append(df)
    
    except Exception as e:
        logger.warning(f"表形式データ抽出エラー: {str(e)}")
    
    return tables

def _convert_lines_to_dataframe(table_lines: List[Tuple[str, str, int]]) -> Optional[pd.DataFrame]:
    """行リストからDataFrameを作成"""
    try:
        if len(table_lines) < 3:
            return None
        
        # 最も一般的な区切り文字を特定
        separator_counts = {}
        for _, sep, _ in table_lines:
            separator_counts[sep] = separator_counts.get(sep, 0) + 1
        
        most_common_sep = max(separator_counts, key=separator_counts.get)
        
        # 同じ区切り文字を使用する行のみを使用
        filtered_lines = []
        for line, sep, _ in table_lines:
            if sep == most_common_sep:
                filtered_lines.append(line)
        
        if len(filtered_lines) < 3:
            return None
        
        # データを分割
        data_rows = []
        for line in filtered_lines:
            cells = [cell.strip() for cell in line.split(most_common_sep)]
            data_rows.append(cells)
        
        # 最も多い列数を特定
        max_cols = max(len(row) for row in data_rows)
        if max_cols < 2:
            return None
        
        # 全ての行を同じ列数に調整
        for row in data_rows:
            while len(row) < max_cols:
                row.append('')
        
        # 最初の行をヘッダーとして使用
        headers = data_rows[0] if data_rows else []
        data = data_rows[1:] if len(data_rows) > 1 else []
        
        # ヘッダーが空の場合はデフォルト名を設定
        for i, header in enumerate(headers):
            if not header or header.isspace():
                headers[i] = f'列{i+1}'
        
        if not data:
            return None
        
        df = pd.DataFrame(data, columns=headers)
        return df
        
    except Exception as e:
        logger.warning(f"DataFrame変換エラー: {str(e)}")
        return None

def split_ocr_text_into_sections(text: str, filename: str) -> list:
    """OCR結果のテキストを適切なセクションに分割し、テーブルも処理する"""
    sections = []
    
    # まずテーブルを抽出
    extracted_tables = extract_tables_from_text(text)
    
    # テーブルが見つかった場合はUnnamedカラム修正を適用
    if extracted_tables:
        handler = UnnamedColumnHandler()
        
        for i, table_df in enumerate(extracted_tables):
            try:
                # テーブルのUnnamedカラム問題を修正
                fixed_df, modifications = handler.fix_dataframe(table_df, f"{filename}_table_{i+1}")
                
                if modifications:
                    logger.info(f"PDF テーブル {i+1} のUnnamedカラム修正: {', '.join(modifications)}")
                
                # 修正されたテーブルをセクションとして追加
                table_sections = handler.create_clean_sections(fixed_df, filename)
                for section in table_sections:
                    section['section'] = f"テーブル{i+1}_{section['section']}"
                    section['source'] = 'PDF Table'
                sections.extend(table_sections)
                
            except Exception as e:
                logger.warning(f"テーブル {i+1} の処理エラー: {str(e)}")
                # エラーの場合はテーブルの生データを追加
                sections.append({
                    'section': f"テーブル{i+1}（生データ）",
                    'content': table_df.to_string(),
                    'source': 'PDF Table',
                    'file': filename,
                    'url': None
                })
    
    # ページ区切りで通常のテキストを分割
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