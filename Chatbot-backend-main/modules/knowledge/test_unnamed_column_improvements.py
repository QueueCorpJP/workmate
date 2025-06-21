"""
Unnamed Column Handler テストファイル
unnamed_column_handling_guide_en.mdに基づく改善のテスト
"""
import unittest
import pandas as pd
import io
from unittest.mock import patch, MagicMock
from unnamed_column_handler import UnnamedColumnHandler
from csv_processor import process_csv_file, detect_csv_encoding, detect_csv_delimiter
from pdf import extract_tables_from_text, split_ocr_text_into_sections

class TestUnnamedColumnHandler(unittest.TestCase):
    """UnnamedColumnHandlerのテストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        self.handler = UnnamedColumnHandler()
    
    def test_detect_unnamed_columns(self):
        """Unnamedカラム検出テスト"""
        df = pd.DataFrame({
            'Unnamed: 0': ['1', '2', '3'],
            '名前': ['田中', '佐藤', '鈴木'],
            'Unnamed: 2': ['A', 'B', 'C'],
            '年齢': ['25', '30', '35']
        })
        
        unnamed_cols = self.handler.detect_unnamed_columns(df)
        self.assertEqual(unnamed_cols, [0, 2])  # インデックス0と2がUnnamed
    
    def test_detect_header_row(self):
        """ヘッダー行検出テスト"""
        df = pd.DataFrame([
            ['タイトル行', '', '', ''],
            ['ID', '名前', '部署', '給与'],
            ['001', '田中太郎', '営業部', '500000'],
            ['002', '佐藤花子', '経理部', '450000']
        ])
        
        header_row = self.handler.detect_header_row(df)
        self.assertEqual(header_row, 1)  # 2行目がヘッダー
    
    def test_is_row_index_column(self):
        """行インデックスカラム判定テスト"""
        # 連続する数値（行インデックス）
        index_col = pd.Series([1, 2, 3, 4, 5])
        self.assertTrue(self.handler._is_row_index_column(index_col))
        
        # 非連続の数値
        non_index_col = pd.Series([1, 5, 10, 15, 20])
        self.assertFalse(self.handler._is_row_index_column(non_index_col))
        
        # 文字列データ
        text_col = pd.Series(['A', 'B', 'C', 'D', 'E'])
        self.assertFalse(self.handler._is_row_index_column(text_col))
    
    def test_fix_dataframe_with_unnamed_columns(self):
        """Unnamedカラム修正テスト"""
        df = pd.DataFrame({
            'Unnamed: 0': [1, 2, 3, 4],  # 行インデックス（削除される）
            '名前': ['田中', '佐藤', '鈴木', '高橋'],
            'Unnamed: 2': ['営業', '経理', '開発', '人事'],  # 意味のあるデータ（名前変更）
            '年齢': [25, 30, 35, 28]
        })
        
        fixed_df, modifications = self.handler.fix_dataframe(df, "test.csv")
        
        # 行インデックスカラムが削除されることを確認
        self.assertNotIn('Unnamed: 0', fixed_df.columns)
        
        # 意味のあるUnnamedカラムが名前変更されることを確認
        unnamed_cols = [col for col in fixed_df.columns if 'Unnamed' in str(col)]
        self.assertEqual(len(unnamed_cols), 0)
        
        # 修正ログが記録されることを確認
        self.assertTrue(len(modifications) > 0)
    
    def test_fix_dataframe_with_header_shift(self):
        """ヘッダー行シフトテスト"""
        df = pd.DataFrame([
            ['レポート', '2024年1月', '', ''],  # 装飾行
            ['ID', '名前', '部署', '給与'],     # 真のヘッダー
            ['001', '田中', '営業', '500000'],
            ['002', '佐藤', '経理', '450000']
        ])
        
        fixed_df, modifications = self.handler.fix_dataframe(df, "report.csv")
        
        # ヘッダー行が正しく設定されることを確認
        expected_headers = ['ID', '名前', '部署', '給与']
        self.assertEqual(list(fixed_df.columns), expected_headers)
        
        # データ行が2行であることを確認
        self.assertEqual(len(fixed_df), 2)
    
    def test_create_clean_sections(self):
        """セクション作成テスト"""
        df = pd.DataFrame({
            'ID': ['001', '002'],
            '名前': ['田中', '佐藤'],
            '部署': ['営業', '経理']
        })
        
        sections = self.handler.create_clean_sections(df, "test.csv")
        
        # テーブル構造セクションが作成されることを確認
        structure_section = next((s for s in sections if s['section'] == 'テーブル構造'), None)
        self.assertIsNotNone(structure_section)
        self.assertIn('ID', structure_section['content'])
        
        # 各行がセクションとして作成されることを確認
        row_sections = [s for s in sections if s['section'].startswith('行')]
        self.assertEqual(len(row_sections), 2)

class TestCSVProcessorIntegration(unittest.TestCase):
    """CSV処理統合テスト"""
    
    def test_csv_with_unnamed_columns(self):
        """Unnamedカラムを含むCSV処理テスト"""
        csv_content = b""",\xe5\x90\x8d\xe5\x89\x8d,,\xe5\xb9\xb4\xe9\xbd\xa2
1,\xe7\x94\xb0\xe4\xb8\xad,\xe5\x96\xb6\xe6\xa5\xad,25
2,\xe4\xbd\x90\xe8\x97\xa4,\xe7\xb5\x8c\xe7\x90\x86,30
3,\xe9\x88\xb4\xe6\x9c\xa8,\xe9\x96\x8b\xe7\x99\xba,35"""
        
        result_df, sections, extracted_text = process_csv_file(csv_content, "test_unnamed.csv")
        
        # 結果が返されることを確認
        self.assertIsNotNone(result_df)
        self.assertIsInstance(sections, dict)
        self.assertIsInstance(extracted_text, str)
        
        # データが適切に処理されることを確認
        self.assertGreater(len(result_df), 0)

class TestPDFTableExtraction(unittest.TestCase):
    """PDF テーブル抽出テスト"""
    
    def test_markdown_table_extraction(self):
        """マークダウンテーブル抽出テスト"""
        text = """
        以下は売上データです：
        
        | 商品名 | 数量 | 単価 | 合計 |
        |--------|------|------|------|
        | リンゴ | 10   | 100  | 1000 |
        | バナナ | 5    | 80   | 400  |
        | オレンジ | 8  | 120  | 960  |
        
        以上のデータから分析します。
        """
        
        tables = extract_tables_from_text(text)
        
        # テーブルが抽出されることを確認
        self.assertGreater(len(tables), 0)
        
        # 最初のテーブルの構造を確認
        first_table = tables[0]
        self.assertEqual(list(first_table.columns), ['商品名', '数量', '単価', '合計'])
        self.assertEqual(len(first_table), 3)  # 3行のデータ
    
    def test_tabular_data_extraction(self):
        """表形式データ抽出テスト"""
        text = """
        商品名    数量    単価    合計
        リンゴ    10      100     1000
        バナナ    5       80      400
        オレンジ  8       120     960
        """
        
        tables = extract_tables_from_text(text)
        
        # テーブルが抽出されることを確認
        self.assertGreater(len(tables), 0)
        
        # データが適切に分離されることを確認
        first_table = tables[0]
        self.assertGreater(len(first_table.columns), 2)
        self.assertGreater(len(first_table), 2)
    
    def test_ocr_text_with_tables(self):
        """テーブルを含むOCRテキスト処理テスト"""
        ocr_text = """
        --- Page 1 ---
        月次売上レポート
        
        | 商品 | 売上 |
        |------|------|
        | A    | 1000 |
        | B    | 2000 |
        
        --- Page 2 ---
        分析結果：
        売上が好調です。
        """
        
        sections = split_ocr_text_into_sections(ocr_text, "sales_report.pdf")
        
        # セクションが作成されることを確認
        self.assertGreater(len(sections), 0)
        
        # テーブルセクションが含まれることを確認
        table_sections = [s for s in sections if 'テーブル' in s['section']]
        self.assertGreater(len(table_sections), 0)

class TestEncodingDetection(unittest.TestCase):
    """エンコーディング検出テスト"""
    
    def test_utf8_detection(self):
        """UTF-8検出テスト"""
        content = "名前,年齢,部署\n田中,25,営業\n佐藤,30,経理".encode('utf-8')
        encoding = detect_csv_encoding(content)
        
        # UTF-8が検出されることを確認
        self.assertIn(encoding.lower(), ['utf-8', 'utf8'])
    
    def test_shift_jis_detection(self):
        """Shift-JIS検出テスト"""
        content = "名前,年齢,部署\n田中,25,営業\n佐藤,30,経理".encode('shift_jis')
        encoding = detect_csv_encoding(content)
        
        # 何らかのエンコーディングが検出されることを確認
        self.assertIsNotNone(encoding)
        self.assertIsInstance(encoding, str)

class TestDelimiterDetection(unittest.TestCase):
    """区切り文字検出テスト"""
    
    def test_comma_delimiter(self):
        """カンマ区切り検出テスト"""
        content = "名前,年齢,部署\n田中,25,営業\n佐藤,30,経理"
        delimiter = detect_csv_delimiter(content)
        self.assertEqual(delimiter, ',')
    
    def test_tab_delimiter(self):
        """タブ区切り検出テスト"""
        content = "名前\t年齢\t部署\n田中\t25\t営業\n佐藤\t30\t経理"
        delimiter = detect_csv_delimiter(content)
        self.assertEqual(delimiter, '\t')
    
    def test_semicolon_delimiter(self):
        """セミコロン区切り検出テスト"""
        content = "名前;年齢;部署\n田中;25;営業\n佐藤;30;経理"
        delimiter = detect_csv_delimiter(content)
        self.assertEqual(delimiter, ';')

if __name__ == '__main__':
    # テスト実行
    unittest.main(verbosity=2) 