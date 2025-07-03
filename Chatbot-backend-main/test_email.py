#!/usr/bin/env python3
"""
メール送信機能テストスクリプト
アカウント作成メール送信をテストします
"""

import os
import sys
import logging
from dotenv import load_dotenv

# モジュールパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# 環境変数読み込み
load_dotenv()

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_email_service():
    """メール送信サービステスト"""
    print("=" * 50)
    print("📧 WorkMate メール送信機能テスト")
    print("=" * 50)
    
    try:
        from modules.email_service import email_service
        
        # 環境変数チェック
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        resend_api_key = os.getenv("RESEND_API_KEY")
        
        print("🔍 環境変数チェック:")
        print(f"  SUPABASE_URL: {'✅ 設定済み' if supabase_url else '❌ 未設定'}")
        print(f"  SUPABASE_KEY: {'✅ 設定済み' if supabase_key else '❌ 未設定'}")
        print(f"  RESEND_API_KEY: {'✅ 設定済み' if resend_api_key else '❌ 未設定'}")
        print()
        
        if not (supabase_url or resend_api_key):
            print("❌ メール送信に必要な環境変数が設定されていません")
            return
        
        # テストメール送信
        test_email = input("📧 テストメールを送信するメールアドレスを入力してください: ").strip()
        
        if not test_email:
            print("❌ メールアドレスが入力されていません")
            return
            
        print(f"📧 テストメール送信中: {test_email}")
        print("⏳ 送信中...")
        
        result = email_service.send_account_creation_email(
            user_email=test_email,
            user_name="テストユーザー",
            password="TestPassword123",
            role="user"
        )
        
        if result:
            print("✅ メール送信成功！")
            print(f"📧 {test_email} にアカウント作成メールを送信しました")
        else:
            print("❌ メール送信失敗")
            print("🔍 ログを確認してください")
            
    except ImportError as e:
        print(f"❌ モジュールインポートエラー: {str(e)}")
        print("💡 modules/email_service.py が正しく作成されているか確認してください")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        print("🔍 詳細なエラー情報:")
        import traceback
        traceback.print_exc()

def test_auth_integration():
    """認証モジュール統合テスト"""
    print("\n" + "=" * 50)
    print("🔐 認証モジュール統合テスト")
    print("=" * 50)
    
    try:
        from modules.auth import register_new_user
        from modules.database import SupabaseConnection
        
        print("✅ 認証モジュールのインポート成功")
        print("💡 実際のユーザー登録は手動でテストしてください")
        
    except ImportError as e:
        print(f"❌ 認証モジュールインポートエラー: {str(e)}")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    print("🚀 WorkMate メール送信機能テスト開始")
    print()
    
    # メール送信サービステスト
    test_email_service()
    
    # 認証モジュール統合テスト
    test_auth_integration()
    
    print("\n" + "=" * 50)
    print("🎉 テスト完了")
    print("=" * 50)
    print()
    print("📝 次のステップ:")
    print("1. Supabaseダッシュボードでプロジェクト設定 > Edge Functions > 環境変数を設定")
    print("   - RESEND_API_KEY: your_resend_api_key")
    print("   - FRONTEND_URL: https://workmatechat.com")
    print()
    print("2. フロントエンドでアカウント作成をテスト")
    print("3. メールが正常に送信されることを確認")
    print()
    print("🎯 実装完了！") 