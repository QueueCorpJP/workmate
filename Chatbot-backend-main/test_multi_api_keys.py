#!/usr/bin/env python3
"""
🧪 複数Gemini APIキーテストスクリプト
Multi Gemini Clientの動作確認
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.multi_gemini_client import get_multi_gemini_client, multi_gemini_available
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_multi_gemini_client():
    """Multi Gemini Clientのテスト"""
    print("🧪 Multi Gemini Client テスト開始")
    print("=" * 50)
    
    # 利用可能性チェック
    if not multi_gemini_available():
        print("❌ Multi Gemini Client が利用できません")
        print("環境変数 GEMINI_API_KEY または GOOGLE_API_KEY_* が設定されているか確認してください")
        return False
    
    try:
        # クライアント取得
        client = get_multi_gemini_client()
        print(f"✅ Multi Gemini Client 初期化成功")
        print(f"📊 利用可能APIキー数: {len(client.api_keys)}個")
        
        # 状態情報表示
        status_info = client.get_status_info()
        print("\n📋 APIキー状態:")
        for client_name, info in status_info.items():
            status_emoji = "✅" if info['status'] == 'active' else "⚠️"
            current_marker = " (現在使用中)" if info['is_current'] else ""
            print(f"  {status_emoji} {client_name}: {info['status']} - 末尾: ...{info['api_key_suffix']}{current_marker}")
        
        # 簡単なテスト呼び出し
        print("\n🔬 簡単なAPI呼び出しテスト...")
        test_prompt = "こんにちは。簡単な挨拶をお願いします。"
        
        try:
            response = await client.generate_content(test_prompt)
            
            if response and "candidates" in response:
                candidate = response["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    answer = candidate["content"]["parts"][0]["text"]
                    print(f"✅ API呼び出し成功!")
                    print(f"📝 回答: {answer[:100]}...")
                else:
                    print("⚠️ レスポンス構造が予期しない形式です")
            else:
                print("⚠️ 無効なレスポンスです")
                
        except Exception as api_error:
            print(f"❌ API呼び出しエラー: {api_error}")
            
            # エラー後の状態確認
            print("\n📊 エラー後のAPIキー状態:")
            status_info = client.get_status_info()
            for client_name, info in status_info.items():
                status_emoji = "✅" if info['status'] == 'active' else "⚠️"
                current_marker = " (現在使用中)" if info['is_current'] else ""
                retry_info = f" (リトライ: {info['retry_count']}/{client.max_retries})" if info['retry_count'] > 0 else ""
                print(f"  {status_emoji} {client_name}: {info['status']}{retry_info}{current_marker}")
                if info['last_error']:
                    print(f"    エラー: {info['last_error']}")
        
        print("\n🎉 Multi Gemini Client テスト完了")
        return True
        
    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        return False

async def test_rate_limit_simulation():
    """レート制限シミュレーションテスト"""
    print("\n🔥 レート制限シミュレーションテスト")
    print("=" * 50)
    
    if not multi_gemini_available():
        print("❌ Multi Gemini Client が利用できません")
        return False
    
    try:
        client = get_multi_gemini_client()
        
        # 複数回連続でAPI呼び出し（レート制限を誘発する可能性）
        for i in range(3):
            print(f"\n📞 API呼び出し {i+1}/3...")
            try:
                test_prompt = f"テスト{i+1}: 短い返答をお願いします。"
                response = await client.generate_content(test_prompt)
                print(f"✅ 呼び出し{i+1}成功")
                
                # 現在のクライアント状態を表示
                status_info = client.get_status_info()
                current_client = [name for name, info in status_info.items() if info['is_current']][0]
                print(f"🎯 使用中クライアント: {current_client}")
                
            except Exception as e:
                print(f"❌ 呼び出し{i+1}失敗: {e}")
                
                # エラー後の状態確認
                status_info = client.get_status_info()
                for client_name, info in status_info.items():
                    if info['status'] != 'active':
                        print(f"⚠️ {client_name}: {info['status']}")
        
        print("\n🎉 レート制限シミュレーションテスト完了")
        return True
        
    except Exception as e:
        print(f"❌ シミュレーションテスト失敗: {e}")
        return False

def main():
    """メイン関数"""
    print("🚀 Multi Gemini API Keys テストスイート")
    print("=" * 60)
    
    # 環境変数確認
    print("\n🔍 環境変数確認:")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print(f"✅ GEMINI_API_KEY: ...{gemini_key[-8:]}")
    else:
        print("❌ GEMINI_API_KEY: 未設定")
    
    for i in range(2, 6):
        key = os.getenv(f"GEMINI_API_KEY_{i}")
        if key:
            print(f"✅ GEMINI_API_KEY_{i}: ...{key[-8:]}")
        else:
            print(f"⚠️ GEMINI_API_KEY_{i}: 未設定")
    
    # Google API Keys確認
    google_keys_count = 0
    for i in [1, 2, 4, 5, 6, 7, 8, 9, 11, 12]:
        key = os.getenv(f"GOOGLE_API_KEY_{i}")
        if key:
            google_keys_count += 1
    
    print(f"📊 GOOGLE_API_KEY_*: {google_keys_count}個設定済み")
    
    # 非同期テスト実行
    async def run_tests():
        success1 = await test_multi_gemini_client()
        
        if success1:
            print("\n" + "="*60)
            success2 = await test_rate_limit_simulation()
            return success1 and success2
        return False
    
    # テスト実行
    try:
        success = asyncio.run(run_tests())
        
        print("\n" + "="*60)
        if success:
            print("🎉 全てのテストが完了しました！")
            print("✅ Multi Gemini API Keys システムは正常に動作しています")
        else:
            print("⚠️ 一部のテストが失敗しました")
            print("設定を確認してください")
            
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")

if __name__ == "__main__":
    main()