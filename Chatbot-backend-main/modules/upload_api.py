"""
📤 ファイルアップロードAPI
完全なRAG対応ドキュメント処理システム

エンドポイント:
- POST /upload-document: ファイルアップロード・処理
- GET /documents: アップロード済みドキュメント一覧
- DELETE /documents/{doc_id}: ドキュメント削除
- POST /documents/{doc_id}/toggle: ドキュメント有効/無効切り替え
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Request
from fastapi.responses import JSONResponse
from psycopg2.extensions import connection as Connection
import google.generativeai as genai

from .database import get_db
from .auth import get_current_user, check_usage_limits
from .document_processor import document_processor
from .resource import get_uploaded_resources_by_company_id, toggle_resource_active_by_id, remove_resource_by_id

# ロガー設定
logger = logging.getLogger(__name__)

# APIルーター
router = APIRouter(prefix="/api/v1", tags=["documents"])

# 定数
MAX_FILE_SIZE_MB = 50  # 最大ファイルサイズ
ALLOWED_EXTENSIONS = {
    '.pdf', '.xlsx', '.xls', '.docx', '.doc', 
    '.txt', '.csv', '.jpg', '.jpeg', '.png', '.gif', '.bmp'
}

@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    request: Request = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    """
    📤 ファイルアップロード・処理エンドポイント
    
    処理フロー:
    1️⃣ ファイル検証（サイズ・形式）
    2️⃣ 利用制限チェック
    3️⃣ テキスト抽出
    4️⃣ チャンク分割（300〜500 token）
    5️⃣ Supabase保存（document_sources + chunks）
    6️⃣ embedding生成を統合
    """
    try:
        logger.info(f"📤 ファイルアップロード開始: {file.filename}")
        
        # ユーザー情報取得
        user_id = current_user.get("id")
        company_id = current_user.get("company_id")
        user_role = current_user.get("role", "user")
        
        if not user_id or not company_id:
            raise HTTPException(status_code=400, detail="ユーザー情報が不完全です")
        
        # 社員アカウントのアップロード制限
        if user_role == "employee":
            raise HTTPException(
                status_code=403, 
                detail="社員アカウントはドキュメントをアップロードできません。管理者にお問い合わせください。"
            )
        
        # ファイル基本検証
        if not file.filename:
            raise HTTPException(status_code=400, detail="ファイル名が指定されていません")
        
        # ファイル拡張子チェック
        file_extension = '.' + file.filename.split('.')[-1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"サポートされていないファイル形式です。対応形式: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # ファイルサイズチェック
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400, 
                detail=f"ファイルサイズが大きすぎます ({file_size_mb:.2f} MB)。{MAX_FILE_SIZE_MB}MB以下のファイルを使用してください。"
            )
        
        # ファイルポインタをリセット
        await file.seek(0)
        
        # 利用制限チェック
        try:
            limits_check = check_usage_limits(user_id, "document_upload", db)
            
            if not limits_check["is_unlimited"] and not limits_check["allowed"]:
                raise HTTPException(
                    status_code=403,
                    detail=f"ドキュメントアップロード制限に達しました（上限: {limits_check['limit']}回）"
                )
        except HTTPException:
            raise
        except Exception as limit_error:
            logger.warning(f"利用制限チェックエラー: {limit_error}")
            # 制限チェックエラーの場合は処理を続行
        
        # ドキュメント処理実行
        logger.info(f"🔄 ドキュメント処理開始: {file.filename}")
        
        # Excelファイルの場合はレコードベース処理を使用
        if file_extension in ['.xlsx', '.xls']:
            logger.info(f"📊 Excelファイル検出、レコードベース処理を使用: {file.filename}")
            from .document_processor_record_based import document_processor_record_based
            processing_result = await document_processor_record_based.process_uploaded_file(
                file=file,
                user_id=user_id,
                company_id=company_id
            )
        else:
            # 他のファイル形式は従来の処理
            processing_result = await document_processor.process_uploaded_file(
                file=file,
                user_id=user_id,
                company_id=company_id
            )
        
        # 処理結果からembedding情報を取得
        embedding_result = {
            "successful_embeddings": processing_result.get("successful_embeddings", 0),
            "failed_embeddings": processing_result.get("failed_embeddings", 0),
            "total_chunks": processing_result.get("total_chunks", 0)
        }
        
        # 利用回数更新
        try:
            from .database import update_usage_count
            update_usage_count(user_id, "document_uploads_used", db)
            db.commit()
        except Exception as usage_error:
            logger.warning(f"利用回数更新エラー: {usage_error}")
        
        # レスポンス準備
        message = f"✅ {file.filename} のアップロード・処理が完了しました"
        if embedding_result:
            message += f"（Embedding: {embedding_result.get('successful_embeddings', 0)}個生成）"
        
        response_data = {
            "success": True,
            "message": message,
            "document": {
                "id": processing_result["document_id"],
                "filename": processing_result["filename"],
                "file_size_mb": processing_result["file_size_mb"],
                "text_length": processing_result["text_length"],
                "total_chunks": processing_result.get("total_chunks"),
                "saved_chunks": processing_result.get("saved_chunks")
            },
            "embedding_stats": embedding_result,
            "remaining_uploads": limits_check.get("remaining") if 'limits_check' in locals() else None
        }
        
        logger.info(f"✅ ファイルアップロード完了: {file.filename}")
        return JSONResponse(content=response_data, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ファイルアップロードエラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"ファイルアップロード中に予期せぬエラーが発生しました: {str(e)}"
        )

@router.get("/documents")
async def get_documents(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    """
    📋 アップロード済みドキュメント一覧取得
    """
    try:
        user_id = current_user.get("id")
        company_id = current_user.get("company_id")
        user_role = current_user.get("role", "user")
        
        if not company_id:
            raise HTTPException(status_code=400, detail="会社情報が見つかりません")
        
        # 管理者は全ドキュメント、一般ユーザーは自分のドキュメントのみ
        uploaded_by_filter = None if user_role == "admin" else user_id
        
        # ドキュメント一覧取得
        resources_result = await get_uploaded_resources_by_company_id(
            company_id=company_id,
            db=db,
            uploaded_by=uploaded_by_filter
        )
        
        documents = []
        for resource in resources_result.get("resources", []):
            # chunksテーブルからチャンク情報を取得
            chunk_info = await _get_document_chunk_info(resource["id"], db)
            
            document_info = {
                "id": resource["id"],
                "name": resource["name"],
                "type": resource["type"],
                "page_count": resource.get("page_count", 1),
                "uploaded_at": resource["timestamp"],
                "uploaded_by": resource["uploaded_by"],
                "uploader_name": resource["uploader_name"],
                "usage_count": resource["usage_count"],
                "last_used": resource["last_used"],
                "chunks": chunk_info
            }
            documents.append(document_info)
        
        return {
            "success": True,
            "documents": documents,
            "total_count": len(documents),
            "message": f"{len(documents)}件のドキュメントが見つかりました"
        }
        
    except Exception as e:
        logger.error(f"❌ ドキュメント一覧取得エラー: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"ドキュメント一覧の取得中にエラーが発生しました: {str(e)}"
        )

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    """
    🗑️ ドキュメント削除
    document_sourcesとchnksテーブルから削除
    """
    try:
        user_role = current_user.get("role", "user")
        
        # 管理者のみ削除可能
        if user_role != "admin":
            raise HTTPException(status_code=403, detail="ドキュメントの削除は管理者のみ可能です")
        
        # ドキュメント削除実行
        result = await remove_resource_by_id(doc_id, db)
        
        # chunksテーブルからも削除（CASCADE制約で自動削除されるはず）
        try:
            from supabase_adapter import get_supabase_client
            supabase = get_supabase_client()
            
            # chunksテーブルから削除
            chunks_delete = supabase.table("chunks").delete().eq("doc_id", doc_id)
            chunks_result = chunks_delete.execute()
            
            logger.info(f"🗑️ チャンク削除完了: {doc_id}")
            
        except Exception as chunk_error:
            logger.warning(f"チャンク削除エラー: {chunk_error}")
        
        return {
            "success": True,
            "message": result["message"],
            "deleted_document": result["name"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ドキュメント削除エラー: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"ドキュメント削除中にエラーが発生しました: {str(e)}"
        )

@router.post("/documents/{doc_id}/toggle")
async def toggle_document_active(
    doc_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Connection = Depends(get_db)
):
    """
    🔄 ドキュメント有効/無効切り替え
    document_sourcesとchnksテーブルの両方を更新
    """
    try:
        user_role = current_user.get("role", "user")
        
        # 管理者のみ切り替え可能
        if user_role != "admin":
            raise HTTPException(status_code=403, detail="ドキュメントの状態変更は管理者のみ可能です")
        
        # document_sourcesテーブルの状態切り替え
        result = await toggle_resource_active_by_id(doc_id, db)
        
        # chunksテーブルの状態も同期
        try:
            from supabase_adapter import get_supabase_client
            supabase = get_supabase_client()
            
            # chunksテーブルの更新日時を同期（activeフラグはdocument_sourcesで管理）
            chunks_update = supabase.table("chunks").update({
                "updated_at": "now()"
            }).eq("doc_id", doc_id)
            
            chunks_result = chunks_update.execute()
            logger.info(f"🔄 チャンク状態同期完了: {doc_id} -> {result['active']}")
            
        except Exception as chunk_error:
            logger.warning(f"チャンク状態同期エラー: {chunk_error}")
        
        return {
            "success": True,
            "message": result["message"],
            "document_name": result["name"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ドキュメント状態切り替えエラー: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"ドキュメント状態切り替え中にエラーが発生しました: {str(e)}"
        )


async def _get_document_chunk_info(doc_id: str, db: Connection) -> Dict[str, Any]:
    """ドキュメントのチャンク情報を取得"""
    try:
        from supabase_adapter import get_supabase_client
        supabase = get_supabase_client()
        
        # chunksテーブルから統計情報を取得
        chunks_query = supabase.table("chunks").select("id,chunk_index").eq("doc_id", doc_id)
        chunks_result = chunks_query.execute()
        
        if chunks_result.data:
            total_chunks = len(chunks_result.data)
            active_chunks = len(chunks_result.data)  # All chunks are now considered active
            
            return {
                "total_chunks": total_chunks,
                "active_chunks": active_chunks,
                "inactive_chunks": total_chunks - active_chunks,
                "chunk_indices": [c.get("chunk_index", 0) for c in chunks_result.data]
            }
        else:
            return {
                "total_chunks": 0,
                "active_chunks": 0,
                "inactive_chunks": 0,
                "chunk_indices": []
            }
            
    except Exception as e:
        logger.warning(f"チャンク情報取得エラー: {e}")
        return {
            "total_chunks": 0,
            "active_chunks": 0,
            "inactive_chunks": 0,
            "chunk_indices": []
        }

# エラーハンドラー
@router.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTPエラーハンドラー"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )