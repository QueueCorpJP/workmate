"""
パフォーマンステスト
チャット機能の応答時間とスループットテスト
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor
import statistics


@pytest.mark.performance
class TestPerformance:
    
    async def test_chat_response_time(self, async_client):
        """チャット応答時間テスト"""
        chat_data = {
            "message": "パフォーマンステストメッセージ",
            "user_id": "perf_test_user",
            "company_id": "perf_test_company"
        }
        
        response_times = []
        
        with patch('modules.chat.process_chat') as mock_process_chat:
            mock_process_chat.return_value = Mock(
                response="テスト応答",
                sources=[],
                category="test",
                sentiment="neutral"
            )
            
            # 10回のリクエストで応答時間を測定
            for _ in range(10):
                start_time = time.time()
                response = await async_client.post("/chat", json=chat_data)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_times.append(end_time - start_time)
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            # 平均応答時間が3秒以下であることを確認
            assert avg_response_time < 3.0, f"平均応答時間が遅すぎます: {avg_response_time:.2f}秒"
            # 最大応答時間が5秒以下であることを確認
            assert max_response_time < 5.0, f"最大応答時間が遅すぎます: {max_response_time:.2f}秒"
    
    async def test_concurrent_chat_requests(self, async_client):
        """並行チャットリクエストテスト"""
        chat_data = {
            "message": "並行テストメッセージ",
            "user_id": "concurrent_user",
            "company_id": "concurrent_company"
        }
        
        with patch('modules.chat.process_chat') as mock_process_chat:
            mock_process_chat.return_value = Mock(
                response="並行テスト応答",
                sources=[],
                category="test",
                sentiment="neutral"
            )
            
            # 10個の並行リクエストを作成
            tasks = []
            start_time = time.time()
            
            for i in range(10):
                task_data = {**chat_data, "message": f"並行メッセージ {i}"}
                task = async_client.post("/chat", json=task_data)
                tasks.append(task)
            
            # すべてのタスクを並行実行
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            total_time = end_time - start_time
            successful_responses = [r for r in responses if not isinstance(r, Exception) and hasattr(r, 'status_code') and r.status_code == 200]
            
            # 10個の並行リクエストが10秒以内に完了することを確認
            assert total_time < 10.0, f"並行リクエストの処理時間が遅すぎます: {total_time:.2f}秒"
            # 少なくとも80%のリクエストが成功することを確認
            assert len(successful_responses) >= 8, f"成功したリクエスト数が少なすぎます: {len(successful_responses)}/10"
    
    async def test_database_query_performance(self, mock_db):
        """データベースクエリパフォーマンステスト"""
        from modules.database import get_all_users, get_user_by_email
        
        # 大量のユーザーデータをシミュレート
        mock_users = [
            {"id": f"user_{i}", "email": f"user{i}@test.com", "name": f"User {i}"}
            for i in range(1000)
        ]
        mock_db.fetch.return_value = mock_users
        mock_db.fetchrow.return_value = mock_users[0] if mock_users else None
        
        # クエリ実行時間を測定
        start_time = time.time()
        result = await get_all_users()
        end_time = time.time()
        
        query_time = end_time - start_time
        
        # 大量データ取得が1秒以内に完了することを確認
        assert query_time < 1.0, f"データベースクエリが遅すぎます: {query_time:.2f}秒"
        assert len(result) == 1000
        
        # 単一ユーザー取得のパフォーマンス
        start_time = time.time()
        user = await get_user_by_email("user1@test.com")
        end_time = time.time()
        
        single_query_time = end_time - start_time
        assert single_query_time < 0.1, f"単一ユーザークエリが遅すぎます: {single_query_time:.2f}秒"
    
    def test_memory_usage(self, client):
        """メモリ使用量テスト"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 大量のリクエストを送信
        for i in range(100):
            response = client.post("/chat", json={
                "message": f"メモリテストメッセージ {i}",
                "user_id": "memory_test_user",
                "company_id": "memory_test_company"
            })
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # メモリ増加が100MB以下であることを確認
        assert memory_increase < 100, f"メモリ使用量の増加が大きすぎます: {memory_increase:.2f}MB"
    
    async def test_large_document_processing(self, async_client):
        """大きなドキュメント処理のパフォーマンステスト"""
        # 大きなテキストデータをシミュレート
        large_text = "これは大きなドキュメントのテストです。" * 1000  # 約50KB
        
        files = {
            "file": ("large_document.txt", large_text.encode(), "text/plain")
        }
        
        start_time = time.time()
        response = await async_client.post("/upload-document", files=files)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # 大きなドキュメントの処理が30秒以内に完了することを確認
        assert processing_time < 30.0, f"大きなドキュメント処理が遅すぎます: {processing_time:.2f}秒"
    
    async def test_api_throughput(self, async_client):
        """APIスループットテスト"""
        requests_per_second_target = 10  # 目標: 10 requests/second
        test_duration = 5  # 5秒間テスト
        
        chat_data = {
            "message": "スループットテスト",
            "user_id": "throughput_user",
            "company_id": "throughput_company"
        }
        
        with patch('modules.chat.process_chat') as mock_process_chat:
            mock_process_chat.return_value = Mock(
                response="スループットテスト応答",
                sources=[],
                category="test",
                sentiment="neutral"
            )
            
            successful_requests = 0
            start_time = time.time()
            
            while time.time() - start_time < test_duration:
                try:
                    response = await async_client.post("/chat", json=chat_data)
                    if response.status_code == 200:
                        successful_requests += 1
                except Exception:
                    pass  # エラーは無視して続行
            
            end_time = time.time()
            actual_duration = end_time - start_time
            actual_rps = successful_requests / actual_duration
            
            # 目標スループットの50%以上を達成することを確認
            minimum_rps = requests_per_second_target * 0.5
            assert actual_rps >= minimum_rps, f"スループットが低すぎます: {actual_rps:.2f} RPS (目標: {minimum_rps:.2f} RPS)"