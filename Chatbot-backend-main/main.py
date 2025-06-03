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
from fastapi.responses import FileResponse, JSONResponse
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
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (user_data.email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="このメールアドレスは既に登録されています"
            )
        
        # 特別な管理者（queue@queuefood.co.jp）の場合はロールを指定できる
        if current_user["email"] == "queue@queuefood.co.jp" and current_user.get("is_special_admin", False):
            # user_dataからロールを取得（デフォルトは"employee"）
            role = user_data.role if hasattr(user_data, "role") and user_data.role in ["user", "employee"] else "employee"
            
            # create_user関数を直接呼び出す（特別管理者が作成するアカウントは常に本番版）
            user_id = create_user(
                email=user_data.email,
                password=user_data.password,
                name=name,
                role=role,
                company_id=None,
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
            # 通常のユーザーの場合は社員アカウントとして登録（管理画面にアクセスできない）
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
    if current_user["email"] == "queue@queuefood.co.jp" and current_user.get("is_special_admin", False):
        # 特別な管理者の場合は全ユーザーのデータを取得
        return await get_chat_history(None, db)
    else:
        # 通常のユーザーの場合は自分のデータのみを取得
        user_id = current_user["id"]
        return await get_chat_history(user_id, db)

# チャット分析エンドポイント
@app.get("/chatbot/api/admin/analyze-chats")
async def admin_analyze_chats(current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """チャット履歴を分析する"""
    try:
        # 特別な管理者（queue@queuefood.co.jp）の場合は全ユーザーのデータを分析できるようにする
        if current_user["email"] == "queue@queuefood.co.jp" and current_user.get("is_special_admin", False):
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
        is_special_admin = current_user["email"] == "queue@queuefood.co.jp" and current_user.get("is_special_admin", False)
        
        # プロンプトを取得
        prompt = request.get("prompt", "")
        
        # 通常の分析結果を取得
        if is_special_admin:
            analysis_result = await analyze_chats(None, db)
        else:
            analysis_result = await analyze_chats(current_user["id"], db)
        
        # チャット履歴からのサンプルデータを取得（analysis_resultから取得可能）
        # カテゴリーとセンチメントの分布から洞察を生成
        categories = analysis_result.get("category_distribution", {})
        sentiments = analysis_result.get("sentiment_distribution", {})
        questions = analysis_result.get("common_questions", [])
        
        # Gemini APIで詳細な分析を実行
        from modules.admin import model
        
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
        """
        
        # Gemini APIによる詳細分析
        analysis_response = model.generate_content(analysis_prompt)
        detailed_analysis_text = analysis_response.text
        
        # 詳細分析の結果をセクションごとに分割して整形
        # 実際のプロンプトに合わせてセクション分割のルールを調整する必要があります
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
        
        # テキスト全体から各セクションを抽出する簡易的な方法
        # より高度な抽出が必要な場合は、正規表現やセクション名の検索方法を調整してください
        sections = [
            ("頻出トピック", "detailed_topic_analysis"),
            ("業務効率化", "efficiency_opportunities"),
            ("フラストレーション", "frustration_points"),
            ("改善", "improvement_suggestions"),
            ("コミュニケーションギャップ", "communication_gaps"),
            ("具体的な改善提案", "specific_recommendations")
        ]
        
        # 正規表現を使ってセクションを検出
        current_section = None
        lines = detailed_analysis_text.split("\n")
        section_content = []
        
        for line in lines:
            matched = False
            for keyword, section_key in sections:
                if keyword in line and (line.startswith("#") or line.startswith("**") or line.startswith(":")):
                    if current_section:
                        detailed_analysis[current_section] = "\n".join(section_content).strip()
                    current_section = section_key
                    section_content = []
                    matched = True
                    break
            
            if not matched and current_section:
                section_content.append(line)
        
        # 最後のセクションを処理
        if current_section and section_content:
            detailed_analysis[current_section] = "\n".join(section_content).strip()
        
        # 何もセクションに当てはまらなかった場合は、最初のキーに全テキストを入れる
        if all(value == "" for value in detailed_analysis.values()):
            detailed_analysis["detailed_topic_analysis"] = detailed_analysis_text
        
        return {
            "detailed_analysis": detailed_analysis
        }
        
    except Exception as e:
        import traceback
        print(f"詳細ビジネス分析エラー: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# 社員詳細情報を取得するエンドポイント
@app.get("/chatbot/api/admin/employee-details/{employee_id}", response_model=List[ChatHistoryItem])
async def admin_get_employee_details(employee_id: str, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """特定の社員の詳細なチャット履歴を取得する"""
    # 特別な管理者（queue@queuefood.co.jp）の場合は全ユーザーのデータを取得できるようにする
    is_special_admin = current_user["email"] == "queue@queuefood.co.jp" and current_user.get("is_special_admin", False)
    
    # ユーザーIDを渡して権限チェックを行う
    return await get_employee_details(employee_id, db, current_user["id"])

# 会社の全社員情報を取得するエンドポイント
@app.get("/chatbot/api/admin/company-employees", response_model=List[dict])
async def admin_get_company_employees(current_user = Depends(get_company_admin), db: SupabaseConnection = Depends(get_db)):
    """会社の全社員情報を取得する"""
    # adminロールのユーザーは全ユーザーのデータを取得できるようにする
    is_admin = current_user["role"] == "admin"
    is_special_admin = current_user["email"] == "queue@queuefood.co.jp" and current_user.get("is_special_admin", False)
    
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
async def admin_get_employee_usage(current_user = Depends(get_company_admin), db: SupabaseConnection = Depends(get_db)):
    """社員ごとの利用状況を取得する"""
    # adminロールのユーザーは全ユーザーのデータを取得できるようにする
    is_admin = current_user["role"] == "admin"
    is_special_admin = current_user["email"] == "queue@queuefood.co.jp" and current_user.get("is_special_admin", False)
    
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
    is_special_admin = current_user["email"] == "queue@queuefood.co.jp" and current_user.get("is_special_admin", False)
    
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
    """デモ版から有料プランにアップグレードする"""
    try:
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
        
        # 実際の決済処理（今回はモック）
        # 本番環境では Stripe や PayPal などの決済サービスと連携
        payment_success = True  # モックとして成功とする
        
        if payment_success:
            # ユーザーのプランを更新
            from supabase_adapter import update_data, select_data
            from modules.database import update_created_accounts_status
            
            # 現在の利用制限を取得（変更前の状態を確認）
            current_limits_result = select_data("usage_limits", filters={"user_id": user_id})
            was_unlimited = False
            if current_limits_result and current_limits_result.data:
                was_unlimited = bool(current_limits_result.data[0].get("is_unlimited", False))
            
            # usage_limitsテーブルを更新
            update_data("usage_limits", {
                "is_unlimited": True,
                "questions_limit": plan["questions_limit"] if plan["questions_limit"] != -1 else 999999,
                "document_uploads_limit": plan["uploads_limit"] if plan["uploads_limit"] != -1 else 999999,
            }, "user_id", user_id)
            
            # ユーザーテーブルにプラン情報を追加（roleを更新）
            update_data("users", {
                "role": "user"  # デモ版からuserプランに変更
            }, "id", user_id)
            
            # デモ版から本番版に切り替わった場合、作成したアカウントも同期
            if not was_unlimited:
                updated_count = update_created_accounts_status(user_id, True, db)
                print(f"プラン変更により {updated_count} 個の子アカウントを本番版に更新しました")
            
            return UpgradePlanResponse(
                success=True,
                message=f"{plan['name']}へのアップグレードが完了しました",
                plan_id=request.plan_id,
                user_id=user_id,
                payment_url=None
            )
        else:
            raise HTTPException(status_code=400, detail="決済処理に失敗しました")
            
    except Exception as e:
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

# その他のルートパスをindex.htmlにリダイレクト（SPAのルーティング用）
@app.get("/{full_path:path}", include_in_schema=False)
async def catch_all(full_path: str):
    print(f"catch_all handler called with path: {full_path}")
    
    # APIエンドポイントはスキップ（/apiで始まるパスはAPIエンドポイントとして処理）
    if full_path.startswith("api/"):
        # APIエンドポイントの場合は404を返す
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # SPAルーティング用にindex.htmlを返す
    index_path = os.path.join(frontend_build_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Not Found")

@app.post("/chatbot/api/admin/update-user-status/{user_id}", response_model=dict)
async def admin_update_user_status(user_id: str, request: dict, current_user = Depends(get_admin_or_user), db: SupabaseConnection = Depends(get_db)):
    """管理者によるユーザーステータス変更"""
    # adminロールまたは特別な管理者のみが実行可能
    is_admin = current_user["role"] == "admin"
    is_special_admin = current_user["email"] == "queue@queuefood.co.jp" and current_user.get("is_special_admin", False)
    
    if not (is_admin or is_special_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者権限が必要です"
        )
    
    try:
        new_is_unlimited = bool(request.get("is_unlimited", False))
        
        # ユーザーの存在確認
        user_result = select_data("users", filters={"id": user_id})
        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたユーザーが見つかりません"
            )
        
        user = user_result.data[0]
        
        # 現在の利用制限を取得
        current_limits_result = select_data("usage_limits", filters={"user_id": user_id})
        if not current_limits_result or not current_limits_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーの利用制限情報が見つかりません"
            )
        
        current_limits = current_limits_result.data[0]
        was_unlimited = bool(current_limits.get("is_unlimited", False))
        
        # ステータスに変更がない場合は何もしない
        if was_unlimited == new_is_unlimited:
            return {
                "message": f"ユーザー {user['email']} のステータスは既に{'本番版' if new_is_unlimited else 'デモ版'}です",
                "user_id": user_id,
                "updated_children": 0
            }
        
        # 利用制限を更新
        update_data("usage_limits", {
            "is_unlimited": new_is_unlimited,
            "questions_limit": 999999 if new_is_unlimited else 10,
            "document_uploads_limit": 999999 if new_is_unlimited else 2
        }, "user_id", user_id)
        
        # 作成したアカウントも同期
        from modules.database import update_created_accounts_status
        updated_count = update_created_accounts_status(user_id, new_is_unlimited, db)
        
        return {
            "message": f"ユーザー {user['email']} のステータスを{'本番版' if new_is_unlimited else 'デモ版'}に変更しました",
            "user_id": user_id,
            "updated_children": updated_count
        }
        
    except HTTPException as e:
        raise
    except Exception as e:
        print(f"ユーザーステータス変更エラー: {str(e)}")
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

# アプリケーションの実行
if __name__ == "__main__":
    import uvicorn
    from modules.config import get_port
    port = get_port()
    uvicorn.run(app, host="0.0.0.0", port=port, timeout_keep_alive=300)
