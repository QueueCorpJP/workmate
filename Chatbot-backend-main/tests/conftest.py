"""
テスト用の共通設定とフィクスチャ
"""
import pytest
import asyncio
import os
from typing import AsyncGenerator
from httpx import AsyncClient
from fastapi.testclient import TestClient
import asyncpg
from unittest.mock import Mock, AsyncMock

# テスト用の環境変数を設定
os.environ.update({
    'SUPABASE_URL': 'test_url',
    'SUPABASE_KEY': 'test_key',
    'GEMINI_API_KEY': 'test_gemini_key',
    'ENVIRONMENT': 'test'
})

from main import app
from modules.database import get_db
from supabase_adapter import get_supabase_client


@pytest.fixture(scope="session")
def event_loop():
    """セッション全体で使用するイベントループ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_supabase():
    """Supabaseクライアントのモック"""
    mock_client = Mock()
    mock_client.table = Mock()
    mock_client.table.return_value.select = Mock()
    mock_client.table.return_value.insert = Mock()
    mock_client.table.return_value.update = Mock()
    mock_client.table.return_value.delete = Mock()
    return mock_client


@pytest.fixture
def mock_db():
    """データベース接続のモック"""
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock()
    mock_conn.fetchrow = AsyncMock()
    mock_conn.execute = AsyncMock()
    return mock_conn


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """非同期HTTPクライアント"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def client():
    """同期HTTPクライアント"""
    return TestClient(app)


@pytest.fixture
def test_user_data():
    """テスト用ユーザーデータ"""
    return {
        "id": "test_user_id",
        "email": "test@example.com",
        "name": "Test User",
        "company_id": "test_company_id",
        "role": "user"
    }


@pytest.fixture
def test_company_data():
    """テスト用企業データ"""
    return {
        "id": "test_company_id",
        "name": "Test Company",
        "created_at": "2023-01-01T00:00:00Z"
    }


@pytest.fixture
def test_chat_data():
    """テスト用チャットデータ"""
    return {
        "user_message": "こんにちは",
        "bot_response": "こんにちは！何かお手伝いできることはありますか？",
        "user_id": "test_user_id",
        "company_id": "test_company_id"
    }


@pytest.fixture
def test_document_data():
    """テスト用ドキュメントデータ"""
    return {
        "id": "test_doc_id",
        "name": "test_document.pdf",
        "type": "pdf",
        "content": "テストドキュメントの内容",
        "uploaded_by": "test_user_id",
        "company_id": "test_company_id"
    }


@pytest.fixture(autouse=True)
def override_dependencies(mock_supabase, mock_db):
    """依存関係を自動的にモックで上書き"""
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides.clear()