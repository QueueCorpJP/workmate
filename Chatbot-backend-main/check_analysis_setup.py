#!/usr/bin/env python3
"""
分析機能の設定状況確認スクリプト
"""

import os
from dotenv import load_dotenv

def check_analysis_setup():
    print("🔍 分析機能設定確認")
    print("=" * 50)
    
    # .envファイルの確認
    env_file = ".env"
    if os.path.exists(env_file):
        print("✅ .envファイルが存在します")
        load_dotenv()
    else:
        print("❌ .envファイルが存在しません")
        print("💡 .envファイルを作成してください")
        return False
    
    # 必要な環境変数の確認
    required_vars = {
        "GOOGLE_API_KEY": "Gemini API キー",
        "SUPABASE_URL": "Supabase URL",
        "SUPABASE_KEY": "Supabase API キー", 
        "DB_PASSWORD": "データベースパスワード (分析機能に必要)",
        "DATABASE_URL": "データベースURL"
    }
    
    all_set = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: 設定済み")
        else:
            print(f"❌ {var}: 未設定 ({description})")
            all_set = False
    
    print("\n" + "=" * 50)
    
    if all_set:
        print("✅ すべての環境変数が設定されています")
        print("💡 次のステップ:")
        print("   1. python main.py でバックエンドサーバーを起動")
        print("   2. フロントエンドで分析ページにアクセス")
        return True
    else:
        print("❌ 環境変数の設定が不完全です")
        print("💡 .envファイルに正しい値を設定してください")
        return False

if __name__ == "__main__":
    check_analysis_setup() 