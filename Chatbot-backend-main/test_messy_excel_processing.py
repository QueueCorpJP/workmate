"""
🧪 乱雑なExcelデータ処理のテストスクリプト
実際の乱雑なデータでExcelDataCleanerの動作を確認
"""

import pandas as pd
import numpy as np
from io import BytesIO
import logging
from modules.excel_data_cleaner import ExcelDataCleaner

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_messy_excel_sample():
    """
    ユーザーが提供したような乱雑なExcelデータのサンプルを作成
    """
    # 乱雑なデータの例（ユーザーの例を参考）
    messy_data = [
        [0, 6, "キャンセル", "", "", "", "○", "フォーバル", "SS0101868", "900101868"],
        ["", "", "ＴＥＮ Ｇｒｅｅｎ Ｆａｃｔｏｒｙ 株式会社", "438-0803", "", "静岡県", "", "", "", ""],
        ["静岡県磐田市富丘905-1 サンキョウハイツ201号", "", "", "", "鈴木貴博", "", "", "", "ビジサポ部", ""],
        ["梅沢佑真", "2022-04-19 00:00:00", "", "", "-", "NaT", "", "ISPH00365", "朝日ネット", ""],
        ["", "", "", "", "", "", "固定なし", "ファミリー", "SHSタイプ隼", "800"],
        ["", "", "", "", "", "", "", "", "", "あり"],
        ["21109680", "", "", "CAF5325209664", "", "", "", "", "", ""],
        ["2022-05-09 00:00:00", "西野", "00:00:00", "", "", "", "", "", "", ""],
        ["-", "", "", "", "", "", "", "", "", ""],
        ["-", "", "", "", "", "", "", "", "", ""],
        ["キャンセル", "", "", "", "", "不要", "", "", "", ""],
        ["", "", "", "", "", "", "", "", "", ""],
        ["1", "とか", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", "", ""],
        ["NaT", "", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", "", ""],
        ["NaT", "", "", "", "", "", "", "", "", ""],
        ["とかあってこういうのって質問しても回答できなかったりするんだけどどうしたらいい", "", "", "", "", "", "", "", "", ""]
    ]
    
    # DataFrameを作成
    df = pd.DataFrame(messy_data)
    
    # Excelファイルとして保存（メモリ上）
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='乱雑なデータ', index=False, header=False)
    
    buffer.seek(0)
    return buffer.getvalue()

def create_structured_excel_sample():
    """
    比較用の構造化されたExcelデータを作成
    """
    structured_data = {
        '会社名': ['ＴＥＮ Ｇｒｅｅｎ Ｆａｃｔｏｒｙ 株式会社', 'サンプル会社A', 'テスト企業B'],
        '郵便番号': ['438-0803', '100-0001', '530-0001'],
        '住所': ['静岡県磐田市富丘905-1', '東京都千代田区千代田1-1', '大阪府大阪市北区梅田1-1'],
        '担当者': ['鈴木貴博', '田中太郎', '佐藤花子'],
        '部署': ['ビジサポ部', '営業部', '開発部'],
        '契約日': ['2022-04-19', '2022-05-01', '2022-06-15'],
        'ステータス': ['キャンセル', 'アクティブ', 'アクティブ']
    }
    
    df = pd.DataFrame(structured_data)
    
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='構造化データ', index=False)
    
    buffer.seek(0)
    return buffer.getvalue()

async def test_messy_excel_processing():
    """
    乱雑なExcelデータの処理をテスト
    """
    print("🧪 乱雑なExcelデータ処理テスト開始")
    print("=" * 60)
    
    # ExcelDataCleanerを初期化
    cleaner = ExcelDataCleaner()
    
    # テスト1: 乱雑なデータ
    print("\n📊 テスト1: 乱雑なデータの処理")
    print("-" * 40)
    
    messy_excel_data = create_messy_excel_sample()
    
    try:
        cleaned_text = cleaner.clean_excel_data(messy_excel_data)
        print("✅ 乱雑なデータの処理成功")
        print(f"📄 処理結果（最初の500文字）:")
        print(cleaned_text[:500])
        print("..." if len(cleaned_text) > 500 else "")
        print(f"\n📊 総文字数: {len(cleaned_text)}")
        
    except Exception as e:
        print(f"❌ 乱雑なデータの処理失敗: {e}")
    
    # テスト2: 構造化されたデータ
    print("\n📊 テスト2: 構造化されたデータの処理")
    print("-" * 40)
    
    structured_excel_data = create_structured_excel_sample()
    
    try:
        cleaned_text = cleaner.clean_excel_data(structured_excel_data)
        print("✅ 構造化データの処理成功")
        print(f"📄 処理結果:")
        print(cleaned_text)
        print(f"\n📊 総文字数: {len(cleaned_text)}")
        
    except Exception as e:
        print(f"❌ 構造化データの処理失敗: {e}")

def test_data_analysis():
    """
    データ分析機能のテスト
    """
    print("\n🔍 データ分析機能テスト")
    print("-" * 40)
    
    cleaner = ExcelDataCleaner()
    
    # サンプルDataFrame
    test_data = pd.DataFrame({
        'A': ['会社名', 'ＴＥＮ Ｇｒｅｅｎ', 'サンプル会社', ''],
        'B': ['担当者', '鈴木貴博', '田中太郎', ''],
        'C': ['金額', '1000', '2000', ''],
        'D': ['日付', '2022-04-19', '2022-05-01', '']
    })
    
    # 構造分析
    structure = cleaner._analyze_data_structure(test_data)
    print(f"📊 構造分析結果:")
    print(f"  - ヘッダー検出: {structure['has_headers']}")
    print(f"  - ヘッダー行: {structure['header_row']}")
    print(f"  - データタイプ: {structure['data_types']}")
    
    # ヘッダー検出テスト
    header_row = test_data.iloc[0]
    is_header = cleaner._looks_like_header(header_row)
    print(f"  - 最初の行がヘッダー: {is_header}")

if __name__ == "__main__":
    print("🚀 乱雑なExcelデータ処理システムのテスト")
    print("=" * 60)
    
    # 非同期テストを実行
    import asyncio
    asyncio.run(test_messy_excel_processing())
    
    # データ分析テスト
    test_data_analysis()
    
    print("\n🎉 テスト完了")
    print("\n💡 使用方法:")
    print("1. 乱雑なExcelファイルをアップロード")
    print("2. システムが自動的にデータをクリーニング・構造化")
    print("3. 構造化されたデータに基づいて質問応答が可能")
    print("\n📝 改善点:")
    print("- より複雑なデータパターンの対応")
    print("- 業界固有の用語辞書の追加")
    print("- データ品質スコアの表示")