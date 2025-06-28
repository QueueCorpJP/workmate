"""
📊 Excel データクリーニング・構造化モジュール（修正版）
乱雑なExcelデータを構造化し、質問応答可能な形式に変換
データ損失を最小限に抑える改良版
"""

import pandas as pd
import numpy as np
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from io import BytesIO
import unicodedata

logger = logging.getLogger(__name__)

class ExcelDataCleanerFixed:
    """Excelデータのクリーニングと構造化を行うクラス（改良版）"""
    
    def __init__(self):
        self.min_meaningful_length = 1  # 最小文字数を緩和（1文字以上）
        self.max_cell_length = 2000     # セル内容の最大文字数を増加
        
    def clean_excel_data(self, content: bytes) -> str:
        """
        乱雑なExcelデータをクリーニングして構造化されたテキストに変換
        データ損失を最小限に抑える改良版
        """
        try:
            excel_file = pd.ExcelFile(BytesIO(content))
            cleaned_parts = []
            
            for sheet_name in excel_file.sheet_names:
                try:
                    logger.info(f"📊 シート処理開始: {sheet_name}")
                    
                    # 複数の読み込み方法を試行
                    df = self._read_excel_sheet_robust(excel_file, sheet_name)
                    
                    if df is None or df.empty:
                        logger.warning(f"⚠️ シート {sheet_name} の読み込みに失敗")
                        continue
                    
                    # データクリーニング（緩和版）
                    cleaned_df = self._clean_dataframe_gentle(df)
                    
                    if cleaned_df.empty:
                        logger.warning(f"⚠️ シート {sheet_name} にクリーニング後のデータがありません")
                        continue
                    
                    # 構造化されたテキストに変換（改良版）
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
            logger.info(f"🎉 Excel処理完了: {len(cleaned_parts)}シート, 総文字数: {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Excel処理エラー: {e}")
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
            lambda: pd.read_excel(excel_file, sheet_name=sheet_name, header=None, dtype=str)
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
    
    def _clean_dataframe_gentle(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameをクリーニング（緩和版 - データ損失を最小限に）
        """
        # 1. 完全に空の行・列のみを削除
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        if df.empty:
            return df
        
        # 2. セル内容をクリーニング（緩和版）
        for col in df.columns:
            df[col] = df[col].apply(self._clean_cell_content_gentle)
        
        # 3. 意味のない行を削除（基準を大幅に緩和）
        df = df[df.apply(self._is_meaningful_row_gentle, axis=1)]
        
        # 4. 重複行を削除（ただし、類似度の高い行は保持）
        df = self._remove_exact_duplicates_only(df)
        
        # 5. インデックスをリセット
        df = df.reset_index(drop=True)
        
        return df
    
    def _clean_cell_content_gentle(self, cell_value) -> str:
        """
        セル内容をクリーニング（緩和版）
        """
        if pd.isna(cell_value):
            return ""
        
        # 文字列に変換
        text = str(cell_value).strip()
        
        # 長すぎるセルは切り詰め（上限を増加）
        if len(text) > self.max_cell_length:
            text = text[:self.max_cell_length] + "..."
        
        # Unicode正規化
        text = unicodedata.normalize('NFKC', text)
        
        # 不要な空白・改行を整理（より緩和）
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        
        # 特殊文字の処理
        text = text.replace('\x00', '')  # NULL文字削除
        text = text.replace('\ufeff', '')  # BOM削除
        
        return text.strip()
    
    def _is_meaningful_row_gentle(self, row: pd.Series) -> bool:
        """
        行が意味のあるデータを含んでいるかチェック（大幅に緩和）
        """
        meaningful_cells = 0
        total_content_length = 0
        
        for cell in row:
            if pd.notna(cell) and str(cell).strip():
                cell_text = str(cell).strip()
                # 基準を大幅に緩和：1文字以上で意味があると判定
                if len(cell_text) >= self.min_meaningful_length:
                    meaningful_cells += 1
                    total_content_length += len(cell_text)
        
        # 意味のあるセルが1個以上、または総文字数が1文字以上（大幅に緩和）
        return meaningful_cells >= 1 or total_content_length >= 1
    
    def _remove_exact_duplicates_only(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        完全に同一の行のみを削除（類似行は保持）
        """
        # 文字列化して完全一致のみを削除
        df_str = df.astype(str)
        return df[~df_str.duplicated()]
    
    def _convert_to_structured_text_enhanced(self, df: pd.DataFrame, sheet_name: str) -> str:
        """
        クリーニングされたDataFrameを構造化されたテキストに変換（改良版）
        """
        if df.empty:
            return ""
        
        text_parts = [f"=== シート: {sheet_name} ==="]
        
        # データの構造を分析（改良版）
        structure_info = self._analyze_data_structure_enhanced(df)
        
        if structure_info["has_headers"]:
            # ヘッダーがある場合の処理（改良版）
            text_parts.append(self._format_with_headers_enhanced(df, structure_info))
        else:
            # ヘッダーがない場合の処理（改良版）
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
        
        # 最初の数行をチェックしてヘッダーを探す（より柔軟に）
        for i in range(min(3, len(df))):  # 3行まで確認
            row = df.iloc[i]
            if self._looks_like_header_enhanced(row):
                structure["has_headers"] = True
                structure["header_row"] = i
                break
        
        # データタイプを分析
        for col in df.columns:
            structure["data_types"][col] = self._analyze_column_type_enhanced(df[col])
        
        return structure
    
    def _looks_like_header_enhanced(self, row: pd.Series) -> bool:
        """
        行がヘッダーらしいかチェック（改良版）
        """
        non_null_count = row.notna().sum()
        if non_null_count < 1:  # 1個以上あればヘッダーの可能性
            return False
        
        # ヘッダーらしいキーワードをチェック（拡張）
        header_keywords = [
            '名前', 'name', '会社', 'company', '住所', 'address', 
            '電話', 'phone', 'tel', '日付', 'date', 'id', 'no',
            '番号', '種類', 'type', '状態', 'status', '金額', 'amount',
            'ステータス', '顧客', '獲得', '物件', '契約', '書類',
            '発行', '請求', 'mail', '解約', '備考', '#'
        ]
        
        text_content = ' '.join([str(cell).lower() for cell in row if pd.notna(cell)])
        
        for keyword in header_keywords:
            if keyword in text_content:
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
        
        # テキストが数値より多い場合はヘッダーの可能性
        return text_cells > numeric_cells
    
    def _analyze_column_type_enhanced(self, column: pd.Series) -> str:
        """
        列のデータタイプを分析（改良版）
        """
        non_null_values = column.dropna()
        if len(non_null_values) == 0:
            return "empty"
        
        # 数値チェック
        numeric_count = 0
        date_count = 0
        text_count = 0
        id_count = 0
        
        for value in non_null_values:
            str_value = str(value).strip()
            
            # ID/番号パターン（SS0000000, ISP000000など）
            if re.match(r'^[A-Z]{2,}\d+$', str_value):
                id_count += 1
            # 数値パターン
            elif re.match(r'^-?\d+\.?\d*$', str_value):
                numeric_count += 1
            # 日付パターン（拡張）
            elif re.match(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', str_value) or 'NaT' in str_value:
                date_count += 1
            else:
                text_count += 1
        
        total = len(non_null_values)
        if id_count / total > 0.5:
            return "id"
        elif numeric_count / total > 0.7:
            return "numeric"
        elif date_count / total > 0.3:  # 日付の閾値を下げる
            return "date"
        else:
            return "text"
    
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
            if pd.notna(header) and str(header).strip():
                clean_header = str(header).strip()
                valid_headers.append((i, clean_header))
                formatted_parts.append(f"- {clean_header}")
        
        formatted_parts.append("\n【データ内容】")
        
        # データ行を処理（改良版 - より多くのデータを保持）
        for idx, row in data_rows.iterrows():
            row_data = []
            for col_idx, header_name in valid_headers:
                if col_idx < len(row):
                    cell_value = row.iloc[col_idx]
                    if pd.notna(cell_value) and str(cell_value).strip():
                        clean_value = str(cell_value).strip()
                        # メタデータ除外を大幅に緩和
                        if len(clean_value) > 0:  # 空でなければ保持
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
                if pd.notna(cell_value) and str(cell_value).strip():
                    clean_value = str(cell_value).strip()
                    # メタデータ除外を大幅に緩和
                    if len(clean_value) > 0:  # 空でなければ保持
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
        non_empty_cells = df.notna().sum().sum()
        total_cells = len(df) * len(df.columns)
        fill_rate = (non_empty_cells / total_cells * 100) if total_cells > 0 else 0
        stats_parts.append(f"データ充填率: {fill_rate:.1f}%")
        
        # データタイプ分布
        unique_values = df.nunique().sum()
        stats_parts.append(f"ユニーク値数: {unique_values}")
        
        return " | ".join(stats_parts)