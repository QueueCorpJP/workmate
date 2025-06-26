#!/usr/bin/env python3
"""
☁️ Google Cloud CLI 自動インストールヘルパー
Windows用のGoogle Cloud CLIインストールを支援
"""

import os
import sys
import subprocess
import urllib.request
import tempfile
from pathlib import Path

def check_gcloud_installed():
    """Google Cloud CLIがインストールされているかチェック"""
    try:
        result = subprocess.run(["gcloud", "--version"], 
                              capture_output=True, text=True, check=True)
        print("✅ Google Cloud CLI は既にインストールされています")
        print(f"バージョン情報:\n{result.stdout}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Google Cloud CLI が見つかりません")
        return False

def download_gcloud_installer():
    """Google Cloud CLI インストーラーをダウンロード"""
    print("📥 Google Cloud CLI インストーラーをダウンロード中...")
    
    # Windows用インストーラーのURL
    installer_url = "https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe"
    
    # 一時ディレクトリにダウンロード
    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, "GoogleCloudSDKInstaller.exe")
    
    try:
        urllib.request.urlretrieve(installer_url, installer_path)
        print(f"✅ ダウンロード完了: {installer_path}")
        return installer_path
    except Exception as e:
        print(f"❌ ダウンロードエラー: {e}")
        return None

def run_installer(installer_path):
    """インストーラーを実行"""
    print("🚀 Google Cloud CLI インストーラーを起動中...")
    print("インストーラーの指示に従ってインストールを完了してください")
    
    try:
        # インストーラーを実行（非同期）
        subprocess.Popen([installer_path])
        print("✅ インストーラーが起動しました")
        return True
    except Exception as e:
        print(f"❌ インストーラー起動エラー: {e}")
        return False

def setup_authentication():
    """認証設定の手順を表示"""
    print("\n" + "=" * 60)
    print("🔐 インストール後の認証設定")
    print("=" * 60)
    
    print("Google Cloud CLI のインストールが完了したら、以下のコマンドを実行してください:")
    print()
    print("1. PowerShell を再起動")
    print()
    print("2. 認証設定:")
    print("   gcloud auth application-default login")
    print()
    print("3. プロジェクト設定:")
    print("   gcloud config set project workmate-462302")
    print()
    print("4. 動作確認:")
    print("   python auth_helper.py")

def manual_installation_guide():
    """手動インストールガイド"""
    print("\n" + "=" * 60)
    print("📋 手動インストールガイド")
    print("=" * 60)
    
    print("自動ダウンロードが失敗した場合の手動インストール手順:")
    print()
    print("1. ブラウザで以下のURLにアクセス:")
    print("   https://cloud.google.com/sdk/docs/install")
    print()
    print("2. 'Windows' タブを選択")
    print()
    print("3. 'GoogleCloudSDKInstaller.exe' をダウンロード")
    print()
    print("4. ダウンロードしたファイルを実行してインストール")
    print()
    print("5. インストール完了後、PowerShellを再起動")
    print()
    print("6. 認証設定:")
    print("   gcloud auth application-default login")
    print("   gcloud config set project workmate-462302")

def main():
    """メイン実行"""
    print("☁️ Google Cloud CLI インストールヘルパー")
    print("=" * 60)
    
    # 既にインストールされているかチェック
    if check_gcloud_installed():
        print("\n🎯 Google Cloud CLI は既にインストールされています")
        print("認証設定を確認するには 'python auth_helper.py' を実行してください")
        return
    
    print("\n📦 Google Cloud CLI をインストールします")
    
    # ユーザーに確認
    response = input("インストールを続行しますか？ (y/N): ").lower().strip()
    if response not in ['y', 'yes']:
        print("インストールをキャンセルしました")
        manual_installation_guide()
        return
    
    # インストーラーをダウンロード
    installer_path = download_gcloud_installer()
    if not installer_path:
        print("自動ダウンロードに失敗しました")
        manual_installation_guide()
        return
    
    # インストーラーを実行
    if run_installer(installer_path):
        setup_authentication()
    else:
        manual_installation_guide()

if __name__ == "__main__":
    main()