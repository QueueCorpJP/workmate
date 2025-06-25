"""
メインアプリケーションファイル
FastAPIアプリケーションの設定とルーティングを行うmain.py
"""
import os
import os.path
import datetime
import traceback
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.exceptions import RequestValidationError
# モジュールのインポート
from modules.config import setup_logging, setup_gemini, get_cors_origins, get_environment
from modules.company import DEFAULT_COMPANY_NAME
from modules.database import get_db, init_db, get_all_users, get_demo_usage_stats, create_user, SupabaseConnection
from supabase_adapter import get_supabase_client, select_data, insert_data, update_data, delete_data
from modules.models import (
    ChatMessage, ChatResponse, ChatHistoryItem, AnalysisResult,
    EmployeeUsageItem, EmployeeUsageResult, UrlSubmission,
    CompanyNameResponse, CompanyNameRequest, ResourcesResult,
    ResourceToggleResponse, ResourceSpecialUpdateRequest, UserLogin, UserRegister, UserResponse,
    UserWithLimits, DemoUsageStats, AdminUserCreate, UpgradePlanRequest,
    UpgradePlanResponse, SubscriptionInfo
)
from modules.knowledge import process_url, process_file, get_knowledge_base_info
from modules.knowledge.google_drive import GoogleDriveHandler
from modules.chat import process_chat, process_chat_chunked, set_model as set_chat_model
from modules.admin import (
    get_chat_history, get_chat_history_paginated, analyze_chats, get_employee_details,
    get_employee_usage, get_uploaded_resources, toggle_resource_active,
    get_company_employees, set_model as set_admin_model, delete_resource,
    get_chat_history_by_company_paginated, get_chat_history_by_company
)
from modules.company import get_company_name, set_company_name
from modules.auth import get_current_user, get_current_admin, register_new_user, get_admin_or_user, get_company_admin, get_user_with_delete_permission, get_user_creation_permission
from modules.resource import get_uploaded_resources_by_company_id, toggle_resource_active_by_id, remove_resource_by_id
import json
from modules.validation import validate_login_input, validate_user_input
import csv
import io

# ロギングの設定
logger = setup_logging()

# Gemini APIの設定
model = setup_gemini()

# モデルの設定
set_chat_model(model)
set_admin_model(model)

# FastAPIアプリケーションの作成
app = FastAPI()

# グローバル例外ハンドラー
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """すべての例外をキャッチして適切なレスポンスを返す"""
    # エラーの詳細をログに記録
    logger.error(f"グローバル例外ハンドラーがエラーをキャッチしました: {str(exc)}")
    logger.error(traceback.format_exc())
    
    # 'int' object has no attribute 'strip' エラーの特別処理
    if "'int' object has no attribute 'strip'" in str(exc):
        return JSONResponse(
            status_code=500,
            content={"detail": "データ型エラーが発生しました。管理者にご連絡してください。"}
        )
    
    # その他の例外は通常のエラーレスポンスを返す
    return JSONResponse(
        status_code=500,
        content={"detail": f"サーバーエラーが発生しました: {str(exc)}"}
    )

# バリデーションエラーハンドラー
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """リクエストバリデーションエラーを処理する"""
    logger.error(f"バリデーションエラー: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": f"リクエストデータが無効です: {str(exc)}"}
    )

# CORSミドルウェアの設定
# 環境別に適切なオリジンを設定
environment = get_environment()
print(f"🌍 実行環境: {environment}")

# 環境に応じたCORSオリジンを取得
origins = get_cors_origins()
print(f"🔗 CORS許可オリジン: {origins}")

# CORSミドルウェアを最初に追加して優先度を上げる
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if environment == "production" else ["*"],  # 本番環境では限定、開発環境では全許可
    allow_credentials=environment == "production",  # 本番環境でのみクレデンシャル許可
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,  # プリフライトリクエストのキャッシュ時間（秒）
)

# リクエストロギングミドルウェア
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        raise

# アプリケーション起動時にデータベースを初期化
init_db()

# データベース整合性をチェック
try:
    from modules.database import ensure_usage_limits_integrity, get_db
    print("起動時データベース整合性チェックを実行中...")
    db_connection = SupabaseConnection()
    fixed_count = ensure_usage_limits_integrity(db_connection)
    if fixed_count > 0:
        print(f"起動時整合性チェック完了。{fixed_count}個のusage_limitsレコードを修正しました")
    else:
        print("起動時整合性チェック完了。修正が必要なレコードはありませんでした")
    db_connection.close()
except Exception as e:
    print(f"起動時整合性チェックでエラーが発生しましたが、アプリケーションは継続します。{str(e)}")

# 認証関連エンドポイント
@app.post("/chatbot/api/auth/login", response_model=UserWithLimits)
async def login(credentials: UserLogin, db: SupabaseConnection = Depends(get_db)):
    """ユーザーログイン"""
    # 入力値バリデーション
    is_valid, errors = validate_login_input(credentials.email, credentials.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(errors)
        )
    
    # 直接データベースから認証
    from modules.database import authenticate_user, get_usage_limits
    user = authenticate_user(credentials.email, credentials.password, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なメールアドレスまたはパスワードです。"
        )
    
    # 利用制限情報を取得
    limits = get_usage_limits(user["id"], db)
    
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "created_at": user["created_at"],
        "company_name": user["company_name"] or "",
        "usage_limits": {
            "document_uploads_used": limits["document_uploads_used"],
            "document_uploads_limit": limits["document_uploads_limit"],
            "questions_used": limits["questions_used"],
            "questions_limit": limits["questions_limit"],
            "is_unlimited": bool(limits["is_unlimited"])
        }
    }

@app.get("/chatbot/api/auth/user", response_model=UserWithLimits)
async def get_current_user_info(current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """現在のユーザー情報を取得"""
    try:
        # 利用制限情報を取得
        from modules.database import get_usage_limits
        limits = get_usage_limits(current_user["id"], db)
        
        return {
            "id": current_user["id"],
            "email": current_user["email"],
            "name": current_user["name"],
            "role": current_user["role"],
            "created_at": current_user["created_at"],
            "company_name": current_user.get("company_name", ""),
            "usage_limits": {
                "document_uploads_used": limits["document_uploads_used"],
                "document_uploads_limit": limits["document_uploads_limit"],
                "questions_used": limits["questions_used"],
                "questions_limit": limits["questions_limit"],
                "is_unlimited": bool(limits["is_unlimited"])
            }
        }
    except Exception as e:
        logger.error(f"ユーザー情報取得エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"ユーザー情報の取得中にエラーが発生しました: {str(e)}"
        )

@app.post("/chatbot/api/auth/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: SupabaseConnection = Depends(get_db)):
    """新規ユーザー登録"""
    try:
        # 入力値バリデーション
        is_valid, errors = validate_user_input(user_data.email, user_data.password, user_data.name)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="; ".join(errors)
            )
        
        # 管理者権限チェックは不要。デモ版では誰でも登録可能
        return register_new_user(user_data.email, user_data.password, user_data.name, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"登録に失敗しました: {str(e)}"
        )

@app.post("/chatbot/api/admin/register-user", response_model=UserResponse)
async def admin_register_user(user_data: AdminUserCreate, current_user = Depends(get_user_creation_permission), db: SupabaseConnection = Depends(get_db)):
    """管理者による新規ユーザー登録"""
    try:
        # 入力値バリデーション
        from modules.validation import validate_user_input
        
        # AdminUserCreateモデルから名前を取得（存在しない場合はメールアドレスから生成）
        name = getattr(user_data, 'name', user_data.email.split('@')[0])
        
        is_valid, errors = validate_user_input(user_data.email, user_data.password, name)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="; ".join(errors)
            )
        
        # roleとcompany_idの空文字チェックを強化
        if not user_data.role or not user_data.role.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="役割(role)は必須です。"
            )

        # 会社IDの事前チェックを緩和- 後続の処理で作成者のcompany_idを継承する場合があるため
        if user_data.company_id and not user_data.company_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="会社IDが指定されている場合は空文字にはできません。"
            )
        
        # まず、メールアドレスが既に存在するかチェック
        from supabase_adapter import select_data
        existing_user_result = select_data("users", filters={"email": user_data.email})
        
        if existing_user_result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="このメールアドレスは既に登録されています"
            )
        
        # new_company_created変数を初期化
        new_company_created = False
        
        # 権限チェックと作成可能なロールの決定
        is_special_admin = current_user["email"] == "queue@queueu-tech.jp" and current_user.get("is_special_admin", False)
        is_admin = current_user["role"] == "admin"
        is_admin_user = current_user["role"] == "admin_user"
        is_user = current_user["role"] == "user"
        
        if is_special_admin:
            # 特別管理者はadmin_userのみ作成可能
            print("特別管理者の権限でadmin_userアカウント作成")
            role = "admin_user"
        elif is_admin or is_admin_user:
            # admin、admin_userはuserロールのみ作成可能
            print(f"管理者の権限でユーザー作成: admin={is_admin}, admin_user={is_admin_user}")
            role = "user"
        elif is_user:
            # userはemployeeのみ作成可能
            print("userの権限でemployeeアカウント作成")
            role = "employee"
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ユーザー作成権限がありません"
            )
        
        if is_special_admin or is_admin or is_admin_user:
            
            # 会社IDの指定
            company_id = None
            company_name = ""
            
            if hasattr(user_data, "company_name") and user_data.company_name:
                # 会社名が指定されている場合、新しい会社を作成
                from modules.database import create_company
                company_id = create_company(user_data.company_name, db)
                company_name = user_data.company_name
                print(f"特別管理者により新しい会社 '{user_data.company_name}' が作成されました (ID: {company_id})")
                # 新しい会社作成なので作成者の会社IDは継承しない
                new_company_created = True
            elif hasattr(user_data, "company_id") and user_data.company_id:
                # 指定された会社IDが存在するかチェック
                company_result = select_data("companies", filters={"id": user_data.company_id})
                if not company_result.data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="指定された会社IDが存在しません"
                    )
                company_id = user_data.company_id
                company_name = company_result.data[0].get("name", "")
                print(f"管理者により既存の会社ID {company_id} が指定されました")
                new_company_created = False
            else:
                # 会社IDも会社名も指定されていない場合
                if is_special_admin:
                    # 特別管理者の場合は新しい会社IDを自動生成
                    company_id = None  # create_user関数で自動生成される
                    print("特別管理者により新しい会社IDが自動生成されます")
                    new_company_created = True
                else:
                    # 通常の管理者の場合は作成者の会社IDを使用
                    company_id = current_user.get("company_id")
                    if company_id:
                        # 会社名も取得
                        company_result = select_data("companies", filters={"id": company_id})
                        if company_result.data:
                            company_name = company_result.data[0].get("name", "")
                        print(f"作成者の会社ID {company_id} を使用します")
                    new_company_created = False
            
            # 特別管理者が社長ユーザーを作成する場合、会社IDが指定されていなければ新しい独立した会社を作成
            if is_special_admin and company_id is None:
                # 特別管理者が会社ID未指定で社長ユーザー作成 →新しい独立した会社を作成
                creator_id_to_pass = None
                print("特別管理者による社長ユーザー作成: 新しい独立した会社IDを生成します")
            elif is_special_admin and new_company_created:
                # 特別管理者が新しい会社名を指定して会社作成 →新しい独立した会社
                creator_id_to_pass = None
                print("特別管理者による新会社作成: 作成者の会社IDは継承しません")
            else:
                # その他の場合は作成者の会社IDを継承
                creator_id_to_pass = current_user["id"]
            
            # create_user関数を直接呼び出す（管理者が作成するアカウントは作成者のステータスを継承）
            user_id = create_user(
                email=user_data.email,
                password=user_data.password,
                name=name,
                role=role,
                company_id=company_id,
                db=db,
                creator_user_id=creator_id_to_pass  # 新しい会社作成時はNone
            )
            
            return {
                "id": user_id,
                "email": user_data.email,
                "name": name,
                "role": role,
                "company_name": company_name,
                "created_at": datetime.datetime.now().isoformat()
            }
        else:
            # userロールの場合は社員アカウントとして登録
            # 現在のユーザーの会社IDを取得して新しいユーザーに設定
            company_id = current_user.get("company_id")
            
            # 会社IDがない場合はエラー
            if not company_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="会社IDが設定されていません。管理者にお問い合わせください。"
                )
            
            # create_user関数を直接呼び出して会社IDを設定し作成者のステータスを継承
            user_id = create_user(
                email=user_data.email,
                password=user_data.password,
                name=name,
                role=role,  # "employee"
                company_id=company_id,
                db=db,
                creator_user_id=current_user["id"]  # 作成者IDを渡す
            )
        
            return {
                "id": user_id,
                "email": user_data.email,
                "name": name,
                "role": role,
                "company_name": "",
                "created_at": datetime.datetime.now().isoformat()
            }
    except HTTPException as e:
        # HTTPExceptionはそのまま再送
        account_type = "ユーザーアカウント" if (current_user["email"] == "queue@queueu-tech.jp" or current_user["role"] == "admin") else "社員アカウント"
        print(f"{account_type}作成エラー: {e.status_code}: {e.detail}")
        raise
    except Exception as e:
        account_type = "ユーザーアカウント" if (current_user["email"] == "queue@queueu-tech.jp" or current_user["role"] == "admin") else "社員アカウント"
        print(f"{account_type}作成エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{account_type}作成に失敗しました: {str(e)}"
        )

@app.delete("/chatbot/api/admin/delete-user/{user_id}", response_model=dict)
async def admin_delete_user(user_id: str, current_user = Depends(get_user_with_delete_permission), db: SupabaseConnection = Depends(get_db)):
    """管理者によるユーザー削除"""
    # 権限チェック
    is_special_admin = current_user["email"] == "queue@queueu-tech.jp" and current_user.get("is_special_admin", False)
    is_admin = current_user["role"] == "admin"
    is_admin_user = current_user["role"] == "admin_user"
    is_user = current_user["role"] == "user"
    
    # 自分の身は削除できない   
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="自分の身を削除することはできません"
        )
    
    # ユーザーの存在確認
    user_result = select_data("users", filters={"id": user_id})
    
    if not user_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたユーザーが見つかりません"
        )
    
    target_user = user_result.data[0]
    
    # 削除権限のチェック
    if is_special_admin:
        # 特別管理者は全員削除可能
        pass
    elif is_admin:
        # adminロールは全員削除可能
        pass
    elif is_admin_user:
        # admin_userロールは同じ会社のuserとemployeeを削除可能
        if target_user.get("role") not in ["user", "employee"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="userまたはemployeeアカウントのみ削除できます"
            )
        
        # 同じ会社かチェック
        current_company_id = current_user.get("company_id")
        target_company_id = target_user.get("company_id")
        
        if not current_company_id or current_company_id != target_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="同じ会社のユーザーのみ削除できます"
            )
    elif is_user:
        # userロールは同じ会社の社員のみ削除可能
        if target_user.get("role") not in ["employee"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="社員アカウントのみ削除できます"
            )
        
        # 同じ会社かチェック
        current_company_id = current_user.get("company_id")
        target_company_id = target_user.get("company_id")
        
        if not current_company_id or current_company_id != target_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="同じ会社の社員のみ削除できます"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者の権限が必要です"
        )
    
    # ユーザーの削除
    from supabase_adapter import delete_data
    delete_data("usage_limits", "user_id", user_id)
    delete_data("document_sources", "uploaded_by", user_id)
    delete_data("chat_history", "employee_id", user_id)  # チャット履歴も削除
    delete_data("users", "id", user_id)
    
    return {"message": f"ユーザー {target_user['email']} を削除しました", "deleted_user_id": user_id}

# チャット履歴をCSV形式でダウンロードするエンドポイント
@app.get("/chatbot/api/admin/chat-history/csv")
async def download_chat_history_csv(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """チャット履歴をCSV形式でダウンロードする"""
    try:
        print(f"CSVダウンロード開始 - ユーザー: {current_user['email']}")
        
        # 権限チェック（user、employeeロールも許可）
        is_admin = current_user["role"] == "admin"
        is_admin_user = current_user["role"] == "admin_user"
        is_user = current_user["role"] == "user"
        is_employee = current_user["role"] == "employee"
        is_special_admin = current_user["email"] == "queue@queueu-tech.jp"
        
        # チャット履歴を複数の方法で取得を試行
        chat_history = []
        try:
            if is_special_admin:
                print("特別管理者として全ユーザーのチャット履歴を取得")
                # 特別な管理者の場合は全ユーザーのチャットを取得
                try:
                    chat_history = get_chat_history(None, db)
                    print(f"get_chat_history結果: {len(chat_history) if chat_history else 0}件")
                except Exception as e1:
                    print(f"get_chat_history失敗: {e1}")
                    # フォールバック：直接Supabaseから取得
                    from supabase_adapter import select_data
                    result = select_data("chat_history")
                    chat_history = result.data if result and result.data else []
                    print(f"直接取得結果: {len(chat_history)}件")
                    
            elif is_admin or is_user:
                print(f"{current_user['role']}ロールとして会社のチャット履歴を取得")
                # 管理者/ユーザーの場合は自分の会社のチャットを取得
                company_id = current_user.get("company_id")
                print(f"company_id: {company_id}")
                if company_id:
                    try:
                        chat_history = get_chat_history_by_company(company_id, db)
                        print(f"get_chat_history_by_company結果: {len(chat_history) if chat_history else 0}件")
                    except Exception as e2:
                        print(f"get_chat_history_by_company失敗: {e2}")
                        # フォールバック：ページネーション版を試行
                        try:
                            chat_history, total_count = get_chat_history_by_company_paginated(company_id, db, limit=10000, offset=0)
                            print(f"get_chat_history_by_company_paginated結果: {len(chat_history) if chat_history else 0}件")
                        except Exception as e3:
                            print(f"get_chat_history_by_company_paginated失敗: {e3}")
                            # さらなるフォールバック：直接取得
                            from supabase_adapter import select_data
                            company_users_result = select_data("users", filters={"company_id": company_id})
                            if company_users_result and company_users_result.data:
                                user_ids = [user["id"] for user in company_users_result.data]
                                print(f"会社のユーザーID: {user_ids}")
                                # 各ユーザーのチャット履歴を個別に取得
                                all_chats = []
                                for user_id in user_ids:
                                    user_chat_result = select_data("chat_history", filters={"employee_id": user_id})
                                    if user_chat_result and user_chat_result.data:
                                        all_chats.extend(user_chat_result.data)
                                chat_history = all_chats
                                print(f"個別取得結果: {len(chat_history)}件")
                else:
                    print("company_idがないため自分のチャットのみ取得")
                    chat_history = get_chat_history(current_user["id"], db)
                    print(f"個人チャット結果: {len(chat_history) if chat_history else 0}件")
            else:
                print(f"通常ユーザーとして個人のチャット履歴を取得: {current_user['id']}")
                # その他の場合は自分のチャットのみを取得
                chat_history = get_chat_history(current_user["id"], db)
                print(f"個人チャット結果: {len(chat_history) if chat_history else 0}件")
                
        except Exception as e:
            print(f"チャット履歴取得エラー: {e}")
            import traceback
            print(traceback.format_exc())
            chat_history = []
        
        print(f"取得したチャット履歴数: {len(chat_history)}")
        
        # デバッグ：データ内容の確認
        if chat_history and len(chat_history) > 0:
            print(f"最初のデータサンプル: {chat_history[0]}")
            print(f"データの型: {type(chat_history[0])}")
        else:
            print("⚠️ チャット履歴が空です。データベースを直接確認します...")
            # 直接データベースをチェック
            from supabase_adapter import select_data
            direct_check = select_data("chat_history", limit=5)
            if direct_check and direct_check.data:
                print(f"データベースには {len(direct_check.data)} 件のデータが存在します")
                print(f"サンプル: {direct_check.data[0] if direct_check.data else 'なし'}")
            else:
                print("データベースに全くデータが存在しません")
        
        # CSV形式に変換
        csv_data = io.StringIO()
        csv_writer = csv.writer(csv_data)
        
        # ヘッダー行を書き込み
        csv_writer.writerow([
            "ID",
            "日時",
            "ユーザーの質問",
            "ボットの回答",
            "カテゴリ",
            "感情",
            "社員ID",
            "社員名",
            "参考文献",
            "ページ番号"
        ])
        
        # データ行を書き込み
        rows_written = 0
        for i, chat in enumerate(chat_history):
            try:
                # デバッグ：最初の数行の内容を表示
                if i < 3:
                    print(f"処理中のデータ {i+1}: {chat}")
                
                csv_writer.writerow([
                    chat.get("id", ""),
                    chat.get("timestamp", ""),
                    chat.get("user_message", ""),
                    chat.get("bot_response", ""),
                    chat.get("category", ""),
                    chat.get("sentiment", ""),
                    chat.get("employee_id", ""),
                    chat.get("employee_name", ""),
                    chat.get("source_document", ""),
                    chat.get("source_page", "")
                ])
                rows_written += 1
            except Exception as row_error:
                print(f"行 {i+1} の書き込みでエラー: {row_error}")
                print(f"問題のあるデータ: {chat}")
        
        print(f"CSVに書き込まれた行数: {rows_written} (ヘッダー除く)")
        
        # CSV内容を取得
        csv_content = csv_data.getvalue()
        csv_data.close()
        
        # UTF-8 BOM付きでエンコード（Excelでの文字化け防止）
        csv_bytes = '\ufeff' + csv_content
        
        # ファイル名に日時を含める
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_history_{timestamp}.csv"
        
        print(f"CSVファイル生成完了: {filename}")
        
        # StreamingResponseでCSVファイルとして返す
        return StreamingResponse(
            io.BytesIO(csv_bytes.encode('utf-8')),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"CSVダウンロードエラー: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"CSVダウンロード中にエラーが発生しました: {str(e)}")

@app.get("/chatbot/api/admin/users", response_model=List[UserResponse])
async def admin_get_users(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """全ユーザー一覧を取得"""
    # 特別な管理者のみ
    if current_user["email"] != "queue@queueu-tech.jp" or not current_user.get("is_special_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には特別な管理者の権限が必要です"
        )
    return get_all_users(db)

@app.get("/chatbot/api/admin/demo-stats", response_model=DemoUsageStats)
async def admin_get_demo_stats(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """チェック利用状況統計を取得"""
    return get_demo_usage_stats(db)

@app.post("/chatbot/api/submit-url")
async def submit_url(submission: UrlSubmission, current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """URLを送信して知識ベースを更新"""
    try:
        # URLが空でないことを確認
        if not submission.url or not submission.url.strip():
            raise HTTPException(
                status_code=400,
                detail="URLが指定されていないか、ファイル名が無効です"
            )
            
        # URLの基本検証
        if not submission.url.startswith(('http://', 'https://')) and not submission.url.startswith('www.'):
            submission.url = 'https://' + submission.url
            
        # URL処理実施
        company_id = current_user.get("company_id")
        print(f"🔍 [UPLOAD DEBUG] URL処理時のcompany_id: {company_id}")
        print(f"🔍 [UPLOAD DEBUG] current_user: {current_user}")
        result = await process_url(submission.url, current_user["id"], company_id, db)
        return result
    except Exception as e:
        logger.error(f"URL送信エラー: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 'int' object has no attribute 'strip' エラーの特別処理
        if "'int' object has no attribute 'strip'" in str(e):
            raise HTTPException(
                status_code=500,
                detail="チャットのデータ型エラーが発生しました。管理者に連絡してください"
            )
        
        # その他の例外は通常のエラーレスポンスを返す
        raise HTTPException(
            status_code=500,
            detail=f"URLの処理にエラーが発生しました: {str(e)}"
        )

@app.post("/chatbot/api/upload-knowledge")
async def upload_knowledge(
    file: UploadFile = File(..., description="アップロードするファイル（最大100MB）"), 
    current_user = Depends(get_current_user), 
    db: SupabaseConnection = Depends(get_db)
):
    """ファイルをアップロードして知識ベースを更新"""
    try:
        # ファイル名が存在することを確認
        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail="ファイルが指定されていないか、ファイル名が無効です"
            )
        
        # ファイルサイズをチェック（100MB = 100 * 1024 * 1024 bytes）
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"ファイルサイズが制限を超えています。最大100MBまで対応しています。（現在のファイルサイズ: {file_size / (1024*1024):.1f}MB）"
            )
        
        # ファイルポインタを先頭に戻す
        await file.seek(0)
            
        # ファイル拡張子をチェック
        if not file.filename.lower().endswith(('.xlsx', '.xls', '.pdf', '.txt', '.csv', '.doc', '.docx', '.avi', '.mp4', '.webp', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif')):
            raise HTTPException(
                status_code=400,
                detail="無効なファイル形式です。Excel、PDF、Word、CSV、テキスト、画像、動画ファイルのみ対応しています"
            )
            
        # ファイル処理実施
        company_id = current_user.get("company_id")
        print(f"🔍 [UPLOAD DEBUG] ファイルアップロード時のcompany_id: {company_id}")
        print(f"🔍 [UPLOAD DEBUG] current_user: {current_user}")
        result = await process_file(file, request=None, user_id=current_user["id"], company_id=company_id, db=db)
        return result
    except Exception as e:
        logger.error(f"ファイルアップロードエラー: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 'int' object has no attribute 'strip' エラーの特別処理
        if "'int' object has no attribute 'strip'" in str(e):
            raise HTTPException(
                status_code=500,
                detail="チャットのデータ型エラーが発生しました。管理者に連絡してください"
            )
        
        # その他の例外は通常のエラーレスポンスを返す
        raise HTTPException(
            status_code=500,
            detail=f"ファイルのアップロード中にエラーが発生しました: {str(e)}"
        )

@app.post("/chatbot/api/upload-multiple-knowledge")
async def upload_multiple_knowledge(
    files: List[UploadFile] = File(...), 
    current_user = Depends(get_current_user), 
    db: SupabaseConnection = Depends(get_db)
):
    """複数ファイルを順次アップロードして知識ベースを更新（サーバー負荷軽減）"""
    try:
        if not files:
            raise HTTPException(
                status_code=400,
                detail="ファイルが指定されていません"
            )
        
        # 最大ファイル数制限
        max_files = 10
        if len(files) > max_files:
            raise HTTPException(
                status_code=400,
                detail=f"一度にアップロードできるファイル数は{max_files}個までです"
            )
        
        results = []
        processed_count = 0
        
        for i, file in enumerate(files):
            try:
                # ファイル名チェック
                if not file or not file.filename:
                    logger.warning(f"ファイル{i+1}: ファイル名が無効です")
                    results.append({
                        "file_index": i + 1,
                        "filename": "不明",
                        "status": "error",
                        "message": "ファイル名が無効です"
                    })
                    continue
                
                # ファイル拡張子チェック
                if not file.filename.lower().endswith(('.xlsx', '.xls', '.pdf', '.txt', '.csv', '.doc', '.docx', '.avi', '.mp4', '.webp', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif')):
                    logger.warning(f"ファイル{i+1}: 無効なファイル形式: {file.filename}")
                    results.append({
                        "file_index": i + 1,
                        "filename": file.filename,
                        "status": "error",
                        "message": "無効なファイル形式です"
                    })
                    continue
                
                logger.info(f"複数ファイル処理 {i+1}/{len(files)}: {file.filename}")
                
                # ファイル処理前の遅延（サーバー負荷軽減）
                if i > 0:  # 最初のファイル以外は遅延
                    delay_seconds = min(2.0 + (i * 0.5), 10.0)  # 2秒から最大10秒まで
                    logger.info(f"サーバー負荷軽減のため{delay_seconds}秒待機")
                    await asyncio.sleep(delay_seconds)
                
                # ファイル処理実行
                company_id = current_user.get("company_id")
                print(f"🔍 [UPLOAD DEBUG] 複数ファイルアップロード時のcompany_id: {company_id} (ファイル: {file.filename})")
                result = await process_file(file, request=None, user_id=current_user["id"], company_id=company_id, db=db)
                processed_count += 1
                
                results.append({
                    "file_index": i + 1,
                    "filename": file.filename,
                    "status": "success",
                    "message": "正常に処理されました",
                    "details": result
                })
                
                logger.info(f"ファイル処理完了 {i+1}/{len(files)}: {file.filename}")
                
            except Exception as file_error:
                logger.error(f"ファイル処理エラー {i+1}/{len(files)}: {file.filename} - {str(file_error)}")
                results.append({
                    "file_index": i + 1,
                    "filename": file.filename if file and file.filename else "不明",
                    "status": "error",
                    "message": f"処理中にエラーが発生しました: {str(file_error)}"
                })
        
        # 処理結果のサマリー
        success_count = sum(1 for r in results if r["status"] == "success")
        error_count = len(results) - success_count
        
        return {
            "total_files": len(files),
            "success_count": success_count,
            "error_count": error_count,
            "processed_count": processed_count,
            "results": results,
            "message": f"複数ファイル処理完了: {success_count}個成功, {error_count}個失敗"
        }
        
    except Exception as e:
        logger.error(f"複数ファイルアップロードエラー: {str(e)}")
        logger.error(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail=f"複数ファイルのアップロード中にエラーが発生しました: {str(e)}"
        )

# 知識ベース情報を取得するエンドポイント
@app.get("/chatbot/api/knowledge-base")
async def get_knowledge_base(current_user = Depends(get_current_user)):
    """現在の知識ベースの情報を取得"""
    return get_knowledge_base_info()

# チャットエンドポイント
@app.post("/chatbot/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """チャットメッセージを処理してGeminiからの応答を返す（シンプル高速処理）"""
    # デバッグ用：現在のユーザー情報と利用制限を出力
    print(f"=== シンプルチャット処理開始 ===")
    print(f"ユーザー情報: {current_user}")
    
    # 現在の利用制限を取得して表示
    from modules.database import get_usage_limits
    current_limits = get_usage_limits(current_user["id"], db)
    print(f"現在の利用制限: {current_limits}")
    
    # ユーザーIDを設定
    message.user_id = current_user["id"]
    message.employee_name = current_user["name"]
    
    # シンプルで高速なprocess_chat関数を使用
    from modules.chat import process_chat
    result = await process_chat(message, db, current_user)
    
    # 応答を返す
    return ChatResponse(
        response=result["response"],
        source=result.get("source", ""),
        remaining_questions=result.get("remaining_questions", 0),
        limit_reached=result.get("limit_reached", False)
    )

@app.post("/chatbot/api/chat-chunked-info", response_model=dict)
async def chat_chunked_info(message: ChatMessage, current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """チャンク化処理の詳細情報を取得する（デバッグ用）"""
    try:
        # ユーザーIDを設定
        message.user_id = current_user["id"]
        message.employee_name = current_user["name"]
        
        # チャンク化処理を実行
        from modules.chat import process_chat_chunked
        result = await process_chat_chunked(message, db, current_user)
        
        # 詳細情報を返す
        return {
            "response": result["response"],
            "chunks_processed": result.get("chunks_processed", 0),
            "successful_chunks": result.get("successful_chunks", 0),
            "remaining_questions": result.get("remaining_questions", 0),
            "limit_reached": result.get("limit_reached", False),
            "processing_success": True
        }
    except Exception as e:
        logger.error(f"チャンク化処理エラー: {str(e)}")
        return {
            "response": f"エラーが発生しました: {str(e)}",
            "chunks_processed": 0,
            "successful_chunks": 0,
            "remaining_questions": 0,
            "limit_reached": False,
            "processing_success": False,
            "error": str(e)
        }

# チャット履歴を取得するエンドポイント（ページネーション対応）
@app.get("/chatbot/api/admin/chat-history")
async def admin_get_chat_history(
    limit: int = 30,
    offset: int = 0,
    current_user = Depends(get_admin_or_user), 
    db: SupabaseConnection = Depends(get_db)
):
    """チャット履歴を取得する（ページネーション対応）"""
    print(f"🔍 [CHAT HISTORY DEBUG] admin_get_chat_history 開始")
    print(f"🔍 [CHAT HISTORY DEBUG] current_user: {current_user}")
    print(f"🔍 [CHAT HISTORY DEBUG] limit: {limit}, offset: {offset}")
    
    # 権限チェック
    is_special_admin = current_user["email"] == "queue@queueu-tech.jp" and current_user.get("is_special_admin", False)
    is_admin = current_user["role"] == "admin"
    is_user = current_user["role"] == "user"
    is_employee = current_user["role"] == "employee"
    
    print(f"🔍 [CHAT HISTORY DEBUG] 権限チェック:")
    print(f"  - is_special_admin: {is_special_admin}")
    print(f"  - is_admin: {is_admin}")
    print(f"  - is_user: {is_user}")
    print(f"  - is_employee: {is_employee}")
    
    try:
        if is_special_admin:
            print(f"🔍 [CHAT HISTORY DEBUG] 特別管理者として全ユーザーのチャットを取得")
            # 特別な管理者の場合は全ユーザーのチャットを取得
            chat_history, total_count = get_chat_history_paginated(None, db, limit, offset)
        elif is_admin:
            print(f"🔍 [CHAT HISTORY DEBUG] 管理者として会社のチャットを取得")
            # 管理者の場合は自分の会社のチャットを取得
            company_id = current_user.get("company_id")
            print(f"🔍 [CHAT HISTORY DEBUG] company_id: {company_id}")
            if company_id:
                chat_history, total_count = get_chat_history_by_company_paginated(company_id, db, limit, offset)
            else:
                print(f"🔍 [CHAT HISTORY DEBUG] company_idがないため自分のチャットのみ取得")
                chat_history, total_count = get_chat_history_paginated(current_user["id"], db, limit, offset)
        elif is_user:
            print(f"🔍 [CHAT HISTORY DEBUG] ユーザーとして会社のチャットを取得")
            # ユーザーの場合は自分の会社のチャットを取得
            company_id = current_user.get("company_id")
            print(f"🔍 [CHAT HISTORY DEBUG] company_id: {company_id}")
            if company_id:
                chat_history, total_count = get_chat_history_by_company_paginated(company_id, db, limit, offset)
            else:
                print(f"🔍 [CHAT HISTORY DEBUG] company_idがないため自分のチャットのみ取得")
                chat_history, total_count = get_chat_history_paginated(current_user["id"], db, limit, offset)
        else:
            print(f"🔍 [CHAT HISTORY DEBUG] 通常ユーザーとして自分のチャットのみ取得")
            # その他の場合は自分のチャットのみ取得
            chat_history, total_count = get_chat_history_paginated(current_user["id"], db, limit, offset)
            
        print(f"🔍 [CHAT HISTORY DEBUG] 取得結果: {len(chat_history) if chat_history else 0}件 (全体: {total_count}件)")
        
    except Exception as e:
        print(f"🔍 [CHAT HISTORY DEBUG] ページネーション機能でエラーが発生: {e}")
        import traceback
        print(traceback.format_exc())
        
        # フォールバック: 古い方法でデータを取得
        if is_special_admin:
            print(f"🔍 [CHAT HISTORY DEBUG] フォールバック: 特別管理者として全チャット取得")
            chat_history = get_chat_history(None, db)
        elif is_admin or is_user:
            print(f"🔍 [CHAT HISTORY DEBUG] フォールバック: 会社チャット取得")
            company_id = current_user.get("company_id")
            if company_id:
                chat_history = get_chat_history_by_company(company_id, db)
            else:
                chat_history = get_chat_history(current_user["id"], db)
        else:
            print(f"🔍 [CHAT HISTORY DEBUG] フォールバック: 個人チャット取得")
            chat_history = get_chat_history(current_user["id"], db)
        
        # ページネーション風に制限
        total_count = len(chat_history)
        start_idx = offset
        end_idx = min(offset + limit, total_count)
        chat_history = chat_history[start_idx:end_idx]
        
        # has_moreを計算
        has_more = (offset + limit) < total_count
    
    # has_moreを計算（try文内で成功した場合の処理）
    if 'has_more' not in locals():
        has_more = (offset + limit) < total_count
    
    print(f"🔍 [CHAT HISTORY DEBUG] 最終レスポンス: {len(chat_history) if chat_history else 0}件, has_more: {has_more}")
    
    return {
        "data": chat_history,
        "pagination": {
            "total_count": total_count,
            "has_more": has_more,
            "limit": limit,
            "offset": offset
        }
    }

# チャット履歴分析エンドポイント
@app.get("/chatbot/api/admin/analyze-chats")
async def admin_analyze_chats(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """チャット履歴を分析する"""
    print(f"🔍 [ANALYZE CHAT DEBUG] admin_analyze_chats 開始")
    print(f"🔍 [ANALYZE CHAT DEBUG] current_user: {current_user}")
    
    # 権限チェック
    is_special_admin = current_user["email"] == "queue@queueu-tech.jp" and current_user.get("is_special_admin", False)
    is_admin = current_user["role"] == "admin"
    is_user = current_user["role"] == "user"
    
    print(f"🔍 [ANALYZE CHAT DEBUG] 権限チェック:")
    print(f"  - is_special_admin: {is_special_admin}")
    print(f"  - is_admin: {is_admin}")
    print(f"  - is_user: {is_user}")
    
    try:
        if is_special_admin:
            print(f"🔍 [ANALYZE CHAT DEBUG] 特別管理者として全ユーザーのチャットを分析")
            # 特別な管理者の場合は全ユーザーのチャットを分析
            result = await analyze_chats(None, db)
        elif is_admin or is_user:
            print(f"🔍 [ANALYZE CHAT DEBUG] 管理者/ユーザーとして会社のチャットを分析")
            # 管理者/ユーザーの場合は自分の会社のチャットのみを分析
            company_id = current_user.get("company_id")
            print(f"🔍 [ANALYZE CHAT DEBUG] company_id: {company_id}")
            if company_id:
                result = await analyze_chats(None, db, company_id=company_id)
            else:
                print(f"🔍 [ANALYZE CHAT DEBUG] company_idがないため自分のチャットのみ分析")
                result = await analyze_chats(current_user["id"], db)
        else:
            print(f"🔍 [ANALYZE CHAT DEBUG] 通常ユーザーとして自分のチャットのみ分析")
            # その他の場合は自分のチャットのみを分析
            result = await analyze_chats(current_user["id"], db)
        
        print(f"🔍 [ANALYZE CHAT DEBUG] 分析結果: {result}")
        return result
    
    except Exception as e:
        print(f"🔍 [ANALYZE CHAT DEBUG] チャット履歴分析エラー: {e}")
        import traceback
        print(traceback.format_exc())
        # エラーが発生した場合でも空の結果を返す
        return {
            "total_messages": 0,
            "average_response_time": 0,
            "category_distribution": [],
            "sentiment_distribution": [],
            "daily_usage": [],
            "common_questions": []
        }

@app.post("/chatbot/api/admin/detailed-analysis")
async def admin_detailed_analysis(request: dict, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """詳細なビジネス分析を行う"""
    print(f"🔍 [DETAILED ANALYSIS DEBUG] admin_detailed_analysis 開始")
    print(f"🔍 [DETAILED ANALYSIS DEBUG] current_user: {current_user}")
    
    try:
        # ユーザー情報の取得
        is_admin = current_user["role"] == "admin"
        is_user = current_user["role"] == "user"
        is_special_admin = current_user["email"] == "queue@queueu-tech.jp" and current_user.get("is_special_admin", False)
        
        print(f"🔍 [DETAILED ANALYSIS DEBUG] 権限チェック:")
        print(f"  - is_special_admin: {is_special_admin}")
        print(f"  - is_admin: {is_admin}")
        print(f"  - is_user: {is_user}")
        
        # プロンプトを取得
        prompt = request.get("prompt", "")
        print(f"🔍 [DETAILED ANALYSIS DEBUG] prompt: {prompt}")
        
        # 通常の分析結果を取得
        if is_special_admin:
            print(f"🔍 [DETAILED ANALYSIS DEBUG] 特別管理者として全チャットで分析")
            # 特別管理者の全チャットのタイプで分析
            analysis_result = await analyze_chats(None, db)
        else:
            # 一般ユーザーは自分の会社のチャットのみで分析
            user_company_id = current_user.get("company_id")
            print(f"🔍 [DETAILED ANALYSIS DEBUG] user_company_id: {user_company_id}")
            if user_company_id:
                print(f"🔍 [DETAILED ANALYSIS DEBUG] 会社のチャットで分析")
                analysis_result = await analyze_chats(None, db, company_id=user_company_id)
            else:
                print(f"🔍 [DETAILED ANALYSIS DEBUG] 個人のチャットで分析")
                # 会社IDがない場合は自分のチャットのみ
                analysis_result = await analyze_chats(current_user["id"], db)
        
        # より詳細なチャットデータを取得
        try:
            if is_special_admin:
                print(f"🔍 [DETAILED ANALYSIS DEBUG] 特別管理者として全チャットデータ取得")
                # 特別管理者の全チャットを取得
                chat_result = select_data("chat_history", limit=1000, order="created_at desc")
            else:
                # 一般ユーザーは自分の会社のチャットのみ取得
                user_company_id = current_user.get("company_id")
                if user_company_id:
                    print(f"🔍 [DETAILED ANALYSIS DEBUG] 会社のチャットデータ取得 (company_id: {user_company_id})")
                    # 会社のユーザーIDを取得
                    users_result = select_data("users", columns="id", filters={"company_id": user_company_id})
                    if users_result and users_result.data:
                        user_ids = [user["id"] for user in users_result.data]
                        user_ids_str = ','.join([f"'{uid}'" for uid in user_ids])
                        chat_result = select_data("chat_history", filters={"employee_id": f"in.({user_ids_str})"}, limit=1000, order="created_at desc")
                    else:
                        print(f"🔍 [DETAILED ANALYSIS DEBUG] 会社のユーザーが見つからないため空のデータで処理")
                        chat_result = None
                else:
                    print(f"🔍 [DETAILED ANALYSIS DEBUG] 個人のチャットデータ取得")
                    # 会社IDがない場合は自分のチャットのみ
                    chat_result = select_data("chat_history", filters={"employee_id": current_user["id"]}, limit=1000, order="created_at desc")
            
            chat_data = chat_result.data if chat_result and chat_result.data else []
            print(f"🔍 [DETAILED ANALYSIS DEBUG] 取得したチャットデータ数: {len(chat_data)}")
            
            # 詳細なチャットのタイプ
            detailed_metrics = {
                "total_conversations": len(chat_data),
                "average_message_length": 0,
                "response_satisfaction_rate": 0,
                "repeat_question_rate": 0,
                "resolution_rate": 0,
                "peak_usage_hours": [],
                "common_failure_patterns": [],
                "user_journey_analysis": {},
                "topic_complexity_analysis": {},
                "temporal_trends": {}
            }
            
            if chat_data:
                # メッシュージ長
                message_lengths = [len(msg.get("message", "")) for msg in chat_data if msg.get("message")]
                detailed_metrics["average_message_length"] = sum(message_lengths) / len(message_lengths) if message_lengths else 0
                
                # 時間帯別の刁ー
                hour_counts = {}
                for msg in chat_data:
                    if msg.get("created_at"):
                        try:
                            dt = datetime.datetime.fromisoformat(msg["created_at"].replace('Z', '+00:00'))
                            hour = dt.hour
                            hour_counts[hour] = hour_counts.get(hour, 0) + 1
                        except:
                            continue
                
                # ピク時間帯を特定                if hour_counts:
                    sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
                    detailed_metrics["peak_usage_hours"] = sorted_hours[:3]
                
                # 繰り返し質問刁ー
                message_texts = [msg.get("message", "").lower() for msg in chat_data if msg.get("message")]
                unique_messages = set(message_texts)
                if message_texts:
                    detailed_metrics["repeat_question_rate"] = (len(message_texts) - len(unique_messages)) / len(message_texts) * 100
                
                # よくある失敗パターンの特定                failure_keywords = ["エラー", "わからなぁE, "できなぁE, "失敁E, "問顁E, "困っぁE, "ぁーくいかなぁE, "動かなぁE]
                failure_count = 0
                for msg in message_texts:
                    if any(keyword in msg for keyword in failure_keywords):
                        failure_count += 1
                
                if message_texts:
                    detailed_metrics["resolution_rate"] = max(0, (len(message_texts) - failure_count) / len(message_texts) * 100)
            
        except Exception as e:
            print(f"詳細メトリクス取得エラー: {e}")
            detailed_metrics = {"error": "詳細メトリクスの取得に失敗しました"}
        
        # カチェックリーとセンチメント刁のら洞察を成
        categories = analysis_result.get("category_distribution", {})
        sentiments = analysis_result.get("sentiment_distribution", {})
        questions = analysis_result.get("common_questions", [])
        daily_usage = analysis_result.get("daily_usage", [])
        
        # Gemini APIで詳細な分析を実施
        from modules.admin import model
        
        # Geminiモデルが初期化されていない場合エラーハンドリング
        if model is None:
            raise HTTPException(status_code=500, detail="Geminiモデルが初期化されていない")
        
        # 短縮されたビジネス特化プロンプト
        repeat_rate = detailed_metrics.get('repeat_question_rate', 0)
        repeat_rate_str = f"{repeat_rate:.1f}%"
        
        total_conversations = detailed_metrics.get('total_conversations', 0)
        peak_hours = detailed_metrics.get('peak_usage_hours', [])
        categories_json = json.dumps(categories, ensure_ascii=False)
        sentiments_json = json.dumps(sentiments, ensure_ascii=False)
        questions_json = json.dumps(questions[:5], ensure_ascii=False)
        
        data_summary = "# データの概要\n"
        data_summary += f"総会話数: {total_conversations}件\n"
        data_summary += f"繰り返し質問率: {repeat_rate_str}\n"
        data_summary += f"ピーク利用時間: {peak_hours}\n\n"
        data_summary += f"カテゴリー別データ: {categories_json}\n"
        data_summary += f"感情データ: {sentiments_json}\n"
        data_summary += f"頻出質問: {questions_json}"
        
        analysis_instructions = "\n# Please analyze the following 6 items in detail:\n"
        analysis_instructions += "Item 1: Frequent Topic Analysis - Identify the most common question patterns and business issues from chat history, and show standardization opportunities.\n"
        analysis_instructions += "Item 2: Efficiency Opportunities - Identify automatable tasks from repetitive questions and propose high-ROI improvement measures.\n"
        analysis_instructions += "Item 3: Frustration Factors - Analyze the causes of negative emotions and unresolved problem patterns, and show priority improvement items.\n"
        analysis_instructions += "Item 4: System Improvement Proposals - Propose specific feature additions/improvements and prioritize user needs.\n"
        analysis_instructions += "Item 5: Information Sharing Issues - Identify departmental information gaps and areas lacking documentation.\n"
        analysis_instructions += "Item 6: Implementation Plan - Present short-term (1-3 months), medium-term (3-6 months), and long-term (6 months-1 year) improvement plans with investment effects."
        
        analysis_prompt = f"{prompt}\n\n{data_summary}\n{analysis_instructions}"
        
        # Gemini APIによる詳細分析
        analysis_response = model.generate_content(analysis_prompt)
        detailed_analysis_text = analysis_response.text
        
        print(f"Gemini分析結果: {detailed_analysis_text[:500]}...")  # チェック用
        
        # 詳細分析の結果をセクションごとに分析して整形
        import re
        
        # セクション分析
        detailed_analysis = {
            "detailed_topic_analysis": "",
            "efficiency_opportunities": "",
            "frustration_points": "",
            "improvement_suggestions": "",
            "communication_gaps": "",
            "specific_recommendations": ""
        }
        
        # より精密なセクション分析パターン
        sections = [
            (r"1\..*?頻出トピック.*?：", "detailed_topic_analysis"),
            (r"2\..*?効率化機会.*?：", "efficiency_opportunities"),
            (r"3\..*?フラストレーション.*?：", "frustration_points"),
            (r"4\..*?システム改善.*?：", "improvement_suggestions"),
            (r"5\..*?情報共有課題.*?：", "communication_gaps"),
            (r"6\..*?実行計画.*?：", "specific_recommendations")
        ]
        
        # セクション分析処理改善
        current_section = None
        section_content = []
        
        for line in text_lines:
            line = line.strip()
            if not line:
                if current_section:
                    section_content.append("")
                continue
                
            matched_section = None
            for pattern, section_key in sections:
                if re.search(pattern, line, re.IGNORECASE):
                    matched_section = section_key
                    break
            
            if matched_section:
                # 前のセクションの内容を保持
                if current_section and section_content:
                    content = "\n".join(section_content).strip()
                    if content:
                        detailed_analysis[current_section] = content
                
                # 新しいセクションを開始
                current_section = matched_section
                section_content = []
            elif current_section:
                # 現在のセクションに内容を追加
                section_content.append(line)
        
        # 最後のセクションを処理
        if current_section and section_content:
            content = "\n".join(section_content).strip()
            if content:
                detailed_analysis[current_section] = content
        
        # セクション刁ーに失敗した場合対処
        filled_sections = sum(1 for value in detailed_analysis.values() if value.strip())
        if filled_sections < 3:
            # セクション刁ーに失敗した場合、チェックストを刁ーして配列E            text_parts = detailed_analysis_text.split("\n\n")
            section_keys = list(detailed_analysis.keys())
            
            for i, part in enumerate(text_parts[:len(section_keys)]):
                if part.strip():
                    detailed_analysis[section_keys[i]] = part.strip()
            
            print("セクション刁ーに失敗したため、テキストを刁ーに刁のしました")
        
        # チェックチェック情報
        print(f"刁ー結果セクション:")
        for key, value in detailed_analysis.items():
            char_count = len(value.strip()) if value else 0
            print(f"  {key}: {char_count} 刁ー")
        
        return {
            "detailed_analysis": detailed_analysis,
            "analysis_metadata": {
                "total_conversations": detailed_metrics.get("total_conversations", 0),
                "analysis_timestamp": datetime.datetime.now().isoformat(),
                "data_quality_score": min(100, (filled_sections / 6) * 100)
            }
        }
        
    except Exception as e:
        import traceback
        print(f"詳細ビジネス情報エラー: {str(e)}")
        print(traceback.format_exc())
        
        # エラーの場合でも有用な刁ー結果を返す
        return {
            "detailed_analysis": {
                "detailed_topic_analysis": f"刁ー処理にエラーが発生しました: {str(e)}\n\n利用可能な基本チャットのタイプから推測される主要な質問パターンを確認し、手動での詳細刁ーを検討してください",
                "efficiency_opportunities": "シスチェックエラーにより自動解析が完了できませんでした。チャット履歴を手動で確認し、繰り返し質問や標準化可能な業務を特定することをお勧めします",
                "frustration_points": "エラーにより詳細な感情刁ーができませんでした。ユーザーからの否定的なフィードバックを個別に確認してください",
                "improvement_suggestions": "自動解析が利用できませんが、基本優先して以下を検討してください",
                "communication_gaps": "シスチェック制限により刁ーできませんでした。部間での情報共有状況を手動で確認し、ドキュメント化が不足している領域を特定してください",
                "specific_recommendations": "技術的な問題により詳細な提案ができませんが、以下の基本優先してください\n1. シスチェック。安定性向上\n2. エラー処理の改善\n3. 機能の再設計"
            },
            "analysis_metadata": {
                "error": str(e),
                "analysis_timestamp": datetime.datetime.now().isoformat(),
                "data_quality_score": 0
            }
        }

# 強化分析エンドポイント
@app.get("/chatbot/api/admin/enhanced-analysis")
async def admin_enhanced_analysis(
    include_ai_insights: bool = False,  # Gemini分析をオプション化
    current_user = Depends(get_admin_or_user), 
    db: SupabaseConnection = Depends(get_db)
):
    """強化されたチャット分析データを取得する（AI洞察はオプション）"""
    try:
        print(f"🔍 [ENHANCED ANALYSIS] 強化分析開始 (AI分析: {include_ai_insights})")
        
        # 特別管理者のみがデータにアクセス可能
        is_special_admin = current_user["email"] == "queue@queueu-tech.jp" and current_user.get("is_special_admin", False)
        
        company_id = None
        if not is_special_admin:
            company_id = current_user.get("company_id")
            print(f"🔍 [ENHANCED ANALYSIS] company_id: {company_id}")
        
        # データベース分析データを取得（高速）
        from modules.analytics import get_enhanced_analytics
        
        print(f"🔍 [ENHANCED ANALYSIS] データベース分析開始")
        analytics_data = get_enhanced_analytics(db, company_id)
        print(f"🔍 [ENHANCED ANALYSIS] データベース分析完了")
        
        # Gemini分析はオプション
        if include_ai_insights:
            print(f"🔍 [ENHANCED ANALYSIS] Gemini洞察生成開始")
            from modules.analytics import generate_gemini_insights
            ai_insights = await generate_gemini_insights(analytics_data, db, company_id)
            analytics_data["ai_insights"] = ai_insights
            print(f"🔍 [ENHANCED ANALYSIS] Gemini洞察生成完了")
        else:
            # AI分析なしの場合はプレースホルダーを設定
            analytics_data["ai_insights"] = ""
            print(f"🔍 [ENHANCED ANALYSIS] AI分析をスキップ")
        
        print(f"🔍 [ENHANCED ANALYSIS] 分析完了")
        return analytics_data
        
    except Exception as e:
        import traceback
        print(f"強化分析エラー: {str(e)}")
        print(traceback.format_exc())
        
        # エラーの場合でも基本的な情報を返す
        return {
            "resource_reference_count": {
                "resources": [],
                "total_references": 0,
                "summary": f"分析エラー: {str(e)}"
            },
            "category_distribution_analysis": {
                "categories": [],
                "distribution": {},
                "bias_analysis": {},
                "summary": f"分析エラー: {str(e)}"
            },
            "active_user_trends": {
                "daily_trends": [],
                "weekly_trends": [],
                "summary": f"分析エラー: {str(e)}"
            },
            "unresolved_and_repeat_analysis": {
                "repeat_questions": [],
                "unresolved_patterns": [],
                "summary": f"分析エラー: {str(e)}"
            },
            "sentiment_analysis": {
                "sentiment_distribution": {},
                "sentiment_by_category": {},
                "temporal_sentiment": [],
                "summary": f"分析エラー: {str(e)}"
            },
            "ai_insights": f"AI分析中にエラーが発生しました: {str(e)}",
            "analysis_metadata": {
                "generated_at": datetime.datetime.now().isoformat(),
                "analysis_type": "enhanced_error",
                "error": str(e)
            }
        }

# AI洞察専用エンドポイントを追加
@app.get("/chatbot/api/admin/ai-insights")
async def admin_get_ai_insights(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """AI洞察のみを取得する（Gemini分析専用）"""
    try:
        print(f"🤖 [AI INSIGHTS] AI洞察生成開始")
        
        # 特別管理者のみがデータにアクセス可能
        is_special_admin = current_user["email"] == "queue@queueu-tech.jp" and current_user.get("is_special_admin", False)
        
        company_id = None
        if not is_special_admin:
            company_id = current_user.get("company_id")
        
        # データベース分析データを取得
        from modules.analytics import get_enhanced_analytics, generate_gemini_insights
        analytics_data = get_enhanced_analytics(db, company_id)
        
        # Gemini洞察生成
        ai_insights = await generate_gemini_insights(analytics_data, db, company_id)
        
        print(f"🤖 [AI INSIGHTS] AI洞察生成完了")
        return {
            "ai_insights": ai_insights,
            "generated_at": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        import traceback
        print(f"AI洞察生成エラー: {str(e)}")
        print(traceback.format_exc())
        return {
            "ai_insights": f"AI分析中にエラーが発生しました: {str(e)}",
            "generated_at": datetime.datetime.now().isoformat(),
            "error": str(e)
        }

# 社員詳細情報を取得するエンドポイント
@app.get("/chatbot/api/admin/employee-details/{employee_id}", response_model=List[ChatHistoryItem])
async def admin_get_employee_details(employee_id: str, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """特定の社員の詳細なチャット履歴を取得する"""
    # 特別な管理者のueue@queuefood.co.jpの場合は全ユーザーのチャットを取得できるようにする
    is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"] and current_user.get("is_special_admin", False)
    
    # ユーザーIDを渡して権限チェックを行う
    return await get_employee_details(employee_id, db, current_user["id"])

# 会社の全社員情報を取得するエンドポイント
@app.get("/chatbot/api/admin/company-employees", response_model=List[dict])
async def admin_get_company_employees(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """会社の全社員情報を取得する"""
    # 特別管理者のみがデータにアクセス可能
    is_special_admin = current_user["email"] == "queue@queueu-tech.jp"
    
    if is_special_admin:
        # 特別管理者の場合は全ユーザーのチャットを取得
        result = await get_company_employees(current_user["id"], db, None)
        return result
    else:
        # 通常のユーザーの場合は自分の会社の社員のチャットのみを取得
        # ユーザーの会社IDを取得
        user_result = select_data("users", filters={"id": current_user["id"]})
        user_row = user_result.data[0] if user_result.data else None
        company_id = user_row.get("company_id") if user_row else None
        
        if not company_id:
            raise HTTPException(status_code=400, detail="会社IDが見つかりません")
        
        result = await get_company_employees(current_user["id"], db, company_id)
        return result

# 社員利用状況を取得するエンドポイント
@app.get("/chatbot/api/admin/employee-usage", response_model=EmployeeUsageResult)
async def admin_get_employee_usage(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """社員ごとの利用状況を取得する"""
    # 特別管理者のみがチのタにアクセス可能
    is_special_admin = current_user["email"] == "queue@queueu-tech.jp" and current_user.get("is_special_admin", False)
    
    if is_special_admin:
        # 特別管理者の場合は全ユーザーのチャットを取得
        return await get_employee_usage(None, db, is_special_admin=True)
    else:
        # 通常のユーザーの場合は自分の会社の社員のチャットのみを取得
        user_id = current_user["id"]
        return await get_employee_usage(user_id, db, is_special_admin=False)

# アップロードされたリソースを取得するエンドポイント
@app.get("/chatbot/api/admin/resources", response_model=ResourcesResult)
async def admin_get_resources(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """アップロードされたリソース（URL、PDF、Excel、TXT等）を取得する"""
    # 特別管理者のみがデータにアクセス可能
    is_special_admin = current_user["email"] == "queue@queueu-tech.jp" and current_user.get("is_special_admin", False)
    
    if is_special_admin:
        # 特別管理者は全てのリソースを表示
        return await get_uploaded_resources_by_company_id(None, db, uploaded_by=None)
    else:
        # 通常のユーザーは自分の会社のリソースのみ表示
        company_id = current_user.get("company_id")
        if not company_id:
            raise HTTPException(status_code=400, detail="会社IDが見つかりません")
        
        print(f"会社ID {company_id} のリソースを取得します")
        return await get_uploaded_resources_by_company_id(company_id, db)

# リソースのアクティブ状態を切り替えるエンドポイント
@app.post("/chatbot/api/admin/resources/{resource_id:path}/toggle", response_model=ResourceToggleResponse)
async def admin_toggle_resource(resource_id: str, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """リソースのアクティブ状態を切り替える"""
    # URLデコード
    import urllib.parse
    decoded_id = urllib.parse.unquote(resource_id)
    print(f"トグルリクエスト: {resource_id} -> デコード後: {decoded_id}")
    return await toggle_resource_active_by_id(decoded_id, db)

# リソースを削除するエンドポイント
@app.delete("/chatbot/api/admin/resources/{resource_id:path}", response_model=dict)
async def admin_delete_resource(resource_id: str, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """リソースを削除する"""
    # URLデコード
    import urllib.parse
    decoded_id = urllib.parse.unquote(resource_id)
    print(f"削除リクエスト: {resource_id} -> デコード後: {decoded_id}")
    return await remove_resource_by_id(decoded_id, db)

# リソースの特別な更新エンドポイント
@app.put("/chatbot/api/admin/resources/{resource_id:path}/special", response_model=dict)
async def admin_update_resource_special(resource_id: str, request: dict, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """リソースの特別な情報を更新する"""
    try:
        # URLデコード
        import urllib.parse
        decoded_id = urllib.parse.unquote(resource_id)
        print(f"特別更新リクエスト: {resource_id} -> デコード後: {decoded_id}")
        print(f"更新データ: {request}")
        
        # リソースの存在確認
        from supabase_adapter import select_data, update_data
        resource_result = select_data("document_sources", filters={"id": decoded_id})
        
        if not resource_result or not resource_result.data:
            raise HTTPException(status_code=404, detail="リソースが見つかりません")
        
        # 更新可能なフィールドを制限
        update_fields = {}
        if "name" in request:
            update_fields["name"] = request["name"]
        if "description" in request:
            update_fields["description"] = request["description"]
        if "special_instructions" in request:
            update_fields["special_instructions"] = request["special_instructions"]
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="更新可能なフィールドが指定されていません")
        
        # リソースを更新
        update_result = update_data("document_sources", update_fields, "id", decoded_id)
        
        if update_result:
            return {
                "success": True, 
                "message": "リソースが正常に更新されました",
                "resource_id": decoded_id,
                "updated_fields": list(update_fields.keys())
            }
        else:
            raise HTTPException(status_code=500, detail="リソースの更新に失敗しました")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"リソース特別更新エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"リソース更新中にエラーが発生しました: {str(e)}")

@app.post("/chatbot/api/admin/update-user-status/{user_id}", response_model=dict)
async def admin_update_user_status(user_id: str, request: dict, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """管理者の操作によるユーザーステータス変更。Adminのみ実行可能"""
    # adminロール、admin_userロール、または特別な管理者のみが実行可能
    is_admin = current_user["role"] == "admin"
    is_admin_user = current_user["role"] == "admin_user"
    is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"] and current_user.get("is_special_admin", False)
    
    print(f"=== ユーザーステータス変更権限チェック ===")
    print(f"操作者 {current_user['email']} (管理者: {is_admin}, admin_user: {is_admin_user}, 特別管理者: {is_special_admin})")
    
    # 権限チェック - admin、admin_user、または特別管理者のみ
    if not (is_admin or is_admin_user or is_special_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者の権限が必要です。一般ユーザーは自分のプラン変更を行うことはできません"
        )
    
    try:
        print(f"=== ユーザーステータス変更開始 ===")
        print(f"対象ユーザーID: {user_id}")
        
        new_is_unlimited = bool(request.get("is_unlimited", False))
        print(f"新しいステータス: {'本番' if new_is_unlimited else 'チェック'}")
        
        # ユーザーの存在確認
        user_result = select_data("users", filters={"id": user_id})
        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたユーザーが見つかりません"
            )
        
        user = user_result.data[0]
        print(f"対象ユーザー: {user['email']} ({user['name']}) - ロール: {user['role']}")
        
        # 管理者のロールの場合は警告
        if user['role'] == 'admin':
            print(f"警告: 管理者のロール ({user['email']}) のステータス変更")
        
        # 現在の利用制限を取得
        current_limits_result = select_data("usage_limits", filters={"user_id": user_id})
        if not current_limits_result or not current_limits_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーの利用制限情報が見つかりません"
            )
        
        current_limits = current_limits_result.data[0]
        was_unlimited = bool(current_limits.get("is_unlimited", False))
        current_questions_used = current_limits.get("questions_used", 0)
        current_uploads_used = current_limits.get("document_uploads_used", 0)
        
        print(f"現在のステータス: {'本番' if was_unlimited else 'チェック'}")
        print(f"現在の使用状況: 質問数{current_questions_used}, アップロード数{current_uploads_used}")
        
        # ステータスに変更がない場合は何もしない
        if was_unlimited == new_is_unlimited:
            print("ステータスに変更がないため処理をスキップ")
            return {
                "message": f"ユーザー {user['email']} のステータスは既に{'本番' if new_is_unlimited else 'チェック'}です",
                "user_id": user_id,
                "updated_children": 0,
                "updated_company_users": 0
            }
        
        # 新しい制限値を計算
        if new_is_unlimited:
            new_questions_limit = 999999
            new_uploads_limit = 999999
        else:
            new_questions_limit = 10
            new_uploads_limit = 2
            
            # チェック版に変更する場合、使用済み数が新しい制限を超える場合は調整
            if current_questions_used > new_questions_limit:
                print(f"質問使用数{current_questions_used} から {new_questions_limit} に調整")
                current_questions_used = new_questions_limit
            if current_uploads_used > new_uploads_limit:
                print(f"アップロード使用数{current_uploads_used} から {new_uploads_limit} に調整")
                current_uploads_used = new_uploads_limit
        
        print(f"新しい制限: 質問数{new_questions_limit} (使用済み: {current_questions_used}), アップロード数{new_uploads_limit} (使用済み: {current_uploads_used})")
        
        # 利用制限を更新
        update_result = update_data("usage_limits", {
            "is_unlimited": new_is_unlimited,
            "questions_limit": new_questions_limit,
            "questions_used": current_questions_used,
            "document_uploads_limit": new_uploads_limit,
            "document_uploads_used": current_uploads_used
        }, "user_id", user_id)
        
        if update_result:
            print("本人のステータス更新完了")
        else:
            print("本人のステータス更新失敗")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="利用制限の更新に失敗しました"
            )
        
        # プラン履歴を記録
        print("プラン履歴を記録します..")
        from modules.database import record_plan_change
        from_plan = "unlimited" if was_unlimited else "demo"
        to_plan = "unlimited" if new_is_unlimited else "demo"
        record_plan_change(user_id, from_plan, to_plan, db)
        
        # 作成したアカウントも同期
        print("子アカウントの同期を開始します..")
        from modules.database import update_created_accounts_status
        updated_children = update_created_accounts_status(user_id, new_is_unlimited, db)
        
        # 同じ会社の全ユーザーも同じステータスに変更
        print("同じ会社のユーザーの同期を開始します..")
        from modules.database import update_company_users_status
        updated_company_users = update_company_users_status(user_id, new_is_unlimited, db)
        
        result_message = f"ユーザー {user['email']} のステータスを{'本番' if new_is_unlimited else 'チェック'}に変更しました"
        if updated_children > 0 or updated_company_users > 0:
            result_message += f"。子アカウント{updated_children} 個、同じ会社のユーザー {updated_company_users} 個も同期しました。"
        
        print(f"=== ユーザーステータス変更完了===")
        print(f"結果: {result_message}")
        
        return {
            "message": result_message,
            "user_id": user_id,
            "updated_children": updated_children,
            "updated_company_users": updated_company_users,
            "details": {
                "user_email": user['email'],
                "user_name": user['name'],
                "old_status": "本番" if was_unlimited else "チェック",
                "new_status": "本番" if new_is_unlimited else "チェック",
                "new_questions_limit": new_questions_limit,
                "new_uploads_limit": new_uploads_limit
            }
        }
        
    except HTTPException as e:
        print(f"HTTPエラー: {e.detail}")
        raise
    except Exception as e:
        print(f"ユーザーステータス変更エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ステータス変更中にエラーが発生しました: {str(e)}"
        )

# YouTube接続テスト用エンドポイント
@app.get("/chatbot/api/test-youtube")
async def test_youtube_connection():
    """YouTube接続をチェックする"""
    try:
        from modules.utils import test_youtube_connection
        success, message = test_youtube_connection()
        return {
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"チェックト実行エラー: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/chatbot/api/admin/companies", response_model=List[dict])
async def admin_get_companies(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """会社一覧を取得(Adminのみ)"""
    # 特別な管理者のみがアクセス可能
    if current_user["email"] not in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"] or not current_user.get("is_special_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には特別な管理者の権限が必要です"
        )
    
    from modules.database import get_all_companies
    companies = get_all_companies(db)
    return companies

@app.post("/chatbot/api/admin/fix-company-status/{company_id}", response_model=dict)
async def admin_fix_company_status(company_id: str, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """会社内のユーザーステータス不整合を修正する"""
    # adminロール、admin_userロール、または特別な管理者のみが実行可能
    is_admin = current_user["role"] == "admin"
    is_admin_user = current_user["role"] == "admin_user"
    is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"] and current_user.get("is_special_admin", False)
    
    if not (is_admin or is_admin_user or is_special_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者の権限が必要です"
        )
    
    try:
        from modules.database import fix_company_status_inconsistency
        fixed_count = fix_company_status_inconsistency(company_id, db)
        
        return {
            "message": f"会社ID {company_id} のステータス不整合修正が完了しました",
            "fixed_count": fixed_count,
            "company_id": company_id
        }
        
    except Exception as e:
        print(f"会社ステータス修正エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ステータス修正中にエラーが発生しました: {str(e)}"
        )

@app.post("/chatbot/api/admin/ensure-database-integrity", response_model=dict)
async def admin_ensure_database_integrity(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """データベース整合性をチェックして修正する"""
    # adminロール、admin_userロール、または特別な管理者のみが実行可能
    is_admin = current_user["role"] == "admin"
    is_admin_user = current_user["role"] == "admin_user"
    is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"] and current_user.get("is_special_admin", False)
    
    if not (is_admin or is_admin_user or is_special_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者の権限が必要です"
        )
    
    try:
        from modules.database import ensure_usage_limits_integrity
        fixed_count = ensure_usage_limits_integrity(db)
        
        return {
            "message": f"チのタベース整合性チェックが完了しました",
            "fixed_count": fixed_count,
            "details": f"{fixed_count}個のusage_limitsレコードを作成しました" if fixed_count > 0 else "修正が必要なレコードはありませんでした"
        }
        
    except Exception as e:
        print(f"チのタベース整合性チェックエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"チのタベース整合性チェック中にエラーが発生しました: {str(e)}"
        )




# 申請管理者ポイント（管理者の申請一覧を取得する）
@app.get("/chatbot/api/admin/applications")
async def admin_get_applications(status: str = None, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """管理者の申請一覧を取得する"""
    try:
        print(f"申請一覧取得要請- ユーザー: {current_user['email']} (ロール: {current_user['role']})")
        
        # 管理者の権限チェック
        is_admin = current_user["role"] == "admin"
        is_admin_user = current_user["role"] == "admin_user"
        is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"] and current_user.get("is_special_admin", False)
        
        if not (is_admin or is_admin_user or is_special_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この操作には管理者の権限が必要です"
            )
        
        from modules.database import get_applications
        applications = get_applications(status=status, db=db)
        
        return {
            "success": True,
            "applications": applications,
            "count": len(applications)
        }
        
    except Exception as e:
        print(f"申請一覧取得エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"申請一覧の取得に失敗しました: {str(e)}"
        )

@app.post("/chatbot/api/admin/applications/{application_id}/status")
async def admin_update_application_status(
    application_id: str, 
    request: dict, 
    current_user = Depends(get_admin_or_user), 
    db: SupabaseConnection = Depends(get_db)
):
    """管理者の申請ステータスを更新する"""
    try:
        print(f"申請ステータス更新要請- ユーザー: {current_user['email']}")
        print(f"申請ID: {application_id}")
        print(f"リクエスト {request}")
        
        # 管理者の権限チェック
        is_admin = current_user["role"] == "admin"
        is_admin_user = current_user["role"] == "admin_user"
        is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"] and current_user.get("is_special_admin", False)
        
        if not (is_admin or is_admin_user or is_special_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この操作には管理者の権限が必要です"
            )
        
        new_status = request.get("status")
        notes = request.get("notes", "")
        
        if not new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ステータスが指定されていせん"
            )
        
        from modules.database import update_application_status
        result = update_application_status(
            application_id=application_id,
            status=new_status,
            processed_by=current_user["email"],
            notes=notes,
            db=db
        )
        
        if result:
            return {
                "success": True,
                "message": f"申請ステータスめE{new_status}'に更新しました"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="申請ステータスの更新に失敗しました"
            )
        
    except Exception as e:
        print(f"申請ステータス更新エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"申請ステータスの更新に失敗しました: {str(e)}"
        )

# 会社全体のトークン使用量と料金情報を取得するエンドポイント
@app.get("/chatbot/api/company-token-usage", response_model=dict)
async def get_company_token_usage(current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """会社全体のトークン使用量と料金情報を取得する"""
    try:
        print(f"company-token-usageエンド�Eイントが呼び出されました - ユーザー: {current_user['email']}")
        
        # ユーザーの会社IDを取得
        from supabase_adapter import select_data
        user_result = select_data("users", columns="company_id", filters={"id": current_user["id"]})
        company_id = None
        if user_result and user_result.data:
            company_id = user_result.data[0].get("company_id")
        
        # 実際の会社ユーザー数を取得
        company_users_count = 1  # デフォルト
        company_name = "あなたの会社"
        
        if company_id:
            # 同じ会社のユーザー数をカウント
            company_users_result = select_data("users", columns="id, name", filters={"company_id": company_id})
            if company_users_result and company_users_result.data:
                company_users_count = len(company_users_result.data)
                print(f"会社ID {company_id} のユーザー数: {company_users_count}人")
            
            # 会社名を取得
            company_result = select_data("companies", columns="name", filters={"id": company_id})
            if company_result and company_result.data:
                company_name = company_result.data[0].get("name", "あなたの会社")
        
        # 実際のトークン使用量を取得
        total_tokens_used = 0
        total_input_tokens = 0
        total_output_tokens = 0
        total_conversations = 0
        total_cost_usd = 0.0
        
        try:
            if company_id:
                # TokenUsageTrackerを使用して実際の使用量を取得                from modules.token_counter import TokenUsageTracker
                import datetime
                
                tracker = TokenUsageTracker(db)
                
                # 現在の月を取得
                current_month = datetime.datetime.now().strftime('%Y-%m')
                print(f"🔍 現在の月: {current_month}")
                
                usage_data = tracker.get_company_monthly_usage(company_id, current_month)
                
                if usage_data and usage_data.get("total_tokens", 0) > 0:
                    total_tokens_used = usage_data.get("total_tokens", 0)
                    total_input_tokens = usage_data.get("total_input_tokens", 0) 
                    total_output_tokens = usage_data.get("total_output_tokens", 0)
                    total_conversations = usage_data.get("conversation_count", 0)
                    total_cost_usd = usage_data.get("total_cost_usd", 0.0)
                    print(f"会社ID {company_id} の実際のトークン使用量 {total_tokens_used:,} tokens")
                else:
                    print("⚠️ 今月のトークン使用量データがない - 全期間で確認します")
                    # 全期間のチャットを取得
                    usage_data_all = tracker.get_company_monthly_usage(company_id, "ALL")
                    if usage_data_all and usage_data_all.get("total_tokens", 0) > 0:
                        total_tokens_used = usage_data_all.get("total_tokens", 0)
                        total_input_tokens = usage_data_all.get("total_input_tokens", 0) 
                        total_output_tokens = usage_data_all.get("total_output_tokens", 0)
                        total_conversations = usage_data_all.get("conversation_count", 0)
                        total_cost_usd = usage_data_all.get("total_cost_usd", 0.0)
                        print(f"全期間での会社ID {company_id} のトークン使用量 {total_tokens_used:,} tokens")
                    else:
                        print("⚠️ 全期間でもトークン使用量データがない")
            else:
                print("⚠️ 会社IDがない - 個人ユーザーのトークン使用量は現在未対応")
        except Exception as e:
            print(f"⚠️ トークン使用量取得エラー: {e} - ダミーデータを使用します")
        
        # 基本設定
        basic_plan_limit = 25000000  # 25M tokens
        usage_percentage = (total_tokens_used / basic_plan_limit * 100) if basic_plan_limit > 0 else 0
        remaining_tokens = max(0, basic_plan_limit - total_tokens_used)
        
        # 警告レベル計算
        warning_level = "safe"
        if usage_percentage >= 95:
            warning_level = "critical"
        elif usage_percentage >= 80:
            warning_level = "warning"
        
        # 日本円での料金計算
        from modules.token_counter import calculate_japanese_pricing
        pricing_info = calculate_japanese_pricing(total_tokens_used)
        
        # 実際のデータを返す
        data = {
            "total_tokens_used": total_tokens_used,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "basic_plan_limit": basic_plan_limit,
            "current_month_cost": pricing_info["total_cost_jpy"],
            "cost_breakdown": {
                "basic_plan_cost": pricing_info["basic_plan_cost"],
                "tier1_cost": pricing_info["tier1_cost"],
                "tier2_cost": pricing_info["tier2_cost"],
                "tier3_cost": pricing_info["tier3_cost"],
                "total_cost_jpy": pricing_info["total_cost_jpy"]
            },
            "usage_percentage": round(usage_percentage, 1),
            "remaining_tokens": remaining_tokens,
            "warning_level": warning_level,
            "company_users_count": company_users_count,
            "active_users": min(total_conversations // 5 if total_conversations > 0 else 1, company_users_count),
            "total_conversations": total_conversations,
            "cost_usd": total_cost_usd,
            "current_month": "2025-01",
            "company_name": company_name
        }
        
        print(f"実際のデータを返却します company_users_count={company_users_count}, total_tokens={total_tokens_used:,}, company_name={company_name}")
        return data
        
    except Exception as e:
        print(f"会社トークン使用量取得エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"トークン使用量の取得中にエラーが発生しました: {str(e)}")

# 料金シミュレーションエンドポイント
@app.post("/chatbot/api/simulate-cost", response_model=dict)
async def simulate_token_cost(request: dict, current_user = Depends(get_current_user)):
    """指定されたトークン数での料金をシミュレーション"""
    try:
        print(f"simulate-costエンドポイントが呼び出されました - ユーザー: {current_user['email']}")
        
        tokens = request.get("tokens", 0)
        print(f"シミュレーション対象トークン数: {tokens}")
        
        if not isinstance(tokens, (int, float)) or tokens < 0:
            raise HTTPException(status_code=400, detail="有効なトークン数を指定してください")
        
        # 簡易料金計算（モデルによる）
        basic_plan_cost = 150000  # ¥150,000
        tier1_cost = 0
        tier2_cost = 0
        tier3_cost = 0
        
        # 基本プラン制限を超えた場合の計算
        if tokens > 25000000:  # 25M tokens
            excess_tokens = tokens - 25000000
            
            # Tier 1: 25M-50M (¥15/1,000 tokens)
            if excess_tokens > 0:
                tier1_tokens = min(excess_tokens, 25000000)  # 最大25M tokens
                tier1_cost = (tier1_tokens / 1000) * 15
                excess_tokens -= tier1_tokens
            
            # Tier 2: 50M-100M (¥12/1,000 tokens)
            if excess_tokens > 0:
                tier2_tokens = min(excess_tokens, 50000000)  # 最大50M tokens
                tier2_cost = (tier2_tokens / 1000) * 12
                excess_tokens -= tier2_tokens
            
            # Tier 3: 100M+ (¥10/1,000 tokens)
            if excess_tokens > 0:
                tier3_cost = (excess_tokens / 1000) * 10
        
        total_cost = basic_plan_cost + tier1_cost + tier2_cost + tier3_cost
        effective_rate = total_cost / tokens * 1000 if tokens > 0 else 0
        
        result = {
            "simulated_tokens": tokens,
            "cost_breakdown": {
                "total_cost": int(total_cost),
                "basic_plan": basic_plan_cost,
                "tier1_cost": int(tier1_cost),
                "tier2_cost": int(tier2_cost),
                "tier3_cost": int(tier3_cost),
                "effective_rate": round(effective_rate, 2)
            },
            "tokens_in_millions": tokens / 1000000,
            "cost_per_million": total_cost / (tokens / 1000000) if tokens > 0 else 0
        }
        
        print(f"シミュレーション結果: {result}")
        return result
        
    except Exception as e:
        print(f"料金シミュレーションエラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"料金シミュレーション中にエラーが発生しました: {str(e)}")

# プロンプト参照を含む会社全体のトークン使用量と料金情報を取得するエンドポイント
@app.get("/chatbot/api/company-token-usage-with-prompts", response_model=dict)
async def get_company_token_usage_with_prompts(current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """プロンプト参照を含む会社全体のトークン使用量と料金情報を取得する"""
    try:
        print(f"company-token-usage-with-promptsエンドポイントが呼び出されました - ユーザー: {current_user['email']}")
        
        # ユーザーの会社IDを取得
        from supabase_adapter import select_data
        user_result = select_data("users", columns="company_id", filters={"id": current_user["id"]})
        company_id = None
        if user_result and user_result.data:
            company_id = user_result.data[0].get("company_id")
        
        # 実際の会社ユーザー数を取得
        company_users_count = 1
        company_name = "あなたの会社"
        
        if company_id:
            company_users_result = select_data("users", columns="id, name", filters={"company_id": company_id})
            if company_users_result and company_users_result.data:
                company_users_count = len(company_users_result.data)
            
            company_result = select_data("companies", columns="name", filters={"id": company_id})
            if company_result and company_result.data:
                company_name = company_result.data[0].get("name", "あなたの会社")
        
        # 実際のトークン使用量とプロンプト参照数を取得
        total_tokens_used = 0
        total_input_tokens = 0
        total_output_tokens = 0
        total_conversations = 0
        total_cost_usd = 0.0
        prompt_references_total = 0
        base_cost_total = 0.0
        prompt_cost_total = 0.0
        
        try:
            if company_id:
                # 新しい料金体系でのデータを取得
                chat_result = select_data(
                    "chat_history", 
                    columns="input_tokens,output_tokens,total_tokens,cost_usd,prompt_references,base_cost_usd,prompt_cost_usd",
                    filters={"company_id": company_id}
                )
                
                if chat_result and chat_result.data:
                    chats = chat_result.data
                    total_input_tokens = sum(chat.get('input_tokens', 0) or 0 for chat in chats)
                    total_output_tokens = sum(chat.get('output_tokens', 0) or 0 for chat in chats)
                    total_tokens_used = sum(chat.get('total_tokens', 0) or 0 for chat in chats)
                    
                    # 新しいカラムがある場合はそれを使用、ない場合は従来のcost_usdを使用
                    has_new_columns = any(chat.get('base_cost_usd') is not None for chat in chats)
                    
                    if has_new_columns:
                        print("✅ 新料金体系カラムを検出 - 正確な計算を使用")
                        prompt_references_total = sum(chat.get('prompt_references', 0) or 0 for chat in chats)
                        base_cost_total = sum(float(chat.get('base_cost_usd', 0) or 0) for chat in chats)
                        prompt_cost_total = sum(float(chat.get('prompt_cost_usd', 0) or 0) for chat in chats)
                        total_cost_usd = base_cost_total + prompt_cost_total
                    else:
                        print("⚠️ 新料金体系カラムなし - 既存データから推定計算")
                        # 既存のcost_usdから推定計算
                        total_cost_usd = sum(float(chat.get('cost_usd', 0) or 0) for chat in chats)
                        
                        # 推定値を計算（アクティブリソース数は分からないので仮定）
                        estimated_prompt_refs = len(chats) * 2  # 平均2つのリソース参照と仮定
                        prompt_references_total = estimated_prompt_refs
                        
                                                # トークンから基本コストを逆算
                        if total_tokens_used > 0:
                            if total_cost_usd > 0:
                                # 既存のコストデータを使用
                                estimated_prompt_cost = estimated_prompt_refs * 0.001
                                base_cost_total = max(0, total_cost_usd - estimated_prompt_cost)
                                prompt_cost_total = estimated_prompt_cost
                            else:
                                # コストが0の場合は新料金体系で再計算
                                print("💰 コストが0のため新料金体系で再計算中...")
                                from modules.token_counter import TokenCounter
                                counter = TokenCounter()
                                pricing = counter.pricing["gemini-pro"]
                                
                                # 30%がinput、70%がoutputと仮定
                                estimated_input = total_input_tokens if total_input_tokens > 0 else int(total_tokens_used * 0.3)
                                estimated_output = total_output_tokens if total_output_tokens > 0 else int(total_tokens_used * 0.7)
                                
                                input_cost = (estimated_input / 1000) * pricing["input"]
                                output_cost = (estimated_output / 1000) * pricing["output"]
                                base_cost_total = input_cost + output_cost
                                prompt_cost_total = estimated_prompt_refs * counter.prompt_reference_cost
                                total_cost_usd = base_cost_total + prompt_cost_total
                                
                                print(f"再計算結果 - 基本: ${base_cost_total:.6f}, プロンプト: ${prompt_cost_total:.6f}, 総計: ${total_cost_usd:.6f}")
                        else:
                            base_cost_total = 0.0
                            prompt_cost_total = 0.0
                    
                    total_conversations = len(chats)
                    
                    print(f"料金計算データ - トークン: {total_tokens_used:,}, プロンプト参照: {prompt_references_total}, 総コスト: ${total_cost_usd:.6f}")
                    print(f"  基本コスト: ${base_cost_total:.6f}, プロンプトコスト: ${prompt_cost_total:.6f}")
                else:
                    print("⚠️ チャットデータがありません")
            else:
                print("⚠️ 会社IDがない")
        except Exception as e:
            print(f"⚠️ トークン使用量取得エラー: {e}")
            import traceback
            print(f"エラー詳細: {traceback.format_exc()}")
        
        # 基本設定
        basic_plan_limit = 25000000  # 25M tokens
        usage_percentage = (total_tokens_used / basic_plan_limit * 100) if basic_plan_limit > 0 else 0
        remaining_tokens = max(0, basic_plan_limit - total_tokens_used)
        
        # 警告レベル計算
        warning_level = "safe"
        if usage_percentage >= 95:
            warning_level = "critical"
        elif usage_percentage >= 80:
            warning_level = "warning"
        
        # 新しい料金体系での計算（USD → JPY変換）
        usd_to_jpy = 150  # 1USD = 150JPY（仮定）
        current_month_cost = total_cost_usd * usd_to_jpy
        
        data = {
            "total_tokens_used": total_tokens_used,
            "input_tokens_total": total_input_tokens,
            "output_tokens_total": total_output_tokens,
            "prompt_references_total": prompt_references_total,
            "basic_plan_limit": basic_plan_limit,
            "current_month_cost": int(current_month_cost),
            "cost_breakdown": {
                "basic_plan": 0,  # 新料金体系では基本プラン料金なし
                "tier1_cost": 0,
                "tier2_cost": 0,
                "tier3_cost": 0,
                "total_cost": int(current_month_cost),
                "base_cost": int(base_cost_total * usd_to_jpy),
                "prompt_cost": int(prompt_cost_total * usd_to_jpy)
            },
            "usage_percentage": round(usage_percentage, 1),
            "remaining_tokens": remaining_tokens,
            "warning_level": warning_level,
            "company_users_count": company_users_count,
            "total_conversations": total_conversations,
            "cost_usd": total_cost_usd,
            "company_name": company_name
        }
        
        print(f"📊 最終データを返却:")
        print(f"  トークン: {total_tokens_used:,}")
        print(f"  プロンプト参照: {prompt_references_total}")
        print(f"  USD総コスト: ${total_cost_usd:.6f}")
        print(f"  JPY総コスト: ¥{current_month_cost:.0f}")
        print(f"  基本コスト(JPY): ¥{int(base_cost_total * usd_to_jpy)}")
        print(f"  プロンプトコスト(JPY): ¥{int(prompt_cost_total * usd_to_jpy)}")
        
        return data
        
    except Exception as e:
        print(f"プロンプト参照含むトークン使用量取得エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"トークン使用量の取得中にエラーが発生しました: {str(e)}")

# プロンプト参照を含む料金シミュレーションエンドポイント
@app.post("/chatbot/api/simulate-cost-with-prompts", response_model=dict)
async def simulate_token_cost_with_prompts(request: dict, current_user = Depends(get_current_user)):
    """プロンプト参照を含む指定されたトークン数での料金をシミュレーション"""
    try:
        print(f"simulate-cost-with-promptsエンドポイントが呼び出されました - ユーザー: {current_user['email']}")
        
        tokens = request.get("tokens", 0)
        prompt_references = request.get("prompt_references", 0)
        
        print(f"シミュレーション - トークン: {tokens}, プロンプト参照: {prompt_references}")
        
        if not isinstance(tokens, (int, float)) or tokens < 0:
            raise HTTPException(status_code=400, detail="有効なトークン数を指定してください")
        
        if not isinstance(prompt_references, (int, float)) or prompt_references < 0:
            raise HTTPException(status_code=400, detail="有効なプロンプト参照数を指定してください")
        
        # 新しい料金体系での計算
        from modules.token_counter import TokenCounter
        counter = TokenCounter()
        
        # 仮のテキストでトークン計算をシミュレート
        # 実際の計算ではinput/outputの比率を仮定
        input_tokens = int(tokens * 0.3)  # 30%がinput
        output_tokens = int(tokens * 0.7)  # 70%がoutput
        
        # 新料金体系で計算
        pricing = counter.pricing["workmate-standard"]
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        base_cost = input_cost + output_cost
        
        # プロンプト参照コスト
        prompt_cost = prompt_references * counter.prompt_reference_cost
        total_cost = base_cost + prompt_cost
        
        # USD → JPY変換
        usd_to_jpy = 150
        total_cost_jpy = total_cost * usd_to_jpy
        base_cost_jpy = base_cost * usd_to_jpy
        prompt_cost_jpy = prompt_cost * usd_to_jpy
        
        effective_rate = total_cost_jpy / tokens * 1000 if tokens > 0 else 0
        
        result = {
            "simulated_tokens": tokens,
            "prompt_references": prompt_references,
            "cost_breakdown": {
                "total_cost": int(total_cost_jpy),
                "basic_plan": 0,
                "tier1_cost": 0,
                "tier2_cost": 0,
                "tier3_cost": 0,
                "base_cost": int(base_cost_jpy),
                "prompt_cost": int(prompt_cost_jpy),
                "effective_rate": round(effective_rate, 2)
            },
            "tokens_in_millions": tokens / 1000000,
            "cost_per_million": total_cost_jpy / (tokens / 1000000) if tokens > 0 else 0
        }
        
        print(f"新料金体系シミュレーション結果: {result}")
        return result
        
    except Exception as e:
        print(f"プロンプト参照含む料金シミュレーションエラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"料金シミュレーション中にエラーが発生しました: {str(e)}")

# プラン履歴を取得するエンドポイント
@app.get("/chatbot/api/plan-history", response_model=dict)
async def admin_get_plan_history(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """プラン変更履歴を取得する"""
    try:
        print(f"プラン履歴取得開始 - ユーザー: {current_user['email']} (ロール: {current_user['role']})")
        
        # 権限チェック
        is_admin = current_user["role"] == "admin"
        is_admin_user = current_user["role"] == "admin_user"
        is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"] and current_user.get("is_special_admin", False)
        
        # 特定のcompany_idのユーザーも料金タブアクセスを許可
        is_special_company_user = current_user.get("company_id") == "77acc2e2-ce67-458d-bd38-7af0476b297a"
        
        if not (is_admin or is_admin_user or is_special_admin or is_special_company_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この操作には管理者の権限が必要です"
            )
        
        from supabase_adapter import select_data
        
        # プラン履歴を取得（会社によってフィルタリング）
        if is_special_company_user and not (is_admin or is_admin_user or is_special_admin):
            # 特定の会社のユーザーは自分の会社の履歴のみを取得
            company_id = current_user.get("company_id")
            print(f"特定会社のユーザー向け履歴取得: company_id={company_id}")
            
            # 同じ会社のユーザーIDを取得
            company_users_result = select_data(
                "users",
                columns="id",
                filters={"company_id": company_id}
            )
            
            if company_users_result and company_users_result.data:
                user_ids = [user["id"] for user in company_users_result.data]
                print(f"対象ユーザーID: {user_ids}")
                
                # 会社のユーザーのプラン履歴のみを取得
                user_ids_str = ','.join(f"'{uid}'" for uid in user_ids)
                plan_history_result = select_data(
                    "plan_history",
                    columns="id, user_id, from_plan, to_plan, changed_at, duration_days",
                    filters={"user_id": f"in.({user_ids_str})"},
                    order="changed_at.desc"
                )
            else:
                # 会社のユーザーが見つからない場合は空の結果
                plan_history_result = None
        else:
            # 管理者は全ての履歴を取得
            plan_history_result = select_data(
                "plan_history",
                columns="id, user_id, from_plan, to_plan, changed_at, duration_days",
                order="changed_at.desc"
            )
        
        history_list = []
        if plan_history_result and plan_history_result.data:
            for record in plan_history_result.data:
                # ユーザー情報を取得
                user_result = select_data(
                    "users",
                    columns="name, email",
                    filters={"id": record["user_id"]}
                )
                
                user_name = "不明なユーザー"
                user_email = "unknown@example.com"
                if user_result and user_result.data:
                    user_data = user_result.data[0]
                    user_name = user_data.get("name", "名前なし")
                    user_email = user_data.get("email", "unknown@example.com")
                
                history_item = {
                    "id": record["id"],
                    "user_id": record["user_id"],
                    "user_name": user_name,
                    "user_email": user_email,
                    "from_plan": record["from_plan"],
                    "to_plan": record["to_plan"],
                    "changed_at": record["changed_at"],
                    "duration_days": record.get("duration_days")
                }
                history_list.append(history_item)
        
        print(f"プラン履歴取得完了: {len(history_list)}件")
        
        return {
            "success": True,
            "history": history_list,
            "count": len(history_list)
        }
        
    except Exception as e:
        print(f"プラン履歴取得エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"プラン履歴の取得中にエラーが発生しました: {str(e)}"
        )

# Google Drive連携エンドポイント
@app.post("/chatbot/api/upload-from-drive")
async def upload_from_google_drive(
    file_id: str = Form(...),
    access_token: str = Form(...),
    file_name: str = Form(...),
    mime_type: str = Form(...),
    current_user = Depends(get_current_user),
    db: SupabaseConnection = Depends(get_db)
):
    """Google Driveからファイルをアップロード"""
    try:
        # Google Driveハンドラー初期化
        drive_handler = GoogleDriveHandler()
        
        print(f"Google Driveファイルアップロード開始 {file_name} (ID: {file_id})")
        
        # サポートされているファイル形式かチェック
        if not drive_handler.is_supported_file(mime_type):
            raise HTTPException(
                status_code=400, 
                detail=f"サポートされているファイル形式ではありません: {mime_type}"
            )
        
        # ファイルメタデータ取得
        file_metadata = await drive_handler.get_file_metadata(file_id, access_token)
        if not file_metadata:
            raise HTTPException(status_code=400, detail="ファイルが見つかりません")
        
        # ファイルサイズチェック。10MB制限
        file_size = int(file_metadata.get('size', 0))
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400, 
                detail=f"ファイルサイズが大きすぎます({file_size / (1024*1024):.1f}MB)、10MB以下のファイルをご利用ください"
            )
        
        # ファイルダウンロード
        print(f"Google Driveからファイルダウンロード中: {file_name}")
        file_content = await drive_handler.download_file(file_id, access_token, mime_type)
        if not file_content:
            raise HTTPException(status_code=400, detail="ファイルのダウンロードに失敗しました")
        
        # 一時ファイル作成
        print(f"一時ファイル作成中: {file_name}")
        temp_file_path = await drive_handler.create_temp_file(file_content, file_name)
        
        try:
            # UploadFileオブジェクトを模倣するクラス
            class MockUploadFile:
                def __init__(self, filename: str, content: bytes):
                    self.filename = filename
                    self.content = content
                
                async def read(self):
                    return self.content
            
            # Google DocsやSheetsの場合、拡張子を変更
            processed_filename = file_name
            if mime_type == 'application/vnd.google-apps.document':
                # Google DocはPDFに変換されるで.pdf拡張子にする
                base_name = os.path.splitext(file_name)[0]
                processed_filename = f"{base_name}.pdf"
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                # Google SheetはExcelに変換されるで.xlsx拡張子にする
                base_name = os.path.splitext(file_name)[0]
                processed_filename = f"{base_name}.xlsx"
            
            # 既存のprocess_file関数を使用
            mock_file = MockUploadFile(processed_filename, file_content)
            company_id = current_user.get("company_id")
            print(f"🔍 [UPLOAD DEBUG] Google Driveアップロード時のcompany_id: {company_id}")
            print(f"🔍 [UPLOAD DEBUG] current_user: {current_user}")
            result = await process_file(
                mock_file,
                request=None,
                user_id=current_user["id"],
                company_id=company_id,
                db=db
            )
            
            print(f"Google Driveファイル処理完了 {file_name}")
            return result
            
        finally:
            # 一時ファイル削除
            drive_handler.cleanup_temp_file(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Google Driveアップロードエラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Google Drive処理エラー: {str(e)}")

@app.get("/chatbot/api/drive/files")
async def list_drive_files(
    access_token: str,
    folder_id: str = 'root',
    search_query: str = None,
    current_user = Depends(get_current_user)
):
    """Google Driveファイル一覧取得"""
    try:
        print(f"Google Driveファイル一覧取得 フォルダID={folder_id}")
        
        drive_handler = GoogleDriveHandler()
        files = await drive_handler.list_files(access_token, folder_id, search_query)
        
        # サポートされているファイルのみフィルター
        supported_files = [
            file for file in files 
            if file.get('mimeType') == 'application/vnd.google-apps.folder' or 
               drive_handler.is_supported_file(file.get('mimeType', ''))
        ]
        
        print(f"Google Driveファイル一覧取得完了 {len(supported_files)}件")
        return {"files": supported_files}
        
    except Exception as e:
        print(f"Google Driveファイル一覧取得エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"ファイル一覧取得エラー: {str(e)}")

# その他のルートパスをindex.htmlにリダイレクト！
# SPAのルーティング用の
# 注意：これを最後に登録することで、他のAPIエンドポイントを優先する
@app.get("/{full_path:path}", include_in_schema=False)
async def catch_all(full_path: str):
    print(f"catch_all handler called with path: {full_path}")
    
    # APIエンドポイントの場合は404を返す（より厳密なチェック）
    # ただし、既に処理済みのAPIリクエストは除外
    if full_path.startswith("chatbot/api/"):
        print(f"API endpoint not found: {full_path}")
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # SPAルーチェックング用にindex.htmlを返す
    index_path = os.path.join(frontend_build_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Not Found")

# アプリケーションの実行
if __name__ == "__main__":
    import uvicorn
    from modules.config import get_port
    port = get_port()
    uvicorn.run(app, host="0.0.0.0", port=port, timeout_keep_alive=600)


