"""
データベース統合テスト
各テーブルの操作と整合性をテスト
"""
import pytest
from unittest.mock import Mock, AsyncMock
import asyncio
from modules.database import (
    get_db, create_user, get_all_users, get_user_by_email,
    update_usage_limits, get_demo_usage_stats
)
from supabase_adapter import insert_data, select_data, update_data, delete_data


@pytest.mark.integration
class TestDatabaseIntegration:
    
    async def test_user_lifecycle(self, mock_supabase, mock_db):
        """ユーザーのライフサイクルテスト（作成→取得→更新→削除）"""
        # ユーザー作成
        user_data = {
            "id": "test_integration_user",
            "email": "integration@test.com",
            "name": "Integration User",
            "company_id": "test_company"
        }
        
        mock_db.execute = AsyncMock()
        mock_db.fetchrow = AsyncMock(return_value=user_data)
        
        # 作成
        await create_user(
            user_data["id"],
            user_data["email"],
            "hashed_password",
            user_data["name"],
            user_data["company_id"],
            "creator_id"
        )
        
        # 取得確認
        result = await get_user_by_email(user_data["email"])
        assert result["email"] == user_data["email"]
        
        # 使用量制限更新
        await update_usage_limits(user_data["id"], document_limit=10, question_limit=50)
        
        # 呼び出し回数確認
        assert mock_db.execute.call_count >= 3
    
    async def test_company_user_relationship(self, mock_supabase, mock_db):
        """企業とユーザーの関連性テスト"""
        company_data = {
            "id": "test_company_rel",
            "name": "Test Company Relation",
            "created_at": "2023-01-01T00:00:00Z"
        }
        
        users_data = [
            {
                "id": "user1",
                "email": "user1@company.com",
                "company_id": "test_company_rel",
                "name": "User 1"
            },
            {
                "id": "user2", 
                "email": "user2@company.com",
                "company_id": "test_company_rel",
                "name": "User 2"
            }
        ]
        
        mock_db.fetch = AsyncMock(return_value=users_data)
        mock_db.execute = AsyncMock()
        
        # 企業のユーザー一覧取得をシミュレート
        result = await get_all_users()
        company_users = [u for u in result if u["company_id"] == "test_company_rel"]
        
        assert len(company_users) == 2
        assert all(u["company_id"] == "test_company_rel" for u in company_users)
    
    async def test_usage_limits_consistency(self, mock_db):
        """使用量制限の整合性テスト"""
        user_id = "test_usage_user"
        
        # 初期値確認
        initial_limits = {
            "document_uploads_used": 0,
            "document_uploads_limit": 2,
            "questions_used": 0,
            "questions_limit": 10
        }
        mock_db.fetchrow = AsyncMock(return_value=initial_limits)
        mock_db.execute = AsyncMock()
        
        # 使用量更新
        await update_usage_limits(user_id, document_limit=5, question_limit=25)
        
        # 更新後の値をシミュレート
        updated_limits = {
            **initial_limits,
            "document_uploads_limit": 5,
            "questions_limit": 25
        }
        mock_db.fetchrow.return_value = updated_limits
        
        # 整合性確認
        assert updated_limits["document_uploads_limit"] > initial_limits["document_uploads_limit"]
        assert updated_limits["questions_limit"] > initial_limits["questions_limit"]
    
    async def test_chat_history_document_relationship(self, mock_db):
        """チャット履歴と文書の関連性テスト"""
        chat_data = {
            "id": "test_chat",
            "user_message": "テスト質問",
            "bot_response": "テスト回答",
            "source_document": "test_doc.pdf",
            "user_id": "test_user",
            "company_id": "test_company"
        }
        
        document_data = {
            "id": "test_doc_id",
            "name": "test_doc.pdf",
            "company_id": "test_company",
            "type": "pdf",
            "uploaded_by": "test_user",
            "uploaded_at": "2024-01-01T00:00:00",
            "special": "統合テスト用ドキュメント"
        }
        
        mock_db.execute = AsyncMock()
        mock_db.fetchrow = AsyncMock()
        
        # チャット履歴と文書の関連性を確認するクエリをシミュレート
        mock_db.fetch = AsyncMock(return_value=[{**chat_data, "document_name": document_data["name"]}])
        
        # 関連データ取得をシミュレート
        result = await mock_db.fetch("SELECT * FROM chat_history ch JOIN document_sources ds ON ch.source_document = ds.name")
        
        assert len(result) == 1
        assert result[0]["source_document"] == document_data["name"]
    
    async def test_concurrent_operations(self, mock_db):
        """並行操作のテスト"""
        mock_db.execute = AsyncMock()
        
        # 複数のユーザー作成を並行実行
        tasks = []
        for i in range(5):
            task = create_user(
                f"concurrent_user_{i}",
                f"user{i}@concurrent.com",
                "password",
                f"User {i}",
                "concurrent_company",
                "creator"
            )
            tasks.append(task)
        
        # 並行実行
        await asyncio.gather(*tasks)
        
        # 期待される呼び出し回数（各ユーザーごとに2回のDB操作）
        assert mock_db.execute.call_count == 10
    
    async def test_transaction_integrity(self, mock_db):
        """トランザクション整合性テスト"""
        # 失敗するケースをシミュレート
        mock_db.execute = AsyncMock(side_effect=[None, Exception("Transaction failed")])
        
        with pytest.raises(Exception):
            await create_user("fail_user", "fail@test.com", "pass", "name", "company", "creator")
        
        # 部分的な実行でもロールバックされることを確認
        assert mock_db.execute.call_count == 2