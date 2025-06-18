"""
チャットAPIエンドポイントのテスト
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from main import app


@pytest.mark.api
class TestChatEndpoints:
    
    def test_chat_endpoint_success(self, client, test_user_data):
        """チャットエンドポイント成功テスト"""
        chat_data = {
            "message": "こんにちは",
            "user_id": test_user_data["id"],
            "company_id": test_user_data["company_id"]
        }
        
        with patch('modules.chat.process_chat') as mock_process_chat:
            mock_process_chat.return_value = Mock(
                response="こんにちは！何かお手伝いできることはありますか？",
                sources=["document1.pdf", "document2.pdf"],
                category="greeting",
                sentiment="positive"
            )
            
            response = client.post("/chat", json=chat_data)
            
        assert response.status_code == 200
        result = response.json()
        assert "response" in result
        assert "sources" in result
        assert result["response"] == "こんにちは！何かお手伝いできることはありますか？"
    
    def test_chat_endpoint_invalid_input(self, client):
        """チャットエンドポイント無効入力テスト"""
        invalid_data = {
            "message": "",  # 空メッセージ
            "user_id": "",
            "company_id": ""
        }
        
        response = client.post("/chat", json=invalid_data)
        assert response.status_code == 400
    
    def test_chat_endpoint_missing_fields(self, client):
        """チャットエンドポイント必須フィールド欠如テスト"""
        incomplete_data = {
            "message": "テスト"
            # user_id と company_id が欠如
        }
        
        response = client.post("/chat", json=incomplete_data)
        assert response.status_code == 422
    
    def test_chat_endpoint_authentication_required(self, client):
        """認証が必要なチャットエンドポイントテスト"""
        # 認証なしでのアクセス
        response = client.post("/chat", json={"message": "test"})
        assert response.status_code in [401, 422]  # 認証エラーまたはバリデーションエラー
    
    def test_chat_history_endpoint(self, client, test_user_data):
        """チャット履歴取得エンドポイントテスト"""
        with patch('modules.admin.get_chat_history') as mock_get_history:
            mock_get_history.return_value = [
                {
                    "id": "1",
                    "user_message": "こんにちは",
                    "bot_response": "こんにちは！",
                    "timestamp": "2023-01-01T00:00:00Z"
                }
            ]
            
            response = client.get(f"/chat-history/{test_user_data['company_id']}")
            
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["user_message"] == "こんにちは"
    
    def test_chat_analysis_endpoint(self, client, test_user_data):
        """チャット分析エンドポイントテスト"""
        with patch('modules.admin.analyze_chats') as mock_analyze:
            mock_analyze.return_value = {
                "total_chats": 100,
                "avg_response_time": 2.5,
                "common_topics": ["挨拶", "質問", "手続き"],
                "sentiment_analysis": {
                    "positive": 60,
                    "neutral": 30,
                    "negative": 10
                }
            }
            
            response = client.get(f"/chat-analysis/{test_user_data['company_id']}")
            
        assert response.status_code == 200
        result = response.json()
        assert "total_chats" in result
        assert "sentiment_analysis" in result
        assert result["total_chats"] == 100