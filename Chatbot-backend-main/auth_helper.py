#!/usr/bin/env python3
"""
🔐 Vertex AI 認証ヘルパー
様々な認証方法をサポートする簡単なセットアップツール
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

def check_service_account_key():
    """サービスアカウントキーファイルの確認"""
    print("=" * 60)
    print("🔑 サービスアカウントキー確認")
    print("=" * 60)
    
    # 環境変数からパスを取得
    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if not key_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS が設定されていません")
        return False
    
    # ファイルの存在確認
    if not os.path.exists(key_path):
        print(f"❌ キーファイルが見つかりません: {key_path}")
        return False
    
    try:
        # JSONファイルの検証
        with open(key_path, 'r', encoding='utf-8') as f:
            key_data = json.load(f)
        
        # 必要なフィールドの確認
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in key_data]
        
        if missing_fields:
            print(f"❌ キーファイルに必要なフィールドがありません: {missing_fields}")
            return False
        
        print(f"✅ サービスアカウントキー検証成功")
        print(f"   ファイル: {key_path}")
        print(f"   プロジェクト: {key_data.get('project_id')}")
        print(f"   サービスアカウント: {key_data.get('client_email')}")
        
        return True
        
    except json.JSONDecodeError:
        print(f"❌ キーファイルのJSON形式が無効です: {key_path}")
        return False
    except Exception as e:
        print(f"❌ キーファイル読み込みエラー: {e}")
        return False

def test_authentication():
    """認証テスト"""
    print("\n" + "=" * 60)
    print("🧪 認証テスト")
    print("=" * 60)
    
    try:
        from google.auth import default
        
        # デフォルト認証情報の取得
        credentials, project = default()
        
        print(f"✅ 認証成功")
        print(f"   プロジェクト: {project}")
        print(f"   認証タイプ: {type(credentials).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ 認証失敗: {e}")
        return False

def test_vertex_ai_simple():
    """簡単なVertex AIテスト"""
    print("\n" + "=" * 60)
    print("🚀 Vertex AI 簡単テスト")
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
        
        # モデル取得
        model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")
        print("✅ gemini-embedding-001 モデル取得成功")
        
        # 簡単なテスト
        test_text = "Hello, Vertex AI!"
        embeddings = model.get_embeddings([test_text])
        
        if embeddings and len(embeddings) > 0:
            embedding_values = embeddings[0].values
            print(f"✅ エンベディング生成成功: {len(embedding_values)}次元")
            return True
        else:
            print("❌ エンベディング生成失敗")
            return False
            
    except Exception as e:
        print(f"❌ Vertex AI テストエラー: {e}")
        return False

def create_sample_env():
    """サンプル.envファイルの作成"""
    sample_env_content = """# Vertex AI 認証設定例

# 方法1: サービスアカウントキーファイル
GOOGLE_APPLICATION_CREDENTIALS=vertex-ai-key.json

# 方法2: サービスアカウントキーの内容を直接設定
# GOOGLE_SERVICE_ACCOUNT_KEY={"type": "service_account", ...}

# 既存の設定
GOOGLE_CLOUD_PROJECT=workmate-462302
USE_VERTEX_AI=true
EMBEDDING_MODEL=gemini-embedding-001
"""
    
    sample_file = "sample.env"
    with open(sample_file, 'w', encoding='utf-8') as f:
        f.write(sample_env_content)
    
    print(f"📝 サンプル環境設定ファイルを作成しました: {sample_file}")

def setup_instructions():
    """セットアップ手順の表示"""
    print("\n" + "=" * 60)
    print("📋 セットアップ手順")
    print("=" * 60)
    
    print("1. Google Cloud Console でサービスアカウントを作成")
    print("   https://console.cloud.google.com/iam-admin/serviceaccounts")
    print()
    print("2. 以下の権限を付与:")
    print("   - Vertex AI User (roles/aiplatform.user)")
    print("   - AI Platform Developer (roles/ml.developer)")
    print()
    print("3. JSONキーをダウンロードして 'vertex-ai-key.json' として保存")
    print()
    print("4. .env ファイルに以下を追加:")
    print("   GOOGLE_APPLICATION_CREDENTIALS=vertex-ai-key.json")
    print()
    print("5. 再度このスクリプトを実行して確認")

def main():
    """メイン実行"""
    print("🔐 Vertex AI 認証ヘルパー")
    print("=" * 60)
    
    # 環境変数確認
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    use_vertex_ai = os.getenv("USE_VERTEX_AI")
    
    print(f"プロジェクト: {project_id}")
    print(f"Vertex AI使用: {use_vertex_ai}")
    
    # テスト実行
    tests = [
        ("サービスアカウントキー", check_service_account_key),
        ("認証", test_authentication),
        ("Vertex AI", test_vertex_ai_simple)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} テストエラー: {e}")
            results.append((test_name, False))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ OK" if result else "❌ NG"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 結果: {passed}/{len(results)} テスト成功")
    
    if passed == len(results):
        print("🎉 Vertex AI の認証設定が完了しています！")
        print("次は 'python test_vertex_ai_embedding.py' を実行してください")
    else:
        print("⚠️ 認証設定に問題があります")
        setup_instructions()
        create_sample_env()

if __name__ == "__main__":
    main()