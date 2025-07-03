"""
メール送信サービスモジュール
Supabase Edge FunctionとResend APIを使用したアカウント作成通知
"""

import os
import logging
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class EmailService:
    """メール送信サービス"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.resend_api_key = os.getenv("RESEND_API_KEY")
        
        # Resend APIのみ使用（開発用に認証済みドメインに変更）
        self.from_email = "onboarding@resend.dev"
        self.frontend_url = os.getenv("FRONTEND_URL", "https://workmatechat.com")
        
    def send_account_creation_email(self, 
                                  user_email: str, 
                                  user_name: str, 
                                  password: str, 
                                  role: str = "user") -> bool:
        """
        アカウント作成通知メールを送信
        
        Args:
            user_email: 送信先メールアドレス
            user_name: ユーザー名
            password: 作成されたパスワード
            role: ユーザーロール
            
        Returns:
            bool: 送信成功時True
        """
        try:
            # Resend API一本化
            if self.resend_api_key:
                logger.info("Resend API経由でメール送信を試行")
                return self._send_via_resend_api(user_email, user_name, password, role)
            else:
                logger.error("RESEND_API_KEY が未設定です。メール送信不可。")
                return False
                
        except Exception as e:
            logger.error(f"メール送信エラー: {str(e)}")
            return False
    
    def _send_via_resend_api(self, user_email: str, user_name: str, password: str, role: str) -> bool:
        """直接Resend API経由でメール送信（フォールバック）"""
        try:
            role_display = {
                "admin": "管理者",
                "admin_user": "管理者ユーザー",
                "user": "ユーザー",
                "employee": "従業員"
            }.get(role, "ユーザー")
            
            # 改良版HTMLメールコンテンツ
            html_content = f"""
            <!DOCTYPE html>
            <html lang=\"ja\">
            <head>
              <meta charset=\"UTF-8\">
              <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
              <title>WorkMate アカウント発行のご案内</title>
            </head>
            <body style=\"font-family:-apple-system, BlinkMacSystemFont, 'Hiragino Kaku Gothic ProN', Meiryo, sans-serif; background:#f4f6f8; margin:0; padding:0;\">
              <table width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"background:#f4f6f8; padding:24px 0;\">
                <tr>
                  <td align=\"center\">
                    <table width=\"600\" cellpadding=\"0\" cellspacing=\"0\" style=\"background:#ffffff; border-radius:8px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.05);\">
                      <tr>
                        <td style=\"background:#4CAF50; padding:32px; text-align:center; color:#ffffff;\">
                          <h1 style=\"margin:0; font-size:24px;\">WorkMate アカウント発行のご案内</h1>
                        </td>
                      </tr>
                      <tr>
                        <td style=\"padding:32px; color:#333333; line-height:1.7; font-size:15px;\">
                          <p style=\"margin-top:0;\"><strong>{user_name} 様</strong></p>
                          <p><strong>WorkMateチャットボット</strong> にご登録されました。<br>
                          下記の内容でアカウントを発行いたしましたので、ご確認ください。</p>
                          
                          <div style=\"background:#f8f9fa; border:1px solid #e0e0e0; border-radius:6px; padding:20px; margin:24px 0;\">
                            <h3 style=\"margin-top:0; font-size:17px; color:#2c3e50;\">ログイン情報</h3>
                            <table style=\"font-size:14px; width:100%;\">
                              <tr><td style=\"padding:6px 0; width:120px;\"><strong>メールアドレス</strong></td><td>{user_email}</td></tr>
                              <tr><td style=\"padding:6px 0;\"><strong>初期パスワード</strong></td><td>{password}</td></tr>
                              <tr><td style=\"padding:6px 0;\"><strong>権限</strong></td><td>{role_display}</td></tr>
                            </table>
                          </div>

                          <p style=\"text-align:center;\">
                            <a href=\"{self.frontend_url}\" style=\"display:inline-block; background:#4CAF50; color:#ffffff; padding:14px 32px; text-decoration:none; border-radius:4px; font-weight:bold;\">ログインページへ</a>
                          </p>

                          <p style=\"margin-bottom:0;\"><strong>⚠️ セキュリティのお願い</strong><br>
                          ・本メールは大切に保管し、第三者へ共有しないようお願いいたします。</p>
                        </td>
                      </tr>
                      <tr>
                        <td style=\"background:#f1f1f1; padding:20px; text-align:center; font-size:12px; color:#6b6b6b;\">
                          WorkMate 運営チーム&nbsp;|&nbsp;{self.from_email}
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </body>
            </html>
            """
            
            payload = {
                "from": f"WorkMate <{self.from_email}>",
                "to": [user_email],
                "subject": "【WorkMate】アカウント発行のご案内",
                "html": html_content
            }
            
            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {self.resend_api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Resend API経由でメール送信成功: {user_email}")
                return True
            else:
                logger.error(f"Resend API経由メール送信失敗: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Resend API経由メール送信エラー: {str(e)}")
            return False

# シングルトンインスタンス
email_service = EmailService() 