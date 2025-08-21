#!/usr/bin/env python3
"""
🔧 複数Gemini APIキー設定スクリプト
環境変数の設定をサポートします
"""

import os
from dotenv import load_dotenv, set_key

def setup_multi_api_keys():
    """複数APIキーの設定をサポート"""
    print("🔧 複数Gemini APIキー設定スクリプト")
    print("=" * 50)
    
    # 現在の.envファイルを読み込み
    env_file = ".env"
    load_dotenv(env_file)
    
    # 現在設定されているAPIキーを確認
    current_keys = []
    key_names = [
        "GEMINI_API_KEY",
        "GEMINI_API_KEY_2", 
        "GEMINI_API_KEY_3",
        "GEMINI_API_KEY_4",
        "GEMINI_API_KEY_5"
    ]
    
    print("\n📋 現在の設定状況:")
    for i, key_name in enumerate(key_names, 1):
        current_value = os.getenv(key_name)
        if current_value:
            masked_key = current_value[:8] + "..." + current_value[-8:] if len(current_value) > 16 else "設定済み"
            print(f"  {i}. {key_name}: {masked_key}")
            current_keys.append(key_name)
        else:
            print(f"  {i}. {key_name}: 未設定")
    
    print(f"\n✅ 設定済みAPIキー数: {len(current_keys)}個")
    
    if len(current_keys) >= 2:
        print("🎉 複数APIキーが設定されています！レート制限対応が有効です。")
    else:
        print("⚠️  レート制限対応のため、複数のAPIキーを設定することを推奨します。")
    
    print("\n📝 追加のAPIキーを設定する場合:")
    print("1. Google AI StudioでAPIキーを生成: https://aistudio.google.com/app/apikey")
    print("2. .envファイルに以下の形式で追加:")
    print("   GEMINI_API_KEY=your_first_api_key")
    print("   GEMINI_API_KEY_2=your_second_api_key")
    print("   GEMINI_API_KEY_3=your_third_api_key")
    print("   GEMINI_API_KEY_4=your_fourth_api_key")
    print("   GEMINI_API_KEY_5=your_fifth_api_key")
    
    # 対話的設定オプション
    print("\n🔧 対話的設定を開始しますか？ (y/n): ", end="")
    if input().lower() == 'y':
        interactive_setup(env_file, key_names)

def interactive_setup(env_file, key_names):
    """対話的APIキー設定"""
    print("\n🔧 対話的APIキー設定開始")
    print("(空白で入力をスキップ、'quit'で終了)")
    
    for key_name in key_names:
        current_value = os.getenv(key_name)
        if current_value:
            print(f"\n{key_name} は既に設定されています。")
            print("上書きしますか？ (y/n): ", end="")
            if input().lower() != 'y':
                continue
        
        print(f"\n{key_name} を入力してください: ", end="")
        new_value = input().strip()
        
        if new_value.lower() == 'quit':
            break
        elif new_value:
            try:
                set_key(env_file, key_name, new_value)
                print(f"✅ {key_name} を設定しました")
            except Exception as e:
                print(f"❌ {key_name} の設定に失敗: {e}")
    
    print("\n🎉 設定完了！アプリケーションを再起動してください。")

def test_multi_api_keys():
    """複数APIキーのテスト"""
    print("\n🧪 複数APIキーのテスト開始")
    
    try:
        from modules.multi_gemini_client import get_multi_gemini_client, multi_gemini_available
        
        if not multi_gemini_available():
            print("❌ Multi Gemini Client が利用できません")
            return
        
        client = get_multi_gemini_client()
        status_info = client.get_status_info()
        
        print("📊 APIキー状態:")
        for client_name, info in status_info.items():
            status_emoji = "✅" if info['status'] == 'active' else "⚠️"
            print(f"  {status_emoji} {client_name}: {info['status']} (末尾: ...{info['api_key_suffix']})")
        
        print("🎉 Multi Gemini Client テスト完了")
        
    except Exception as e:
        print(f"❌ テスト失敗: {e}")

if __name__ == "__main__":
    setup_multi_api_keys()
    
    print("\n🧪 APIキーのテストを実行しますか？ (y/n): ", end="")
    if input().lower() == 'y':
        test_multi_api_keys()