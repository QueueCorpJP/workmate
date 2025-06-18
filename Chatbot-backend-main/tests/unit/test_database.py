"""
データベースモジュールのユニットテスト
"""
import pytest
from unittest.mock import AsyncMock, Mock
from modules.database import (
    get_all_users, create_user, get_demo_usage_stats, 
    get_user_by_email, update_usage_limits
)


@pytest.mark.unit
class TestDatabase:
    
    async def test_get_all_users_success(self, mock_db):
        """全ユーザー取得成功テスト"""
        mock_users = [
            {"id": "1", "email": "user1@test.com", "name": "User 1"},
            {"id": "2", "email": "user2@test.com", "name": "User 2"}
        ]
        mock_db.fetch.return_value = mock_users
        
        result = await get_all_users()
        
        assert len(result) == 2
        assert result[0]["email"] == "user1@test.com"
        mock_db.fetch.assert_called_once()
    
    async def test_create_user_success(self, mock_db, test_user_data):
        """ユーザー作成成功テスト"""
        mock_db.execute.return_value = None
        
        await create_user(
            test_user_data["id"],
            test_user_data["email"],
            "hashed_password",
            test_user_data["name"],
            test_user_data["company_id"],
            "creator_id"
        )
        
        assert mock_db.execute.call_count == 2  # users テーブルと usage_limits テーブル
    
    async def test_get_demo_usage_stats_success(self, mock_db):
        """デモ使用統計取得成功テスト"""
        mock_stats = {
            "total_users": 100,
            "total_documents": 50,
            "total_chats": 1000,
            "avg_response_time": 2.5
        }
        mock_db.fetchrow.return_value = mock_stats
        
        result = await get_demo_usage_stats()
        
        assert result["total_users"] == 100
        assert result["total_chats"] == 1000
        mock_db.fetchrow.assert_called_once()
    
    async def test_get_user_by_email_found(self, mock_db, test_user_data):
        """メールアドレスでユーザー取得成功"""
        mock_db.fetchrow.return_value = test_user_data
        
        result = await get_user_by_email(test_user_data["email"])
        
        assert result["id"] == test_user_data["id"]
        assert result["email"] == test_user_data["email"]
    
    async def test_get_user_by_email_not_found(self, mock_db):
        """メールアドレスでユーザー取得失敗"""
        mock_db.fetchrow.return_value = None
        
        result = await get_user_by_email("nonexistent@test.com")
        
        assert result is None
    
    async def test_update_usage_limits_success(self, mock_db):
        """使用量制限更新成功テスト"""
        mock_db.execute = AsyncMock()
        
        await update_usage_limits("user_id", document_limit=5, question_limit=20)
        
        mock_db.execute.assert_called()
    
    async def test_database_connection_error(self, mock_db):
        """データベース接続エラーテスト"""
        mock_db.fetch.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception):
            await get_all_users()
    
    async def test_transaction_rollback(self, mock_db):
        """トランザクションロールバックテスト"""
        mock_db.execute.side_effect = [None, Exception("Second query failed")]
        
        with pytest.raises(Exception):
            await create_user("id", "email", "pass", "name", "company", "creator")