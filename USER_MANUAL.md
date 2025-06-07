# Workmate AIチャットボット - 完全利用マニュアル

## 目次
1. [システム概要](#システム概要)
2. [システム構成](#システム構成)
3. [ユーザーガイド](#ユーザーガイド)
4. [管理者ガイド](#管理者ガイド)
5. [技術仕様](#技術仕様)
6. [デプロイメント](#デプロイメント)
7. [トラブルシューティング](#トラブルシューティング)

---

## システム概要

### Workmate AIチャットボットとは
Workmate AIチャットボットは、企業向けのマルチテナント対応AIアシスタントシステムです。Google Gemini 2.0-flash-expを活用し、企業固有の知識ベースに基づいたインテリジェントな対話を提供します。

### 主要機能
- **🤖 AI対話**: 企業の知識ベースを活用した高精度な回答
- **📄 文書処理**: PDF、Excel、テキスト、動画の自動処理・学習
- **👥 ユーザー管理**: 役割ベースのアクセス制御
- **📊 分析機能**: チャット履歴分析とビジネスインサイト
- **🏢 マルチテナント**: 企業別データ分離
- **🔒 セキュリティ**: 堅牢な認証・認可システム

---

## システム構成

### アーキテクチャ図
```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   フロントエンド  │────│    Nginx     │────│   バックエンド   │
│   React + TS    │    │   リバース   │    │   FastAPI       │
│   (Port 3025)   │    │   プロキシ   │    │   (Port 8083)   │
└─────────────────┘    └──────────────┘    └─────────────────┘
                                                      │
                              ┌─────────────────────────┼─────────────────────────┐
                              │                         │                         │
                    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                    │   Supabase      │    │   Google        │    │   知識処理      │
                    │   PostgreSQL    │    │   Gemini AI     │    │   エンジン      │
                    │   データベース   │    │   (2.0-flash)   │    │                │
                    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 技術スタック

#### フロントエンド
- **React 18.2.0** + **TypeScript 5.3.3**
- **Material-UI 5.15.10** (UIコンポーネント)
- **Vite 5.1.3** (ビルドツール)
- **Chart.js 4.4.1** (グラフ表示)
- **React Dropzone 14.2.3** (ファイルアップロード)

#### バックエンド
- **FastAPI 0.109.2** (APIフレームワーク)
- **Google Generative AI 0.3.2** (Gemini統合)
- **PostgreSQL** (Supabase)
- **Pandas 2.2.0** (データ処理)
- **PyPDF2、PyMuPDF** (PDF処理)
- **Playwright、BeautifulSoup4** (Web scraping)

---

## ユーザーガイド

### アカウント登録・ログイン

#### 1. 新規登録
1. **登録ページアクセス**: https://workmatechat.com にアクセス
2. **情報入力**:
   - メールアドレス
   - パスワード（8文字以上）
   - 氏名
   - 会社名
3. **登録完了**: 自動的にログイン状態となります

#### 2. ログイン
1. **ログインページ**: 登録済みの場合は直接ログイン
2. **認証**: メールアドレスとパスワードでBasic認証
3. **アクセス**: ダッシュボードへ自動リダイレクト

### チャット機能の使用方法

#### 基本的な対話
1. **質問入力**: テキストエリアに質問を入力
2. **送信**: Enterキーまたは送信ボタンをクリック
3. **AI回答**: 知識ベースに基づいた回答を受信
4. **出典表示**: 回答の根拠となった文書が表示されます

#### 対話のコツ
- **具体的な質問**: 「〇〇について教えて」より「〇〇の手順を教えて」
- **文脈の活用**: 前の会話（最大5メッセージ）を参考に回答
- **日本語対応**: 日本語での自然な対話が可能

### 文書アップロード機能

#### サポートファイル形式

| ファイル形式 | 最大サイズ | 特徴 |
|-------------|-----------|------|
| **PDF** | 10MB | OCR対応、複数ページ処理 |
| **Excel** | 5MB | 複数シート対応、データ分析 |
| **Text** | 2MB | プレインテキスト、Markdown |
| **動画** | 500MB | MP4、AVI、WebM（字幕抽出） |

#### アップロード手順
1. **ファイル選択**: ドラッグ&ドロップまたはファイル選択
2. **自動処理**: システムが自動的に内容を解析
3. **知識ベース追加**: 処理完了後、チャットで参照可能
4. **確認**: アップロード履歴で処理状況を確認

#### URL登録機能
1. **URL入力**: WebページのURLを入力
2. **自動スクレイピング**: コンテンツを自動取得・処理
3. **知識ベース統合**: 取得内容をチャットで活用

### ユーザー設定

#### 会社名設定
1. **設定アクセス**: 右上メニューから「設定」
2. **会社名変更**: 現在の会社名を編集
3. **保存**: 変更内容を保存

#### プラン管理
- **デモプラン**: 制限付き無料利用
- **本格プラン**: 無制限利用（管理者による升级）
- **使用状況**: 質問数、アップロード数の確認

---

## 管理者ガイド

### 管理者パネルアクセス
- **対象ユーザー**: `role = 'user'` または `role = 'admin'`
- **アクセス方法**: ログイン後、自動的に管理者メニュー表示

### ユーザー管理

#### 従業員登録
1. **ユーザー管理タブ**: 管理者パネルから選択
2. **新規作成**:
   ```
   メールアドレス: 従業員のメール
   パスワード: 初期パスワード設定
   氏名: フルネーム
   役割: employee（チャットのみ）/ user（管理権限付き）
   ```
3. **登録完了**: 従業員に認証情報を共有

#### ユーザー削除
- **権限**: 特別管理者（`queue@queuefood.co.jp`）のみ
- **操作**: ユーザー一覧から削除ボタン
- **注意**: 削除は元に戻せません

### チャット履歴分析

#### 基本分析機能
1. **履歴表示**:
   - 全社員のチャット履歴
   - 時系列表示
   - カテゴリ別分類
   - センチメント分析

2. **フィルタリング**:
   - 期間指定
   - ユーザー別
   - カテゴリ別
   - 感情別（ポジティブ/ネガティブ/ニュートラル）

#### 詳細ビジネス分析
**AI駆動分析機能**で6つの視点から詳細な洞察を提供:

1. **頻繁なトピックとトレンド**
   - よく質問される内容の傾向
   - 時期による変化の分析

2. **効率化機会**
   - 業務プロセス改善の提案
   - 自動化可能な作業の特定

3. **フラストレーションポイント**
   - ユーザーの困りごと分析
   - 解決すべき課題の優先順位

4. **製品・サービス改善提案**
   - チャット内容から見える改善案
   - 顧客ニーズの洞察

5. **コミュニケーションギャップ**
   - 情報伝達の課題
   - 社内連携の改善点

6. **具体的推奨アクション**
   - 実行可能な改善策
   - 優先度付きアクションアイテム

### リソース管理

#### 知識ベース制御
1. **リソース一覧**: アップロードされた全文書表示
2. **有効/無効切り替え**: 特定文書の利用制御
3. **アップロード履歴**: 誰がいつ何をアップロードしたか

#### 文書管理ベストプラクティス
- **定期更新**: 古い文書の無効化
- **品質管理**: 不正確な情報源の除外
- **カテゴリ整理**: 文書の体系的管理

### 使用状況監視

#### 個別ユーザー使用状況
- **質問数**: 日別、月別の質問数
- **アクティビティ**: 最終ログイン、活動頻度
- **使用制限**: 上限設定と現在の使用量

#### 全体統計
- **デモ統計**: デモユーザーの利用状況
- **会社別統計**: 企業単位での利用分析
- **成長指標**: ユーザー数、質問数の推移

---

## 技術仕様

### API仕様

#### 認証方式
```http
Authorization: Basic <base64(email:password)>
Content-Type: application/json
```

#### 主要エンドポイント

**チャット機能**
```http
POST /chatbot/api/chat
Body: {
  "message": "質問内容",
  "conversation_history": [...] // 直近5メッセージ
}
Response: {
  "response": "AI回答",
  "sources": ["文書名1", "文書名2"]
}
```

**ファイルアップロード**
```http
POST /chatbot/api/upload-knowledge
Content-Type: multipart/form-data
Body: file (PDF/Excel/Text/Video)
```

**URL登録**
```http
POST /chatbot/api/submit-url
Body: {
  "url": "https://example.com",
  "description": "説明"
}
```

#### 管理者API

**チャット履歴取得**
```http
GET /chatbot/api/admin/chat-history
Response: [
  {
    "id": 1,
    "user_message": "質問",
    "bot_response": "回答",
    "timestamp": "2025-01-07T10:00:00Z",
    "employee_name": "田中太郎",
    "sentiment": "positive"
  }
]
```

**詳細分析**
```http
POST /chatbot/api/admin/detailed-analysis
Body: {
  "start_date": "2025-01-01",
  "end_date": "2025-01-31"
}
Response: {
  "analysis": {
    "frequent_topics": [...],
    "efficiency_opportunities": [...],
    "frustration_points": [...],
    "improvement_suggestions": [...],
    "communication_gaps": [...],
    "recommendations": [...]
  }
}
```

### データベーススキーマ

#### ユーザー管理
```sql
-- ユーザーテーブル
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'employee',
    company_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 使用制限テーブル
CREATE TABLE usage_limits (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    questions_used INTEGER DEFAULT 0,
    questions_limit INTEGER DEFAULT 10,
    document_uploads_used INTEGER DEFAULT 0,
    document_uploads_limit INTEGER DEFAULT 2,
    is_unlimited BOOLEAN DEFAULT FALSE
);
```

#### 会社管理
```sql
-- 会社テーブル
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    plan_type VARCHAR(50) DEFAULT 'demo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 知識ベーステーブル
CREATE TABLE document_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    content TEXT,
    uploaded_by INTEGER REFERENCES users(id),
    company_id INTEGER REFERENCES companies(id),
    active BOOLEAN DEFAULT TRUE,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### チャット履歴
```sql
-- チャット履歴テーブル
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    category VARCHAR(100),
    sentiment VARCHAR(20),
    employee_id INTEGER REFERENCES users(id),
    employee_name VARCHAR(255),
    source_document VARCHAR(255),
    source_page INTEGER
);
```

### セキュリティ仕様

#### 認証・認可
- **Basic認証**: email:passwordのBase64エンコード
- **役割ベースアクセス制御**:
  - `employee`: チャット機能のみ
  - `user`: 会社管理 + 管理者パネル
  - `admin`: システム全体管理
- **マルチテナント**: 会社IDによるデータ分離

#### データ保護
- **SSL/TLS**: HTTPS通信の強制
- **入力検証**: SQLインジェクション対策
- **CORS設定**: クロスオリジン制御
- **ファイルサイズ制限**: DoS攻撃対策

### パフォーマンス仕様

#### 処理能力
- **同時接続数**: 最大100ユーザー
- **レスポンス時間**: 
  - チャット: 平均2-5秒
  - ファイル処理: 1-10秒（サイズ依存）
- **アップロード制限**:
  - PDF: 10MB
  - Excel: 5MB
  - Video: 500MB

#### 拡張性
- **水平スケーリング**: 複数インスタンス対応
- **データベース**: PostgreSQL接続プール
- **キャッシュ**: インメモリキャッシュ対応
- **CDN**: Vercel Edge Network

---

## デプロイメント

### 開発環境セットアップ

#### 前提条件
- **Node.js**: 18.0.0以上
- **Python**: 3.9以上
- **PostgreSQL**: 13以上（またはSupabase）

#### フロントエンド環境構築
```bash
# プロジェクトクローン
git clone <repository-url>
cd workmate/Chatbot-Frontend-main

# 依存関係インストール
npm install

# 環境変数設定
cp .env.example .env
# VITE_API_URL=http://localhost:8083 を設定

# 開発サーバー起動
npm run dev
# → http://localhost:3025 で起動
```

#### バックエンド環境構築
```bash
# バックエンドディレクトリ
cd workmate/Chatbot-backend-main

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# 以下の変数を設定:
# GOOGLE_API_KEY=<Gemini API Key>
# SUPABASE_URL=<Supabase Project URL>
# SUPABASE_KEY=<Supabase API Key>
# PORT=8083

# データベースセットアップ
python setup_supabase.py

# 開発サーバー起動
uvicorn main:app --host 0.0.0.0 --port 8083 --reload
```

### 本番環境デプロイ

#### AWS EC2バックエンドデプロイ
```bash
# EC2インスタンス準備（Ubuntu 20.04 LTS推奨）
sudo apt update
sudo apt install python3-pip nginx certbot python3-certbot-nginx

# プロジェクト配置
git clone <repository-url> /var/www/workmate
cd /var/www/workmate/Chatbot-backend-main

# Python環境構築
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 環境変数設定
sudo nano /etc/environment
# 本番用の環境変数を設定

# systemdサービス作成
sudo nano /etc/systemd/system/workmate-backend.service
```

**systemdサービス設定**:
```ini
[Unit]
Description=Workmate Chatbot Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/workmate/Chatbot-backend-main
Environment=PATH=/var/www/workmate/Chatbot-backend-main/venv/bin
EnvironmentFile=/etc/environment
ExecStart=/var/www/workmate/Chatbot-backend-main/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8083
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Nginx設定
```nginx
# /etc/nginx/sites-available/workmate
server {
    listen 80;
    server_name workmatechat.com www.workmatechat.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name workmatechat.com www.workmatechat.com;
    
    ssl_certificate /etc/letsencrypt/live/workmatechat.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/workmatechat.com/privkey.pem;
    
    # セキュリティヘッダー
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
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
    }
    
    # ファイルアップロード制限
    client_max_body_size 500M;
    
    # 静的ファイル（フロントエンド用）
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
    }
}
```

#### SSL証明書設定
```bash
# Let's Encrypt証明書取得
sudo certbot --nginx -d workmatechat.com -d www.workmatechat.com

# 自動更新設定
sudo crontab -e
# 以下を追加:
0 12 * * * /usr/bin/certbot renew --quiet
```

#### Vercelフロントエンドデプロイ

**vercel.json設定**:
```json
{
  "rewrites": [
    {
      "source": "/chatbot/api/(.*)",
      "destination": "https://workmatechat.com/chatbot/api/$1"
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
        }
      ]
    }
  ]
}
```

**デプロイ手順**:
1. **Vercelアカウント**: GitHubアカウントでログイン
2. **プロジェクト接続**: リポジトリを選択
3. **環境変数設定**: 
   ```
   VITE_API_URL=https://workmatechat.com
   ```
4. **ビルド設定**:
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. **デプロイ実行**: 自動ビルド・デプロイ

### CI/CD パイプライン

#### GitHub Actions設定

**.github/workflows/deploy-backend.yml**:
```yaml
name: Deploy Backend

on:
  push:
    branches: [ master ]
    paths: 
      - 'Chatbot-backend-main/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
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
          sudo systemctl reload nginx
```

**.github/workflows/deploy-frontend.yml**:
```yaml
name: Deploy Frontend

on:
  push:
    branches: [ master ]
    paths: 
      - 'Chatbot-Frontend-main/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        
    - name: Install and Build
      run: |
        cd Chatbot-Frontend-main
        npm ci
        npm run build
        
    - name: Deploy to Vercel
      uses: amondnet/vercel-action@v20
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.ORG_ID }}
        vercel-project-id: ${{ secrets.PROJECT_ID }}
        working-directory: ./Chatbot-Frontend-main
```

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. ログイン関連の問題

**問題**: 「認証に失敗しました」エラー
**原因**: 
- 間違ったメールアドレス・パスワード
- アカウントが存在しない
- サーバー接続エラー

**解決方法**:
1. **認証情報確認**: メールアドレス・パスワードを再確認
2. **アカウント状態確認**: 管理者にアカウント存在を確認
3. **ネットワーク確認**: インターネット接続を確認
4. **サーバー状態確認**: https://workmatechat.com/health でサーバー状態確認

#### 2. チャット機能の問題

**問題**: AI回答が遅い・回答しない
**原因**:
- Gemini API制限
- 知識ベースの問題
- サーバー負荷

**解決方法**:
1. **待機**: 30秒程度待ってから再試行
2. **質問の簡素化**: より具体的で短い質問に変更
3. **知識ベース確認**: 関連文書がアップロードされているか確認
4. **管理者へ連絡**: 継続的な問題の場合は管理者へ報告

**問題**: 「知識ベースに関連情報が見つかりません」
**原因**:
- 関連文書が未アップロード
- 文書が無効化されている
- 質問と文書の関連性が低い

**解決方法**:
1. **文書アップロード**: 関連する文書をアップロード
2. **質問の修正**: より具体的な質問に変更
3. **管理者確認**: 文書の有効性を管理者に確認

#### 3. ファイルアップロードの問題

**問題**: ファイルアップロードに失敗
**原因**:
- ファイルサイズ制限超過
- サポートされていないファイル形式
- ネットワークエラー

**解決方法**:
1. **ファイルサイズ確認**: 
   - PDF: 10MB以下
   - Excel: 5MB以下
   - 動画: 500MB以下
2. **形式確認**: サポートされているファイル形式か確認
3. **ファイル修復**: 破損しているファイルの再作成
4. **分割アップロード**: 大きなファイルは複数に分割

#### 4. 管理者パネルの問題

**問題**: 管理者パネルにアクセスできない
**原因**:
- 権限不足（role = 'employee'）
- ログイン状態の問題

**解決方法**:
1. **権限確認**: 自分の役割を確認（user/admin必須）
2. **再ログイン**: ログアウト→再ログイン
3. **管理者相談**: 権限昇格を管理者に依頼

**問題**: 分析データが表示されない
**原因**:
- データ不足
- 期間設定の問題
- サーバーエラー

**解決方法**:
1. **データ確認**: チャット履歴が存在するか確認
2. **期間調整**: 分析期間を広げて再試行
3. **ブラウザ更新**: ページを更新して再実行

### エラーコードと対処法

#### HTTP エラーコード

| コード | 意味 | 対処法 |
|--------|------|--------|
| **400** | Bad Request | リクエスト形式を確認 |
| **401** | Unauthorized | 認証情報を確認 |
| **403** | Forbidden | 権限を確認 |
| **404** | Not Found | URLを確認 |
| **413** | Payload Too Large | ファイルサイズを削減 |
| **429** | Too Many Requests | 時間を置いて再試行 |
| **500** | Internal Server Error | 管理者に連絡 |

#### アプリケーションエラー

**"GOOGLE_API_KEY not configured"**
- **原因**: Gemini API キーが未設定
- **対処**: 管理者にAPI key設定を依頼

**"Database connection failed"**
- **原因**: データベース接続エラー
- **対処**: ネットワーク確認、管理者に連絡

**"File processing failed"**
- **原因**: ファイル処理中のエラー
- **対処**: ファイル形式・内容を確認

### サポート連絡先

#### 技術的な問題
- **システム管理者**: queue@queuefood.co.jp
- **緊急時**: 社内チャットまたは電話連絡

#### 機能改善要望
- **GitHub Issues**: プロジェクトリポジトリのIssues
- **フィードバックフォーム**: 管理者パネル内

#### システム状態確認
- **ヘルスチェック**: https://workmatechat.com/health
- **システム状態**: 管理者パネルの統計画面

---

## 付録

### 利用規約・プライバシーポリシー

#### データ取り扱いについて
- **データ保存期間**: チャット履歴は無期限保存
- **データ共有**: 同一企業内でのみ共有
- **データ削除**: ユーザー削除と共に関連データも削除

#### 利用制限
- **商用利用**: 企業内利用に限定
- **API利用**: 直接的なAPI利用は禁止
- **リバースエンジニアリング**: システムの解析・複製禁止

### 更新履歴

#### Version 2.0.0 (2025-01-07)
- Gemini 2.0-flash-exp へのアップグレード
- ビジネス分析機能の追加
- マルチテナント対応の強化
- 動画ファイル処理機能の追加

#### Version 1.5.0 (2024-12-15)
- Excel ファイル処理の改善
- チャート表示機能の追加
- ユーザー管理機能の強化

#### Version 1.0.0 (2024-11-01)
- 初回リリース
- 基本的なチャット機能
- PDF・テキストファイル処理
- 基本的な管理者機能

### FAQ（よくある質問）

**Q: 無料で利用できますか？**
A: デモプランでは制限付きで無料利用可能です。本格利用には管理者による升级が必要です。

**Q: どの程度の精度で回答できますか？**
A: アップロードされた知識ベースの品質に依存します。正確で詳細な文書をアップロードすることで、より高精度な回答が可能です。

**Q: 複数の会社で利用できますか？**
A: はい、マルチテナント対応により、複数企業での独立した利用が可能です。

**Q: スマートフォンからも利用できますか？**
A: はい、レスポンシブデザインによりスマートフォン・タブレットからも利用可能です。

**Q: APIは提供されていますか？**
A: 現在は直接的なAPI提供はしていません。システム統合が必要な場合は管理者にご相談ください。

---

**このマニュアルについて**
- **最終更新**: 2025年1月7日
- **バージョン**: 2.0.0
- **作成者**: Workmate開発チーム
- **連絡先**: queue@queuefood.co.jp

このマニュアルは定期的に更新されます。最新版は常にプロジェクトリポジトリで確認してください。