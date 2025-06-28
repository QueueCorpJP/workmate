"""
📊 Excel レコードベースデータクリーニング・構造化モジュール
1レコード（1行）を1つの意味のまとまりとして自然文に変換
RAG検索精度向上のための構造化データ専用処理
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

class ExcelDataCleanerRecordBased:
    """Excelデータを1レコード単位で自然文に変換するクラス"""
    
    def __init__(self):
        self.max_cell_length = 3000     # セル内容の最大文字数
        self.max_record_length = 8000   # 1レコードの最大文字数
        self.max_tokens_per_chunk = 400 # チャンクあたりの最大トークン数
        
        # 除外対象の無意味な値
        self.meaningless_values = {
            'nan', 'NaN', 'null', 'NULL', 'None', 'NONE', '',
            '#N/A', '#VALUE!', '#REF!', '#DIV/0!', '#NAME?', '#NUM!', '#NULL!',
            'naan', 'naaN', 'NAAN', 'NaT', '-', '－', '―', '—'
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
        
        # 一般的なカラム名のマッピング（自然文生成用）
        self.column_mappings = {
            # 会社・組織関連
            '会社名': '会社名',
            '企業名': '会社名',
            '法人名': '会社名',
            '組織名': '組織名',
            '団体名': '団体名',
            
            # 住所関連
            '住所': '住所',
            '所在地': '所在地',
            '設置先': '設置先',
            '設置場所': '設置場所',
            '設置先住所': '設置先住所',
            '本社住所': '本社住所',
            '支社住所': '支社住所',
            
            # 連絡先関連
            '電話番号': '電話番号',
            'TEL': '電話番号',
            'tel': '電話番号',
            'FAX': 'FAX番号',
            'fax': 'FAX番号',
            'メール': 'メールアドレス',
            'email': 'メールアドレス',
            'Email': 'メールアドレス',
            'E-mail': 'メールアドレス',
            
            # サービス関連
            'サービス': 'サービス',
            '契約サービス': '契約サービス',
            'プラン': 'プラン',
            '料金プラン': '料金プラン',
            '契約プラン': '契約プラン',
            
            # 日付関連
            '契約日': '契約日',
            '開始日': '開始日',
            '終了日': '終了日',
            '更新日': '更新日',
            
            # 担当者関連
            '担当者': '担当者',
            '責任者': '責任者',
            '連絡先担当者': '連絡先担当者',
            
            # その他
            '備考': '備考',
            'メモ': 'メモ',
            '注記': '注記',
            '状態': '状態',
            'ステータス': 'ステータス'
        }
    
    def clean_excel_data(self, content: bytes) -> List[Dict[str, Any]]:
        """
        Excelデータを1レコード単位で自然文に変換
        戻り値: レコードごとの構造化データのリスト
        """
        try:
            # XLSファイルかXLSXファイルかを判定
            if self._is_xls_file(content):
                logger.info("📊 XLSファイルとして処理開始（レコードベース）")
                return self._process_xls_file_record_based(content)
            else:
                logger.info("📊 XLSXファイルとして処理開始（レコードベース）")
                return self._process_xlsx_file_record_based(content)
                
        except Exception as e:
            logger.error(f"❌ Excel処理エラー（レコードベース）: {e}")
            # フォールバック処理
            try:
                logger.info("🔄 フォールバック処理開始（レコードベース）")
                return self._process_xlsx_file_record_based(content)
            except Exception as fallback_error:
                logger.error(f"❌ フォールバック処理も失敗（レコードベース）: {fallback_error}")
                raise Exception(f"Excelファイルの処理に失敗しました: {e}")
    
    def _is_xls_file(self, content: bytes) -> bool:
        """ファイルがXLS形式かどうかを判定"""
        try:
            # XLSファイルのマジックナンバーをチェック
            if content[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
                return True
            # xlrdで読み込み可能かテスト
            xlrd.open_workbook(file_contents=content)
            return True
        except:
            return False
    
    def _process_xls_file_record_based(self, content: bytes) -> List[Dict[str, Any]]:
        """XLSファイルをレコードベースで処理"""
        try:
            workbook = xlrd.open_workbook(file_contents=content)
            all_records = []
            
            for sheet_name in workbook.sheet_names():
                try:
                    logger.info(f"📊 XLSシート処理開始（レコードベース）: {sheet_name}")
                    
                    sheet = workbook.sheet_by_name(sheet_name)
                    df = self._xls_sheet_to_dataframe(sheet)
                    
                    if df is not None and not df.empty:
                        records = self._convert_dataframe_to_records(df, sheet_name)
                        all_records.extend(records)
                        logger.info(f"✅ シート {sheet_name}: {len(records)}レコード処理完了")
                    
                except Exception as sheet_error:
                    logger.warning(f"⚠️ XLSシート {sheet_name} 処理エラー: {sheet_error}")
                    continue
            
            logger.info(f"🎉 XLSファイル処理完了（レコードベース）: 総レコード数 {len(all_records)}")
            return all_records
            
        except Exception as e:
            logger.error(f"❌ XLSファイル処理エラー（レコードベース）: {e}")
            raise
    
    def _process_xlsx_file_record_based(self, content: bytes) -> List[Dict[str, Any]]:
        """XLSXファイルをレコードベースで処理"""
        try:
            excel_file = pd.ExcelFile(BytesIO(content))
            all_records = []
            
            for sheet_name in excel_file.sheet_names:
                try:
                    logger.info(f"📊 XLSXシート処理開始（レコードベース）: {sheet_name}")
                    
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    df = self._clean_dataframe_enhanced(df)
                    
                    if df is not None and not df.empty:
                        records = self._convert_dataframe_to_records(df, sheet_name)
                        all_records.extend(records)
                        logger.info(f"✅ シート {sheet_name}: {len(records)}レコード処理完了")
                    
                except Exception as sheet_error:
                    logger.warning(f"⚠️ XLSXシート {sheet_name} 処理エラー: {sheet_error}")
                    continue
            
            logger.info(f"🎉 XLSXファイル処理完了（レコードベース）: 総レコード数 {len(all_records)}")
            return all_records
            
        except Exception as e:
            logger.error(f"❌ XLSXファイル処理エラー（レコードベース）: {e}")
            raise
    
    def _xls_sheet_to_dataframe(self, sheet) -> Optional[pd.DataFrame]:
        """XLSシートをDataFrameに変換"""
        try:
            if sheet.nrows == 0:
                return None
            
            # データを2次元リストに変換
            data = []
            for row_idx in range(sheet.nrows):
                row_data = []
                for col_idx in range(sheet.ncols):
                    cell = sheet.cell(row_idx, col_idx)
                    
                    # セルタイプに応じて値を変換
                    if cell.ctype == xlrd.XL_CELL_EMPTY:
                        value = ''
                    elif cell.ctype == xlrd.XL_CELL_TEXT:
                        value = cell.value
                    elif cell.ctype == xlrd.XL_CELL_NUMBER:
                        value = cell.value
                    elif cell.ctype == xlrd.XL_CELL_DATE:
                        # 日付の処理
                        try:
                            date_tuple = xlrd.xldate_as_tuple(cell.value, sheet.book.datemode)
                            value = f"{date_tuple[0]}-{date_tuple[1]:02d}-{date_tuple[2]:02d}"
                        except:
                            value = cell.value
                    elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
                        value = bool(cell.value)
                    else:
                        value = str(cell.value)
                    
                    row_data.append(value)
                data.append(row_data)
            
            # DataFrameに変換
            if data:
                df = pd.DataFrame(data[1:], columns=data[0] if len(data) > 1 else None)
                return self._clean_dataframe_enhanced(df)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ XLSシート→DataFrame変換エラー: {e}")
            return None
    
    def _clean_dataframe_enhanced(self, df: pd.DataFrame) -> pd.DataFrame:
        """DataFrameをクリーニング（改良版）"""
        if df is None or df.empty:
            return df
        
        try:
            # 1. 完全に空の行・列を削除
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            if df.empty:
                return df
            
            # 2. セル内容をクリーニング
            for col in df.columns:
                df[col] = df[col].apply(self._clean_cell_content)
            
            # 3. 空白行を再度削除（クリーニング後）
            df = df[df.apply(lambda row: any(str(cell).strip() for cell in row if pd.notna(cell)), axis=1)]
            
            # 4. 意味のない行を除去
            df = df[df.apply(self._is_meaningful_row_enhanced, axis=1)]
            
            # 5. インデックスをリセット
            df = df.reset_index(drop=True)
            
            return df
            
        except Exception as e:
            logger.error(f"❌ DataFrame クリーニングエラー: {e}")
            return df
    
    def _clean_cell_content(self, cell_value) -> str:
        """セル内容をクリーニング"""
        if pd.isna(cell_value) or cell_value is None:
            return ''
        
        try:
            # 文字列に変換
            text = str(cell_value).strip()
            
            # 無意味な値をチェック
            if text.lower() in [v.lower() for v in self.meaningless_values]:
                return ''
            
            # 不要な記号を除去（重要な記号は保持）
            cleaned_text = ''
            for char in text:
                if char in self.unwanted_symbols:
                    continue
                elif char in self.important_symbols or char.isalnum() or char.isspace() or ord(char) > 127:
                    cleaned_text += char
                else:
                    cleaned_text += char
            
            # 制御文字を除去
            cleaned_text = ''.join(char for char in cleaned_text if unicodedata.category(char)[0] != 'C' or char in '\t\n\r')
            
            # 連続する空白を整理
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            
            # 最大文字数制限
            if len(cleaned_text) > self.max_cell_length:
                cleaned_text = cleaned_text[:self.max_cell_length] + '...'
            
            return cleaned_text
            
        except Exception as e:
            logger.warning(f"⚠️ セルクリーニングエラー: {e}")
            return str(cell_value) if cell_value is not None else ''
    
    def _is_meaningful_row_enhanced(self, row: pd.Series) -> bool:
        """行が意味のあるデータを含んでいるかチェック（改良版）"""
        meaningful_cells = 0
        
        for cell in row:
            if pd.notna(cell):
                cell_text = str(cell).strip()
                if cell_text and cell_text.lower() not in [v.lower() for v in self.meaningless_values]:
                    # 1文字以上で無意味な値でなければ意味があると判定
                    if len(cell_text) >= 1:
                        meaningful_cells += 1
        
        # 2つ以上の意味のあるセルがあれば有効な行とする
        return meaningful_cells >= 2
    
    def _convert_dataframe_to_records(self, df: pd.DataFrame, sheet_name: str) -> List[Dict[str, Any]]:
        """DataFrameを1レコード単位の自然文に変換"""
        if df is None or df.empty:
            return []
        
        records = []
        
        # カラム名を正規化
        normalized_columns = self._normalize_column_names(df.columns.tolist())
        
        for index, row in df.iterrows():
            try:
                # 1レコードを自然文に変換
                natural_text = self._convert_row_to_natural_text(row, normalized_columns, sheet_name, index)
                
                if natural_text and len(natural_text.strip()) > 10:  # 最小文字数チェック
                    # レコードが長すぎる場合は分割
                    if len(natural_text) > self.max_record_length:
                        chunks = self._split_long_record(natural_text, normalized_columns, sheet_name, index)
                        records.extend(chunks)
                    else:
                        record = {
                            'content': natural_text,
                            'source_sheet': sheet_name,
                            'record_index': index,
                            'record_type': 'single',
                            'token_estimate': self._estimate_tokens(natural_text)
                        }
                        records.append(record)
                
            except Exception as row_error:
                logger.warning(f"⚠️ 行 {index} 処理エラー: {row_error}")
                continue
        
        return records
    
    def _normalize_column_names(self, columns: List[str]) -> List[str]:
        """カラム名を正規化"""
        normalized = []
        
        for col in columns:
            col_str = str(col).strip()
            
            # マッピング辞書から対応する名前を取得
            normalized_name = self.column_mappings.get(col_str, col_str)
            normalized.append(normalized_name)
        
        return normalized
    
    def _convert_row_to_natural_text(self, row: pd.Series, normalized_columns: List[str], sheet_name: str, index: int) -> str:
        """1行のデータを自然文に変換"""
        try:
            text_parts = []
            
            # シート名を含める
            if sheet_name and sheet_name.strip():
                text_parts.append(f"【{sheet_name}】")
            
            # 各セルの内容を自然文形式で追加
            meaningful_data = []
            
            for i, (col_name, cell_value) in enumerate(zip(normalized_columns, row)):
                if pd.notna(cell_value):
                    cell_text = str(cell_value).strip()
                    if cell_text and cell_text.lower() not in [v.lower() for v in self.meaningless_values]:
                        # カラム名と値を組み合わせて自然文形式に
                        if col_name and str(col_name).strip():
                            meaningful_data.append(f"{col_name}は{cell_text}")
                        else:
                            meaningful_data.append(cell_text)
            
            if meaningful_data:
                # 自然文として結合
                if len(meaningful_data) == 1:
                    text_parts.append(meaningful_data[0])
                elif len(meaningful_data) == 2:
                    text_parts.append(f"{meaningful_data[0]}で、{meaningful_data[1]}です。")
                else:
                    # 複数の項目がある場合
                    main_parts = meaningful_data[:-1]
                    last_part = meaningful_data[-1]
                    text_parts.append(f"{'、'.join(main_parts)}で、{last_part}です。")
            
            result = " ".join(text_parts)
            
            # 文の終わりを整える
            if result and not result.endswith(('。', '.', '！', '？')):
                result += "。"
            
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ 自然文変換エラー (行 {index}): {e}")
            return ""
    
    def _split_long_record(self, text: str, normalized_columns: List[str], sheet_name: str, index: int) -> List[Dict[str, Any]]:
        """長いレコードを適切なサイズに分割"""
        chunks = []
        
        try:
            # 文単位で分割
            sentences = re.split(r'[。！？\.\!\?]\s*', text)
            
            current_chunk = ""
            chunk_index = 0
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # 文を追加した場合のトークン数を推定
                test_chunk = current_chunk + ("。" if current_chunk else "") + sentence
                estimated_tokens = self._estimate_tokens(test_chunk)
                
                if estimated_tokens > self.max_tokens_per_chunk and current_chunk:
                    # 現在のチャンクを保存
                    if current_chunk.strip():
                        chunk = {
                            'content': current_chunk.strip() + "。",
                            'source_sheet': sheet_name,
                            'record_index': index,
                            'record_type': 'split',
                            'chunk_index': chunk_index,
                            'token_estimate': self._estimate_tokens(current_chunk)
                        }
                        chunks.append(chunk)
                        chunk_index += 1
                    
                    current_chunk = sentence
                else:
                    current_chunk = test_chunk
            
            # 最後のチャンクを追加
            if current_chunk.strip():
                chunk = {
                    'content': current_chunk.strip() + ("。" if not current_chunk.endswith(('。', '.', '！', '？')) else ""),
                    'source_sheet': sheet_name,
                    'record_index': index,
                    'record_type': 'split',
                    'chunk_index': chunk_index,
                    'token_estimate': self._estimate_tokens(current_chunk)
                }
                chunks.append(chunk)
            
        except Exception as e:
            logger.warning(f"⚠️ レコード分割エラー: {e}")
            # エラーの場合は元のテキストをそのまま返す
            chunks = [{
                'content': text,
                'source_sheet': sheet_name,
                'record_index': index,
                'record_type': 'error',
                'token_estimate': self._estimate_tokens(text)
            }]
        
        return chunks
    
    def _estimate_tokens(self, text: str) -> int:
        """テキストのトークン数を推定"""
        if not text:
            return 0
        
        # 日本語: 1文字 ≈ 1.5トークン, 英語: 4文字 ≈ 1トークン
        japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text))
        other_chars = len(text) - japanese_chars
        estimated_tokens = int(japanese_chars * 1.5 + other_chars * 0.25)
        return estimated_tokens