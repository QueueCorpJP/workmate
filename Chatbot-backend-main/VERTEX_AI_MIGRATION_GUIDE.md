# 🚀 Vertex AI Embedding Migration Guide

## 概要

このガイドでは、現在の `gemini-embedding-exp-03-07` から Vertex AI の `gemini-embedding-001` グローバルエンドポイントへの移行手順を説明します。

## 変更内容

### 1. 環境変数の更新

`.env` ファイルに以下の設定を追加/更新：

```bash
# Embedding Model Configuration
EMBEDDING_MODEL=gemini-embedding-001
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID_HERE  # 実際のプロジェクトIDに置き換え
USE_VERTEX_AI=true
```

### 2. 依存関係の追加

`requirements.txt` に Vertex AI ライブラリを追加：

```
google-cloud-aiplatform>=1.38.0
```

### 3. 新しいモジュール

- `modules/vertex_ai_embedding.py`: Vertex AI Embedding クライアント

### 4. 更新されたモジュール

- `modules/auto_embedding.py`: Vertex AI サポート追加
- `modules/realtime_rag.py`: Vertex AI サポート追加
- `modules/vector_search.py`: Vertex AI サポート追加

## セットアップ手順

### Step 1: Google Cloud Project ID の設定

1. Google Cloud Console にアクセス
2. プロジェクト ID を確認
3. `.env` ファイルの `GOOGLE_CLOUD_PROJECT` を実際のプロジェクト ID に更新

### Step 2: 認証の設定

Application Default Credentials を使用する場合：

```bash
# Google Cloud CLI をインストール
# https://cloud.google.com/sdk/docs/install

# 認証
gcloud auth application-default login

# プロジェクトを設定
gcloud config set project YOUR_PROJECT_ID
```

### Step 3: 依存関係のインストール

```bash
pip install -r requirements.txt
```

### Step 4: 設定の有効化

`.env` ファイルで以下を設定：

```bash
USE_VERTEX_AI=true
GOOGLE_CLOUD_PROJECT=your-actual-project-id
```

## 動作確認

### テスト用スクリプト

```python
# test_vertex_ai_embedding.py
import os
from dotenv import load_dotenv
from modules.vertex_ai_embedding import get_vertex_ai_embedding_client

load_dotenv()

def test_vertex_ai_embedding():
    client = get_vertex_ai_embedding_client()
    if not client:
        print("❌ Vertex AI クライアントの初期化に失敗")
        return
    
    test_text = "これはテスト用のテキストです。"
    embedding = client.generate_embedding(test_text)
    
    if embedding:
        print(f"✅ エンベディング生成成功: {len(embedding)}次元")
        print(f"最初の5要素: {embedding[:5]}")
    else:
        print("❌ エンベディング生成に失敗")

if __name__ == "__main__":
    test_vertex_ai_embedding()
```

## フォールバック機能

システムは自動的にフォールバック機能を提供：

1. `USE_VERTEX_AI=true` かつ Vertex AI が利用可能 → Vertex AI 使用
2. `USE_VERTEX_AI=false` または Vertex AI が利用不可 → 標準 Gemini API 使用

## エンドポイント情報

### Vertex AI Global Endpoint
```
https://aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/global/publishers/google/models/gemini-embedding-001:embedContent
```

### モデル仕様
- **モデル名**: `gemini-embedding-001`
- **次元数**: 768次元
- **入力制限**: テキストあたり最大2048トークン
- **レート制限**: プロジェクトごとの制限に従う

## トラブルシューティング

### よくある問題

1. **認証エラー**
   ```
   google.auth.exceptions.DefaultCredentialsError
   ```
   → `gcloud auth application-default login` を実行

2. **プロジェクト ID エラー**
   ```
   GOOGLE_CLOUD_PROJECT 環境変数が設定されていません
   ```
   → `.env` ファイルでプロジェクト ID を設定

3. **ライブラリ不足エラー**
   ```
   ModuleNotFoundError: No module named 'google.cloud.aiplatform'
   ```
   → `pip install google-cloud-aiplatform` を実行

### ログの確認

アプリケーション起動時に以下のログを確認：

```
✅ Vertex AI Embedding初期化完了: gemini-embedding-001 (global endpoint)
🧠 Vertex AI Embedding使用: gemini-embedding-001
```

## 移行のメリット

1. **安定性**: 実験的モデルから本番モデルへ
2. **グローバル可用性**: 世界中からアクセス可能
3. **一貫性**: Google Cloud の標準的な認証・課金システム
4. **スケーラビリティ**: Vertex AI の高可用性インフラ

## 注意事項

- `gemini-embedding-001` は768次元、`gemini-embedding-exp-03-07` は3072次元
- 既存のエンベディングデータとの互換性はありません
- 新しいエンベディングで再生成が必要な場合があります

## サポート

問題が発生した場合は、以下を確認してください：

1. Google Cloud Console でプロジェクトが有効
2. Vertex AI API が有効化されている
3. 適切な権限が設定されている
4. 課金アカウントが設定されている