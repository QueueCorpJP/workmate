"""
GCP認証モジュール
ワークロードアイデンティティやCompute Engine認証を使用
"""
import os
import logging
from typing import Optional
from google.auth import default
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

def get_default_credentials_service():
    """
    デフォルト認証情報を使用してGoogle Sheets APIサービスを取得
    以下の順序で認証を試行：
    1. GOOGLE_APPLICATION_CREDENTIALS環境変数
    2. gcloud認証
    3. Compute Engine メタデータサーバー
    4. ワークロードアイデンティティ
    """
    try:
        # デフォルト認証情報を取得
        credentials, project = default(
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive.file'
            ]
        )
        
        # 認証情報が有効かチェック
        if not credentials.valid:
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                logger.error("認証情報が無効です")
                return None
        
        # Google Sheets APIサービスを構築
        service = build('sheets', 'v4', credentials=credentials)
        logger.info(f"デフォルト認証でGoogle Sheets APIサービスを取得（プロジェクト: {project}）")
        
        return service
        
    except Exception as e:
        logger.error(f"デフォルト認証エラー: {str(e)}")
        return None

def get_gcp_metadata_token():
    """
    GCP Compute Engineメタデータサーバーからアクセストークンを取得
    """
    try:
        import requests
        
        # メタデータサーバーからトークンを取得
        metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
        headers = {"Metadata-Flavor": "Google"}
        
        response = requests.get(metadata_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        
        if access_token:
            logger.info("GCPメタデータサーバーからアクセストークンを取得")
            return access_token
        else:
            logger.error("メタデータサーバーからトークンを取得できませんでした")
            return None
            
    except Exception as e:
        logger.error(f"GCPメタデータサーバー認証エラー: {str(e)}")
        return None

def is_running_on_gcp():
    """
    GCP環境で実行されているかチェック
    """
    try:
        import requests
        
        # メタデータサーバーへの接続テスト
        metadata_url = "http://metadata.google.internal/computeMetadata/v1/"
        headers = {"Metadata-Flavor": "Google"}
        
        response = requests.get(metadata_url, headers=headers, timeout=5)
        return response.status_code == 200
        
    except:
        return False

async def get_sheets_service_with_default_auth():
    """
    デフォルト認証を使用してGoogle Sheets APIサービスを非同期で取得
    """
    import asyncio
    
    def get_service():
        return get_default_credentials_service()
    
    return await asyncio.to_thread(get_service)

# 設定チェック関数
def check_gcp_auth_setup():
    """
    GCP認証の設定状況をチェック
    """
    setup_status = {
        'gcp_environment': is_running_on_gcp(),
        'application_credentials': bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS')),
        'default_credentials_available': False,
        'metadata_server_accessible': False
    }
    
    try:
        # デフォルト認証情報の確認
        credentials, project = default()
        setup_status['default_credentials_available'] = True
        setup_status['project_id'] = project
    except Exception as e:
        logger.warning(f"デフォルト認証情報が利用できません: {str(e)}")
    
    if setup_status['gcp_environment']:
        try:
            token = get_gcp_metadata_token()
            setup_status['metadata_server_accessible'] = bool(token)
        except:
            pass
    
    return setup_status