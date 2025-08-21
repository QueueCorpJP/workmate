#!/usr/bin/env python3
"""
🔍 Multi Gemini Client デバッグスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔍 Multi Gemini Client デバッグ開始")
print("=" * 50)

# 環境変数確認
print("\n📋 環境変数確認:")
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    print(f"✅ GEMINI_API_KEY: ...{gemini_key[-8:]}")
else:
    print("❌ GEMINI_API_KEY: 未設定")

# Google API Keys確認
google_keys = []
for i in [1, 2, 4, 5, 6, 7, 8, 9, 11, 12]:
    key = os.getenv(f"GOOGLE_API_KEY_{i}")
    if key:
        google_keys.append(f"GOOGLE_API_KEY_{i}")
        print(f"✅ GOOGLE_API_KEY_{i}: ...{key[-8:]}")

print(f"📊 利用可能なGoogle APIキー: {len(google_keys)}個")

# モジュールインポートテスト
print("\n🧪 モジュールインポートテスト:")
try:
    from modules.multi_gemini_client import MultiGeminiClient, get_multi_gemini_client, multi_gemini_available
    print("✅ multi_gemini_client モジュールインポート成功")
except Exception as e:
    print(f"❌ multi_gemini_client モジュールインポート失敗: {e}")
    sys.exit(1)

# 利用可能性チェック
print("\n🔍 利用可能性チェック:")
try:
    available = multi_gemini_available()
    print(f"Multi Gemini利用可能: {available}")
except Exception as e:
    print(f"❌ 利用可能性チェック失敗: {e}")

# クライアント初期化テスト
print("\n🚀 クライアント初期化テスト:")
try:
    client = MultiGeminiClient()
    print(f"✅ MultiGeminiClient初期化成功")
    print(f"📊 利用可能APIキー数: {len(client.api_keys)}個")
    
    # APIキー詳細表示
    print("\n📋 APIキー詳細:")
    for i, key in enumerate(client.api_keys):
        if key:
            print(f"  {i+1}. ...{key[-8:]}")
        else:
            print(f"  {i+1}. None")
    
    # 状態情報表示
    print("\n📊 状態情報:")
    status_info = client.get_status_info()
    for client_name, info in status_info.items():
        status_emoji = "✅" if info['status'] == 'active' else "⚠️"
        current_marker = " (現在使用中)" if info['is_current'] else ""
        print(f"  {status_emoji} {client_name}: {info['status']}{current_marker}")
        
except Exception as e:
    print(f"❌ クライアント初期化失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n🎉 デバッグ完了")