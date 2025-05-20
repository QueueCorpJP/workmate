"""
Excelファイル処理モジュール
Excelファイルの読み込みと処理を行います
"""
import pandas as pd
from io import BytesIO
import traceback

def process_excel_file(contents, filename):
    """Excelファイルを処理してデータフレーム、セクション、テキストを返す"""
    try:
        # BytesIOオブジェクトを作成
        excel_file = BytesIO(contents)
        
        # Excelファイルを読み込む
        df_dict = pd.read_excel(excel_file, sheet_name=None)
        
        # 全シートのデータを結合
        all_data = []
        sections = {}
        extracted_text = f"=== ファイル: {filename} ===\n\n"
        
        for sheet_name, sheet_df in df_dict.items():
            # シート名をセクションとして追加
            section_name = f"シート: {sheet_name}"
            # DataFrameをstring形式に変換する前に、すべての値を文字列に変換
            sheet_df_str = sheet_df.applymap(lambda x: str(x) if x is not None else "")
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