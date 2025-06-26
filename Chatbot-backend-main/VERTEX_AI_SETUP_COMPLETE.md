# 🚀 Vertex AI Python SDK 完全セットアップガイド

## 現在の状況
✅ **ライブラリ**: google-cloud-aiplatform インストール済み  
✅ **環境変数**: 正しく設定済み  
❌ **認証**: 未設定（これが主な問題）

## 🔐 認証設定方法

### 方法1: サービスアカウントキー（推奨・簡単）

#### Step 1: サービスアカウントの作成
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクト `workmate-462302` を選択
3. 左メニュー「IAM と管理」→「サービスアカウント」
4. 「サービスアカウントを作成」をクリック

#### Step 2: サービスアカウント詳細
- **名前**: `vertex-ai-embedding`
- **説明**: `Vertex AI Embedding API用`

#### Step 3: 権限の設定
以下の役割を付与:
- `Vertex AI User` (roles/aiplatform.user)
- `AI Platform Developer` (roles/ml.developer)

#### Step 4: キーの作成
1. 作成したサービスアカウントをクリック
2. 「キー」タブ → 「キーを追加」→「新しいキーを作成」
3. **JSON** を選択してダウンロード
4. ファイルを `workmate/Chatbot-backend-main/` フォルダに保存
5. ファイル名を `vertex-ai-key.json` に変更

#### Step 5: 環境変数の設定
`.env` ファイルに以下を追加:
```bash
# Vertex AI 認証
GOOGLE_APPLICATION_CREDENTIALS=vertex-ai-key.json
```

### 方法2: Google Cloud CLI（完全版）

#### Step 1: Google Cloud CLI インストール
1. [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) からWindows版をダウンロード
2. インストーラーを実行
3. PowerShellを再起動

#### Step 2: 認証
```bash
# 認証
gcloud auth application-default login

# プロジェクト設定
gcloud config set project workmate-462302
```

## 🧪 動作確認

### 認証設定後のテスト
```bash
python setup_vertex_ai.py
python test_vertex_ai_embedding.py
```

### 期待される結果
```
✅ Vertex AI 初期化成功
✅ エンベディング生成成功: 768次元
🎉 すべてのテストが成功しました！
```

## 🔧 トラブルシューティング

### よくあるエラー

#### 1. 認証エラー
```
Unable to authenticate your request
```
**解決方法**: サービスアカウントキーのパスを確認

#### 2. プロジェクトアクセスエラー
```
Permission denied
```
**解決方法**: サービスアカウントに適切な権限を付与

#### 3. API無効エラー
```
Vertex AI API has not been used
```
**解決方法**: Google Cloud Console で Vertex AI API を有効化

## 📋 必要なAPI

以下のAPIが有効化されている必要があります:
- Vertex AI API
- AI Platform API
- Cloud Resource Manager API

[API有効化ページ](https://console.cloud.google.com/apis/library)

## 🎯 次のステップ

認証が完了したら:
1. `python test_vertex_ai_embedding.py` でテスト
2. 既存のエンベディングシステムが自動的にVertex AIを使用開始
3. より高品質なエンベディング生成が可能に

## 💡 ヒント

- サービスアカウントキーファイルは `.gitignore` に追加してください
- 本番環境では環境変数でキーの内容を設定することを推奨
- Vertex AI は768次元のエンベディングを生成（従来の3072次元から変更）