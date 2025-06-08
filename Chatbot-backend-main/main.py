"""
メインアプリケーションファイル
FastAPIアプリケーションの設定とルーティングを行います
main.py
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
from modules.config import setup_logging, setup_gemini
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
            content={"detail": "データ型エラーが発生しました。管理者に連絡してください。"}
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
# すべてのオリジンを許可する
origins = [
    "http://localhost:3000",
    "http://localhost:3025",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3025",
    "http://127.0.0.1:5173",
    "https://chatbot-frontend-nine-eta.vercel.app",
    "http://13.211.77.231",
    "https://13.211.77.231",
    "*"
]

# CORSミドルウェアを最初に追加して優先度を上げる
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # すべてのオリジンを許可
    allow_credentials=True,  # クレデンシャルを含むリクエストを許可
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # 明示的にHTTPメソッドを指定
    allow_headers=["*"],  # すべてのヘッダーを許可
    expose_headers=["*"],  # レスポンスヘッダーを公開
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

# CORSミドルウェアの設定
# 統合環境では、すべてのオリジンを許可する
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["https://chatbot-frontend-nine-eta.vercel.app"],  # すべてのオリジンを許可
#     allow_credentials=True,  # クレデンシャルを含むリクエストを許可
#     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#     allow_headers=["*"],
# )

# アプリケーション起動時にデータベースを初期化
init_db()

# データベース整合性をチェック
try:
    from modules.database import ensure_usage_limits_integrity, get_db
    print("起動時データベース整合性チェックを実行中...")
    db_connection = SupabaseConnection()
    fixed_count = ensure_usage_limits_integrity(db_connection)
    if fixed_count > 0:
        print(f"起動時整合性チェック完了: {fixed_count}個のusage_limitsレコードを修正しました")
    else:
        print("起動時整合性チェック完了: 修正が必要なレコードはありませんでした")
    db_connection.close()
except Exception as e:
    print(f"起動時整合性チェックでエラーが発生しましたが、アプリケーションは継続します: {str(e)}")

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
            detail="無効なメールアドレスまたはパスワードです",
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
        
        # 管理者権限チェックは不要（デモ版では誰でも登録可能）
        return register_new_user(user_data.email, user_data.password, user_data.name, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"登録に失敗しました: {str(e)}"
        )

@app.post("/chatbot/api/admin/register-user", response_model=UserResponse)
async def admin_register_user(user_data: AdminUserCreate, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
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
        
        # まず、メールアドレスが既に存在するかチェック
        from supabase_adapter import select_data
        existing_user_result = select_data("users", filters={"email": user_data.email})
        
        if existing_user_result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="このメールアドレスは既に登録されています"
            )
        
        # 特別な管理者（queue@queuefood.co.jp）またはadminロールの場合はuserロールのみ作成可能
        is_special_admin = current_user["email"] == "queue@queuefood.co.jp" and current_user.get("is_special_admin", False)
        is_admin = current_user["role"] == "admin"
        
        if is_special_admin or is_admin:
            print(f"管理者権限でユーザー作成: 特別管理者={is_special_admin}, admin={is_admin}")
            
            # adminロールは常にuserロールのアカウントのみ作成可能
            role = "user"
            
            # 会社IDの指定
            company_id = None
            if hasattr(user_data, "company_id") and user_data.company_id:
                # 指定された会社IDが存在するかチェック
                company_result = select_data("companies", filters={"id": user_data.company_id})
                if not company_result.data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="指定された会社IDが存在しません"
                    )
                company_id = user_data.company_id
                print(f"管理者により会社ID {company_id} が指定されました")
            else:
                # 会社IDが指定されていない場合、作成者の会社IDを使用
                company_id = current_user.get("company_id")
                if company_id:
                    print(f"作成者の会社ID {company_id} を使用します")
            
            # create_user関数を直接呼び出す（管理者が作成するアカウントは作成者のステータスを継承）
            user_id = create_user(
                email=user_data.email,
                password=user_data.password,
                name=name,
                role=role,
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
        else:
            # userロールの場合のみ社員アカウント作成可能、employeeロールは作成権限なし
            if current_user["role"] == "employee":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="社員アカウントにはユーザー作成権限がありません"
                )
            
            # userロールの場合は社員アカウントとして登録（管理画面にアクセスできない）
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
                role="employee",
                company_id=company_id,
                db=db,
                creator_user_id=current_user["id"]  # 作成者IDを渡す
            )
            
            return {
                "id": user_id,
                "email": user_data.email,
                "name": name,
                "role": "employee",
                "company_name": "",
                "created_at": datetime.datetime.now().isoformat()
            }
    except HTTPException as e:
        # HTTPExceptionはそのまま再送出
        print(f"社員アカウント作成エラー: {e.status_code}: {e.detail}")
        raise
    except Exception as e:
        print(f"社員アカウント作成エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"社員アカウント作成に失敗しました: {str(e)}"
        )

@app.delete("/chatbot/api/admin/delete-user/{user_id}", response_model=dict)
async def admin_delete_user(user_id: str, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """管理者によるユーザー削除"""
    # 特別な管理者（queue@queuefood.co.jp）のみがユーザーを削除できる
    if current_user["email"] != "queue@queuefood.co.jp" or not current_user.get("is_special_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には特別な管理者権限が必要です"
        )
    
    # 自分自身は削除できない
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="自分自身を削除することはできません"
        )
    
    # ユーザーの存在確認
    user_result = select_data("users", filters={"id": user_id})
    
    if not user_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたユーザーが見つかりません"
        )
    
    user = user_result.data[0]
    
    # ユーザーの削除
    delete_data("usage_limits", "user_id", user_id)
    delete_data("document_sources", "uploaded_by", user_id)
    delete_data("users", "id", user_id)
    
    return {"message": f"ユーザー {user['email']} を削除しました", "deleted_user_id": user_id}

@app.get("/chatbot/api/admin/users", response_model=List[UserResponse])
async def admin_get_users(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """全ユーザー一覧を取得"""
    # 特別な管理者（queue@queuefood.co.jp）のみが全ユーザー一覧を取得できる
    if current_user["email"] != "queue@queuefood.co.jp" or not current_user.get("is_special_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には特別な管理者権限が必要です"
        )
    return get_all_users(db)

@app.get("/chatbot/api/admin/demo-stats", response_model=DemoUsageStats)
async def admin_get_demo_stats(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """デモ利用状況の統計を取得"""
    return get_demo_usage_stats(db)

# URLを送信するエンドポイント
@app.post("/chatbot/api/submit-url")
async def submit_url(submission: UrlSubmission, current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """URLを送信して知識ベースを更新"""
    try:
        # URLが空でないことを確認
        if not submission.url or not submission.url.strip():
            raise HTTPException(
                status_code=400,
                detail="URLが指定されていません。"
            )
            
        # URLの基本的な検証
        if not submission.url.startswith(('http://', 'https://')) and not submission.url.startswith('www.'):
            submission.url = 'https://' + submission.url
            
        # URL処理を実行
        result = await process_url(submission.url, current_user["id"], None, db)
        return result
    except Exception as e:
        logger.error(f"URL送信エラー: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 'int' object has no attribute 'strip' エラーの特別処理
        if "'int' object has no attribute 'strip'" in str(e):
            raise HTTPException(
                status_code=500,
                detail="データ型エラーが発生しました。管理者に連絡してください。"
            )
        
        # その他の例外は通常のエラーレスポンスを返す
        raise HTTPException(
            status_code=500,
            detail=f"URLの処理中にエラーが発生しました: {str(e)}"
        )

# ファイルをアップロードするエンドポイント
@app.post("/chatbot/api/upload-knowledge")
async def upload_knowledge(file: UploadFile = File(...), current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """ファイルをアップロードして知識ベースを更新"""
    try:
        # ファイル名が存在することを確認
        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail="ファイルが指定されていないか、ファイル名が無効です。"
            )
            
        # ファイル拡張子をチェック（Google Driveアップロードの場合はスキップ）
        if not file.filename.lower().endswith(('.xlsx', '.xls', '.pdf', '.txt', '.avi', '.mp4', '.webp')):
            raise HTTPException(
                status_code=400,
                detail="無効なファイル形式です。ExcelファイルまたはPDFファイル、テキストファイル（.xlsx、.xls、.pdf、.txt）のみ対応しています。"
            )
            
        # ファイル処理を実行
        result = await process_file(file, current_user["id"], None, db)
        return result
    except Exception as e:
        logger.error(f"ファイルアップロードエラー: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 'int' object has no attribute 'strip' エラーの特別処理
        if "'int' object has no attribute 'strip'" in str(e):
            raise HTTPException(
                status_code=500,
                detail="データ型エラーが発生しました。管理者に連絡してください。"
            )
        
        # その他の例外は通常のエラーレスポンスを返す
        raise HTTPException(
            status_code=500,
            detail=f"ファイルのアップロード中にエラーが発生しました: {str(e)}"
        )

# 知識ベース情報を取得するエンドポイント
@app.get("/chatbot/api/knowledge-base")
async def get_knowledge_base(current_user = Depends(get_current_user)):
    """現在の知識ベースの情報を取得"""
    return get_knowledge_base_info()

# チャットエンドポイント
@app.post("/chatbot/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """チャットメッセージを処理してGeminiからの応答を返す"""
    # デバッグ：現在のユーザー情報と利用制限を出力
    print(f"=== チャット処理開始 ===")
    print(f"ユーザー情報: {current_user}")
    
    # 現在の利用制限を取得して表示
    from modules.database import get_usage_limits
    current_limits = get_usage_limits(current_user["id"], db)
    print(f"現在の利用制限: {current_limits}")
    
    # ユーザーIDを設定
    message.user_id = current_user["id"]
    message.employee_name = current_user["name"]
    
    return await process_chat(message, db)

# チャット履歴を取得するエンドポイント
@app.get("/chatbot/api/admin/chat-history", response_model=List[ChatHistoryItem])
async def admin_get_chat_history(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """チャット履歴を取得する"""
    # 現在のユーザーIDを渡して、そのユーザーのデータのみを取得
    # 特別な管理者（queue@queuefood.co.jp）の場合は全ユーザーのデータを取得できるようにする
    if current_user["email"] in ["queue@queuefood.co.jp", "queue@queue-tech.jp"] and current_user.get("is_special_admin", False):
        # 特別な管理者の場合は全ユーザーのデータを取得
        return get_chat_history(None, db)
    else:
        # 通常のユーザーの場合は自分のデータのみを取得
        user_id = current_user["id"]
        return get_chat_history(user_id, db)

# チャット分析エンドポイント
@app.get("/chatbot/api/admin/analyze-chats")
async def admin_analyze_chats(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """チャット履歴を分析する"""
    try:
        # 特別な管理者（queue@queuefood.co.jp）の場合は全ユーザーのデータを分析できるようにする
        if current_user["email"] in ["queue@queuefood.co.jp", "queue@queue-tech.jp"] and current_user.get("is_special_admin", False):
            # 特別な管理者の場合は全ユーザーのデータを分析
            result = await analyze_chats(None, db)
            print(f"分析結果: {result}")
            return result
        else:
            # 通常のユーザーの場合は自分のデータのみを分析
            user_id = current_user["id"]
            result = await analyze_chats(user_id, db)
            print(f"分析結果: {result}")
            return result
    except Exception as e:
        print(f"チャット分析エラー: {e}")
        # エラーが発生した場合でも空の結果を返す
        return {
            "total_messages": 0,
            "average_response_time": 0,
            "category_distribution": [],
            "sentiment_distribution": [],
            "daily_usage": [],
            "common_questions": []
        }

# 詳細ビジネス分析エンドポイント
@app.post("/chatbot/api/admin/detailed-analysis")
async def admin_detailed_analysis(request: dict, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """詳細なビジネス分析を行う"""
    try:
        # ユーザー情報の取得
        is_admin = current_user["role"] == "admin"
        is_user = current_user["role"] == "user"
        is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queue-tech.jp"] and current_user.get("is_special_admin", False)
        
        # プロンプトを取得
        prompt = request.get("prompt", "")
        
        # 通常の分析結果を取得
        if is_special_admin or is_admin:
            # 管理者または特別管理者は全データで分析
            analysis_result = await analyze_chats(None, db)
        else:
            # userロールを含む一般ユーザーは自分のデータのみで分析
            analysis_result = await analyze_chats(current_user["id"], db)
        
        # より詳細なチャットデータを取得
        try:
            if is_special_admin or is_admin:
                # 全データを取得
                chat_result = select_data("chat_history", limit=1000, order="created_at desc")
            else:
                # 自分のデータのみ取得
                chat_result = select_data("chat_history", filters={"user_id": current_user["id"]}, limit=1000, order="created_at desc")
            
            chat_data = chat_result.data if chat_result.data else []
            
            # 詳細なデータ分析
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
                # メッセージ長の分析
                message_lengths = [len(msg.get("message", "")) for msg in chat_data if msg.get("message")]
                detailed_metrics["average_message_length"] = sum(message_lengths) / len(message_lengths) if message_lengths else 0
                
                # 時間帯別の分析
                hour_counts = {}
                for msg in chat_data:
                    if msg.get("created_at"):
                        try:
                            dt = datetime.datetime.fromisoformat(msg["created_at"].replace('Z', '+00:00'))
                            hour = dt.hour
                            hour_counts[hour] = hour_counts.get(hour, 0) + 1
                        except:
                            continue
                
                # ピーク時間帯を特定
                if hour_counts:
                    sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
                    detailed_metrics["peak_usage_hours"] = sorted_hours[:3]
                
                # 繰り返し質問の分析
                message_texts = [msg.get("message", "").lower() for msg in chat_data if msg.get("message")]
                unique_messages = set(message_texts)
                if message_texts:
                    detailed_metrics["repeat_question_rate"] = (len(message_texts) - len(unique_messages)) / len(message_texts) * 100
                
                # よくある失敗パターンの特定
                failure_keywords = ["エラー", "わからない", "できない", "失敗", "問題", "困った", "うまくいかない", "動かない"]
                failure_count = 0
                for msg in message_texts:
                    if any(keyword in msg for keyword in failure_keywords):
                        failure_count += 1
                
                if message_texts:
                    detailed_metrics["resolution_rate"] = max(0, (len(message_texts) - failure_count) / len(message_texts) * 100)
            
        except Exception as e:
            print(f"詳細メトリクス取得エラー: {e}")
            detailed_metrics = {"error": "詳細メトリクスの取得に失敗しました"}
        
        # カテゴリーとセンチメントの分布から洞察を生成
        categories = analysis_result.get("category_distribution", {})
        sentiments = analysis_result.get("sentiment_distribution", {})
        questions = analysis_result.get("common_questions", [])
        daily_usage = analysis_result.get("daily_usage", [])
        
        # Gemini APIで詳細な分析を実行
        from modules.admin import model
        
        # Geminiモデルが初期化されていない場合のエラーハンドリング
        if model is None:
            raise HTTPException(status_code=500, detail="Geminiモデルが初期化されていません")
        
        # 短縮されたビジネス特化プロンプト
        analysis_prompt = f"""
        {prompt}
        
        # 分析データ
        - 総会話数: {detailed_metrics.get('total_conversations', 0)}件
        - 繰り返し質問率: {detailed_metrics.get('repeat_question_rate', 0):.1f}%
        - ピーク利用時間: {detailed_metrics.get('peak_usage_hours', [])}
        
        カテゴリ分布: {json.dumps(categories, ensure_ascii=False)}
        感情分布: {json.dumps(sentiments, ensure_ascii=False)}
        頻出質問: {json.dumps(questions[:5], ensure_ascii=False)}
        
        # 以下の6項目でビジネス分析を実施してください。各項目300文字以内で簡潔に。
        
        【1. 頻出トピック分析】
        最多質問パターンと業務課題を特定し、標準化の機会を示してください。
        
        【2. 効率化機会】
        繰り返し質問から自動化可能な業務を特定し、ROIの高い改善案を提案してください。
        
        【3. フラストレーション要因】
        ネガティブ感情の原因と未解決問題のパターンを分析し、優先改善点を明示してください。
        
        【4. システム改善案】
        機能追加・改善の具体提案とユーザーニーズの優先順位を示してください。
        
        【5. 情報共有課題】
        部門間の情報ギャップとドキュメント化が必要な領域を特定してください。
        
        【6. 実行計画】
        短期（1-3ヶ月）・中期（3-6ヶ月）・長期（6ヶ月-1年）の改善提案を投資対効果と共に提示してください。
        """
        
        # Gemini APIによる詳細分析
        analysis_response = model.generate_content(analysis_prompt)
        detailed_analysis_text = analysis_response.text
        
        print(f"Gemini分析結果: {detailed_analysis_text[:500]}...")  # デバッグ用
        
        # 詳細分析の結果をセクションごとに分割して整形
        import re
        
        # 各セクションのデータ
        detailed_analysis = {
            "detailed_topic_analysis": "",
            "efficiency_opportunities": "",
            "frustration_points": "",
            "improvement_suggestions": "",
            "communication_gaps": "",
            "specific_recommendations": ""
        }
        
        # より精密なセクション分割パターン
        sections = [
            (r"【1\..*?頻出トピック.*?】", "detailed_topic_analysis"),
            (r"【2\..*?業務効率化.*?】", "efficiency_opportunities"),
            (r"【3\..*?フラストレーション.*?】", "frustration_points"),
            (r"【4\..*?製品.*?サービス.*?改善.*?】", "improvement_suggestions"),
            (r"【5\..*?コミュニケーション.*?】", "communication_gaps"),
            (r"【6\..*?具体的.*?改善提案.*?】", "specific_recommendations")
        ]
        
        # セクション分割処理の改善
        text_lines = detailed_analysis_text.split("\n")
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
                # 前のセクションの内容を保存
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
        
        # セクション分割に失敗した場合の対処
        filled_sections = sum(1 for value in detailed_analysis.values() if value.strip())
        if filled_sections < 3:
            # セクション分割に失敗した場合は、全テキストを分割して配布
            text_parts = detailed_analysis_text.split("\n\n")
            section_keys = list(detailed_analysis.keys())
            
            for i, part in enumerate(text_parts[:len(section_keys)]):
                if part.strip():
                    detailed_analysis[section_keys[i]] = part.strip()
            
            print("セクション分割に失敗したため、テキストを均等に分配しました")
        
        # デバッグ情報
        print(f"分析結果セクション:")
        for key, value in detailed_analysis.items():
            char_count = len(value.strip()) if value else 0
            print(f"  {key}: {char_count} 文字")
        
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
        print(f"詳細ビジネス分析エラー: {str(e)}")
        print(traceback.format_exc())
        
        # エラーの場合でも有用な分析結果を返す
        return {
            "detailed_analysis": {
                "detailed_topic_analysis": f"分析処理中にエラーが発生しました: {str(e)}\n\n利用可能な基本データから推測される主要な質問パターンを確認し、手動での詳細分析を検討してください。",
                "efficiency_opportunities": "システムエラーにより自動分析が完了できませんでした。チャット履歴を手動で確認し、繰り返し質問や標準化可能な業務を特定することをお勧めします。",
                "frustration_points": "エラーにより詳細な感情分析ができませんでした。ユーザーからの否定的なフィードバックやクレームを個別に確認してください。",
                "improvement_suggestions": "自動分析は利用できませんが、基本的な改善として以下を検討してください：\n- FAQ の充実\n- 回答精度の向上\n- ユーザーインターフェースの改善",
                "communication_gaps": "システム制限により分析できませんでした。部門間での情報共有状況を手動で確認し、ドキュメント化が必要な領域を特定してください。",
                "specific_recommendations": "技術的な問題により詳細な提案ができませんが、以下の基本的な改善を優先してください：\n1. システムの安定性向上\n2. エラー処理の改善\n3. 分析機能の再設計"
            },
            "analysis_metadata": {
                "error": str(e),
                "analysis_timestamp": datetime.datetime.now().isoformat(),
                "data_quality_score": 0
            }
        }

# 社員詳細情報を取得するエンドポイント
@app.get("/chatbot/api/admin/employee-details/{employee_id}", response_model=List[ChatHistoryItem])
async def admin_get_employee_details(employee_id: str, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """特定の社員の詳細なチャット履歴を取得する"""
    # 特別な管理者（queue@queuefood.co.jp）の場合は全ユーザーのデータを取得できるようにする
    is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queue-tech.jp"] and current_user.get("is_special_admin", False)
    
    # ユーザーIDを渡して権限チェックを行う
    return await get_employee_details(employee_id, db, current_user["id"])

# 会社の全社員情報を取得するエンドポイント
@app.get("/chatbot/api/admin/company-employees", response_model=List[dict])
async def admin_get_company_employees(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """会社の全社員情報を取得する"""
    # adminロールのユーザーは全ユーザーのデータを取得できるようにする
    is_admin = current_user["role"] == "admin"
    is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queue-tech.jp"] and current_user.get("is_special_admin", False)
    
    # 直接get_company_employees関数に処理を委譲
    if is_admin or is_special_admin:
        # adminロールまたは特別な管理者の場合は全ユーザーのデータを取得
        result = await get_company_employees(current_user["id"], db, None)
        return result
    else:
        # 通常のユーザーの場合は自分の会社の社員のデータのみを取得
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
    # adminロールのユーザーは全ユーザーのデータを取得できるようにする
    is_admin = current_user["role"] == "admin"
    is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queue-tech.jp"] and current_user.get("is_special_admin", False)
    
    if is_admin or is_special_admin:
        # adminロールまたは特別な管理者の場合は全ユーザーのデータを取得
        return await get_employee_usage(None, db, is_special_admin=True)
    else:
        # 通常のユーザーの場合は自分の会社の社員のデータのみを取得
        user_id = current_user["id"]
        return await get_employee_usage(user_id, db, is_special_admin=False)

# アップロードされたリソースを取得するエンドポイント
@app.get("/chatbot/api/admin/resources", response_model=ResourcesResult)
async def admin_get_resources(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """アップロードされたリソース（URL、PDF、Excel、TXT）の情報を取得する"""
    # adminロールのユーザーは全リソースのデータを取得できるようにする
    is_admin = current_user["role"] == "admin"
    is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queue-tech.jp"] and current_user.get("is_special_admin", False)
    
    if is_admin or is_special_admin:
        return await get_uploaded_resources_by_company_id(None, db)
    else:
        company_id = current_user["company_id"]
        print(await get_uploaded_resources_by_company_id(company_id, db))
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
    # return await delete_resource(decoded_id)
    return await remove_resource_by_id(decoded_id, db)

# 会社名を取得するエンドポイント
@app.get("/chatbot/api/company-name", response_model=CompanyNameResponse)
async def api_get_company_name(current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """現在の会社名を取得する"""
    return await get_company_name(current_user, db)

# 会社名を設定するエンドポイント
@app.post("/chatbot/api/company-name", response_model=CompanyNameResponse)
async def api_set_company_name(request: CompanyNameRequest, current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """会社名を設定する"""
    return await set_company_name(request, current_user, db)

# プラン変更エンドポイント
@app.post("/chatbot/api/upgrade-plan", response_model=UpgradePlanResponse)
async def upgrade_plan(request: UpgradePlanRequest, current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """デモ版から有料プランにアップグレードする（強化版）"""
    try:
        print(f"=== プランアップグレード開始 ===")
        print(f"ユーザー: {current_user['email']} ({current_user['name']})")
        print(f"ユーザーID: {current_user['id']}")
        print(f"要求プラン: {request.plan_id}")
        
        # プラン情報を定義
        plans = {
            "starter": {"name": "スタータープラン", "price": 2980, "questions_limit": -1, "uploads_limit": 10},
            "business": {"name": "ビジネスプラン", "price": 9800, "questions_limit": -1, "uploads_limit": 100},
            "enterprise": {"name": "エンタープライズプラン", "price": 29800, "questions_limit": -1, "uploads_limit": -1},
        }
        
        if request.plan_id not in plans:
            raise HTTPException(status_code=400, detail="無効なプランIDです")
        
        plan = plans[request.plan_id]
        user_id = current_user["id"]
        
        print(f"選択されたプラン: {plan['name']} (価格: ¥{plan['price']})")
        
        # 現在の利用制限を取得（変更前の状態を確認）
        from supabase_adapter import update_data, select_data
        current_limits_result = select_data("usage_limits", filters={"user_id": user_id})
        was_unlimited = False
        current_questions_used = 0
        current_uploads_used = 0
        
        if current_limits_result and current_limits_result.data:
            current_limits = current_limits_result.data[0]
            was_unlimited = bool(current_limits.get("is_unlimited", False))
            current_questions_used = current_limits.get("questions_used", 0)
            current_uploads_used = current_limits.get("document_uploads_used", 0)
            
            print(f"現在のステータス: {'本番版' if was_unlimited else 'デモ版'}")
            print(f"現在の使用状況: 質問={current_questions_used}, アップロード={current_uploads_used}")
        
        if was_unlimited:
            print("⚠ ユーザーは既に本番版です")
            return UpgradePlanResponse(
                success=True,
                message=f"既に本番版です。{plan['name']}の機能をご利用いただけます。",
                plan_id=request.plan_id,
                user_id=user_id,
                payment_url=None
            )
        
        # 実際の決済処理（今回はモック）
        # 本番環境では Stripe や PayPal などの決済サービスと連携
        print("決済処理中...")
        payment_success = True  # モックとして成功とする
        
        if payment_success:
            print("✓ 決済成功")
            
            # 新しい制限値を計算
            new_questions_limit = plan["questions_limit"] if plan["questions_limit"] != -1 else 999999
            new_uploads_limit = plan["uploads_limit"] if plan["uploads_limit"] != -1 else 999999
            
            print(f"新しい制限: 質問={new_questions_limit}, アップロード={new_uploads_limit}")
            
            # usage_limitsテーブルを更新
            update_result = update_data("usage_limits", {
                "is_unlimited": True,
                "questions_limit": new_questions_limit,
                "questions_used": current_questions_used,  # 現在の使用数を保持
                "document_uploads_limit": new_uploads_limit,
                "document_uploads_used": current_uploads_used  # 現在の使用数を保持
            }, "user_id", user_id)
            
            if update_result:
                print("✓ 利用制限更新完了")
            else:
                print("✗ 利用制限更新失敗")
                raise HTTPException(status_code=500, detail="利用制限の更新に失敗しました")
            
            # ユーザーテーブルにプラン情報を追加（roleを更新）
            user_update_result = update_data("users", {
                "role": "user"  # デモ版からuserプランに変更
            }, "id", user_id)
            
            if user_update_result:
                print("✓ ユーザーロール更新完了 (demo -> user)")
            else:
                print("✗ ユーザーロール更新失敗")
            
            # デモ版から本番版に切り替わった場合、作成したアカウントも同期
            print("子アカウントの同期を開始...")
            from modules.database import update_created_accounts_status
            updated_children = update_created_accounts_status(user_id, True, db)
            
            # 同じ会社の全ユーザーも同期
            print("同じ会社のユーザーの同期を開始...")
            from modules.database import update_company_users_status
            updated_company_users = update_company_users_status(user_id, True, db)
            
            success_message = f"{plan['name']}へのアップグレードが完了しました"
            if updated_children > 0 or updated_company_users > 0:
                success_message += f"（子アカウント {updated_children} 個、同じ会社のユーザー {updated_company_users} 個も同期）"
            
            print(f"=== プランアップグレード完了 ===")
            print(f"結果: {success_message}")
            
            return UpgradePlanResponse(
                success=True,
                message=success_message,
                plan_id=request.plan_id,
                user_id=user_id,
                payment_url=None
            )
        else:
            print("✗ 決済失敗")
            raise HTTPException(status_code=400, detail="決済処理に失敗しました")
            
    except HTTPException as e:
        print(f"✗ HTTPエラー: {e.detail}")
        raise
    except Exception as e:
        print(f"✗ プランアップグレードエラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        logger.error(f"プランアップグレードエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"アップグレード処理中にエラーが発生しました: {str(e)}")

@app.get("/chatbot/api/subscription-info", response_model=SubscriptionInfo)
async def get_subscription_info(current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """現在のユーザーのサブスクリプション情報を取得する"""
    try:
        from supabase_adapter import select_data
        
        # ユーザーの利用制限情報を取得
        limits_result = select_data("usage_limits", filters={"user_id": current_user["id"]})
        
        if not limits_result.data:
            raise HTTPException(status_code=404, detail="サブスクリプション情報が見つかりません")
        
        limits = limits_result.data[0]
        is_unlimited = limits.get("is_unlimited", False)
        
        if is_unlimited:
            # プランを判定（questions_limitやuploads_limitから推測）
            uploads_limit = limits.get("document_uploads_limit", 2)
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
                plan_name="デモ版",
                status="trial",
                start_date=current_user.get("created_at", ""),
                price=0
            )
            
    except Exception as e:
        logger.error(f"サブスクリプション情報取得エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"サブスクリプション情報の取得中にエラーが発生しました: {str(e)}")

# 申請フォーム送信エンドポイント
@app.post("/chatbot/api/submit-application")
async def submit_application(request: Request):
    """本番版移行申請を受け付ける"""
    try:
        body = await request.json()
        print(f"申請フォーム受信: {body}")
        
        # 申請データを処理
        application_data = {
            "company_name": body.get("companyName"),
            "contact_name": body.get("contactName"),
            "email": body.get("email"),
            "phone": body.get("phone"),
            "expected_users": body.get("expectedUsers"),
            "current_usage": body.get("currentUsage"),
            "message": body.get("message"),
            "application_type": body.get("applicationType", "production-upgrade")
        }
        
        # データベースに申請データを保存
        from modules.database import save_application
        application_id = save_application(application_data)
        
        if application_id:
            print(f"✓ 申請受付完了: ID={application_id}")
            print(f"  会社名: {application_data['company_name']}")
            print(f"  担当者: {application_data['contact_name']}")
            print(f"  メール: {application_data['email']}")
            print(f"  電話: {application_data['phone']}")
            print(f"  予想利用者: {application_data['expected_users']}")
            print(f"  現在の利用状況: {application_data['current_usage']}")
            print(f"  メッセージ: {application_data['message']}")
            
            # TODO: 今後の機能追加
            # 1. 営業担当者にメール通知
            # 2. 申請者に受付完了メールを送信
            # 3. Slack通知などの外部連携
            
            return {
                "success": True, 
                "message": "申請を受け付けました。営業担当者よりご連絡いたします。",
                "application_id": application_id
            }
        else:
            raise HTTPException(status_code=500, detail="申請データの保存に失敗しました")
        
    except Exception as e:
        print(f"申請フォーム処理エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="申請の処理中にエラーが発生しました")

# 静的ファイルのマウント
# フロントエンドのビルドディレクトリを指定
frontend_build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# 静的ファイルを提供するためのルートを追加
@app.get("/", include_in_schema=False)
async def read_root():
    index_path = os.path.join(frontend_build_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": f"Welcome to {DEFAULT_COMPANY_NAME} Chatbot API"}



# 静的ファイルをマウント
if os.path.exists(os.path.join(frontend_build_dir, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_build_dir, "assets")), name="assets")

# プラン履歴取得エンドポイント（catch_allより前に配置）
@app.get("/chatbot/api/plan-history", response_model=dict)
async def get_plan_history_endpoint(current_user = Depends(get_current_user), db: SupabaseConnection = Depends(get_db)):
    """プラン履歴を人単位でグループ化して取得する"""
    try:
        print(f"プラン履歴取得要求 - ユーザー: {current_user['email']} (ロール: {current_user['role']})")
        
        from modules.database import get_plan_history
        
        # 管理者・特別管理者は全てのプラン履歴を、一般ユーザーは自分の履歴のみを取得
        if current_user["role"] in ["admin"] or current_user["email"] in ["queue@queuefood.co.jp", "queue@queue-tech.jp"]:
            # 管理者または特別管理者は全履歴を取得
            user_histories = get_plan_history(db=db)
        else:
            # 一般ユーザー（userロール含む）は自分の履歴のみを取得
            user_histories = get_plan_history(user_id=current_user["id"], db=db)
        
        # 追加の統計情報を計算
        total_users = len(user_histories)
        total_changes = sum(user.get("total_changes", 0) for user in user_histories)
        
        # プラン別の統計
        plan_stats = {}
        for user in user_histories:
            current_plan = user.get("current_plan", "不明")
            if current_plan in plan_stats:
                plan_stats[current_plan] += 1
            else:
                plan_stats[current_plan] = 1
        
        return {
            "success": True,
            "data": {
                "users": user_histories,
                "statistics": {
                    "total_users": total_users,
                    "total_changes": total_changes,
                    "plan_distribution": plan_stats
                }
            },
            "count": total_users,
            "message": f"{total_users}人のプラン履歴を人単位でグループ化して表示しています"
        }
        
    except Exception as e:
        print(f"プラン履歴取得エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"プラン履歴の取得に失敗しました: {str(e)}"
        )

# テスト用デバッグエンドポイント（認証なし）
@app.get("/chatbot/api/test-simple")
async def simple_test():
    """認証なしの簡単なテスト"""
    return {"message": "Backend is working!", "timestamp": datetime.datetime.now().isoformat()}

# テスト用デバッグエンドポイント
@app.get("/chatbot/api/admin/csv-test")
async def csv_test_endpoint():
    """CSVエンドポイントのテスト"""
    return {"message": "CSV endpoint is working", "timestamp": datetime.datetime.now().isoformat()}

# チャット履歴をCSV形式でダウンロードするエンドポイント（catch_allより前に配置）
@app.get("/chatbot/api/admin/chat-history/csv")
async def download_chat_history_csv(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """チャット履歴をCSV形式でダウンロードする"""
    try:
        print(f"CSVダウンロード開始 - ユーザー: {current_user['email']}")
        
        # 権限チェック（user、employeeロールも許可）
        is_admin = current_user["role"] == "admin"
        is_user = current_user["role"] == "user"
        is_employee = current_user["role"] == "employee"
        is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queue-tech.jp"] and current_user.get("is_special_admin", False)
        
        # チャット履歴を直接Supabaseから取得
        try:
            if is_special_admin or is_admin:
                # 管理者または特別管理者の場合は全ユーザーのデータを取得
                print("管理者として全ユーザーのチャット履歴を取得")
                from supabase_adapter import select_data
                result = select_data("chat_history", columns="*")
                chat_history = result.data if result and result.data else []
            elif is_user or is_employee:
                # userまたはemployeeロールの場合は自分の会社のデータのみを取得
                print(f"{current_user['role']}ロールとして自分の会社のチャット履歴を取得")
                from supabase_adapter import select_data
                # まずユーザーの会社IDを取得
                user_result = select_data("users", filters={"id": current_user["id"]})
                if user_result and user_result.data:
                    user_data = user_result.data[0]
                    company_name = user_data.get("company_name")
                    if company_name:
                        # 同じ会社のユーザーIDリストを取得
                        company_users_result = select_data("users", filters={"company_name": company_name})
                        if company_users_result and company_users_result.data:
                            company_user_ids = [user["id"] for user in company_users_result.data]
                            # 会社のユーザーのチャット履歴を取得
                            result = select_data("chat_history", filters={"employee_id": f"in.({','.join(company_user_ids)})"})
                            chat_history = result.data if result and result.data else []
                        else:
                            chat_history = []
                    else:
                        # 会社名がない場合は自分のデータのみ
                        result = select_data("chat_history", filters={"employee_id": current_user["id"]})
                        chat_history = result.data if result and result.data else []
                else:
                    chat_history = []
            else:
                # その他のユーザーの場合は自分のデータのみを取得
                user_id = current_user["id"]
                print(f"通常ユーザーとして個人のチャット履歴を取得: {user_id}")
                from supabase_adapter import select_data
                result = select_data("chat_history", columns="*", filters={"employee_id": user_id})
                chat_history = result.data if result and result.data else []
        except Exception as e:
            print(f"チャット履歴取得エラー: {e}")
            chat_history = []
        
        print(f"取得したチャット履歴数: {len(chat_history)}")
        
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
            "参照文書",
            "ページ番号"
        ])
        
        # データ行を書き込み
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
        
        # CSV文字列を取得
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

@app.post("/chatbot/api/admin/update-user-status/{user_id}", response_model=dict)
async def admin_update_user_status(user_id: str, request: dict, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """管理者によるユーザーステータス変更（adminのみ実行可能）"""
    # adminロールまたは特別な管理者のみが実行可能
    is_admin = current_user["role"] == "admin"
    is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queue-tech.jp"] and current_user.get("is_special_admin", False)
    
    print(f"=== ユーザーステータス変更権限チェック ===")
    print(f"操作者: {current_user['email']} (管理者: {is_admin}, 特別管理者: {is_special_admin})")
    
    # 権限チェック - adminまたは特別管理者のみ
    if not (is_admin or is_special_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者権限が必要です。一般ユーザーは自分のプラン変更を行うことはできません。"
        )
    
    try:
        print(f"=== ユーザーステータス変更開始 ===")
        print(f"対象ユーザーID: {user_id}")
        
        new_is_unlimited = bool(request.get("is_unlimited", False))
        print(f"新しいステータス: {'本番版' if new_is_unlimited else 'デモ版'}")
        
        # ユーザーの存在確認
        user_result = select_data("users", filters={"id": user_id})
        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたユーザーが見つかりません"
            )
        
        user = user_result.data[0]
        print(f"対象ユーザー: {user['email']} ({user['name']}) - ロール: {user['role']}")
        
        # 管理者ロールの場合は警告
        if user['role'] == 'admin':
            print(f"警告: 管理者ロール ({user['email']}) のステータス変更")
        
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
        
        print(f"現在のステータス: {'本番版' if was_unlimited else 'デモ版'}")
        print(f"現在の使用状況: 質問={current_questions_used}, アップロード={current_uploads_used}")
        
        # ステータスに変更がない場合は何もしない
        if was_unlimited == new_is_unlimited:
            print("ステータスに変更がないため処理をスキップします")
            return {
                "message": f"ユーザー {user['email']} のステータスは既に{'本番版' if new_is_unlimited else 'デモ版'}です",
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
            
            # デモ版に変更する場合、使用済み数が新しい制限を超える場合は調整
            if current_questions_used > new_questions_limit:
                print(f"質問使用数を {current_questions_used} から {new_questions_limit} に調整")
                current_questions_used = new_questions_limit
            if current_uploads_used > new_uploads_limit:
                print(f"アップロード使用数を {current_uploads_used} から {new_uploads_limit} に調整")
                current_uploads_used = new_uploads_limit
        
        print(f"新しい制限: 質問={new_questions_limit} (使用済み: {current_questions_used}), アップロード={new_uploads_limit} (使用済み: {current_uploads_used})")
        
        # 利用制限を更新
        update_result = update_data("usage_limits", {
            "is_unlimited": new_is_unlimited,
            "questions_limit": new_questions_limit,
            "questions_used": current_questions_used,
            "document_uploads_limit": new_uploads_limit,
            "document_uploads_used": current_uploads_used
        }, "user_id", user_id)
        
        if update_result:
            print("✓ 本人のステータス更新完了")
        else:
            print("✗ 本人のステータス更新失敗")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="利用制限の更新に失敗しました"
            )
        
        # プラン履歴を記録
        print("プラン履歴を記録します...")
        from modules.database import record_plan_change
        from_plan = "unlimited" if was_unlimited else "demo"
        to_plan = "unlimited" if new_is_unlimited else "demo"
        record_plan_change(user_id, from_plan, to_plan, db)
        
        # 作成したアカウントも同期
        print("子アカウントの同期を開始します...")
        from modules.database import update_created_accounts_status
        updated_children = update_created_accounts_status(user_id, new_is_unlimited, db)
        
        # 同じ会社の全ユーザーも同期
        print("同じ会社のユーザーの同期を開始...")
        from modules.database import update_company_users_status
        updated_company_users = update_company_users_status(user_id, new_is_unlimited, db)
        
        result_message = f"ユーザー {user['email']} のステータスを{'本番版' if new_is_unlimited else 'デモ版'}に変更しました"
        if updated_children > 0 or updated_company_users > 0:
            result_message += f"（子アカウント {updated_children} 個、同じ会社のユーザー {updated_company_users} 個も同期）"
        
        print(f"=== ユーザーステータス変更完了 ===")
        print(f"結果: {result_message}")
        
        return {
            "message": result_message,
            "user_id": user_id,
            "updated_children": updated_children,
            "updated_company_users": updated_company_users,
            "details": {
                "user_email": user['email'],
                "user_name": user['name'],
                "old_status": "本番版" if was_unlimited else "デモ版",
                "new_status": "本番版" if new_is_unlimited else "デモ版",
                "new_questions_limit": new_questions_limit,
                "new_uploads_limit": new_uploads_limit
            }
        }
        
    except HTTPException as e:
        print(f"✗ HTTPエラー: {e.detail}")
        raise
    except Exception as e:
        print(f"✗ ユーザーステータス変更エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ステータス変更中にエラーが発生しました: {str(e)}"
        )

# YouTube接続テスト用エンドポイント
@app.get("/chatbot/api/test-youtube")
async def test_youtube_connection():
    """YouTube接続をテストする"""
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
            "message": f"テスト実行エラー: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/chatbot/api/admin/companies", response_model=List[dict])
async def admin_get_companies(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """会社一覧を取得（adminのみ）"""
    # 特別な管理者のみがアクセス可能
    if current_user["email"] not in ["queue@queuefood.co.jp", "queue@queue-tech.jp"] or not current_user.get("is_special_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には特別な管理者権限が必要です"
        )
    
    from modules.database import get_all_companies
    companies = get_all_companies(db)
    return companies

@app.post("/chatbot/api/admin/fix-company-status/{company_id}", response_model=dict)
async def admin_fix_company_status(company_id: str, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """会社内のユーザーステータス不整合を修正する"""
    # adminロールまたは特別な管理者のみが実行可能
    is_admin = current_user["role"] == "admin"
    is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queue-tech.jp"] and current_user.get("is_special_admin", False)
    
    if not (is_admin or is_special_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者権限が必要です"
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
    # adminロールまたは特別な管理者のみが実行可能
    is_admin = current_user["role"] == "admin"
    is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queue-tech.jp"] and current_user.get("is_special_admin", False)
    
    if not (is_admin or is_special_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者権限が必要です"
        )
    
    try:
        from modules.database import ensure_usage_limits_integrity
        fixed_count = ensure_usage_limits_integrity(db)
        
        return {
            "message": f"データベース整合性チェックが完了しました",
            "fixed_count": fixed_count,
            "details": f"{fixed_count}個のusage_limitsレコードを作成しました" if fixed_count > 0 else "修正が必要なレコードはありませんでした"
        }
        
    except Exception as e:
        print(f"データベース整合性チェックエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"データベース整合性チェック中にエラーが発生しました: {str(e)}"
        )




# 申請管理エンドポイント（管理者用）
@app.get("/chatbot/api/admin/applications")
async def admin_get_applications(status: str = None, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """管理者が申請一覧を取得する"""
    try:
        print(f"申請一覧取得要求 - ユーザー: {current_user['email']} (ロール: {current_user['role']})")
        
        # 管理者権限チェック
        is_admin = current_user["role"] == "admin"
        is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queue-tech.jp"] and current_user.get("is_special_admin", False)
        
        if not (is_admin or is_special_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この操作には管理者権限が必要です"
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
    """管理者が申請のステータスを更新する"""
    try:
        print(f"申請ステータス更新要求 - ユーザー: {current_user['email']}")
        print(f"申請ID: {application_id}")
        print(f"リクエスト: {request}")
        
        # 管理者権限チェック
        is_admin = current_user["role"] == "admin"
        is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queue-tech.jp"] and current_user.get("is_special_admin", False)
        
        if not (is_admin or is_special_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この操作には管理者権限が必要です"
            )
        
        new_status = request.get("status")
        notes = request.get("notes", "")
        
        if not new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ステータスが指定されていません"
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
                "message": f"申請ステータスを'{new_status}'に更新しました"
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
        print(f"company-token-usageエンドポイントが呼び出されました - ユーザー: {current_user['email']}")
        
        # ユーザーの会社IDを取得
        from supabase_adapter import select_data
        user_result = select_data("users", columns="company_id", filters={"id": current_user["id"]})
        company_id = None
        if user_result and user_result.data:
            company_id = user_result.data[0].get("company_id")
        
        # 実際の会社ユーザー数を取得
        company_users_count = 1  # デフォルト（自分だけ）
        company_name = "あなたの会社"
        
        if company_id:
            # 同じ会社のユーザー数をカウント
            company_users_result = select_data("users", columns="id, name", filters={"company_id": company_id})
            if company_users_result and company_users_result.data:
                company_users_count = len(company_users_result.data)
                print(f"✓ 会社ID {company_id} のユーザー数: {company_users_count}人")
            
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
                # TokenUsageTrackerを使用して実際の使用量を取得
                from modules.token_counter import TokenUsageTracker
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
                    print(f"✓ 会社ID {company_id} の実際のトークン使用量: {total_tokens_used:,} tokens")
                else:
                    print("⚠️ 今月のトークン使用量データなし - 全期間で確認します")
                    # 全期間のデータを取得
                    usage_data_all = tracker.get_company_monthly_usage(company_id, "ALL")
                    if usage_data_all and usage_data_all.get("total_tokens", 0) > 0:
                        total_tokens_used = usage_data_all.get("total_tokens", 0)
                        total_input_tokens = usage_data_all.get("total_input_tokens", 0) 
                        total_output_tokens = usage_data_all.get("total_output_tokens", 0)
                        total_conversations = usage_data_all.get("conversation_count", 0)
                        total_cost_usd = usage_data_all.get("total_cost_usd", 0.0)
                        print(f"✓ 全期間での会社ID {company_id} のトークン使用量: {total_tokens_used:,} tokens")
                    else:
                        print("⚠️ 全期間でもトークン使用量データなし")
            else:
                print("⚠️ 会社IDなし - 個人ユーザーのトークン使用量は現在未対応")
        except Exception as e:
            print(f"⚠️ トークン使用量取得エラー: {e} - モックデータを使用します")
        
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
        
        # 日本円料金計算
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
        
        print(f"実際のデータを返却します: company_users_count={company_users_count}, total_tokens={total_tokens_used:,}, company_name={company_name}")
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
        
        # 簡易料金計算（モック）
        basic_plan_cost = 150000  # ¥150,000
        tier1_cost = 0
        tier2_cost = 0
        tier3_cost = 0
        
        # 基本プラン制限を超えた分の計算
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
        
        print(f"Google Driveファイルアップロード開始: {file_name} (ID: {file_id})")
        
        # サポートされているファイル形式かチェック
        if not drive_handler.is_supported_file(mime_type):
            raise HTTPException(
                status_code=400, 
                detail=f"サポートされていないファイル形式です: {mime_type}"
            )
        
        # ファイルメタデータ取得
        file_metadata = await drive_handler.get_file_metadata(file_id, access_token)
        if not file_metadata:
            raise HTTPException(status_code=400, detail="ファイルが見つかりません")
        
        # ファイルサイズチェック（10MB制限）
        file_size = int(file_metadata.get('size', 0))
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400, 
                detail=f"ファイルサイズが大きすぎます ({file_size / (1024*1024):.1f}MB)。10MB以下のファイルをご利用ください。"
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
            
            # Google DocsやSheetsの場合、適切な拡張子に変更
            processed_filename = file_name
            if mime_type == 'application/vnd.google-apps.document':
                # Google DocはPDFに変換されるので.pdf拡張子にする
                base_name = os.path.splitext(file_name)[0]
                processed_filename = f"{base_name}.pdf"
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                # Google SheetはExcelに変換されるので.xlsx拡張子にする
                base_name = os.path.splitext(file_name)[0]
                processed_filename = f"{base_name}.xlsx"
            
            # 既存のprocess_file関数を使用
            mock_file = MockUploadFile(processed_filename, file_content)
            result = await process_file(
                mock_file,
                current_user["id"],
                None,  # company_id
                db
            )
            
            print(f"Google Driveファイル処理完了: {file_name}")
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
        print(f"Google Driveファイル一覧取得: フォルダID={folder_id}")
        
        drive_handler = GoogleDriveHandler()
        files = await drive_handler.list_files(access_token, folder_id, search_query)
        
        # サポートされているファイルのみフィルター
        supported_files = [
            file for file in files 
            if file.get('mimeType') == 'application/vnd.google-apps.folder' or 
               drive_handler.is_supported_file(file.get('mimeType', ''))
        ]
        
        print(f"Google Driveファイル一覧取得完了: {len(supported_files)}件")
        return {"files": supported_files}
        
    except Exception as e:
        print(f"Google Driveファイル一覧取得エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"ファイル一覧取得エラー: {str(e)}")

# その他のルートパスをindex.htmlにリダイレクト（SPAのルーティング用）
# 注意：これを最後に登録することで、他のAPIエンドポイントを優先する
@app.get("/{full_path:path}", include_in_schema=False)
async def catch_all(full_path: str):
    print(f"catch_all handler called with path: {full_path}")
    
    # APIエンドポイントはスキップ（/api で始まるパスまたは chatbot/api で始まるパスはAPIエンドポイントとして処理）
    if full_path.startswith("api/") or full_path.startswith("chatbot/api/"):
        # APIエンドポイントの場合は404を返す
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # SPAルーティング用にindex.htmlを返す
    index_path = os.path.join(frontend_build_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Not Found")

# アプリケーションの実行
if __name__ == "__main__":
    import uvicorn
    from modules.config import get_port
    port = get_port()
    uvicorn.run(app, host="0.0.0.0", port=port, timeout_keep_alive=300)
