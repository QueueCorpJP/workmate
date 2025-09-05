"""
PDFファイル処理モジュール
PDFファイルの読み込みと処理を行います（文字化け対応強化版）
"""
import pandas as pd
import pypdf as PyPDF2  # Security fix: Using pypdf instead of PyPDF2
from io import BytesIO
import re
import traceback
import logging
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
    '繝ｂ': 'チ',
    '繝ｃ': 'ッ',
    '繝ｄ': 'ヅ',
    '繝ｅ': 'テ',
    '繝ｆ': 'デ',
    '繝ｧ': 'ト',
    '繝ｈ': 'ド',
    '繝ｉ': 'ナ',
    '繝ｊ': 'ニ',
    
    # 新しい文字化けパターン（ユーザー報告のもの含む）
    'جຊΞΠςϜ': 'マルチドライブ',
    'υϥΠϒʗ': 'ドライブ',
    'ϚϧνυϥΠϒ': 'マルチドライブ',
    'Ϟχλʔʗ': 'モニター',
    'ܕӷথ': '型番',
    'ඪ४౥ࡌιϑτ': '標準搭載ソフト',
    'MpDF': 'PDF',
    'PNF': 'HOME',
    'VTJOFTT': 'BUSINESS',
    'PP': 'アプリ',
    'VBSE': 'Guard',
    'PMp': 'Solo',
    'BOPOJNBHF': 'Canonimage',
    'BSFEFTLUPQ': 'WARE Desktop',
    '֎ܗੇ๏': '外形寸法',
    '࣭ྔ': '質量',
    'ʷ': 'mm',
    'ᶱ': '(mm)',
    'LH': 'kg',
    'όοςϦʔؚΉ': 'バッテリー含む',
    'εϖοΫ': 'スペック',
    'JOEPXT': 'Windows',
    'SPCJU': 'Pro bit',
    '16': 'CPU',
    'PSF': 'Core',
    'MUSB': 'Ultra',
    '16()[': 'UHzGHz',
    'ϝϞϦʗ': 'メモリー',
    '%%3': 'DDR',
    '(#': 'GB',
    'σΟεΫʗ': 'ディスク',
    '44%': 'SSD',
    
    # 追加の文字化けパターン（分解して詳細にマッピング）
    'جຊ': 'マルチ',
    'ΞΠ': 'ドライブ',
    'ςϜ': 'ドライブ',
    'υϥ': 'ドライ',
    'Πϒ': 'ブ',
    'ʗ%7%': 'ー DVD ',
    'Ϛϧν': 'マルチ',
    'Ϟχλ': 'モニター',
    'ʔʗ%': 'ー',
    ')ܕ': '型',
    'ӷথ': '番',
    'ඪ४': '標準',
    '౥ࡌ': '搭載',
    'ιϑτ': 'ソフト',
    '0GpDF': 'PDF',
    ')PNF': 'HOME',
    '#VTJOFTT': 'BUSINESS',
    'ʢ104': '(POS',
    '"൛ʣ': '版)',
    '"QQ': 'App',
    '(VBSE': 'Guard',
    '4PMP': 'Solo',
    '$BOPOJ': 'Canoni',
    'NBHF': 'mage',
    '8"3&': 'WARE',
    '%FTLUPQ': 'Desktop',
    '֎ܗ': '外形',
    'ੇ๏': '寸法',
    'ɾ': '・',
    '࣭': '質',
    'ྔ': '量',
    'ʢ8': '(W',
    'ʢ)': '(H',
    'ʢ%': '(D',
    '໿': '約',
    'όο': 'バッ',
    'ςϦ': 'テリ',
    'ʔؚ': 'ー含',
    'Ή': 'む',
    'ʣ˔': ')',
    'εϖ': 'スペ',
    'οΫ': 'ック',
    '04ʗ': 'OS:',
    '8JOEPXT': 'Windows',
    '1SP': 'Pro',
    'CJU': ' bit',
    '$16ʗ': 'CPU:',
    '$PSF': 'Core',
    '6MUSB': 'Ultra',
    '6()': 'GHz',
    'ϝϞ': 'メモ',
    'Ϧʗ': 'リー',
    '%%3': 'DDR',
    'σΟ': 'ディ',
    'εΫ': 'スク',
    '44%': 'SSD',
    
    # 記号文字化け（更新版）
    'ʗ': 'ー',
    'ʢ': '(',
    'ʣ': ')',
    '˔': '・',
    'ΞΠ': 'AI',
    'ιϑτ': 'ソフト',
    'ςϜ': 'ステム',
    'Ξϓ': 'アプリ',
    '%7%': 'DVD',
    '%)': ')',
    'ɾ': '・',
    'ᶱ': '(mm)',
}

# Unicode正規化マッピング（より包括的）
UNICODE_NORMALIZATION = {
    # 半角カタカナを全角に
    'ｱ': 'ア', 'ｲ': 'イ', 'ｳ': 'ウ', 'ｴ': 'エ', 'ｵ': 'オ',
    'ｶ': 'カ', 'ｷ': 'キ', 'ｸ': 'ク', 'ｹ': 'ケ', 'ｺ': 'コ',
    'ｻ': 'サ', 'ｼ': 'シ', 'ｽ': 'ス', 'ｾ': 'セ', 'ｿ': 'ソ',
    'ﾀ': 'タ', 'ﾁ': 'チ', 'ﾂ': 'ツ', 'ﾃ': 'テ', 'ﾄ': 'ト',
    'ﾅ': 'ナ', 'ﾆ': 'ニ', 'ﾇ': 'ヌ', 'ﾈ': 'ネ', 'ﾉ': 'ノ',
    'ﾊ': 'ハ', 'ﾋ': 'ヒ', 'ﾌ': 'フ', 'ﾍ': 'ヘ', 'ﾎ': 'ホ',
    'ﾏ': 'マ', 'ﾐ': 'ミ', 'ﾑ': 'ム', 'ﾒ': 'メ', 'ﾓ': 'モ',
    'ﾔ': 'ヤ', 'ﾕ': 'ユ', 'ﾖ': 'ヨ',
    'ﾗ': 'ラ', 'ﾘ': 'リ', 'ﾙ': 'ル', 'ﾚ': 'レ', 'ﾛ': 'ロ',
    'ﾜ': 'ワ', 'ｦ': 'ヲ', 'ﾝ': 'ン',
    'ｯ': 'ッ', 'ｬ': 'ャ', 'ｭ': 'ュ', 'ｮ': 'ョ',
    'ｰ': 'ー',
}

def fix_mojibake_text(text: str) -> str:
    """文字化けテキストを修復する（強化版）"""
    if not text:
        return text
    
    fixed_text = text
    
    # 🎯 ページマーカー削除（最優先）
    fixed_text = re.sub(r'=== ページ \d+ ===', '', fixed_text)
    fixed_text = re.sub(r'=== Page \d+ ===', '', fixed_text)
    fixed_text = re.sub(r'--- Page \d+ ---', '', fixed_text)
    fixed_text = re.sub(r'=== ファイル: .* ===', '', fixed_text)
    
    # 🎯 著作権情報とヘッダーフッターを削除
    fixed_text = re.sub(r'Copyright \d{4}-\d{4} © .* All Rights Reserved', '', fixed_text)
    fixed_text = re.sub(r'Company Secret', '', fixed_text)
    fixed_text = re.sub(r'VER\d{6} -\d{2}-\d{2}', '', fixed_text)
    
    # 🎯 全角ピリオドを半角に正規化
    fixed_text = fixed_text.replace('。', '.')
    fixed_text = fixed_text.replace('．', '.')
    fixed_text = fixed_text.replace('，', ',')
    
    # 🎯 会社名の正規化
    fixed_text = fixed_text.replace('No。1', 'No.1')
    fixed_text = fixed_text.replace('CO。,LTD。', 'CO.,LTD.')
    
    # 🎯 Unicode正規化を適用
    for half_char, full_char in UNICODE_NORMALIZATION.items():
        fixed_text = fixed_text.replace(half_char, full_char)
    
    # 重度の文字化けがある場合のみ修復を適用
    if check_text_corruption(fixed_text):
        # 文字化けマッピングを適用（長いものから順に処理）
        sorted_mapping = sorted(MOJIBAKE_MAPPING.items(), key=lambda x: len(x[0]), reverse=True)
        for mojibake, correct in sorted_mapping:
            fixed_text = fixed_text.replace(mojibake, correct)
        
        # CIDエラーパターンを除去
        fixed_text = re.sub(r'\(cid:\d+\)', '', fixed_text)
        
        # 連続する文字化け文字を除去（実際の文字化け文字のみ）
        fixed_text = re.sub(r'[縺繝繧]{3,}', '[文字化け]', fixed_text)
        
        # 置換文字を処理
        fixed_text = fixed_text.replace('\ufffd', '') # 完全に削除
    
    # 🎯 余分な空白を整理（強化版）
    fixed_text = re.sub(r'\s+', ' ', fixed_text)
    fixed_text = re.sub(r'\n\s*\n', '\n\n', fixed_text)  # 余分な改行を削除
    fixed_text = fixed_text.strip()
    
    return fixed_text

def check_text_corruption(text: str) -> bool:
    """テキストに文字化けが含まれているかチェック（強化版）"""
    if not text or len(text) < 10:
        return False
    
    # 文字化けパターンの検出（更新版）
    corruption_patterns = [
        # 従来の文字化けパターン
        r'[縺繝繧]{2,}',  # 連続する文字化け文字
        r'\(cid:\d+\)',   # CIDエラー
        r'[\ufffd]+',     # 置換文字
        
        # 新しい文字化けパターン
        r'[جຊ]{1,}',     # アラビア文字などの混入
        r'[ΞΠςϜυϥ]{2,}', # ギリシャ文字の混入
        r'[ʗʢʣ˔]{1,}',  # 特殊記号の混入
        r'[࣭ܕ]{1,}',     # 他言語文字の混入
        
        # エンコーディング破損パターン
        r'[A-Z]{4,}[A-Z]{4,}', # 連続する大文字（VTJOFTT等）
        r'%%\d+',        # %% + 数字パターン
        r'\d+\(\)\[',     # 数字 + () + [パターン
    ]
    
    # パターンマッチングによる文字化け検出
    corruption_count = 0
    for pattern in corruption_patterns:
        matches = re.findall(pattern, text)
        corruption_count += len(matches)
    
    # 文字化け文字の割合を計算
    total_chars = len(text)
    corruption_ratio = corruption_count / total_chars if total_chars > 0 else 0
    
    # 文字化けと判定する条件
    is_corrupted = (
        corruption_ratio > 0.05 or  # 5%以上が文字化け文字（敏感に）
        corruption_count > 3 or     # 3個以上の文字化けパターン（敏感に）
        '縺' in text or           # 確実な文字化け文字
        '繧' in text or
        '繝' in text or
        'جຊ' in text or          # 新パターン
        'ΞΠςϜ' in text or
        'ϚϧνυϥΠϒ' in text or
        'ܕӷথ' in text or
        'جຊΞΠςϜ' in text or     # 報告されたパターン
        'υϥΠϒʗ%7%' in text or
        'Ϟχλʔʗ%' in text or
        'ඪ४౥ࡌιϑτ' in text or
        'VTJOFTT' in text or      # 英語の文字化け
        'JOEPXT' in text or
        '#VTJOFTT' in text or
        '8JOEPXT' in text
    )
    
    if is_corrupted:
        print(f"文字化け検出: 文字化け率 {corruption_ratio:.2%}, パターン数 {corruption_count}")
    
    return is_corrupted

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
    """PDFファイルを処理してデータフレーム、セクション、テキストを返す（Gemini 2.5 Flash OCR完璧版）"""
    try:
        # まずGemini 2.5 Flash OCRを試行（最高品質）
        logger.info(f"🚀 Gemini 2.5 Flash OCR優先でPDF処理開始: {filename}")
        
        try:
            # Gemini 2.5 Flash OCRを使用してPDF処理
            from .gemini_flash_ocr import ocr_pdf_with_gemini_flash
            
            logger.info(f"🔄 Gemini 2.5 Flash OCRでテキスト抽出中: {filename}")
            ocr_text = await ocr_pdf_with_gemini_flash(contents)
            
            if ocr_text and ocr_text.strip() and not ocr_text.startswith("OCR処理エラー"):
                # OCR結果をセクション化
                sections = {}
                all_data = []
                full_text = f"=== ファイル: {filename} (Gemini 2.5 Flash OCR) ===\n\n"
                
                # ページごとにセクション分割
                pages = ocr_text.split("--- ページ")
                for i, page_content in enumerate(pages):
                    if not page_content.strip():
                        continue
                    
                    # ページ番号を抽出
                    lines = page_content.strip().split('\n')
                    if lines and lines[0].strip().endswith("---"):
                        page_num_line = lines[0].replace("---", "").strip()
                        page_content_lines = lines[1:]
                    else:
                        page_num_line = f"ページ {i + 1}"
                        page_content_lines = lines
                    
                    page_text = '\n'.join(page_content_lines).strip()
                    
                    if page_text:
                        section_name = page_num_line
                        sections[section_name] = page_text
                        all_data.append({
                            'section': section_name,
                            'content': page_text,
                            'source': 'PDF (Gemini 2.5 Flash OCR)',
                            'file': filename,
                            'url': None
                        })
                        
                        full_text += f"=== {section_name} ===\n{page_text}\n\n"
                
                if all_data:
                    # DataFrame作成
                    import pandas as pd
                    df = pd.DataFrame(all_data)
                    for col in df.columns:
                        df[col] = df[col].apply(ensure_string)
                    
                    logger.info(f"✅ Gemini 2.5 Flash OCRで正常に処理完了: {filename} ({len(all_data)} セクション)")
                    return df, sections, full_text
                else:
                    logger.warning(f"⚠️ Gemini 2.5 Flash OCRでセクションを作成できませんでした: {filename}")
                    raise Exception("Gemini Flash OCR section processing failed")
            else:
                logger.warning(f"⚠️ Gemini 2.5 Flash OCRで処理できませんでした: {filename}")
                raise Exception("Gemini Flash OCR processing failed")
                
        except Exception as ocr_error:
            logger.warning(f"⚠️ Gemini 2.5 Flash OCR処理エラー: {ocr_error}")
            logger.info(f"🔄 PyMuPDFフォールバックを使用: {filename}")
            
            # PyMuPDFフォールバックでの処理
            try:
                result = await process_pdf_with_pymupdf(contents, filename)
                if result is not None:
                    df, sections, extracted_text = result
                    logger.info(f"✅ PyMuPDFフォールバックで正常に処理完了: {filename}")
                    return df, sections, extracted_text
                else:
                    logger.warning(f"⚠️ PyMuPDFで処理できませんでした: {filename}")
                    raise Exception("PyMuPDF processing failed")
            except Exception as pymupdf_error:
                logger.warning(f"⚠️ PyMuPDF処理エラー: {pymupdf_error}")
                logger.info(f"🔄 PyPDF2最終フォールバックを使用: {filename}")
                
                # PyPDF2最終フォールバックでの処理
                return await _process_pdf_with_pypdf2_fallback(contents, filename)
            
    except Exception as e:
        print(f"PDFファイル処理エラー: {e}")
        
        # エラー時の空のDataFrame
        import pandas as pd
        empty_df = pd.DataFrame(columns=['section', 'content', 'source', 'file', 'url'])
        empty_sections = {"エラー": f"PDFファイル処理中にエラーが発生しました: {str(e)}"}
        error_text = f"=== ファイル: {filename} ===\n\n=== エラー ===\nPDFファイル処理中にエラーが発生しました: {str(e)}\n\n"
        
        return empty_df, empty_sections, error_text

async def _process_pdf_with_pypdf2_fallback(contents, filename):
    """PyPDF2を使用したフォールバック処理"""
    # BytesIOオブジェクトを作成
    pdf_file = BytesIO(contents)
    
    # PDFファイルを読み込む
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    
    # テキストを抽出
    all_text = ""
    sections = {}
    extracted_text = f"=== ファイル: {filename} (PyPDF2フォールバック) ===\n\n"
    
    for i, page in enumerate(pdf_reader.pages):
        try:
            # 強化されたテキスト抽出を使用
            page_text = extract_text_with_encoding_fallback(page)
            
            # Ensure page_text is not None and convert to string if needed
            if page_text is not None:
                page_text = ensure_string(page_text).replace('\x00', '') # 🧼 Remove NUL characters
                
                # 文字化け修正を適用
                fixed_text = fix_mojibake_text(page_text)
                
                if fixed_text.strip():
                    section_name = f"ページ {i+1}"
                    sections[section_name] = fixed_text
                    all_text += fixed_text + "\n"
                    extracted_text += f"{fixed_text}\n\n"
                else:
                    logger.debug(f"ページ {i+1} でテキストが抽出できませんでした")
            else:
                logger.debug(f"ページ {i+1} でテキスト抽出結果がNullでした")
                
        except Exception as page_error:
            logger.warning(f"ページ {i+1} の処理エラー: {page_error}")
            continue
    
    # DataFrameを作成
    import pandas as pd
    data_list = []
    for section_name, content in sections.items():
        data_list.append({
            'section': section_name,
            'content': content,
            'source': 'PDF (PyPDF2)',
            'file': filename,
            'url': None
        })
    
    df = pd.DataFrame(data_list) if data_list else pd.DataFrame(columns=['section', 'content', 'source', 'file', 'url'])
    
    # 各列を文字列として確保
    for col in df.columns:
        df[col] = df[col].apply(ensure_string)
    
    logger.info(f"PyPDF2フォールバック処理完了: {filename} ({len(sections)} セクション)")
    return df, sections, extracted_text

async def process_pdf_with_pymupdf(contents: bytes, filename: str):
    """PyMuPDF を用いて PDF から直接テキストを抽出する

    Gemini の OCR を使用せず、PDF 内のテキストレイヤーをそのまま取得します。
    文字化け修正も適用し、ページ単位でセクション化して DataFrame を返します。
    """
    try:
        try:
            import fitz  # PyMuPDF
        except ImportError:
            error_msg = """PyMuPDF (fitz) が利用できません。
            
PDFを適切に処理するために、PyMuPDFをインストールしてください:

pip install PyMuPDF

PyMuPDFはPopplerに依存しない高性能なPDF処理ライブラリです。
インストール後、アプリケーションを再起動してください。

現在はPyPDF2フォールバックを使用します。"""
            
            logger.warning(error_msg)
            return None

        logger.info(f"PDFファイル処理開始（PyMuPDFテキスト抽出使用）: {filename}")

        # PyMuPDF でバイト列を直接開く
        with fitz.open(stream=contents, filetype="pdf") as doc:
            sections = {}
            all_data = []
            full_text = f"=== ファイル: {filename} (PyMuPDF 抽出) ===\n\n"

            for page_num, page in enumerate(doc, start=1):
                try:
                    # テキスト抽出。layout 選択は "text" でシンプルに取得
                    page_text = page.get_text("text") or ""

                    # 文字化け修正を試みる
                    fixed_text = fix_mojibake_text(page_text)

                    if not fixed_text.strip():
                        # 空または修正後も空の場合はスキップ
                        logger.debug(f"ページ {page_num} で抽出テキストが空でした")
                        continue

                    section_name = f"ページ {page_num}"
                    sections[section_name] = fixed_text
                    all_data.append({
                        "section": section_name,
                        "content": fixed_text,
                        "source": "PDF (PyMuPDF)",
                        "file": filename,
                        "url": None,
                    })

                    full_text += f"=== {section_name} ===\n{fixed_text}\n\n"
                except Exception as page_error:
                    logger.warning(f"ページ {page_num} の PyMuPDF 抽出中にエラー: {page_error}")
                    continue

        if not all_data:
            logger.warning("PyMuPDF で有効なテキストを抽出できませんでした")
            return None

        # DataFrame 生成
        import pandas as pd
        result_df = pd.DataFrame(all_data)
        for col in result_df.columns:
            result_df[col] = result_df[col].apply(ensure_string)

        logger.info(f"PDFファイル処理完了（PyMuPDF 抽出）: {len(result_df)} セクション")
        return result_df, sections, full_text

    except Exception as e:
        logger.error(f"PyMuPDF PDFファイル処理エラー: {e}")
        return None 

def extract_text_with_encoding_fallback(page) -> str:
    """複数のエンコーディングでテキスト抽出を試行"""
    encodings_to_try = ['utf-8', 'cp932', 'shift_jis', 'euc-jp', 'iso-2022-jp']
    
    # まず標準的な抽出を試行
    try:
        text = page.extract_text()
        if text and not check_text_corruption(text):
            return fix_mojibake_text(text)
    except Exception as e:
        print(f"標準抽出エラー: {e}")
    
    # 文字化けまたはエラーの場合、複数エンコーディングを試行
    for encoding in encodings_to_try:
        try:
            # PyPDF2の内部処理でエンコーディングを強制
            text = page.extract_text(visitor_text=lambda text, cm, tm, fontDict, fontSize: text)
            if text:
                # エンコーディング変換を試行
                try:
                    if isinstance(text, bytes):
                        text = text.decode(encoding, errors='ignore')
                    elif isinstance(text, str):
                        # 一度バイト化してから再デコード
                        text = text.encode('latin1', errors='ignore').decode(encoding, errors='ignore')
                except Exception:
                    continue
                
                # 修復処理を適用
                fixed_text = fix_mojibake_text(text)
                if fixed_text and not check_text_corruption(fixed_text):
                    print(f"エンコーディング {encoding} で修復成功")
                    return fixed_text
        except Exception as e:
            print(f"エンコーディング {encoding} で抽出エラー: {e}")
            continue
    
    # すべて失敗した場合は標準抽出結果を修復して返す
    try:
        text = page.extract_text() or ""
        return fix_mojibake_text(text)
    except Exception:
        return "[テキスト抽出失敗]" 