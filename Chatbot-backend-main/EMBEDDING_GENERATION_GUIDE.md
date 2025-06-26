# 🧠 Embedding生成ガイド

## 概要

ファイルアップロード後、チャンクの分割は完了していますが、embedding（ベクトル化）は別途実行する必要があります。このガイドでは、Gemini Flash Embedding API（`gemini-embedding-exp-03-07`モデル）を使用してembeddingを生成する方法を説明します。

## 🔧 設定

### 環境変数

`.env`ファイルに以下の設定が必要です：

```env
# Google API Key
GOOGLE_API_KEY=your_google_api_key
GEMINI_API_KEY=your_google_api_key

# Embedding Model
EMBEDDING_MODEL=gemini-embedding-exp-03-07

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
DB_PASSWORD=your_db_password
```

## 🚀 Embedding生成の実行

### 方法1: 統合スクリプトを使用（推奨）

```bash
# 全チャンクのembeddingを生成
python run_embedding_generation.py --enhanced

# 100チャンクまでのembeddingを生成（テスト用）
python run_embedding_generation.py --enhanced 100

# シンプル版を使用
python run_embedding_generation.py --simple

# ヘルプを表示
python run_embedding_generation.py --help
```

### 方法2: 個別スクリプトを使用

#### 強化版（推奨）
```bash
# 全チャンク処理
python generate_embeddings_enhanced.py

# 制限数指定
python generate_embeddings_enhanced.py 100
```

#### シンプル版
```bash
python embed_documents.py
```

## 📊 処理の流れ

1. **チャンク検索**: `chunks`テーブルから`embedding IS NULL`のチャンクを検索
2. **Embedding生成**: Gemini Flash Embedding API（`gemini-embedding-exp-03-07`）でベクトル化
3. **データベース更新**: 生成されたembedding（768次元）を`chunks.embedding`カラムに保存

## 🔍 処理状況の確認

### データベースクエリで確認

```sql
-- embedding未生成のチャンク数
SELECT COUNT(*) as pending_chunks 
FROM chunks 
WHERE active = true AND embedding IS NULL;

-- embedding生成済みのチャンク数
SELECT COUNT(*) as completed_chunks 
FROM chunks 
WHERE active = true AND embedding IS NOT NULL;

-- 会社別の処理状況
SELECT 
    company_id,
    COUNT(*) as total_chunks,
    COUNT(embedding) as completed_chunks,
    COUNT(*) - COUNT(embedding) as pending_chunks
FROM chunks 
WHERE active = true 
GROUP BY company_id;
```

## ⚡ パフォーマンス最適化

### 強化版の特徴

- **バッチ処理**: 10チャンクずつ並行処理
- **リトライ機能**: 失敗時に最大3回リトライ
- **進捗表示**: リアルタイムで処理状況を表示
- **統計レポート**: 処理完了後に詳細な統計を表示
- **エラー回復**: 一部のチャンクが失敗しても処理を継続

### 処理速度の目安

- **小規模**: 100チャンク → 約2-3分
- **中規模**: 1,000チャンク → 約20-30分
- **大規模**: 10,000チャンク → 約3-5時間

## 🛠️ トラブルシューティング

### よくある問題

#### 1. API制限エラー
```
Error: Quota exceeded
```
**解決策**: 処理を一時停止し、時間をおいて再実行

#### 2. データベース接続エラー
```
Error: connection to server failed
```
**解決策**: 
- Supabase接続情報を確認
- DB_PASSWORDが正しく設定されているか確認

#### 3. 空のコンテンツエラー
```
Warning: 空のテキスト
```
**解決策**: 正常な動作です。空のチャンクはスキップされます

### ログファイル

強化版では`embedding_generation.log`にログが保存されます：

```bash
# ログを確認
tail -f embedding_generation.log

# エラーのみ表示
grep "ERROR" embedding_generation.log
```

## 📈 モニタリング

### 処理中の監視

```bash
# リアルタイムでログを監視
tail -f embedding_generation.log

# 処理状況をデータベースで確認
psql -c "SELECT COUNT(*) FROM chunks WHERE embedding IS NULL;"
```

### 完了後の確認

```sql
-- 最終統計
SELECT 
    COUNT(*) as total_chunks,
    COUNT(embedding) as with_embedding,
    COUNT(*) - COUNT(embedding) as without_embedding,
    ROUND(COUNT(embedding) * 100.0 / COUNT(*), 2) as completion_rate
FROM chunks 
WHERE active = true;
```

## 🔄 定期実行の設定

新しいファイルが定期的にアップロードされる場合、cronジョブで自動実行できます：

```bash
# crontabに追加（毎時実行）
0 * * * * cd /path/to/workmate/Chatbot-backend-main && python run_embedding_generation.py --enhanced >> /var/log/embedding_cron.log 2>&1
```

## 📝 注意事項

1. **API制限**: Google APIの制限に注意し、大量処理時は適切な間隔を設ける
2. **データベース負荷**: 大量のチャンク処理時はデータベースの負荷に注意
3. **バックアップ**: 重要なデータは事前にバックアップを取る
4. **モデル変更**: embedding モデルを変更する場合は既存のembeddingとの互換性に注意

## 🎯 次のステップ

Embedding生成完了後：

1. **RAG検索のテスト**: 生成されたembeddingでベクトル検索をテスト
2. **パフォーマンス測定**: 検索速度と精度を測定
3. **インデックス最適化**: 必要に応じてベクトルインデックスを作成

```sql
-- ベクトル検索用インデックス作成（必要に応じて）
CREATE INDEX IF NOT EXISTS idx_chunks_embedding 
ON chunks USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);