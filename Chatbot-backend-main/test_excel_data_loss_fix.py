"""
🧪 Excel データ損失修正のテストスクリプト
修正版ExcelDataCleanerFixedの動作を確認し、データ損失を検証
"""

import asyncio
import logging
from modules.excel_data_cleaner_fixed import ExcelDataCleanerFixed
from modules.excel_data_cleaner import ExcelDataCleaner
from modules.document_processor import DocumentProcessor

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_excel_data_loss_fix():
    """
    Excel データ損失修正のテスト
    """
    print("🧪 Excel データ損失修正テスト開始")
    print("=" * 60)
    
    # 実際のファイルを読み込み
    excel_file_path = "01_ISP案件一覧.xlsx"
    
    try:
        with open(excel_file_path, 'rb') as f:
            content = f.read()
        
        print(f"📄 ファイル読み込み完了: {len(content)} bytes")
        
        # 1. 従来版での処理
        print("\n📊 テスト1: 従来版ExcelDataCleaner")
        print("-" * 40)
        
        try:
            original_cleaner = ExcelDataCleaner()
            original_result = original_cleaner.clean_excel_data(content)
            print(f"✅ 従来版処理成功")
            print(f"📄 処理結果文字数: {len(original_result)}")
            print(f"📄 処理結果（最初の300文字）:")
            print(original_result[:300])
            print("..." if len(original_result) > 300 else "")
            
        except Exception as e:
            print(f"❌ 従来版処理失敗: {e}")
            original_result = ""
        
        # 2. 修正版での処理
        print("\n📊 テスト2: 修正版ExcelDataCleanerFixed")
        print("-" * 40)
        
        try:
            fixed_cleaner = ExcelDataCleanerFixed()
            fixed_result = fixed_cleaner.clean_excel_data(content)
            print(f"✅ 修正版処理成功")
            print(f"📄 処理結果文字数: {len(fixed_result)}")
            print(f"📄 処理結果（最初の300文字）:")
            print(fixed_result[:300])
            print("..." if len(fixed_result) > 300 else "")
            
        except Exception as e:
            print(f"❌ 修正版処理失敗: {e}")
            fixed_result = ""
        
        # 3. DocumentProcessorでの処理
        print("\n📊 テスト3: DocumentProcessor（修正版統合）")
        print("-" * 40)
        
        try:
            processor = DocumentProcessor()
            
            # UploadFileオブジェクトをモック
            class MockUploadFile:
                def __init__(self, filename, content):
                    self.filename = filename
                    self.content = content
                
                async def read(self):
                    return self.content
            
            mock_file = MockUploadFile(excel_file_path, content)
            processor_result = await processor._extract_text_from_excel(content)
            
            print(f"✅ DocumentProcessor処理成功")
            print(f"📄 処理結果文字数: {len(processor_result)}")
            print(f"📄 処理結果（最初の300文字）:")
            print(processor_result[:300])
            print("..." if len(processor_result) > 300 else "")
            
        except Exception as e:
            print(f"❌ DocumentProcessor処理失敗: {e}")
            processor_result = ""
        
        # 4. 結果比較
        print("\n📊 結果比較")
        print("-" * 40)
        
        if original_result and fixed_result:
            improvement_ratio = len(fixed_result) / len(original_result)
            print(f"📈 文字数改善率: {improvement_ratio:.2f}倍")
            
            if improvement_ratio > 1.2:
                print("🎉 修正版で大幅な改善が確認されました！")
            elif improvement_ratio > 1.0:
                print("✅ 修正版で改善が確認されました")
            else:
                print("⚠️ 修正版での改善が限定的です")
        
        # 5. チャンク分割テスト
        print("\n📊 テスト4: チャンク分割")
        print("-" * 40)
        
        if fixed_result:
            try:
                processor = DocumentProcessor()
                chunks = processor._split_text_into_chunks(fixed_result, excel_file_path)
                
                print(f"📄 生成チャンク数: {len(chunks)}")
                
                if chunks:
                    token_counts = [chunk["token_count"] for chunk in chunks]
                    avg_tokens = sum(token_counts) / len(token_counts)
                    min_tokens = min(token_counts)
                    max_tokens = max(token_counts)
                    
                    print(f"📊 トークン統計:")
                    print(f"  - 平均: {avg_tokens:.1f}")
                    print(f"  - 最小: {min_tokens}")
                    print(f"  - 最大: {max_tokens}")
                    
                    # 最初の3チャンクの内容を表示
                    print(f"\n📄 最初の3チャンクの内容:")
                    for i, chunk in enumerate(chunks[:3]):
                        print(f"チャンク{i}: {chunk['content'][:100]}...")
                
            except Exception as e:
                print(f"❌ チャンク分割テスト失敗: {e}")
        
        print("\n🎉 テスト完了")
        
    except FileNotFoundError:
        print(f"❌ ファイルが見つかりません: {excel_file_path}")
        print("💡 カレントディレクトリにファイルを配置してください")
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")

def compare_data_extraction():
    """
    データ抽出の詳細比較
    """
    print("\n🔍 データ抽出詳細比較")
    print("=" * 60)
    
    excel_file_path = "01_ISP案件一覧.xlsx"
    
    try:
        with open(excel_file_path, 'rb') as f:
            content = f.read()
        
        # 従来版と修正版の詳細比較
        original_cleaner = ExcelDataCleaner()
        fixed_cleaner = ExcelDataCleanerFixed()
        
        original_result = original_cleaner.clean_excel_data(content)
        fixed_result = fixed_cleaner.clean_excel_data(content)
        
        # キーワード検索による比較
        keywords = ["SS0", "ISP", "ステータス", "顧客情報", "獲得情報", "契約情報", "V付与済", "発行", "請求"]
        
        print("🔍 キーワード出現回数比較:")
        for keyword in keywords:
            original_count = original_result.count(keyword)
            fixed_count = fixed_result.count(keyword)
            improvement = fixed_count - original_count
            
            print(f"  {keyword}: 従来版={original_count}, 修正版={fixed_count}, 改善=+{improvement}")
        
        # 行数比較
        original_lines = len(original_result.split('\n'))
        fixed_lines = len(fixed_result.split('\n'))
        
        print(f"\n📊 行数比較:")
        print(f"  従来版: {original_lines}行")
        print(f"  修正版: {fixed_lines}行")
        print(f"  改善: +{fixed_lines - original_lines}行")
        
    except Exception as e:
        print(f"❌ 詳細比較エラー: {e}")

if __name__ == "__main__":
    print("🚀 Excel データ損失修正テストシステム")
    print("=" * 60)
    
    # 非同期テストを実行
    asyncio.run(test_excel_data_loss_fix())
    
    # 詳細比較
    compare_data_extraction()
    
    print("\n💡 修正内容:")
    print("1. データフィルタリング基準の大幅緩和")
    print("2. メタデータ除外ロジックの改善")
    print("3. ヘッダー検出の精度向上")
    print("4. ID・番号パターンの保護")
    print("5. DocumentProcessorでの修正版統合")
    
    print("\n📝 期待される改善:")
    print("- チャンク数の増加（より多くのデータ保持）")
    print("- 重要な識別子（SS番号、ISP番号等）の保持")
    print("- ステータス情報の完全保持")
    print("- 質問応答精度の向上")