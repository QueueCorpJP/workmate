# Workmate Chatbot QAT (Quality Assurance Testing) 完全ガイド

## 概要

このQATシステムは、Workmate Chatbotの品質保証を行うための包括的なテストスイートです。データベース構造に基づいて設計され、プロダクション環境へのリリース前に完璧なテストを実行できます。

## テストの種類と構成

### 1. 単体テスト (Unit Tests)
**場所**: `tests/unit/`
**対象**: 個別のモジュールと関数

- **認証モジュール** (`test_auth.py`)
  - ユーザー認証とトークン検証
  - 管理者権限チェック
  - 新規ユーザー登録処理

- **チャットモジュール** (`test_chat.py`)
  - メッセージ処理ロジック
  - AI応答生成
  - エラーハンドリング

- **データベースモジュール** (`test_database.py`)
  - CRUD操作
  - 使用量制限管理
  - 統計データ取得

### 2. 統合テスト (Integration Tests)
**場所**: `tests/integration/`
**対象**: システム間の連携

- **データベース統合** (`test_database_integration.py`)
  - 各テーブル間の関連性検証
  - トランザクション整合性
  - 並行処理テスト

### 3. APIテスト (API Tests)
**場所**: `tests/api/`
**対象**: REST APIエンドポイント

- **チャットAPI** (`test_chat_endpoints.py`)
  - メッセージ送受信
  - 履歴取得
  - 分析機能

- **認証API** (`test_auth_endpoints.py`)
  - ログイン/ログアウト
  - ユーザー登録
  - 権限管理

### 4. セキュリティテスト (Security Tests)
**場所**: `tests/security/`
**対象**: セキュリティ脆弱性

- **SQLインジェクション防止**
- **XSS攻撃防止**
- **CSRF保護**
- **認証バイパス検証**
- **データ分離確認**

### 5. パフォーマンステスト (Performance Tests)
**場所**: `tests/performance/`
**対象**: システムパフォーマンス

- **応答時間測定**
- **並行処理性能**
- **メモリ使用量**
- **スループット測定**

### 6. E2Eテスト (End-to-End Tests)
**場所**: `tests/e2e/`
**対象**: ユーザーワークフロー

- **完全な登録フロー**
- **文書アップロードとチャット**
- **管理者機能**
- **複数企業間のデータ分離**

## データベーステーブル対応表

以下のテーブルに対してテストが実装されています：

| テーブル名 | 主なテスト内容 |
|-----------|---------------|
| `companies` | 企業作成、取得、関連データ確認 |
| `users` | ユーザー登録、認証、権限管理 |
| `usage_limits` | 制限チェック、使用量更新 |
| `document_sources` | 文書アップロード、検索、有効性 |
| `chat_history` | チャット記録、分析、取得 |
| `plan_history` | プラン変更履歴追跡 |
| `applications` | 申請処理フロー |
| `monthly_token_usage` | 月次使用量集計 |
| `company_settings` | 企業設定管理 |

## 実行方法

### 1. 基本的な実行
```bash
# バックエンド全テスト実行
cd workmate/Chatbot-backend-main
./scripts/run_tests.sh

# フロントエンド全テスト実行
cd workmate/Chatbot-Frontend-main
npm test
```

### 2. 種類別実行
```bash
# 単体テストのみ
pytest tests/unit/ -v -m unit

# 統合テストのみ
pytest tests/integration/ -v -m integration

# APIテストのみ
pytest tests/api/ -v -m api

# セキュリティテストのみ
pytest tests/security/ -v -m security

# パフォーマンステストのみ
pytest tests/performance/ -v -m performance

# E2Eテストのみ
pytest tests/e2e/ -v -m e2e
```

### 3. カバレッジ付き実行
```bash
pytest tests/ --cov=modules --cov-report=html
```

## 環境設定

### 1. 依存関係インストール
```bash
# バックエンド
pip install -r requirements-test.txt

# フロントエンド
npm install
```

### 2. テスト環境設定
```bash
# 環境変数設定
cp .env.test .env

# テストデータベース起動
docker-compose -f docker-compose.test.yml up -d
```

## レポート確認

テスト実行後、以下の場所でレポートを確認できます：

- **HTMLカバレッジ**: `htmlcov/index.html`
- **テストレポート**: `reports/test_report.html`
- **JSONレポート**: `reports/test_report.json`
- **サマリー**: `reports/test_summary.txt`

## 品質基準

### 合格基準
- **コードカバレッジ**: 80%以上
- **単体テスト**: 100%成功
- **統合テスト**: 100%成功
- **APIテスト**: 100%成功
- **セキュリティテスト**: 100%成功
- **パフォーマンステスト**: 基準値内
- **E2Eテスト**: 主要フロー100%成功

### パフォーマンス基準
- **チャット応答時間**: 平均3秒以下
- **API応答時間**: 95%が1秒以下
- **並行処理**: 10リクエスト/秒以上
- **メモリ使用量**: 100MB増加以下

## トラブルシューティング

### よくある問題

1. **データベース接続エラー**
   ```bash
   docker-compose -f docker-compose.test.yml down
   docker-compose -f docker-compose.test.yml up -d
   ```

2. **依存関係エラー**
   ```bash
   pip install -r requirements-test.txt --upgrade
   ```

3. **ポート競合**
   ```bash
   # docker-compose.test.ymlのポート番号を変更
   ```

### テスト失敗時の対応

1. **単体テスト失敗**: モジュールロジックの確認
2. **統合テスト失敗**: データベース設定とスキーマ確認
3. **APIテスト失敗**: エンドポイント実装の確認
4. **セキュリティテスト失敗**: 脆弱性の修正
5. **パフォーマンステスト失敗**: コード最適化

## 継続的な品質管理

### 1. 定期実行
- **毎日**: 単体テストと統合テスト
- **毎週**: 全テストスイート実行
- **リリース前**: 完全QAT実行

### 2. メトリクス監視
- カバレッジトレンド
- テスト実行時間
- 失敗率の推移

### 3. 新機能追加時
1. 対応するテストケース追加
2. カバレッジ維持
3. パフォーマンス基準確認

## カスタマイズ

### テストデータの追加
`tests/factories/test_data_factory.py`でファクトリーを拡張

### 新しいテストケース追加
適切なディレクトリにテストファイルを作成し、マーカーを設定

### 設定変更
- `pytest.ini`: pytest設定
- `.env.test`: 環境変数
- `docker-compose.test.yml`: テストインフラ

## まとめ

このQATシステムにより、Workmate Chatbotの品質を網羅的に検証できます。データベース構造に基づいた完全なテストカバレッジにより、プロダクション環境でも安心してリリースできる品質を保証します。

定期的なテスト実行と継続的な改善により、高品質なシステムを維持しましょう。