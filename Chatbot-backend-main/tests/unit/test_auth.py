"""
認証モジュールのユニットテスト
"""
import pytest
from unittest.mock import Mock, AsyncMock
from modules.auth import get_current_user, get_current_admin, register_new_user
from modules.models import UserResponse
from fastapi import HTTPException


@pytest.mark.unit
class TestAuth:
    
    async def test_get_current_user_valid_token(self, mock_supabase, test_user_data):
        """有効なトークンでユーザー取得成功"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
            data=test_user_data
        )
        
        result = await get_current_user("valid_token")
        assert result["id"] == test_user_data["id"]
        assert result["email"] == test_user_data["email"]
    
    async def test_get_current_user_invalid_token(self, mock_supabase):
        """無効なトークンでユーザー取得失敗"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
            data=None
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("invalid_token")
        assert exc_info.value.status_code == 401
    
    async def test_get_current_admin_success(self, mock_supabase, test_user_data):
        """管理者権限ユーザー取得成功"""
        admin_data = {**test_user_data, "role": "admin"}
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
            data=admin_data
        )
        
        result = await get_current_admin("admin_token")
        assert result["role"] == "admin"
    
    async def test_get_current_admin_not_admin(self, mock_supabase, test_user_data):
        """一般ユーザーで管理者権限取得失敗"""
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
            data=test_user_data
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin("user_token")
        assert exc_info.value.status_code == 403
    
    async def test_register_new_user_success(self, mock_supabase, mock_db):
        """新規ユーザー登録成功"""
        user_data = {
            "email": "new@example.com",
            "password": "password123",
            "name": "New User",
            "company_id": "test_company"
        }
        
        mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock(
            data=[{"id": "new_user_id", **user_data}]
        )
        mock_db.execute = AsyncMock()
        
        result = await register_new_user(user_data, "creator_id")
        assert result.email == user_data["email"]
        assert result.name == user_data["name"]
    
    async def test_register_new_user_duplicate_email(self, mock_supabase):
        """重複メールアドレスでの登録失敗"""
        user_data = {
            "email": "existing@example.com",
            "password": "password123",
            "name": "User",
            "company_id": "test_company"
        }
        
        mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("Email already exists")
        
        with pytest.raises(HTTPException) as exc_info:
            await register_new_user(user_data, "creator_id")
        assert exc_info.value.status_code == 400