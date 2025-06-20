# Google Drive & Sheets API設定手順

## 必要な環境変数

### 1. OAuth2認証用（推奨）
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://workmatechat.com/auth/callback
```

### 2. サービスアカウント認証用（オプション）
```bash
GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service-account-key.json
```

### 3. デフォルト認証用（開発環境）
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

## Google Cloud Console設定手順

### 1. プロジェクトの作成・選択
1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成するか、既存のプロジェクトを選択

### 2. APIの有効化
以下のAPIを有効にしてください：
- Google Drive API
- Google Sheets API

```bash
gcloud services enable drive.googleapis.com
gcloud services enable sheets.googleapis.com
```

### 3. OAuth2認証設定（推奨）

#### 3.1 OAuth同意画面の設定
1. Google Cloud Console > APIs & Services > OAuth consent screen
2. User Type: External（または Internal）を選択
3. 必要事項を入力：
   - App name: WorkMate Chat
   - User support email: your-email@example.com
   - Developer contact information: your-email@example.com

#### 3.2 OAuth2クライアントIDの作成
1. Google Cloud Console > APIs & Services > Credentials
2. "Create Credentials" > "OAuth client ID"
3. Application type: Web application
4. Name: WorkMate Chat Client
5. Authorized redirect URIs:
   - `https://workmatechat.com/auth/callback`
   - `http://localhost:3000/auth/callback`（開発用）

### 4. サービスアカウント設定（オプション）

#### 4.1 サービスアカウントの作成
1. Google Cloud Console > IAM & Admin > Service Accounts
2. "Create Service Account"
3. Service account name: workmate-excel-processor
4. Grant roles:
   - Editor（または必要最小限の権限）

#### 4.2 キーファイルの作成
1. 作成したサービスアカウントをクリック
2. Keys タブ > "Add Key" > "Create new key"
3. Key type: JSON
4. ダウンロードしたJSONファイルを安全な場所に保存

## 権限設定

### 必要なスコープ
- `https://www.googleapis.com/auth/drive`
- `https://www.googleapis.com/auth/spreadsheets`

### OAuth2の場合
フロントエンドで以下のスコープを要求：
```javascript
const scopes = [
  'https://www.googleapis.com/auth/drive.file',
  'https://www.googleapis.com/auth/spreadsheets'
];
```

## セキュリティ考慮事項

### 1. 認証方式の優先順位
1. **OAuth2** - ユーザーの個人アカウントを使用（推奨）
2. **サービスアカウント** - アプリケーション専用アカウント
3. **デフォルト認証** - 開発環境用

### 2. 本番環境での注意事項
- サービスアカウントキーは環境変数として設定
- キーファイルは安全な場所に保存
- 不要な権限は付与しない
- 定期的にキーのローテーションを実施

## トラブルシューティング

### 1. 認証エラー
- 環境変数が正しく設定されているか確認
- APIが有効になっているか確認
- 権限が適切に設定されているか確認

### 2. アップロードエラー
- ファイルサイズ制限（10MB）を確認
- サポートされているファイル形式か確認
- Google Driveの容量制限を確認

### 3. 変換エラー
- Excelファイルが破損していないか確認
- 複雑なフォーマットや数式が含まれていないか確認
- シート数が多すぎないか確認

## 開発環境での設定

### 1. gcloud CLIを使用
```bash
gcloud auth application-default login
```

### 2. 環境変数ファイル（.env）
```bash
# OAuth2設定
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback

# サービスアカウント設定（オプション）
GOOGLE_SERVICE_ACCOUNT_FILE=./service-account-key.json
```

## 本番環境での設定

### 1. Heroku
```bash
heroku config:set GOOGLE_CLIENT_ID=your-client-id
heroku config:set GOOGLE_CLIENT_SECRET=your-client-secret
heroku config:set GOOGLE_REDIRECT_URI=https://workmatechat.com/auth/callback
```

### 2. Docker
```dockerfile
ENV GOOGLE_CLIENT_ID=your-client-id
ENV GOOGLE_CLIENT_SECRET=your-client-secret
ENV GOOGLE_REDIRECT_URI=https://workmatechat.com/auth/callback
```

## 料金について

- Google Drive API: 無料枠あり（1日あたり100,000リクエスト）
- Google Sheets API: 無料枠あり（1日あたり100,000リクエスト）
- 通常の使用量では無料枠内で十分です

詳細は[Google Cloud Pricing](https://cloud.google.com/pricing)を参照してください。 