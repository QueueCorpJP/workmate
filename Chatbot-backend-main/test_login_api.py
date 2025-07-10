#!/usr/bin/env python3
"""
実際のAPIエンドポイントでログインをテストするスクリプト
"""
import os
import json
import requests
import traceback
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def test_login_api():
    print("=== ログインAPIテスト開始 ===")
    
    # テスト用のデータ
    test_data = {
        "email": "shunya0619@gmail.com",
        "password": "Shun0619"
    }
    
    # FastAPIアプリケーションを起動する必要があるため、直接関数をテスト
    print("1. 直接関数テスト:")
    try:
        from modules.database import authenticate_user, get_usage_limits, SupabaseConnection
        from modules.validation import validate_login_input
        
        # 入力値バリデーション
        is_valid, errors = validate_login_input(test_data["email"], test_data["password"])
        print(f"  入力値バリデーション: {'✅ 成功' if is_valid else '❌ 失敗'}")
        if not is_valid:
            print(f"  エラー: {errors}")
        
        # 認証テスト
        db = SupabaseConnection()
        user = authenticate_user(test_data["email"], test_data["password"], db)
        
        if user:
            print(f"  認証テスト: ✅ 成功")
            print(f"  ユーザー: {user.get('name')} ({user.get('email')})")
            print(f"  ロール: {user.get('role')}")
            
            # 利用制限情報の取得
            limits = get_usage_limits(user["id"], db)
            print(f"  利用制限取得: {'✅ 成功' if limits else '❌ 失敗'}")
            if limits:
                print(f"    無制限: {limits.get('is_unlimited')}")
                print(f"    質問制限: {limits.get('questions_limit')}")
                print(f"    質問使用済み: {limits.get('questions_used')}")
                print(f"    ドキュメント制限: {limits.get('document_uploads_limit')}")
                print(f"    ドキュメント使用済み: {limits.get('document_uploads_used')}")
            
            # レスポンス形式の確認
            response_data = {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "role": user["role"],
                "company_id": user.get("company_id"),
                "company_name": user.get("company_name"),
                "limits": limits
            }
            
            print(f"  レスポンス形式: ✅ 正常")
            print(f"  レスポンス内容:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
        else:
            print(f"  認証テスト: ❌ 失敗")
            
    except Exception as e:
        print(f"  ❌ 直接関数テストエラー: {e}")
        print(traceback.format_exc())
    
    # 2. FastAPIアプリケーションの起動確認
    print("\n2. FastAPIアプリケーション起動確認:")
    try:
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # ログインエンドポイントのテスト
        response = client.post("/chatbot/api/auth/login", json=test_data)
        
        print(f"  ステータスコード: {response.status_code}")
        print(f"  レスポンス: {response.json()}")
        
        if response.status_code == 200:
            print("  ✅ ログインAPI成功")
        else:
            print("  ❌ ログインAPI失敗")
            
    except Exception as e:
        print(f"  ❌ FastAPIテストエラー: {e}")
        print(traceback.format_exc())
    
    # 3. 他のユーザーでのテスト
    print("\n3. 他のユーザーでのテスト:")
    try:
        from supabase_adapter import select_data
        
        # 他のユーザーを取得
        other_users_result = select_data("users", limit=5)
        
        if other_users_result.success and other_users_result.data:
            for user in other_users_result.data:
                if user.get('email') != 'shunya0619@gmail.com':
                    print(f"  ユーザー: {user.get('email')} ({user.get('name')})")
                    print(f"    ロール: {user.get('role')}")
                    print(f"    パスワード: {user.get('password')}")
                    
                    # 認証テスト
                    db = SupabaseConnection()
                    auth_result = authenticate_user(user.get('email'), user.get('password'), db)
                    print(f"    認証テスト: {'✅ 成功' if auth_result else '❌ 失敗'}")
                    print("    ---")
                    
    except Exception as e:
        print(f"  ❌ 他のユーザーテストエラー: {e}")
        print(traceback.format_exc())
    
    print("\n=== ログインAPIテスト終了 ===")

if __name__ == "__main__":
    test_login_api()