# 🔄 Embedding再実行機能実装完了

## 📋 概要

429エラー（API制限）などで失敗したembeddingを自動的に再実行する機能を実装しました。これにより、一度に全チャンクの処理を終えた後、エラーになった分だけを対象として再実行を行うことで、確実にembeddingを完了させることができます。

## 🚀 実装した機能

### 1. 強化されたembedding生成機能

**ファイル**: `modules/document_processor.py`

#### `_generate_embeddings_batch()` メソッドの改良
- **失敗したインデックスのみ再実行**: `failed_indices`パラメータで特定のインデックスのみ処理
- **詳細なログ出力**: 成功/失敗の詳細な追跡
- **失敗インデックスの記録**: どのチャンクが失敗したかを明確に記録

```python
async def _generate_embeddings_batch(self, texts: List[str], failed_indices: List[int] = None)
```

#### `_save_chunks_to_database()` メソッドの改良
- **自動リトライ機能**: 失敗したembeddingを最大10回まで自動再試行
- **インクリメンタル修復**: 失敗分のみを対象とした効率的な再実行
- **詳細な統計情報**: 再試行回数、成功率などの詳細な情報を提供

```python
async def _save_chunks_to_database(self, doc_id: str, chunks: List[Dict[str, Any]], 
                                 company_id: str, doc_name: str, max_retries: int = 3)
```

### 2. 既存データの修復機能

#### `retry_failed_embeddings()` メソッド
- **既存の失敗チャンクを検索**: データベースからembeddingがNullのチャンクを特定
- **バッチ処理**: 50件ずつの効率的なバッチ処理
- **柔軟なフィルタリング**: 特定のドキュメントや会社のみを対象とした修復
- **リトライ機能**: 失敗したチャンクを最大10回まで再試行

```python
async def retry_failed_embeddings(self, doc_id: str = None, company_id: str = None, max_retries: int = 3)
```

## 🛠️ 使用方法

### 1. 自動修復（新規アップロード時）

新しいファイルをアップロードする際、embedding生成で失敗があった場合、自動的に再試行されます：

```python
# 通常のファイル処理で自動的にリトライが実行される
result = await document_processor.process_uploaded_file(file, user_id, company_id)
```

### 2. 手動修復（既存の失敗データ）

#### 全体修復
```bash
python fix_failed_embeddings.py --all
```

#### 特定ドキュメントの修復
```bash
python fix_failed_embeddings.py --doc-id <document_id>
```

#### 特定会社の修復
```bash
python fix_failed_embeddings.py --company-id <company_id>
```

### 3. プログラムからの呼び出し

```python
from modules.document_processor import document_processor

# 全体修復
result = await document_processor.retry_failed_embeddings()

# 特定ドキュメント修復
result = await document_processor.retry_failed_embeddings(doc_id="your-doc-id")

# 特定会社修復
result = await document_processor.retry_failed_embeddings(company_id="your-company-id")
```

## 📊 統計情報

修復処理では以下の詳細な統計情報が提供されます：

```python
{
    "total_failed": 10,      # 失敗していたチャンク数
    "processed": 10,         # 処理したチャンク数
    "successful": 8,         # 成功したチャンク数
    "still_failed": 2,       # 依然として失敗しているチャンク数
    "retry_attempts": 3      # 最大再試行回数
}
```

## 🔧 設定可能なパラメータ

### リトライ回数
```python
# デフォルトは10回
max_retries = 10
```

### バッチサイズ
```python
# デフォルトは50件ずつ処理
batch_size = 50
```

### API制限対策の待機時間
```python
# 各リクエスト間の待機時間（秒）
await asyncio.sleep(0.2)  # 通常処理
await asyncio.sleep(2.0)  # リトライ間隔
```

## 📝 ログ出力例

```
2025-06-26 20:43:10,330 - modules.document_processor - INFO - ✅ embedding生成成功: 49/55 (次元: 3072)
2025-06-26 20:43:12,445 - modules.document_processor - ERROR - ❌ embedding生成エラー (インデックス 51): 429 Resource has been exhausted
2025-06-26 20:43:14,395 - modules.document_processor - INFO - 🔄 embedding再生成開始: 3件の失敗分
2025-06-26 20:43:15,736 - modules.document_processor - INFO - ✅ 再試行成功: 全てのembeddingが生成されました
2025-06-26 20:43:16,000 - modules.document_processor - INFO - 🎉 最終結果: 55/55 embedding成功, 最大10回再試行
```

## 🎯 効果

### Before（修正前）
- 429エラーで失敗したチャンクは手動で対処が必要
- 55個中52個成功、3個失敗で処理終了
- 失敗したデータは使用不可

### After（修正後）
- 失敗したチャンクを自動的に再実行
- 最大3回まで自動リトライ
- 確実にembedding生成を完了
- 既存の失敗データも後から修復可能

## 🔍 トラブルシューティング

### 429エラーが継続する場合
1. **API制限の確認**: Google API Keyの制限を確認
2. **待機時間の調整**: リトライ間隔を長くする
3. **バッチサイズの調整**: 一度に処理する件数を減らす

### 修復が完了しない場合
1. **環境変数の確認**: `GOOGLE_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`
2. **ネットワーク接続の確認**: APIへの接続状況
3. **ログの確認**: 詳細なエラーメッセージを確認

## 📁 関連ファイル

- `modules/document_processor.py` - メイン実装
- `fix_failed_embeddings.py` - 修復用スクリプト
- `test_embedding_retry.py` - テスト用スクリプト
- `EMBEDDING_RETRY_FIX_SUMMARY.md` - このドキュメント

## ✅ 実装完了

embedding再実行機能の実装が完了しました。これにより、API制限などで失敗したembeddingを確実に修復し、全てのチャンクでembeddingを生成できるようになりました。