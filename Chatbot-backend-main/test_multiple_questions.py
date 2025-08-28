"""
🧪 複数質問同時処理テストスクリプト
Enhanced Multi Gemini Clientのテスト
"""

import asyncio
import sys
import time
import logging
from typing import List, Dict, Any

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.append('.')

async def test_multiple_questions():
    """複数質問同時処理のテスト"""
    try:
        from modules.enhanced_multi_client import get_enhanced_multi_gemini_client, enhanced_multi_gemini_available
        
        print("="*80)
        print("🧪 Enhanced Multi Gemini Client テスト開始")
        print("="*80)
        
        # 利用可能性チェック
        if not enhanced_multi_gemini_available():
            print("❌ Enhanced Multi Gemini Client が利用できません")
            return
        
        # クライアント取得
        client = get_enhanced_multi_gemini_client(max_concurrent_requests=3)
        await client.initialize()
        
        print("✅ Enhanced Multi Gemini Client 初期化完了")
        
        # テスト用質問リスト
        test_questions = [
            {
                "prompt": "こんにちは。今日の天気はどうですか？",
                "user_id": "user1",
                "company_id": "test_company"
            },
            {
                "prompt": "Pythonでリストを作成する方法を教えてください。",
                "user_id": "user2", 
                "company_id": "test_company"
            },
            {
                "prompt": "機械学習とは何ですか？簡単に説明してください。",
                "user_id": "user3",
                "company_id": "test_company"
            },
            {
                "prompt": "日本の首都はどこですか？",
                "user_id": "user4",
                "company_id": "test_company"
            },
            {
                "prompt": "1+1は何ですか？",
                "user_id": "user5",
                "company_id": "test_company"
            }
        ]
        
        print(f"📝 テスト質問数: {len(test_questions)}件")
        print()
        
        # テスト1: 単一質問処理
        print("【テスト1】単一質問処理")
        print("-" * 40)
        
        start_time = time.time()
        result = await client.generate_content_async(
            prompt=test_questions[0]["prompt"],
            user_id=test_questions[0]["user_id"],
            company_id=test_questions[0]["company_id"],
            timeout=60.0
        )
        end_time = time.time()
        
        if result:
            print(f"✅ 単一質問処理成功 ({end_time - start_time:.2f}秒)")
            # レスポンスの最初の50文字を表示
            if 'candidates' in result and result['candidates']:
                response_text = result['candidates'][0]['content']['parts'][0]['text']
                print(f"📄 応答: {response_text[:100]}...")
        else:
            print("❌ 単一質問処理失敗")
        
        print()
        
        # テスト2: 複数質問同時処理
        print("【テスト2】複数質問同時処理")
        print("-" * 40)
        
        start_time = time.time()
        results = await client.generate_multiple_content(test_questions, timeout=120.0)
        end_time = time.time()
        
        print(f"⏱️ 処理時間: {end_time - start_time:.2f}秒")
        print(f"📊 結果: {len([r for r in results if r is not None])}/{len(results)}件成功")
        
        for i, result in enumerate(results):
            if result:
                print(f"  ✅ 質問{i+1}: 成功")
            else:
                print(f"  ❌ 質問{i+1}: 失敗")
        
        print()
        
        # テスト3: 状態確認
        print("【テスト3】システム状態確認")
        print("-" * 40)
        
        status = await client.get_status()
        print("📊 システム状態:")
        print(f"  - Enhanced Client初期化: {status['enhanced_client']['is_initialized']}")
        print(f"  - 最大同時処理数: {status['enhanced_client']['max_concurrent_requests']}")
        print(f"  - キューサイズ: {status['queue_manager']['queue_size']}")
        print(f"  - 処理中: {status['queue_manager']['processing_count']}")
        print(f"  - 完了数: {status['queue_manager']['completed_count']}")
        print(f"  - 失敗数: {status['queue_manager']['failed_count']}")
        print(f"  - 平均処理時間: {status['queue_manager']['avg_processing_time']:.2f}秒")
        print(f"  - 利用可能APIキー数: {len(status['base_client']['api_keys'])}")
        
        print()
        print("="*80)
        print("🎉 テスト完了")
        print("="*80)
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()

async def test_sequential_vs_parallel():
    """逐次処理 vs 並列処理の比較テスト"""
    try:
        from modules.enhanced_multi_client import get_enhanced_multi_gemini_client
        
        print("\n" + "="*80)
        print("🏁 逐次処理 vs 並列処理 比較テスト")
        print("="*80)
        
        client = get_enhanced_multi_gemini_client()
        await client.initialize()
        
        test_prompts = [
            "1+1は何ですか？",
            "2+2は何ですか？", 
            "3+3は何ですか？"
        ]
        
        # 逐次処理テスト
        print("【逐次処理】")
        start_time = time.time()
        for i, prompt in enumerate(test_prompts):
            result = await client.generate_content_async(prompt, timeout=60.0)
            if result:
                print(f"  ✅ 質問{i+1}完了")
            else:
                print(f"  ❌ 質問{i+1}失敗")
        sequential_time = time.time() - start_time
        print(f"⏱️ 逐次処理時間: {sequential_time:.2f}秒")
        
        # 並列処理テスト
        print("\n【並列処理】")
        requests = [{"prompt": prompt} for prompt in test_prompts]
        start_time = time.time()
        results = await client.generate_multiple_content(requests, timeout=120.0)
        parallel_time = time.time() - start_time
        print(f"⏱️ 並列処理時間: {parallel_time:.2f}秒")
        
        # 結果比較
        improvement = ((sequential_time - parallel_time) / sequential_time) * 100
        print(f"\n📈 並列処理による改善: {improvement:.1f}% 高速化")
        
    except Exception as e:
        print(f"❌ 比較テストエラー: {e}")

if __name__ == "__main__":
    asyncio.run(test_multiple_questions())
    asyncio.run(test_sequential_vs_parallel())

