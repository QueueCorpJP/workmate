"""
Google OAuth2認証モジュール
組織ポリシーでサービスアカウントキー作成が制限されている場合の代替手段
"""
import os
import json
import logging
from typing import Optional, Dict
from urllib.parse import urlencode, parse_qs, urlparse
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

class GoogleOAuth2Manager:
    """Google OAuth2認証管理クラス"""
    
    def __init__(self):
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8080/callback')
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
    
    def get_authorization_url(self) -> str:
        """認証URLを生成"""
        if not self.client_id:
            raise ValueError("GOOGLE_CLIENT_IDが設定されていません")
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes),
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
        logger.info(f"認証URL生成: {auth_url}")
        return auth_url
    
    def exchange_code_for_tokens(self, authorization_code: str) -> Dict:
        """認証コードをアクセストークンに交換"""
        if not all([self.client_id, self.client_secret]):
            raise ValueError("Google OAuth2の設定が不完全です")
        
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': authorization_code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            tokens = response.json()
            
            logger.info("アクセストークン取得成功")
            return tokens
            
        except requests.RequestException as e:
            logger.error(f"トークン交換エラー: {str(e)}")
            raise
    
    def refresh_access_token(self, refresh_token: str) -> Dict:
        """リフレッシュトークンを使用してアクセストークンを更新"""
        if not all([self.client_id, self.client_secret]):
            raise ValueError("Google OAuth2の設定が不完全です")
        
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            tokens = response.json()
            
            logger.info("アクセストークン更新成功")
            return tokens
            
        except requests.RequestException as e:
            logger.error(f"トークン更新エラー: {str(e)}")
            raise
    
    def get_credentials_from_tokens(self, tokens: Dict) -> Credentials:
        """トークンからCredentialsオブジェクトを作成"""
        return Credentials(
            token=tokens.get('access_token'),
            refresh_token=tokens.get('refresh_token'),
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.scopes
        )

# グローバルインスタンス
oauth2_manager = GoogleOAuth2Manager()

def get_oauth2_authorization_url() -> str:
    """OAuth2認証URLを取得"""
    return oauth2_manager.get_authorization_url()

def process_oauth2_callback(authorization_code: str) -> Dict:
    """OAuth2コールバックを処理"""
    return oauth2_manager.exchange_code_for_tokens(authorization_code)

def get_google_sheets_credentials(access_token: str, refresh_token: str = None) -> Credentials:
    """Google Sheets用のCredentialsを取得"""
    tokens = {
        'access_token': access_token,
        'refresh_token': refresh_token
    }
    return oauth2_manager.get_credentials_from_tokens(tokens)

class GoogleTokenStorage:
    """トークンの永続化管理クラス"""
    
    def __init__(self, storage_file: str = "google_tokens.json"):
        self.storage_file = storage_file
    
    def save_tokens(self, user_id: str, tokens: Dict) -> None:
        """ユーザーのトークンを保存"""
        try:
            # 既存のトークンファイルを読み込み
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    all_tokens = json.load(f)
            else:
                all_tokens = {}
            
            # ユーザーのトークンを更新
            all_tokens[user_id] = tokens
            
            # ファイルに保存
            with open(self.storage_file, 'w') as f:
                json.dump(all_tokens, f, indent=2)
            
            logger.info(f"ユーザー {user_id} のトークンを保存")
            
        except Exception as e:
            logger.error(f"トークン保存エラー: {str(e)}")
            raise
    
    def load_tokens(self, user_id: str) -> Optional[Dict]:
        """ユーザーのトークンを読み込み"""
        try:
            if not os.path.exists(self.storage_file):
                return None
            
            with open(self.storage_file, 'r') as f:
                all_tokens = json.load(f)
            
            return all_tokens.get(user_id)
            
        except Exception as e:
            logger.error(f"トークン読み込みエラー: {str(e)}")
            return None
    
    def refresh_user_tokens(self, user_id: str) -> Optional[Dict]:
        """ユーザーのトークンを更新"""
        try:
            tokens = self.load_tokens(user_id)
            if not tokens or 'refresh_token' not in tokens:
                return None
            
            # リフレッシュトークンでアクセストークンを更新
            new_tokens = oauth2_manager.refresh_access_token(tokens['refresh_token'])
            
            # 新しいトークンを保存
            updated_tokens = {**tokens, **new_tokens}
            self.save_tokens(user_id, updated_tokens)
            
            return updated_tokens
            
        except Exception as e:
            logger.error(f"トークン更新エラー: {str(e)}")
            return None

# グローバルトークンストレージ
token_storage = GoogleTokenStorage()