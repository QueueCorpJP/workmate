#!/usr/bin/env python3
"""
🔄 Multi API Keys対応アプリケーション再起動スクリプト
"""

import os
import sys
import subprocess
import time

def main():
    print("🔄 Multi API Keys対応アプリケーション再起動")
    print("=" * 50)
    
    # 現在のプロセス確認
    print("\n🔍 現在のプロセス確認...")
    try:
        # Windowsでpythonプロセスを確認
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        if 'python.exe' in result.stdout:
            print("✅ Pythonプロセスが実行中です")
            print("📋 実行中のPythonプロセス:")
            lines = result.stdout.split('\n')
            for line in lines:
                if 'python.exe' in line:
                    print(f"   {line.strip()}")
        else:
            print("⚠️ Pythonプロセスが見つかりません")
    except Exception as e:
        print(f"❌ プロセス確認エラー: {e}")
    
    # Multi Gemini Client状態確認
    print("\n🧪 Multi Gemini Client状態確認...")
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from modules.multi_gemini_client import get_multi_gemini_client, multi_gemini_available
        
        if multi_gemini_available():
            client = get_multi_gemini_client()
            print(f"✅ Multi Gemini Client利用可能: {len(client.api_keys)}個のAPIキー")
            
            # 状態情報表示
            status_info = client.get_status_info()
            active_count = sum(1 for info in status_info.values() if info['status'] == 'active')
            print(f"📊 アクティブなAPIキー: {active_count}個")
            
        else:
            print("❌ Multi Gemini Client利用不可")
            
    except Exception as e:
        print(f"❌ Multi Gemini Client確認エラー: {e}")
    
    print("\n📋 再起動手順:")
    print("1. 現在実行中のアプリケーションを停止してください")
    print("   - Ctrl+C でサーバーを停止")
    print("   - または、ターミナルを閉じる")
    print("")
    print("2. 以下のコマンドでアプリケーションを再起動してください:")
    print("   cd workmate/Chatbot-backend-main")
    print("   python main.py")
    print("")
    print("3. 再起動後、以下のログメッセージを確認してください:")
    print("   ✅ Multi Gemini Client初期化完了")
    print("   📊 使用可能APIキー: X個")
    print("")
    print("4. 429エラーが発生した場合、自動的に次のAPIキーに切り替わります:")
    print("   🔄 APIキー切り替え: gemini_client_X")
    print("   ✅ gemini_client_X API呼び出し成功")
    
    print("\n🎯 期待される動作:")
    print("- 最初のAPIキーでレート制限に達した場合")
    print("- 自動的に2番目のAPIキーに切り替え")
    print("- 継続的なサービス提供")
    print("- エラーログの代わりに成功ログが表示される")
    
    print("\n🔧 トラブルシューティング:")
    print("- もし「Multi Gemini Client利用不可」が表示される場合:")
    print("  python debug_multi_client.py を実行して詳細を確認")
    print("- APIキーが正しく設定されているか .env ファイルを確認")
    print("- 必要に応じて python test_multi_api_keys.py でテスト実行")

if __name__ == "__main__":
    main()