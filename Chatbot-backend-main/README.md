# チャットボットバックエンド

# ローカル開発セットアップ

## リポジトリのクローン

```git
git clone https://github.com/QueueCorpJP/Chatbot-backend.git
cd Chatbot-backend
```

## Python 依存関係のインストール

```bash
python -m venv venv

# macOS/Linuxの場合
source venv/bin/activate

# Windowsの場合
venv\Scripts\activate

# 必要な依存関係をインストール
pip install -r requirements.txt
playwright install  # 重要
```

## PostgreSQL のインストール

Ubuntu の場合:

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

macOS (Homebrew を使用):

```bash
brew install postgresql
```

Windows の場合: PostgreSQL 公式サイトから PostgreSQL をダウンロードしてインストールします。

## PostgreSQL データベースの設定

PostgreSQL をインストールした後、データベースとユーザーを作成する必要があります。

## .env ファイルの設定

プロジェクトのルートディレクトリに .env ファイルを作成し、以下の内容を追加します（プレースホルダーを実際の値に置き換えてください）：

```txt
# ========================================
# サーバー設定（必須）
# ========================================

# バックエンドサーバーのポート番号（必須）
PORT=8083

# 環境設定（development / production）
ENVIRONMENT=development

# CORS許可オリジン（カンマ区切り）
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://chatbot-frontend-nine-eta.vercel.app

# 開発環境でのフロントエンドポート（カンマ区切り）
FRONTEND_PORTS=3000,3025,5173

# 全てのオリジンを許可（開発環境のみ推奨）
ALLOW_ALL_ORIGINS=false

# ========================================
# API設定（必須）
# ========================================

# Gemini API Key（必須）
GEMINI_API_KEY=AI...7I

# YouTube API Key（オプション）
YOUTUBE_API_KEY=your_youtube_api_key_here

# ========================================
# PDF処理設定（オプション）
# ========================================

# Gemini 2.5 Flash OCR設定（最高品質PDF処理）
# GEMINI_API_KEY は上記で設定済み

# カスタムPopplerパス（従来OCR使用時のみ - 非推奨）
# POPPLER_PATH=/path/to/poppler/bin

# 埋め込みモデル設定
EMBEDDING_MODEL=gemini-embedding-001

# ========================================
# レガシー設定（互換性のため）
# ========================================

GOOGLE_API_KEY=AI...7I
COMPANY_NAME="Queue"
WEBSHAREPROXY_USERNAME=xv...ll
WEBSHAREPROXY_PASSWORD=t6...rt
ASSEMBLYAI_API_KEY=12...7b
DB_NAME=chatbot
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

# ========================================
# プロキシ設定（企業環境の場合）
# ========================================

# HTTP_PROXY=http://proxy.company.com:8080
# HTTPS_PROXY=https://proxy.company.com:8080
```

## PDF処理の設定について

このアプリケーションでは、PDFファイルの処理に最新のAI技術を活用した複数の方法を提供しています：

### 🚀 最推奨: Gemini 2.5 Flash OCR（完璧版）

**Gemini 2.5 Flash Vision API** を使用した最高品質のOCR処理：

```bash
# .envファイルにGemini API Key設定（必須）
GEMINI_API_KEY=your_gemini_api_key_here
```

この設定により：
- ✅ **Gemini 2.5 Flash Vision API** で最高精度OCR
- ✅ **PyMuPDF** でPDF→画像変換（Poppler不要）
- ✅ **バッチ処理** による高速化
- ✅ **自動リトライ機能** とエラーハンドリング
- ✅ **画像品質最適化** で認識精度向上
- ✅ **構造化テキスト抽出**（表・リスト・見出し対応）

### 🔄 フォールバック処理

Gemini OCR失敗時の自動フォールバック：
- ✅ **PyMuPDF** でのテキスト直接抽出
- ✅ **PyPDF2** での最終フォールバック処理

### PyMuPDFのインストール（必須）

Gemini 2.5 Flash OCRとフォールバック処理のため、PyMuPDFのインストールが必要です：

```bash
pip install PyMuPDF
```

> **注意**: PyMuPDFは既にrequirements.txtに含まれています。`pip install -r requirements.txt`で自動インストールされます。

### 🔧 従来のOCR（非推奨）

従来のpdf2image + PopplerベースのOCRも利用可能ですが、非推奨です：

#### Windows:
```bash
# Condaを使用
conda install -c conda-forge poppler

# Chocolateyを使用
choco install poppler
```

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

#### macOS:
```bash
brew install poppler
```

> **推奨**: 従来OCRではなく、Gemini 2.5 Flash OCRを使用してください。

## FastAPI アプリの実行

```bash
python main.py
```

サーバーは環境変数PORTで指定されたポート（ローカル例：`http://localhost:8085`、本番例：`http://localhost:8083`）で起動します。

# AWS EC2 上で FastAPI + PostgreSQL アプリケーションを構築・デプロイする手順

# 1. AWS EC2 インスタンスの作成（Amazon Linux 2023 + g4dn.2xlarge）

## (1) AWS にログイン：

https://aws.amazon.com/console/ にアクセスしてログインします。

## (2) EC2 ダッシュボードへ移動：

「EC2」と検索し、ダッシュボードを開きます。

## (3) インスタンスの起動：

「インスタンスを起動」をクリックします。

## (4) Amazon マシンイメージ（AMI）を選択：

Amazon Linux 2023 を選択してください。

## (5) インスタンスタイプを選択：

g4dn.2xlarge を選択します（NVIDIA T4 GPU 搭載、GPU ベースのアプリに最適）。

## (6) キーペアを作成または選択：

SSH 接続用に既存のキーペアを選ぶか、新しく作成してください。

## (7) ストレージ設定：

必要に応じて EBS（SSD）のサイズを増やすことを推奨します（例：50GB〜100GB 以上）。

## (8) セキュリティグループ設定：

以下のポートを開放します：

- 22（SSH）

- 80（HTTP）

- 443（HTTPS）

- 8083（FastAPI のバックエンド）

## (9) インスタンスの起動と接続：

.pem ファイルを使って以下のように SSH 接続します：

```bash
chmod 400 your-key.pem
ssh -i "your-key.pem" ec2-user@your-ec2-ip
```

# 2. AWS EC2 インスタンスへの FastAPI + PostgreSQL アプリケーションのデプロイ手順

## (1) 初期セットアップ：

- PostgreSQL のインストール

```bash
sudo yum clean metadata
sudo yum install -y postgresql15 postgresql15-server
which postgresql-setup
sudo postgresql-setup --initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql
sudo systemctl status postgresql
```

- データベースとユーザーの作成

```bash
sudo -i -u postgres
psql -U postgres -W
// set password
sudo -i -u postgres
psql
\password postgres
```

- 認証方式の設定を変更

```bash
sudo nano /var/lib/pgsql/data/pg_hba.conf
```

- "peer" and "ident" update to "md5"

- PostgreSQL を再起動

```bash
sudo systemctl restart postgresql
```

- 最新のコードをプル：

```git
git clone https://github.com/QueueCorpJP/Chatbot-backend.git
cd Chatbot-backend
```

- 仮想環境の作成：

```bash
python -m venv venv
source venv/bin/activate
```

- 依存パッケージのインストール：

```bash
pip install -r requirements.txt
playwright install
```

- .env ファイルの作成： 例：

```txt
GOOGLE_API_KEY=AI...7I
COMPANY_NAME="Queue"
WEBSHAREPROXY_USERNAME=xv...ll
WEBSHAREPROXY_PASSWORD=t6...rt
ASSEMBLYAI_API_KEY=12...7b
DB_NAME = chatbot
DB_USER = postgres
DB_PASSWORD = yourpassword
DB_HOST = localhost
DB_PORT = 5432
```

- FastAPI アプリの起動：

```bash
python main.py
```

## (2) リバースプロキシ設定（Nginx）：

- Nginx をインストール（未インストールの場合）：

```bash
sudo apt install nginx
```

- Nginx の設定を編集：

```bash
sudo nano /etc/nginx/nginx.conf
```

- 以下を追加または修正：

```nginx
server {
  ...
  location /chatbot/api/ {
    proxy_pass http://127.0.0.1:8083; # バックエンドサービス（ポート 8083）
    proxy_set_header Host $host; # オリジナルの Host ヘッダーを保持
    proxy_set_header X-Real-IP $remote_addr; # クライアントの IP アドレス
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; # IP チェーンの保持
    proxy_set_header X-Forwarded-Proto $scheme; # 使用プロトコルの保持
  }
  ...
}
```

- Nginx を再起動：

```bash
sudo systemctl restart nginx
```

## (3) 起動手順

### systemd を使用する場合：sudo systemctl start chatbot-backend

### ※サービスが未設定の場合は、別途 chatbot-backend.service を /etc/systemd/system/ に作成してください。

## (4) メンテナンス手順

### 最新のコードを取得：git pull

### サービスを再起動：sudo systemctl restart chatbot-backend

### ログを確認：journalctl -u chatbot-backend -f
