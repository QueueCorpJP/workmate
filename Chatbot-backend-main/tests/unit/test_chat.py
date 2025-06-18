"""
チャットモジュールのユニットテスト
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from modules.chat import process_chat
from modules.models import ChatMessage


@pytest.mark.unit
class TestChat:
    
    @patch('modules.chat.get_knowledge_base_info')
    @patch('modules.chat.model')
    async def test_process_chat_success(self, mock_model, mock_knowledge, mock_db, test_user_data):
        """チャット処理成功テスト"""
        chat_message = ChatMessage(
            message="こんにちは",
            user_id=test_user_data["id"],
            company_id=test_user_data["company_id"]
        )
        
        mock_knowledge.return_value = ["関連文書1", "関連文書2"]
        mock_model.generate_content.return_value.text = "こんにちは！何かお手伝いできることはありますか？"
        mock_db.execute = AsyncMock()
        
        result = await process_chat(chat_message)
        
        assert result.response == "こんにちは！何かお手伝いできることはありますか？"
        assert len(result.sources) > 0
        mock_db.execute.assert_called()
    
    @patch('modules.chat.get_knowledge_base_info')
    async def test_process_chat_no_knowledge_base(self, mock_knowledge, mock_db, test_user_data):
        """ナレッジベースなしでのチャット処理"""
        chat_message = ChatMessage(
            message="テスト質問",
            user_id=test_user_data["id"],
            company_id=test_user_data["company_id"]
        )
        
        mock_knowledge.return_value = []
        mock_db.execute = AsyncMock()
        
        result = await process_chat(chat_message)
        
        assert "申し訳ございませんが" in result.response
        assert len(result.sources) == 0
    
    @patch('modules.chat.model')
    async def test_process_chat_api_error(self, mock_model, mock_db, test_user_data):
        """API エラー時のテスト"""
        chat_message = ChatMessage(
            message="テスト質問",
            user_id=test_user_data["id"],
            company_id=test_user_data["company_id"]
        )
        
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_db.execute = AsyncMock()
        
        result = await process_chat(chat_message)
        
        assert "申し訳ございませんが" in result.response
        assert "エラーが発生しました" in result.response
    
    async def test_process_chat_empty_message(self, mock_db, test_user_data):
        """空メッセージのテスト"""
        chat_message = ChatMessage(
            message="",
            user_id=test_user_data["id"],
            company_id=test_user_data["company_id"]
        )
        
        result = await process_chat(chat_message)
        
        assert "質問を入力してください" in result.response
    
    async def test_process_chat_long_message(self, mock_db, test_user_data):
        """長すぎるメッセージのテスト"""
        long_message = "テスト" * 1000  # 非常に長いメッセージ
        chat_message = ChatMessage(
            message=long_message,
            user_id=test_user_data["id"],
            company_id=test_user_data["company_id"]
        )
        
        result = await process_chat(chat_message)
        
        assert "メッセージが長すぎます" in result.response or result.response is not None