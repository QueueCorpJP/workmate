"""
知識ベースAPI関数モジュール
ファイルとURLの処理、リソースの管理を行うAPI関数を提供します
"""
import uuid
import logging
import pandas as pd
from datetime import datetime
from fastapi import HTTPException, UploadFile, File, Depends
from io import BytesIO
import PyPDF2
import traceback
from typing import Dict, List, Optional, Tuple, Any, Union
from psycopg2.extensions import connection as Connection
from ..database import get_db, update_usage_count, ensure_string
from ..auth import check_usage_limits
from .base import knowledge_base, _update_knowledge_base, get_active_resources
from .excel import process_excel_file
from .pdf import process_pdf_file
from .text import process_txt_file
from .url import extract_text_from_url, process_url_content
from ..company import DEFAULT_COMPANY_NAME
from ..utils import _process_video_file

# ロガーの設定
logger = logging.getLogger(__name__)

# 共通のエラーメッセージ
EMPLOYEE_UPLOAD_ERROR = "社員アカウントはドキュメントをアップロードできません。管理者にお問い合わせください。"
LIMIT_REACHED_ERROR = "申し訳ございません。デモ版のドキュメントアップロード制限（{limit}回）に達しました。"
INVALID_FILE_ERROR = "無効なファイル形式です。ExcelファイルまたはPDFファイル、テキストファイル（.xlsx、.xls、.pdf、.txt）のみ対応しています。"
PDF_SIZE_ERROR = "PDFファイルが大きすぎます ({size:.2f} MB)。10MB以下のファイルを使用するか、ファイルを分割してください。"
VIDEO_SIZE_ERROR = "ビデオファイルが大きすぎます ({size:.2f} MB)。500MB以下のファイルを使用するか、ファイルを分割してください。"
TIMEOUT_ERROR = "処理がタイムアウトしました。ファイルが大きすぎるか、複雑すぎる可能性があります。ファイルを分割するか、より小さなファイルを使用してください。"

def _get_user_info(user_id: str, db: Connection) -> Tuple[Optional[str], bool]:
    """ユーザー情報を取得し、アップロード権限をチェックする"""
    if not user_id:
        return None, True
        
    cursor = db.cursor()
    cursor.execute("SELECT company_id, role FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        return None, True
        
    # 社員アカウントはアップロード不可
    if user['role'] == 'employee':
        raise HTTPException(status_code=403, detail=EMPLOYEE_UPLOAD_ERROR)
        
    return user['company_id'], True

def _check_upload_limits(user_id: str, db: Connection) -> Dict[str, Any]:
    """アップロード制限をチェックする"""
    if not user_id:
        return {"allowed": True, "remaining": None, "limit_reached": False}
        
    limits_check = check_usage_limits(user_id, "document_upload", db)
    
    if not limits_check["is_unlimited"] and not limits_check["allowed"]:
        raise HTTPException(
            status_code=403,
            detail=LIMIT_REACHED_ERROR.format(limit=limits_check['limit'])
        )
    
    return {
        "allowed": True,
        "remaining": limits_check.get("remaining") if not limits_check["is_unlimited"] else None,
        "limit_reached": False
    }

def _record_document_source(
    name: str, 
    doc_type: str, 
    page_count: int, 
    content: str, 
    user_id: str, 
    company_id: str, 
    db: Connection
) -> None:
    """ドキュメントソースをデータベースに記録する"""
    document_id = str(uuid.uuid4())
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO document_sources (id, name, type, page_count, content, uploaded_by, company_id, uploaded_at, active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (document_id, name, doc_type, page_count, ensure_string(content, for_db=True), user_id, company_id, datetime.now().isoformat(), True)
    )
    
    # 会社のソースリストに追加
    if company_id:
        if company_id not in knowledge_base.company_sources:
            knowledge_base.company_sources[company_id] = []
        if name not in knowledge_base.company_sources[company_id]:
            knowledge_base.company_sources[company_id].append(name)

def _update_source_info(source_name: str) -> None:
    """ソース情報を更新する"""
    if source_name not in knowledge_base.sources:
        knowledge_base.sources.append(source_name)
        knowledge_base.source_info[source_name] = {
            'timestamp': datetime.now().isoformat(),
            'active': True
        }

def _prepare_response(
    df: pd.DataFrame, 
    sections: Dict[str, str], 
    source_name: str, 
    remaining_uploads: Optional[int] = None, 
    limit_reached: bool = False
) -> Dict[str, Any]:
    """レスポンスデータを準備する"""
    active_sources = get_active_resources()
    
    preview_data = []
    total_rows = 0
    
    if df is not None and not df.empty:
        preview_data = df.head(5).to_dict('records')
        # NaN値を適切に処理
        preview_data = [{k: (None if pd.isna(v) else str(v)) for k, v in record.items()} for record in preview_data]
        total_rows = len(df)
    
    return {
        "message": f"{DEFAULT_COMPANY_NAME}の情報が正常に更新されました（{source_name}）",
        "columns": knowledge_base.columns if knowledge_base.data is not None else [],
        "preview": preview_data,
        "total_rows": total_rows,
        "sections": list(sections.keys()),
        "file" if not source_name.startswith(('http://', 'https://')) else "url": source_name,
        "sources": knowledge_base.sources,
        "active_sources": active_sources,
        "remaining_uploads": remaining_uploads,
        "limit_reached": limit_reached
    }

async def process_url(url: str, user_id: str = None, company_id: str = None, db: Connection = None):
    """URLを処理して知識ベースを更新する"""
    try:
        # ユーザー情報の取得と会社IDの設定
        if user_id and not company_id:
            company_id, _ = _get_user_info(user_id, db)
        
        # アップロード制限のチェック
        limits = _check_upload_limits(user_id, db)
        
        # URLからテキストを抽出
        extracted_text = await extract_text_from_url(url)
        if extracted_text.startswith("URLからのテキスト抽出エラー:"):
            raise HTTPException(status_code=500, detail=extracted_text)
        
        # URLのコンテンツを処理
        df, sections, processed_text = await process_url_content(url, extracted_text)
        
        # 知識ベースを更新
        _update_knowledge_base(df, processed_text, is_file=False, source_name=url, company_id=company_id)
        
        # ソース情報を更新
        _update_source_info(url)
        
        # ユーザーIDがある場合はドキュメントアップロードカウントを更新
        if user_id:
            updated_limits = update_usage_count(user_id, "document_uploads_used", db)
            _record_document_source(url, "URL", 1, processed_text, user_id, company_id, db)
            db.commit()
        
        # レスポンスを準備して返す
        return _prepare_response(
            df, sections, url, 
            limits.get("remaining"), 
            limits.get("limit_reached", False)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL処理エラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"URLの処理中にエラーが発生しました: {str(e)}")

async def process_file(file: UploadFile = File(...), user_id: str = None, company_id: str = None, db: Connection = None):
    """ファイルを処理して知識ベースを更新する"""
    # ユーザー情報の取得と会社IDの設定
    if user_id and not company_id:
        company_id, _ = _get_user_info(user_id, db)
    
    # ファイル名が存在することを確認
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="ファイルが指定されていないか、ファイル名が無効です。")

    # ファイル拡張子をチェック
    if not file.filename.endswith(('.xlsx', '.xls', '.pdf', '.txt', '.avi', '.mp4', '.webm')):
        raise HTTPException(status_code=400, detail=INVALID_FILE_ERROR)

    try:
        # アップロード制限のチェック
        limits = _check_upload_limits(user_id, db)
        remaining_uploads = limits.get("remaining")
        limit_reached = limits.get("limit_reached", False)
        
        logger.info(f"ファイルアップロード開始: {file.filename}")
        
        # ファイルを読み込む
        try:
            contents = await file.read()
        except Exception as e:
            logger.error(f"ファイル読み込みエラー: {str(e)}")
            raise HTTPException(status_code=400, detail=f"ファイルの読み込み中にエラーが発生しました: {str(e)}")
            
        file_size_mb = len(contents) / (1024 * 1024)
        logger.info(f"ファイルサイズ: {file_size_mb:.2f} MB")
        
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="ファイルが空です。有効なファイルをアップロードしてください。")
        
        # ファイル形式に応じた処理
        file_extension = file.filename.split('.')[-1].lower()
        
        # データフレームとセクションを初期化
        df = None
        sections = {}
        extracted_text = ""
        page_count = 1
        
        try:
            # ファイル形式に応じた処理関数を呼び出す
            if file_extension in ['xlsx', 'xls']:
                logger.info(f"Excelファイル処理開始: {file.filename}")
                df, sections, extracted_text = process_excel_file(contents, file.filename)
                
                # Excelファイルのシート数を取得
                try:
                    excel_file = BytesIO(contents)
                    df_dict = pd.read_excel(excel_file, sheet_name=None)
                    page_count = len(df_dict)
                except:
                    page_count = 1
                    
            elif file_extension == 'pdf':
                logger.info(f"PDFファイル処理開始: {file.filename}")
                
                # PDFファイルが大きすぎる場合はエラーを返す
                if file_size_mb > 10:
                    raise HTTPException(status_code=400, detail=PDF_SIZE_ERROR.format(size=file_size_mb))
                
                try:
                    # PDFファイルの有効性を確認
                    pdf_file = BytesIO(contents)
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    page_count = len(pdf_reader.pages)
                    
                    # PDFファイルを処理
                    df, sections, extracted_text = await process_pdf_file(contents, file.filename)
                except PyPDF2.errors.PdfReadError as pdf_err:
                    raise HTTPException(status_code=400, detail=f"無効なPDFファイルです: {str(pdf_err)}")
                except Exception as pdf_ex:
                    logger.error(f"PDFファイル処理中のエラー: {str(pdf_ex)}")
                    # エラー時のフォールバック処理
                    df = pd.DataFrame({
                        'section': ["エラー"],
                        'content': [f"PDFファイル処理中にエラーが発生しました: {str(pdf_ex)}"],
                        'source': ['PDF'],
                        'file': [file.filename],
                        'url': [None]
                    })
                    sections = {"エラー": f"PDFファイル処理中にエラーが発生しました: {str(pdf_ex)}"}
                    extracted_text = f"=== ファイル: {file.filename} ===\n\n=== エラー ===\nPDFファイル処理中にエラーが発生しました: {str(pdf_ex)}\n\n"
                    
            elif file_extension == 'txt':
                logger.info(f"テキストファイル処理開始: {file.filename}")
                df, sections, extracted_text = process_txt_file(contents, file.filename)
                
            elif file_extension in ['avi', 'mp4', 'webm']:
                if file_size_mb > 500:
                    raise HTTPException(status_code=400, detail=VIDEO_SIZE_ERROR.format(size=file_size_mb))
                
                df, sections, extracted_text = _process_video_file(contents, file.filename)
                
            # データフレームの内容を確認
            if df is None or df.empty:
                logger.warning("空のデータフレームが生成されました")
                # 空のデータフレームの場合、最低限のデータを設定
                df = pd.DataFrame({
                    'section': ["一般情報"],
                    'content': ["ファイルからテキストを抽出できませんでした。"],
                    'source': [file_extension.upper()],
                    'file': [file.filename],
                    'url': [None]
                })
                
        except HTTPException:
            raise
        except Exception as e:
            error_type = {
                'xlsx': 'Excel', 'xls': 'Excel',
                'pdf': 'PDF',
                'txt': 'テキスト'
            }.get(file_extension, 'ファイル')
            
            logger.error(f"{error_type}ファイル処理エラー: {str(e)}", exc_info=True)
            
            # タイムアウトエラーの特別処理
            if "timeout" in str(e).lower():
                raise HTTPException(status_code=408, detail=TIMEOUT_ERROR)
            else:
                raise HTTPException(status_code=500, detail=f"{error_type}ファイルの処理中にエラーが発生しました: {str(e)}")
        
        # 知識ベースを更新（ファイルデータとして保存）
        if df is not None and not df.empty:
            # ファイル列が存在することを確認
            if 'file' not in df.columns:
                df['file'] = file.filename
                
            # すべての列の値を適切に変換（NULL値はそのまま保持）
            for col in df.columns:
                # NULLでない値のみを文字列に変換
                df[col] = df[col].apply(lambda x: str(x) if pd.notna(x) else None)
                
            # 知識ベースを更新
            _update_knowledge_base(df, extracted_text, is_file=True, source_name=file.filename, company_id=company_id)
        
        # ソース情報を更新
        _update_source_info(file.filename)
        
        # ユーザーIDがある場合はドキュメントアップロードカウントを更新
        if user_id:
            updated_limits = update_usage_count(user_id, "document_uploads_used", db)
            remaining_uploads = updated_limits["document_uploads_limit"] - updated_limits["document_uploads_used"]
            limit_reached = remaining_uploads <= 0
            
            # ドキュメントソースを記録
            _record_document_source(file.filename, file_extension.upper(), page_count, extracted_text, user_id, company_id, db)
            db.commit()
        
        # レスポンスを準備して返す
        return _prepare_response(df, sections, file.filename, remaining_uploads, limit_reached)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ファイルアップロード処理中の予期しないエラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ファイルのアップロード中にエラーが発生しました: {str(e)}")

async def toggle_resource_active(resource_name: str):
    """リソースのアクティブ状態を切り替える"""
    if resource_name not in knowledge_base.sources:
        raise HTTPException(status_code=404, detail=f"リソース '{resource_name}' が見つかりません")
    
    # 現在の状態を取得
    current_state = knowledge_base.source_info.get(resource_name, {}).get('active', True)
    
    # 状態を反転
    new_state = not current_state
    
    # 状態を更新
    if resource_name not in knowledge_base.source_info:
        knowledge_base.source_info[resource_name] = {}
    
    knowledge_base.source_info[resource_name]['active'] = new_state
    
    return {
        "name": resource_name,
        "active": new_state,
        "message": f"リソース '{resource_name}' のアクティブ状態を {new_state} に変更しました"
    }

async def get_uploaded_resources():
    """アップロードされたリソース（URL、PDF、Excel、TXT）の情報を取得する"""
    resources = []
    
    for source in knowledge_base.sources:
        info = knowledge_base.source_info.get(source, {})
        
        # リソースタイプを判定
        if source.startswith(('http://', 'https://')):
            resource_type = "URL"
        else:
            extension = source.split('.')[-1].lower() if '.' in source else ""
            resource_type = {
                'xlsx': 'Excel', 'xls': 'Excel',
                'pdf': 'PDF',
                'txt': 'テキスト',
                'avi': 'Video', 'mp4': 'Video', 'webm': 'Video'
            }.get(extension, "その他")
        
        resources.append({
            "name": source,
            "type": resource_type,
            "timestamp": info.get('timestamp', datetime.now().isoformat()),
            "active": info.get('active', True)
        })
    
    return {
        "resources": resources,
        "message": f"{len(resources)}件のリソースが見つかりました"
    }