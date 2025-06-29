# 🗄️ Workmate データベース構造 完全解説ガイド

## 📋 目次
- [🏗️ システムアーキテクチャー概要](#システムアーキテクチャー概要)
- [🔐 認証システム (auth スキーマ)](#認証システム-auth-スキーマ)
- [🏢 ビジネスロジック (public スキーマ)](#ビジネスロジック-public-スキーマ)
- [🔗 テーブル関係図](#テーブル関係図)
- [📊 データフロー解説](#データフロー解説)
- [🔧 運用・管理機能](#運用管理機能)

---

## 🏗️ システムアーキテクチャー概要

Workmate は **RAG（Retrieval-Augmented Generation）技術**を活用したAIチャットボットプラットフォームです。

### 📂 スキーマ構成
- **`auth`** - Supabase認証システム（16テーブル）
- **`public`** - アプリケーション固有のビジネスロジック（12テーブル）🔄

### 🎯 主要機能
1. **企業・ユーザー管理** - マルチテナント対応
2. **ドキュメント管理** - PDF、Excel等のアップロード・解析
3. **チャンク分割処理** - 効率的なRAG検索のための文書分割（768次元ベクトル）
4. **AIチャット** - Gemini 2.5 Flash による自然言語処理
5. **利用状況追跡** - トークン使用量・コスト管理
6. **プラン管理** - ユーザーの料金プラン制御
7. **申請管理** - 本番環境アップグレード等の申請処理🆕
8. **トークン分析** - 月次使用量分析・企業設定管理🆕

---

## 🔐 認証システム (auth スキーマ)

### 👤 users - メインユーザーテーブル
```sql
-- 主要カラム（35カラム）
id                         uuid PRIMARY KEY
email                      varchar UNIQUE
encrypted_password         varchar
created_at                timestamptz
updated_at                timestamptz
instance_id               uuid
aud                       varchar
role                      varchar
email_confirmed_at        timestamptz
invited_at               timestamptz
confirmation_token       varchar
confirmation_sent_at     timestamptz
recovery_token           varchar
recovery_sent_at         timestamptz
email_change_token_new   varchar
email_change             varchar
email_change_sent_at     timestamptz
last_sign_in_at          timestamptz
raw_app_meta_data        jsonb      -- プロフィール情報
raw_user_meta_data       jsonb      -- アプリケーション情報
is_super_admin           boolean
phone                    text UNIQUE
phone_confirmed_at       timestamptz
phone_change             text DEFAULT ''
phone_change_token       varchar DEFAULT ''
phone_change_sent_at     timestamptz
confirmed_at             timestamptz GENERATED -- LEAST(email_confirmed_at, phone_confirmed_at)
email_change_token_current varchar DEFAULT ''
email_change_confirm_status smallint DEFAULT 0 CHECK (>= 0 AND <= 2)
banned_until             timestamptz
reauthentication_token   varchar DEFAULT ''
reauthentication_sent_at timestamptz
is_sso_user              boolean DEFAULT false -- SSO経由のアカウント識別
deleted_at               timestamptz
is_anonymous             boolean DEFAULT false

-- 統計情報
現在のサイズ: 96 kB
推定データ: 0レコード
RLS: 有効
```

**🔑 キーポイント:**
- Supabase認証の中核テーブル（35カラム）
- 電話番号認証・匿名ユーザー・SSO対応
- ユーザー削除・BANにも対応
- confirmed_at は生成カラム（email/phone確認の早い方）
- RLS（Row Level Security）対応

### 🔄 sessions - セッション管理
```sql
-- 主要カラム（11カラム）
id          uuid PRIMARY KEY
user_id     uuid NOT NULL → auth.users(id)
created_at  timestamptz
updated_at  timestamptz
factor_id   uuid          -- MFA要素ID
aal         aal_level ENUM('aal1','aal2','aal3')  -- 認証レベル
not_after   timestamptz   -- セッション有効期限
refreshed_at timestamp    -- 最終リフレッシュ時刻
user_agent  text          -- ユーザーエージェント
ip          inet          -- IPアドレス
tag         text          -- セッション識別子

-- 統計情報
現在のサイズ: 40 kB
推定データ: 0レコード
RLS: 有効
```

### 🔐 MFA（多要素認証）システム

#### mfa_factors - 認証要素
```sql
-- テーブル構造（12カラム）
id                    uuid PRIMARY KEY
user_id              uuid NOT NULL → auth.users(id)
friendly_name        text              -- 表示名
factor_type          factor_type ENUM('totp','webauthn','phone')
status               factor_status ENUM('unverified','verified')
created_at           timestamptz NOT NULL
updated_at           timestamptz NOT NULL
secret               text              -- TOTP秘密鍵
phone                text              -- SMS認証用
last_challenged_at   timestamptz UNIQUE
web_authn_credential jsonb             -- WebAuthn認証情報
web_authn_aaguid     uuid              -- WebAuthn AAGUID

-- 統計情報
現在のサイズ: 56 kB
推定データ: 0レコード
RLS: 有効
```

#### mfa_challenges - 認証チャレンジ
```sql
-- テーブル構造（7カラム）
id                      uuid PRIMARY KEY
factor_id              uuid NOT NULL → mfa_factors(id)
created_at             timestamptz NOT NULL
verified_at            timestamptz
ip_address             inet NOT NULL
otp_code               text
web_authn_session_data jsonb    -- WebAuthn セッション

-- 統計情報
現在のサイズ: 24 kB
推定データ: 0レコード
RLS: 有効
```

#### mfa_amr_claims - 認証方法記録
```sql
-- テーブル構造（5カラム）
session_id             uuid NOT NULL → sessions(id)
created_at            timestamptz NOT NULL
updated_at            timestamptz NOT NULL
authentication_method  text NOT NULL
id                    uuid PRIMARY KEY

-- 統計情報
現在のサイズ: 24 kB
推定データ: 0レコード
RLS: 有効
```

### 🌐 SSO（シングルサインオン）

#### sso_providers - SSOプロバイダー
```sql
-- テーブル構造（4カラム）
id           uuid PRIMARY KEY
resource_id  text UNIQUE  -- ユーザー定義のリソースID（大文字小文字区別なし）
created_at   timestamptz
updated_at   timestamptz

-- 統計情報
現在のサイズ: 24 kB
推定データ: 0レコード
RLS: 有効
CHECK: resource_id = NULL OR char_length(resource_id) > 0
```

#### sso_domains - SSOドメインマッピング
```sql
-- テーブル構造（5カラム）
id              uuid PRIMARY KEY
sso_provider_id uuid NOT NULL → sso_providers(id)
domain          text NOT NULL  -- マッピング対象ドメイン
created_at      timestamptz
updated_at      timestamptz

-- 統計情報
現在のサイズ: 32 kB
推定データ: 0レコード
RLS: 有効
CHECK: char_length(domain) > 0
```

#### saml_providers - SAML設定
```sql
-- テーブル構造（9カラム）
id                  uuid PRIMARY KEY
sso_provider_id     uuid NOT NULL → sso_providers(id)
entity_id           text NOT NULL UNIQUE  -- SAMLエンティティID
metadata_xml        text NOT NULL         -- SAMLメタデータXML
metadata_url        text                  -- メタデータURL（オプション）
attribute_mapping   jsonb                 -- 属性マッピング設定
created_at          timestamptz
updated_at          timestamptz
name_id_format      text                  -- NameIDフォーマット

-- 統計情報
現在のサイズ: 32 kB
推定データ: 0レコード
RLS: 有効
CHECK: char_length(entity_id) > 0, char_length(metadata_xml) > 0
CHECK: metadata_url = NULL OR char_length(metadata_url) > 0
```

#### saml_relay_states - SAML Relay State
```sql
-- テーブル構造（8カラム）
id              uuid PRIMARY KEY
sso_provider_id uuid NOT NULL → sso_providers(id)
request_id      text NOT NULL  -- SAMLリクエストID
for_email       text           -- 対象メールアドレス
redirect_to     text           -- リダイレクト先URL
created_at      timestamptz
updated_at      timestamptz
flow_state_id   uuid → flow_state(id)  -- PKCEフロー連携

-- 統計情報
現在のサイズ: 40 kB
推定データ: 0レコード
RLS: 有効
CHECK: char_length(request_id) > 0
```

### 🔑 その他の認証テーブル

#### identities - 外部ID連携
```sql
-- テーブル構造（9カラム）
provider_id      text NOT NULL          -- プロバイダー固有ID
user_id          uuid NOT NULL → users(id)
identity_data    jsonb NOT NULL         -- ID情報
provider         text NOT NULL          -- プロバイダー名
last_sign_in_at  timestamptz
created_at       timestamptz
updated_at       timestamptz
email            text GENERATED         -- identity_dataから抽出
id               uuid PRIMARY KEY DEFAULT gen_random_uuid()

-- 統計情報
現在のサイズ: 40 kB
推定データ: 0レコード
RLS: 有効
```

#### refresh_tokens - JWTリフレッシュトークン
```sql
-- テーブル構造（9カラム）
instance_id  uuid
id           bigint PRIMARY KEY DEFAULT nextval('auth.refresh_tokens_id_seq')
token        varchar UNIQUE
user_id      varchar
revoked      boolean
created_at   timestamptz
updated_at   timestamptz
parent       varchar
session_id   uuid → sessions(id)

-- 統計情報
現在のサイズ: 64 kB
推定データ: 0レコード
RLS: 有効
```

#### one_time_tokens - ワンタイムトークン
```sql
-- テーブル構造（7カラム）
id          uuid PRIMARY KEY
user_id     uuid NOT NULL → users(id)
token_type  one_time_token_type ENUM(
    'confirmation_token',
    'reauthentication_token', 
    'recovery_token',
    'email_change_token_new',
    'email_change_token_current',
    'phone_change_token'
)
token_hash  text NOT NULL     -- トークンハッシュ
relates_to  text NOT NULL     -- 関連情報
created_at  timestamp NOT NULL DEFAULT now()
updated_at  timestamp NOT NULL DEFAULT now()

-- 統計情報
現在のサイズ: 88 kB
推定データ: 0レコード
RLS: 有効
CHECK: char_length(token_hash) > 0
```

#### flow_state - PKCE認証フロー
```sql
-- テーブル構造（12カラム）
id                      uuid PRIMARY KEY
user_id                 uuid → users(id)
auth_code               text NOT NULL
code_challenge_method   code_challenge_method ENUM('s256','plain')
code_challenge          text NOT NULL
provider_type           text NOT NULL
provider_access_token   text
provider_refresh_token  text
created_at              timestamptz
updated_at              timestamptz
authentication_method   text NOT NULL
auth_code_issued_at     timestamptz

-- 統計情報
現在のサイズ: 40 kB
推定データ: 0レコード
RLS: 有効
```

#### audit_log_entries - 監査ログ
```sql
-- テーブル構造（5カラム）
instance_id  uuid
id           uuid PRIMARY KEY
payload      json              -- 監査データ
created_at   timestamptz
ip_address   varchar NOT NULL DEFAULT ''

-- 統計情報
現在のサイズ: 24 kB
推定データ: 0レコード
RLS: 有効
```

#### instances - インスタンス管理
```sql
-- テーブル構造（5カラム）
id               uuid PRIMARY KEY
uuid             uuid
raw_base_config  text          -- 基本設定
created_at       timestamptz
updated_at       timestamptz

-- 統計情報
現在のサイズ: 16 kB
推定データ: 0レコード
RLS: 有効
```

#### schema_migrations - スキーマ管理
```sql
-- テーブル構造（1カラム）
version  varchar PRIMARY KEY   -- マイグレーションバージョン

-- 統計情報
現在のサイズ: 24 kB
推定データ: 61レコード
RLS: 有効
```

---

## 🏢 ビジネスロジック (public スキーマ)

### 🏢 companies - 企業マスター
```sql
-- テーブル構造（3カラム）
id          text PRIMARY KEY     -- 企業ID
name        text NOT NULL        -- 企業名
created_at  timestamp NOT NULL   -- 作成日時

-- 統計情報
現在のサイズ: 32 kB
推定データ: 7レコード
RLS: 無効
```

### 👥 users - アプリケーションユーザー
```sql
-- テーブル構造（8カラム）
id          text PRIMARY KEY           -- ユーザーID
email       text UNIQUE NOT NULL       -- メールアドレス
password    text NOT NULL              -- パスワード（ハッシュ化）
name        text NOT NULL              -- 表示名
role        text DEFAULT 'user'        -- ロール
company_id  text → companies(id)       -- 所属企業
created_at  timestamp NOT NULL         -- 作成日時
created_by  text → users(id)           -- 作成者（管理者）

-- 統計情報
現在のサイズ: 80 kB
推定データ: 4レコード
RLS: 無効
```

### 📊 usage_limits - 利用制限管理
```sql
-- テーブル構造（6カラム）
user_id                  text PRIMARY KEY → users(id)
document_uploads_used    int DEFAULT 0      -- 使用済みドキュメント数
document_uploads_limit   int DEFAULT 2      -- ドキュメント上限
questions_used          int DEFAULT 0      -- 使用済み質問数
questions_limit         int DEFAULT 10     -- 質問回数上限
is_unlimited            bool DEFAULT false -- 無制限フラグ

-- 統計情報
現在のサイズ: 64 kB
推定データ: 4レコード
RLS: 無効
```

### 📄 document_sources - ドキュメント管理（🚀最適化済み）
```sql
-- テーブル構造（12カラム）- 実際のSupabase構造
id           text PRIMARY KEY              -- ドキュメントID
name         text NOT NULL                 -- ファイル名
type         text NOT NULL                 -- ファイル種別（PDF、Excel等）
page_count   integer                      -- ページ数
uploaded_by  text NOT NULL → users(id)     -- アップロード者
company_id   text NOT NULL → companies(id) -- 所属企業
uploaded_at  timestamp NOT NULL           -- アップロード日時
active       boolean DEFAULT true         -- 有効フラグ
special      text                         -- 特殊属性（メタデータ）
parent_id    text → document_sources(id)  -- 親ドキュメント（階層構造）🆕
doc_id       text UNIQUE                  -- ドキュメント識別子🆕

-- 統計情報（2025年1月現在）
現在のサイズ: 104 kB
推定データ: 6レコード（アクティブ）
RLS: 無効

-- ✅ 最適化完了
-- ❌ content カラム削除済み（chunksテーブルで管理）
-- ❌ embedding カラム削除済み（chunksテーブルで管理）
-- 🆕 parent_id: 階層構造サポート
-- 🆕 doc_id: ユニーク識別子
```

### 🧩 chunks - チャンク管理テーブル（🆕ベクトルRAG対応）

**📋 テーブル構造詳細:**
```sql
-- テーブル構造（8カラム）- 実際のSupabase構造
id          uuid PRIMARY KEY DEFAULT gen_random_uuid()  -- チャンク一意ID（UUID）
content     text NOT NULL                              -- チャンク本文（300-500トークン）
embedding   vector                                     -- 🧠 Gemini Embedding（768次元ベクトル）
chunk_index integer NOT NULL                           -- チャンクの順序（0, 1, 2, …）
doc_id      text NOT NULL                             -- 紐づく document_sources.id（親）
company_id  text                                       -- 所属企業ID（企業分離用）
created_at  timestamptz DEFAULT now()                  -- 登録日時
updated_at  timestamptz DEFAULT now()                  -- 更新日時

-- 統計情報（2025年1月現在）
現在のサイズ: 58 MB
推定データ: 2,953レコード（アクティブ）
RLS: 無効

-- インデックス（推奨）
CREATE INDEX idx_chunks_doc_id ON chunks(doc_id);
CREATE INDEX idx_chunks_company_id ON chunks(company_id);
CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

**🔧 主な用途:**
| 用途 | 説明 |
|------|------|
| **高速な部分検索（semantic）** | embedding検索で、質問と「意味的に近いチャンク」だけを抽出する |
| **LLMとの組み合わせ（RAG）** | Gemini 2.5 Flashに「部分情報だけ」渡すことで効率よく回答を生成 |
| **ドキュメント単位の絞り込み** | doc_idで document_sources と紐づけて、対象ファイル内に限定可能 |
| **企業データ分離** | company_idで企業ごとのデータを分離管理 |

**🚀 パフォーマンス:**
- **pgvector拡張**: 高速ベクトル検索対応
- **バッチ処理**: 50個単位でembedding生成・挿入
- **リアルタイム保存**: ドキュメント処理と並行してチャンク保存

### 💬 chat_history - チャット履歴
```sql
-- テーブル構造（20カラム）
id               text PRIMARY KEY     -- チャットID
user_message     text NOT NULL        -- ユーザー質問
bot_response     text NOT NULL        -- AI応答
timestamp        timestamp NOT NULL   -- 会話時刻
category         text                 -- カテゴリ分類
sentiment        text                 -- 感情分析結果
employee_id      text                 -- 従業員ID
employee_name    text                 -- 従業員名
source_document  text                 -- 参照ドキュメント
source_page      text                 -- 参照ページ
user_id          varchar              -- ユーザーID
company_id       varchar              -- 企業ID

-- 🤖 AI分析情報（Gemini 2.5 Flash）
model_name       varchar DEFAULT 'gpt-4o-mini'  -- AIモデル名🔄
input_tokens     int DEFAULT 0        -- 入力トークン数
output_tokens    int DEFAULT 0        -- 出力トークン数
total_tokens     int DEFAULT 0        -- 合計トークン数
cost_usd         numeric DEFAULT 0.000000    -- コスト（USD）
base_cost_usd    numeric DEFAULT 0.000000    -- 基本コスト
prompt_cost_usd  numeric DEFAULT 0.000000    -- プロンプトコスト
prompt_references int DEFAULT 0       -- プロンプト参照数

-- 統計情報（2025年1月現在）
現在のサイズ: 592 kB
推定データ: 69レコード
RLS: 無効
```

### 📊 plan_history - プラン変更履歴（🆕新機能）
```sql
-- テーブル構造（6カラム）
id              text PRIMARY KEY DEFAULT gen_random_uuid()  -- 変更履歴ID
user_id         text NOT NULL → users(id)     -- ユーザーID
from_plan       text NOT NULL                  -- 変更前プラン
to_plan         text NOT NULL                  -- 変更後プラン
changed_at      timestamp DEFAULT now()        -- 変更日時
duration_days   integer                       -- プラン期間（日数）

-- 統計情報（2025年1月現在）
現在のサイズ: 32 kB
推定データ: 1レコード
RLS: 無効
```

### 📝 applications - 申請管理（🆕新機能）
```sql
-- テーブル構造（14カラム）
id                 text PRIMARY KEY           -- 申請ID
company_name       text NOT NULL              -- 会社名
contact_name       text NOT NULL              -- 担当者名
email              text NOT NULL              -- メールアドレス
phone              text                       -- 電話番号
expected_users     text                       -- 予想ユーザー数
current_usage      text                       -- 現在の使用状況
message            text                       -- メッセージ
application_type   text DEFAULT 'production-upgrade'  -- 申請種別
status             text DEFAULT 'pending'     -- ステータス
submitted_at       text NOT NULL              -- 申請日時
processed_at       text                       -- 処理日時
processed_by       text                       -- 処理者
notes              text                       -- 備考

-- 統計情報（2025年1月現在）
現在のサイズ: 48 kB
推定データ: 0レコード
RLS: 無効
```

### 📊 monthly_token_usage - 月次トークン使用量（🆕新機能）
```sql
-- テーブル構造（11カラム）
id                   varchar PRIMARY KEY       -- 使用量ID
company_id           varchar NOT NULL          -- 企業ID
user_id              varchar NOT NULL          -- ユーザーID
year_month           varchar NOT NULL          -- 年月（YYYY-MM）
total_input_tokens   int DEFAULT 0             -- 入力トークン合計
total_output_tokens  int DEFAULT 0             -- 出力トークン合計
total_tokens         int DEFAULT 0             -- 総トークン数
total_cost_usd       numeric DEFAULT 0.000000  -- 総コスト（USD）
conversation_count   int DEFAULT 0             -- 会話回数
created_at           timestamp DEFAULT CURRENT_TIMESTAMP  -- 作成日時
updated_at           timestamp DEFAULT CURRENT_TIMESTAMP  -- 更新日時

-- 統計情報（2025年1月現在）
現在のサイズ: 88 kB
推定データ: 0レコード
RLS: 無効

-- ユニーク制約（推奨）
UNIQUE(company_id, user_id, year_month)
```

### ⚙️ company_settings - 企業設定（🆕新機能）
```sql
-- テーブル構造（7カラム）
company_id                     varchar PRIMARY KEY    -- 企業ID
monthly_token_limit            int DEFAULT 25000000   -- 月次トークン制限
warning_threshold_percentage   int DEFAULT 80         -- 警告閾値（%）
critical_threshold_percentage  int DEFAULT 95         -- 危険閾値（%）
pricing_tier                   varchar DEFAULT 'basic' -- 料金ティア
created_at                     timestamp DEFAULT CURRENT_TIMESTAMP  -- 作成日時
updated_at                     timestamp DEFAULT CURRENT_TIMESTAMP  -- 更新日時

-- 統計情報（2025年1月現在）
現在のサイズ: 24 kB
推定データ: 1レコード
RLS: 無効
```

---

## 🔗 テーブル関係図

### 🏢 企業・ユーザー関係
```
companies (企業マスター)
    ↓ 1:N
users (アプリケーションユーザー)
    ↓ 1:1
usage_limits (利用制限)
    ↓ 1:N
plan_history (プラン変更履歴)🆕

companies
    ↓ 1:1
company_settings (企業設定)🆕
    ↓ 1:N
monthly_token_usage (月次使用量)🆕
```

### 📄 ドキュメント・チャンク関係
```
companies
    ↓ 1:N
document_sources (ドキュメント管理)
    ↓ 1:N
chunks (RAGチャンク)

document_sources (自己参照)
    ↓ parent_id (階層構造)🆕
document_sources

chunks → pgvector extension (ベクトル検索)
```

### 💬 チャット・分析関係
```
users
    ↓ 1:N
chat_history (チャット履歴)
    ↓ 分析データ集約
monthly_token_usage (月次統計)

companies
    ↓ 1:N
applications (申請管理)🆕
```

### 🔐 認証システム関係
```
auth.users (Supabase認証)
    ↓ 1:N
auth.sessions (セッション管理)
    ↓ 1:N
auth.mfa_factors (MFA要素)
    ↓ 1:N
auth.mfa_challenges (認証チャレンジ)

auth.users
    ↓ 1:N
auth.identities (外部ID連携)

auth.sso_providers (SSOプロバイダー)
    ↓ 1:N
auth.sso_domains (ドメインマッピング)
    ↓ 1:N
auth.saml_providers (SAML設定)
```

---

## 📊 データフロー解説

### 🔄 ユーザー登録・認証フロー
```
1. 新規ユーザー登録
   auth.users → 認証情報作成
   ↓
2. アプリケーションユーザー作成
   public.users → プロフィール作成
   ↓
3. 利用制限設定
   usage_limits → デフォルト制限適用
   ↓
4. 企業設定確認
   company_settings → トークン制限取得🆕
```

### 📤 ドキュメントアップロード・RAG処理フロー
```
1. ファイルアップロード
   document_sources → メタデータ保存
   ↓
2. テキスト抽出・前処理
   PDF/Excel → テキスト抽出
   ↓
3. チャンク分割（300-500トークン）
   chunks → content（本文）保存
   ↓
4. Gemini Embedding生成
   chunks → embedding（768次元ベクトル）🔄
   ↓
5. pgvector インデックス更新
   ベクトル検索インデックス最適化
```

### 💬 チャット・RAG検索フロー
```
1. ユーザー質問受信
   chat_history → user_message 保存
   ↓
2. ベクトル検索実行
   chunks.embedding → 類似チャンク検索
   ↓
3. Gemini 2.5 Flash 応答生成🔄
   RAGコンテキスト → AI応答
   ↓
4. 結果保存・統計更新
   chat_history → bot_response 保存
   monthly_token_usage → トークン使用量更新🆕
   ↓
5. 利用制限チェック
   usage_limits → 残り制限確認
```

### 📊 分析・管理フロー
```
1. リアルタイム統計
   chat_history → 即座に統計更新
   ↓
2. 月次集計処理
   monthly_token_usage → 企業・ユーザー別集計🆕
   ↓
3. 制限アラート
   company_settings → 閾値チェック🆕
   ↓
4. プラン変更
   plan_history → 変更履歴記録🆕
```

### 🎫 申請・承認フロー
```
1. アップグレード申請
   applications → 申請情報保存🆕
   ↓
2. 管理者確認
   applications.status → 'pending' → 'approved'🆕
   ↓
3. プラン変更実行
   plan_history → 変更履歴記録🆕
   usage_limits → 制限値更新
```

---

## 🔧 運用・管理機能

### 🎯 パフォーマンス最適化

#### ベクトル検索の最適化
```sql
-- pgvector インデックス作成（必須）
CREATE EXTENSION IF NOT EXISTS vector;

-- 効率的なベクトルインデックス
CREATE INDEX idx_chunks_embedding_ivfflat 
ON chunks USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- 高速検索のための複合インデックス
CREATE INDEX idx_chunks_company_doc 
ON chunks(company_id, doc_id);

-- アクティブチャンクのみの検索
CREATE INDEX idx_chunks_active 
ON chunks(company_id) 
WHERE doc_id IN (
    SELECT id FROM document_sources WHERE active = true
);
```

#### 統計処理の最適化
```sql
-- 月次統計の高速化
CREATE INDEX idx_monthly_usage_lookup 
ON monthly_token_usage(company_id, user_id, year_month);

-- チャット履歴の分析用インデックス
CREATE INDEX idx_chat_history_analytics 
ON chat_history(company_id, timestamp DESC);

-- プラン履歴の追跡用
CREATE INDEX idx_plan_history_user_time 
ON plan_history(user_id, changed_at DESC);
```

### 📊 監視・アラート

#### トークン使用量監視
```sql
-- 企業別月次使用量チェック
SELECT 
    c.name as company_name,
    mtu.year_month,
    mtu.total_tokens,
    cs.monthly_token_limit,
    ROUND(mtu.total_tokens::float / cs.monthly_token_limit * 100, 1) as usage_percentage
FROM monthly_token_usage mtu
JOIN companies c ON mtu.company_id = c.id
JOIN company_settings cs ON c.id = cs.company_id
WHERE mtu.year_month = TO_CHAR(CURRENT_DATE, 'YYYY-MM')
ORDER BY usage_percentage DESC;
```

#### 異常検知クエリ
```sql
-- 大量トークン使用の検知
SELECT 
    ch.company_id,
    ch.user_id,
    DATE(ch.timestamp) as date,
    SUM(ch.total_tokens) as daily_tokens,
    COUNT(*) as conversation_count
FROM chat_history ch
WHERE ch.timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY ch.company_id, ch.user_id, DATE(ch.timestamp)
HAVING SUM(ch.total_tokens) > 100000  -- 10万トークン/日
ORDER BY daily_tokens DESC;
```

### 🔒 セキュリティ・データ保護

#### 企業データ分離の確認
```sql
-- 企業間のデータ漏洩チェック
SELECT 
    'chunks' as table_name,
    company_id,
    COUNT(*) as record_count
FROM chunks 
GROUP BY company_id
UNION ALL
SELECT 
    'document_sources',
    company_id,
    COUNT(*)
FROM document_sources 
GROUP BY company_id
ORDER BY table_name, company_id;
```

#### 削除データの完全性確認
```sql
-- カスケード削除の動作確認
SELECT 
    ds.id as doc_id,
    ds.name as doc_name,
    COUNT(c.id) as chunk_count
FROM document_sources ds
LEFT JOIN chunks c ON ds.id = c.doc_id
WHERE ds.active = false
GROUP BY ds.id, ds.name
HAVING COUNT(c.id) > 0;  -- 非アクティブなのにチャンクが残っている場合
```

### 🚀 運用のベストプラクティス

#### 1. 定期メンテナンス（推奨）
```bash
# 週次実行推奨
# 1. 統計情報更新
ANALYZE chunks;
ANALYZE chat_history;
ANALYZE monthly_token_usage;

# 2. 不要データクリーンアップ（6ヶ月以上前）
DELETE FROM chat_history 
WHERE timestamp < CURRENT_DATE - INTERVAL '6 months';

# 3. インデックス再構築（月次）
REINDEX INDEX idx_chunks_embedding_ivfflat;
```

#### 2. 容量管理
```sql
-- テーブルサイズ監視
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;
```

#### 3. バックアップ戦略
- **chunks テーブル**: 最重要（embeddings再生成コスト高）
- **chat_history**: 分析用途で重要
- **document_sources**: メタデータ（復旧容易）
- **auth スキーマ**: Supabase自動バックアップ

#### 4. スケーリング指針
| 指標 | 注意 | 対策 |
|------|------|------|
| **chunks > 1万件** | ベクトル検索遅延 | インデックス調整 |
| **チャット > 1000件/日** | レスポンス低下 | 履歴アーカイブ |
| **月次トークン > 1000万** | コスト急増 | 制限強化・プラン見直し |

---

## 🎉 まとめ

### ✅ システムの強み
- **🔐 強固な認証**: Supabase auth + MFA + SSO対応
- **🧠 高精度RAG**: pgvector + Gemini 2.5 Flash
- **📊 詳細分析**: リアルタイム統計 + 月次レポート
- **🏢 マルチテナント**: 企業データ完全分離
- **⚡ 高パフォーマンス**: 最適化されたインデックス戦略
- **🔄 運用性**: 充実した監視・アラート機能

### 🚀 今後の拡張性
- **AI機能強化**: より高度なRAG・マルチモーダル対応
- **分析機能**: BI連携・カスタムダッシュボード
- **API拡張**: 外部システム連携・Webhook
- **グローバル対応**: 多言語・タイムゾーン対応

**現在のアーキテクチャは、中規模〜大規模企業での本格運用に対応した堅牢な設計となっています。** 🎯 