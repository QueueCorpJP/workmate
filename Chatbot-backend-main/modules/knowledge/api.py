"""
知識ベースAPI関数モジュール
ファイルとURLの処理、リソースの管理を行うAPI関数を提供します
"""
import uuid
import logging
import pandas as pd
import asyncio
from datetime import datetime
from fastapi import HTTPException, UploadFile, File, Depends, Request
from io import BytesIO
import PyPDF2
import traceback
from typing import Dict, List, Optional, Tuple, Any, Union
from psycopg2.extensions import connection as Connection
from ..database import get_db, update_usage_count, ensure_string
from ..auth import check_usage_limits
from .base import knowledge_base, _update_knowledge_base, _update_knowledge_base_from_list, get_active_resources
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
from .unnamed_column_handler import UnnamedColumnHandler
import tempfile
from fastapi.responses import JSONResponse

# ロガーの設定
logger = logging.getLogger(__name__)

# 共通のエラーメッセージ
EMPLOYEE_UPLOAD_ERROR = "社員アカウントはドキュメントをアップロードできません。管理者にお問い合わせください。"
LIMIT_REACHED_ERROR = "申し訳ございません。デモ版のドキュメントアップロード制限（{limit}回）に達しました。"
INVALID_FILE_ERROR = "無効なファイル形式です。Excel、PDF、Word、CSV、テキスト、画像ファイル（.xlsx、.xls、.pdf、.doc、.docx、.csv、.txt、.jpg、.png等）のみ対応しています。"
PDF_SIZE_ERROR = "PDFファイルが大きすぎます ({size:.2f} MB)。10MB以下のファイルを使用するか、ファイルを分割してください。"
VIDEO_SIZE_ERROR = "ビデオファイルが大きすぎます ({size:.2f} MB)。500MB以下のファイルを使用するか、ファイルを分割してください。"
TIMEOUT_ERROR = "処理がタイムアウトしました。ファイルが大きすぎるか、複雑すぎる可能性があります。ファイルを分割するか、より小さなファイルを使用してください。"

# 大きなファイル処理用の設定
MAX_PROCESSING_TIME = 300  # 5分の処理時間制限
BATCH_SIZE_FOR_DB = 100    # データベース保存時のバッチサイズ

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
    
    try:
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
    except HTTPException as e:
        if e.status_code == 404:
            # 利用制限情報が見つからない場合は自動作成
            logger.warning(f"ユーザー {user_id} の利用制限情報が見つかりません。自動作成を試行します。")
            try:
                # 利用制限レコードを直接作成
                from supabase_adapter import insert_data
                
                # ユーザー情報を取得して正しいuser_idを使用
                from supabase_adapter import select_data
                user_result = select_data("users", columns="id, email, role", filters={"id": user_id})
                
                if not user_result or not user_result.data:
                    # user_idで見つからない場合はcompany_idで検索
                    user_result = select_data("users", columns="id, email, role", filters={"company_id": user_id})
                
                if user_result and user_result.data:
                    actual_user = user_result.data[0]
                    actual_user_id = actual_user.get("id")
                    user_email = actual_user.get("email", "")
                    user_role = actual_user.get("role", "user")
                    
                    logger.info(f"実際のユーザーID: {actual_user_id}, email: {user_email}, role: {user_role}")
                    
                    # デフォルトの利用制限を設定
                    is_admin = user_role == "admin" or user_email == "queue@queueu-tech.jp"
                    limit_data = {
                        "user_id": actual_user_id,
                        "document_uploads_used": 0,
                        "document_uploads_limit": 999999 if is_admin else 2,
                        "questions_used": 0,
                        "questions_limit": 999999 if is_admin else 10,
                        "is_unlimited": is_admin
                    }
                else:
                    logger.error(f"ユーザーID {user_id} に対応するユーザーが見つかりません")
                    raise Exception(f"ユーザーID {user_id} が存在しません")
                
                insert_data("usage_limits", limit_data)
                logger.info(f"ユーザー {user_id} の利用制限情報を作成しました。")
                
                # 再度チェック（正しいuser_idを使用）
                limits_check = check_usage_limits(actual_user_id, "document_upload", db)
                
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
            except Exception as create_error:
                logger.error(f"利用制限情報の自動作成に失敗しました: {str(create_error)}")
                # フォールバック：デフォルト値を使用（管理者の場合は無制限）
                logger.info(f"フォールバック：ユーザー {user_id} にデフォルト制限を適用します。")
                return {
                    "allowed": True,
                    "remaining": 100,  # デフォルト制限
                    "limit_reached": False
                }
        else:
            # その他のHTTPExceptionは再発生
            raise

async def _record_document_source(
    name: str, 
    doc_type: str, 
    page_count: int, 
    content: str, 
    user_id: str, 
    company_id: str, 
    db: Connection
) -> None:
    """ドキュメントソースをデータベースに記録する（大きなコンテンツ対応）"""
    import time
    
    try:
        start_time = time.time()
        document_id = str(uuid.uuid4())
        
        # コンテンツサイズをチェック
        content_str = ensure_string(content, for_db=True)
        content_size_mb = len(content_str.encode('utf-8')) / (1024 * 1024)
        
        logger.info(f"ドキュメント保存開始: {name}, サイズ: {content_size_mb:.2f}MB")
        
        # 2MB以上の場合は最初から分割保存（statement timeout対策）
        if content_size_mb > 2:  # 2MB以上の場合
            logger.info(f"大きなコンテンツを分割保存します: {content_size_mb:.2f}MB")
            
            # コンテンツを分割（1MB程度のチャンク）
            chunk_size = 800000  # 800KB程度のチャンク（安全マージン）
            content_chunks = []
            for i in range(0, len(content_str), chunk_size):
                chunk = content_str[i:i + chunk_size]
                content_chunks.append(chunk)
            
            logger.info(f"コンテンツを{len(content_chunks)}個のチャンクに分割")
            
            # メインレコードを先に保存（完全なコンテンツを保存）
            # Supabaseアダプターを使用してメインレコードを保存
            from supabase_adapter import insert_data
            main_record = {
                "id": document_id,
                "name": name,
                "type": doc_type,
                "page_count": page_count,
                "content": content_str,  # 完全なコンテンツを保存
                "uploaded_by": user_id,
                "company_id": company_id,
                "uploaded_at": datetime.now().isoformat(),
                "active": True
            }
            
            try:
                insert_data("document_sources", main_record)
                logger.info(f"メインレコード保存完了: {document_id} (完全なコンテンツ: {content_size_mb:.2f}MB)")
                doc_id = document_id  # 成功時にdoc_idを設定
            except Exception as main_error:
                logger.error(f"メインレコード保存エラー: {str(main_error)}")
                doc_id = None  # 初期化
                
                # statement timeoutの場合はチャンク分割保存を試行
                error_str = str(main_error)
                if "statement timeout" in error_str.lower() or "57014" in error_str:
                    logger.warning("Statement timeoutが発生 - チャンク分割保存に切り替え")
                    
                    # メインレコードは要約版で保存
                    summary_content = content_str[:1000] + f"...\n\n[このドキュメントは{len(content_chunks)}個のチャンクに分割されています。総サイズ: {content_size_mb:.2f}MB]"
                    main_record["content"] = summary_content
                    
                    try:
                        result = insert_data("document_sources", main_record)
                        if result and result.data:
                            doc_id = result.data[0]["id"]
                            logger.info(f"要約版メインレコード保存成功: {doc_id}")
                        else:
                            logger.error("要約版メインレコード保存に失敗")
                            doc_id = None
                    except Exception as summary_error:
                        logger.error(f"要約版メインレコード保存エラー: {str(summary_error)}")
                        doc_id = None
                
                elif "document_sources_uploaded_by_fkey" in error_str:
                    logger.warning(f"ユーザー '{user_id}' が存在しません - company_idで代替保存を試行")
                    try:
                        # company_idから代替ユーザーを検索
                        from supabase_adapter import select_data
                        company_users = select_data(
                            "users", 
                            columns="id", 
                            filters={"company_id": company_id}
                        )
                        
                        if company_users.data and len(company_users.data) > 0:
                            alternative_user_id = company_users.data[0]["id"]
                            logger.info(f"代替ユーザーを発見: {alternative_user_id}")
                            
                            # 代替ユーザーIDで再保存
                            main_record["uploaded_by"] = alternative_user_id
                            result = insert_data("document_sources", main_record)
                            
                            if result and result.data:
                                logger.info(f"代替ユーザーIDでメインレコード保存成功: {alternative_user_id}")
                                doc_id = result.data[0]["id"]
                            else:
                                logger.error("代替ユーザーIDでもメインレコード保存に失敗")
                                doc_id = None
                        else:
                            logger.error(f"Company ID {company_id} に関連するユーザーが見つかりません")
                            doc_id = None
                            
                    except Exception as alt_error:
                        logger.error(f"代替ユーザー検索エラー: {str(alt_error)}")
                        doc_id = None
            
            # チャンク保存処理（メインレコードが要約版の場合のみ）
            if doc_id and "[このドキュメントは" in main_record.get("content", ""):
                logger.info(f"チャンク保存開始: {len(content_chunks)} 個のチャンク")
                successful_chunks = 0
                for i, chunk in enumerate(content_chunks):
                    try:
                        chunk_record = {
                            "id": str(uuid.uuid4()),
                            "name": f"{name}_chunk_{i+1}",
                            "type": f"{doc_type}_CHUNK",
                            "page_count": 0,
                            "content": chunk,
                            "uploaded_by": main_record["uploaded_by"],  # メインレコードと同じuser_idを使用
                            "company_id": company_id,
                            "uploaded_at": datetime.now().isoformat(),
                            "active": True,
                            "parent_id": doc_id  # メインレコードへの参照
                        }
                        
                        chunk_result = insert_data("document_sources", chunk_record)
                        if not chunk_result or not chunk_result.data:
                            logger.warning(f"チャンク {i+1} の保存に失敗")
                        else:
                            successful_chunks += 1
                            logger.info(f"チャンク {i+1}/{len(content_chunks)} 保存完了")
                            
                    except Exception as chunk_error:
                        logger.error(f"チャンク {i+1} 保存エラー: {str(chunk_error)}")
                        continue
                
                logger.info(f"チャンク保存完了: {successful_chunks}/{len(content_chunks)} 個成功")
            elif doc_id and "[このドキュメントは" not in main_record.get("content", ""):
                logger.info("完全なコンテンツが保存されたため、チャンク保存は不要")
            elif not doc_id:
                logger.error("メインレコード保存に失敗したため、チャンク保存をスキップ")
            
            # データベースコミット（dbがNoneの場合は安全にスキップ）
            if db is not None:
                try:
                    db.commit()
                except AttributeError:
                    # dbオブジェクトにcommitメソッドがない場合はスキップ
                    logger.debug("データベースオブジェクトにcommitメソッドがありません")
            else:
                logger.debug("データベース接続がNullのためcommitをスキップ")
            
            logger.info(f"分割保存完了: {time.time() - start_time:.1f}秒")
            
        else:
            # 通常サイズの場合は一括保存
            try:
                from supabase_adapter import insert_data
                record = {
                    "id": document_id,
                    "name": name,
                    "type": doc_type,
                    "page_count": page_count,
                    "content": content_str,
                    "uploaded_by": user_id,
                    "company_id": company_id,
                    "uploaded_at": datetime.now().isoformat(),
                    "active": True
                }
                
                insert_data("document_sources", record)
                logger.info(f"通常保存完了: {time.time() - start_time:.1f}秒")
                
            except Exception as normal_error:
                logger.error(f"通常保存エラー: {str(normal_error)}")
                
                # 外部キー制約エラーの場合はユーザー情報を確認
                error_str = str(normal_error)
                if "document_sources_uploaded_by_fkey" in error_str:
                    logger.warning(f"ユーザー '{user_id}' が存在しません - company_idで代替保存を試行")
                    try:
                        # company_idから代替ユーザーを検索
                        from supabase_adapter import select_data
                        company_users = select_data(
                            "users", 
                            columns="id", 
                            filters={"company_id": company_id}
                        )
                        
                        if company_users.data and len(company_users.data) > 0:
                            alternative_user_id = company_users.data[0]["id"]
                            logger.info(f"代替ユーザーを発見: {alternative_user_id}")
                            
                            # 代替ユーザーIDで再保存
                            record["uploaded_by"] = alternative_user_id
                            result = insert_data("document_sources", record)
                            
                            if result and result.data:
                                logger.info(f"代替ユーザーIDで通常保存成功: {alternative_user_id}")
                                doc_id = result.data[0]["id"]
                            else:
                                logger.error("代替ユーザーIDでも通常保存に失敗")
                                doc_id = None
                        else:
                            logger.error(f"Company ID {company_id} に関連するユーザーが見つかりません")
                            doc_id = None
                            
                    except Exception as alt_error:
                        logger.error(f"代替ユーザー検索エラー: {str(alt_error)}")
                        doc_id = None
                
                # データベースコミット（dbがNoneの場合は安全にスキップ）
                if db is not None:
                    try:
                        db.commit()
                    except AttributeError:
                        # dbオブジェクトにcommitメソッドがない場合はスキップ
                        logger.debug("データベースオブジェクトにcommitメソッドがありません")
                else:
                    logger.debug("データベース接続がNullのためcommitをスキップ")
        
        # 会社のソースリストに追加
        if company_id:
            if company_id not in knowledge_base.company_sources:
                knowledge_base.company_sources[company_id] = []
            if name not in knowledge_base.company_sources[company_id]:
                knowledge_base.company_sources[company_id].append(name)
                
    except Exception as e:
        logger.error(f"ドキュメントソース保存エラー: {str(e)}")
        # データベースエラーでも処理は継続（知識ベースは更新済み）
        raise HTTPException(status_code=500, detail=f"ドキュメントの保存中にエラーが発生しました: {str(e)}")

def _update_source_info(source_name: str) -> None:
    """ソース情報を更新する"""
    if source_name not in knowledge_base.sources:
        knowledge_base.sources[source_name] = {}  # 辞書として初期化
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
        
        # アップロード制限のチェック（エラーハンドリング付き）
        try:
            limits = _check_upload_limits(user_id, db)
        except HTTPException as http_error:
            # HTTPExceptionはそのまま再発生
            raise http_error
        except Exception as limit_error:
            logger.warning(f"URL処理の利用制限チェックでエラーが発生しました: {str(limit_error)}")
            # 利用制限チェックでエラーが発生した場合はデフォルト値を設定
            limits = {"remaining": None, "limit_reached": False}
        
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
            await _record_document_source(url, "URL", 1, processed_text, user_id, company_id, db)
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

async def process_file(file: UploadFile = File(...), request: Request = None, user_id: str = None, company_id: str = None, db: Connection = None):
    """ファイルを処理して知識ベースを更新する"""
    logger.info(f"ファイル処理開始: {file.filename}, ユーザーID: {user_id}, 会社ID: {company_id}")
    
    # 初期化
    remaining_uploads = None
    limit_reached = False
    page_count = 1
    
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
        # アップロード制限のチェック（エラーハンドリング付き）
        try:
            limits = _check_upload_limits(user_id, db)
            remaining_uploads = limits.get("remaining")
            limit_reached = limits.get("limit_reached", False)
        except HTTPException as http_error:
            # HTTPExceptionはそのまま再発生
            raise http_error
        except Exception as limit_error:
            logger.warning(f"利用制限チェックでエラーが発生しました: {str(limit_error)}")
            # 利用制限チェックでエラーが発生した場合はデフォルト値を設定
            remaining_uploads = None
            limit_reached = False
        
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
        
        try:
            # 検知されたファイル形式に基づいて処理を実行
            if detected_type == 'excel' or file_extension in ['xlsx', 'xls']:
                logger.info(f"Excelファイル処理開始: {file.filename}")
                
                # 大きなExcelファイルの処理時間制限
                processing_start_time = asyncio.get_event_loop().time()
                
                try:
                    # Google Sheets APIを使用してExcelファイルを処理
                    # OAuth2トークンを優先的に使用（requestがある場合のみ）
                    access_token = None
                    if request and hasattr(request, 'state'):
                        access_token = getattr(request.state, 'google_access_token', None)
                    
                    service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
                    
                    logger.info(f"Google Sheets API処理開始 - access_token: {'あり' if access_token else 'なし'}, service_account: {'あり' if service_account_file else 'なし'}")
                    
                    # 大きなファイルの場合は処理前に警告
                    if file_size_mb > 3:
                        logger.info(f"大きなExcelファイル（{file_size_mb:.2f}MB）を処理します - 時間がかかる可能性があります")
                        # 処理前の小さな遅延
                        await asyncio.sleep(1)
                    
                    # タイムアウト付きでExcel処理を実行
                    try:
                        data_list, sections, extracted_text = await asyncio.wait_for(
                            process_excel_file_with_sheets_api(
                                contents, 
                                file.filename, 
                                access_token, 
                                service_account_file
                            ),
                            timeout=MAX_PROCESSING_TIME  # 5分のタイムアウト
                        )
                    except asyncio.TimeoutError:
                        logger.error(f"Excel処理がタイムアウトしました: {file.filename} ({file_size_mb:.2f}MB)")
                        raise HTTPException(
                            status_code=408, 
                            detail=f"Excelファイルの処理がタイムアウトしました（{file_size_mb:.2f}MB）。ファイルを分割するか、より小さなファイルを使用してください。"
                        )
                    
                    # 処理時間をログ出力
                    processing_time = asyncio.get_event_loop().time() - processing_start_time
                    logger.info(f"Excel処理時間: {processing_time:.1f}秒")
                    
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
                    
                    logger.info(f"Excel処理完了（Google Sheets API使用）: {len(data_list)} レコード, {page_count} シート, {processing_time:.1f}秒")
                    
                    # データベース保存用にデータを準備
                    df = None  # DataFrameは使用しない
                    
                except Exception as e:
                    logger.warning(f"Google Sheets API処理エラー、従来の処理にフォールバック: {str(e)}")
                    # フォールバック：従来のpandas処理
                    try:
                        df, sections, extracted_text = await asyncio.wait_for(
                            asyncio.to_thread(process_excel_file, contents, file.filename),
                            timeout=MAX_PROCESSING_TIME
                        )
                        # ⚠️ 重要修正: data_listをNoneに設定しない（フォールバック処理でも知識ベース更新を確実に実行）
                        # data_list = None  # この行をコメントアウト
                        
                        # ⚠️ 重要修正: フォールバック処理でextracted_textのUnnamed修正を強制実行
                        from .unnamed_column_handler import UnnamedColumnHandler
                        handler = UnnamedColumnHandler()
                        
                        # extracted_textのUnnamedパターンを修正
                        if extracted_text and "Unnamed:" in extracted_text:
                            lines = extracted_text.split('\n')
                            fixed_lines = []
                            
                            for line in lines:
                                if "Unnamed:" in line:
                                    # Unnamed: X パターンを修正
                                    import re
                                    line = re.sub(r'Unnamed:\s*\d+', lambda m: f"データ{m.group().split(':')[1].strip() if ':' in m.group() else '1'}", line)
                                fixed_lines.append(line)
                            
                            extracted_text = '\n'.join(fixed_lines)
                            logger.info("フォールバック処理でextracted_textのUnnamed修正を実行")
                        
                        # Excelファイルのシート数を取得
                        try:
                            excel_file = BytesIO(contents)
                            df_dict = pd.read_excel(excel_file, sheet_name=None)
                            
                            # 各シートにUnnamed処理を適用
                            for sheet_name, sheet_df in df_dict.items():
                                if not sheet_df.empty:
                                    try:
                                        fixed_df, modifications = handler.fix_dataframe(sheet_df, f"{file.filename}:{sheet_name}")
                                        df_dict[sheet_name] = fixed_df
                                        if modifications:
                                            logger.info(f"api.py Excel処理 - シート '{sheet_name}' のUnnamed修正: {', '.join(modifications)}")
                                    except Exception as fix_error:
                                        logger.warning(f"シート '{sheet_name}' のUnnamed修正でエラー: {str(fix_error)} - 元のデータを使用")
                                        # エラーの場合は元のシートをそのまま使用
                        
                            page_count = len(df_dict)
                        except Exception as excel_error:
                            logger.warning(f"Excelシート数取得エラー: {str(excel_error)}")
                            page_count = 1
                            
                    except asyncio.TimeoutError:
                        logger.error(f"Excel従来処理もタイムアウトしました: {file.filename}")
                        raise HTTPException(
                            status_code=408, 
                            detail=f"Excelファイルの処理がタイムアウトしました。ファイルサイズ（{file_size_mb:.2f}MB）が大きすぎます。"
                        )

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
                    from .unnamed_column_handler import UnnamedColumnHandler
                    handler = UnnamedColumnHandler()
                    
                    df = pd.DataFrame({
                        'section': ["Word処理エラー"],
                        'content': [f"Wordファイル処理中にエラーが発生しました: {str(word_error)}"],
                        'source': ['Word'],
                        'file': [file.filename],
                        'url': [None]
                    })
                    
                    # エラー時のDataFrameもUnnamed処理を適用
                    try:
                        df, error_modifications = handler.fix_dataframe(df, f"{file.filename}_word_error")
                        if error_modifications:
                            logger.debug(f"Word処理エラーのUnnamed修正: {', '.join(error_modifications)}")
                    except:
                        pass  # エラー処理中のエラーは無視
                    
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
                    from .unnamed_column_handler import UnnamedColumnHandler
                    handler = UnnamedColumnHandler()
                    
                    df = pd.DataFrame({
                        'section': ["画像処理エラー"],
                        'content': [f"画像ファイル処理中にエラーが発生しました: {str(img_error)}"],
                        'source': ['画像'],
                        'file': [file.filename],
                        'url': [None]
                    })
                    
                    # エラー時のDataFrameもUnnamed処理を適用
                    try:
                        df, error_modifications = handler.fix_dataframe(df, f"{file.filename}_image_error")
                        if error_modifications:
                            logger.debug(f"画像処理エラーのUnnamed修正: {', '.join(error_modifications)}")
                    except:
                        pass  # エラー処理中のエラーは無視
                    
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
                    from .unnamed_column_handler import UnnamedColumnHandler
                    handler = UnnamedColumnHandler()
                    
                    df = pd.DataFrame({
                        'section': ["エラー"],
                        'content': [f"PDFファイル処理中にエラーが発生しました: {str(pdf_ex)}"],
                        'source': ['PDF'],
                        'file': [file.filename],
                        'url': [None]
                    })
                    
                    # エラー時のDataFrameもUnnamed処理を適用
                    try:
                        df, error_modifications = handler.fix_dataframe(df, f"{file.filename}_pdf_error")
                        if error_modifications:
                            logger.debug(f"PDF処理エラーのUnnamed修正: {', '.join(error_modifications)}")
                    except:
                        pass  # エラー処理中のエラーは無視
                    
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
                from .unnamed_column_handler import UnnamedColumnHandler
                handler = UnnamedColumnHandler()
                
                df = pd.DataFrame({
                    'section': ["一般情報"],
                    'content': ["ファイルからテキストを抽出できませんでした。"],
                    'source': [file_extension.upper()],
                    'file': [file.filename],
                    'url': [None]
                })
                
                # 空のDataFrameもUnnamed処理を適用
                try:
                    df, empty_modifications = handler.fix_dataframe(df, f"{file.filename}_empty")
                    if empty_modifications:
                        logger.debug(f"空DataFrame処理のUnnamed修正: {', '.join(empty_modifications)}")
                except:
                    pass  # エラー処理中のエラーは無視
                
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
        knowledge_base_updated = False  # 更新状況をトラッキング
        
        if 'data_list' in locals() and data_list:
            # 新しいGoogle Sheets API処理の場合：data_listを直接使用
            logger.info(f"data_listを使用して知識ベースを更新: {len(data_list)} レコード")
            _update_knowledge_base_from_list(data_list, extracted_text, is_file=True, source_name=file.filename, company_id=company_id)
            knowledge_base_updated = True
        elif df is not None and not df.empty:
            # 従来のpandas処理の場合：DataFrameを使用
            logger.info(f"DataFrameを使用して知識ベースを更新: {len(df)} 行")
            # ファイル列が存在することを確認
            if 'file' not in df.columns:
                df['file'] = file.filename
                
            # すべての列の値を適切に変換（NULL値はそのまま保持）
            for col in df.columns:
                # NULLでない値のみを文字列に変換
                df[col] = df[col].apply(lambda x: str(x) if pd.notna(x) else None)
                
            # 知識ベースを更新
            _update_knowledge_base(df, extracted_text, is_file=True, source_name=file.filename, company_id=company_id)
            knowledge_base_updated = True
        else:
            # データが空の場合でも最低限のエントリを作成
            logger.warning(f"データが空または無効です - 最低限のエントリを作成: {file.filename}")
            if file.filename not in knowledge_base.sources:
                knowledge_base.sources[file.filename] = {}
            knowledge_base.sources[file.filename]["処理結果"] = extracted_text or f"ファイル '{file.filename}' を処理しました"
            knowledge_base_updated = True
        
        # 知識ベース更新完了をログ出力
        logger.info(f"知識ベース更新完了: {knowledge_base_updated}, ソース数: {len(knowledge_base.sources)}")
        
        # ソース情報を更新
        _update_source_info(file.filename)
        
        # ユーザーIDがある場合はドキュメントアップロードカウントを更新
        if user_id:
            updated_limits = update_usage_count(user_id, "document_uploads_used", db)
            if updated_limits:
                remaining_uploads = updated_limits["document_uploads_limit"] - updated_limits["document_uploads_used"]
                limit_reached = remaining_uploads <= 0
            else:
                # 利用制限が取得できない場合のデフォルト値
                logger.warning(f"利用制限の更新に失敗しました - user_id: {user_id}")
                remaining_uploads = None
                limit_reached = False
            
            # ドキュメントソースを記録
            await _record_document_source(file.filename, file_extension.upper(), page_count, extracted_text, user_id, company_id, db)
            # データベースコミット（dbがNoneの場合は安全にスキップ）
            if db is not None:
                try:
                    db.commit()
                except AttributeError:
                    # dbオブジェクトにcommitメソッドがない場合はスキップ
                    logger.debug("データベースオブジェクトにcommitメソッドがありません")
            else:
                logger.debug("データベース接続がNullのためcommitをスキップ")
        
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
    # デバッグ情報をログに出力
    logger.info(f"get_uploaded_resources 開始 - knowledge_base.sources の型: {type(knowledge_base.sources)}")
    logger.info(f"knowledge_base.sources の内容: {knowledge_base.sources}")
    logger.info(f"knowledge_base.source_info の内容: {knowledge_base.source_info}")
    
    resources = []
    
    # knowledge_base.sources が辞書の場合とリストの場合を両方対応
    sources_to_process = []
    if isinstance(knowledge_base.sources, dict):
        logger.info("knowledge_base.sources は辞書として扱います")
        sources_to_process = list(knowledge_base.sources.keys())
    elif isinstance(knowledge_base.sources, list):
        logger.info("knowledge_base.sources はリストとして扱います")
        sources_to_process = knowledge_base.sources
    else:
        logger.warning(f"knowledge_base.sources の型が予期しない型です: {type(knowledge_base.sources)}")
        sources_to_process = []
    
    logger.info(f"処理対象のソース数: {len(sources_to_process)}")
    
    for source in sources_to_process:
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
        
        logger.info(f"リソース追加: {source} (タイプ: {resource_type})")
    
    logger.info(f"get_uploaded_resources 完了 - {len(resources)}件のリソース")
    
    return {
        "resources": resources,
        "message": f"{len(resources)}件のリソースが見つかりました"
    }

async def cleanup_unnamed_columns(company_id: str = None):
    """既存のデータベースコンテンツのUnnamedカラムをクリーンアップする"""
    
    try:
        handler = UnnamedColumnHandler()
        updated_count = 0
        
        # knowledge_baseの内容を確認・修正
        for source_name in list(knowledge_base.sources.keys()):
            sections = knowledge_base.sources[source_name]
            updated_sections = {}
            
            for section_name, content in sections.items():
                # contentを行ごとに分割して処理
                lines = content.split('\n')
                updated_lines = []
                
                for line in lines:
                    # テーブル形式の行を検出（|で区切られている）
                    if '|' in line and line.count('|') >= 2:
                        # マークダウンテーブル形式の処理
                        parts = [part.strip() for part in line.split('|')]
                        if parts and parts[0] == '':
                            parts = parts[1:]  # 最初の空要素を削除
                        if parts and parts[-1] == '':
                            parts = parts[:-1]  # 最後の空要素を削除
                        
                        # unnamedパターンを修正
                        updated_parts = []
                        for i, part in enumerate(parts):
                            if handler._is_unnamed_pattern(part):
                                if i == 0 and part.strip() in ['', 'unnamed', 'Unnamed']:
                                    # 最初のカラムが空の場合はスキップ
                                    continue
                                else:
                                    # 意味のある名前に変更
                                    updated_parts.append(f"カラム{i+1}")
                            else:
                                updated_parts.append(part)
                        
                        if updated_parts:
                            updated_lines.append('| ' + ' | '.join(updated_parts) + ' |')
                        else:
                            updated_lines.append(line)
                    else:
                        # 通常の行はそのまま
                        updated_lines.append(line)
                
                updated_content = '\n'.join(updated_lines)
                if updated_content != content:
                    updated_sections[section_name] = updated_content
                    updated_count += 1
                else:
                    updated_sections[section_name] = content
            
            # 更新されたsectionsで置換
            knowledge_base.sources[source_name] = updated_sections
        
        logger.info(f"データベースクリーンアップ完了: {updated_count}個のセクションを更新")
        
        return {
            "success": True,
            "updated_sections": updated_count,
            "message": f"{updated_count}個のセクションのUnnamedカラムを修正しました"
        }
        
    except Exception as e:
        logger.error(f"データベースクリーンアップエラー: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "データベースクリーンアップ中にエラーが発生しました"
        }