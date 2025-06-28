"""
📊 Excel データクリーニング・構造化モジュール（超保守版）
データ損失を極限まで抑制し、ほぼ全ての情報を保持
空白・"nan"・完全に無意味なデータのみを除外
"""

import pandas as pd
import numpy as np
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from io import BytesIO
import unicodedata

logger = logging.getLogger(__name__)

class ExcelDataCleanerUltraConservative:
    """Excelデータのクリーニングと構造化を行うクラス（超保守版）"""
    
    def __init__(self):
        self.max_cell_length = 5000     # セル内容の最大文字数をさらに増加
        
        # 除外対象の無意味な値（最小限）
        self.meaningless_values = {
            'nan', 'NaN', 'null', 'NULL', 'None', 'NONE', '',
            '#N/A', '#VALUE!', '#REF!', '#DIV/0!', '#NAME?', '#NUM!', '#NULL!',
            'naan', 'naaN', 'NAAN'  # ユーザー指定の除外対象
        }
        
    def clean_excel_data(self, content: bytes) -> str:
        """
        乱雑なExcelデータをクリーニングして構造化されたテキストに変換
        データ損失を極限まで抑制する超保守版
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
                    
                    # データクリーニング（超保守版）
                    cleaned_df = self._clean_dataframe_ultra_conservative(df)
                    
                    if cleaned_df.empty:
                        logger.warning(f"⚠️ シート {sheet_name} にクリーニング後のデータがありません")
                        continue
                    
                    # 構造化されたテキストに変換（超保守版）
                    structured_text = self._convert_to_structured_text_ultra_conservative(cleaned_df, sheet_name)
                    
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
            logger.info(f"🎉 Excel処理完了（超保守版）: {len(cleaned_parts)}シート, 総文字数: {len(result)}")
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
    
    def _clean_dataframe_ultra_conservative(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameをクリーニング（超保守版 - ほぼ全てのデータを保持）
        """
        # 1. 完全に空の行・列のみを削除
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        if df.empty:
            return df
        
        # 2. セル内容をクリーニング（最小限）
        for col in df.columns:
            df[col] = df[col].apply(self._clean_cell_content_ultra_conservative)
        
        # 3. 完全に無意味な行のみを削除（基準を極限まで緩和）
        df = df[df.apply(self._is_meaningful_row_ultra_conservative, axis=1)]
        
        # 4. 重複行は削除しない（データの重要性を優先）
        
        # 5. インデックスをリセット
        df = df.reset_index(drop=True)
        
        return df
    
    def _clean_cell_content_ultra_conservative(self, cell_value) -> str:
        """
        セル内容をクリーニング（超保守版 - 最小限の処理）
        """
        if pd.isna(cell_value):
            return ""
        
        # 文字列に変換
        text = str(cell_value).strip()
        
        # 無意味な値をチェック
        if text.lower() in [v.lower() for v in self.meaningless_values]:
            return ""
        
        # 長すぎるセルは切り詰め（上限をさらに増加）
        if len(text) > self.max_cell_length:
            text = text[:self.max_cell_length] + "..."
        
        # Unicode正規化（最小限）
        text = unicodedata.normalize('NFKC', text)
        
        # 特殊文字の処理（最小限）
        text = text.replace('\x00', '')  # NULL文字削除
        text = text.replace('\ufeff', '')  # BOM削除
        
        # 空白の整理は最小限に
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _is_meaningful_row_ultra_conservative(self, row: pd.Series) -> bool:
        """
        行が意味のあるデータを含んでいるかチェック（超保守版）
        """
        for cell in row:
            if pd.notna(cell):
                cell_text = str(cell).strip()
                # 無意味な値でなければ意味があると判定
                if cell_text and cell_text.lower() not in [v.lower() for v in self.meaningless_values]:
                    return True
        
        return False
    
    def _convert_to_structured_text_ultra_conservative(self, df: pd.DataFrame, sheet_name: str) -> str:
        """
        クリーニングされたDataFrameを構造化されたテキストに変換（超保守版）
        """
        if df.empty:
            return ""
        
        text_parts = [f"=== シート: {sheet_name} ==="]
        
        # データの構造を分析（超保守版）
        structure_info = self._analyze_data_structure_ultra_conservative(df)
        
        if structure_info["has_headers"]:
            # ヘッダーがある場合の処理（超保守版）
            text_parts.append(self._format_with_headers_ultra_conservative(df, structure_info))
        else:
            # ヘッダーがない場合の処理（超保守版）
            text_parts.append(self._format_without_headers_ultra_conservative(df))
        
        # 統計情報を追加
        stats = self._generate_data_statistics_ultra_conservative(df)
        if stats:
            text_parts.append(f"\n【データ統計】\n{stats}")
        
        return "\n".join(text_parts)
    
    def _analyze_data_structure_ultra_conservative(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        データの構造を分析（超保守版）
        """
        structure = {
            "has_headers": False,
            "header_row": None,
            "data_types": {},
            "patterns": []
        }
        
        # 最初の数行をチェックしてヘッダーを探す（より柔軟に）
        for i in range(min(5, len(df))):  # 5行まで確認
            row = df.iloc[i]
            if self._looks_like_header_ultra_conservative(row):
                structure["has_headers"] = True
                structure["header_row"] = i
                break
        
        return structure
    
    def _looks_like_header_ultra_conservative(self, row: pd.Series) -> bool:
        """
        行がヘッダーらしいかチェック（超保守版）
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
            '回線', '速度', '料金', 'プラン', 'コース', 'オプション'
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
        return text_cells >= numeric_cells
    
    def _format_with_headers_ultra_conservative(self, df: pd.DataFrame, structure_info: Dict) -> str:
        """
        ヘッダーありの場合のフォーマット（超保守版）
        """
        header_row = structure_info["header_row"]
        headers = df.iloc[header_row].tolist()
        data_rows = df.iloc[header_row + 1:]
        
        formatted_parts = []
        formatted_parts.append("【データ項目】")
        
        # ヘッダー情報（全て保持）
        valid_headers = []
        for i, header in enumerate(headers):
            if pd.notna(header):
                clean_header = str(header).strip()
                if clean_header:  # 空でなければ全て保持
                    valid_headers.append((i, clean_header))
                    formatted_parts.append(f"- {clean_header}")
                else:
                    valid_headers.append((i, f"列{i+1}"))  # 空のヘッダーも番号で保持
                    formatted_parts.append(f"- 列{i+1}")
        
        formatted_parts.append("\n【データ内容】")
        
        # データ行を処理（超保守版 - 全てのデータを保持）
        for idx, row in data_rows.iterrows():
            row_data = []
            for col_idx, header_name in valid_headers:
                if col_idx < len(row):
                    cell_value = row.iloc[col_idx]
                    if pd.notna(cell_value):
                        clean_value = str(cell_value).strip()
                        # 無意味な値以外は全て保持
                        if clean_value and clean_value.lower() not in [v.lower() for v in self.meaningless_values]:
                            row_data.append(f"{header_name}: {clean_value}")
            
            if row_data:
                formatted_parts.append(f"• {' | '.join(row_data)}")
        
        return "\n".join(formatted_parts)
    
    def _format_without_headers_ultra_conservative(self, df: pd.DataFrame) -> str:
        """
        ヘッダーなしの場合のフォーマット（超保守版）
        """
        formatted_parts = []
        formatted_parts.append("【データ内容】")
        
        for idx, row in df.iterrows():
            row_data = []
            for col_idx, cell_value in enumerate(row):
                if pd.notna(cell_value):
                    clean_value = str(cell_value).strip()
                    # 無意味な値以外は全て保持
                    if clean_value and clean_value.lower() not in [v.lower() for v in self.meaningless_values]:
                        row_data.append(clean_value)
            
            if row_data:
                formatted_parts.append(f"行{idx + 1}: {' | '.join(row_data)}")
        
        return "\n".join(formatted_parts)
    
    def _generate_data_statistics_ultra_conservative(self, df: pd.DataFrame) -> str:
        """
        データの統計情報を生成（超保守版）
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
        
        # データタイプ分布
        unique_values = df.nunique().sum()
        stats_parts.append(f"ユニーク値数: {unique_values}")
        
        return " | ".join(stats_parts)