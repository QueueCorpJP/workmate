"""
認証モジュール
ユーザー認証と権限管理を行います
"""
import uuid
import datetime
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .database import get_db, authenticate_user, create_user, get_usage_limits, check_user_exists, SupabaseConnection
from .email_service import email_service

logger = logging.getLogger(__name__)

security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security), db: SupabaseConnection = Depends(get_db)):
    """現在のユーザーを取得します"""
    user = authenticate_user(credentials.username, credentials.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なメールアドレスまたはパスワードです",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

def get_current_admin(user = Depends(get_current_user)):
    """現在の管理者ユーザーを取得します（特別管理者のみ）"""
    if user["email"] != "queue@queueu-tech.jp":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には特別管理者権限が必要です",
        )
    return user

def get_admin_or_user(user = Depends(get_current_user)):
    """現在のユーザーを取得します（管理者でなくても可）"""
    # 特定のメールアドレスを持つユーザーは特別な権限を持つ
    if user["email"] == "queue@queueu-tech.jp":
        user["is_special_admin"] = True
    else:
        user["is_special_admin"] = False
    
    # 社員アカウントは管理画面に完全にアクセス不可
    if user["role"] == "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="社員アカウントは管理画面にアクセスできません",
        )
    return user

def get_company_admin(user = Depends(get_current_user)):
    """会社の管理者ユーザーを取得します"""
    # 特定のメールアドレスを持つユーザーは特別な権限を持つ
    if user["email"] == "queue@queueu-tech.jp":
        user["is_special_admin"] = True
        return user
        
    # 会社IDがない場合はエラー
    if not user.get("company_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="会社に所属していないユーザーは会社管理機能にアクセスできません",
        )
    
    # 社員アカウントは管理機能にアクセスできない（admin_userは管理機能にアクセス可能）
    if user["role"] == "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="社員アカウントは管理機能にアクセスできません",
        )
    
    # admin_user、admin、userは会社の管理者として扱う
    return user

def get_user_with_delete_permission(user = Depends(get_current_user)):
    """削除権限を持つユーザーを取得します（admin_user, admin, 特別管理者）"""
    # 特定のメールアドレスを持つユーザーは特別な権限を持つ
    if user["email"] == "queue@queueu-tech.jp":
        user["is_special_admin"] = True
    else:
        user["is_special_admin"] = False
    
    # admin_userまたは特別管理者のみ削除権限を持つ
    if user["role"] != "admin_user" and not user.get("is_special_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者権限が必要です",
        )
    return user

def get_user_creation_permission(user = Depends(get_current_user)):
    """ユーザー作成権限を持つユーザーを取得します"""
    # 特定のメールアドレスを持つユーザーは特別な権限を持つ
    if user["email"] == "queue@queueu-tech.jp":
        user["is_special_admin"] = True
    else:
        user["is_special_admin"] = False
    
    # 特別管理者はadmin_userのみ作成可能
    # admin_userはuser・employeeを作成可能
    # userはemployeeを作成可能
    # employeeは作成権限なし
    if user["role"] not in ["admin_user", "user"] and not user.get("is_special_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作にはユーザー作成権限が必要です",
        )
    return user

def register_new_user(email: str, password: str, name: str, role: str = "user", db: SupabaseConnection = Depends(get_db)):
    """新しいユーザーを登録します"""
    if check_user_exists(email, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に登録されています",
        )
    
    user_id = create_user(email, password, name, role, "", db)
    
    # 🚀 アカウント作成通知メールを送信
    try:
        logger.info(f"アカウント作成メール送信開始: {email}")
        email_sent = email_service.send_account_creation_email(
            user_email=email,
            user_name=name,
            password=password,
            role=role
        )
        
        if email_sent:
            logger.info(f"✅ アカウント作成メール送信成功: {email}")
        else:
            logger.warning(f"⚠️ アカウント作成メール送信失敗: {email}")
            
    except Exception as e:
        logger.error(f"❌ メール送信エラー: {str(e)}")
        # メール送信失敗してもアカウント作成は継続
    
    return {
        "id": user_id,
        "email": email,
        "name": name,
        "role": role,
        "company_name": "",
        "created_at": datetime.datetime.now().isoformat()
    }

def check_usage_limits(user_id: str, limit_type: str, db: SupabaseConnection = Depends(get_db)):
    """利用制限をチェックします"""
    print(f"=== 利用制限チェック開始 ===")
    print(f"ユーザーID: {user_id}, 制限タイプ: {limit_type}")
    
    limits = get_usage_limits(user_id, db)
    print(f"取得した利用制限: {limits}")
    
    if not limits:
        print("利用制限情報が見つかりません")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーの利用制限情報が見つかりません",
        )
    
    # 無制限アカウントの場合は制限をチェックしない
    if limits["is_unlimited"]:
        print("無制限アカウントです")
        return {
            "allowed": True,
            "remaining": None,
            "is_unlimited": True
        }
    
    if limit_type == "document_upload":
        used = limits["document_uploads_used"]
        limit = limits["document_uploads_limit"]
        remaining = limit - used
        allowed = remaining > 0
        print(f"ドキュメントアップロード制限: 使用済み={used}, 制限={limit}, 残り={remaining}, 許可={allowed}")
    elif limit_type == "question":
        used = limits["questions_used"]
        limit = limits["questions_limit"]
        remaining = limit - used
        allowed = remaining > 0
        print(f"質問制限: 使用済み={used}, 制限={limit}, 残り={remaining}, 許可={allowed}")
    else:
        print(f"不明な制限タイプ: {limit_type}")
        raise ValueError(f"不明な制限タイプ: {limit_type}")
    
    result = {
        "allowed": allowed,
        "remaining": remaining,
        "is_unlimited": False,
        "used": used,
        "limit": limit
    }
    print(f"利用制限チェック結果: {result}")
    return result