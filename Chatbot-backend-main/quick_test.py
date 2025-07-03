#!/usr/bin/env python3
"""
非対話的メール送信テスト
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
logging.basicConfig(level=logging.INFO)

def test_email():
    """メール送信テスト"""
    print("🚀 WorkMate メール送信テスト開始")
    
    try:
        from modules.email_service import email_service
        
        # 環境変数チェック
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")  
        resend_api_key = os.getenv("RESEND_API_KEY")
        
        print(f"SUPABASE_URL: {'✅' if supabase_url else '❌'}")
        print(f"SUPABASE_KEY: {'✅' if supabase_key else '❌'}")
        print(f"RESEND_API_KEY: {'✅' if resend_api_key else '❌'}")
        
        # テストメール送信（Resendのテストモードでは登録済みアドレスのみ）
        test_email = "queue@queue-tech.jp"
        print(f"📧 テストメール送信: {test_email}")
        
        result = email_service.send_account_creation_email(
            user_email=test_email,
            user_name="関口俊哉",
            password="TestPassword123",
            role="user"
        )
        
        if result:
            print("✅ メール送信成功！")
        else:
            print("❌ メール送信失敗")
            
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email() 