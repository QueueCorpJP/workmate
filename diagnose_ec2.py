#!/usr/bin/env python3
"""
EC2環境診断スクリプト
EC2環境でのWorkMate AI Chatbotの問題を診断します
"""
import os
import sys
import requests
import subprocess
import json
from pathlib import Path

def check_environment():
    """環境変数と設定をチェック"""
    print("🔍 環境変数チェック")
    print("=" * 50)
    
    # 重要な環境変数をチェック
    important_vars = [
        'ENVIRONMENT', 'NODE_ENV', 'PORT', 
        'GEMINI_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY'
    ]
    
    for var in important_vars:
        value = os.getenv(var)
        if value:
            # APIキーなどは一部のみ表示
            if 'KEY' in var or 'SECRET' in var:
                display_value = value[:10] + "..." if len(value) > 10 else value
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: 未設定")
    
    print()

def check_ports():
    """ポート使用状況をチェック"""
    print("🔍 ポート使用状況チェック")
    print("=" * 50)
    
    ports_to_check = [8083, 8085, 80, 443]
    
    for port in ports_to_check:
        try:
            # netstatコマンドでポート使用状況をチェック
            result = subprocess.run(
                ['netstat', '-tlnp'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if f":{port}" in result.stdout:
                print(f"✅ ポート {port}: 使用中")
            else:
                print(f"❌ ポート {port}: 未使用")
                
        except Exception as e:
            print(f"⚠️  ポート {port}: チェック失敗 ({str(e)})")
    
    print()

def check_processes():
    """Pythonプロセスをチェック"""
    print("🔍 Pythonプロセスチェック")
    print("=" * 50)
    
    try:
        result = subprocess.run(
            ['ps', 'aux'], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        python_processes = [line for line in result.stdout.split('\n') if 'python' in line.lower()]
        
        if python_processes:
            print(f"✅ {len(python_processes)}個のPythonプロセスが実行中:")
            for process in python_processes[:5]:  # 最初の5個のみ表示
                print(f"   {process}")
        else:
            print("❌ Pythonプロセスが見つかりません")
            
    except Exception as e:
        print(f"⚠️  プロセスチェック失敗: {str(e)}")
    
    print()

def check_api_endpoints():
    """APIエンドポイントをチェック"""
    print("🔍 APIエンドポイントチェック")
    print("=" * 50)
    
    base_urls = [
        "http://localhost:8083",
        "http://127.0.0.1:8083",
        "http://localhost:8085",
        "http://127.0.0.1:8085"
    ]
    
    endpoints = [
        "/chatbot/api/docs",
        "/chatbot/api/auth/login",
        "/chatbot/api/chat"
    ]
    
    for base_url in base_urls:
        print(f"\n📡 テスト対象: {base_url}")
        
        for endpoint in endpoints:
            full_url = f"{base_url}{endpoint}"
            try:
                response = requests.get(full_url, timeout=5)
                print(f"   {endpoint}: {response.status_code}")
                
                if endpoint == "/chatbot/api/docs" and response.status_code == 200:
                    print(f"   ✅ APIドキュメントが利用可能")
                    
            except requests.exceptions.ConnectionError:
                print(f"   {endpoint}: 接続エラー")
            except requests.exceptions.Timeout:
                print(f"   {endpoint}: タイムアウト")
            except Exception as e:
                print(f"   {endpoint}: エラー ({str(e)})")
    
    print()

def check_nginx_config():
    """Nginx設定をチェック"""
    print("🔍 Nginx設定チェック")
    print("=" * 50)
    
    nginx_config_paths = [
        "/etc/nginx/conf.d/workmatechat.com.conf",
        "/etc/nginx/sites-available/workmatechat.com",
        "/etc/nginx/nginx.conf"
    ]
    
    for config_path in nginx_config_paths:
        if os.path.exists(config_path):
            print(f"✅ {config_path}: 存在")
            try:
                with open(config_path, 'r') as f:
                    content = f.read()
                    if "8083" in content:
                        print(f"   ✅ ポート8083の設定を確認")
                    if "chatbot_backend" in content:
                        print(f"   ✅ upstream設定を確認")
            except Exception as e:
                print(f"   ⚠️  設定ファイル読み込みエラー: {str(e)}")
        else:
            print(f"❌ {config_path}: 存在しない")
    
    # Nginxのステータスをチェック
    try:
        result = subprocess.run(
            ['systemctl', 'status', 'nginx'], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if "active (running)" in result.stdout:
            print("✅ Nginx: 実行中")
        else:
            print("❌ Nginx: 停止中")
            
    except Exception as e:
        print(f"⚠️  Nginxステータスチェック失敗: {str(e)}")
    
    print()

def check_logs():
    """ログファイルをチェック"""
    print("🔍 ログファイルチェック")
    print("=" * 50)
    
    log_files = [
        "backend.log",
        "/var/log/nginx/error.log",
        "/var/log/nginx/access.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"✅ {log_file}: 存在")
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"   📝 最新のログエントリ:")
                        for line in lines[-3:]:  # 最後の3行を表示
                            print(f"      {line.strip()}")
            except Exception as e:
                print(f"   ⚠️  ログ読み込みエラー: {str(e)}")
        else:
            print(f"❌ {log_file}: 存在しない")
    
    print()

def generate_fix_suggestions():
    """修正提案を生成"""
    print("🔧 修正提案")
    print("=" * 50)
    
    suggestions = [
        "1. バックエンドサーバーが起動していない場合:",
        "   cd /path/to/workmate/Chatbot-backend-main",
        "   source venv/bin/activate",
        "   export ENVIRONMENT=production",
        "   export PORT=8083",
        "   python main.py",
        "",
        "2. Nginxの設定を確認:",
        "   sudo nginx -t",
        "   sudo systemctl reload nginx",
        "",
        "3. ファイアウォール設定を確認:",
        "   sudo ufw status",
        "   sudo ufw allow 8083",
        "",
        "4. PM2を使用する場合:",
        "   pm2 start main.py --name workmate-backend --interpreter python3",
        "   pm2 logs workmate-backend",
        "",
        "5. 環境変数を確認:",
        "   printenv | grep -E '(ENVIRONMENT|PORT|NODE_ENV)'",
    ]
    
    for suggestion in suggestions:
        print(suggestion)

if __name__ == "__main__":
    print("🚀 EC2環境診断スクリプト")
    print("=" * 70)
    print()
    
    check_environment()
    check_ports()
    check_processes()
    check_api_endpoints()
    check_nginx_config()
    check_logs()
    generate_fix_suggestions()
    
    print("\n" + "=" * 70)
    print("✅ 診断完了")