"""
Google Drive連携処理モジュール
Google Drive APIを使用してファイルのダウンロードと処理を行います
"""
import io
import os
import tempfile
import logging
import asyncio
from typing import Optional, Dict, Any, List
import aiohttp
import aiofiles

# ロガーの設定
logger = logging.getLogger(__name__)

class GoogleDriveHandler:
    """Google Drive API処理ハンドラー"""
    
    def __init__(self):
        self.base_url = os.getenv("GOOGLE_DRIVE_API_BASE_URL", "https://www.googleapis.com/drive/v3")
        self.download_url = os.getenv("GOOGLE_DRIVE_FILES_URL", "https://www.googleapis.com/drive/v3/files")
    
    async def get_file_metadata(self, file_id: str, access_token: str) -> Optional[Dict[str, Any]]:
        """
        ファイルメタデータを取得
        
        Args:
            file_id: Google DriveファイルID
            access_token: アクセストークン
            
        Returns:
            ファイルメタデータまたはNone
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
            
            url = f"{self.base_url}/files/{file_id}"
            params = {
                'fields': 'id,name,mimeType,size,modifiedTime,webViewLink'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        metadata = await response.json()
                        logger.info(f"ファイルメタデータ取得成功: {metadata['name']}")
                        return metadata
                    else:
                        logger.error(f"メタデータ取得エラー: {response.status} - {await response.text()}")
                        return None
                        
        except Exception as e:
            logger.error(f"メタデータ取得中のエラー: {str(e)}")
            return None
    
    async def download_file(self, file_id: str, access_token: str, mime_type: str) -> Optional[bytes]:
        """
        ファイルをダウンロード
        
        Args:
            file_id: Google DriveファイルID
            access_token: アクセストークン
            mime_type: ファイルのMIMEタイプ
            
        Returns:
            ファイルバイナリデータまたはNone
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            # Google DocsやSheetsの場合は変換してダウンロード
            if mime_type == 'application/vnd.google-apps.document':
                url = f"{self.download_url}/{file_id}/export"
                params = {'mimeType': 'application/pdf'}
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                url = f"{self.download_url}/{file_id}/export"
                params = {'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}
            else:
                # 通常のファイルダウンロード
                url = f"{self.download_url}/{file_id}"
                params = {'alt': 'media'}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        file_content = await response.read()
                        logger.info(f"ファイルダウンロード成功: {len(file_content)} bytes")
                        return file_content
                    else:
                        logger.error(f"ファイルダウンロードエラー: {response.status} - {await response.text()}")
                        return None
                        
        except Exception as e:
            logger.error(f"ファイルダウンロード中のエラー: {str(e)}")
            return None
    
    async def list_files(self, access_token: str, folder_id: str = 'root', 
                        search_query: str = None) -> List[Dict[str, Any]]:
        """
        ファイル一覧を取得
        
        Args:
            access_token: アクセストークン
            folder_id: フォルダID（デフォルト: root）
            search_query: 検索クエリ
            
        Returns:
            ファイル一覧
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
            
            # クエリ構築
            query_parts = [f"'{folder_id}' in parents", "trashed = false"]
            
            if search_query:
                query_parts.append(f"name contains '{search_query}'")
            
            query = " and ".join(query_parts)
            
            url = f"{self.base_url}/files"
            params = {
                'q': query,
                'pageSize': 100,
                'fields': 'files(id,name,mimeType,size,modifiedTime,webViewLink)',
                'orderBy': 'folder,name'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        files = result.get('files', [])
                        logger.info(f"ファイル一覧取得成功: {len(files)}件")
                        return files
                    else:
                        logger.error(f"ファイル一覧取得エラー: {response.status} - {await response.text()}")
                        return []
                        
        except Exception as e:
            logger.error(f"ファイル一覧取得中のエラー: {str(e)}")
            return []
    
    async def create_temp_file(self, file_content: bytes, filename: str) -> str:
        """
        一時ファイルを作成
        
        Args:
            file_content: ファイルバイナリデータ
            filename: ファイル名
            
        Returns:
            一時ファイルパス
        """
        try:
            # ファイル拡張子を取得
            _, ext = os.path.splitext(filename)
            
            # 一時ファイルを作成
            temp_fd, temp_path = tempfile.mkstemp(suffix=ext)
            
            # ファイルに書き込み
            async with aiofiles.open(temp_path, 'wb') as temp_file:
                await temp_file.write(file_content)
            
            # ファイルディスクリプタを閉じる
            os.close(temp_fd)
            
            logger.info(f"一時ファイル作成成功: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"一時ファイル作成エラー: {str(e)}")
            raise
    
    def cleanup_temp_file(self, temp_path: str):
        """
        一時ファイルを削除
        
        Args:
            temp_path: 一時ファイルパス
        """
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                logger.info(f"一時ファイル削除完了: {temp_path}")
        except Exception as e:
            logger.error(f"一時ファイル削除エラー: {str(e)}")
    
    def get_supported_mime_types(self) -> List[str]:
        """
        サポートされているMIMEタイプ一覧を取得
        
        Returns:
            サポートされているMIMEタイプのリスト
        """
        return [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'text/plain',
            'application/vnd.google-apps.document',
            'application/vnd.google-apps.spreadsheet'
        ]
    
    def is_supported_file(self, mime_type: str) -> bool:
        """
        ファイルがサポートされているかチェック
        
        Args:
            mime_type: ファイルのMIMEタイプ
            
        Returns:
            サポートされている場合True
        """
        return mime_type in self.get_supported_mime_types() 