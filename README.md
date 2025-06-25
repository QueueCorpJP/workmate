# Workmate AI チャットボットシステム

このプロジェクトは、企業向けAIチャットボットシステム「Workmate」です。

## 📋 目次

- [概要](#概要)
- [主要機能](#主要機能)
- [技術スタック](#技術スタック)
- [アーキテクチャ](#アーキテクチャ)
- [プロジェクト構成](#プロジェクト構成)
- [セットアップ](#セットアップ)
- [環境変数](#環境変数)
- [使用方法](#使用方法)
- [API ドキュメント](#api-ドキュメント)
- [デプロイ](#デプロイ)
- [管理機能](#管理機能)
- [トラブルシューティング](#トラブルシューティング)
- [貢献者](#貢献者)

## 概要

**Workmate** は、企業内のドキュメントやナレッジベースを活用した高性能AIチャットボットシステムです。Google Gemini AIを搭載し、PDF、Excel、動画などの多様なフォーマットのドキュメントを処理・分析して、従業員の質問に的確な回答を提供します。

### 🎯 主な用途
- 社内FAQシステム
- ドキュメント検索・分析
- 新入社員向けガイドシステム
- 業務効率化支援
- ナレッジマネジメント

## 主要機能

### 🤖 AIチャット機能
- **Google Gemini AI** による高精度な質問応答
- 会話履歴の保持とコンテキスト理解
- 情報ソースの明示（どのドキュメントから回答を生成したか）
- 感情分析とカテゴリ分類

### 📁 ドキュメント処理機能
| ファイル形式 | 対応機能 | 最大サイズ |
|-------------|----------|-----------|
| **PDF** | OCR、複数ページ対応 | 10MB |
| **Excel** | 複数シート、データ分析 | 5MB |
| **テキスト** | プレーンテキスト、マークダウン | 2MB |
| **動画** | MP4, AVI, WebM | 500MB |
| **URL** | Webスクレイピング、動的コンテンツ | - |

### 👥 ユーザー管理機能
- **多階層認証**: 管理者・一般ユーザー
- **会社別管理**: 企業ごとの情報分離
- **利用制限**: 質問回数・ドキュメント数の制限設定
- **詳細なユーザー分析**: 利用状況の可視化

### 📊 管理ダッシュボード
- 利用統計の可視化
- チャット履歴の感情分析
- リソース管理（ドキュメントの有効/無効化）
- ユーザー行動分析

## 技術スタック

### フロントエンド
- **React** + **TypeScript**
- **Vite** (ビルドツール)
- **Material-UI** (UIコンポーネント)
- **React Router** (ルーティング)

### バックエンド  
- **FastAPI** (Python Web フレームワーク)
- **Supabase** (データベース・認証)
- **Google Gemini API** (AI チャット機能)
- **RAG** (文書検索・回答生成)

### データベース・インフラ
```yaml
データベース: Supabase (PostgreSQL)
認証: JWT ベース
クラウド: AWS EC2
Web サーバー: Nginx (リバースプロキシ)
CI/CD: GitHub Actions
デプロイ: 自動デプロイメント
```

## アーキテクチャ

```mermaid
graph TB
    A[フロントエンド<br/>React + TypeScript] --> B[Nginx<br/>リバースプロキシ]
    B --> C[バックエンド<br/>FastAPI + Python]
    C --> D[Supabase<br/>PostgreSQL Database]
    C --> E[Google Gemini AI<br/>質問応答処理]
    C --> F[ドキュメント処理<br/>PDF, Excel, 動画]
    
    G[GitHub Repository] --> H[GitHub Actions<br/>CI/CD]
    H --> I[AWS EC2<br/>本番環境]
```

## 📁 プロジェクト構成

```
workmate/
├── Chatbot-Backend-main/     # バックエンドAPI（FastAPI + Supabase）
├── Chatbot-Frontend-main/    # フロントエンドUI（React + Vite）
├── docs/                     # ドキュメント類
│   ├── README.md            # プロジェクト概要
│   ├── WORKMATE_USER_GUIDE.md
│   ├── admin-manual.md
│   └── guide-analysis.md
├── scripts/                  # 実行スクリプト類
│   ├── start-production.sh
│   └── start-local.bat
├── public/                   # 静的ファイル
├── supabase/                # Supabaseスキーマ
└── package.json            # プロジェクト設定
```

## 🚀 クイックスタート

### フロントエンド開発サーバー起動
```bash
npm run dev
```

### バックエンド開発サーバー起動
```bash
cd Chatbot-backend-main
python main.py
```

### 本番環境実行
```bash
# Windows
scripts/start-local.bat

# Linux/Mac
scripts/start-production.sh
```

## 📚 ドキュメント

詳細なドキュメントは `docs/` フォルダを参照してください：

- **[ユーザーガイド](docs/WORKMATE_USER_GUIDE.md)** - エンドユーザー向け操作説明
- **[管理者マニュアル](docs/admin-manual.md)** - 管理者向け設定・管理方法
- **[開発ガイド](docs/guide-analysis.md)** - 開発者向け技術情報
- **[プロジェクト分析](docs/data.md)** - システム分析・仕様詳細

## 📝 最近の更新

- ✅ RAGパフォーマンス最適化（チャンクサイズ、コンテキストキャッシュ）
- ✅ プロジェクト構造整理・クリーンアップ
- ✅ ドキュメント統合・整理

## 🤝 開発・サポート

プロジェクトに関する質問や問題は、該当するドキュメントを参照するか、開発チームまでお問い合わせください。

## セットアップ

### 前提条件
- **Node.js** 18以上
- **Python** 3.9以上
- **Git**
- **Google AI API Key**
- **Supabase アカウント**

### 1. リポジトリのクローン
```bash
git clone https://github.com/QueueCorpJP/workmate.git
cd workmate
```

### 2. バックエンドセットアップ
```bash
cd Chatbot-backend-main

# 仮想環境作成・有効化
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# Playwright ブラウザインストール
playwright install

# 環境変数設定 (.env ファイル作成)
cp .env.example .env
# .env ファイルを編集して API キーを設定

# 企業プロキシ環境の場合、以下も追加設定
# HTTP_PROXY=http://proxy.company.com:8080
# HTTPS_PROXY=https://proxy.company.com:8080
# 認証が必要な場合:
# HTTP_PROXY=http://username:password@proxy.company.com:8080
# HTTPS_PROXY=https://username:password@proxy.company.com:8080

# データベース初期化
python -c "from modules.database import init_db; init_db()"

# サーバー起動
python main.py
```

### 3. フロントエンドセットアップ
```bash
cd Chatbot-Frontend-main

# 依存関係インストール
npm install

# 環境変数設定
echo "VITE_API_URL=http://localhost:8085" > .env

# 開発サーバー起動
npm run dev
```

### 4. 一括起動（Windows）
```batch
# すべてのコンポーネントを一度に起動
run_all.bat
```

## 環境変数

### バックエンド環境変数 (.env)
```bash
# Google AI設定
GOOGLE_API_KEY=your_google_api_key_here

# Supabase設定
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# データベース設定（Supabaseの場合は不要な場合もあり）
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chatbot
DB_USER=postgres
DB_PASSWORD=your_password

# アプリケーション設定
COMPANY_NAME="Your Company Name"
PORT=8083

# オプション（使用する場合）
WEBSHAREPROXY_USERNAME=your_proxy_username
WEBSHAREPROXY_PASSWORD=your_proxy_password
ASSEMBLYAI_API_KEY=your_assemblyai_key
```

### フロントエンド環境変数 (.env)
```bash
# API エンドポイント
VITE_API_URL=http://localhost:8085

# 本番環境の場合
VITE_API_URL=https://your-backend-domain.com
```

## 使用方法

### 1. 初回ログイン
- **管理者アカウント**: `queue@queuefood.co.jp` / `John.Queue2025`
- ログイン後、右上の設定から会社名を変更可能

### 2. ドキュメントアップロード
1. 管理者でログイン
2. 「リソース管理」タブに移動
3. 対応ファイルをドラッグ&ドロップまたは選択
4. アップロード完了後、チャットで質問可能

### 3. チャット機能
- 左側パネルでドキュメントまたはURL入力
- 右側でAIとチャット
- 情報ソースが回答と共に表示

### 4. ユーザー管理
- 新規ユーザーの追加・削除
- 利用制限の設定（質問回数、ドキュメント数）
- 利用状況の分析

## API ドキュメント

### 認証エンドポイント
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@company.com",
  "password": "password"
}
```

### チャットエンドポイント
```http
POST /chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "質問内容",
  "employee_id": "user_id",
  "employee_name": "ユーザー名"
}
```

### ドキュメントアップロード
```http
POST /upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

{
  "file": <ファイル>,
  "company_id": "company_id"
}
```

### 詳細なAPI仕様
FastAPIの自動生成ドキュメントを参照：
- **開発環境**: http://localhost:8085/docs
- **本番環境**: https://your-domain.com/docs

## デプロイ

### GitHub Actions による自動デプロイ

#### 必要なGitHub Secrets
```bash
# EC2接続設定
EC2_KEY=<EC2のSSH秘密鍵(.pemファイルの内容)>
EC2_HOST=<EC2のパブリックIP>
EC2_USER=ec2-user
EC2_PATH=/home/ec2-user

# アプリケーション設定
GOOGLE_API_KEY=<Google AI APIキー>
SUPABASE_URL=<Supabase URL>
SUPABASE_KEY=<Supabase Key>
COMPANY_NAME=<会社名>
```

#### デプロイフロー
1. `master` ブランチにプッシュ
2. GitHub Actions が自動実行
3. バックエンド: EC2 に SSH 接続してデプロイ
4. フロントエンド: Vercel または EC2 にデプロイ

### 手動デプロイ（EC2）
```bash
# EC2 に SSH 接続
ssh -i workmate-ai.pem ec2-user@your-ec2-ip

# プロジェクト更新
cd /home/ec2-user/workmate
git pull origin master

# バックエンド再起動
cd Chatbot-backend-main
source venv/bin/activate
pip install -r requirements.txt
pkill -f main.py
nohup python main.py > backend.log 2>&1 &

# フロントエンド更新
cd ../Chatbot-Frontend-main
npm install
npm run build
sudo cp -r dist/* /var/www/html/workmate/
sudo systemctl reload nginx
```

## 管理機能

### 利用状況分析
- **総ユーザー数**: 登録ユーザーの総数
- **アクティブユーザー**: 一週間以内にチャットを使用したユーザー
- **総ドキュメント数**: アップロードされたドキュメント数
- **総質問数**: 累計質問回数
- **制限到達ユーザー**: 利用制限に達したユーザー数

### チャット履歴分析
- 感情分析（ポジティブ、ネガティブ、ニュートラル）
- カテゴリ分類（一般的な質問、技術的な質問など）
- 情報ソースの追跡
- 時系列での利用パターン分析

### リソース管理
- ドキュメントの有効化・無効化
- ファイルサイズ・形式の制限
- 会社別リソース分離
- ドキュメントの利用状況追跡

## トラブルシューティング

### よくある問題

#### 1. バックエンドが起動しない
```bash
# ポート使用状況確認
lsof -i :8083

# 既存プロセス終了
pkill -f main.py

# 仮想環境の確認
which python  # 仮想環境のPythonが使われているか確認
```

#### 2. フロントエンドでAPIに接続できない
```javascript
// Vite設定（vite.config.ts）でプロキシ確認
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:8085'
    }
  }
})
```

#### 3. Supabase接続エラー
```python
# 環境変数の確認
import os
print("SUPABASE_URL:", os.getenv("SUPABASE_URL"))
print("SUPABASE_KEY:", os.getenv("SUPABASE_KEY"))

# Supabase APIキーの権限確認
# anon キーとservice_role キーの違いを確認
```

#### 4. Google AI APIエラー
```python
# APIキーの有効性確認
import google.generativeai as genai
genai.configure(api_key="your_api_key")
model = genai.GenerativeModel('gemini-2.5-flash')
```

#### 5. ファイルアップロードエラー
- ファイルサイズ制限の確認（PDF: 10MB、動画: 500MB）
- ファイル形式の確認
- CORS設定の確認

#### 6. プロキシエラー (407 Proxy Authentication Required)
**症状**: YouTube URL処理時に「プロキシ認証が必要」エラーが発生
```
HTTPSConnectionPool(host='www.youtube.com', port=443): Max retries exceeded 
(Caused by ProxyError('Cannot connect to proxy.', OSError('Tunnel connection failed: 407 Proxy Authentication Required')))
```

**原因**: 企業ネットワークでプロキシ認証が必要だが設定されていない

**解決方法**:
1. **環境変数でプロキシ設定を追加**:
```bash
# .env ファイルに追加
HTTP_PROXY=http://username:password@proxy.company.com:8080
HTTPS_PROXY=https://username:password@proxy.company.com:8080
```

2. **認証情報なしの場合**:
```bash
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=https://proxy.company.com:8080
```

3. **システム環境変数での設定**:
```bash
# Windows PowerShell
$env:HTTP_PROXY="http://proxy.company.com:8080"
$env:HTTPS_PROXY="https://proxy.company.com:8080"

# Linux/Mac
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=https://proxy.company.com:8080
```

4. **プロキシを使わない場合**:
```bash
# 環境変数を削除
unset HTTP_PROXY HTTPS_PROXY
# または .env ファイルから該当行を削除
```

### ログの確認
```
```

## SPA用Nginx設定（現在の設定の修正版）

現在のNginx設定を以下のようにSPA用に変更してください：

```nginx
###############################################################################
# 80番 : HTTP  → HTTPS へリダイレクト（ACME チャレンジのみ許可）
###############################################################################
server {
    listen 80;
    server_name workmatechat.com www.workmatechat.com;

    # Let's Encrypt 用
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # それ以外は HTTPS へ転送
    location / {
        return 301 https://$host$request_uri;
    }
}

###############################################################################
# 443番 : 本番サーバー（SPA + API）
#   フロント  : 静的ファイル配信 (/var/www/html/)
#   バックエンド API : FastAPI (127.0.0.1:8083/chatbot/api/)
###############################################################################
server {
    listen 443 ssl;
    server_name workmatechat.com www.workmatechat.com;

    ssl_certificate     /etc/letsencrypt/live/workmatechat.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/workmatechat.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    ###########################################################################
    # バックエンド API（変更なし）
    ###########################################################################
    location /chatbot/api/ {
        proxy_pass http://127.0.0.1:8083/chatbot/api/;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    ###########################################################################
    # 静的アセット（長期キャッシュ）
    ###########################################################################
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        root /var/www/html;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Access-Control-Allow-Origin "*";
    }

    ###########################################################################
    # フロントエンド（SPA - 静的ファイル配信）
    ###########################################################################
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
        
        # HTMLファイルはキャッシュしない（常に最新版を取得）
        location = /index.html {
            expires -1;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
        }
    }

    ###########################################################################
    # エラーページ
    ###########################################################################
    error_page 404 /404.html;
    location = /404.html { 
        root /var/www/html;
    }

    error_page 500 502 503 504 /50x.html;
    location = /50x.html { 
        root /var/www/html;
    }
}
```

## 🔧 **変更手順**

1. **Nginx設定ファイル編集**:
   ```bash
   sudo nano /etc/nginx/sites-available/default
   # または
   sudo nano /etc/nginx/nginx.conf
   ```

2. **上記設定に置き換え**

3. **設定確認**:
   ```bash
   sudo nginx -t
   ```

4. **Nginx再起動**:
   ```bash
   sudo systemctl reload nginx
   ```

## 🎯 **主な変更点**

| 項目 | 変更前（SSR） | 変更後（SPA） |
|------|---------------|---------------|
| **フロントエンド配信** | `proxy_pass http://18.183.34.30:3000` | `root /var/www/html; try_files $uri $uri/ /index.html` |
| **Node.jsサーバー** | 必要（ポート3000） | 不要 |
| **キャッシュ戦略** | なし | アセット長期キャッシュ + HTML無キャッシュ |
| **SPA対応** | なし | `try_files` でフォールバック |

## ⚡ **メリット**

- **シンプル**: Node.jsプロセス不要
- **高速**: Nginxが直接静的ファイル配信
- **安定**: プロセス管理不要
- **キャッシュ最適化**: 反映遅れを解消