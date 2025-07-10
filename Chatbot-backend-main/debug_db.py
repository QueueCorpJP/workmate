#!/usr/bin/env python3
"""
データベースの状態を確認するためのデバッグスクリプト
"""
import os
import sys
import traceback
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def main():
    print("=== データベース診断開始 ===")
    
    # 1. 環境変数の確認
    print("\n1. 環境変数の確認:")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    print(f"SUPABASE_URL: {supabase_url}")
    print(f"SUPABASE_KEY: {'設定済み' if supabase_key else '未設定'}")
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase設定が不完全です")
        return
    
    # 2. Supabaseクライアントの初期化テスト
    print("\n2. Supabaseクライアント初期化テスト:")
    try:
        from supabase_adapter import get_supabase_client, test_connection
        
        # クライアント初期化
        client = get_supabase_client()
        print("✅ Supabaseクライアント初期化成功")
        
        # 接続テスト
        connection_ok = test_connection()
        print(f"接続テスト: {'✅ 成功' if connection_ok else '❌ 失敗'}")
        
    except Exception as e:
        print(f"❌ Supabaseクライアント初期化エラー: {e}")
        print(traceback.format_exc())
        return
    
    # 3. usersテーブルの構造確認
    print("\n3. usersテーブルの構造確認:")
    try:
        from supabase_adapter import select_data
        
        # 少数のレコードを取得してテーブル構造を確認
        result = select_data("users", limit=1)
        if result.success and result.data:
            print(f"✅ usersテーブル: {len(result.data)}件のデータ")
            if result.data:
                print("カラム:", list(result.data[0].keys()))
        else:
            print(f"❌ usersテーブルアクセスエラー: {result.error}")
            
    except Exception as e:
        print(f"❌ usersテーブル確認エラー: {e}")
        print(traceback.format_exc())
    
    # 4. 特定ユーザー（shunya0619@gmail.com）の検索
    print("\n4. 特定ユーザーの検索:")
    try:
        from supabase_adapter import select_data
        
        target_email = "shunya0619@gmail.com"
        result = select_data("users", filters={"email": target_email})
        
        if result.success:
            if result.data:
                user = result.data[0]
                print(f"✅ ユーザー見つかりました: {target_email}")
                print(f"   ID: {user.get('id')}")
                print(f"   名前: {user.get('name')}")
                print(f"   ロール: {user.get('role')}")
                print(f"   会社ID: {user.get('company_id')}")
                print(f"   作成日: {user.get('created_at')}")
                
                # パスワードハッシュの確認
                password = user.get('password')
                if password:
                    print(f"   パスワード: 設定済み (長さ: {len(password)})")
                else:
                    print("   パスワード: 未設定")
                    
            else:
                print(f"❌ ユーザーが見つかりません: {target_email}")
        else:
            print(f"❌ ユーザー検索エラー: {result.error}")
            
    except Exception as e:
        print(f"❌ ユーザー検索エラー: {e}")
        print(traceback.format_exc())
    
    # 5. 全ユーザーの一覧表示
    print("\n5. 全ユーザーの一覧:")
    try:
        from supabase_adapter import select_data
        
        result = select_data("users", columns="id, email, name, role, company_id, created_at")
        
        if result.success and result.data:
            print(f"✅ 総ユーザー数: {len(result.data)}")
            for i, user in enumerate(result.data[:10]):  # 最初の10件のみ表示
                print(f"   {i+1}. {user.get('email')} ({user.get('name')}) - {user.get('role')}")
                
            if len(result.data) > 10:
                print(f"   ... 他{len(result.data) - 10}件")
        else:
            print(f"❌ ユーザー一覧取得エラー: {result.error}")
            
    except Exception as e:
        print(f"❌ ユーザー一覧取得エラー: {e}")
        print(traceback.format_exc())
    
    # 6. 認証テスト
    print("\n6. 認証テスト:")
    try:
        from modules.database import authenticate_user, SupabaseConnection
        
        # テスト用の接続を作成
        db = SupabaseConnection()
        
        # 認証テスト
        target_email = "shunya0619@gmail.com"
        # 実際のパスワードは分からないため、まず空のパスワードでテスト
        test_passwords = ["", "password", "test", "123456"]
        
        for password in test_passwords:
            try:
                user = authenticate_user(target_email, password, db)
                if user:
                    print(f"✅ 認証成功: {target_email} / パスワード: '{password}'")
                    break
                else:
                    print(f"❌ 認証失敗: {target_email} / パスワード: '{password}'")
            except Exception as auth_error:
                print(f"❌ 認証エラー: {target_email} / パスワード: '{password}' - {auth_error}")
                
    except Exception as e:
        print(f"❌ 認証テストエラー: {e}")
        print(traceback.format_exc())
    
    # 7. 利用制限テーブルの確認
    print("\n7. 利用制限テーブルの確認:")
    try:
        from supabase_adapter import select_data
        
        result = select_data("usage_limits", limit=5)
        
        if result.success and result.data:
            print(f"✅ usage_limits テーブル: {len(result.data)}件のデータ")
            for limit in result.data:
                print(f"   ユーザーID: {limit.get('user_id')}")
                print(f"   無制限: {limit.get('is_unlimited')}")
                print(f"   質問制限: {limit.get('questions_limit')}")
                print(f"   質問使用済み: {limit.get('questions_used')}")
                print("   ---")
        else:
            print(f"❌ usage_limits テーブルアクセスエラー: {result.error}")
            
    except Exception as e:
        print(f"❌ usage_limits テーブル確認エラー: {e}")
        print(traceback.format_exc())
    
    # 8. 直接SQLテスト
    print("\n8. 直接SQLテスト:")
    try:
        client = get_supabase_client()
        
        # 直接Supabaseクライアントを使用してクエリを実行
        response = client.table("users").select("email, name").eq("email", "shunya0619@gmail.com").execute()
        
        if response.data:
            print("✅ 直接SQLクエリ成功")
            print(f"   結果: {response.data}")
        else:
            print("❌ 直接SQLクエリ: データなし")
            
    except Exception as e:
        print(f"❌ 直接SQLテストエラー: {e}")
        print(traceback.format_exc())
    
    print("\n=== データベース診断完了 ===")

if __name__ == "__main__":
    main()