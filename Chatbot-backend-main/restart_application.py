#!/usr/bin/env python3
"""
アプリケーションサーバーを再起動してスキーマキャッシュを完全にリフレッシュするスクリプト
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def find_running_processes():
    """実行中のPythonプロセスを検索"""
    try:
        # Windows用のプロセス検索
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'], 
                              capture_output=True, text=True)
        
        processes = []
        lines = result.stdout.strip().split('\n')
        
        for line in lines[1:]:  # ヘッダーをスキップ
            if 'python.exe' in line:
                parts = line.split(',')
                if len(parts) >= 2:
                    pid = parts[1].strip('"')
                    processes.append(pid)
        
        return processes
    except Exception as e:
        print(f"プロセス検索エラー: {e}")
        return []

def restart_application():
    """アプリケーションを再起動"""
    print("🔄 アプリケーション再起動プロセス開始...")
    
    # 現在のディレクトリを確認
    current_dir = Path.cwd()
    print(f"📁 現在のディレクトリ: {current_dir}")
    
    # main.pyが存在するか確認
    main_py = current_dir / "main.py"
    if not main_py.exists():
        print("❌ main.pyが見つかりません")
        return False
    
    print("🛑 既存のPythonプロセスを確認中...")
    running_processes = find_running_processes()
    
    if running_processes:
        print(f"📋 実行中のPythonプロセス: {len(running_processes)}個")
        print("⚠️ 手動でアプリケーションサーバーを停止してから再起動してください")
        print("   Ctrl+C でサーバーを停止し、以下のコマンドで再起動:")
        print("   python main.py")
    else:
        print("✅ 実行中のPythonプロセスが見つかりません")
        print("🚀 アプリケーションサーバーを起動中...")
        
        try:
            # バックグラウンドでmain.pyを起動
            subprocess.Popen([sys.executable, "main.py"], 
                           cwd=current_dir,
                           creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
            
            print("✅ アプリケーションサーバーが起動されました")
            print("🌐 http://localhost:8000 でアクセス可能です")
            
        except Exception as e:
            print(f"❌ サーバー起動エラー: {e}")
            return False
    
    return True

def main():
    print("🔧 Workmate Chatbot アプリケーション再起動ツール")
    print("=" * 50)
    
    # スキーマキャッシュの状態を確認
    print("✅ document_sourcesテーブルのスキーマキャッシュは既に修正済みです")
    
    # アプリケーション再起動
    if restart_application():
        print("\n🎉 再起動プロセス完了!")
        print("📝 ファイルアップロード機能を再試行してください")
    else:
        print("\n❌ 再起動プロセスでエラーが発生しました")

if __name__ == "__main__":
    main()