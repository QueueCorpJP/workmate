"""
メインアプリケーションファイル
FastAPIアプリケーションの設定とルーチE��ングを行いまぁEmain.py
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
# モジュールのインポ�EチEfrom modules.config import setup_logging, setup_gemini
from modules.company import DEFAULT_COMPANY_NAME
from modules.database import get_db, init_db, get_all_users, get_demo_usage_stats, create_user, SupabaseConnection
from supabase_adapter import get_supabase_client, select_data, insert_data, update_data, delete_data
from modules.models import (
    ChatMessage, ChatResponse, ChatHistoryItem, AnalysisResult,
    EmployeeUsageItem, EmployeeUsageResult, UrlSubmission,
    CompanyNameResponse, CompanyNameRequest, ResourcesResult,
    ResourceToggleResponse, UserLogin, UserRegister, UserResponse,
    UserWithLimits, DemoUsageStats, AdminUserCreate, UpgradePlanRequest,
    UpgradePlanResponse, SubscriptionInfo
)
from modules.knowledge import process_url, process_file, get_knowledge_base_info
from modules.knowledge.google_drive import GoogleDriveHandler
from modules.chat import process_chat, set_model as set_chat_model
from modules.admin import (
    get_chat_history, analyze_chats, get_employee_details,
    get_employee_usage, get_uploaded_resources, toggle_resource_active,
    get_company_employees, set_model as set_admin_model, delete_resource
)
from modules.company import get_company_name, set_company_name
from modules.auth import get_current_user, get_current_admin, register_new_user, get_admin_or_user, get_company_admin
from modules.resource import get_uploaded_resources_by_company_id, toggle_resource_active_by_id, remove_resource_by_id
import json
from modules.validation import validate_login_input, validate_user_input
import csv
import io

# ロギングの設宁Elogger = setup_logging()

# Gemini APIの設宁Emodel = setup_gemini()

# モチE��の設宁Eset_chat_model(model)
set_admin_model(model)

# FastAPIアプリケーションの作�E
app = FastAPI()

# グローバル例外ハンドラー
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """すべての例外をキャチE��して適刁E��レスポンスを返す"""
    # エラーの詳細をログに記録
    logger.error(f"グローバル例外ハンドラーがエラーをキャチE��しました: {str(exc)}")
    logger.error(traceback.format_exc())
    
    # 'int' object has no attribute 'strip' エラーの特別処理
    if "'int' object has no attribute 'strip'" in str(exc):
        return JSONResponse(
            status_code=500,
            content={"detail": "データ型エラーが発生しました。管理者に連絡してください。"}
        )
    
    # そ�E他�E例外�E通常のエラーレスポンスを返す
    return JSONResponse(
        status_code=500,
        content={"detail": f"サーバ�Eエラーが発生しました: {str(exc)}"}
    )

# バリチE�Eションエラーハンドラー
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """リクエストバリチE�Eションエラーを�E琁E��めE""
    logger.error(f"バリチE�Eションエラー: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": f"リクエストデータが無効でぁE {str(exc)}"}
    )

# CORSミドルウェアの設宁E# すべてのオリジンを許可する
origins = []
# 環墁E��数からCORSオリジンを取征Eallowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173,https://chatbot-frontend-nine-eta.vercel.app")
if allowed_origins:
    origins = [origin.strip() for origin in allowed_origins.split(",")]
    
# 開発環墁E��は追加のローカルオリジンを許可
if os.getenv("ENVIRONMENT", "development") == "development":
    # 環墁E��数からフロントエンド�Eートを取得（デフォルト値を設定！E    frontend_ports = os.getenv("FRONTEND_PORTS", "3000,3025,5173")
    ports = [port.strip() for port in frontend_ports.split(",")]
    
    dev_origins = []
    for port in ports:
        if port.isdigit():
            dev_origins.extend([
                f"http://localhost:{port}",
                f"http://127.0.0.1:{port}"
            ])
    
    origins.extend(dev_origins)

# すべてのオリジンを許可する場合（開発環墁E�Eみ推奨�E�Eif os.getenv("ALLOW_ALL_ORIGINS", "false").lower() == "true":
    origins.append("*")

# CORSミドルウェアを最初に追加して優先度を上げめEapp.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # すべてのオリジンを許可
    allow_credentials=True,  # クレチE��シャルを含むリクエストを許可
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # 明示皁E��HTTPメソチE��を指宁E    allow_headers=["*"],  # すべてのヘッダーを許可
    expose_headers=["*"],  # レスポンスヘッダーを�E閁E    max_age=86400,  # プリフライトリクエスト�EキャチE��ュ時間�E�秒！E)

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

# CORSミドルウェアの設宁E# 統合環墁E��は、すべてのオリジンを許可する
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["https://chatbot-frontend-nine-eta.vercel.app"],  # すべてのオリジンを許可
#     allow_credentials=True,  # クレチE��シャルを含むリクエストを許可
#     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#     allow_headers=["*"],
# )

# アプリケーション起動時にチE�Eタベ�Eスを�E期化
init_db()

# チE�Eタベ�Eス整合性をチェチE��
try:
    from modules.database import ensure_usage_limits_integrity, get_db
    print("起動時チE�Eタベ�Eス整合性チェチE��を実行中...")
    db_connection = SupabaseConnection()
    fixed_count = ensure_usage_limits_integrity(db_connection)
    if fixed_count > 0:
        print(f"起動時整合性チェチE��完亁E {fixed_count}個�Eusage_limitsレコードを修正しました")
    else:
        print("起動時整合性チェチE��完亁E 修正が忁E��なレコード�Eありませんでした")
    db_connection.close()
except Exception as e:
    print(f"起動時整合性チェチE��でエラーが発生しましたが、アプリケーションは継続しまぁE {str(e)}")

# 認証関連エンド�EインチE@app.post("/chatbot/api/auth/login", response_model=UserWithLimits)
async def login(credentials: UserLogin, db: SupabaseConnection = Depends(get_db)):
    """ユーザーログイン"""
    # 入力値バリチE�Eション
    is_valid, errors = validate_login_input(credentials.email, credentials.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(errors)
        )
    
    # 直接チE�Eタベ�Eスから認証
    from modules.database import authenticate_user, get_usage_limits
    user = authenticate_user(credentials.email, credentials.password, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なメールアドレスまた�EパスワードでぁE,
        )
    
    # 利用制限情報を取征E    limits = get_usage_limits(user["id"], db)
    
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

@app.post("/chatbot/api/auth/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: SupabaseConnection = Depends(get_db)):
    """新規ユーザー登録"""
    try:
        # 入力値バリチE�Eション
        is_valid, errors = validate_user_input(user_data.email, user_data.password, user_data.name)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="; ".join(errors)
            )
        
        # 管琁E��E��限チェチE��は不要E��デモ版では誰でも登録可能�E�E        return register_new_user(user_data.email, user_data.password, user_data.name, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"登録に失敗しました: {str(e)}"
        )

@app.post("/chatbot/api/admin/register-user", response_model=UserResponse)
async def admin_register_user(user_data: AdminUserCreate, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """管琁E��E��よる新規ユーザー登録"""
    try:
        # 入力値バリチE�Eション
        from modules.validation import validate_user_input
        
        # AdminUserCreateモチE��から名前を取得（存在しなぁE��合�Eメールアドレスから生�E�E�E        name = getattr(user_data, 'name', user_data.email.split('@')[0])
        
        is_valid, errors = validate_user_input(user_data.email, user_data.password, name)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="; ".join(errors)
            )
        
        # roleとcompany_idの空斁E��チェチE��を強匁E        if not user_data.role or not user_data.role.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="役割(role)は忁E��です、E
            )

        # 会社IDの事前チェチE��を緩咁E- 後続�E処琁E��作�E老E�Ecompany_idを継承する場合があるため
        if user_data.company_id and not user_data.company_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="会社IDが指定されてぁE��場合�E空斁E���Eにはできません、E
            )
        
        # まず、メールアドレスが既に存在するかチェチE��
        from supabase_adapter import select_data
        existing_user_result = select_data("users", filters={"email": user_data.email})
        
        if existing_user_result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="こ�Eメールアドレスは既に登録されてぁE��ぁE
            )
        
        # 特別な管琁E��E��Eueue@queueu-tech.jp�E�また�Eadminロールの場合�Euserロールのみ作�E可能
        is_special_admin = current_user["email"] == "queue@queueu-tech.jp" and current_user.get("is_special_admin", False)
        is_admin = current_user["role"] == "admin"
        
        if is_special_admin or is_admin:
            print(f"管琁E��E��限でユーザー作�E: 特別管琁E��E{is_special_admin}, admin={is_admin}")
            
            # adminロールは常にuserロールのアカウント�Eみ作�E可能
            role = "user"
            
            # 会社IDの持E��E            company_id = None
            company_name = ""
            
            if hasattr(user_data, "company_name") and user_data.company_name:
                # 会社名が持E��されてぁE��場合、新しい会社を作�E
                from modules.database import create_company
                company_id = create_company(user_data.company_name, db)
                company_name = user_data.company_name
                print(f"特別管琁E��E��より新しい会社 '{user_data.company_name}' が作�Eされました (ID: {company_id})")
                # 新しい会社作�Eなので作�E老E�E会社IDは継承しなぁE                new_company_created = True
            elif hasattr(user_data, "company_id") and user_data.company_id:
                # 持E��された会社IDが存在するかチェチE��
                company_result = select_data("companies", filters={"id": user_data.company_id})
                if not company_result.data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="持E��された会社IDが存在しません"
                    )
                company_id = user_data.company_id
                company_name = company_result.data[0].get("name", "")
                print(f"管琁E��E��より既存�E会社ID {company_id} が指定されました")
                new_company_created = False
            else:
                # 会社IDも会社名も持E��されてぁE��ぁE��吁E                if is_special_admin:
                    # 特別管琁E��E�E場合�E新しい会社IDを�E動生戁E                    company_id = None  # create_user関数で自動生成される
                    print("特別管琁E��E��より新しい会社IDが�E動生成されまぁE)
                    new_company_created = True
                else:
                    # 通常の管琁E��E�E場合�E作�E老E�E会社IDを使用
                    company_id = current_user.get("company_id")
                    if company_id:
                        # 会社名も取征E                        company_result = select_data("companies", filters={"id": company_id})
                        if company_result.data:
                            company_name = company_result.data[0].get("name", "")
                        print(f"作�E老E�E会社ID {company_id} を使用しまぁE)
                    new_company_created = False
            
            # 特別管琁E��E��社長ユーザーを作�Eする場合、会社IDが指定されてぁE��ければ新しい独立した会社を作�E
            if is_special_admin and company_id is None:
                # 特別管琁E��E��会社ID未持E��で社長ユーザー作�E ↁE新しい独立した会社を作�E
                creator_id_to_pass = None
                print("特別管琁E��E��よる社長ユーザー作�E: 新しい独立した会社IDを生成しまぁE)
            elif is_special_admin and new_company_created:
                # 特別管琁E��E��新しい会社名を持E��して会社作�E ↁE新しい独立した会社
                creator_id_to_pass = None
                print("特別管琁E��E��よる新会社作�E: 作�E老E�E会社IDは継承しません")
            else:
                # そ�E他�E場合�E作�E老E�E会社IDを継承
                creator_id_to_pass = current_user["id"]
            
            # create_user関数を直接呼び出す（管琁E��E��作�Eするアカウント�E作�E老E�EスチE�Eタスを継承�E�E            user_id = create_user(
                email=user_data.email,
                password=user_data.password,
                name=name,
                role=role,
                company_id=company_id,
                db=db,
                creator_user_id=creator_id_to_pass  # 新しい会社作�E時�ENone
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
            # userロールの場合�Eみ社員アカウント作�E可能、employeeロールは作�E権限なぁE            if current_user["role"] == "employee":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="社員アカウントにはユーザー作�E権限がありません"
                )
            
            # userロールの場合�E社員アカウントとして登録�E�管琁E��面にアクセスできなぁE��E            # 現在のユーザーの会社IDを取得して新しいユーザーに設宁E            company_id = current_user.get("company_id")
            
            # 会社IDがなぁE��合�Eエラー
            if not company_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="会社IDが設定されてぁE��せん。管琁E��E��お問ぁE��わせください、E
                )
            
            # create_user関数を直接呼び出して会社IDを設定し作�E老E�EスチE�Eタスを継承
            user_id = create_user(
                email=user_data.email,
                password=user_data.password,
                name=name,
                role="employee",
                company_id=company_id,
                db=db,
                creator_user_id=current_user["id"]  # 作�E老EDを渡ぁE            )
            
            return {
                "id": user_id,
                "email": user_data.email,
                "name": name,
                "role": "employee",
                "company_name": "",
                "created_at": datetime.datetime.now().isoformat()
            }
    except HTTPException as e:
        # HTTPExceptionはそ�Eまま再送�E
        account_type = "ユーザーアカウンチE if (current_user["email"] == "queue@queueu-tech.jp" or current_user["role"] == "admin") else "社員アカウンチE
        print(f"{account_type}作�Eエラー: {e.status_code}: {e.detail}")
        raise
    except Exception as e:
        account_type = "ユーザーアカウンチE if (current_user["email"] == "queue@queueu-tech.jp" or current_user["role"] == "admin") else "社員アカウンチE
        print(f"{account_type}作�Eエラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{account_type}作�Eに失敗しました: {str(e)}"
        )

@app.delete("/chatbot/api/admin/delete-user/{user_id}", response_model=dict)
async def admin_delete_user(user_id: str, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """管琁E��E��よるユーザー削除"""
    # 特別な管琁E��E��Eueue@queueu-tech.jp�E��Eみがユーザーを削除できる
    if current_user["email"] != "queue@queueu-tech.jp" or not current_user.get("is_special_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="こ�E操作には特別な管琁E��E��限が忁E��でぁE
        )
    
    # 自刁E�E身は削除できなぁE    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="自刁E�E身を削除することはできません"
        )
    
    # ユーザーの存在確誁E    user_result = select_data("users", filters={"id": user_id})
    
    if not user_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="持E��されたユーザーが見つかりません"
        )
    
    user = user_result.data[0]
    
    # ユーザーの削除
    delete_data("usage_limits", "user_id", user_id)
    delete_data("document_sources", "uploaded_by", user_id)
    delete_data("users", "id", user_id)
    
    return {"message": f"ユーザー {user['email']} を削除しました", "deleted_user_id": user_id}

@app.get("/chatbot/api/admin/users", response_model=List[UserResponse])
async def admin_get_users(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """全ユーザー一覧を取征E""
    # 特別な管琁E��E��Eueue@queueu-tech.jp�E��Eみが�Eユーザー一覧を取得できる
    if current_user["email"] != "queue@queueu-tech.jp" or not current_user.get("is_special_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="こ�E操作には特別な管琁E��E��限が忁E��でぁE
        )
    return get_all_users(db)

@app.get("/chatbot/api/admin/demo-stats", response_model=DemoUsageStats)
async def admin_get_demo_stats(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """チE��利用状況�E統計を取征E""
    return get_demo_usage_stats(db)

# URLを送信するエンド�EインチE@app.post("/chatbot/api/submit-url")
async def submit_url(submission: UrlSubmission, current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """URLを送信して知識�Eースを更新"""
    try:
        # URLが空でなぁE��とを確誁E        if not submission.url or not submission.url.strip():
            raise HTTPException(
                status_code=400,
                detail="URLが指定されてぁE��せん、E
            )
            
        # URLの基本皁E��検証
        if not submission.url.startswith(('http://', 'https://')) and not submission.url.startswith('www.'):
            submission.url = 'https://' + submission.url
            
        # URL処琁E��実衁E        result = await process_url(submission.url, current_user["id"], None, db)
        return result
    except Exception as e:
        logger.error(f"URL送信エラー: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 'int' object has no attribute 'strip' エラーの特別処琁E        if "'int' object has no attribute 'strip'" in str(e):
            raise HTTPException(
                status_code=500,
                detail="チE�Eタ型エラーが発生しました。管琁E��E��連絡してください、E
            )
        
        # そ�E他�E例外�E通常のエラーレスポンスを返す
        raise HTTPException(
            status_code=500,
            detail=f"URLの処琁E��にエラーが発生しました: {str(e)}"
        )

# ファイルをアチE�Eロードするエンド�EインチE@app.post("/chatbot/api/upload-knowledge")
async def upload_knowledge(file: UploadFile = File(...), current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """ファイルをアチE�Eロードして知識�Eースを更新"""
    try:
        # ファイル名が存在することを確誁E        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail="ファイルが指定されてぁE��ぁE��、ファイル名が無効です、E
            )
            
        # ファイル拡張子をチェチE���E�Eoogle DriveアチE�Eロード�E場合�EスキチE�E�E�E        if not file.filename.lower().endswith(('.xlsx', '.xls', '.pdf', '.txt', '.avi', '.mp4', '.webp')):
            raise HTTPException(
                status_code=400,
                detail="無効なファイル形式です、Excelファイルまた�EPDFファイル、テキストファイル�E�Exlsx、Exls、Epdf、Etxt�E��Eみ対応してぁE��す、E
            )
            
        # ファイル処琁E��実衁E        result = await process_file(file, current_user["id"], None, db)
        return result
    except Exception as e:
        logger.error(f"ファイルアチE�Eロードエラー: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 'int' object has no attribute 'strip' エラーの特別処琁E        if "'int' object has no attribute 'strip'" in str(e):
            raise HTTPException(
                status_code=500,
                detail="チE�Eタ型エラーが発生しました。管琁E��E��連絡してください、E
            )
        
        # そ�E他�E例外�E通常のエラーレスポンスを返す
        raise HTTPException(
            status_code=500,
            detail=f"ファイルのアチE�Eロード中にエラーが発生しました: {str(e)}"
        )

# 知識�Eース惁E��を取得するエンド�EインチE@app.get("/chatbot/api/knowledge-base")
async def get_knowledge_base(current_user = Depends(get_current_user)):
    """現在の知識�Eースの惁E��を取征E""
    return get_knowledge_base_info()

# チャチE��エンド�EインチE@app.post("/chatbot/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """チャチE��メチE��ージを�E琁E��てGeminiからの応答を返す"""
    # チE��チE���E�現在のユーザー惁E��と利用制限を出劁E    print(f"=== チャチE��処琁E��姁E===")
    print(f"ユーザー惁E��: {current_user}")
    
    # 現在の利用制限を取得して表示
    from modules.database import get_usage_limits
    current_limits = get_usage_limits(current_user["id"], db)
    print(f"現在の利用制陁E {current_limits}")
    
    # ユーザーIDを設宁E    message.user_id = current_user["id"]
    message.employee_name = current_user["name"]
    
    return await process_chat(message, db, current_user)

# チャチE��履歴を取得するエンド�EインチE@app.get("/chatbot/api/admin/chat-history", response_model=List[ChatHistoryItem])
async def admin_get_chat_history(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """チャチE��履歴を取得すめE""
    # 現在のユーザーIDを渡して、そのユーザーのチE�Eタのみを取征E    # 特別な管琁E��E��Eueue@queuefood.co.jp�E��E場合�E全ユーザーのチE�Eタを取得できるようにする
    if current_user["email"] == "queue@queueu-tech.jp" and current_user.get("is_special_admin", False):
        # 特別な管琁E��E�E場合�E全ユーザーのチE�Eタを取征E        return get_chat_history(None, db)
    else:
        # 通常のユーザーの場合�E自刁E�EチE�Eタのみを取征E        user_id = current_user["id"]
        return get_chat_history(user_id, db)

# チャチE��刁E��エンド�EインチE@app.get("/chatbot/api/admin/analyze-chats")
async def admin_analyze_chats(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """チャチE��履歴を�E析すめE""
    try:
        # 特別な管琁E��E��Eueue@queuefood.co.jp�E��E場合�E全ユーザーのチE�Eタを�E析できるようにする
        if current_user["email"] == "queue@queueu-tech.jp" and current_user.get("is_special_admin", False):
            # 特別な管琁E��E�E場合�E全ユーザーのチE�Eタを�E极E            result = await analyze_chats(None, db)
            print(f"刁E��結果: {result}")
            return result
        else:
            # 通常のユーザーの場合�E自刁E�EチE�Eタのみを�E极E            user_id = current_user["id"]
            result = await analyze_chats(user_id, db)
            print(f"刁E��結果: {result}")
            return result
    except Exception as e:
        print(f"チャチE��刁E��エラー: {e}")
        # エラーが発生した場合でも空の結果を返す
        return {
            "total_messages": 0,
            "average_response_time": 0,
            "category_distribution": [],
            "sentiment_distribution": [],
            "daily_usage": [],
            "common_questions": []
        }

# 詳細ビジネス刁E��エンド�EインチE@app.post("/chatbot/api/admin/detailed-analysis")
async def admin_detailed_analysis(request: dict, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """詳細なビジネス刁E��を行う"""
    try:
        # ユーザー惁E��の取征E        is_admin = current_user["role"] == "admin"
        is_user = current_user["role"] == "user"
        is_special_admin = current_user["email"] == "queue@queueu-tech.jp" and current_user.get("is_special_admin", False)
        
        # プロンプトを取征E        prompt = request.get("prompt", "")
        
        # 通常の刁E��結果を取征E        if is_special_admin:
            # 特別管琁E��E�E全チE�Eタで刁E��
            analysis_result = await analyze_chats(None, db)
        else:
            # 一般ユーザーは自刁E�E会社のチE�Eタのみで刁E��
            user_company_id = current_user.get("company_id")
            if user_company_id:
                analysis_result = await analyze_chats(None, db, company_id=user_company_id)
            else:
                # 会社IDがなぁE��合�E自刁E�EチE�Eタのみ
                analysis_result = await analyze_chats(current_user["id"], db)
        
        # より詳細なチャチE��チE�Eタを取征E        try:
            if is_special_admin:
                # 特別管琁E��E�E全チE�Eタを取征E                chat_result = select_data("chat_history", limit=1000, order="created_at desc")
            else:
                # 一般ユーザーは自刁E�E会社のチE�Eタのみ取征E                user_company_id = current_user.get("company_id")
                if user_company_id:
                    chat_result = select_data("chat_history", filters={"company_id": user_company_id}, limit=1000, order="created_at desc")
                else:
                    # 会社IDがなぁE��合�E自刁E�EチE�Eタのみ
                    chat_result = select_data("chat_history", filters={"user_id": current_user["id"]}, limit=1000, order="created_at desc")
            
            chat_data = chat_result.data if chat_result.data else []
            
            # 詳細なチE�Eタ刁E��
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
                # メチE��ージ長の刁E��
                message_lengths = [len(msg.get("message", "")) for msg in chat_data if msg.get("message")]
                detailed_metrics["average_message_length"] = sum(message_lengths) / len(message_lengths) if message_lengths else 0
                
                # 時間帯別の刁E��
                hour_counts = {}
                for msg in chat_data:
                    if msg.get("created_at"):
                        try:
                            dt = datetime.datetime.fromisoformat(msg["created_at"].replace('Z', '+00:00'))
                            hour = dt.hour
                            hour_counts[hour] = hour_counts.get(hour, 0) + 1
                        except:
                            continue
                
                # ピ�Eク時間帯を特宁E                if hour_counts:
                    sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
                    detailed_metrics["peak_usage_hours"] = sorted_hours[:3]
                
                # 繰り返し質問�E刁E��
                message_texts = [msg.get("message", "").lower() for msg in chat_data if msg.get("message")]
                unique_messages = set(message_texts)
                if message_texts:
                    detailed_metrics["repeat_question_rate"] = (len(message_texts) - len(unique_messages)) / len(message_texts) * 100
                
                # よくある失敗パターンの特宁E                failure_keywords = ["エラー", "わからなぁE, "できなぁE, "失敁E, "問顁E, "困っぁE, "ぁE��くいかなぁE, "動かなぁE]
                failure_count = 0
                for msg in message_texts:
                    if any(keyword in msg for keyword in failure_keywords):
                        failure_count += 1
                
                if message_texts:
                    detailed_metrics["resolution_rate"] = max(0, (len(message_texts) - failure_count) / len(message_texts) * 100)
            
        except Exception as e:
            print(f"詳細メトリクス取得エラー: {e}")
            detailed_metrics = {"error": "詳細メトリクスの取得に失敗しました"}
        
        # カチE��リーとセンチメント�E刁E��E��ら洞察を生�E
        categories = analysis_result.get("category_distribution", {})
        sentiments = analysis_result.get("sentiment_distribution", {})
        questions = analysis_result.get("common_questions", [])
        daily_usage = analysis_result.get("daily_usage", [])
        
        # Gemini APIで詳細な刁E��を実衁E        from modules.admin import model
        
        # GeminiモチE��が�E期化されてぁE��ぁE��合�Eエラーハンドリング
        if model is None:
            raise HTTPException(status_code=500, detail="GeminiモチE��が�E期化されてぁE��せん")
        
        # 短縮されたビジネス特化�Eロンプト
        analysis_prompt = f"""
        {prompt}
        
        # 刁E��チE�Eタ
        - 総会話数: {detailed_metrics.get('total_conversations', 0)}件
        - 繰り返し質問率: {detailed_metrics.get('repeat_question_rate', 0):.1f}%
        - ピ�Eク利用時間: {detailed_metrics.get('peak_usage_hours', [])}
        
        カチE��リ刁E��E {json.dumps(categories, ensure_ascii=False)}
        感情刁E��E {json.dumps(sentiments, ensure_ascii=False)}
        頻出質啁E {json.dumps(questions[:5], ensure_ascii=False)}
        
        # 以下�E6頁E��でビジネス刁E��を実施してください。各頁E��300斁E��以冁E��簡潔に、E        
        、E. 頻出トピチE��刁E��、E        最多質問パターンと業務課題を特定し、標準化の機会を示してください、E        
        、E. 効玁E��機会、E        繰り返し質問から�E動化可能な業務を特定し、ROIの高い改喁E��を提案してください、E        
        、E. フラストレーション要因、E        ネガチE��ブ感惁E�E原因と未解決問題�Eパターンを�E析し、優先改喁E��を�E示してください、E        
        、E. シスチE��改喁E��、E        機�E追加・改喁E�E具体提案とユーザーニ�Eズの優先頁E��を示してください、E        
        、E. 惁E��共有課題、E        部門間�E惁E��ギャチE�Eとドキュメント化が忁E��な領域を特定してください、E        
        、E. 実行計画、E        短期！E-3ヶ月）�E中期！E-6ヶ月）�E長期！Eヶ朁E1年�E��E改喁E��案を投賁E��効果と共に提示してください、E        """
        
        # Gemini APIによる詳細刁E��
        analysis_response = model.generate_content(analysis_prompt)
        detailed_analysis_text = analysis_response.text
        
        print(f"Gemini刁E��結果: {detailed_analysis_text[:500]}...")  # チE��チE��用
        
        # 詳細刁E��の結果をセクションごとに刁E��して整形
        import re
        
        # 吁E��クションのチE�Eタ
        detailed_analysis = {
            "detailed_topic_analysis": "",
            "efficiency_opportunities": "",
            "frustration_points": "",
            "improvement_suggestions": "",
            "communication_gaps": "",
            "specific_recommendations": ""
        }
        
        # より精寁E��セクション刁E��パターン
        sections = [
            (r"、E\..*?頻出トピチE��.*?、E, "detailed_topic_analysis"),
            (r"、E\..*?業務効玁E��.*?、E, "efficiency_opportunities"),
            (r"、E\..*?フラストレーション.*?、E, "frustration_points"),
            (r"、E\..*?製品E*?サービス.*?改喁E*?、E, "improvement_suggestions"),
            (r"、E\..*?コミュニケーション.*?、E, "communication_gaps"),
            (r"、E\..*?具体的.*?改喁E��桁E*?、E, "specific_recommendations")
        ]
        
        # セクション刁E��処琁E�E改喁E        text_lines = detailed_analysis_text.split("\n")
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
                    # 前�Eセクションの冁E��を保孁E                    if current_section and section_content:
                        content = "\n".join(section_content).strip()
                        if content:
                            detailed_analysis[current_section] = content
                    
                    # 新しいセクションを開姁E                    current_section = matched_section
                    section_content = []
            elif current_section:
                # 現在のセクションに冁E��を追加
                section_content.append(line)
        
        # 最後�Eセクションを�E琁E        if current_section and section_content:
            content = "\n".join(section_content).strip()
            if content:
                detailed_analysis[current_section] = content
        
        # セクション刁E��に失敗した場合�E対処
        filled_sections = sum(1 for value in detailed_analysis.values() if value.strip())
        if filled_sections < 3:
            # セクション刁E��に失敗した場合�E、�EチE��ストを刁E��して配币E            text_parts = detailed_analysis_text.split("\n\n")
            section_keys = list(detailed_analysis.keys())
            
            for i, part in enumerate(text_parts[:len(section_keys)]):
                if part.strip():
                    detailed_analysis[section_keys[i]] = part.strip()
            
            print("セクション刁E��に失敗したため、テキストを坁E��に刁E�Eしました")
        
        # チE��チE��惁E��
        print(f"刁E��結果セクション:")
        for key, value in detailed_analysis.items():
            char_count = len(value.strip()) if value else 0
            print(f"  {key}: {char_count} 斁E��E)
        
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
        print(f"詳細ビジネス刁E��エラー: {str(e)}")
        print(traceback.format_exc())
        
        # エラーの場合でも有用な刁E��結果を返す
        return {
            "detailed_analysis": {
                "detailed_topic_analysis": f"刁E��処琁E��にエラーが発生しました: {str(e)}\n\n利用可能な基本チE�Eタから推測される主要な質問パターンを確認し、手動での詳細刁E��を検討してください、E,
                "efficiency_opportunities": "シスチE��エラーにより自動�E析が完亁E��きませんでした。チャチE��履歴を手動で確認し、繰り返し質問や標準化可能な業務を特定することをお勧めします、E,
                "frustration_points": "エラーにより詳細な感情刁E��ができませんでした。ユーザーからの否定的なフィードバチE��めE��レームを個別に確認してください、E,
                "improvement_suggestions": "自動�E析�E利用できませんが、基本皁E��改喁E��して以下を検討してください�E�\n- FAQ の允E��\n- 回答精度の向上\n- ユーザーインターフェースの改喁E,
                "communication_gaps": "シスチE��制限により刁E��できませんでした。部門間での惁E��共有状況を手動で確認し、ドキュメント化が忁E��な領域を特定してください、E,
                "specific_recommendations": "技術的な問題により詳細な提案ができませんが、以下�E基本皁E��改喁E��優先してください�E�\n1. シスチE��の安定性向上\n2. エラー処琁E�E改善\n3. 刁E��機�Eの再設訁E
            },
            "analysis_metadata": {
                "error": str(e),
                "analysis_timestamp": datetime.datetime.now().isoformat(),
                "data_quality_score": 0
            }
        }

# 社員詳細惁E��を取得するエンド�EインチE@app.get("/chatbot/api/admin/employee-details/{employee_id}", response_model=List[ChatHistoryItem])
async def admin_get_employee_details(employee_id: str, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """特定�E社員の詳細なチャチE��履歴を取得すめE""
    # 特別な管琁E��E��Eueue@queuefood.co.jp�E��E場合�E全ユーザーのチE�Eタを取得できるようにする
    is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"] and current_user.get("is_special_admin", False)
    
    # ユーザーIDを渡して権限チェチE��を行う
    return await get_employee_details(employee_id, db, current_user["id"])

# 会社の全社員惁E��を取得するエンド�EインチE@app.get("/chatbot/api/admin/company-employees", response_model=List[dict])
async def admin_get_company_employees(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """会社の全社員惁E��を取得すめE""
    # 特別管琁E��E�Eみが�EチE�Eタにアクセス可能
    is_special_admin = current_user["email"] == "queue@queueu-tech.jp"
    
    if is_special_admin:
        # 特別管琁E��E�E場合�E全ユーザーのチE�Eタを取征E        result = await get_company_employees(current_user["id"], db, None)
        return result
    else:
        # 通常のユーザーの場合�E自刁E�E会社の社員のチE�Eタのみを取征E        # ユーザーの会社IDを取征E        user_result = select_data("users", filters={"id": current_user["id"]})
        user_row = user_result.data[0] if user_result.data else None
        company_id = user_row.get("company_id") if user_row else None
        
        if not company_id:
            raise HTTPException(status_code=400, detail="会社IDが見つかりません")
        
        result = await get_company_employees(current_user["id"], db, company_id)
        return result

# 社員利用状況を取得するエンド�EインチE@app.get("/chatbot/api/admin/employee-usage", response_model=EmployeeUsageResult)
async def admin_get_employee_usage(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """社員ごとの利用状況を取得すめE""
    # 特別管琁E��E�Eみが�EチE�Eタにアクセス可能
    is_special_admin = current_user["email"] == "queue@queueu-tech.jp" and current_user.get("is_special_admin", False)
    
    if is_special_admin:
        # 特別管琁E��E�E場合�E全ユーザーのチE�Eタを取征E        return await get_employee_usage(None, db, is_special_admin=True)
    else:
        # 通常のユーザーの場合�E自刁E�E会社の社員のチE�Eタのみを取征E        user_id = current_user["id"]
        return await get_employee_usage(user_id, db, is_special_admin=False)

# アチE�Eロードされたリソースを取得するエンド�EインチE@app.get("/chatbot/api/admin/resources", response_model=ResourcesResult)
async def admin_get_resources(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """アチE�Eロードされたリソース�E�ERL、PDF、Excel、TXT�E��E惁E��を取得すめE""
    # 特別管琁E��E�Eみが�EチE�Eタにアクセス可能
    is_special_admin = current_user["email"] == "queue@queueu-tech.jp" and current_user.get("is_special_admin", False)
    
    if is_special_admin:
        # 特別管琁E��E�E全てのリソースを表示
        return await get_uploaded_resources_by_company_id(None, db, uploaded_by=None)
    else:
        # 通常のユーザーは自刁E�E会社のリソースのみ表示
        company_id = current_user.get("company_id")
        if not company_id:
            raise HTTPException(status_code=400, detail="会社IDが見つかりません")
        
        print(f"会社ID {company_id} のリソースを取得しまぁE)
        return await get_uploaded_resources_by_company_id(company_id, db)

# リソースのアクチE��ブ状態を刁E��替えるエンド�EインチE@app.post("/chatbot/api/admin/resources/{resource_id:path}/toggle", response_model=ResourceToggleResponse)
async def admin_toggle_resource(resource_id: str, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """リソースのアクチE��ブ状態を刁E��替える"""
    # URLチE��ーチE    import urllib.parse
    decoded_id = urllib.parse.unquote(resource_id)
    print(f"トグルリクエスチE {resource_id} -> チE��ード征E {decoded_id}")
    return await toggle_resource_active_by_id(decoded_id, db)

# リソースを削除するエンド�EインチE@app.delete("/chatbot/api/admin/resources/{resource_id:path}", response_model=dict)
async def admin_delete_resource(resource_id: str, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """リソースを削除する"""
    # URLチE��ーチE    import urllib.parse
    decoded_id = urllib.parse.unquote(resource_id)
    print(f"削除リクエスチE {resource_id} -> チE��ード征E {decoded_id}")
    # return await delete_resource(decoded_id)
    return await remove_resource_by_id(decoded_id, db)

# 会社名を取得するエンド�EインチE@app.get("/chatbot/api/company-name", response_model=CompanyNameResponse)
async def api_get_company_name(current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """現在の会社名を取得すめE""
    return await get_company_name(current_user, db)

# 会社名を設定するエンド�EインチE@app.post("/chatbot/api/company-name", response_model=CompanyNameResponse)
async def api_set_company_name(request: CompanyNameRequest, current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """会社名を設定すめE""
    return await set_company_name(request, current_user, db)

# プラン変更エンド�EインチE@app.post("/chatbot/api/upgrade-plan", response_model=UpgradePlanResponse)
async def upgrade_plan(request: UpgradePlanRequest, current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """チE��版から有料�EランにアチE�Eグレードする（強化版�E�E""
    try:
        print(f"=== プランアチE�Eグレード開姁E===")
        print(f"ユーザー: {current_user['email']} ({current_user['name']})")
        print(f"ユーザーID: {current_user['id']}")
        print(f"要求�Eラン: {request.plan_id}")
        
        # プラン惁E��を定義
        plans = {
            "starter": {"name": "スタータープラン", "price": 2980, "questions_limit": -1, "uploads_limit": 10},
            "business": {"name": "ビジネスプラン", "price": 9800, "questions_limit": -1, "uploads_limit": 100},
            "enterprise": {"name": "エンタープライズプラン", "price": 29800, "questions_limit": -1, "uploads_limit": -1},
        }
        
        if request.plan_id not in plans:
            raise HTTPException(status_code=400, detail="無効なプランIDでぁE)
        
        plan = plans[request.plan_id]
        user_id = current_user["id"]
        
        print(f"選択されたプラン: {plan['name']} (価格: ¥{plan['price']})")
        
        # 現在の利用制限を取得（変更前�E状態を確認！E        from supabase_adapter import update_data, select_data
        current_limits_result = select_data("usage_limits", filters={"user_id": user_id})
        was_unlimited = False
        current_questions_used = 0
        current_uploads_used = 0
        
        if current_limits_result and current_limits_result.data:
            current_limits = current_limits_result.data[0]
            was_unlimited = bool(current_limits.get("is_unlimited", False))
            current_questions_used = current_limits.get("questions_used", 0)
            current_uploads_used = current_limits.get("document_uploads_used", 0)
            
            print(f"現在のスチE�Eタス: {'本番牁E if was_unlimited else 'チE��牁E}")
            print(f"現在の使用状況E 質啁E{current_questions_used}, アチE�EローチE{current_uploads_used}")
        
        if was_unlimited:
            print("⚠ ユーザーは既に本番版でぁE)
            return UpgradePlanResponse(
                success=True,
                message=f"既に本番版です、Eplan['name']}の機�Eをご利用ぁE��だけます、E,
                plan_id=request.plan_id,
                user_id=user_id,
                payment_url=None
            )
        
        # 実際の決済�E琁E��今回はモチE���E�E        # 本番環墁E��は Stripe めEPayPal などの決済サービスと連携
        print("決済�E琁E��...")
        payment_success = True  # モチE��として成功とする
        
        if payment_success:
            print("✁E決済�E劁E)
            
            # 新しい制限値を計箁E            new_questions_limit = plan["questions_limit"] if plan["questions_limit"] != -1 else 999999
            new_uploads_limit = plan["uploads_limit"] if plan["uploads_limit"] != -1 else 999999
            
            print(f"新しい制陁E 質啁E{new_questions_limit}, アチE�EローチE{new_uploads_limit}")
            
            # usage_limitsチE�Eブルを更新
            update_result = update_data("usage_limits", {
                "is_unlimited": True,
                "questions_limit": new_questions_limit,
                "questions_used": current_questions_used,  # 現在の使用数を保持
                "document_uploads_limit": new_uploads_limit,
                "document_uploads_used": current_uploads_used  # 現在の使用数を保持
            }, "user_id", user_id)
            
            if update_result:
                print("✁E利用制限更新完亁E)
            else:
                print("✁E利用制限更新失敁E)
                raise HTTPException(status_code=500, detail="利用制限�E更新に失敗しました")
            
            # ユーザーチE�Eブルにプラン惁E��を追加�E�Eoleを更新�E�E            user_update_result = update_data("users", {
                "role": "user"  # チE��版からuserプランに変更
            }, "id", user_id)
            
            if user_update_result:
                print("✁Eユーザーロール更新完亁E(demo -> user)")
            else:
                print("✁Eユーザーロール更新失敁E)
            
            # チE��版から本番版に刁E��替わった場合、作�Eしたアカウントも同期
            print("子アカウント�E同期を開姁E..")
            from modules.database import update_created_accounts_status
            updated_children = update_created_accounts_status(user_id, True, db)
            
            # 同じ会社の全ユーザーも同朁E            print("同じ会社のユーザーの同期を開姁E..")
            from modules.database import update_company_users_status
            updated_company_users = update_company_users_status(user_id, True, db)
            
            success_message = f"{plan['name']}へのアチE�Eグレードが完亁E��ました"
            if updated_children > 0 or updated_company_users > 0:
                success_message += f"�E�子アカウンチE{updated_children} 個、同じ会社のユーザー {updated_company_users} 個も同期�E�E
            
            print(f"=== プランアチE�Eグレード完亁E===")
            print(f"結果: {success_message}")
            
            return UpgradePlanResponse(
                success=True,
                message=success_message,
                plan_id=request.plan_id,
                user_id=user_id,
                payment_url=None
            )
        else:
            print("✁E決済失敁E)
            raise HTTPException(status_code=400, detail="決済�E琁E��失敗しました")
            
    except HTTPException as e:
        print(f"✁EHTTPエラー: {e.detail}")
        raise
    except Exception as e:
        print(f"✁EプランアチE�Eグレードエラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        logger.error(f"プランアチE�Eグレードエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"アチE�Eグレード�E琁E��にエラーが発生しました: {str(e)}")

@app.get("/chatbot/api/subscription-info", response_model=SubscriptionInfo)
async def get_subscription_info(current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """現在のユーザーのサブスクリプション惁E��を取得すめE""
    try:
        from supabase_adapter import select_data
        
        # ユーザーの利用制限情報を取征E        limits_result = select_data("usage_limits", filters={"user_id": current_user["id"]})
        
        if not limits_result.data:
            raise HTTPException(status_code=404, detail="サブスクリプション惁E��が見つかりません")
        
        limits = limits_result.data[0]
        is_unlimited = limits.get("is_unlimited", False)
        
        if is_unlimited:
            # プランを判定！Euestions_limitやuploads_limitから推測�E�E            uploads_limit = limits.get("document_uploads_limit", 2)
            if uploads_limit >= 999999:
                plan_id = "enterprise"
                plan_name = "エンタープライズプラン"
            elif uploads_limit >= 100:
                plan_id = "business"
                plan_name = "ビジネスプラン"
            else:
                plan_id = "starter"
                plan_name = "スタータープラン"
            
            return SubscriptionInfo(
                plan_id=plan_id,
                plan_name=plan_name,
                status="active",
                start_date=current_user.get("created_at", ""),
                price=2980 if plan_id == "starter" else 9800 if plan_id == "business" else 29800
            )
        else:
            return SubscriptionInfo(
                plan_id="demo",
                plan_name="チE��牁E,
                status="trial",
                start_date=current_user.get("created_at", ""),
                price=0
            )
            
    except Exception as e:
        logger.error(f"サブスクリプション惁E��取得エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"サブスクリプション惁E��の取得中にエラーが発生しました: {str(e)}")

# 申請フォーム送信エンド�EインチE@app.post("/chatbot/api/submit-application")
async def submit_application(request: Request):
    """本番版移行申請を受け付けめE""
    try:
        body = await request.json()
        print(f"申請フォーム受信: {body}")
        
        # 申請データを�E琁E        application_data = {
            "company_name": body.get("companyName"),
            "contact_name": body.get("contactName"),
            "email": body.get("email"),
            "phone": body.get("phone"),
            "expected_users": body.get("expectedUsers"),
            "current_usage": body.get("currentUsage"),
            "message": body.get("message"),
            "application_type": body.get("applicationType", "production-upgrade")
        }
        
        # チE�Eタベ�Eスに申請データを保孁E        from modules.database import save_application
        application_id = save_application(application_data)
        
        if application_id:
            print(f"✁E申請受付完亁E ID={application_id}")
            print(f"  会社吁E {application_data['company_name']}")
            print(f"  拁E��老E {application_data['contact_name']}")
            print(f"  メール: {application_data['email']}")
            print(f"  電話: {application_data['phone']}")
            print(f"  予想利用老E {application_data['expected_users']}")
            print(f"  現在の利用状況E {application_data['current_usage']}")
            print(f"  メチE��ージ: {application_data['message']}")
            
            # TODO: 今後�E機�E追加
            # 1. 営業拁E��老E��メール通知
            # 2. 申請老E��受付完亁E��ールを送信
            # 3. Slack通知などの外部連携
            
            return {
                "success": True, 
                "message": "申請を受け付けました。営業拁E��老E��りご連絡ぁE��します、E,
                "application_id": application_id
            }
        else:
            raise HTTPException(status_code=500, detail="申請データの保存に失敗しました")
        
    except Exception as e:
        print(f"申請フォーム処琁E��ラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="申請�E処琁E��にエラーが発生しました")

# 静的ファイルのマウンチE# フロントエンド�Eビルドディレクトリを指宁Efrontend_build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# 静的ファイルを提供するため�Eルートを追加
@app.get("/", include_in_schema=False)
async def read_root():
    index_path = os.path.join(frontend_build_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": f"Welcome to {DEFAULT_COMPANY_NAME} Chatbot API"}



# 静的ファイルを�EウンチEif os.path.exists(os.path.join(frontend_build_dir, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_build_dir, "assets")), name="assets")

# プラン履歴取得エンド�Eイント！Eatch_allより前に配置�E�E@app.get("/chatbot/api/plan-history", response_model=dict)
async def get_plan_history_endpoint(current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """プラン履歴を人単位でグループ化して取得すめE""
    try:
        print(f"プラン履歴取得要汁E- ユーザー: {current_user['email']} (ロール: {current_user['role']})")
        
        from modules.database import get_plan_history
        
        # 管琁E��E�E特別管琁E��E�E全てのプラン履歴を、一般ユーザーは自刁E�E履歴のみを取征E        if current_user["role"] in ["admin"] or current_user["email"] in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"]:
            # 管琁E��E��た�E特別管琁E��E�E全履歴を取征E            user_histories = get_plan_history(db=db)
        else:
            # 一般ユーザー�E�Eserロール含む�E��E自刁E�E履歴のみを取征E            user_histories = get_plan_history(user_id=current_user["id"], db=db)
        
        # 追加の統計情報を計箁E        total_users = len(user_histories)
        total_changes = sum(user.get("total_changes", 0) for user in user_histories)
        
        # プラン別の統訁E        plan_stats = {}
        for user in user_histories:
            current_plan = user.get("current_plan", "不�E")
            if current_plan in plan_stats:
                plan_stats[current_plan] += 1
            else:
                plan_stats[current_plan] = 1
        
        # queue@queueu-tech.jp用の追加分析
        additional_analytics = {}
        if current_user["email"] == "queue@queueu-tech.jp":
            from modules.analytics import get_usage_analytics
            additional_analytics = get_usage_analytics(db)
        
        return {
            "success": True,
            "data": {
                "users": user_histories,
                "statistics": {
                    "total_users": total_users,
                    "total_changes": total_changes,
                    "plan_distribution": plan_stats
                },
                "analytics": additional_analytics
            },
            "count": total_users,
            "message": f"{total_users}人のプラン履歴を人単位でグループ化して表示してぁE��ぁE
        }
        
    except Exception as e:
        print(f"プラン履歴取得エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"プラン履歴の取得に失敗しました: {str(e)}"
        )

# チE��ト用チE��チE��エンド�Eイント（認証なし！E@app.get("/chatbot/api/test-simple")
async def simple_test():
    """認証なし�E簡単なチE��チE""
    return {"message": "Backend is working!", "timestamp": datetime.datetime.now().isoformat()}

# チE��ト用チE��チE��エンド�EインチE@app.get("/chatbot/api/admin/csv-test")
async def csv_test_endpoint():
    """CSVエンド�Eイント�EチE��チE""
    return {"message": "CSV endpoint is working", "timestamp": datetime.datetime.now().isoformat()}

# チャチE��履歴をCSV形式でダウンロードするエンド�Eイント！Eatch_allより前に配置�E�E@app.get("/chatbot/api/admin/chat-history/csv")
async def download_chat_history_csv(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """チャチE��履歴をCSV形式でダウンロードすめE""
    try:
        print(f"CSVダウンロード開姁E- ユーザー: {current_user['email']}")
        
        # 権限チェチE���E�Eser、employeeロールも許可�E�E        is_admin = current_user["role"] == "admin"
        is_user = current_user["role"] == "user"
        is_employee = current_user["role"] == "employee"
        is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"] and current_user.get("is_special_admin", False)
        
        # チャチE��履歴を直接Supabaseから取征E        try:
            if is_special_admin or is_admin:
                # 管琁E��E��た�E特別管琁E��E�E場合�E全ユーザーのチE�Eタを取征E                print("管琁E��E��して全ユーザーのチャチE��履歴を取征E)
                from supabase_adapter import select_data
                result = select_data("chat_history", columns="*")
                chat_history = result.data if result and result.data else []
            elif is_user or is_employee:
                # userまた�Eemployeeロールの場合�E自刁E�E会社のチE�Eタのみを取征E                print(f"{current_user['role']}ロールとして自刁E�E会社のチャチE��履歴を取征E)
                from supabase_adapter import select_data
                # まずユーザーの会社IDを取征E                user_result = select_data("users", filters={"id": current_user["id"]})
                if user_result and user_result.data:
                    user_data = user_result.data[0]
                    company_name = user_data.get("company_name")
                    if company_name:
                        # 同じ会社のユーザーIDリストを取征E                        company_users_result = select_data("users", filters={"company_name": company_name})
                        if company_users_result and company_users_result.data:
                            company_user_ids = [user["id"] for user in company_users_result.data]
                            # 会社のユーザーのチャチE��履歴を取征E                            result = select_data("chat_history", filters={"employee_id": f"in.({','.join(company_user_ids)})"})
                            chat_history = result.data if result and result.data else []
                        else:
                            chat_history = []
                    else:
                        # 会社名がなぁE��合�E自刁E�EチE�Eタのみ
                        result = select_data("chat_history", filters={"employee_id": current_user["id"]})
                        chat_history = result.data if result and result.data else []
                else:
                    chat_history = []
            else:
                # そ�E他�Eユーザーの場合�E自刁E�EチE�Eタのみを取征E                user_id = current_user["id"]
                print(f"通常ユーザーとして個人のチャチE��履歴を取征E {user_id}")
                from supabase_adapter import select_data
                result = select_data("chat_history", columns="*", filters={"employee_id": user_id})
                chat_history = result.data if result and result.data else []
        except Exception as e:
            print(f"チャチE��履歴取得エラー: {e}")
            chat_history = []
        
        print(f"取得したチャチE��履歴数: {len(chat_history)}")
        
        # CSV形式に変換
        csv_data = io.StringIO()
        csv_writer = csv.writer(csv_data)
        
        # ヘッダー行を書き込み
        csv_writer.writerow([
            "ID",
            "日晁E,
            "ユーザーの質啁E,
            "ボット�E回筁E,
            "カチE��リ",
            "感情",
            "社員ID",
            "社員吁E,
            "参�E斁E��",
            "ペ�Eジ番号"
        ])
        
        # チE�Eタ行を書き込み
        for chat in chat_history:
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
        
        # CSV斁E���Eを取征E        csv_content = csv_data.getvalue()
        csv_data.close()
        
        # UTF-8 BOM付きでエンコード！Excelでの斁E��化け防止�E�E        csv_bytes = '\ufeff' + csv_content
        
        # ファイル名に日時を含める
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_history_{timestamp}.csv"
        
        print(f"CSVファイル生�E完亁E {filename}")
        
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

@app.post("/chatbot/api/admin/update-user-status/{user_id}", response_model=dict)
async def admin_update_user_status(user_id: str, request: dict, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """管琁E��E��よるユーザースチE�Eタス変更�E�Edminのみ実行可能�E�E""
    # adminロールまた�E特別な管琁E��E�Eみが実行可能
    is_admin = current_user["role"] == "admin"
    is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"] and current_user.get("is_special_admin", False)
    
    print(f"=== ユーザースチE�Eタス変更権限チェチE�� ===")
    print(f"操作老E {current_user['email']} (管琁E��E {is_admin}, 特別管琁E��E {is_special_admin})")
    
    # 権限チェチE�� - adminまた�E特別管琁E��E�Eみ
    if not (is_admin or is_special_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="こ�E操作には管琁E��E��限が忁E��です。一般ユーザーは自刁E�Eプラン変更を行うことはできません、E
        )
    
    try:
        print(f"=== ユーザースチE�Eタス変更開姁E===")
        print(f"対象ユーザーID: {user_id}")
        
        new_is_unlimited = bool(request.get("is_unlimited", False))
        print(f"新しいスチE�Eタス: {'本番牁E if new_is_unlimited else 'チE��牁E}")
        
        # ユーザーの存在確誁E        user_result = select_data("users", filters={"id": user_id})
        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="持E��されたユーザーが見つかりません"
            )
        
        user = user_result.data[0]
        print(f"対象ユーザー: {user['email']} ({user['name']}) - ロール: {user['role']}")
        
        # 管琁E��E��ールの場合�E警呁E        if user['role'] == 'admin':
            print(f"警呁E 管琁E��E��ール ({user['email']}) のスチE�Eタス変更")
        
        # 現在の利用制限を取征E        current_limits_result = select_data("usage_limits", filters={"user_id": user_id})
        if not current_limits_result or not current_limits_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーの利用制限情報が見つかりません"
            )
        
        current_limits = current_limits_result.data[0]
        was_unlimited = bool(current_limits.get("is_unlimited", False))
        current_questions_used = current_limits.get("questions_used", 0)
        current_uploads_used = current_limits.get("document_uploads_used", 0)
        
        print(f"現在のスチE�Eタス: {'本番牁E if was_unlimited else 'チE��牁E}")
        print(f"現在の使用状況E 質啁E{current_questions_used}, アチE�EローチE{current_uploads_used}")
        
        # スチE�Eタスに変更がなぁE��合�E何もしなぁE        if was_unlimited == new_is_unlimited:
            print("スチE�Eタスに変更がなぁE��め�E琁E��スキチE�EしまぁE)
            return {
                "message": f"ユーザー {user['email']} のスチE�Eタスは既に{'本番牁E if new_is_unlimited else 'チE��牁E}でぁE,
                "user_id": user_id,
                "updated_children": 0,
                "updated_company_users": 0
            }
        
        # 新しい制限値を計箁E        if new_is_unlimited:
            new_questions_limit = 999999
            new_uploads_limit = 999999
        else:
            new_questions_limit = 10
            new_uploads_limit = 2
            
            # チE��版に変更する場合、使用済み数が新しい制限を趁E��る場合�E調整
            if current_questions_used > new_questions_limit:
                print(f"質問使用数めE{current_questions_used} から {new_questions_limit} に調整")
                current_questions_used = new_questions_limit
            if current_uploads_used > new_uploads_limit:
                print(f"アチE�Eロード使用数めE{current_uploads_used} から {new_uploads_limit} に調整")
                current_uploads_used = new_uploads_limit
        
        print(f"新しい制陁E 質啁E{new_questions_limit} (使用済み: {current_questions_used}), アチE�EローチE{new_uploads_limit} (使用済み: {current_uploads_used})")
        
        # 利用制限を更新
        update_result = update_data("usage_limits", {
            "is_unlimited": new_is_unlimited,
            "questions_limit": new_questions_limit,
            "questions_used": current_questions_used,
            "document_uploads_limit": new_uploads_limit,
            "document_uploads_used": current_uploads_used
        }, "user_id", user_id)
        
        if update_result:
            print("✁E本人のスチE�Eタス更新完亁E)
        else:
            print("✁E本人のスチE�Eタス更新失敁E)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="利用制限�E更新に失敗しました"
            )
        
        # プラン履歴を記録
        print("プラン履歴を記録しまぁE..")
        from modules.database import record_plan_change
        from_plan = "unlimited" if was_unlimited else "demo"
        to_plan = "unlimited" if new_is_unlimited else "demo"
        record_plan_change(user_id, from_plan, to_plan, db)
        
        # 作�Eしたアカウントも同期
        print("子アカウント�E同期を開始しまぁE..")
        from modules.database import update_created_accounts_status
        updated_children = update_created_accounts_status(user_id, new_is_unlimited, db)
        
        # 同じ会社の全ユーザーも同朁E        print("同じ会社のユーザーの同期を開姁E..")
        from modules.database import update_company_users_status
        updated_company_users = update_company_users_status(user_id, new_is_unlimited, db)
        
        result_message = f"ユーザー {user['email']} のスチE�Eタスを{'本番牁E if new_is_unlimited else 'チE��牁E}に変更しました"
        if updated_children > 0 or updated_company_users > 0:
            result_message += f"�E�子アカウンチE{updated_children} 個、同じ会社のユーザー {updated_company_users} 個も同期�E�E
        
        print(f"=== ユーザースチE�Eタス変更完亁E===")
        print(f"結果: {result_message}")
        
        return {
            "message": result_message,
            "user_id": user_id,
            "updated_children": updated_children,
            "updated_company_users": updated_company_users,
            "details": {
                "user_email": user['email'],
                "user_name": user['name'],
                "old_status": "本番牁E if was_unlimited else "チE��牁E,
                "new_status": "本番牁E if new_is_unlimited else "チE��牁E,
                "new_questions_limit": new_questions_limit,
                "new_uploads_limit": new_uploads_limit
            }
        }
        
    except HTTPException as e:
        print(f"✁EHTTPエラー: {e.detail}")
        raise
    except Exception as e:
        print(f"✁EユーザースチE�Eタス変更エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"スチE�Eタス変更中にエラーが発生しました: {str(e)}"
        )

# YouTube接続テスト用エンド�EインチE@app.get("/chatbot/api/test-youtube")
async def test_youtube_connection():
    """YouTube接続をチE��トすめE""
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
            "message": f"チE��ト実行エラー: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/chatbot/api/admin/companies", response_model=List[dict])
async def admin_get_companies(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """会社一覧を取得！Edminのみ�E�E""
    # 特別な管琁E��E�Eみがアクセス可能
    if current_user["email"] not in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"] or not current_user.get("is_special_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="こ�E操作には特別な管琁E��E��限が忁E��でぁE
        )
    
    from modules.database import get_all_companies
    companies = get_all_companies(db)
    return companies

@app.post("/chatbot/api/admin/fix-company-status/{company_id}", response_model=dict)
async def admin_fix_company_status(company_id: str, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """会社冁E�EユーザースチE�Eタス不整合を修正する"""
    # adminロールまた�E特別な管琁E��E�Eみが実行可能
    is_admin = current_user["role"] == "admin"
    is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"] and current_user.get("is_special_admin", False)
    
    if not (is_admin or is_special_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="こ�E操作には管琁E��E��限が忁E��でぁE
        )
    
    try:
        from modules.database import fix_company_status_inconsistency
        fixed_count = fix_company_status_inconsistency(company_id, db)
        
        return {
            "message": f"会社ID {company_id} のスチE�Eタス不整合修正が完亁E��ました",
            "fixed_count": fixed_count,
            "company_id": company_id
        }
        
    except Exception as e:
        print(f"会社スチE�Eタス修正エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"スチE�Eタス修正中にエラーが発生しました: {str(e)}"
        )

@app.post("/chatbot/api/admin/ensure-database-integrity", response_model=dict)
async def admin_ensure_database_integrity(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """チE�Eタベ�Eス整合性をチェチE��して修正する"""
    # adminロールまた�E特別な管琁E��E�Eみが実行可能
    is_admin = current_user["role"] == "admin"
    is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"] and current_user.get("is_special_admin", False)
    
    if not (is_admin or is_special_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="こ�E操作には管琁E��E��限が忁E��でぁE
        )
    
    try:
        from modules.database import ensure_usage_limits_integrity
        fixed_count = ensure_usage_limits_integrity(db)
        
        return {
            "message": f"チE�Eタベ�Eス整合性チェチE��が完亁E��ました",
            "fixed_count": fixed_count,
            "details": f"{fixed_count}個�Eusage_limitsレコードを作�Eしました" if fixed_count > 0 else "修正が忁E��なレコード�Eありませんでした"
        }
        
    except Exception as e:
        print(f"チE�Eタベ�Eス整合性チェチE��エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"チE�Eタベ�Eス整合性チェチE��中にエラーが発生しました: {str(e)}"
        )




# 申請管琁E��ンド�Eイント（管琁E��E���E�E@app.get("/chatbot/api/admin/applications")
async def admin_get_applications(status: str = None, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """管琁E��E��申請一覧を取得すめE""
    try:
        print(f"申請一覧取得要汁E- ユーザー: {current_user['email']} (ロール: {current_user['role']})")
        
        # 管琁E��E��限チェチE��
        is_admin = current_user["role"] == "admin"
        is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"] and current_user.get("is_special_admin", False)
        
        if not (is_admin or is_special_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="こ�E操作には管琁E��E��限が忁E��でぁE
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
    """管琁E��E��申請�EスチE�Eタスを更新する"""
    try:
        print(f"申請スチE�Eタス更新要汁E- ユーザー: {current_user['email']}")
        print(f"申請ID: {application_id}")
        print(f"リクエスチE {request}")
        
        # 管琁E��E��限チェチE��
        is_admin = current_user["role"] == "admin"
        is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queueu-tech.jp"] and current_user.get("is_special_admin", False)
        
        if not (is_admin or is_special_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="こ�E操作には管琁E��E��限が忁E��でぁE
            )
        
        new_status = request.get("status")
        notes = request.get("notes", "")
        
        if not new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="スチE�Eタスが指定されてぁE��せん"
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
                "message": f"申請スチE�EタスめE{new_status}'に更新しました"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="申請スチE�Eタスの更新に失敗しました"
            )
        
    except Exception as e:
        print(f"申請スチE�Eタス更新エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"申請スチE�Eタスの更新に失敗しました: {str(e)}"
        )

# 会社全体�Eト�Eクン使用量と料��惁E��を取得するエンド�EインチE@app.get("/chatbot/api/company-token-usage", response_model=dict)
async def get_company_token_usage(current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """会社全体�Eト�Eクン使用量と料��惁E��を取得すめE""
    try:
        print(f"company-token-usageエンド�Eイントが呼び出されました - ユーザー: {current_user['email']}")
        
        # ユーザーの会社IDを取征E        from supabase_adapter import select_data
        user_result = select_data("users", columns="company_id", filters={"id": current_user["id"]})
        company_id = None
        if user_result and user_result.data:
            company_id = user_result.data[0].get("company_id")
        
        # 実際の会社ユーザー数を取征E        company_users_count = 1  # チE��ォルト（�E刁E��け！E        company_name = "あなた�E会社"
        
        if company_id:
            # 同じ会社のユーザー数をカウンチE            company_users_result = select_data("users", columns="id, name", filters={"company_id": company_id})
            if company_users_result and company_users_result.data:
                company_users_count = len(company_users_result.data)
                print(f"✁E会社ID {company_id} のユーザー数: {company_users_count}人")
            
            # 会社名を取征E            company_result = select_data("companies", columns="name", filters={"id": company_id})
            if company_result and company_result.data:
                company_name = company_result.data[0].get("name", "あなた�E会社")
        
        # 実際のト�Eクン使用量を取征E        total_tokens_used = 0
        total_input_tokens = 0
        total_output_tokens = 0
        total_conversations = 0
        total_cost_usd = 0.0
        
        try:
            if company_id:
                # TokenUsageTrackerを使用して実際の使用量を取征E                from modules.token_counter import TokenUsageTracker
                import datetime
                
                tracker = TokenUsageTracker(db)
                
                # 現在の月を取征E                current_month = datetime.datetime.now().strftime('%Y-%m')
                print(f"🔍 現在の朁E {current_month}")
                
                usage_data = tracker.get_company_monthly_usage(company_id, current_month)
                
                if usage_data and usage_data.get("total_tokens", 0) > 0:
                    total_tokens_used = usage_data.get("total_tokens", 0)
                    total_input_tokens = usage_data.get("total_input_tokens", 0) 
                    total_output_tokens = usage_data.get("total_output_tokens", 0)
                    total_conversations = usage_data.get("conversation_count", 0)
                    total_cost_usd = usage_data.get("total_cost_usd", 0.0)
                    print(f"✁E会社ID {company_id} の実際のト�Eクン使用釁E {total_tokens_used:,} tokens")
                else:
                    print("⚠�E�E今月のト�Eクン使用量データなぁE- 全期間で確認しまぁE)
                    # 全期間のチE�Eタを取征E                    usage_data_all = tracker.get_company_monthly_usage(company_id, "ALL")
                    if usage_data_all and usage_data_all.get("total_tokens", 0) > 0:
                        total_tokens_used = usage_data_all.get("total_tokens", 0)
                        total_input_tokens = usage_data_all.get("total_input_tokens", 0) 
                        total_output_tokens = usage_data_all.get("total_output_tokens", 0)
                        total_conversations = usage_data_all.get("conversation_count", 0)
                        total_cost_usd = usage_data_all.get("total_cost_usd", 0.0)
                        print(f"✁E全期間での会社ID {company_id} のト�Eクン使用釁E {total_tokens_used:,} tokens")
                    else:
                        print("⚠�E�E全期間でもトークン使用量データなぁE)
            else:
                print("⚠�E�E会社IDなぁE- 個人ユーザーのト�Eクン使用量�E現在未対忁E)
        except Exception as e:
            print(f"⚠�E�Eト�Eクン使用量取得エラー: {e} - モチE��チE�Eタを使用しまぁE)
        
        # 基本設宁E        basic_plan_limit = 25000000  # 25M tokens
        usage_percentage = (total_tokens_used / basic_plan_limit * 100) if basic_plan_limit > 0 else 0
        remaining_tokens = max(0, basic_plan_limit - total_tokens_used)
        
        # 警告レベル計箁E        warning_level = "safe"
        if usage_percentage >= 95:
            warning_level = "critical"
        elif usage_percentage >= 80:
            warning_level = "warning"
        
        # 日本冁E��金計箁E        from modules.token_counter import calculate_japanese_pricing
        pricing_info = calculate_japanese_pricing(total_tokens_used)
        
        # 実際のチE�Eタを返す
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
        
        print(f"実際のチE�Eタを返却しまぁE company_users_count={company_users_count}, total_tokens={total_tokens_used:,}, company_name={company_name}")
        return data
        
    except Exception as e:
        print(f"会社ト�Eクン使用量取得エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"ト�Eクン使用量�E取得中にエラーが発生しました: {str(e)}")

# 料��シミュレーションエンド�EインチE@app.post("/chatbot/api/simulate-cost", response_model=dict)
async def simulate_token_cost(request: dict, current_user = Depends(get_current_user)):
    """持E��されたト�Eクン数での料��をシミュレーション"""
    try:
        print(f"simulate-costエンド�Eイントが呼び出されました - ユーザー: {current_user['email']}")
        
        tokens = request.get("tokens", 0)
        print(f"シミュレーション対象ト�Eクン数: {tokens}")
        
        if not isinstance(tokens, (int, float)) or tokens < 0:
            raise HTTPException(status_code=400, detail="有効なト�Eクン数を指定してください")
        
        # 簡易料金計算（モチE���E�E        basic_plan_cost = 150000  # ¥150,000
        tier1_cost = 0
        tier2_cost = 0
        tier3_cost = 0
        
        # 基本プラン制限を趁E��た�Eの計箁E        if tokens > 25000000:  # 25M tokens
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
        print(f"料��シミュレーションエラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"料��シミュレーション中にエラーが発生しました: {str(e)}")

# Google Drive連携エンド�EインチE@app.post("/chatbot/api/upload-from-drive")
async def upload_from_google_drive(
    file_id: str = Form(...),
    access_token: str = Form(...),
    file_name: str = Form(...),
    mime_type: str = Form(...),
    current_user = Depends(get_current_user),
    db: SupabaseConnection = Depends(get_db)
):
    """Google DriveからファイルをアチE�EローチE""
    try:
        # Google Driveハンドラー初期匁E        drive_handler = GoogleDriveHandler()
        
        print(f"Google DriveファイルアチE�Eロード開姁E {file_name} (ID: {file_id})")
        
        # サポ�EトされてぁE��ファイル形式かチェチE��
        if not drive_handler.is_supported_file(mime_type):
            raise HTTPException(
                status_code=400, 
                detail=f"サポ�EトされてぁE��ぁE��ァイル形式でぁE {mime_type}"
            )
        
        # ファイルメタチE�Eタ取征E        file_metadata = await drive_handler.get_file_metadata(file_id, access_token)
        if not file_metadata:
            raise HTTPException(status_code=400, detail="ファイルが見つかりません")
        
        # ファイルサイズチェチE���E�E0MB制限！E        file_size = int(file_metadata.get('size', 0))
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400, 
                detail=f"ファイルサイズが大きすぎまぁE({file_size / (1024*1024):.1f}MB)、E0MB以下�Eファイルをご利用ください、E
            )
        
        # ファイルダウンローチE        print(f"Google Driveからファイルダウンロード中: {file_name}")
        file_content = await drive_handler.download_file(file_id, access_token, mime_type)
        if not file_content:
            raise HTTPException(status_code=400, detail="ファイルのダウンロードに失敗しました")
        
        # 一時ファイル作�E
        print(f"一時ファイル作�E中: {file_name}")
        temp_file_path = await drive_handler.create_temp_file(file_content, file_name)
        
        try:
            # UploadFileオブジェクトを模倣するクラス
            class MockUploadFile:
                def __init__(self, filename: str, content: bytes):
                    self.filename = filename
                    self.content = content
                
                async def read(self):
                    return self.content
            
            # Google DocsやSheetsの場合、E��刁E��拡張子に変更
            processed_filename = file_name
            if mime_type == 'application/vnd.google-apps.document':
                # Google DocはPDFに変換される�Eで.pdf拡張子にする
                base_name = os.path.splitext(file_name)[0]
                processed_filename = f"{base_name}.pdf"
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                # Google SheetはExcelに変換される�Eで.xlsx拡張子にする
                base_name = os.path.splitext(file_name)[0]
                processed_filename = f"{base_name}.xlsx"
            
            # 既存�Eprocess_file関数を使用
            mock_file = MockUploadFile(processed_filename, file_content)
            result = await process_file(
                mock_file,
                current_user["id"],
                None,  # company_id
                db
            )
            
            print(f"Google Driveファイル処琁E��亁E {file_name}")
            return result
            
        finally:
            # 一時ファイル削除
            drive_handler.cleanup_temp_file(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Google DriveアチE�Eロードエラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Google Drive処琁E��ラー: {str(e)}")

@app.get("/chatbot/api/drive/files")
async def list_drive_files(
    access_token: str,
    folder_id: str = 'root',
    search_query: str = None,
    current_user = Depends(get_current_user)
):
    """Google Driveファイル一覧取征E""
    try:
        print(f"Google Driveファイル一覧取征E フォルダID={folder_id}")
        
        drive_handler = GoogleDriveHandler()
        files = await drive_handler.list_files(access_token, folder_id, search_query)
        
        # サポ�EトされてぁE��ファイルのみフィルター
        supported_files = [
            file for file in files 
            if file.get('mimeType') == 'application/vnd.google-apps.folder' or 
               drive_handler.is_supported_file(file.get('mimeType', ''))
        ]
        
        print(f"Google Driveファイル一覧取得完亁E {len(supported_files)}件")
        return {"files": supported_files}
        
    except Exception as e:
        print(f"Google Driveファイル一覧取得エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"ファイル一覧取得エラー: {str(e)}")

# そ�E他�Eルートパスをindex.htmlにリダイレクト！EPAのルーチE��ング用�E�E# 注意：これを最後に登録することで、他�EAPIエンド�Eイントを優先すめE@app.get("/{full_path:path}", include_in_schema=False)
async def catch_all(full_path: str):
    print(f"catch_all handler called with path: {full_path}")
    
    # APIエンド�Eイント�EスキチE�E�E�Eapi で始まるパスまた�E chatbot/api で始まるパスはAPIエンド�Eイントとして処琁E��E    if full_path.startswith("api/") or full_path.startswith("chatbot/api/"):
        # APIエンド�Eイント�E場合�E404を返す
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # SPAルーチE��ング用にindex.htmlを返す
    index_path = os.path.join(frontend_build_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Not Found")

# アプリケーションの実衁Eif __name__ == "__main__":
    import uvicorn
    from modules.config import get_port
    port = get_port()
    uvicorn.run(app, host="0.0.0.0", port=port, timeout_keep_alive=300)
