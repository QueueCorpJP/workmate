"""
Excel処理モジュール（Google Sheets API使用）
ExcelファイルをGoogle Drive APIでCSVに変換し、Google Sheets APIで綺麗な形で抽出してSupabaseに保存
"""
import os
import io
import tempfile
import logging
import asyncio
from typing import Optional, Dict, Any, List, Tuple
import aiohttp
import aiofiles
from ..database import ensure_string
from .unnamed_column_handler import UnnamedColumnHandler

# ロガーの設定
logger = logging.getLogger(__name__)

# Google APIs
try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from google.auth import default
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
    from googleapiclient.errors import HttpError
    GOOGLE_APIS_AVAILABLE = True
    logger.info("Google APIs ライブラリが利用可能です")
except ImportError:
    GOOGLE_APIS_AVAILABLE = False
    logger.error("Google APIs ライブラリが見つかりません。pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2を実行してください。")

class ExcelSheetsProcessor:
    """Excel処理クラス（Google Sheets API使用）"""
    
    def __init__(self):
        self.drive_service = None
        self.sheets_service = None
        self.temp_files = []  # 一時フォルダ管理用
    
    def __del__(self):
        """デストラクタで一時ファイルをクリーンアップ"""
        self.cleanup_temp_files()
    
    def cleanup_temp_files(self):
        """一時ファイルをクリーンアップ"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.info(f"一時ファイル削除: {temp_file}")
            except Exception as e:
                logger.warning(f"一時ファイル削除エラー: {temp_file} - {str(e)}")
        self.temp_files.clear()
    
    async def get_google_services(self, access_token: str = None, service_account_file: str = None):
        """Google Drive & Sheets APIサービスを取得"""
        if not GOOGLE_APIS_AVAILABLE:
            raise Exception("Google APIs ライブラリが利用できません")
        
        credentials = None
        
        try:
            # 認証方法の優先順位：OAuth2 > サービスアカウント > デフォルト認証
            if access_token:
                logger.info("OAuth2アクセストークンを使用")
                credentials = Credentials(token=access_token)
            
            elif service_account_file and os.path.exists(service_account_file):
                logger.info("サービスアカウントファイルを使用")
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_file,
                    scopes=[
                        'https://www.googleapis.com/auth/drive',
                        'https://www.googleapis.com/auth/spreadsheets'
                    ]
                )
            
            else:
                logger.info("デフォルト認証を使用")
                credentials, _ = default(
                    scopes=[
                        'https://www.googleapis.com/auth/drive',
                        'https://www.googleapis.com/auth/spreadsheets'
                    ]
                )
            
            if not credentials:
                raise Exception("認証情報が取得できませんでした")
            
            # 認証情報の有効性をチェック
            if not credentials.valid:
                if credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                elif not credentials.valid:
                    raise Exception("認証情報が無効です")
            
            # サービスを構築
            def build_services():
                drive_service = build('drive', 'v3', credentials=credentials)
                sheets_service = build('sheets', 'v4', credentials=credentials)
                return drive_service, sheets_service
            
            self.drive_service, self.sheets_service = await asyncio.to_thread(build_services)
            logger.info("Google Drive & Sheets APIサービス取得成功")
            
        except Exception as e:
            logger.error(f"Google APIサービス取得エラー: {str(e)}")
            raise
    
    async def upload_excel_to_drive(self, excel_content: bytes, filename: str) -> str:
        """ExcelファイルをGoogle Driveにアップロード"""
        try:
            if not self.drive_service:
                raise Exception("Google Drive サービスが初期化されていません")
            
            # 一時ファイルを作成
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
            temp_file.write(excel_content)
            temp_file.close()
            self.temp_files.append(temp_file.name)
            
            logger.info(f"Excelファイルを一時ファイルに保存: {temp_file.name}")
            
            # Google Driveにアップロード
            def upload_to_drive():
                file_metadata = {
                    'name': f"{filename}_temp",
                    'parents': []  # ルートフォルダにアップロード
                }
                
                media = MediaIoBaseUpload(
                    io.BytesIO(excel_content),
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    resumable=True
                )
                
                file = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                
                return file.get('id')
            
            file_id = await asyncio.to_thread(upload_to_drive)
            logger.info(f"Google Driveアップロード成功: {file_id}")
            return file_id
            
        except Exception as e:
            logger.error(f"Google Driveアップロードエラー: {str(e)}")
            raise
    
    async def convert_excel_to_sheets(self, drive_file_id: str, filename: str) -> str:
        """ExcelファイルをGoogle Sheetsに変換"""
        try:
            if not self.drive_service:
                raise Exception("Google Drive サービスが初期化されていません")
            
            def convert_file():
                # Google SheetsとしてコピーしてExcelファイルを変換
                copy_metadata = {
                    'name': f"{filename}_converted",
                    'mimeType': 'application/vnd.google-apps.spreadsheet'
                }
                
                copied_file = self.drive_service.files().copy(
                    fileId=drive_file_id,
                    body=copy_metadata,
                    fields='id'
                ).execute()
                
                # 元のExcelファイルを削除
                self.drive_service.files().delete(fileId=drive_file_id).execute()
                
                return copied_file.get('id')
            
            sheets_file_id = await asyncio.to_thread(convert_file)
            logger.info(f"Google Sheets変換成功: {sheets_file_id}")
            return sheets_file_id
            
        except Exception as e:
            logger.error(f"Google Sheets変換エラー: {str(e)}")
            raise
    
    async def extract_data_from_sheets(self, spreadsheet_id: str, filename: str) -> Tuple[List[Dict], Dict[str, str], str]:
        """Google Sheetsからデータを抽出"""
        try:
            if not self.sheets_service:
                raise Exception("Google Sheets サービスが初期化されていません")
            
            def get_spreadsheet_data():
                import time
                start_time = time.time()
                
                # スプレッドシートのメタデータを取得
                logger.info(f"スプレッドシートメタデータ取得開始: {spreadsheet_id}")
                spreadsheet = self.sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
                sheets = spreadsheet.get('sheets', [])
                
                logger.info(f"検出されたシート数: {len(sheets)}")
                
                all_data = []
                sections = {}
                extracted_text = f"=== ファイル: {filename} ===\n\n"
                
                # 各シートを処理
                for sheet_index, sheet in enumerate(sheets):
                    sheet_title = sheet['properties']['title']
                    logger.info(f"シート処理開始 ({sheet_index + 1}/{len(sheets)}): {sheet_title}")
                    
                    # 処理時間チェック
                    elapsed_time = time.time() - start_time
                    if elapsed_time > 240:  # 4分制限
                        logger.warning(f"シート処理時間制限に達しました ({elapsed_time:.1f}秒) - 残りのシートをスキップ")
                        break
                    
                    # シートデータを取得
                    try:
                        range_name = f"'{sheet_title}'!A:ZZ"
                        result = self.sheets_service.spreadsheets().values().get(
                            spreadsheetId=spreadsheet_id,
                            range=range_name,
                            valueRenderOption='FORMATTED_VALUE'  # フォーマット済みの値を取得
                        ).execute()
                        
                        values = result.get('values', [])
                        
                        if not values:
                            logger.warning(f"シート '{sheet_title}' にデータがありません")
                            continue
                        
                        logger.info(f"シート '{sheet_title}' データ取得完了: {len(values)} 行")
                        
                        # ヘッダー行とデータ行を分離
                        headers = values[0] if values else []
                        data_rows = values[1:] if len(values) > 1 else []
                        
                        # 大きなシートの場合は行数制限
                        max_rows = 5000  # 最大5000行
                        if len(data_rows) > max_rows:
                            logger.warning(f"シート '{sheet_title}' の行数が多すぎます ({len(data_rows)} 行) - 最初の{max_rows}行のみ処理")
                            data_rows = data_rows[:max_rows]
                    
                        # 生のデータをDataFrameに変換してUnnamedカラム修正を適用
                        if headers and data_rows:
                            try:
                                # DataFrameを作成
                                import pandas as pd
                                df_data = []
                                for row in data_rows:
                                    # 行の長さをヘッダーに合わせる
                                    extended_row = row + [''] * (len(headers) - len(row))
                                    df_data.append(extended_row[:len(headers)])
                                
                                df = pd.DataFrame(df_data, columns=headers)
                                
                                # Unnamedカラム修正を適用
                                handler = UnnamedColumnHandler()
                                df, modifications = handler.fix_dataframe(df, f"{filename}_{sheet_title}")
                                
                                if modifications:
                                    logger.info(f"シート '{sheet_title}' のUnnamedカラム修正: {', '.join(modifications)}")
                                
                                # 修正されたヘッダーとデータ行を更新
                                headers = df.columns.tolist()
                                data_rows = df.values.tolist()
                                
                            except Exception as fix_error:
                                logger.warning(f"シート '{sheet_title}' のUnnamedカラム修正エラー: {str(fix_error)}")
                                # エラーの場合は元のデータを使用
                        
                        # セクション情報を作成
                        section_name = f"シート: {sheet_title}"
                        section_content = f"行数: {len(data_rows)}, 列数: {len(headers)}\n"
                        
                        if headers:
                            section_content += f"列名: {', '.join(headers)}\n"
                        
                        # サンプルデータを追加
                        if data_rows:
                            sample_rows = data_rows[:3]  # 最初の3行をサンプルとして
                            section_content += "サンプルデータ:\n"
                            for i, row in enumerate(sample_rows):
                                row_data = []
                                for j, header in enumerate(headers):
                                    if j < len(row) and row[j]:
                                        row_data.append(f"{header}: {row[j]}")
                                if row_data:
                                    section_content += f"  行{i+1}: {' | '.join(row_data)}\n"
                        
                        sections[section_name] = section_content
                        extracted_text += f"=== {section_name} ===\n{section_content}\n\n"
                        
                        # 各データ行を処理
                        for row_index, row in enumerate(data_rows):
                            if not any(cell for cell in row if cell):  # 空行をスキップ
                                continue
                            
                            # 行データを辞書形式で作成
                            row_dict = {}
                            content_parts = []
                            
                            for col_index, header in enumerate(headers):
                                cell_value = row[col_index] if col_index < len(row) else ""
                                
                                if cell_value:
                                    header_str = ensure_string(header) if header else f"列{col_index+1}"
                                    cell_str = ensure_string(cell_value)
                                    row_dict[header_str] = cell_str
                                    content_parts.append(f"{header_str}: {cell_str}")
                            
                            if content_parts:
                                # データベース保存用の構造を作成
                                data_record = {
                                    'section': ensure_string(section_name),
                                    'content': ' | '.join(content_parts),
                                    'source': 'Excel (Google Sheets)',
                                    'file': ensure_string(filename),
                                    'url': None,
                                    'metadata': {
                                        'sheet_name': ensure_string(sheet_title),
                                        'row_index': row_index + 1,
                                        'columns': list(row_dict.keys())
                                    }
                                }
                                
                                # 元の列データも保持
                                for key, value in row_dict.items():
                                    data_record[f"column_{key}"] = value
                                
                                all_data.append(data_record)
                    
                    except Exception as sheet_error:
                        logger.error(f"シート '{sheet_title}' の処理エラー: {str(sheet_error)}")
                        # エラーが発生したシートはスキップして次のシートを処理
                        continue
                
                return all_data, sections, extracted_text
            
            result = await asyncio.to_thread(get_spreadsheet_data)
            logger.info(f"データ抽出完了: {len(result[0])} レコード")
            return result
            
        except Exception as e:
            logger.error(f"Google Sheetsデータ抽出エラー: {str(e)}")
            raise
    
    async def cleanup_drive_file(self, file_id: str):
        """Google Driveファイルを削除"""
        try:
            if self.drive_service:
                def delete_file():
                    self.drive_service.files().delete(fileId=file_id).execute()
                
                await asyncio.to_thread(delete_file)
                logger.info(f"Google Driveファイル削除: {file_id}")
        except Exception as e:
            logger.warning(f"Google Driveファイル削除エラー: {file_id} - {str(e)}")

async def process_excel_file_with_sheets_api(
    contents: bytes, 
    filename: str, 
    access_token: str = None, 
    service_account_file: str = None
) -> Tuple[List[Dict], Dict[str, str], str]:
    """
    ExcelファイルをGoogle Sheets APIで処理
    
    Args:
        contents: Excelファイルのバイナリデータ
        filename: ファイル名
        access_token: OAuth2アクセストークン
        service_account_file: サービスアカウントファイルパス
    
    Returns:
        (データリスト, セクション辞書, 抽出テキスト)
    """
    processor = ExcelSheetsProcessor()
    spreadsheet_id = None
    
    try:
        logger.info(f"Excel処理開始（Google Sheets API使用）: {filename}")
        
        # Google APIサービスを取得
        await processor.get_google_services(access_token, service_account_file)
        
        # ExcelファイルをGoogle Driveにアップロード
        drive_file_id = await processor.upload_excel_to_drive(contents, filename)
        
        # ExcelファイルをGoogle Sheetsに変換
        spreadsheet_id = await processor.convert_excel_to_sheets(drive_file_id, filename)
        
        # Google Sheetsからデータを抽出
        data_list, sections, extracted_text = await processor.extract_data_from_sheets(spreadsheet_id, filename)
        
        logger.info(f"Excel処理完了: {len(data_list)} レコード抽出")
        return data_list, sections, extracted_text
        
    except Exception as e:
        logger.error(f"Excel処理エラー: {str(e)}")
        raise
    
    finally:
        # クリーンアップ
        if spreadsheet_id:
            await processor.cleanup_drive_file(spreadsheet_id)
        
        processor.cleanup_temp_files()

# 後方互換性のための関数
async def process_excel_file_async(contents: bytes, filename: str, access_token: str = None) -> Tuple[List[Dict], Dict[str, str], str]:
    """非同期でExcelファイルを処理（後方互換性用）"""
    service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    return await process_excel_file_with_sheets_api(contents, filename, access_token, service_account_file)

def is_excel_file(filename: str) -> bool:
    """ファイルがExcelファイルかどうかを判定"""
    if not filename:
        return False
    
    extension = filename.lower().split('.')[-1]
    return extension in ['xls', 'xlsx']

def get_excel_mime_types() -> List[str]:
    """サポートされているExcel MIMEタイプのリストを返す"""
    return [
        'application/vnd.ms-excel',  # .xls
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.google-apps.spreadsheet'  # Google Sheets
    ]
