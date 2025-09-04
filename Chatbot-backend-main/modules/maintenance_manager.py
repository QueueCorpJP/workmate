"""
メンテナンスモード管理モジュール
システムのメンテナンス状態を管理し、特定の管理者アカウントのみアクセス可能にします
"""

from datetime import datetime
from typing import Dict, Optional, List
from pydantic import BaseModel
from supabase_adapter import select_data, update_data, insert_data
from modules.database import SupabaseConnection
from modules.timezone_utils import create_timestamp_for_db

# メンテナンス管理者のメールアドレス（メンテナンス中でもアクセス可能）
MAINTENANCE_ADMINS = [
    "taichi.taniguchi@queue-tech.jp",
    "queue@queue-tech.jp"
]

class MaintenanceModeRequest(BaseModel):
    is_active: bool
    message: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class MaintenanceStatus(BaseModel):
    is_active: bool
    message: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    created_by: Optional[str] = None
    updated_at: str

class MaintenanceManager:
    """メンテナンスモード管理クラス"""
    
    def __init__(self, db: SupabaseConnection):
        self.db = db
    
    def is_maintenance_admin(self, email: str) -> bool:
        """ユーザーがメンテナンス管理者かどうかチェック"""
        return email in MAINTENANCE_ADMINS
    
    async def get_maintenance_status(self) -> MaintenanceStatus:
        """現在のメンテナンス状態を取得"""
        try:
            result = select_data(
                "maintenance_mode",
                order="created_at desc",
                limit=1
            )
            
            if result.success and result.data:
                data = result.data[0]
                return MaintenanceStatus(
                    is_active=data.get("is_active", False),
                    message=data.get("message", ""),
                    start_time=data.get("start_time"),
                    end_time=data.get("end_time"),
                    created_by=data.get("created_by"),
                    updated_at=data.get("updated_at", "")
                )
            else:
                # デフォルト状態を返す
                return MaintenanceStatus(
                    is_active=False,
                    message="メンテナンスは現在実行されていません",
                    updated_at=create_timestamp_for_db()
                )
        except Exception as e:
            print(f"メンテナンス状態取得エラー: {e}")
            return MaintenanceStatus(
                is_active=False,
                message="メンテナンス状態の取得に失敗しました",
                updated_at=create_timestamp_for_db()
            )
    
    async def set_maintenance_mode(self, request: MaintenanceModeRequest, admin_email: str) -> Dict:
        """メンテナンスモードを設定"""
        try:
            # 管理者権限チェック
            if not self.is_maintenance_admin(admin_email):
                raise Exception("メンテナンス管理権限がありません")
            
            # 新しいメンテナンス状態レコードを挿入
            maintenance_data = {
                "is_active": request.is_active,
                "message": request.message or ("メンテナンス中です。しばらくお待ちください。" if request.is_active else "メンテナンスが完了しました。"),
                "start_time": request.start_time,
                "end_time": request.end_time,
                "created_by": admin_email,
                "created_at": create_timestamp_for_db(),
                "updated_at": create_timestamp_for_db()
            }
            
            result = insert_data("maintenance_mode", maintenance_data)
            
            if result.success:
                status = "有効化" if request.is_active else "無効化"
                return {
                    "success": True,
                    "message": f"メンテナンスモードが{status}されました",
                    "maintenance_status": maintenance_data
                }
            else:
                raise Exception(f"データベース更新失敗: {result.error}")
                
        except Exception as e:
            print(f"メンテナンスモード設定エラー: {e}")
            return {
                "success": False,
                "message": f"メンテナンスモード設定に失敗しました: {str(e)}"
            }
    
    async def check_user_access(self, user_email: str) -> Dict:
        """ユーザーのアクセス権限をチェック"""
        try:
            # メンテナンス管理者は常にアクセス可能
            if self.is_maintenance_admin(user_email):
                return {
                    "allowed": True,
                    "is_maintenance_admin": True,
                    "reason": "メンテナンス管理者"
                }
            
            # メンテナンス状態を確認
            maintenance_status = await self.get_maintenance_status()
            
            if maintenance_status.is_active:
                return {
                    "allowed": False,
                    "is_maintenance_admin": False,
                    "maintenance_message": maintenance_status.message,
                    "reason": "メンテナンス中"
                }
            else:
                return {
                    "allowed": True,
                    "is_maintenance_admin": False,
                    "reason": "通常運用中"
                }
                
        except Exception as e:
            print(f"アクセス権限チェックエラー: {e}")
            # エラー時は安全のためアクセス拒否（管理者は除く）
            if self.is_maintenance_admin(user_email):
                return {
                    "allowed": True,
                    "is_maintenance_admin": True,
                    "reason": "メンテナンス管理者（エラー時フォールバック）"
                }
            else:
                return {
                    "allowed": False,
                    "is_maintenance_admin": False,
                    "maintenance_message": "システムにアクセスできません。しばらくお待ちください。",
                    "reason": "システムエラー"
                }
