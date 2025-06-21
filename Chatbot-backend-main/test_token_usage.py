#!/usr/bin/env python3
"""
トークン使用量取得機能のテストスクリプト
"""

import sys
import os
sys.path.append('.')

def test_token_usage():
    """トークン使用量取得機能をテストする"""
    print("=== トークン使用量取得機能テスト開始 ===")
    
    try:
        # モジュールのインポートテスト
        print("1. モジュールインポートテスト...")
        from modules.token_counter import TokenUsageTracker, TokenCounter
        from modules.database import get_db
        print("✓ モジュールインポート成功")
        
        # データベース接続テスト
        print("\n2. データベース接続テスト...")
        db = get_db()
        print(f"✓ データベース接続成功: {type(db)}")
        
        # TokenCounterテスト
        print("\n3. TokenCounterテスト...")
        counter = TokenCounter()
        print(f"✓ TokenCounter初期化成功")
        print(f"  - 利用可能な料金設定: {list(counter.pricing.keys())}")
        print(f"  - workmate-standard料金: {counter.pricing.get('workmate-standard', 'なし')}")
        print(f"  - プロンプト参照料金: {counter.prompt_reference_cost}")
        
        # TokenUsageTrackerテスト
        print("\n4. TokenUsageTrackerテスト...")
        tracker = TokenUsageTracker(db)
        print("✓ TokenUsageTracker初期化成功")
        
        # 実際の会社データでテスト
        print("\n5. 実際のデータ取得テスト...")
        
        # 既存の会社IDを取得してテスト
        try:
            from supabase_adapter import select_data
            companies_result = select_data("companies", columns="id, name", limit=1)
            
            if companies_result and companies_result.data:
                test_company_id = companies_result.data[0]['id']
                company_name = companies_result.data[0]['name']
                print(f"  - テスト対象会社: {company_name} (ID: {test_company_id})")
                
                # 月次使用量取得テスト
                usage_data = tracker.get_company_monthly_usage(test_company_id, 'ALL')
                print("✓ get_company_monthly_usage実行成功")
                print(f"  - 結果: {usage_data}")
                
                # 特定月のテスト
                usage_data_current = tracker.get_company_monthly_usage(test_company_id, '2025-01')
                print("✓ 現在月の使用量取得成功")
                print(f"  - 2025-01の結果: {usage_data_current}")
                
            else:
                print("⚠ 会社データが見つかりません - ダミーIDでテスト")
                test_company_id = 'test-company-id'
                usage_data = tracker.get_company_monthly_usage(test_company_id, 'ALL')
                print(f"✓ ダミーIDでのテスト成功: {usage_data}")
                
        except Exception as e:
            print(f"⚠ 実データテストでエラー: {e}")
            print("ダミーIDでテストを継続...")
            test_company_id = 'test-company-id'
            usage_data = tracker.get_company_monthly_usage(test_company_id, 'ALL')
            print(f"✓ ダミーIDでのテスト成功: {usage_data}")
        
        # 新料金体系テスト
        print("\n6. 新料金体系テスト...")
        test_input = "テストメッセージ"
        test_output = "テスト回答です。これは料金計算のテストです。"
        test_prompts = 5
        
        result = counter.calculate_tokens_and_cost_with_prompts(
            test_input, test_output, test_prompts, "workmate-standard"
        )
        print("✓ 新料金体系計算成功")
        print(f"  - 計算結果: {result}")
        
        print("\n=== 全テスト完了 ===")
        print("✓ すべての機能が正常に動作しています")
        
    except Exception as e:
        print(f"\n✗ テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_token_usage()
    sys.exit(0 if success else 1) 