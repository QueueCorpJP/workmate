#!/usr/bin/env python3
"""
Supabaseクライアントの初期化問題を調査するスクリプト
"""
import os
import traceback
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def test_supabase_client_creation():
    print("=== Supabaseクライアント初期化テスト ===")
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ 環境変数が設定されていません")
        return
    
    # 1. 基本的なクライアント作成
    print("\n1. 基本的なクライアント作成:")
    try:
        from supabase import create_client, Client
        
        client = create_client(url, key)
        print("✅ 基本的なクライアント作成成功")
        
        # 簡単なクエリをテスト
        result = client.table('users').select('id').limit(1).execute()
        print(f"✅ 基本クエリ成功: {len(result.data)}件")
        
    except Exception as e:
        print(f"❌ 基本的なクライアント作成失敗: {e}")
        print(traceback.format_exc())
    
    # 2. ClientOptionsを使用したクライアント作成
    print("\n2. ClientOptionsを使用したクライアント作成:")
    try:
        from supabase import create_client, Client
        from supabase.client import ClientOptions
        
        options = ClientOptions(
            postgrest_client_timeout=10,
            storage_client_timeout=10,
        )
        
        client = create_client(url, key, options=options)
        print("✅ ClientOptionsを使用したクライアント作成成功")
        
        # 簡単なクエリをテスト
        result = client.table('users').select('id').limit(1).execute()
        print(f"✅ ClientOptionsクエリ成功: {len(result.data)}件")
        
    except Exception as e:
        print(f"❌ ClientOptionsを使用したクライアント作成失敗: {e}")
        print(traceback.format_exc())
    
    # 3. 現在のsupabase_adapterのget_supabase_client関数をテスト
    print("\n3. 現在のsupabase_adapterのget_supabase_client関数をテスト:")
    try:
        from supabase_adapter import get_supabase_client
        
        client = get_supabase_client()
        print("✅ supabase_adapterのget_supabase_client成功")
        
        # 簡単なクエリをテスト
        result = client.table('users').select('id').limit(1).execute()
        print(f"✅ supabase_adapterクエリ成功: {len(result.data)}件")
        
    except Exception as e:
        print(f"❌ supabase_adapterのget_supabase_client失敗: {e}")
        print(traceback.format_exc())
    
    # 4. Supabase環境の詳細情報を表示
    print("\n4. Supabase環境の詳細情報:")
    try:
        import supabase
        print(f"Supabaseバージョン: {supabase.__version__}")
        
        # Supabaseクライアントの詳細情報
        from supabase import create_client
        client = create_client(url, key)
        print(f"Supabase URL: {client.supabase_url}")
        print(f"Supabase Key: {'設定済み' if client.supabase_key else '未設定'}")
        
    except Exception as e:
        print(f"❌ Supabase環境情報取得失敗: {e}")
        print(traceback.format_exc())
    
    # 5. 認証テスト
    print("\n5. 認証テスト:")
    try:
        from supabase import create_client
        
        client = create_client(url, key)
        
        # 匿名認証テスト
        # auth_response = client.auth.sign_in_anonymously()
        # print(f"匿名認証: {auth_response}")
        
        # 現在のセッション情報
        session = client.auth.get_session()
        print(f"現在のセッション: {session}")
        
        user = client.auth.get_user()
        print(f"現在のユーザー: {user}")
        
    except Exception as e:
        print(f"❌ 認証テスト失敗: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_supabase_client_creation()