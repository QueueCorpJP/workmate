"""
知識ベースAPI関数モジュール
ファイルとURLの処理、リソースの管理を行うAPI関数を提供します
"""
import uuid
import logging
import pandas as pd
import asyncio
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
from .excel_sheets_processor import process_excel_file_with_sheets_api, is_excel_file
from .pdf import process_pdf_file
from .text import process_txt_file
from .image import process_image_file, is_image_file
from .csv_processor import process_csv_file, process_csv_with_gemini_ocr, is_csv_file
from .word_processor import process_word_file, is_word_file
from .file_detector import detect_file_type
from .url import extract_text_from_url, process_url_content
from ..company import DEFAULT_COMPANY_NAME
from ..utils import _process_video_file
import os

# ロガーの設定
logger = logging.getLogger(__name__)

# 共通のエラーメッセージ
EMPLOYEE_UPLOAD_ERROR = "社員アカウントはドキュメントをアップロードできません。管理者にお問い合わせください。"
LIMIT_REACHED_ERROR = "申し訳ございません。デモ版のドキュメントアップロード制限（{limit}回）に達しました。"
INVALID_FILE_ERROR = "無効なファイル形式です。Excel、PDF、Word、CSV、テキスト、画像ファイル（.xlsx、.xls、.pdf、.doc、.docx、.csv、.txt、.jpg、.png等）のみ対応しています。"
PDF_SIZE_ERROR = "PDFファイルが大きすぎます ({size:.2f} MB)。10MB以下のファイルを使用するか、ファイルを分割してください。"
VIDEO_SIZE_ERROR = "ビデオファイルが大きすぎます ({size:.2f} MB)。500MB以下のファイルを使用するか、ファイルを分割してください。"
TIMEOUT_ERROR = "処理がタイムアウトしました。ファイルが大きすぎるか、複雑すぎる可能性があります。ファイルを分割するか、より小さなファイルを使用してください。"

def _get_user_info(user_id: str, db: Connection) -> Tuple[Optional[str], bool]:
    """ユーザー情報を取得し、アップロード権限をチェックする"""
    if not user_id:
        return None, True
    
    try:
        from supabase_adapter import select_data
        user_result = select_data("users", columns="company_id,role", filters={"id": user_id})
        
        if not user_result.data or len(user_result.data) == 0:
            return None, True
        
        user = user_result.data[0]
        
        # 社員アカウントはアップロード不可
        if user.get('role') == 'employee':
            raise HTTPException(status_code=403, detail=EMPLOYEE_UPLOAD_ERROR)
    except HTTPException:
        # HTTPExceptionは再度発生させる
        raise
    except Exception as e:
        logger.error(f"ユーザー情報取得エラー: {str(e)}")
        return None, True
        
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

def _prepare_response_from_list(
    data_list: List[Dict], 
    sections: Dict[str, str], 
    source_name: str, 
    remaining_uploads: Optional[int] = None, 
    limit_reached: bool = False
) -> Dict[str, Any]:
    """データリストからレスポンスデータを準備する"""
    active_sources = get_active_resources()
    
    preview_data = []
    total_rows = len(data_list) if data_list else 0
    
    if data_list:
        # 最初の5件をプレビューとして取得
        preview_data = data_list[:5]
        # 値を適切に処理
        preview_data = [{k: (None if v is None else str(v)) for k, v in record.items()} for record in preview_data]
    
    # 列名を抽出
    columns = []
    if data_list:
        # 最初のレコードから列名を取得
        columns = list(data_list[0].keys())
    
    return {
        "message": f"{DEFAULT_COMPANY_NAME}の情報が正常に更新されました（{source_name}）",
        "columns": columns,
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

    # ファイル拡張子をチェック（CSV・Word形式を追加）
    allowed_extensions = ('.xlsx', '.xls', '.pdf', '.txt', '.csv', '.doc', '.docx',
                         '.avi', '.mp4', '.webm', 
                         '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp')
    if not file.filename.endswith(allowed_extensions):
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
            
            # メモリ使用量を制御するため、処理前に少し待機
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"ファイル読み込みエラー: {str(e)}")
            raise HTTPException(status_code=400, detail=f"ファイルの読み込み中にエラーが発生しました: {str(e)}")
            
        file_size_mb = len(contents) / (1024 * 1024)
        logger.info(f"ファイルサイズ: {file_size_mb:.2f} MB")
        
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="ファイルが空です。有効なファイルをアップロードしてください。")
        
        # ファイル形式を検知
        file_info = detect_file_type(file.filename, contents)
        file_extension = file_info['extension']
        detected_type = file_info['file_type']
        recommended_processor = file_info['processor']
        
        logger.info(f"ファイル形式検知結果: {detected_type} (プロセッサー: {recommended_processor}, 信頼度: {file_info['confidence']})")
        
        # データフレームとセクションを初期化
        df = None
        sections = {}
        extracted_text = ""
        page_count = 1
        
        try:
            # 検知されたファイル形式に基づいて処理を実行
            if detected_type == 'excel' or file_extension in ['xlsx', 'xls']:
                logger.info(f"Excelファイル処理開始: {file.filename}")
                
                try:
                    # Google Sheets APIを使用してExcelファイルを処理
                    # OAuth2トークンを優先的に使用
                    access_token = getattr(request.state, 'google_access_token', None)
                    service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
                    
                    data_list, sections, extracted_text = await process_excel_file_with_sheets_api(
                        contents, 
                        file.filename, 
                        access_token, 
                        service_account_file
                    )
                    
                    # データリストを直接使用（DataFrameを使用しない）
                    if not data_list:
                        data_list = [{
                            'section': "データなし",
                            'content': "Excelファイルに有効なデータが見つかりませんでした",
                            'source': 'Excel (Google Sheets)',
                            'file': file.filename,
                            'url': None
                        }]
                    
                    # ページ数を推定（シート数に基づく）
                    sheet_count = len(set(item.get('metadata', {}).get('sheet_name', 'Sheet1') for item in data_list))
                    page_count = max(1, sheet_count)
                    
                    logger.info(f"Excel処理完了（Google Sheets API使用）: {len(data_list)} レコード, {page_count} シート")
                    
                    # データベース保存用にデータを準備
                    df = None  # DataFrameは使用しない
                    
                except Exception as e:
                    logger.warning(f"Google Sheets API処理エラー、従来の処理にフォールバック: {str(e)}")
                    # フォールバック：従来のpandas処理
                    df, sections, extracted_text = process_excel_file(contents, file.filename)
                    data_list = None  # 従来処理の場合はDataFrameを使用
                    
                    # Excelファイルのシート数を取得
                    try:
                        excel_file = BytesIO(contents)
                        df_dict = pd.read_excel(excel_file, sheet_name=None)
                        page_count = len(df_dict)
                    except:
                        page_count = 1
                    
            elif detected_type == 'csv' or is_csv_file(file.filename):
                logger.info(f"CSVファイル処理開始: {file.filename}, サイズ: {file_size_mb:.2f}MB")
                # CSVファイルサイズ制限（50MB）
                if file_size_mb > 50:
                    raise HTTPException(status_code=400, detail=f"CSVファイルが大きすぎます ({file_size_mb:.2f} MB)。50MB以下のファイルを使用してください。")
                
                # 文字化け検出でGemini OCR優先処理を決定
                from .csv_processor import detect_csv_encoding, detect_mojibake_in_content
                logger.info("CSV文字エンコーディング検出開始")
                detected_encoding = detect_csv_encoding(contents)
                logger.info(f"検出されたエンコーディング: {detected_encoding}")
                has_mojibake = detect_mojibake_in_content(contents, detected_encoding)
                logger.info(f"文字化け検出結果: {has_mojibake}")
                
                if has_mojibake:
                    logger.info("文字化け検出 - Gemini OCRを優先使用")
                    try:
                        # 文字化け検出時: Gemini OCRを最初に試行
                        logger.info("文字化け対応: Gemini OCRを使用してCSVを処理")
                        df, sections, extracted_text = await process_csv_with_gemini_ocr(contents, file.filename)
                        logger.info(f"Gemini OCR処理成功: {len(df) if df is not None else 0} 行")
                        page_count = 1
                    except Exception as ocr_error:
                        logger.error(f"Gemini OCR処理失敗: {str(ocr_error)}")
                        try:
                            # OCR失敗時: Google Sheets APIを試行
                            logger.info("OCR失敗 - Google Sheets APIを試行")
                            from .csv_processor import process_csv_file_with_sheets_api
                            df, sections, extracted_text = await process_csv_file_with_sheets_api(contents, file.filename)
                            logger.info(f"Google Sheets API処理成功: {len(df) if df is not None else 0} 行")
                            page_count = 1
                        except Exception as sheets_error:
                            logger.error(f"Google Sheets API処理失敗: {str(sheets_error)}")
                            # 最終フォールバック: 従来の処理
                            logger.info("最終フォールバック: 従来のCSV処理")
                            from .csv_processor import process_csv_file
                            df, sections, extracted_text = process_csv_file(contents, file.filename)
                            logger.info(f"従来のCSV処理結果: {len(df) if df is not None else 0} 行")
                            page_count = 1
                else:
                    logger.info("文字化けなし - 通常のCSV処理フロー")
                    try:
                        # 通常処理: Google Sheets APIを使用してCSVを処理
                        logger.info("Google Sheets APIを使用してCSVを処理")
                        from .csv_processor import process_csv_file_with_sheets_api
                        df, sections, extracted_text = await process_csv_file_with_sheets_api(contents, file.filename)
                        logger.info(f"Google Sheets API処理成功: {len(df) if df is not None else 0} 行")
                        page_count = 1
                    except Exception as sheets_error:
                        logger.error(f"Google Sheets API処理失敗: {str(sheets_error)}")
                        try:
                            # フォールバック: Gemini OCRを使用してCSVを処理
                            logger.info("Gemini OCRを使用してCSVを処理（フォールバック）")
                            df, sections, extracted_text = await process_csv_with_gemini_ocr(contents, file.filename)
                            logger.info(f"Gemini OCR処理成功: {len(df) if df is not None else 0} 行")
                            page_count = 1
                        except Exception as csv_error:
                            logger.error(f"CSV処理エラー: {str(csv_error)}")
                            # 最終フォールバック: 従来の処理
                            logger.info("最終フォールバック実行: 従来のCSV処理")
                            from .csv_processor import process_csv_file
                            df, sections, extracted_text = process_csv_file(contents, file.filename)
                            logger.info(f"従来のCSV処理結果: {len(df) if df is not None else 0} 行")
                            page_count = 1
                
                # CSV処理結果の検証
                logger.info(f"CSV処理完了後の検証: df={df is not None}, sections={len(sections) if sections else 0}, extracted_text={len(extracted_text) if extracted_text else 0}")
                if df is None or df.empty:
                    logger.error("CSVファイルから有効なデータを抽出できませんでした")
                    raise HTTPException(status_code=400, detail="CSVファイルから有効なデータを抽出できませんでした。ファイルの形式をご確認ください。")

            elif detected_type == 'word' or is_word_file(file.filename):
                logger.info(f"Wordファイル処理開始: {file.filename}")
                # Wordファイルサイズ制限（20MB）
                if file_size_mb > 20:
                    raise HTTPException(status_code=400, detail=f"Wordファイルが大きすぎます ({file_size_mb:.2f} MB)。20MB以下のファイルを使用してください。")
                
                try:
                    # Word処理前に少し待機（メモリ負荷軽減）
                    await asyncio.sleep(0.2)
                    df, sections, extracted_text = await process_word_file(contents, file.filename)
                    page_count = 1
                except Exception as word_error:
                    logger.error(f"Word処理エラー: {str(word_error)}")
                    # Word処理が失敗した場合のフォールバック
                    df = pd.DataFrame({
                        'section': ["Word処理エラー"],
                        'content': [f"Wordファイル処理中にエラーが発生しました: {str(word_error)}"],
                        'source': ['Word'],
                        'file': [file.filename],
                        'url': [None]
                    })
                    sections = {"Word処理エラー": f"Wordファイル処理中にエラーが発生しました: {str(word_error)}"}
                    extracted_text = f"=== ファイル: {file.filename} ===\n\n=== Word処理エラー ===\nWordファイル処理中にエラーが発生しました: {str(word_error)}\n\n"
                    page_count = 1

            elif detected_type == 'image' or is_image_file(file.filename):
                logger.info(f"画像ファイル処理開始: {file.filename}")
                # 画像ファイルサイズ制限（10MB）
                if file_size_mb > 10:
                    raise HTTPException(status_code=400, detail=f"画像ファイルが大きすぎます ({file_size_mb:.2f} MB)。10MB以下のファイルを使用してください。")
                
                try:
                    # 画像処理前に少し待機（メモリ負荷軽減）
                    await asyncio.sleep(0.2)
                    df, sections, extracted_text = await process_image_file(contents, file.filename)
                    page_count = 1
                except Exception as img_error:
                    logger.error(f"画像処理エラー: {str(img_error)}")
                    # 画像処理が失敗した場合のフォールバック
                    df = pd.DataFrame({
                        'section': ["画像処理エラー"],
                        'content': [f"画像ファイル処理中にエラーが発生しました: {str(img_error)}"],
                        'source': ['画像'],
                        'file': [file.filename],
                        'url': [None]
                    })
                    sections = {"画像処理エラー": f"画像ファイル処理中にエラーが発生しました: {str(img_error)}"}
                    extracted_text = f"=== ファイル: {file.filename} ===\n\n=== 画像処理エラー ===\n画像ファイル処理中にエラーが発生しました: {str(img_error)}\n\n"
                    page_count = 1
                    
            elif detected_type == 'pdf' or file_extension == 'pdf':
                logger.info(f"PDFファイル処理開始: {file.filename}")
                
                # PDFファイルが大きすぎる場合はエラーを返す
                if file_size_mb > 10:
                    raise HTTPException(status_code=400, detail=PDF_SIZE_ERROR.format(size=file_size_mb))
                
                try:
                    # PDFファイルの有効性を確認
                    pdf_file = BytesIO(contents)
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    page_count = len(pdf_reader.pages)
                    
                    logger.info(f"PDFページ数: {page_count}")
                    
                    # ページ数が多い場合は処理前に警告
                    if page_count > 8:
                        logger.info(f"大きなPDFファイル（{page_count}ページ）を分割処理します")
                        await asyncio.sleep(0.5)  # 処理前の待機
                    
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
                    
            elif detected_type == 'text' or file_extension == 'txt':
                logger.info(f"テキストファイル処理開始: {file.filename}")
                df, sections, extracted_text = await process_txt_file(contents, file.filename)
                
            elif detected_type == 'video' or file_extension in ['avi', 'mp4', 'webm']:
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
                'txt': 'テキスト',
                'csv': 'CSV',
                'doc': 'Word', 'docx': 'Word',
                'jpg': '画像', 'jpeg': '画像', 'png': '画像', 'gif': '画像',
                'bmp': '画像', 'tiff': '画像', 'tif': '画像', 'webp': '画像'
            }.get(file_extension, 'ファイル')
            
            logger.error(f"{error_type}ファイル処理エラー: {str(e)}", exc_info=True)
            
            # タイムアウトエラーの特別処理
            if "timeout" in str(e).lower():
                raise HTTPException(status_code=408, detail=TIMEOUT_ERROR)
            else:
                raise HTTPException(status_code=500, detail=f"{error_type}ファイルの処理中にエラーが発生しました: {str(e)}")
        
        # 知識ベースを更新（ファイルデータとして保存）
        if 'data_list' in locals() and data_list:
            # 新しいGoogle Sheets API処理の場合：data_listを直接使用
            from .base import _update_knowledge_base_from_list
            _update_knowledge_base_from_list(data_list, extracted_text, is_file=True, source_name=file.filename, company_id=company_id)
        elif df is not None and not df.empty:
            # 従来のpandas処理の場合：DataFrameを使用
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
        if 'data_list' in locals() and data_list:
            # 新しいGoogle Sheets API処理の場合
            logger.info(f"最終レスポンス準備: data_list={len(data_list)}レコード, sections={len(sections)}, filename={file.filename}")
            response = _prepare_response_from_list(data_list, sections, file.filename, remaining_uploads, limit_reached)
        else:
            # 従来のpandas処理の場合
            logger.info(f"最終レスポンス準備: df={len(df) if df is not None else 0}行, sections={len(sections)}, filename={file.filename}")
            response = _prepare_response(df, sections, file.filename, remaining_uploads, limit_reached)
        
        logger.info(f"レスポンス準備完了: total_rows={response.get('total_rows', 0)}, preview_rows={len(response.get('preview', []))}")
        return response
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
                'csv': 'CSV',
                'doc': 'Word', 'docx': 'Word',
                'avi': 'Video', 'mp4': 'Video', 'webm': 'Video',
                'jpg': '画像', 'jpeg': '画像', 'png': '画像', 'gif': '画像', 
                'bmp': '画像', 'tiff': '画像', 'tif': '画像', 'webp': '画像'
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