#!/usr/bin/env python3
"""
shunya0619@gmail.comの利用制限情報を調査するスクリプト
"""
import os
import traceback
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def debug_usage_limits():
    print("=== 利用制限調査開始 ===")
    
    try:
        from supabase_adapter import select_data
        from modules.database import get_usage_limits, SupabaseConnection
        
        # 対象ユーザーの基本情報
        target_email = "shunya0619@gmail.com"
        result = select_data("users", filters={"email": target_email})
        
        if result.success and result.data:
            user = result.data[0]
            user_id = user.get('id')
            
            print(f"ユーザー情報:")
            print(f"  Email: {user.get('email')}")
            print(f"  Name: {user.get('name')}")
            print(f"  Role: {user.get('role')}")
            print(f"  User ID: {user_id}")
            print(f"  Company ID: {user.get('company_id')}")
            
            # 利用制限情報の取得
            print(f"\n利用制限情報:")
            db = SupabaseConnection()
            limits = get_usage_limits(user_id, db)
            
            if limits:
                print(f"  Found: Yes")
                print(f"  User ID: {limits.get('user_id')}")
                print(f"  Is Unlimited: {limits.get('is_unlimited')}")
                print(f"  Questions Used: {limits.get('questions_used')}")
                print(f"  Questions Limit: {limits.get('questions_limit')}")
                print(f"  Documents Used: {limits.get('document_uploads_used')}")
                print(f"  Documents Limit: {limits.get('document_uploads_limit')}")
            else:
                print(f"  Found: No")
                print(f"  利用制限情報が見つかりません")
                
                # 利用制限テーブルの全レコードを確認
                print(f"\n全利用制限レコード:")
                all_limits_result = select_data("usage_limits")
                if all_limits_result.success and all_limits_result.data:
                    print(f"  Total Records: {len(all_limits_result.data)}")
                    for i, limit in enumerate(all_limits_result.data):
                        print(f"    {i+1}. User ID: {limit.get('user_id')}")
                        print(f"       Is Unlimited: {limit.get('is_unlimited')}")
                        print(f"       Questions: {limit.get('questions_used')}/{limit.get('questions_limit')}")
                        print(f"       Documents: {limit.get('document_uploads_used')}/{limit.get('document_uploads_limit')}")
                        print()
                
                # 利用制限レコードを自動作成
                print(f"\n利用制限レコード自動作成:")
                try:
                    from modules.utils import create_default_usage_limits
                    from supabase_adapter import insert_data
                    
                    # デフォルト利用制限を作成
                    default_limits = create_default_usage_limits(user_id, user.get('email'), user.get('role'))
                    print(f"  デフォルト利用制限: {default_limits}")
                    
                    # データベースに挿入
                    insert_result = insert_data("usage_limits", default_limits)
                    if insert_result.success:
                        print(f"  ✅ 利用制限レコード作成成功")
                        
                        # 再度取得して確認
                        limits = get_usage_limits(user_id, db)
                        if limits:
                            print(f"  確認: 利用制限情報が正常に作成されました")
                            print(f"    Is Unlimited: {limits.get('is_unlimited')}")
                            print(f"    Questions Limit: {limits.get('questions_limit')}")
                            print(f"    Documents Limit: {limits.get('document_uploads_limit')}")
                        else:
                            print(f"  ❌ 作成したはずの利用制限情報が見つかりません")
                    else:
                        print(f"  ❌ 利用制限レコード作成失敗: {insert_result.error}")
                        
                except Exception as e:
                    print(f"  ❌ 利用制限レコード作成エラー: {e}")
                    print(traceback.format_exc())
        else:
            print(f"❌ ユーザーが見つかりません: {target_email}")
            
    except Exception as e:
        print(f"❌ 利用制限調査エラー: {e}")
        print(traceback.format_exc())
    
    print("\n=== 利用制限調査終了 ===")

if __name__ == "__main__":
    debug_usage_limits()