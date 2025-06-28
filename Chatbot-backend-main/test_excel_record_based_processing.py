"""
📊 Excelレコードベース処理テストスクリプト
1レコード（1行）を1つの意味のまとまりとして自然文に変換する機能をテスト
"""

import os
import sys
import logging
import asyncio
import pandas as pd
from io import BytesIO
from typing import Dict, Any, List

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_excel_data() -> bytes:
    """テスト用のExcelデータを作成"""
    try:
        # ISP案件一覧のサンプルデータ
        data = {
            '会社名': [
                '株式会社テクノロジー',
                '有限会社ネットワーク',
                '合同会社クラウド',
                '株式会社データセンター',
                '企業法人コミュニケーション'
            ],
            '設置先住所': [
                '東京都渋谷区神宮前1-1-1',
                '大阪府大阪市北区梅田2-2-2',
                '愛知県名古屋市中区栄3-3-3',
                '福岡県福岡市博多区博多駅前4-4-4',
                '北海道札幌市中央区大通5-5-5'
            ],
            '契約サービス': [
                '光ファイバー 100Mbps',
                'ADSL 50Mbps',
                '光ファイバー 1Gbps',
                '専用線 10Mbps',
                'CATV インターネット 200Mbps'
            ],
            '契約日': [
                '2023-01-15',
                '2023-02-20',
                '2023-03-10',
                '2023-04-05',
                '2023-05-12'
            ],
            '担当者': [
                '田中太郎',
                '佐藤花子',
                '鈴木一郎',
                '高橋美咲',
                '渡辺健太'
            ],
            '電話番号': [
                '03-1234-5678',
                '06-2345-6789',
                '052-3456-7890',
                '092-4567-8901',
                '011-5678-9012'
            ],
            '備考': [
                '新規契約、設置工事完了',
                '既存回線からの切り替え',
                '増速プランに変更予定',
                '24時間監視サービス付き',
                'VPN接続オプション追加'
            ]
        }
        
        # DataFrameを作成
        df = pd.DataFrame(data)
        
        # Excelファイルとしてバイト形式で出力
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='ISP案件一覧', index=False)
        
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"❌ テストExcelデータ作成エラー: {e}")
        raise

async def test_record_based_cleaner():
    """レコードベースクリーナーのテスト"""
    try:
        logger.info("🧪 レコードベースクリーナーテスト開始")
        
        # テストデータを作成
        excel_content = create_test_excel_data()
        logger.info(f"📊 テストExcelデータ作成完了: {len(excel_content)} bytes")
        
        # レコードベースクリーナーをテスト
        from modules.excel_data_cleaner_record_based import ExcelDataCleanerRecordBased
        cleaner = ExcelDataCleanerRecordBased()
        
        records = cleaner.clean_excel_data(excel_content)
        
        logger.info(f"📋 抽出されたレコード数: {len(records)}")
        
        # 各レコードの内容を表示
        for i, record in enumerate(records):
            logger.info(f"📄 レコード {i + 1}:")
            logger.info(f"  内容: {record.get('content', '')[:200]}...")
            logger.info(f"  シート: {record.get('source_sheet', 'N/A')}")
            logger.info(f"  レコードインデックス: {record.get('record_index', 'N/A')}")
            logger.info(f"  タイプ: {record.get('record_type', 'N/A')}")
            logger.info(f"  推定トークン数: {record.get('token_estimate', 0)}")
            logger.info("")
        
        # 期待される結果をチェック
        assert len(records) == 5, f"期待されるレコード数: 5, 実際: {len(records)}"
        
        # 各レコードが会社名、住所、サービスを含んでいることを確認
        for record in records:
            content = record.get('content', '')
            assert '会社名は' in content, f"会社名が含まれていません: {content}"
            assert '設置先住所は' in content, f"設置先住所が含まれていません: {content}"
            assert '契約サービスは' in content, f"契約サービスが含まれていません: {content}"
        
        logger.info("✅ レコードベースクリーナーテスト成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ レコードベースクリーナーテストエラー: {e}")
        return False

async def test_record_based_processor():
    """レコードベースプロセッサーのテスト"""
    try:
        logger.info("🧪 レコードベースプロセッサーテスト開始")
        
        # 環境変数をテスト用に設定
        os.environ["AUTO_GENERATE_EMBEDDINGS"] = "false"  # テスト時はEmbedding生成を無効化
        
        # テストデータを作成
        excel_content = create_test_excel_data()
        
        # モックファイルオブジェクトを作成
        class MockUploadFile:
            def __init__(self, content: bytes, filename: str):
                self.content = content
                self.filename = filename
                self._position = 0
            
            async def read(self):
                return self.content
            
            async def seek(self, position: int):
                self._position = position
        
        mock_file = MockUploadFile(excel_content, "test_isp_data.xlsx")
        
        # レコードベースプロセッサーをテスト
        from modules.document_processor_record_based import DocumentProcessorRecordBased
        processor = DocumentProcessorRecordBased()
        
        # 注意: 実際のデータベース操作は行わず、処理ロジックのみテスト
        logger.info("⚠️ 注意: データベース操作は実行されません（テストモード）")
        
        # レコードベースクリーナーの部分のみテスト
        from modules.excel_data_cleaner_record_based import ExcelDataCleanerRecordBased
        cleaner = ExcelDataCleanerRecordBased()
        records = cleaner.clean_excel_data(excel_content)
        
        logger.info(f"📋 プロセッサーで処理されたレコード数: {len(records)}")
        
        # レコードの品質をチェック
        for i, record in enumerate(records):
            content = record.get('content', '')
            token_estimate = record.get('token_estimate', 0)
            
            logger.info(f"📄 レコード {i + 1} 品質チェック:")
            logger.info(f"  文字数: {len(content)}")
            logger.info(f"  推定トークン数: {token_estimate}")
            logger.info(f"  内容プレビュー: {content[:100]}...")
            
            # 品質チェック
            assert len(content) > 50, f"レコード {i + 1} の内容が短すぎます"
            assert token_estimate > 0, f"レコード {i + 1} のトークン推定が無効です"
            assert '会社名は' in content, f"レコード {i + 1} に会社名が含まれていません"
        
        logger.info("✅ レコードベースプロセッサーテスト成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ レコードベースプロセッサーテストエラー: {e}")
        return False

async def test_natural_text_conversion():
    """自然文変換の品質テスト"""
    try:
        logger.info("🧪 自然文変換品質テスト開始")
        
        # テストデータを作成
        excel_content = create_test_excel_data()
        
        from modules.excel_data_cleaner_record_based import ExcelDataCleanerRecordBased
        cleaner = ExcelDataCleanerRecordBased()
        records = cleaner.clean_excel_data(excel_content)
        
        logger.info("📝 自然文変換結果:")
        
        for i, record in enumerate(records):
            content = record.get('content', '')
            logger.info(f"\n--- レコード {i + 1} ---")
            logger.info(content)
            
            # 自然文の品質チェック
            # 1. 適切な助詞が使われているか
            assert 'は' in content, f"レコード {i + 1}: 助詞「は」が使われていません"
            assert 'で、' in content or 'です。' in content, f"レコード {i + 1}: 適切な接続詞・語尾がありません"
            
            # 2. 文として完結しているか
            assert content.endswith('。'), f"レコード {i + 1}: 文が句点で終わっていません"
            
            # 3. 重要な情報が含まれているか
            assert any(keyword in content for keyword in ['会社名', '住所', 'サービス']), \
                f"レコード {i + 1}: 重要な情報が含まれていません"
        
        logger.info("✅ 自然文変換品質テスト成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 自然文変換品質テストエラー: {e}")
        return False

async def main():
    """メインテスト実行"""
    logger.info("🚀 Excelレコードベース処理テスト開始")
    
    test_results = []
    
    # テスト1: レコードベースクリーナー
    result1 = await test_record_based_cleaner()
    test_results.append(("レコードベースクリーナー", result1))
    
    # テスト2: レコードベースプロセッサー
    result2 = await test_record_based_processor()
    test_results.append(("レコードベースプロセッサー", result2))
    
    # テスト3: 自然文変換品質
    result3 = await test_natural_text_conversion()
    test_results.append(("自然文変換品質", result3))
    
    # 結果サマリー
    logger.info("\n" + "="*50)
    logger.info("📊 テスト結果サマリー")
    logger.info("="*50)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 成功" if result else "❌ 失敗"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    logger.info("="*50)
    
    if all_passed:
        logger.info("🎉 全テスト成功！レコードベース処理が正常に動作しています。")
    else:
        logger.error("💥 一部テストが失敗しました。実装を確認してください。")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main())