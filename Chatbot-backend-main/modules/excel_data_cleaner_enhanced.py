"""
📊 Excel データクリーニング・構造化モジュール（改良版）
XLSファイル対応、空白行・空白列除去、文字化け・記号除去を強化
データ損失を最小限に抑えつつ、不要なデータを適切に除去
"""

import pandas as pd
import numpy as np
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from io import BytesIO
import unicodedata
import xlrd  # XLSファイル対応

logger = logging.getLogger(__name__)

class ExcelDataCleanerEnhanced:
    """Excelデータのクリーニングと構造化を行うクラス（改良版）"""
    
    def __init__(self):
        self.max_cell_length = 3000     # セル内容の最大文字数
        
        # 除外対象の無意味な値
        self.meaningless_values = {
            'nan', 'NaN', 'null', 'NULL', 'None', 'NONE', '',
            '#N/A', '#VALUE!', '#REF!', '#DIV/0!', '#NAME?', '#NUM!', '#NULL!',
            'naan', 'naaN', 'NAAN', 'NaT'
        }
        
        # 除去対象の記号・文字化け文字
        self.unwanted_symbols = {
            '◯', '△', '×', '○', '●', '▲', '■', '□', '★', '☆',
            '※', '＊', '♪', '♫', '♬', '♭', '♯', '♮',
            '①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩',
            '㊤', '㊥', '㊦', '㊧', '㊨', '㊙', '㊚', '㊛', '㊜', '㊝',
            '〒', '〓', '〔', '〕', '〖', '〗', '〘', '〙', '〚', '〛'
        }
        
        # 保持すべき重要な記号
        self.important_symbols = {
            '@', '#', '$', '%', '&', '*', '+', '-', '=', '/', '\\',
            '(', ')', '[', ']', '{', '}', '<', '>', '|', '~', '^',
            '!', '?', '.', ',', ';', ':', '"', "'", '`'
        }
        
    def clean_excel_data(self, content: bytes) -> str:
        """
        Excelデータをクリーニングして構造化されたテキストに変換
        XLS/XLSX両対応、文字化け・記号除去強化版
        """
        try:
            # XLSファイルかXLSXファイルかを判定
            if self._is_xls_file(content):
                logger.info("📊 XLSファイルとして処理開始")
                return self._process_xls_file(content)
            else:
                logger.info("📊 XLSXファイルとして処理開始")
                return self._process_xlsx_file(content)
                
        except Exception as e:
            logger.error(f"❌ Excel処理エラー: {e}")
            # フォールバック処理
            try:
                logger.info("🔄 フォールバック処理開始")
                return self._process_xlsx_file(content)
            except Exception as fallback_error:
                logger.error(f"❌ フォールバック処理も失敗: {fallback_error}")
                raise Exception(f"Excelファイルの処理に失敗しました: {e}")
    
    def _is_xls_file(self, content: bytes) -> bool:
        """
        ファイルがXLS形式かどうかを判定
        """
        try:
            # XLSファイルのマジックナンバーをチェック
            if content[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
                return True
            # xlrdで読み込み可能かテスト
            xlrd.open_workbook(file_contents=content)
            return True
        except:
            return False
    
    def _process_xls_file(self, content: bytes) -> str:
        """
        XLSファイルを処理
        """
        try:
            workbook = xlrd.open_workbook(file_contents=content)
            cleaned_parts = []
            
            for sheet_name in workbook.sheet_names():
                try:
                    logger.info(f"📊 XLSシート処理開始: {sheet_name}")
                    
                    sheet = workbook.sheet_by_name(sheet_name)
                    
                    # XLSシートをDataFrameに変換
                    df = self._xls_sheet_to_dataframe(sheet)
                    
                    if df is None or df.empty:
                        logger.warning(f"⚠️ シート {sheet_name} の読み込みに失敗")
                        continue
                    
                    # データクリーニング
                    cleaned_df = self._clean_dataframe_enhanced(df)
                    
                    if cleaned_df.empty:
                        logger.warning(f"⚠️ シート {sheet_name} にクリーニング後のデータがありません")
                        continue
                    
                    # 構造化されたテキストに変換
                    structured_text = self._convert_to_structured_text_enhanced(cleaned_df, sheet_name)
                    
                    if structured_text.strip():
                        cleaned_parts.append(structured_text)
                        logger.info(f"✅ シート {sheet_name} 処理完了: {len(structured_text)} 文字")
                    
                except Exception as e:
                    logger.warning(f"⚠️ シート {sheet_name} 処理エラー: {e}")
                    continue
            
            if not cleaned_parts:
                logger.warning("⚠️ 処理可能なデータが見つかりませんでした")
                return "このExcelファイルには処理可能なデータが含まれていません。"
            
            result = "\n\n".join(cleaned_parts)
            logger.info(f"🎉 XLS処理完了: {len(cleaned_parts)}シート, 総文字数: {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"❌ XLS処理エラー: {e}")
            raise
    
    def _xls_sheet_to_dataframe(self, sheet) -> Optional[pd.DataFrame]:
        """
        XLSシートをDataFrameに変換
        """
        try:
            data = []
            for row_idx in range(sheet.nrows):
                row_data = []
                for col_idx in range(sheet.ncols):
                    cell = sheet.cell(row_idx, col_idx)
                    
                    # セルタイプに応じて値を取得
                    if cell.ctype == xlrd.XL_CELL_EMPTY:
                        row_data.append("")
                    elif cell.ctype == xlrd.XL_CELL_TEXT:
                        row_data.append(cell.value)
                    elif cell.ctype == xlrd.XL_CELL_NUMBER:
                        row_data.append(cell.value)
                    elif cell.ctype == xlrd.XL_CELL_DATE:
                        # 日付の処理
                        try:
                            date_tuple = xlrd.xldate_as_tuple(cell.value, sheet.book.datemode)
                            if date_tuple[:3] != (0, 0, 0):  # 有効な日付
                                row_data.append(f"{date_tuple[0]}-{date_tuple[1]:02d}-{date_tuple[2]:02d}")
                            else:
                                row_data.append(cell.value)
                        except:
                            row_data.append(cell.value)
                    elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
                        row_data.append(bool(cell.value))
                    elif cell.ctype == xlrd.XL_CELL_ERROR:
                        row_data.append("#ERROR!")
                    else:
                        row_data.append(str(cell.value))
                
                data.append(row_data)
            
            if not data:
                return None
            
            # DataFrameを作成
            df = pd.DataFrame(data)
            return df
            
        except Exception as e:
            logger.error(f"❌ XLSシート変換エラー: {e}")
            return None
    
    def _process_xlsx_file(self, content: bytes) -> str:
        """
        XLSXファイルを処理
        """
        try:
            excel_file = pd.ExcelFile(BytesIO(content))
            cleaned_parts = []
            
            for sheet_name in excel_file.sheet_names:
                try:
                    logger.info(f"📊 XLSXシート処理開始: {sheet_name}")
                    
                    # 複数の読み込み方法を試行
                    df = self._read_excel_sheet_robust(excel_file, sheet_name)
                    
                    if df is None or df.empty:
                        logger.warning(f"⚠️ シート {sheet_name} の読み込みに失敗")
                        continue
                    
                    # データクリーニング
                    cleaned_df = self._clean_dataframe_enhanced(df)
                    
                    if cleaned_df.empty:
                        logger.warning(f"⚠️ シート {sheet_name} にクリーニング後のデータがありません")
                        continue
                    
                    # 構造化されたテキストに変換
                    structured_text = self._convert_to_structured_text_enhanced(cleaned_df, sheet_name)
                    
                    if structured_text.strip():
                        cleaned_parts.append(structured_text)
                        logger.info(f"✅ シート {sheet_name} 処理完了: {len(structured_text)} 文字")
                    
                except Exception as e:
                    logger.warning(f"⚠️ シート {sheet_name} 処理エラー: {e}")
                    continue
            
            if not cleaned_parts:
                logger.warning("⚠️ 処理可能なデータが見つかりませんでした")
                return "このExcelファイルには処理可能なデータが含まれていません。"
            
            result = "\n\n".join(cleaned_parts)
            logger.info(f"🎉 XLSX処理完了: {len(cleaned_parts)}シート, 総文字数: {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"❌ XLSX処理エラー: {e}")
            raise
    
    def _read_excel_sheet_robust(self, excel_file, sheet_name: str) -> Optional[pd.DataFrame]:
        """
        Excelシートを堅牢に読み込む（複数の方法を試行）
        """
        read_methods = [
            # 方法1: ヘッダーなしで読み込み
            lambda: pd.read_excel(excel_file, sheet_name=sheet_name, header=None),
            # 方法2: 最初の行をヘッダーとして読み込み
            lambda: pd.read_excel(excel_file, sheet_name=sheet_name, header=0),
            # 方法3: 複数行をスキップして読み込み
            lambda: pd.read_excel(excel_file, sheet_name=sheet_name, header=None, skiprows=1),
            # 方法4: 文字列として全て読み込み
            lambda: pd.read_excel(excel_file, sheet_name=sheet_name, header=None, dtype=str),
            # 方法5: エンコーディングを指定して読み込み
            lambda: pd.read_excel(excel_file, sheet_name=sheet_name, header=None, encoding='utf-8'),
            lambda: pd.read_excel(excel_file, sheet_name=sheet_name, header=None, encoding='shift_jis'),
            lambda: pd.read_excel(excel_file, sheet_name=sheet_name, header=None, encoding='cp932')
        ]
        
        for i, method in enumerate(read_methods):
            try:
                df = method()
                if df is not None and not df.empty:
                    logger.info(f"📖 シート {sheet_name} 読み込み成功（方法{i+1}）")
                    return df
            except Exception as e:
                logger.debug(f"読み込み方法{i+1}失敗: {e}")
                continue
        
        logger.warning(f"⚠️ シート {sheet_name} の全ての読み込み方法が失敗")
        return None
    
    def _clean_dataframe_enhanced(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameをクリーニング（改良版）
        """
        # 1. 完全に空の行・列を削除
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        if df.empty:
            return df
        
        # 2. セル内容をクリーニング（改良版）
        for col in df.columns:
            df[col] = df[col].apply(self._clean_cell_content_enhanced)
        
        # 3. 空白行を再度削除（クリーニング後）
        df = df[df.apply(lambda row: any(str(cell).strip() for cell in row if pd.notna(cell)), axis=1)]
        
        # 4. 意味のない行を削除（改良版）
        df = df[df.apply(self._is_meaningful_row_enhanced, axis=1)]
        
        # 5. 重複行を削除（ただし、重要なデータは保持）
        df = self._remove_duplicates_smart(df)
        
        # 6. インデックスをリセット
        df = df.reset_index(drop=True)
        
        return df
    
    def _clean_cell_content_enhanced(self, cell_value) -> str:
        """
        セル内容をクリーニング（改良版）
        """
        if pd.isna(cell_value):
            return ""
        
        # 文字列に変換
        text = str(cell_value).strip()
        
        # 無意味な値をチェック
        if text.lower() in [v.lower() for v in self.meaningless_values]:
            return ""
        
        # 長すぎるセルは切り詰め
        if len(text) > self.max_cell_length:
            text = text[:self.max_cell_length] + "..."
        
        # Unicode正規化
        text = unicodedata.normalize('NFKC', text)
        
        # 文字化け・不要な記号を除去
        text = self._remove_unwanted_symbols(text)
        
        # 特殊文字の処理
        text = text.replace('\x00', '')  # NULL文字削除
        text = text.replace('\ufeff', '')  # BOM削除
        text = text.replace('\u200b', '')  # ゼロ幅スペース削除
        text = text.replace('\u200c', '')  # ゼロ幅非結合子削除
        text = text.replace('\u200d', '')  # ゼロ幅結合子削除
        text = text.replace('\ufffe', '')  # 不正なUnicode文字削除
        text = text.replace('\uffff', '')  # 不正なUnicode文字削除
        
        # 空白の整理
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()
    
    def _remove_unwanted_symbols(self, text: str) -> str:
        """
        不要な記号・文字化け文字を除去
        """
        # 不要な記号を除去
        for symbol in self.unwanted_symbols:
            text = text.replace(symbol, '')
        
        # 制御文字を除去（ただし改行・タブは保持）
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t\r')
        
        # 連続する特殊文字を整理
        text = re.sub(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>?/~`]{3,}', '', text)
        
        return text
    
    def _is_meaningful_row_enhanced(self, row: pd.Series) -> bool:
        """
        行が意味のあるデータを含んでいるかチェック（改良版）
        """
        meaningful_cells = 0
        total_content_length = 0
        
        for cell in row:
            if pd.notna(cell):
                cell_text = str(cell).strip()
                if cell_text and cell_text.lower() not in [v.lower() for v in self.meaningless_values]:
                    # 1文字以上で無意味な値でなければ意味があると判定
                    if len(cell_text) >= 1:
                        meaningful_cells += 1
                        total_content_length += len(cell_text)
        
        # 意味のあるセルが1個以上、または総文字数が1文字以上
        return meaningful_cells >= 1 or total_content_length >= 1
    
    def _remove_duplicates_smart(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        重複行をスマートに削除（重要なデータは保持）
        """
        # 完全に同一の行のみを削除
        df_deduplicated = df.drop_duplicates()
        
        # 削除された行数をログ出力
        removed_count = len(df) - len(df_deduplicated)
        if removed_count > 0:
            logger.info(f"🗑️ 重複行を{removed_count}行削除")
        
        return df_deduplicated
    
    def _convert_to_structured_text_enhanced(self, df: pd.DataFrame, sheet_name: str) -> str:
        """
        クリーニングされたDataFrameを構造化されたテキストに変換（改良版）
        """
        if df.empty:
            return ""
        
        text_parts = [f"=== シート: {sheet_name} ==="]
        
        # データの構造を分析
        structure_info = self._analyze_data_structure_enhanced(df)
        
        if structure_info["has_headers"]:
            # ヘッダーがある場合の処理
            text_parts.append(self._format_with_headers_enhanced(df, structure_info))
        else:
            # ヘッダーがない場合の処理
            text_parts.append(self._format_without_headers_enhanced(df))
        
        # 統計情報を追加
        stats = self._generate_data_statistics_enhanced(df)
        if stats:
            text_parts.append(f"\n【データ統計】\n{stats}")
        
        return "\n".join(text_parts)
    
    def _analyze_data_structure_enhanced(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        データの構造を分析（改良版）
        """
        structure = {
            "has_headers": False,
            "header_row": None,
            "data_types": {},
            "patterns": []
        }
        
        # 最初の数行をチェックしてヘッダーを探す
        for i in range(min(5, len(df))):
            row = df.iloc[i]
            if self._looks_like_header_enhanced(row):
                structure["has_headers"] = True
                structure["header_row"] = i
                break
        
        return structure
    
    def _looks_like_header_enhanced(self, row: pd.Series) -> bool:
        """
        行がヘッダーらしいかチェック（改良版）
        """
        non_null_count = row.notna().sum()
        if non_null_count < 1:
            return False
        
        # ヘッダーらしいキーワードをチェック（大幅拡張）
        header_keywords = [
            '名前', 'name', '会社', 'company', '住所', 'address', 
            '電話', 'phone', 'tel', '日付', 'date', 'id', 'no',
            '番号', '種類', 'type', '状態', 'status', '金額', 'amount',
            'ステータス', '顧客', '獲得', '物件', '契約', '書類',
            '発行', '請求', 'mail', '解約', '備考', '#', '項目',
            'プロバイダ', 'ISP', '案件', '一覧', '管理', '情報',
            '担当', '部署', '支店', '営業', '売上', '利益', '費用',
            '開始', '終了', '期間', '期限', '予定', '実績', '進捗',
            '顧客番号', '社名', '法人', '個人', '連絡先', 'メール',
            '郵便番号', '都道府県', '市区町村', '建物', 'ビル',
            '回線', '速度', '料金', 'プラン', 'コース', 'オプション',
            'SS', 'ISP', '申込', '工事', '開通', '設置', '撤去'
        ]
        
        text_content = ' '.join([str(cell).lower() for cell in row if pd.notna(cell)])
        
        for keyword in header_keywords:
            if keyword.lower() in text_content:
                return True
        
        # 数値が少なく、テキストが多い場合もヘッダーの可能性
        text_cells = 0
        numeric_cells = 0
        for cell in row:
            if pd.notna(cell):
                cell_str = str(cell).strip()
                if re.match(r'^-?\d+\.?\d*$', cell_str):
                    numeric_cells += 1
                else:
                    text_cells += 1
        
        # テキストが数値以上の場合はヘッダーの可能性
        return text_cells >= numeric_cells and text_cells >= 2
    
    def _format_with_headers_enhanced(self, df: pd.DataFrame, structure_info: Dict) -> str:
        """
        ヘッダーありの場合のフォーマット（改良版）
        """
        header_row = structure_info["header_row"]
        headers = df.iloc[header_row].tolist()
        data_rows = df.iloc[header_row + 1:]
        
        formatted_parts = []
        formatted_parts.append("【データ項目】")
        
        # ヘッダー情報
        valid_headers = []
        for i, header in enumerate(headers):
            if pd.notna(header):
                clean_header = str(header).strip()
                if clean_header:
                    valid_headers.append((i, clean_header))
                    formatted_parts.append(f"- {clean_header}")
                else:
                    valid_headers.append((i, f"列{i+1}"))
                    formatted_parts.append(f"- 列{i+1}")
        
        formatted_parts.append("\n【データ内容】")
        
        # データ行を処理
        for idx, row in data_rows.iterrows():
            row_data = []
            for col_idx, header_name in valid_headers:
                if col_idx < len(row):
                    cell_value = row.iloc[col_idx]
                    if pd.notna(cell_value):
                        clean_value = str(cell_value).strip()
                        # 無意味な値以外は保持
                        if clean_value and clean_value.lower() not in [v.lower() for v in self.meaningless_values]:
                            row_data.append(f"{header_name}: {clean_value}")
            
            if row_data:
                formatted_parts.append(f"• {' | '.join(row_data)}")
        
        return "\n".join(formatted_parts)
    
    def _format_without_headers_enhanced(self, df: pd.DataFrame) -> str:
        """
        ヘッダーなしの場合のフォーマット（改良版）
        """
        formatted_parts = []
        formatted_parts.append("【データ内容】")
        
        for idx, row in df.iterrows():
            row_data = []
            for col_idx, cell_value in enumerate(row):
                if pd.notna(cell_value):
                    clean_value = str(cell_value).strip()
                    # 無意味な値以外は保持
                    if clean_value and clean_value.lower() not in [v.lower() for v in self.meaningless_values]:
                        row_data.append(clean_value)
            
            if row_data:
                formatted_parts.append(f"行{idx + 1}: {' | '.join(row_data)}")
        
        return "\n".join(formatted_parts)
    
    def _generate_data_statistics_enhanced(self, df: pd.DataFrame) -> str:
        """
        データの統計情報を生成（改良版）
        """
        stats_parts = []
        
        # 基本統計
        stats_parts.append(f"総行数: {len(df)}")
        stats_parts.append(f"総列数: {len(df.columns)}")
        
        # 非空セル数
        non_empty_cells = 0
        meaningful_cells = 0
        total_cells = len(df) * len(df.columns)
        
        for col in df.columns:
            for cell in df[col]:
                if pd.notna(cell):
                    cell_str = str(cell).strip()
                    if cell_str:
                        non_empty_cells += 1
                        if cell_str.lower() not in [v.lower() for v in self.meaningless_values]:
                            meaningful_cells += 1
        
        fill_rate = (non_empty_cells / total_cells * 100) if total_cells > 0 else 0
        meaningful_rate = (meaningful_cells / total_cells * 100) if total_cells > 0 else 0
        
        stats_parts.append(f"データ充填率: {fill_rate:.1f}%")
        stats_parts.append(f"有意義データ率: {meaningful_rate:.1f}%")
        
        return " | ".join(stats_parts)