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
            
        # ファイル拡張子をチェック
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
        
        # チャット履歴からのサンプルデータを取得（analysis_resultから取得可能）
        # カテゴリーとセンチメントの分布から洞察を生成
        categories = analysis_result.get("category_distribution", {})
        sentiments = analysis_result.get("sentiment_distribution", {})
        questions = analysis_result.get("common_questions", [])
        
        # Gemini APIで詳細な分析を実行
        from modules.admin import model
        
        # Geminiモデルが初期化されていない場合のエラーハンドリング
        if model is None:
            raise HTTPException(status_code=500, detail="Geminiモデルが初期化されていません")
        
        analysis_prompt = f"""
        {prompt}
        
        # 分析データ
        
        ## カテゴリ分布:
        {json.dumps(categories, ensure_ascii=False, indent=2)}
        
        ## 感情分布:
        {json.dumps(sentiments, ensure_ascii=False, indent=2)}
        
        ## よくある質問（上位件）:
        {json.dumps(questions, ensure_ascii=False, indent=2)}
        
        ## 基本的な洞察:
        {analysis_result.get("insights", "")}
        
        上記のデータに基づいて、以下の6つのセクションに分けて詳細な分析を行ってください。
        各セクションは明確に区別できるよう、【セクション名】の形式で記載してください：
        
        【1. 頻出トピック/質問とその傾向分析】
        【2. 業務効率化の機会】
        【3. 社員のフラストレーションポイント】
        【4. 製品/サービス改善の示唆】
        【5. コミュニケーションギャップ】
        【6. 具体的な改善提案】
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
        
        # セクション分割の改善
        sections = [
            (r"【1\..*?頻出トピック.*?】|1\..*?頻出トピック|頻出トピック", "detailed_topic_analysis"),
            (r"【2\..*?業務効率化.*?】|2\..*?業務効率化|業務効率化", "efficiency_opportunities"),
            (r"【3\..*?フラストレーション.*?】|3\..*?フラストレーション|フラストレーション", "frustration_points"),
            (r"【4\..*?改善.*?示唆.*?】|4\..*?改善.*?示唆|製品.*?改善|サービス.*?改善", "improvement_suggestions"),
            (r"【5\..*?コミュニケーション.*?】|5\..*?コミュニケーション|コミュニケーション", "communication_gaps"),
            (r"【6\..*?具体的.*?改善提案.*?】|6\..*?具体的.*?改善|具体的.*?改善提案", "specific_recommendations")
        ]
        
        # テキストを行に分割
        lines = detailed_analysis_text.split("\n")
        current_section = None
        section_content = []
        
        for line in lines:
            matched = False
            
            # 各セクションのパターンをチェック
            for pattern, section_key in sections:
                if re.search(pattern, line, re.IGNORECASE):
                    # 前のセクションの内容を保存
                    if current_section and section_content:
                        detailed_analysis[current_section] = "\n".join(section_content).strip()
                    
                    # 新しいセクションを開始
                    current_section = section_key
                    section_content = []
                    matched = True
                    break
            
            # セクションヘッダー以外の行は現在のセクションに追加
            if not matched and current_section:
                section_content.append(line)
        
        # 最後のセクションを処理
        if current_section and section_content:
            detailed_analysis[current_section] = "\n".join(section_content).strip()
        
        # セクションが分割できなかった場合は、全テキストを最初のセクションに入れる
        if all(not value.strip() for value in detailed_analysis.values()):
            detailed_analysis["detailed_topic_analysis"] = detailed_analysis_text
            print("セクション分割に失敗したため、全文を最初のセクションに配置しました")
        
        # デバッグ情報を追加
        print(f"分析結果セクション:")
        for key, value in detailed_analysis.items():
            if value.strip():
                print(f"  {key}: {len(value)} 文字")
            else:
                print(f"  {key}: 空")
        
        return {
            "detailed_analysis": detailed_analysis
        }
        
    except Exception as e:
        import traceback
        print(f"詳細ビジネス分析エラー: {str(e)}")
        print(traceback.format_exc())
        
        # エラーの場合でも基本的な分析結果を返す
        return {
            "detailed_analysis": {
                "detailed_topic_analysis": f"分析処理中にエラーが発生しました: {str(e)}",
                "efficiency_opportunities": "エラーのため分析できませんでした。",
                "frustration_points": "エラーのため分析できませんでした。",
                "improvement_suggestions": "エラーのため分析できませんでした。",
                "communication_gaps": "エラーのため分析できませんでした。",
                "specific_recommendations": "システム管理者に連絡して、エラーログを確認してください。"
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
    """プラン履歴を取得する"""
    try:
        print(f"プラン履歴取得要求 - ユーザー: {current_user['email']} (ロール: {current_user['role']})")
        
        from modules.database import get_plan_history
        
        # 管理者・特別管理者は全てのプラン履歴を、一般ユーザーは自分の履歴のみを取得
        if current_user["role"] in ["admin"] or current_user["email"] in ["queue@queuefood.co.jp", "queue@queue-tech.jp"]:
            # 管理者または特別管理者は全履歴を取得
            history = get_plan_history(db=db)
        else:
            # 一般ユーザー（userロール含む）は自分の履歴のみを取得
            history = get_plan_history(user_id=current_user["id"], db=db)
        
        return {
            "success": True,
            "history": history,
            "count": len(history)
        }
        
    except Exception as e:
        print(f"プラン履歴取得エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"プラン履歴の取得に失敗しました: {str(e)}"
        )

# チャット履歴をCSV形式でダウンロードするエンドポイント（catch_allより前に配置）
@app.get("/chatbot/api/admin/chat-history/csv")
async def download_chat_history_csv(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """チャット履歴をCSV形式でダウンロードする"""
    try:
        print(f"CSVダウンロード開始 - ユーザー: {current_user['email']}")
        
        # 権限チェック（userロールも許可）
        is_admin = current_user["role"] == "admin"
        is_user = current_user["role"] == "user"
        is_special_admin = current_user["email"] in ["queue@queuefood.co.jp", "queue@queue-tech.jp"] and current_user.get("is_special_admin", False)
        
        # チャット履歴を直接Supabaseから取得
        try:
            if is_special_admin or is_admin:
                # 管理者または特別管理者の場合は全ユーザーのデータを取得
                print("管理者として全ユーザーのチャット履歴を取得")
                from supabase_adapter import select_data
                result = select_data("chat_history", columns="*")
                chat_history = result.data if result and result.data else []
            elif is_user:
                # userロールの場合は自分の会社のデータのみを取得
                print("userロールとして自分の会社のチャット履歴を取得")
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


# その他のルートパスをindex.htmlにリダイレクト（SPAのルーティング用）
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

# アプリケーションの実行
if __name__ == "__main__":
    import uvicorn
    from modules.config import get_port
    port = get_port()
    uvicorn.run(app, host="0.0.0.0", port=port, timeout_keep_alive=300)
