"""
⚠️ 非推奨モジュール ⚠️
このモジュールは非推奨です。新しいGoogle Sheets API処理については excel_sheets_processor.py を使用してください。

Excelファイル処理モジュール（pandas使用 - 非推奨）
Excelファイル(.xlsx、.xls)の読み込みと処理を行います

新しい実装では以下の利点があります：
- pandasに依存しない
- Google Drive APIでファイル変換
- Google Sheets APIで綺麗なデータ抽出
- より正確なフォーマット処理
"""
import pandas as pd
from io import BytesIO
import traceback
import logging
import warnings
from .unnamed_column_handler import UnnamedColumnHandler

# 非推奨警告
warnings.warn(
    "excel.py は非推奨です。excel_sheets_processor.py を使用してください。",
    DeprecationWarning,
    stacklevel=2
)

# ロガーの設定
logger = logging.getLogger(__name__)

# .xls形式のサポートのためのライブラリチェック
try:
    import xlrd
    XLRD_AVAILABLE = True
    logger.info("xlrdライブラリが利用可能です（.xlsファイルサポート）")
except ImportError:
    XLRD_AVAILABLE = False
    logger.warning("xlrdライブラリが見つかりません。.xlsファイルのサポートが制限されます。pip install xlrdを実行してください。")

# .xlsx形式のサポートのためのライブラリチェック
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
    logger.info("openpyxlライブラリが利用可能です（.xlsxファイルサポート）")
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning("openpyxlライブラリが見つかりません。.xlsxファイルのサポートが制限されます。pip install openpyxlを実行してください。")

def process_excel_file(contents, filename):
    """
    ⚠️ 非推奨関数 ⚠️
    この関数は非推奨です。excel_sheets_processor.process_excel_file_with_sheets_api() を使用してください。
    
    Excelファイルを処理してデータフレーム、セクション、テキストを返す
    """
    logger.warning("⚠️ process_excel_file() は非推奨です。excel_sheets_processor.process_excel_file_with_sheets_api() を使用してください。")
    
    try:
        # BytesIOオブジェクトを作成
        excel_file = BytesIO(contents)
        
        # ファイル拡張子を確認してエンジンを選択
        file_extension = filename.lower().split('.')[-1]
        engine = None
        
        if file_extension == 'xls':
            if XLRD_AVAILABLE:
                engine = 'xlrd'
                logger.info(f"xlsファイル {filename} をxlrdエンジンで処理します")
            else:
                logger.error(f"xlsファイル {filename} の処理にはxlrdライブラリが必要です")
                raise ImportError("xlsファイルの処理にはxlrdライブラリが必要です。pip install xlrdを実行してください。")
        elif file_extension == 'xlsx':
            if OPENPYXL_AVAILABLE:
                engine = 'openpyxl'
                logger.info(f"xlsxファイル {filename} をopenpyxlエンジンで処理します")
            else:
                logger.error(f"xlsxファイル {filename} の処理にはopenpyxlライブラリが必要です")
                raise ImportError("xlsxファイルの処理にはopenpyxlライブラリが必要です。pip install openpyxlを実行してください。")
        else:
            logger.warning(f"サポートされていないファイル形式: {file_extension}。xlsまたはxlsxファイルをサポートしています。")
        
        # Excelファイルを読み込む（エンジンを指定）
        if engine:
            df_dict = pd.read_excel(excel_file, sheet_name=None, engine=engine)
        else:
            df_dict = pd.read_excel(excel_file, sheet_name=None)
        
        # UnnamedColumnHandlerを初期化
        handler = UnnamedColumnHandler()
        
        # 全シートのデータを結合
        all_data = []
        sections = {}
        extracted_text = f"=== ファイル: {filename} ===\n\n"
        
        for sheet_name, sheet_df in df_dict.items():
            # UnnamedColumnHandlerでカラムを修正
            sheet_df, modifications = handler.fix_dataframe(sheet_df, f"{filename}:{sheet_name}")
            
            if modifications:
                logger.info(f"シート '{sheet_name}' のUnnamedカラム修正: {', '.join(modifications)}")
            
            # シート名をセクションとして追加
            section_name = f"シート: {sheet_name}"
            # DataFrameをstring形式に変換する前に、すべての値を文字列に変換
            sheet_df_str = sheet_df.map(lambda x: str(x) if x is not None else "")
            sections[section_name] = sheet_df_str.to_string(index=False)
            extracted_text += f"=== {section_name} ===\n{sheet_df_str.to_string(index=False)}\n\n"
            
            # 各行のすべての内容を結合して content 列を作成
            for _, row in sheet_df.iterrows():
                row_dict = row.to_dict()
                
                # content 列を作成（すべての列の値を結合）
                content_parts = []
                for col, val in row_dict.items():
                    if not pd.isna(val):  # NaN値をスキップ
                        content_parts.append(str(val))
                
                # 結合したコンテンツを設定
                row_dict['content'] = " ".join(str(part) for part in content_parts if part)
                
                # メタデータを追加
                row_dict['section'] = str(section_name)
                row_dict['source'] = 'Excel'
                row_dict['file'] = filename
                row_dict['url'] = None
                
                # すべての値を文字列に変換（NULL値はそのまま保持）
                row_dict = {k: str(v) if v is not None else None for k, v in row_dict.items()}
                all_data.append(row_dict)
        
        # データフレームを作成
        result_df = pd.DataFrame(all_data) if all_data else pd.DataFrame({
            'section': ["シート: 不明"],
            'content': [""],
            'source': ['Excel'],
            'file': [filename],
            'url': [None]
        })
        
        # 必須列が存在することを確認
        for col in ['section', 'source', 'file', 'url', 'content']:
            if col not in result_df.columns:
                if col == 'source':
                    result_df[col] = 'Excel'
                elif col == 'file':
                    result_df[col] = filename
                elif col == 'content':
                    # 各行の全ての列の値を結合して content 列を作成
                    if not result_df.empty:
                        result_df[col] = result_df.apply(
                            lambda row: " ".join(str(val) for val in row.values if not pd.isna(val)),
                            axis=1
                        )
                else:
                    result_df[col] = None
        
        # デバッグ情報を出力
        print(f"処理後のデータフレーム列: {result_df.columns.tolist()}")
        if not result_df.empty:
            print(f"最初の行の content: {result_df['content'].iloc[0]}")
        
        return result_df, sections, extracted_text
    except Exception as e:
        print(f"Excelファイル処理エラー: {str(e)}")
        print(traceback.format_exc())
        
        # エラーが発生しても最低限のデータを返す
        empty_df = pd.DataFrame({
            'section': ["エラー"],
            'content': [f"Excelファイル処理中にエラーが発生しました: {str(e)}"],
            'source': ['Excel'],
            'file': [filename],
            'url': [None]
        })
        empty_sections = {"エラー": f"Excelファイル処理中にエラーが発生しました: {str(e)}"}
        error_text = f"=== ファイル: {filename} ===\n\n=== エラー ===\nExcelファイル処理中にエラーが発生しました: {str(e)}\n\n"
        
        return empty_df, empty_sections, error_text 