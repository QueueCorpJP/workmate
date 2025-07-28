# Workmate プロジェクト データベース設計書

## 📋 概要

**プロジェクト名**: Workmate-Chatbot  
**データベース**: Supabase PostgreSQL  
**プロジェクトID**: lqlswsymlyscfmnihtze  
**リージョン**: ap-northeast-1  
**PostgreSQL バージョン**: 15.8.1.070  

Workmateは、アップロードしたPDF・ドキュメント・FAQなどを自動で解析し、RAG（Retrieval-Augmented Generation）技術を用いて高精度なチャット応答を提供するAIチャットボットプラットフォームです。

## 📊 データ統計

| テーブル | レコード数 | 説明 |
|---------|-----------|------|
| chat_history | 730 | チャット履歴 |
| chunks | 15,587 | ドキュメントチャンク |
| users | 17 | ユーザー |
| companies | 13 | 企業 |

---

## 🏗️ テーブル構造

### 🔐 認証システム (auth スキーマ)

#### `auth.users`
**用途**: Supabaseの認証システムによるユーザー管理  
**サイズ**: 96 kB  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | uuid | PK | ユーザーID |
| email | varchar | - | メールアドレス |
| encrypted_password | varchar | - | 暗号化パスワード |
| email_confirmed_at | timestamptz | - | メール確認日時 |
| created_at | timestamptz | - | 作成日時 |
| updated_at | timestamptz | - | 更新日時 |
| raw_user_meta_data | jsonb | - | ユーザーメタデータ |
| is_super_admin | boolean | - | スーパー管理者フラグ |
| phone | text | UNIQUE | 電話番号 |
| confirmed_at | timestamptz | GENERATED | 確認日時 |

#### `auth.sessions`
**用途**: ユーザーセッション管理  
**サイズ**: 40 kB  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | uuid | PK | セッションID |
| user_id | uuid | FK | ユーザーID |
| created_at | timestamptz | - | 作成日時 |
| updated_at | timestamptz | - | 更新日時 |
| not_after | timestamptz | - | 有効期限 |
| refreshed_at | timestamp | - | リフレッシュ日時 |
| user_agent | text | - | ユーザーエージェント |
| ip | inet | - | IPアドレス |

#### `auth.identities`
**用途**: 外部プロバイダー認証情報  
**サイズ**: 40 kB  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | uuid | PK | アイデンティティID |
| user_id | uuid | FK | ユーザーID |
| provider | text | - | プロバイダー名 |
| provider_id | text | - | プロバイダーID |
| identity_data | jsonb | - | アイデンティティデータ |
| email | text | GENERATED | メールアドレス |

---

### 👥 ユーザー・企業管理 (public スキーマ)

#### `public.users`
**用途**: アプリケーション固有のユーザー情報  
**サイズ**: 64 kB | **レコード数**: 17  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | text | PK | ユーザーID |
| email | text | UNIQUE | メールアドレス |
| password | text | - | パスワード |
| name | text | - | ユーザー名 |
| role | text | DEFAULT 'user' | 役割 (user/admin) |
| company_id | text | FK | 企業ID |
| created_at | timestamp | - | 作成日時 |
| created_by | text | FK | 作成者ID |

**関連テーブル**: companies, usage_limits, plan_history, document_sources

#### `public.companies`
**用途**: 企業情報管理  
**サイズ**: 32 kB | **レコード数**: 13  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | text | PK | 企業ID |
| name | text | - | 企業名 |
| created_at | timestamp | - | 作成日時 |

**関連テーブル**: users, document_sources, prompt_templates, template_usage_history

#### `public.usage_limits`
**用途**: ユーザーの利用制限管理  
**サイズ**: 64 kB | **レコード数**: 17  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| user_id | text | PK, FK | ユーザーID |
| document_uploads_used | integer | DEFAULT 0 | 使用ドキュメント数 |
| document_uploads_limit | integer | DEFAULT 2 | ドキュメント上限 |
| questions_used | integer | DEFAULT 0 | 使用質問数 |
| questions_limit | integer | DEFAULT 10 | 質問上限 |
| is_unlimited | boolean | DEFAULT false | 無制限フラグ |

---

### 💬 チャット機能

#### `public.chat_history`
**用途**: チャット履歴とメタデータ  
**サイズ**: 1584 kB | **レコード数**: 730  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | text | PK | チャットID |
| user_message | text | - | ユーザーメッセージ |
| bot_response | text | - | ボット応答 |
| timestamp | timestamptz | DEFAULT now() | タイムスタンプ |
| category | text | - | カテゴリ |
| sentiment | text | - | 感情分析結果 |
| employee_id | text | - | 従業員ID |
| employee_name | text | - | 従業員名 |
| source_document | text | - | 参照ドキュメント |
| source_page | text | - | 参照ページ |
| input_tokens | integer | DEFAULT 0 | 入力トークン数 |
| output_tokens | integer | DEFAULT 0 | 出力トークン数 |
| total_tokens | integer | DEFAULT 0 | 総トークン数 |
| model_name | varchar | DEFAULT 'gpt-4o-mini' | 使用モデル |
| cost_usd | numeric | DEFAULT 0.000000 | コスト（USD） |
| user_id | varchar | - | ユーザーID |
| company_id | varchar | - | 企業ID |
| prompt_references | integer | DEFAULT 0 | プロンプト参照数 |
| base_cost_usd | numeric | DEFAULT 0.000000 | 基本コスト |
| prompt_cost_usd | numeric | DEFAULT 0.000000 | プロンプトコスト |

---

### 📄 ドキュメント管理

#### `public.document_sources`
**用途**: アップロードされたドキュメント情報  
**サイズ**: 184 kB | **レコード数**: 10  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | text | PK | ドキュメントID |
| name | text | - | ドキュメント名 |
| type | text | - | ファイルタイプ |
| page_count | integer | - | ページ数 |
| uploaded_by | text | FK | アップロード者 |
| company_id | text | FK | 企業ID |
| uploaded_at | timestamptz | - | アップロード日時 |
| active | boolean | DEFAULT true | アクティブ状態 |
| special | text | - | 特別フラグ |
| parent_id | text | FK | 親ドキュメントID |
| doc_id | text | UNIQUE | ドキュメント識別子 |
| metadata | jsonb | - | メタデータ |

#### `public.chunks`
**用途**: ドキュメントのベクトル化チャンク  
**サイズ**: 388 MB | **レコード数**: 15,587  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | uuid | PK, DEFAULT gen_random_uuid() | チャンクID |
| content | text | - | チャンク内容 |
| chunk_index | integer | - | チャンクインデックス |
| doc_id | text | - | ドキュメントID |
| company_id | text | - | 企業ID |
| created_at | timestamptz | DEFAULT now() | 作成日時 |
| updated_at | timestamptz | DEFAULT now() | 更新日時 |
| embedding | vector | - | ベクトル埋め込み |

---

### 🎯 プロンプトテンプレート機能

#### `public.template_categories`
**用途**: プロンプトテンプレートのカテゴリ管理  
**サイズ**: 64 kB | **レコード数**: 6  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | uuid | PK, DEFAULT gen_random_uuid() | カテゴリID |
| name | text | - | カテゴリ名 |
| description | text | - | 説明 |
| icon | text | - | アイコン |
| display_order | integer | DEFAULT 0 | 表示順 |
| is_active | boolean | DEFAULT true | アクティブ状態 |
| created_at | timestamptz | DEFAULT now() | 作成日時 |
| updated_at | timestamptz | DEFAULT now() | 更新日時 |

#### `public.prompt_templates`
**用途**: プロンプトテンプレートの本体情報  
**サイズ**: 128 kB | **レコード数**: 2  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | uuid | PK, DEFAULT gen_random_uuid() | テンプレートID |
| title | text | - | タイトル |
| description | text | - | 説明 |
| template_content | text | - | テンプレート内容 |
| category_id | uuid | FK | カテゴリID |
| template_type | text | DEFAULT 'system' | テンプレートタイプ |
| difficulty_level | text | DEFAULT 'beginner' | 難易度 |
| usage_count | integer | DEFAULT 0 | 使用回数 |
| is_public | boolean | DEFAULT true | 公開状態 |
| is_active | boolean | DEFAULT true | アクティブ状態 |
| created_by | text | FK | 作成者 |
| company_id | text | FK | 企業ID |
| created_at | timestamptz | DEFAULT now() | 作成日時 |
| updated_at | timestamptz | DEFAULT now() | 更新日時 |

**制約**:
- `template_type` ∈ {'system', 'company', 'user'}
- `difficulty_level` ∈ {'beginner', 'intermediate', 'advanced'}

#### `public.template_variables`
**用途**: テンプレート内変数の定義  
**サイズ**: 40 kB  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | uuid | PK, DEFAULT gen_random_uuid() | 変数ID |
| template_id | uuid | FK | テンプレートID |
| variable_name | text | - | 変数名 |
| variable_label | text | - | 変数ラベル |
| variable_type | text | DEFAULT 'text' | 変数タイプ |
| is_required | boolean | DEFAULT true | 必須フラグ |
| default_value | text | - | デフォルト値 |
| placeholder_text | text | - | プレースホルダー |
| validation_rules | jsonb | - | バリデーションルール |
| display_order | integer | DEFAULT 0 | 表示順 |
| created_at | timestamptz | DEFAULT now() | 作成日時 |

**制約**:
- `variable_type` ∈ {'text', 'textarea', 'date', 'select', 'number'}

#### `public.user_template_favorites`
**用途**: ユーザーのお気に入りテンプレート  
**サイズ**: 48 kB  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | uuid | PK, DEFAULT gen_random_uuid() | お気に入りID |
| user_id | text | FK | ユーザーID |
| template_id | uuid | FK | テンプレートID |
| custom_title | text | - | カスタムタイトル |
| custom_variables | jsonb | - | カスタム変数 |
| created_at | timestamptz | DEFAULT now() | 作成日時 |

#### `public.template_usage_history`
**用途**: テンプレート使用履歴と分析データ  
**サイズ**: 56 kB  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | uuid | PK, DEFAULT gen_random_uuid() | 履歴ID |
| user_id | text | FK | ユーザーID |
| template_id | uuid | FK | テンプレートID |
| company_id | text | FK | 企業ID |
| executed_prompt | text | - | 実行されたプロンプト |
| variable_values | jsonb | - | 変数値 |
| chat_history_id | text | FK | チャット履歴ID |
| execution_time_ms | integer | - | 実行時間（ms） |
| success | boolean | DEFAULT true | 成功フラグ |
| error_message | text | - | エラーメッセージ |
| used_at | timestamptz | DEFAULT now() | 使用日時 |

#### `public.company_template_settings`
**用途**: 会社ごとのテンプレート機能設定  
**サイズ**: 24 kB  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| company_id | text | PK, FK | 企業ID |
| allow_user_templates | boolean | DEFAULT true | ユーザーテンプレート許可 |
| allow_template_sharing | boolean | DEFAULT true | テンプレート共有許可 |
| max_templates_per_user | integer | DEFAULT 50 | ユーザー当たり最大テンプレート数 |
| enable_template_analytics | boolean | DEFAULT true | テンプレート分析有効 |
| default_template_category | uuid | FK | デフォルトカテゴリ |
| created_at | timestamptz | DEFAULT now() | 作成日時 |
| updated_at | timestamptz | DEFAULT now() | 更新日時 |

---

### 📊 利用状況・分析

#### `public.monthly_token_usage`
**用途**: 月次トークン使用量追跡  
**サイズ**: 48 kB  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | varchar | PK | 使用量ID |
| company_id | varchar | - | 企業ID |
| user_id | varchar | - | ユーザーID |
| year_month | varchar | - | 年月 |
| total_input_tokens | integer | DEFAULT 0 | 総入力トークン |
| total_output_tokens | integer | DEFAULT 0 | 総出力トークン |
| total_tokens | integer | DEFAULT 0 | 総トークン |
| total_cost_usd | numeric | DEFAULT 0.000000 | 総コスト |
| conversation_count | integer | DEFAULT 0 | 会話数 |
| created_at | timestamp | DEFAULT CURRENT_TIMESTAMP | 作成日時 |
| updated_at | timestamp | DEFAULT CURRENT_TIMESTAMP | 更新日時 |

#### `public.company_settings`
**用途**: 企業設定管理  
**サイズ**: 24 kB | **レコード数**: 1  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| company_id | varchar | PK | 企業ID |
| monthly_token_limit | integer | DEFAULT 25000000 | 月次トークン制限 |
| warning_threshold_percentage | integer | DEFAULT 80 | 警告閾値（%） |
| critical_threshold_percentage | integer | DEFAULT 95 | 重要閾値（%） |
| pricing_tier | varchar | DEFAULT 'basic' | 料金プラン |
| created_at | timestamp | DEFAULT CURRENT_TIMESTAMP | 作成日時 |
| updated_at | timestamp | DEFAULT CURRENT_TIMESTAMP | 更新日時 |

#### `public.plan_history`
**用途**: プラン変更履歴  
**サイズ**: 32 kB | **レコード数**: 10  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | text | PK, DEFAULT gen_random_uuid() | 履歴ID |
| user_id | text | FK | ユーザーID |
| from_plan | text | - | 変更前プラン |
| to_plan | text | - | 変更後プラン |
| changed_at | timestamp | DEFAULT now() | 変更日時 |
| duration_days | integer | - | 期間（日） |

---

### 🔔 通知・申請

#### `public.notifications`
**用途**: システム通知管理  
**サイズ**: 48 kB | **レコード数**: 6  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | uuid | PK, DEFAULT gen_random_uuid() | 通知ID |
| title | text | - | タイトル |
| content | text | - | 内容 |
| notification_type | text | DEFAULT 'general' | 通知タイプ |
| created_at | timestamptz | DEFAULT now() | 作成日時 |
| updated_at | timestamptz | DEFAULT now() | 更新日時 |
| created_by | text | - | 作成者 |

#### `public.applications`
**用途**: 申請管理（プロダクション移行等）  
**サイズ**: 48 kB  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | text | PK | 申請ID |
| company_name | text | - | 企業名 |
| contact_name | text | - | 担当者名 |
| email | text | - | メールアドレス |
| phone | text | - | 電話番号 |
| expected_users | text | - | 予想ユーザー数 |
| current_usage | text | - | 現在の使用状況 |
| message | text | - | メッセージ |
| application_type | text | DEFAULT 'production-upgrade' | 申請タイプ |
| status | text | DEFAULT 'pending' | ステータス |
| submitted_at | text | - | 提出日時 |
| processed_at | text | - | 処理日時 |
| processed_by | text | - | 処理者 |
| notes | text | - | 備考 |

---

### 💾 ストレージ (storage スキーマ)

#### `storage.buckets`
**用途**: ストレージバケット管理  
**サイズ**: 24 kB  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | text | PK | バケットID |
| name | text | - | バケット名 |
| owner_id | text | - | 所有者ID |
| created_at | timestamptz | DEFAULT now() | 作成日時 |
| updated_at | timestamptz | DEFAULT now() | 更新日時 |
| public | boolean | DEFAULT false | 公開設定 |
| file_size_limit | bigint | - | ファイルサイズ制限 |
| allowed_mime_types | text[] | - | 許可MIMEタイプ |

#### `storage.objects`
**用途**: ストレージオブジェクト管理  
**サイズ**: 40 kB  

| カラム | 型 | 制約 | 説明 |
|--------|----|----- |------|
| id | uuid | PK, DEFAULT gen_random_uuid() | オブジェクトID |
| bucket_id | text | FK | バケットID |
| name | text | - | オブジェクト名 |
| owner_id | text | - | 所有者ID |
| created_at | timestamptz | DEFAULT now() | 作成日時 |
| updated_at | timestamptz | DEFAULT now() | 更新日時 |
| last_accessed_at | timestamptz | DEFAULT now() | 最終アクセス日時 |
| metadata | jsonb | - | メタデータ |
| path_tokens | text[] | GENERATED | パストークン |
| version | text | - | バージョン |
| user_metadata | jsonb | - | ユーザーメタデータ |

---

## 🔗 主要なリレーションシップ

### ユーザー関連
```
companies (1) ←→ (N) users
users (1) ←→ (1) usage_limits
users (1) ←→ (N) plan_history
users (1) ←→ (N) document_sources
```

### チャット関連
```
users (1) ←→ (N) chat_history
companies (1) ←→ (N) chat_history
chat_history (1) ←→ (N) template_usage_history
```

### ドキュメント関連
```
document_sources (1) ←→ (N) chunks
companies (1) ←→ (N) document_sources
users (1) ←→ (N) document_sources
```

### テンプレート関連
```
template_categories (1) ←→ (N) prompt_templates
prompt_templates (1) ←→ (N) template_variables
prompt_templates (1) ←→ (N) user_template_favorites
prompt_templates (1) ←→ (N) template_usage_history
companies (1) ←→ (N) prompt_templates
users (1) ←→ (N) prompt_templates
```

### 認証関連
```
auth.users (1) ←→ (N) auth.sessions
auth.users (1) ←→ (N) auth.identities
auth.users (1) ←→ (N) auth.mfa_factors
```

---

## 🎯 主要機能とテーブルの対応

### RAGチャットボット機能
- **ドキュメント管理**: `document_sources`, `chunks`
- **チャット処理**: `chat_history`
- **ベクトル検索**: `chunks.embedding`

### ユーザー管理
- **認証**: `auth.users`, `auth.sessions`, `auth.identities`
- **アプリケーション情報**: `public.users`
- **利用制限**: `usage_limits`

### 企業管理
- **企業情報**: `companies`
- **設定**: `company_settings`
- **テンプレート設定**: `company_template_settings`

### プロンプトテンプレート
- **テンプレート管理**: `prompt_templates`, `template_categories`
- **変数定義**: `template_variables`
- **使用履歴**: `template_usage_history`
- **お気に入り**: `user_template_favorites`

### 分析・監視
- **利用状況**: `monthly_token_usage`
- **プラン履歴**: `plan_history`
- **通知**: `notifications`

### ストレージ
- **ファイル管理**: `storage.buckets`, `storage.objects`
- **マルチパートアップロード**: `storage.s3_multipart_uploads`

---

## 📈 パフォーマンス考慮事項

### インデックス戦略
- **chunks.embedding**: ベクトル検索用インデックス
- **chat_history.timestamp**: 時系列検索用
- **chunks.doc_id**: ドキュメント検索用
- **users.email**: ログイン用ユニークインデックス

### 大容量データ
- **chunks**: 15,587レコード、388MB（ベクトルデータ）
- **chat_history**: 730レコード、1.6MB（継続的増加）

### RLS (Row Level Security)
- **auth スキーマ**: 全テーブルでRLS有効
- **storage スキーマ**: 全テーブルでRLS有効
- **public スキーマ**: RLS無効（アプリケーションレベルで制御）

---

## 🔧 開発・運用情報

### 環境設定
```env
SUPABASE_URL=https://lqlswsymlyscfmnihtze.supabase.co/
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 主要な制約・制限
- **ドキュメントアップロード**: デフォルト2件/ユーザー
- **質問制限**: デフォルト10件/ユーザー
- **月次トークン制限**: 25,000,000トークン/企業
- **テンプレート制限**: 50件/ユーザー

### 料金プラン
- **basic**: 基本プラン
- **production**: プロダクションプラン
- **unlimited**: 無制限プラン

---

*📅 最終更新: 2025年1月28日*  
*🔄 データベースバージョン: PostgreSQL 15.8.1.070*  
*📊 総テーブル数: 30+ (auth: 16, public: 16, storage: 4)* 