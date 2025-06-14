# Workmate AIチャットボット - 完全使用書

## 📋 目次

1. [システム概要](#システム概要)
2. [プロジェクト構成](#プロジェクト構成)
3. [技術仕様](#技術仕様)
4. [環境構築手順](#環境構築手順)
5. [機能詳細](#機能詳細)
6. [ユーザーガイド](#ユーザーガイド)
7. [管理者ガイド](#管理者ガイド)
8. [API仕様](#api仕様)
9. [デプロイメント](#デプロイメント)
10. [トラブルシューティング](#トラブルシューティング)
11. [運用・保守](#運用保守)

---

## システム概要

### Workmate AIチャットボットとは

**Workmate**は、企業内のドキュメントやナレッジベースを活用した高性能AIチャットボットシステムです。Google Gemini 2.0-flash-expを搭載し、PDF、Excel、動画などの多様なフォーマットのドキュメントを処理・分析して、従業員の質問に的確な回答を提供します。

### 🎯 主な特徴

- **🤖 高度なAI応答**: Google Gemini 2.0-flash-exp による高精度な質問応答
- **📁 多様なファイル対応**: PDF（OCR対応）、Excel、テキスト、動画ファイルの処理
- **🏢 マルチテナント**: 企業別の完全なデータ分離
- **👥 権限管理**: 役割ベースのアクセス制御（従業員・ユーザー・管理者）
- **📊 高度な分析**: 6つの視点からのビジネス分析機能
- **🔒 セキュリティ**: 企業レベルのセキュリティ対応

### 利用対象

| 対象 | 主な用途 |
|------|----------|
| **従業員** | 日常業務での情報検索・質問応答 |
| **人事・総務** | 就業規則、各種手続きの案内 |
| **営業部門** | 商品情報、営業資料の活用 |
| **技術部門** | 技術仕様書、開発ガイドラインの参照 |
| **カスタマーサポート** | FAQ、対応マニュアルの活用 |
| **管理者** | システム管理、利用状況分析 |

---

## プロジェクト構成

### ディレクトリ構造

```
workmate/
├── 📁 Chatbot-Frontend-main/          # フロントエンド (React + TypeScript)
│   ├── src/
│   │   ├── components/               # UIコンポーネント
│   │   │   ├── admin/               # 管理者パネル関連
│   │   │   │   ├── AdminPanel.tsx    # メイン管理パネル
│   │   │   │   ├── AnalysisTab.tsx   # 分析タブ
│   │   │   │   ├── ChatHistoryTab.tsx # チャット履歴タブ
│   │   │   │   ├── DemoStatsTab.tsx  # デモ統計タブ
│   │   │   │   ├── EmployeeUsageTab.tsx # 従業員利用状況
│   │   │   │   ├── PlanHistoryTab.tsx # プラン履歴タブ
│   │   │   │   ├── ResourcesTab.tsx  # リソース管理タブ
│   │   │   │   └── UserManagementTab.tsx # ユーザー管理タブ
│   │   │   ├── ApplicationForm.tsx   # 申請フォーム
│   │   │   ├── BillingTab.tsx       # 請求タブ
│   │   │   ├── DemoLimits.tsx       # 利用制限表示
│   │   │   ├── GoogleDriveAuth.tsx  # Google Drive認証
│   │   │   └── SourceCitation.tsx   # ソース引用表示
│   │   ├── contexts/                # React Context
│   │   │   ├── AuthContext.tsx      # 認証コンテキスト
│   │   │   └── CompanyContext.tsx   # 会社コンテキスト
│   │   ├── utils/                   # ユーティリティ
│   │   │   ├── googleConfig.ts      # Google設定
│   │   │   └── validation.ts        # バリデーション
│   │   ├── App.tsx                  # メインアプリケーション
│   │   ├── ChatInterface.tsx        # チャットインターフェース
│   │   ├── LoginPage.tsx            # ログインページ
│   │   ├── AdminPanel.tsx           # 管理者パネル
│   │   ├── CompanySettings.tsx      # 会社設定
│   │   ├── UserGuide.tsx            # ユーザーガイド
│   │   └── api.ts                   # API通信
│   ├── public/                      # 静的ファイル
│   ├── package.json                 # 依存関係定義
│   ├── vite.config.ts              # Vite設定
│   └── vercel.json                  # Vercelデプロイ設定
│
├── 📁 Chatbot-backend-main/           # バックエンド (Python + FastAPI)
│   ├── modules/                     # コアモジュール
│   │   ├── auth.py                  # 認証機能
│   │   ├── chat.py                  # チャット処理
│   │   ├── company.py               # 会社管理
│   │   ├── admin.py                 # 管理者機能
│   │   ├── database.py              # データベース接続
│   │   ├── models.py                # データモデル
│   │   ├── resource.py              # リソース管理
│   │   ├── token_counter.py         # トークン使用量追跡
│   │   ├── knowledge_base.py        # 知識ベース管理
│   │   └── knowledge/               # ドキュメント処理
│   │       ├── api.py               # API関連処理
│   │       ├── base.py              # 基本処理
│   │       ├── excel.py             # Excel処理
│   │       ├── google_drive.py      # Google Drive連携
│   │       ├── ocr.py               # OCR処理
│   │       ├── pdf.py               # PDF処理
│   │       ├── text.py              # テキスト処理
│   │       └── url.py               # URL処理
│   ├── main.py                      # FastAPIアプリケーション
│   ├── requirements.txt             # Python依存関係
│   ├── database_schema.py           # データベーススキーマ
│   ├── supabase_adapter.py          # Supabaseアダプター
│   └── setup_supabase.py            # Supabase初期設定
│
├── 📄 README.md                       # プロジェクト概要
├── 📄 USER_MANUAL.md                  # 技術マニュアル
├── 📄 CLIENT_GUIDE.md                 # クライアントガイド
└── 📄 nginx-workmatechat.conf         # Nginx設定ファイル
```

### ファイル詳細

#### フロントエンド主要ファイル

| ファイル | 機能 | 重要度 |
|----------|------|--------|
| `App.tsx` | メインアプリケーション、ルーティング設定 | ⭐⭐⭐ |
| `ChatInterface.tsx` | チャット画面のメインコンポーネント | ⭐⭐⭐ |
| `AdminPanel.tsx` | 管理者パネルのメインコンポーネント | ⭐⭐⭐ |
| `api.ts` | バックエンドAPIとの通信処理 | ⭐⭐⭐ |
| `contexts/AuthContext.tsx` | 認証状態管理 | ⭐⭐⭐ |
| `contexts/CompanyContext.tsx` | 会社情報管理 | ⭐⭐ |

#### バックエンド主要ファイル

| ファイル | 機能 | 重要度 |
|----------|------|--------|
| `main.py` | FastAPIアプリケーションのエントリーポイント | ⭐⭐⭐ |
| `modules/chat.py` | チャット処理とAI応答生成 | ⭐⭐⭐ |
| `modules/auth.py` | 認証・認可機能 | ⭐⭐⭐ |
| `modules/admin.py` | 管理者機能 | ⭐⭐⭐ |
| `modules/database.py` | データベース接続管理 | ⭐⭐⭐ |
| `modules/knowledge_base.py` | 知識ベース管理 | ⭐⭐⭐ |
| `supabase_adapter.py` | Supabaseとの連携 | ⭐⭐⭐ |

---

## 技術仕様

### フロントエンド技術スタック

```json
{
  "フレームワーク": "React 18.2.0",
  "言語": "TypeScript 5.3.3",
  "ビルドツール": "Vite 5.1.3",
  "UIライブラリ": "Material-UI 5.15.10",
  "ルーティング": "React Router 6.22.1",
  "HTTP通信": "Axios >= 1.8.2",
  "チャート": "Chart.js 4.4.1",
  "ファイルアップロード": "React Dropzone 14.2.3",
  "認証": "Google Auth Library 10.0.0-rc.3",
  "状態管理": "React Context API"
}
```

### バックエンド技術スタック

```python
{
    "フレームワーク": "FastAPI 0.109.2",
    "Webサーバー": "Uvicorn 0.27.1",
    "AI": "Google Generative AI 0.3.2 (Gemini 2.0-flash-exp)",
    "データ処理": "Pandas 2.2.0",
    "ドキュメント処理": {
        "PDF": "PyPDF2 3.0.1, PyMuPDF 1.23.7",
        "Excel": "openpyxl 3.1.2",
        "OCR": "pdf2image 1.16.3, Pillow >= 10.3.0",
        "画像": "Pillow >= 10.3.0"
    },
    "Web処理": {
        "スクレイピング": "BeautifulSoup4 4.12.2",
        "ブラウザ自動化": "Playwright",
        "動画処理": "yt-dlp, youtube_transcript_api"
    },
    "データベース": "PostgreSQL (Supabase), psycopg2-binary 2.9.10",
    "非同期処理": "asyncpg 0.30.0, aiofiles 24.1.0",
    "その他": "boto3 1.37.22, tiktoken"
}
```

### データベース設計

#### 主要テーブル

**1. ユーザー管理 (users)**
```sql
CREATE TABLE users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'employee',
    company_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**2. 会社管理 (companies)**
```sql
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    plan_type VARCHAR(50) DEFAULT 'demo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**3. チャット履歴 (chat_history)**
```sql
CREATE TABLE chat_history (
    id VARCHAR(255) PRIMARY KEY,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    category VARCHAR(100),
    sentiment VARCHAR(20),
    employee_id VARCHAR(255),
    employee_name VARCHAR(255),
    source_document VARCHAR(255),
    source_page VARCHAR(50),
    user_id VARCHAR(255),
    company_id INTEGER
);
```

**4. 利用制限 (usage_limits)**
```sql
CREATE TABLE usage_limits (
    user_id VARCHAR(255) PRIMARY KEY,
    document_uploads_used INT DEFAULT 0,
    document_uploads_limit INT DEFAULT 3,
    questions_used INT DEFAULT 0,
    questions_limit INT DEFAULT 200,
    is_unlimited BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**5. ドキュメントソース (document_sources)**
```sql
CREATE TABLE document_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    content TEXT,
    uploaded_by VARCHAR(255),
    company_id INTEGER,
    active BOOLEAN DEFAULT TRUE,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 環境構築手順

### 前提条件

- **Node.js**: 18.0.0 以上
- **Python**: 3.9 以上
- **Git**: 最新版
- **Google AI API Key**: Gemini API の利用権限
- **Supabase アカウント**: データベース用

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-repo/workmate.git
cd workmate
```

### 2. バックエンド環境構築

#### 2.1 依存関係のインストール

```bash
cd Chatbot-backend-main

# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt

# Playwrightブラウザのインストール
playwright install
```

#### 2.2 環境変数の設定

`.env` ファイルを作成：

```bash
# Google AI設定
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Supabase設定
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# アプリケーション設定
COMPANY_NAME="Your Company Name"
PORT=8083

# オプション設定（プロキシ環境の場合）
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=https://proxy.company.com:8080

# 認証が必要なプロキシの場合
# HTTP_PROXY=http://username:password@proxy.company.com:8080
# HTTPS_PROXY=https://username:password@proxy.company.com:8080

# AssemblyAI（音声処理用、オプション）
ASSEMBLYAI_API_KEY=your_assemblyai_key

# WebShare Proxy（オプション）
WEBSHAREPROXY_USERNAME=your_proxy_username
WEBSHAREPROXY_PASSWORD=your_proxy_password
```

#### 2.3 データベース初期化

```bash
# Supabaseのセットアップ
python setup_supabase.py

# または手動でデータベース初期化
python -c "from modules.database import init_db; init_db()"
```

#### 2.4 バックエンドサーバー起動

```bash
# 開発環境での起動
python main.py

# または uvicorn での起動
uvicorn main:app --host 0.0.0.0 --port 8083 --reload
```

### 3. フロントエンド環境構築

#### 3.1 依存関係のインストール

```bash
cd Chatbot-Frontend-main

# 依存関係のインストール
npm install
```

#### 3.2 環境変数の設定

`.env` ファイルを作成：

```bash
# 開発環境
VITE_API_URL=http://localhost:8083

# 本番環境
# VITE_API_URL=https://your-backend-domain.com
```

#### 3.3 フロントエンドサーバー起動

```bash
# 開発サーバーの起動
npm run dev

# ビルド（本番用）
npm run build
```

### 4. 動作確認

1. **バックエンド確認**: http://localhost:8083/docs でAPI仕様を確認
2. **フロントエンド確認**: http://localhost:5173 でアプリケーションにアクセス
3. **初期ログイン**: 
   - メール: `queue@queuefood.co.jp`
   - パスワード: `John.Queue2025`

---

## 機能詳細

### 🤖 AI チャット機能

#### 概要
Google Gemini 2.0-flash-exp を使用した高精度な質問応答システム

#### 主要機能

**1. 質問応答処理**
- 自然言語での質問受付
- 知識ベースに基づく回答生成
- 情報ソースの明示
- 会話履歴の考慮（最大5メッセージ）

**2. 感情・カテゴリ分析**
- 質問の感情分析（ポジティブ・ネガティブ・ニュートラル）
- カテゴリ自動分類
- ビジネス分析への活用

**3. 利用制限管理**
- デモプラン: 10質問/月
- 本格プラン: 無制限
- リアルタイム制限チェック

#### 実装詳細

```python
# modules/chat.py の主要機能

async def process_chat(message: ChatMessage, db: Connection, current_user: dict):
    """
    チャットメッセージの処理フロー:
    1. 利用制限チェック
    2. 会社固有の知識ベース取得
    3. 会話履歴の構築
    4. Gemini API による回答生成
    5. 感情・カテゴリ分析
    6. データベース保存
    7. 利用制限更新
    """
```

### 📁 ドキュメント処理機能

#### サポートファイル形式

| 形式 | 最大サイズ | 対応機能 | 処理エンジン |
|------|-----------|----------|-------------|
| **PDF** | 10MB | OCR、複数ページ、画像抽出 | PyPDF2, PyMuPDF, pdf2image |
| **Excel** | 5MB | 複数シート、データ分析 | openpyxl, pandas |
| **テキスト** | 2MB | プレーンテキスト、Markdown | 内蔵処理 |
| **動画** | 500MB | 字幕抽出、音声転写 | yt-dlp, AssemblyAI |
| **URL** | 制限なし | Webスクレイピング | Playwright, BeautifulSoup |

#### 処理フロー

```python
# modules/knowledge/ の処理フロー

# 1. PDF処理 (modules/knowledge/pdf.py)
async def process_pdf_file(content: bytes, file_name: str):
    """
    PDF処理:
    1. テキスト抽出
    2. OCR処理（画像ベースPDF）
    3. ページ分割
    4. DataFrame変換
    """

# 2. Excel処理 (modules/knowledge/excel.py)
def process_excel_file(content: bytes, file_name: str):
    """
    Excel処理:
    1. 複数シート読込
    2. データ型自動判定
    3. 表形式データの構造化
    """

# 3. URL処理 (modules/knowledge/url.py)
async def extract_text_from_url(url: str):
    """
    URL処理:
    1. Playwright での動的コンテンツ取得
    2. BeautifulSoup でのHTML解析
    3. メタデータ抽出
    """
```

### 👥 ユーザー管理機能

#### 権限体系

| 役割 | 権限 | アクセス範囲 |
|------|------|-------------|
| **employee** | チャット機能のみ | 自分のデータのみ |
| **user** | チャット + 管理機能 | 同一会社のデータ |
| **admin** | システム全体管理 | 全データ（制限あり） |
| **特別管理者** | 全権限 | 全データ・全機能 |

#### 実装詳細

```python
# modules/auth.py の認証フロー

def authenticate_user(email: str, password: str, db: Connection):
    """
    認証フロー:
    1. Basic認証（email:password）
    2. パスワードハッシュ検証
    3. 権限情報取得
    4. 会社情報取得
    """

def check_usage_limits(user_id: str, action_type: str, db: Connection):
    """
    利用制限チェック:
    1. 現在の使用量取得
    2. 制限値との比較
    3. 無制限フラグ確認
    """
```

### 📊 分析機能

#### 6つの分析視点

**1. 頻繁なトピックとトレンド**
- よく質問される内容の傾向分析
- 時系列での変化追跡

**2. 効率化機会**
- 業務プロセス改善の提案
- 自動化可能な作業の特定

**3. フラストレーションポイント**
- ユーザーの困りごと分析
- ネガティブ感情の傾向

**4. 製品・サービス改善提案**
- チャット内容から見える改善案
- 顧客ニーズの洞察

**5. コミュニケーションギャップ**
- 情報伝達の課題特定
- 部門間の連携問題

**6. 具体的推奨アクション**
- 実行可能な改善策
- 優先度付きアクションアイテム

#### 実装詳細

```python
# modules/admin.py の分析機能

async def analyze_chats(user_id: str, db: Connection, company_id: str):
    """
    チャット分析フロー:
    1. データ取得（ユーザー/会社/全体）
    2. 統計計算（カテゴリ、感情、時系列）
    3. AI による洞察生成
    4. ビジネス向けの提案作成
    """
```

---

## ユーザーガイド

### 🚀 利用開始手順

#### 1. アカウント登録

1. **Webサイトアクセス**: `https://workmatechat.com`
2. **新規登録**: 
   - メールアドレス
   - パスワード（8文字以上）
   - 氏名
   - 会社名
3. **自動ログイン**: 登録完了後、自動的にログイン状態

#### 2. 初回設定

1. **会社名設定**: 右上設定メニューから正式名称に変更
2. **知識ベース構築**: 関連文書をアップロード
3. **従業員招待**: 管理者権限がある場合、従業員アカウント作成

### 💬 チャット機能の使用方法

#### 基本操作

1. **質問入力**: 画面下部のテキストエリアに質問を入力
2. **送信**: Enter キーまたは送信ボタンをクリック
3. **AI回答**: 数秒で知識ベースに基づく回答を表示
4. **出典確認**: 回答の根拠となった文書名を確認

#### 効果的な質問のコツ

| ❌ 悪い例 | ✅ 良い例 |
|-----------|----------|
| 「売上について」 | 「2024年12月の売上実績と前年同月比を教えて」 |
| 「手続きは？」 | 「新入社員の入社手続きの流れを詳しく教えて」 |
| 「エラーが出る」 | 「ログイン時に『認証エラー』が表示される場合の対処法」 |

#### 会話機能

- **継続会話**: 前の質問への追加質問や詳細確認が可能
- **履歴参照**: 最大5つ前の会話を考慮した回答
- **文脈理解**: 「それについて詳しく」などの指示語にも対応

### 📄 ファイルアップロード

#### 対応形式と制限

| ファイル形式 | 最大サイズ | 特徴 |
|-------------|-----------|------|
| PDF | 10MB | OCR対応、複数ページ |
| Excel (xlsx/xls) | 5MB | 複数シート対応 |
| テキスト (.txt) | 2MB | プレーンテキスト |
| 動画 (mp4/avi/webm) | 500MB | 字幕・音声抽出 |

#### アップロード手順

1. **ファイル選択**: ドラッグ&ドロップ または ファイル選択ボタン
2. **自動処理**: システムが自動的に内容を解析・学習
3. **完了確認**: 処理完了通知を確認
4. **チャットテスト**: アップロードした内容について質問

#### ベストプラクティス

- **ファイル名**: わかりやすい名前を付ける（例：営業マニュアル_2024年版.pdf）
- **内容の質**: 正確で最新の情報のみアップロード
- **定期更新**: 古い情報は無効化し、最新版をアップロード
- **カテゴリ分け**: 部署別・用途別に整理

### 🌐 URL登録機能

#### 対応サイト

- **企業サイト**: 製品ページ、FAQ、ニュース
- **ドキュメント**: Confluence、Notion、Google Docs
- **動画**: YouTube（字幕あり）
- **一般サイト**: 技術記事、業界情報

#### 登録手順

1. **URL入力**: 対象サイトのURLを入力
2. **自動取得**: システムが自動的にコンテンツを取得
3. **処理確認**: 取得内容をプレビューで確認
4. **知識ベース追加**: 承認後、チャットで利用可能

---

## 管理者ガイド

### 🎛️ 管理者パネル

#### アクセス方法

- **対象ユーザー**: role が 'user' または 'admin' のユーザー
- **アクセス**: ログイン後、自動的に管理者メニューが表示

#### メイン機能

1. **ユーザー管理**: 従業員の追加・削除・権限設定
2. **チャット履歴**: 全社員のチャット内容確認
3. **分析機能**: 6つの視点からのビジネス分析
4. **リソース管理**: アップロードファイルの有効/無効切り替え
5. **使用統計**: 利用状況の可視化
6. **デモ統計**: デモユーザーの利用状況

### 👥 ユーザー管理

#### 従業員の追加

1. **ユーザー管理タブ**: 管理者パネルから選択
2. **新規作成**:
   ```
   メールアドレス: 従業員のメールアドレス
   パスワード: 初期パスワード（8文字以上）
   氏名: フルネーム
   役割: employee（チャットのみ）/ user（管理権限付き）
   ```
3. **登録完了**: 認証情報を従業員に共有

#### 権限管理

| 権限レベル | 設定方法 | アクセス範囲 |
|-----------|----------|-------------|
| **employee** | 新規作成時に選択 | チャット機能のみ |
| **user** | 管理者が設定 | 管理機能アクセス可能 |
| **admin** | 特別管理者のみ設定可能 | システム全体管理 |

#### 利用制限設定

```javascript
// デモプランの制限
{
  "questions_limit": 10,        // 月間質問数
  "document_uploads_limit": 2,  // アップロード可能ファイル数
  "is_unlimited": false         // 制限フラグ
}

// 本格プランの設定
{
  "is_unlimited": true          // 無制限利用
}
```

### 📊 分析機能

#### チャット履歴分析

**基本分析**
- 期間別利用状況
- カテゴリ別分類
- 感情分析結果
- ユーザー別活動状況

**詳細分析（AI駆動）**
1. **頻繁なトピック**: よく質問される内容の傾向
2. **効率化機会**: 業務プロセス改善提案
3. **フラストレーション**: ユーザーの困りごと
4. **改善提案**: 製品・サービスの改善案
5. **コミュニケーションギャップ**: 情報伝達の課題
6. **推奨アクション**: 具体的な改善策

#### 分析レポート活用

**月次レポート作成**
1. **データ期間**: 分析対象期間を設定
2. **分析実行**: AIによる詳細分析を実行
3. **レポート生成**: ビジネス向けの洞察レポート
4. **アクション計画**: 改善策の優先順位付け

**部門別分析**
- 人事・総務: 制度案内の充実度
- 営業: 製品知識の習得状況
- 技術: 開発プロセスの課題
- サポート: 顧客対応の改善点

### 🗂️ リソース管理

#### ファイル管理

**一覧表示**
- アップロード済みファイル一覧
- ファイル形式・サイズ・アップロード日時
- アクティブ状態（有効/無効）

**操作機能**
- **有効化/無効化**: チェックボックスで一括操作
- **削除**: 不要なファイルの削除
- **プレビュー**: ファイル内容の確認

#### 知識ベース最適化

**定期メンテナンス**
1. **月次レビュー**: 利用頻度の低いファイルの見直し
2. **内容更新**: 古い情報の無効化と新情報の追加
3. **品質管理**: 不正確な情報源の除外
4. **カテゴリ整理**: 体系的な分類の維持

### 📈 使用統計・監視

#### 全体統計

```javascript
// 統計指標
{
  "total_users": 50,           // 総ユーザー数
  "active_users": 30,          // アクティブユーザー（7日以内）
  "total_documents": 25,       // 総ドキュメント数
  "total_questions": 500,      // 総質問数
  "limit_reached_users": 5,    // 制限到達ユーザー数
  "total_companies": 3         // 総会社数
}
```

#### ユーザー別詳細

- **利用頻度**: 日別・週別・月別の質問数
- **アクティビティ**: 最終ログイン、活動パターン
- **制限状況**: 使用量と残り制限
- **よく使用するカテゴリ**: 質問傾向の分析

---

## API仕様

### 認証方式

```http
Authorization: Basic <base64(email:password)>
Content-Type: application/json
```

### 主要エンドポイント

#### 1. 認証関連

**ログイン**
```http
POST /chatbot/api/auth/login
Content-Type: application/json

Request:
{
  "email": "user@company.com",
  "password": "password"
}

Response:
{
  "user": {
    "id": "user_id",
    "email": "user@company.com",
    "name": "ユーザー名",
    "role": "user",
    "company_id": 1
  },
  "message": "ログイン成功"
}
```

**ユーザー情報取得**
```http
GET /chatbot/api/auth/me
Authorization: Basic <credentials>

Response:
{
  "id": "user_id",
  "email": "user@company.com",
  "name": "ユーザー名",
  "role": "user",
  "company_id": 1
}
```

#### 2. チャット機能

**チャット送信**
```http
POST /chatbot/api/chat
Authorization: Basic <credentials>
Content-Type: application/json

Request:
{
  "text": "質問内容",
  "user_id": "user_id",
  "employee_id": "employee_id",
  "employee_name": "従業員名"
}

Response:
{
  "response": "AI回答",
  "source": "情報ソース名 (P.1)",
  "remaining_questions": 9,
  "limit_reached": false
}
```

#### 3. ファイル処理

**ファイルアップロード**
```http
POST /chatbot/api/upload-knowledge
Authorization: Basic <credentials>
Content-Type: multipart/form-data

Form Data:
- file: <PDF/Excel/Text/Video file>
- description: "ファイルの説明"

Response:
{
  "message": "ファイルがアップロードされ、処理されました",
  "filename": "document.pdf",
  "size": 1024000,
  "type": "pdf"
}
```

**URL登録**
```http
POST /chatbot/api/submit-url
Authorization: Basic <credentials>
Content-Type: application/json

Request:
{
  "url": "https://example.com",
  "description": "サイトの説明"
}

Response:
{
  "message": "URLの内容を取得し、知識ベースに追加しました",
  "url": "https://example.com",
  "title": "ページタイトル"
}
```

#### 4. 管理者機能

**チャット履歴取得**
```http
GET /chatbot/api/admin/chat-history
Authorization: Basic <credentials>

Query Parameters:
- user_id (optional): 特定ユーザーの履歴
- start_date (optional): 開始日
- end_date (optional): 終了日

Response:
[
  {
    "id": "chat_id",
    "user_message": "質問",
    "bot_response": "回答",
    "timestamp": "2024-01-01T10:00:00Z",
    "employee_name": "田中太郎",
    "category": "一般",
    "sentiment": "positive",
    "source_document": "マニュアル.pdf",
    "source_page": "1"
  }
]
```

**詳細分析**
```http
POST /chatbot/api/admin/detailed-analysis
Authorization: Basic <credentials>
Content-Type: application/json

Request:
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "user_id": "user_id" // optional
}

Response:
{
  "total_messages": 100,
  "category_distribution": [
    {"category": "一般", "count": 50},
    {"category": "技術", "count": 30}
  ],
  "sentiment_distribution": [
    {"sentiment": "positive", "count": 60},
    {"sentiment": "neutral", "count": 30}
  ],
  "insights": "詳細な分析結果..."
}
```

**ユーザー管理**
```http
POST /chatbot/api/admin/create-employee
Authorization: Basic <credentials>
Content-Type: application/json

Request:
{
  "email": "new@company.com",
  "password": "initial_password",
  "name": "新しい従業員",
  "role": "employee"
}

Response:
{
  "message": "従業員が正常に作成されました",
  "employee": {
    "id": "new_employee_id",
    "email": "new@company.com",
    "name": "新しい従業員",
    "role": "employee"
  }
}
```

**リソース管理**
```http
GET /chatbot/api/admin/resources
Authorization: Basic <credentials>

Response:
[
  {
    "id": 1,
    "name": "マニュアル.pdf",
    "type": "pdf",
    "active": true,
    "uploaded_by": "user_id",
    "uploaded_at": "2024-01-01T10:00:00Z",
    "size": 1024000
  }
]

PUT /chatbot/api/admin/resources/{resource_id}/toggle
Authorization: Basic <credentials>

Response:
{
  "message": "リソースの状態を更新しました",
  "active": false
}
```

#### 5. エラーレスポンス

```http
HTTP/1.1 400 Bad Request
{
  "detail": "リクエストが無効です"
}

HTTP/1.1 401 Unauthorized
{
  "detail": "認証が必要です"
}

HTTP/1.1 403 Forbidden
{
  "detail": "アクセス権限がありません"
}

HTTP/1.1 429 Too Many Requests
{
  "detail": "質問回数の制限に達しました"
}

HTTP/1.1 500 Internal Server Error
{
  "detail": "サーバー内部エラーが発生しました"
}
```

---

## デプロイメント

### 本番環境構成

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Vercel        │    │    AWS EC2   │    │   Supabase      │
│   Frontend      │───▶│   Backend    │───▶│   PostgreSQL    │
│   (Static)      │    │   FastAPI    │    │   Database      │
└─────────────────┘    └──────────────┘    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │   Google Cloud  │
                    │   Gemini API    │
                    └─────────────────┘
```

### 1. バックエンドデプロイ（AWS EC2）

#### EC2インスタンス準備

```bash
# Ubuntu 20.04 LTS 推奨
sudo apt update
sudo apt install -y python3-pip nginx certbot python3-certbot-nginx git

# Pythonとpipの最新化
sudo apt install -y python3.9 python3.9-venv python3.9-dev
```

#### アプリケーションデプロイ

```bash
# プロジェクトクローン
sudo mkdir -p /var/www
sudo chown $USER:$USER /var/www
cd /var/www
git clone https://github.com/your-repo/workmate.git
cd workmate/Chatbot-backend-main

# Python仮想環境
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install

# 環境変数設定
sudo nano /etc/environment
# 本番用環境変数を設定
```

#### systemd サービス設定

```bash
sudo nano /etc/systemd/system/workmate-backend.service
```

```ini
[Unit]
Description=Workmate Chatbot Backend
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/workmate/Chatbot-backend-main
Environment=PATH=/var/www/workmate/Chatbot-backend-main/venv/bin
EnvironmentFile=/etc/environment
ExecStart=/var/www/workmate/Chatbot-backend-main/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8083
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# サービス有効化・起動
sudo systemctl enable workmate-backend
sudo systemctl start workmate-backend
sudo systemctl status workmate-backend
```

#### Nginx設定

```bash
sudo nano /etc/nginx/sites-available/workmate
```

```nginx
# HTTPリダイレクト
server {
    listen 80;
    server_name workmatechat.com www.workmatechat.com;
    
    # Let's Encrypt認証
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # HTTPSリダイレクト
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS メインサーバー
server {
    listen 443 ssl http2;
    server_name workmatechat.com www.workmatechat.com;
    
    # SSL証明書
    ssl_certificate /etc/letsencrypt/live/workmatechat.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/workmatechat.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS;
    ssl_prefer_server_ciphers off;
    
    # セキュリティヘッダー
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # ファイルサイズ制限
    client_max_body_size 500M;
    
    # API プロキシ
    location /chatbot/api/ {
        proxy_pass http://127.0.0.1:8083/chatbot/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # タイムアウト設定
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # WebSocket対応
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 静的ファイル（SPA対応）
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
        
        # キャッシュ設定
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # HTMLファイルはキャッシュしない
        location = /index.html {
            expires -1;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
        }
    }
    
    # エラーページ
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
}
```

```bash
# Nginx設定有効化
sudo ln -s /etc/nginx/sites-available/workmate /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### SSL証明書取得

```bash
# Let's Encrypt証明書取得
sudo certbot --nginx -d workmatechat.com -d www.workmatechat.com

# 自動更新設定
sudo crontab -e
# 以下を追加:
0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. フロントエンドデプロイ（Vercel）

#### Vercel設定ファイル

```json
{
  "name": "workmate-frontend",
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": { "distDir": "dist" }
    }
  ],
  "routes": [
    {
      "src": "/chatbot/api/(.*)",
      "dest": "https://workmatechat.com/chatbot/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ],
  "env": {
    "VITE_API_URL": "https://workmatechat.com"
  }
}
```

#### デプロイ手順

1. **Vercelアカウント作成**: GitHub連携
2. **プロジェクト設定**:
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Root Directory: `Chatbot-Frontend-main`
3. **環境変数設定**:
   ```
   VITE_API_URL=https://workmatechat.com
   ```
4. **自動デプロイ**: masterブランチへのpushで自動デプロイ

### 3. CI/CDパイプライン

#### GitHub Actions設定

**.github/workflows/deploy-backend.yml**
```yaml
name: Deploy Backend to EC2

on:
  push:
    branches: [ master ]
    paths: 
      - 'Chatbot-backend-main/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Deploy to EC2
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.EC2_HOST }}
        username: ${{ secrets.EC2_USER }}
        key: ${{ secrets.EC2_SSH_KEY }}
        script: |
          cd /var/www/workmate
          git pull origin master
          cd Chatbot-backend-main
          source venv/bin/activate
          pip install -r requirements.txt
          sudo systemctl restart workmate-backend
          sudo systemctl status workmate-backend
```

**.github/workflows/deploy-frontend.yml**
```yaml
name: Deploy Frontend to Vercel

on:
  push:
    branches: [ master ]
    paths: 
      - 'Chatbot-Frontend-main/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: 'Chatbot-Frontend-main/package-lock.json'
        
    - name: Install dependencies
      run: |
        cd Chatbot-Frontend-main
        npm ci
        
    - name: Build application
      run: |
        cd Chatbot-Frontend-main
        npm run build
        
    - name: Deploy to Vercel
      uses: amondnet/vercel-action@v20
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.ORG_ID }}
        vercel-project-id: ${{ secrets.PROJECT_ID }}
        working-directory: ./Chatbot-Frontend-main
```

#### 必要なGitHub Secrets

```bash
# EC2接続設定
EC2_HOST=your-ec2-public-ip
EC2_USER=ubuntu
EC2_SSH_KEY=<EC2のSSH秘密鍵内容>

# Vercel設定
VERCEL_TOKEN=<Vercelのアクセストークン>
ORG_ID=<VercelのOrganization ID>
PROJECT_ID=<VercelのProject ID>

# アプリケーション設定
GOOGLE_API_KEY=<Google Gemini APIキー>
SUPABASE_URL=<Supabase URL>
SUPABASE_KEY=<Supabase API Key>
```

### 4. 本番環境監視

#### サーバー監視

```bash
# システム監視スクリプト
sudo nano /usr/local/bin/workmate-monitor.sh
```

```bash
#!/bin/bash

# Workmate監視スクリプト
LOG_FILE="/var/log/workmate-monitor.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] 監視開始" >> $LOG_FILE

# バックエンドサービスチェック
if systemctl is-active --quiet workmate-backend; then
    echo "[$TIMESTAMP] Backend: OK" >> $LOG_FILE
else
    echo "[$TIMESTAMP] Backend: ERROR - 再起動中" >> $LOG_FILE
    sudo systemctl restart workmate-backend
fi

# Nginx チェック
if systemctl is-active --quiet nginx; then
    echo "[$TIMESTAMP] Nginx: OK" >> $LOG_FILE
else
    echo "[$TIMESTAMP] Nginx: ERROR - 再起動中" >> $LOG_FILE
    sudo systemctl restart nginx
fi

# ディスク使用量チェック
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "[$TIMESTAMP] DISK: WARNING - 使用量 ${DISK_USAGE}%" >> $LOG_FILE
fi

# メモリ使用量チェック
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.2f", $3*100/$2}')
echo "[$TIMESTAMP] Memory: ${MEMORY_USAGE}%" >> $LOG_FILE

echo "[$TIMESTAMP] 監視完了" >> $LOG_FILE
```

```bash
# 監視スクリプトを実行可能にし、cronに登録
sudo chmod +x /usr/local/bin/workmate-monitor.sh
sudo crontab -e
# 以下を追加（5分毎に監視）:
*/5 * * * * /usr/local/bin/workmate-monitor.sh
```

#### ログローテーション

```bash
sudo nano /etc/logrotate.d/workmate
```

```
/var/log/workmate-monitor.log {
    daily
    missingok
    rotate 30
    compress
    create 644 root root
}

/var/www/workmate/Chatbot-backend-main/backend.log {
    daily
    missingok
    rotate 7
    compress
    create 644 www-data www-data
    postrotate
        systemctl reload workmate-backend
    endscript
}
```

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. 認証・ログイン関連

**問題**: 「認証に失敗しました」エラー

**原因と解決方法**:
```bash
# 1. 認証情報確認
echo "dXNlckBleGFtcGxlLmNvbTpwYXNzd29yZA==" | base64 -d
# → user@example.com:password

# 2. データベース接続確認
python3 -c "
from modules.database import get_db
try:
    db = next(get_db())
    print('Database: OK')
except Exception as e:
    print(f'Database Error: {e}')
"

# 3. ユーザー存在確認
python3 -c "
from supabase_adapter import select_data
result = select_data('users', filters={'email': 'user@example.com'})
print(f'User exists: {bool(result.data)}')
"
```

#### 2. AI応答関連

**問題**: AI回答が遅い・回答しない

**診断手順**:
```bash
# 1. Gemini APIキー確認
python3 -c "
import os
print(f'API Key configured: {bool(os.getenv(\"GOOGLE_API_KEY\"))}')
"

# 2. API接続テスト
python3 -c "
import google.generativeai as genai
import os
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
try:
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content('テスト')
    print('Gemini API: OK')
    print(f'Response: {response.text[:50]}...')
except Exception as e:
    print(f'Gemini API Error: {e}')
"

# 3. 知識ベース確認
python3 -c "
from modules.resource import get_active_resources_by_company_id
import asyncio
async def check():
    resources = await get_active_resources_by_company_id(1, None)
    print(f'Active resources: {len(resources)}')
asyncio.run(check())
"
```

**問題**: 「知識ベースに関連情報が見つかりません」

**解決方法**:
```bash
# 1. リソース状態確認
python3 -c "
from supabase_adapter import select_data
result = select_data('document_sources', columns='name, active, company_id')
for doc in result.data:
    print(f'{doc[\"name\"]}: active={doc[\"active\"]}, company={doc[\"company_id\"]}')
"

# 2. リソース再有効化
python3 -c "
from supabase_adapter import update_data
update_data('document_sources', {'active': True}, {'id': 'resource_id'})
"
```

#### 3. ファイルアップロード関連

**問題**: ファイルアップロードに失敗

**診断・解決**:
```bash
# 1. ファイルサイズ確認
ls -lh uploaded_file.pdf
# PDF: 10MB以下, Excel: 5MB以下, Video: 500MB以下

# 2. ファイル形式確認
file uploaded_file.pdf
# 期待値: PDF document, Microsoft Excel, etc.

# 3. 処理エンジン確認
python3 -c "
try:
    import PyPDF2, pymupdf, openpyxl, pandas
    print('Document processors: OK')
except ImportError as e:
    print(f'Missing dependency: {e}')
"

# 4. OCR機能確認
python3 -c "
try:
    from PIL import Image
    import pdf2image
    print('OCR support: OK')
except ImportError as e:
    print(f'OCR Error: {e}')
"
```

#### 4. システム負荷・パフォーマンス

**問題**: システムが重い・応答が遅い

**パフォーマンス診断**:
```bash
# 1. システムリソース確認
top -b -n1 | head -10
free -h
df -h

# 2. プロセス確認
ps aux | grep -E "(python|uvicorn|nginx)"

# 3. ネットワーク確認
netstat -tlnp | grep -E "(8083|80|443)"

# 4. ログ確認
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
journalctl -u workmate-backend -f
```

**最適化手順**:
```bash
# 1. バックエンド最適化
# uvicorn のワーカー数調整
ExecStart=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8083 --workers 4

# 2. Nginx最適化
# /etc/nginx/nginx.conf に追加
worker_processes auto;
worker_connections 1024;

# 3. データベース接続プール
# modules/database.py で調整
asyncpg.create_pool(min_size=5, max_size=20)
```

#### 5. データベース関連

**問題**: データベース接続エラー

**診断手順**:
```bash
# 1. Supabase接続確認
python3 -c "
import os
from supabase import create_client
try:
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )
    result = supabase.table('users').select('id').limit(1).execute()
    print('Supabase: OK')
except Exception as e:
    print(f'Supabase Error: {e}')
"

# 2. 環境変数確認
echo "SUPABASE_URL: $SUPABASE_URL"
echo "SUPABASE_KEY: ${SUPABASE_KEY:0:20}..."

# 3. テーブル存在確認
python3 -c "
from supabase_adapter import select_data
tables = ['users', 'companies', 'chat_history', 'document_sources', 'usage_limits']
for table in tables:
    try:
        result = select_data(table, limit=1)
        print(f'{table}: OK ({len(result.data)} records)')
    except Exception as e:
        print(f'{table}: ERROR - {e}')
"
```

#### 6. プロキシ・ネットワーク関連

**問題**: プロキシ認証エラー (407 Proxy Authentication Required)

**解決方法**:
```bash
# 1. 環境変数でプロキシ設定
export HTTP_PROXY=http://username:password@proxy.company.com:8080
export HTTPS_PROXY=https://username:password@proxy.company.com:8080

# 2. .env ファイルに追加
echo "HTTP_PROXY=http://proxy.company.com:8080" >> .env
echo "HTTPS_PROXY=https://proxy.company.com:8080" >> .env

# 3. プロキシ回避設定
export NO_PROXY=localhost,127.0.0.1,supabase.co

# 4. Playwright プロキシ設定
python3 -c "
from playwright.async_api import async_playwright
async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            proxy={'server': 'http://proxy.company.com:8080'}
        )
"
```

#### 7. SSL/TLS証明書関連

**問題**: SSL証明書エラー

**診断・解決**:
```bash
# 1. 証明書確認
openssl x509 -in /etc/letsencrypt/live/workmatechat.com/fullchain.pem -text -noout

# 2. 証明書有効期限確認
certbot certificates

# 3. 証明書更新
sudo certbot renew --dry-run
sudo certbot renew

# 4. Nginx設定テスト
sudo nginx -t

# 5. SSL設定テスト
curl -I https://workmatechat.com
```

### エラーコード一覧

| HTTP Code | 意味 | 一般的な原因 | 解決方法 |
|-----------|------|-------------|----------|
| **400** | Bad Request | リクエスト形式が不正 | リクエストパラメータを確認 |
| **401** | Unauthorized | 認証情報が無効 | ログイン情報を再確認 |
| **403** | Forbidden | アクセス権限なし | ユーザー権限を確認 |
| **404** | Not Found | リソースが存在しない | URLパスを確認 |
| **413** | Payload Too Large | ファイルサイズ超過 | ファイルサイズを削減 |
| **429** | Too Many Requests | 利用制限到達 | 時間をおいて再試行 |
| **500** | Internal Server Error | サーバー内部エラー | ログを確認してサポートに連絡 |
| **502** | Bad Gateway | バックエンドサーバーエラー | バックエンドサービスを確認 |
| **503** | Service Unavailable | サービス利用不可 | サーバー負荷またはメンテナンス |

### 緊急時対応

#### サービス復旧手順

**1. 完全停止時**
```bash
# 全サービス再起動
sudo systemctl restart workmate-backend
sudo systemctl restart nginx

# 状態確認
sudo systemctl status workmate-backend
sudo systemctl status nginx
```

**2. データベース問題**
```bash
# Supabase接続確認
python3 -c "from modules.database import test_connection; test_connection()"

# フォールバック処理
# 一時的にローカルファイルベースでの動作に切り替え
```

**3. AI API制限**
```bash
# API使用量確認
# Google Cloud Console でQuota確認

# 一時的な応答設定
# 制限時は定型メッセージで対応
```

---

## 運用・保守

### 日常運用タスク

#### 毎日の確認項目

**システム状態チェック**
```bash
# 自動化スクリプト: daily-check.sh
#!/bin/bash

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="/var/log/workmate-daily.log"

echo "[$TIMESTAMP] 日次チェック開始" >> $LOG_FILE

# 1. サービス状態
systemctl is-active --quiet workmate-backend && echo "Backend: OK" || echo "Backend: ERROR"
systemctl is-active --quiet nginx && echo "Nginx: OK" || echo "Nginx: ERROR"

# 2. API応答確認
curl -f https://workmatechat.com/chatbot/api/health && echo "API: OK" || echo "API: ERROR"

# 3. ディスク使用量
df -h | grep -E "(/$|/var)" 

# 4. 利用統計
python3 -c "
from supabase_adapter import select_data
from datetime import datetime, timedelta

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
result = select_data('chat_history', filters={'timestamp__gte': yesterday})
print(f'昨日の質問数: {len(result.data) if result.data else 0}')
"

echo "[$TIMESTAMP] 日次チェック完了" >> $LOG_FILE
```

#### 週次メンテナンス

**1. ログ分析**
```bash
# 週次ログ分析スクリプト
#!/bin/bash

echo "=== 週次ログ分析 ==="

# エラーログ確認
echo "Nginx エラーログ (過去7日):"
grep -c "error" /var/log/nginx/error.log

echo "バックエンドエラー (過去7日):"
journalctl -u workmate-backend --since "7 days ago" | grep -c ERROR

# アクセス統計
echo "週間アクセス統計:"
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10
```

**2. データベース最適化**
```python
# weekly-db-maintenance.py
from supabase_adapter import execute_query
from datetime import datetime, timedelta

# 古いチャット履歴の統計集計（3ヶ月以上前）
three_months_ago = (datetime.now() - timedelta(days=90)).isoformat()

# 使用統計更新
def update_usage_stats():
    query = """
    UPDATE usage_limits 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE updated_at < %s
    """
    execute_query(query, (three_months_ago,))

# データベース統計更新
def analyze_chat_patterns():
    query = """
    SELECT 
        DATE(timestamp) as date,
        COUNT(*) as question_count,
        COUNT(DISTINCT employee_id) as unique_users
    FROM chat_history 
    WHERE timestamp >= %s
    GROUP BY DATE(timestamp)
    ORDER BY date DESC
    """
    return execute_query(query, (three_months_ago,))
```

**3. リソース最適化**
```bash
# 未使用リソースのクリーンアップ
python3 -c "
from modules.admin import get_uploaded_resources
import asyncio

async def cleanup_unused_resources():
    resources = await get_uploaded_resources()
    for resource in resources:
        if not resource.get('active') and resource.get('last_accessed'):
            # 30日以上アクセスされていない無効リソースを削除候補に
            print(f'削除候補: {resource[\"name\"]}')

asyncio.run(cleanup_unused_resources())
"
```

#### 月次保守

**1. セキュリティ更新**
```bash
# セキュリティアップデート
sudo apt update && sudo apt upgrade -y

# Python依存関係更新
cd /var/www/workmate/Chatbot-backend-main
source venv/bin/activate
pip list --outdated
# 必要に応じて個別アップデート

# Node.js依存関係確認
cd /var/www/workmate/Chatbot-Frontend-main
npm audit
npm audit fix
```

**2. バックアップ確認**
```bash
# Supabase自動バックアップ確認
# Supabase Dashboard → Settings → Database → Backups

# 設定ファイルバックアップ
tar -czf "/backup/workmate-config-$(date +%Y%m%d).tar.gz" \
    /etc/nginx/sites-available/workmate \
    /etc/systemd/system/workmate-backend.service \
    /var/www/workmate/Chatbot-backend-main/.env
```

**3. パフォーマンス分析**
```python
# monthly-performance-report.py
from supabase_adapter import select_data, execute_query
from datetime import datetime, timedelta
import json

def generate_monthly_report():
    last_month = (datetime.now() - timedelta(days=30)).isoformat()
    
    # 利用統計
    chat_stats = select_data(
        'chat_history',
        columns='COUNT(*) as total, AVG(LENGTH(user_message)) as avg_question_length',
        filters={'timestamp__gte': last_month}
    )
    
    # ユーザー増加率
    user_stats = select_data(
        'users',
        columns='COUNT(*) as total, role',
        group_by='role'
    )
    
    # 人気カテゴリ
    category_stats = select_data(
        'chat_history',
        columns='category, COUNT(*) as count',
        filters={'timestamp__gte': last_month},
        group_by='category',
        order_by='count DESC'
    )
    
    report = {
        'period': last_month,
        'chat_statistics': chat_stats.data,
        'user_statistics': user_stats.data,
        'popular_categories': category_stats.data[:10]
    }
    
    with open(f'/var/log/workmate-monthly-{datetime.now().strftime("%Y%m")}.json', 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report
```

### 監視・アラート設定

#### システム監視

**CloudWatch設定（AWS EC2の場合）**
```bash
# CloudWatch Agentインストール
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# 設定ファイル
sudo nano /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
```

```json
{
  "metrics": {
    "namespace": "WorkmateChatbot",
    "metrics_collected": {
      "cpu": {
        "measurement": ["cpu_usage_idle", "cpu_usage_iowait", "cpu_usage_user", "cpu_usage_system"],
        "metrics_collection_interval": 300
      },
      "disk": {
        "measurement": ["used_percent"],
        "metrics_collection_interval": 300,
        "resources": ["*"]
      },
      "mem": {
        "measurement": ["mem_used_percent"],
        "metrics_collection_interval": 300
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/nginx/access.log",
            "log_group_name": "workmate-nginx-access",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/log/nginx/error.log",
            "log_group_name": "workmate-nginx-error",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
```

#### アプリケーション監視

**カスタムヘルスチェック**
```python
# modules/health.py
from fastapi import APIRouter
from datetime import datetime
import psutil
import os

router = APIRouter()

@router.get("/health")
async def health_check():
    """システムヘルスチェック"""
    
    # システム情報
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # データベース接続確認
    try:
        from modules.database import get_db
        db = next(get_db())
        db_status = "OK"
    except Exception as e:
        db_status = f"ERROR: {str(e)}"
    
    # Gemini API確認
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        model.generate_content("test")
        ai_status = "OK"
    except Exception as e:
        ai_status = f"ERROR: {str(e)}"
    
    status_code = 200
    if db_status != "OK" or ai_status != "OK":
        status_code = 503
    
    return {
        "status": "healthy" if status_code == 200 else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": (disk.used / disk.total) * 100
        },
        "services": {
            "database": db_status,
            "ai_api": ai_status
        }
    }

@router.get("/metrics")
async def get_metrics():
    """Prometheus形式メトリクス"""
    from supabase_adapter import select_data
    
    # 基本統計
    total_users = len(select_data('users').data or [])
    total_chats = len(select_data('chat_history').data or [])
    active_resources = len(select_data('document_sources', filters={'active': True}).data or [])
    
    metrics = f"""
# HELP workmate_users_total Total number of users
# TYPE workmate_users_total counter
workmate_users_total {total_users}

# HELP workmate_chats_total Total number of chat messages
# TYPE workmate_chats_total counter
workmate_chats_total {total_chats}

# HELP workmate_resources_active Number of active resources
# TYPE workmate_resources_active gauge
workmate_resources_active {active_resources}

# HELP workmate_system_cpu_percent CPU usage percentage
# TYPE workmate_system_cpu_percent gauge
workmate_system_cpu_percent {psutil.cpu_percent()}

# HELP workmate_system_memory_percent Memory usage percentage
# TYPE workmate_system_memory_percent gauge
workmate_system_memory_percent {psutil.virtual_memory().percent}
"""
    
    return Response(content=metrics, media_type="text/plain")
```

#### アラート設定

**Slack通知設定**
```python
# modules/alerts.py
import requests
import json
import os
from datetime import datetime

def send_slack_alert(message, severity="info"):
    """Slackアラート送信"""
    
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        return
    
    color_map = {
        "info": "#36a64f",
        "warning": "#ff9900", 
        "error": "#ff0000",
        "critical": "#8B0000"
    }
    
    payload = {
        "attachments": [{
            "color": color_map.get(severity, "#36a64f"),
            "title": "Workmate システムアラート",
            "text": message,
            "timestamp": datetime.now().timestamp()
        }]
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Slack通知エラー: {e}")

def check_system_health():
    """システムヘルスチェック＆アラート"""
    
    # CPU使用率チェック
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > 80:
        send_slack_alert(
            f"⚠️ CPU使用率が高いです: {cpu_percent}%",
            "warning"
        )
    
    # メモリ使用率チェック
    memory_percent = psutil.virtual_memory().percent
    if memory_percent > 85:
        send_slack_alert(
            f"⚠️ メモリ使用率が高いです: {memory_percent}%",
            "warning"
        )
    
    # ディスク使用率チェック
    disk_percent = (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
    if disk_percent > 90:
        send_slack_alert(
            f"🚨 ディスク使用率が危険レベルです: {disk_percent}%",
            "critical"
        )
    
    # サービス状態チェック
    try:
        import subprocess
        backend_status = subprocess.run(['systemctl', 'is-active', 'workmate-backend'], 
                                     capture_output=True, text=True)
        if backend_status.stdout.strip() != 'active':
            send_slack_alert(
                "🚨 バックエンドサービスが停止しています",
                "critical"
            )
    except Exception as e:
        send_slack_alert(
            f"🚨 サービスチェックエラー: {e}",
            "error"
        )
```

### バックアップ・復旧

#### データバックアップ戦略

**1. Supabaseバックアップ**
- **自動バックアップ**: Supabaseの自動バックアップ機能を有効化
- **ポイントインタイム復旧**: 過去7日間の任意の時点に復旧可能
- **手動スナップショット**: 重要な変更前に手動でスナップショット作成

**2. アプリケーションファイルバックアップ**
```bash
# 日次バックアップスクリプト
#!/bin/bash

BACKUP_DIR="/backup/workmate"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="workmate_backup_${TIMESTAMP}.tar.gz"

# バックアップディレクトリ作成
mkdir -p $BACKUP_DIR

# アプリケーションファイルバックアップ
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" \
    --exclude="*/node_modules/*" \
    --exclude="*/venv/*" \
    --exclude="*/__pycache__/*" \
    --exclude="*/dist/*" \
    /var/www/workmate \
    /etc/nginx/sites-available/workmate \
    /etc/systemd/system/workmate-backend.service

# 古いバックアップファイル削除（30日以上前）
find $BACKUP_DIR -name "workmate_backup_*.tar.gz" -mtime +30 -delete

echo "バックアップ完了: ${BACKUP_FILE}"
```

**3. 設定ファイルバックアップ**
```bash
# 設定ファイル専用バックアップ
CONFIG_BACKUP_DIR="/backup/config"
mkdir -p $CONFIG_BACKUP_DIR

# 重要な設定ファイルをGitリポジトリで管理
cd $CONFIG_BACKUP_DIR
git init
git add .
git commit -m "Config backup $(date)"

# リモートリポジトリに自動プッシュ
git push origin main
```

#### 災害復旧計画

**1. 完全復旧手順**
```bash
# 1. 新しいEC2インスタンス準備
# 2. 基本ソフトウェアインストール
sudo apt update
sudo apt install -y python3-pip nginx certbot python3-certbot-nginx git

# 3. バックアップから復元
cd /var/www
tar -xzf /backup/workmate/workmate_backup_latest.tar.gz

# 4. 依存関係インストール
cd workmate/Chatbot-backend-main
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. 環境変数復元
# .env ファイルを安全な場所から復元

# 6. サービス再設定
sudo systemctl enable workmate-backend
sudo systemctl start workmate-backend

# 7. Nginx設定復元
sudo cp /backup/nginx/workmate /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/workmate /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# 8. SSL証明書復元
sudo certbot --nginx -d workmatechat.com
```

**2. データベース復旧**
```bash
# Supabaseからの復旧
# 1. Supabase Dashboard → Settings → Database → Backups
# 2. 復元したい時点を選択
# 3. Restore ボタンクリック

# 手動復旧の場合
psql -h your-db-host -U postgres -d workmate < backup.sql
```

**3. 部分復旧手順**
```bash
# バックエンドのみ復旧
sudo systemctl stop workmate-backend
cd /var/www/workmate/Chatbot-backend-main
git pull origin master
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start workmate-backend

# フロントエンドのみ復旧
# Vercel Dashboard → Deployments → Redeploy
```

### セキュリティ管理

#### 定期セキュリティチェック

**1. 脆弱性スキャン**
```bash
# Python依存関係の脆弱性チェック
cd /var/www/workmate/Chatbot-backend-main
source venv/bin/activate
pip install safety
safety check

# Node.js依存関係の脆弱性チェック
cd /var/www/workmate/Chatbot-Frontend-main
npm audit

# システムパッケージの脆弱性チェック
sudo apt list --upgradable | grep -i security
```

**2. アクセスログ分析**
```bash
# 不審なアクセスパターン検出
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -20

# 失敗したログイン試行
grep "401\|403" /var/log/nginx/access.log | tail -20

# 大量リクエストの検出
awk '$9 !~ /^[23]/ {print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn
```

**3. システムファイル整合性チェック**
```bash
# 重要ファイルのハッシュチェック
find /var/www/workmate -name "*.py" -exec md5sum {} \; > /tmp/file_hashes.txt
# 定期的に比較して変更を検出

# 設定ファイルの変更監視
sudo apt install aide
sudo aide --init
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db
sudo aide --check
```

#### アクセス制御強化

**1. IP制限設定**
```nginx
# 管理者パネルへのアクセス制限
location /admin {
    allow 192.168.1.0/24;    # 社内ネットワーク
    allow 203.0.113.0/24;    # VPN範囲
    deny all;
    
    # 既存の設定...
}
```

**2. レート制限**
```nginx
# Nginx レート制限
http {
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
    
    server {
        location /chatbot/api/auth/ {
            limit_req zone=login burst=3 nodelay;
        }
        
        location /chatbot/api/ {
            limit_req zone=api burst=10 nodelay;
        }
    }
}
```

**3. ファイアウォール設定**
```bash
# UFW設定
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 必要なポートのみ開放
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# 特定IPからのみSSHアクセス許可
sudo ufw delete allow ssh
sudo ufw allow from 192.168.1.0/24 to any port 22
```

---

## 🎯 まとめ

この使用書では、Workmate AIチャットボットシステムの包括的な情報を提供しました。

### 重要なポイント

1. **システム理解**: React + FastAPI + Supabase の構成
2. **セキュリティ**: 企業レベルのセキュリティ対応
3. **スケーラビリティ**: マルチテナント対応
4. **運用性**: 監視・バックアップ・復旧体制

### 今後の発展

- **多言語対応**: 英語・中国語での利用
- **API提供**: 外部システム連携
- **音声入力**: 音声による質問入力
- **リアルタイム通知**: 重要更新の即時通知

### サポート・連絡先

- **技術的な問題**: queue@queuefood.co.jp
- **GitHub Issues**: プロジェクトリポジトリ
- **緊急時対応**: 社内エスカレーション

---

**📅 最終更新**: 2025年1月13日  
**📝 作成者**: Workmate開発チーム  
**📞 サポート**: queue@queuefood.co.jp

この使用書は定期的に更新されます。最新版は常にプロジェクトリポジトリで確認してください。