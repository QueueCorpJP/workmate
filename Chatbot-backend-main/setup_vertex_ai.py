#!/usr/bin/env python3
"""
🚀 Vertex AI セットアップスクリプト
Google Cloud Vertex AI Python SDK の設定と認証確認
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

def check_requirements():
    """必要なライブラリの確認"""
    print("=" * 60)
    print("📦 必要なライブラリの確認")
    print("=" * 60)
    
    required_packages = [
        "google-cloud-aiplatform",
        "google-auth",
        "google-api-python-client"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}: インストール済み")
        except ImportError:
            print(f"❌ {package}: 未インストール")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ 以下のパッケージをインストールしてください:")
        for package in missing_packages:
            print(f"   pip install {package}")
        return False
    
    return True

def check_environment_variables():
    """環境変数の確認"""
    print("\n" + "=" * 60)
    print("🔧 環境変数の確認")
    print("=" * 60)
    
    required_vars = {
        "GOOGLE_CLOUD_PROJECT": "Google Cloud プロジェクト ID",
        "USE_VERTEX_AI": "Vertex AI 使用フラグ",
        "EMBEDDING_MODEL": "エンベディングモデル名"
    }
    
    all_set = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: 未設定 ({description})")
            all_set = False
    
    return all_set

def check_gcloud_cli():
    """Google Cloud CLI の確認"""
    print("\n" + "=" * 60)
    print("☁️ Google Cloud CLI の確認")
    print("=" * 60)
    
    try:
        result = subprocess.run(["gcloud", "--version"], 
                              capture_output=True, text=True, check=True)
        print("✅ Google Cloud CLI インストール済み")
        print(f"バージョン情報:\n{result.stdout}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Google Cloud CLI が見つかりません")
        print("\n📥 インストール方法:")
        print("1. https://cloud.google.com/sdk/docs/install にアクセス")
        print("2. Windows用インストーラーをダウンロード")
        print("3. インストール後、以下のコマンドを実行:")
        print("   gcloud auth application-default login")
        print("   gcloud config set project YOUR_PROJECT_ID")
        return False

def check_authentication():
    """認証状態の確認"""
    print("\n" + "=" * 60)
    print("🔐 認証状態の確認")
    print("=" * 60)
    
    # Application Default Credentials の確認
    try:
        from google.auth import default
        credentials, project = default()
        print(f"✅ Application Default Credentials 検出")
        print(f"プロジェクト: {project}")
        return True
    except Exception as e:
        print(f"❌ Application Default Credentials エラー: {e}")
    
    # サービスアカウントキーファイルの確認
    service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if service_account_path and os.path.exists(service_account_path):
        print(f"✅ サービスアカウントキー検出: {service_account_path}")
        return True
    
    print("\n🔧 認証設定方法:")
    print("方法1: Application Default Credentials (推奨)")
    print("  gcloud auth application-default login")
    print("\n方法2: サービスアカウントキー")
    print("  1. Google Cloud Console でサービスアカウントキーを作成")
    print("  2. JSONファイルをダウンロード")
    print("  3. 環境変数 GOOGLE_APPLICATION_CREDENTIALS にパスを設定")
    
    return False

def test_vertex_ai_connection():
    """Vertex AI 接続テスト"""
    print("\n" + "=" * 60)
    print("🧪 Vertex AI 接続テスト")
    print("=" * 60)
    
    try:
        import vertexai
        from vertexai.language_models import TextEmbeddingModel
        
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            print("❌ GOOGLE_CLOUD_PROJECT が設定されていません")
            return False
        
        # Vertex AI 初期化
        vertexai.init(project=project_id, location="global")
        print(f"✅ Vertex AI 初期化成功 (プロジェクト: {project_id})")
        
        # モデル取得テスト
        model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")
        print("✅ gemini-embedding-001 モデル取得成功")
        
        # 簡単なエンベディングテスト
        test_text = "テスト用テキスト"
        embeddings = model.get_embeddings([test_text])
        
        if embeddings and len(embeddings) > 0:
            embedding_values = embeddings[0].values
            print(f"✅ エンベディング生成成功: {len(embedding_values)}次元")
            print(f"最初の5要素: {embedding_values[:5]}")
            return True
        else:
            print("❌ エンベディング生成失敗")
            return False
            
    except Exception as e:
        print(f"❌ Vertex AI 接続エラー: {e}")
        return False

def create_service_account_setup_guide():
    """サービスアカウント設定ガイドの作成"""
    guide_content = '''# 🔐 Vertex AI サービスアカウント設定ガイド

## 1. サービスアカウントの作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクトを選択
3. 「IAM と管理」→「サービスアカウント」に移動
4. 「サービスアカウントを作成」をクリック

### サービスアカウント詳細
- **名前**: `vertex-ai-embedding-service`
- **説明**: `Vertex AI Embedding API用サービスアカウント`

## 2. 権限の設定

以下の役割を付与:
- `Vertex AI User` (roles/aiplatform.user)
- `AI Platform Developer` (roles/ml.developer)

## 3. キーの作成

1. 作成したサービスアカウントをクリック
2. 「キー」タブに移動
3. 「キーを追加」→「新しいキーを作成」
4. 「JSON」を選択してダウンロード

## 4. 環境変数の設定

`.env` ファイルに以下を追加:

```bash
# サービスアカウントキーのパス
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json

# または、キーの内容を直接設定
GOOGLE_SERVICE_ACCOUNT_KEY={"type": "service_account", ...}
```

## 5. 動作確認

```bash
python setup_vertex_ai.py
```
'''
    
    with open("VERTEX_AI_SERVICE_ACCOUNT_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide_content)
    
    print("📝 サービスアカウント設定ガイドを作成しました: VERTEX_AI_SERVICE_ACCOUNT_GUIDE.md")

def main():
    """メイン実行関数"""
    print("🚀 Vertex AI Python SDK セットアップ診断")
    print("=" * 60)
    
    # チェック項目
    checks = [
        ("必要なライブラリ", check_requirements),
        ("環境変数", check_environment_variables),
        ("Google Cloud CLI", check_gcloud_cli),
        ("認証", check_authentication),
        ("Vertex AI 接続", test_vertex_ai_connection)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} チェック中にエラー: {e}")
            results.append((check_name, False))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 診断結果サマリー")
    print("=" * 60)
    
    passed = 0
    for check_name, result in results:
        status = "✅ OK" if result else "❌ NG"
        print(f"{status} {check_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 結果: {passed}/{len(results)} 項目が正常")
    
    if passed == len(results):
        print("🎉 Vertex AI の設定が完了しています！")
    else:
        print("⚠️ 設定に問題があります。上記の指示に従って修正してください。")
        
        # サービスアカウント設定ガイドの作成
        if passed < 3:  # 認証関連で問題がある場合
            create_service_account_setup_guide()

if __name__ == "__main__":
    main()