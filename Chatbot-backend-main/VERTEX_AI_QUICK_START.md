# 🚀 Vertex AI Python SDK クイックスタートガイド

## 📋 現在の状況

✅ **Python SDK**: `google-cloud-aiplatform` インストール済み  
✅ **環境変数**: 正しく設定済み (`USE_VERTEX_AI=true`)  
✅ **プロジェクト**: `workmate-462302` 設定済み  
❌ **認証**: 未設定（**これが唯一の問題**）

## 🎯 解決方法（2つの選択肢）

### 方法A: サービスアカウントキー（推奨・簡単）

#### 1. サービスアカウント作成
[Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts?project=workmate-462302) にアクセス

#### 2. 新しいサービスアカウント作成
- **名前**: `vertex-ai-embedding`
- **説明**: `Vertex AI Embedding API用`

#### 3. 権限設定
以下の役割を付与:
- `Vertex AI User`
- `AI Platform Developer`

#### 4. キー作成・ダウンロード
- 「キー」タブ → 「新しいキーを作成」
- **JSON** 形式を選択
- ダウンロードしたファイルを `vertex-ai-key.json` として保存

#### 5. 環境変数設定
`.env` ファイルに追加:
```bash
GOOGLE_APPLICATION_CREDENTIALS=vertex-ai-key.json
```

### 方法B: Google Cloud CLI（完全版）

#### 1. CLI インストール
```bash
python install_gcloud.py
```

#### 2. 認証
```bash
gcloud auth application-default login
gcloud config set project workmate-462302
```

## 🧪 動作確認

### 認証テスト
```bash
python auth_helper.py
```

### 完全テスト
```bash
python test_vertex_ai_embedding.py
```

### 期待される結果
```
✅ サービスアカウントキー検証成功
✅ 認証成功
✅ Vertex AI テスト成功
✅ エンベディング生成成功: 768次元
🎉 すべてのテストが成功しました！
```

## 📁 作成されたファイル

| ファイル | 用途 |
|---------|------|
| `setup_vertex_ai.py` | 総合診断ツール |
| `auth_helper.py` | 認証専用ヘルパー |
| `install_gcloud.py` | Google Cloud CLI インストーラー |
| `VERTEX_AI_SETUP_COMPLETE.md` | 詳細セットアップガイド |
| `sample.env` | 環境変数設定例 |

## 🔧 トラブルシューティング

### よくあるエラーと解決方法

| エラー | 原因 | 解決方法 |
|--------|------|----------|
| `Unable to authenticate` | 認証未設定 | サービスアカウントキー設定 |
| `Permission denied` | 権限不足 | 適切な役割を付与 |
| `API not enabled` | API無効 | Vertex AI API を有効化 |

### API有効化確認
[Vertex AI API](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=workmate-462302) が有効になっているか確認

## 🎉 完了後の効果

認証設定完了後、以下が自動的に有効になります:

1. **高品質エンベディング**: `gemini-embedding-001` (768次元)
2. **自動フォールバック**: 認証失敗時は標準Gemini APIを使用
3. **既存システム統合**: 追加コード変更不要

## 💡 重要なポイント

- **セキュリティ**: `vertex-ai-key.json` を `.gitignore` に追加
- **次元数変更**: 768次元（従来の3072次元から変更）
- **コスト**: Vertex AI使用時は Google Cloud の課金対象

## 🚀 次のステップ

1. 認証設定完了
2. `python test_vertex_ai_embedding.py` で動作確認
3. 既存のチャットボットシステムが自動的にVertex AIを使用開始
4. より高精度な検索・回答が可能に

---

**質問や問題がある場合は、`python auth_helper.py` を実行して診断してください。**