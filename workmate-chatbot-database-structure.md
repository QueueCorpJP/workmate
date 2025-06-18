# Workmate-Chatbot データベース構造説明書

## 概要

このドキュメントは、Workmate-Chatbotシステムのデータベース構造を詳しく説明します。システムは企業向けのAIチャットボットプラットフォームで、文書管理、ユーザー認証、使用量制限、チャット履歴などの機能を提供します。

## テーブル一覧

### 1. companies（企業テーブル）
**目的**: システムを利用する企業の基本情報を管理

| カラム名 | データ型 | 説明 |
|---------|----------|------|
| id | text | 企業ID（主キー） |
| name | text | 企業名 |
| created_at | timestamp | 作成日時 |

**リレーション**:
- `users` テーブルの `company_id` から参照される
- `document_sources` テーブルの `company_id` から参照される

### 2. users（ユーザーテーブル）
**目的**: システムを利用するユーザーの認証情報と基本情報を管理

| カラム名 | データ型 | デフォルト値 | 説明 |
|---------|----------|-------------|------|
| id | text | - | ユーザーID（主キー） |
| email | text | - | メールアドレス（ユニーク） |
| password | text | - | パスワード（ハッシュ化） |
| name | text | - | ユーザー名 |
| role | text | 'user' | ユーザーロール |
| company_id | text | - | 所属企業ID |
| created_at | timestamp | - | 作成日時 |
| created_by | text | - | 作成者ID |

**リレーション**:
- `companies` テーブルの `id` を参照
- `document_sources` テーブルの `uploaded_by` から参照される
- `usage_limits` テーブルの `user_id` から参照される
- `plan_history` テーブルの `user_id` から参照される
- 自己参照（`created_by` → `id`）

### 3. usage_limits（使用量制限テーブル）
**目的**: ユーザーごとの使用量制限と現在の使用状況を管理

| カラム名 | データ型 | デフォルト値 | 説明 |
|---------|----------|-------------|------|
| user_id | text | - | ユーザーID（主キー） |
| document_uploads_used | integer | 0 | 使用した文書アップロード数 |
| document_uploads_limit | integer | 2 | 文書アップロード制限数 |
| questions_used | integer | 0 | 使用した質問数 |
| questions_limit | integer | 10 | 質問制限数 |
| is_unlimited | boolean | false | 無制限フラグ |

**リレーション**:
- `users` テーブルの `id` を参照

### 4. document_sources（文書ソーステーブル）
**目的**: アップロードされた文書の情報とコンテンツを管理

| カラム名 | データ型 | デフォルト値 | 説明 |
|---------|----------|-------------|------|
| id | text | - | 文書ID（主キー） |
| name | text | - | 文書名 |
| type | text | - | 文書タイプ |
| page_count | integer | - | ページ数 |
| content | text | - | 文書内容 |
| uploaded_by | text | - | アップロード者ID |
| company_id | text | - | 企業ID |
| uploaded_at | timestamp | - | アップロード日時 |
| active | boolean | true | アクティブフラグ |

**リレーション**:
- `users` テーブルの `id` を参照（`uploaded_by`）
- `companies` テーブルの `id` を参照（`company_id`）

### 5. chat_history（チャット履歴テーブル）
**目的**: ユーザーとAIチャットボットのやり取りの履歴を記録

| カラム名 | データ型 | デフォルト値 | 説明 |
|---------|----------|-------------|------|
| id | text | - | チャット履歴ID（主キー） |
| user_message | text | - | ユーザーメッセージ |
| bot_response | text | - | ボットの応答 |
| timestamp | timestamp | - | やり取り日時 |
| category | text | - | 質問カテゴリ |
| sentiment | text | - | 感情分析結果 |
| employee_id | text | - | 従業員ID |
| employee_name | text | - | 従業員名 |
| source_document | text | - | 参照元文書 |
| source_page | text | - | 参照元ページ |
| input_tokens | integer | 0 | 入力トークン数 |
| output_tokens | integer | 0 | 出力トークン数 |
| total_tokens | integer | 0 | 総トークン数 |
| model_name | varchar | 'gpt-4o-mini' | 使用モデル名 |
| cost_usd | numeric | 0.000000 | 使用料金（USD） |
| user_id | varchar | - | ユーザーID |
| company_id | varchar | - | 企業ID |

### 6. plan_history（プラン履歴テーブル）
**目的**: ユーザーのプラン変更履歴を記録

| カラム名 | データ型 | デフォルト値 | 説明 |
|---------|----------|-------------|------|
| id | text | gen_random_uuid() | 履歴ID（主キー） |
| user_id | text | - | ユーザーID |
| from_plan | text | - | 変更前プラン |
| to_plan | text | - | 変更後プラン |
| changed_at | timestamp | now() | 変更日時 |
| duration_days | integer | - | 継続日数 |

**リレーション**:
- `users` テーブルの `id` を参照

### 7. applications（申請テーブル）
**目的**: 本格運用やアップグレードの申請を管理

| カラム名 | データ型 | デフォルト値 | 説明 |
|---------|----------|-------------|------|
| id | text | - | 申請ID（主キー） |
| company_name | text | - | 企業名 |
| contact_name | text | - | 連絡担当者名 |
| email | text | - | メールアドレス |
| phone | text | - | 電話番号 |
| expected_users | text | - | 想定ユーザー数 |
| current_usage | text | - | 現在の使用状況 |
| message | text | - | メッセージ |
| application_type | text | 'production-upgrade' | 申請タイプ |
| status | text | 'pending' | 申請ステータス |
| submitted_at | text | - | 申請日時 |
| processed_at | text | - | 処理日時 |
| processed_by | text | - | 処理者 |
| notes | text | - | 備考 |

### 8. monthly_token_usage（月次トークン使用量テーブル）
**目的**: 企業・ユーザーごとの月次トークン使用量を集計

| カラム名 | データ型 | デフォルト値 | 説明 |
|---------|----------|-------------|------|
| id | varchar | - | ID（主キー） |
| company_id | varchar | - | 企業ID |
| user_id | varchar | - | ユーザーID |
| year_month | varchar | - | 年月（YYYY-MM形式） |
| total_input_tokens | integer | 0 | 入力トークン総数 |
| total_output_tokens | integer | 0 | 出力トークン総数 |
| total_tokens | integer | 0 | 総トークン数 |
| total_cost_usd | numeric | 0.000000 | 総使用料金（USD） |
| conversation_count | integer | 0 | 会話数 |
| created_at | timestamp | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | timestamp | CURRENT_TIMESTAMP | 更新日時 |

### 9. company_settings（企業設定テーブル）
**目的**: 企業ごとの設定情報とトークン制限を管理

| カラム名 | データ型 | デフォルト値 | 説明 |
|---------|----------|-------------|------|
| company_id | varchar | - | 企業ID（主キー） |
| monthly_token_limit | integer | 25000000 | 月次トークン制限 |
| warning_threshold_percentage | integer | 80 | 警告閾値（%） |
| critical_threshold_percentage | integer | 95 | 危険閾値（%） |
| pricing_tier | varchar | 'basic' | 料金プラン |
| created_at | timestamp | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | timestamp | CURRENT_TIMESTAMP | 更新日時 |

## データベース設計の特徴

### 1. **多段階認証システム**
- 企業単位での管理
- ユーザーロールベースのアクセス制御
- 使用量制限の細かい管理

### 2. **使用量追跡機能**
- リアルタイムでの使用量監視
- 月次集計による詳細な分析
- コスト管理機能

### 3. **文書管理システム**
- 企業ごとの文書隔離
- 文書の有効/無効切り替え
- アップロード者の追跡

### 4. **チャット履歴の詳細記録**
- 感情分析結果の保存
- トークン使用量の追跡
- 参照元文書の記録

### 5. **プラン管理機能**
- プラン変更履歴の記録
- 申請プロセスの管理
- 企業設定の柔軟な管理

## 使用例

### 典型的なワークフロー

1. **企業登録**: `companies` テーブルに企業情報を登録
2. **ユーザー作成**: `users` テーブルにユーザーを作成し、企業に紐付け
3. **使用量制限設定**: `usage_limits` テーブルでユーザーの制限を設定
4. **文書アップロード**: `document_sources` テーブルに文書を保存
5. **チャット開始**: `chat_history` テーブルにやり取りを記録
6. **使用量集計**: `monthly_token_usage` テーブルで月次使用量を集計

このデータベース設計により、企業向けAIチャットボットプラットフォームとして必要な機能を包括的に提供できます。 