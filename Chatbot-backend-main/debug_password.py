#!/usr/bin/env python3
"""
パスワードの実際の値を調査するスクリプト
"""
import os
import traceback
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def debug_password():
    print("=== パスワード調査開始 ===")
    
    try:
        from supabase_adapter import select_data
        
        # 特定ユーザーの詳細情報を取得
        target_email = "shunya0619@gmail.com"
        result = select_data("users", filters={"email": target_email})
        
        if result.success and result.data:
            user = result.data[0]
            print(f"ユーザー情報:")
            print(f"  Email: {user.get('email')}")
            print(f"  Name: {user.get('name')}")
            print(f"  Role: {user.get('role')}")
            print(f"  Password: '{user.get('password')}'")
            print(f"  Password Length: {len(user.get('password', ''))}")
            print(f"  Password Type: {type(user.get('password'))}")
            
            # パスワードの文字コードを確認
            password = user.get('password', '')
            print(f"  Password Bytes: {password.encode('utf-8')}")
            print(f"  Password Repr: {repr(password)}")
            
            # 認証テスト
            print("\n認証テスト:")
            from modules.database import authenticate_user, SupabaseConnection
            
            db = SupabaseConnection()
            
            # 実際のパスワードで認証テスト
            auth_result = authenticate_user(target_email, password, db)
            
            if auth_result:
                print(f"✅ 認証成功: {target_email}")
                print(f"  認証結果: {auth_result}")
            else:
                print(f"❌ 認証失敗: {target_email}")
                
                # パスワードの詳細な比較
                print(f"\n詳細なパスワード比較:")
                print(f"  入力パスワード: '{password}'")
                print(f"  入力パスワードの型: {type(password)}")
                print(f"  入力パスワードの長さ: {len(password)}")
                
                # 実際の認証処理を再実行して詳細確認
                user_result = select_data("users", filters={"email": target_email})
                if user_result.success and user_result.data:
                    stored_user = user_result.data[0]
                    stored_password = stored_user.get("password")
                    print(f"  保存されたパスワード: '{stored_password}'")
                    print(f"  保存されたパスワードの型: {type(stored_password)}")
                    print(f"  保存されたパスワードの長さ: {len(stored_password)}")
                    print(f"  パスワード一致: {stored_password == password}")
                    
                    # 文字単位で比較
                    if stored_password != password:
                        print(f"  詳細比較:")
                        for i, (c1, c2) in enumerate(zip(stored_password, password)):
                            if c1 != c2:
                                print(f"    位置{i}: '{c1}' != '{c2}'")
                                break
                        else:
                            print(f"    長さが異なります: {len(stored_password)} vs {len(password)}")
            
        else:
            print(f"❌ ユーザーが見つかりません: {target_email}")
            
    except Exception as e:
        print(f"❌ パスワード調査エラー: {e}")
        print(traceback.format_exc())
    
    print("\n=== パスワード調査終了 ===")

if __name__ == "__main__":
    debug_password()