# 🔐 Vertex AI サービスアカウント設定ガイド

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
