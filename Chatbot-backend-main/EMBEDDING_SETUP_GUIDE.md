# 🔍 Gemini Embeddingを使用したベクトル検索システム セットアップガイド

このガイドでは、既存のRAGシステムをGemini Embeddingを使用したベクトル検索システムに切り替える手順を説明します。

## 📋 概要

- **従来**: BM25 + TF-IDFベースの検索
- **新システム**: Gemini Embedding APIを使用したベクトル類似検索
- **利点**: セマンティックな理解による高精度検索

## 🔧 セットアップ手順

### 1. 依存関係のインストール

```bash
cd Chatbot-backend-main
pip install -r requirements.txt
```

新しく追加された依存関係：
- `google-genai>=0.2.2`
- `pgvector>=0.2.0`

### 2. 環境変数の設定

`.env`ファイルを作成（または既存ファイルに追加）：

```env
# Google API設定
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# データベース設定
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
DB_PASSWORD=your_db_password

# エンベディング設定
EMBEDDING_MODEL=gemini-embedding-exp-03-07
EMBEDDING_DIM=1536
```

**重要**: `GOOGLE_API_KEY`または`GEMINI_API_KEY`が必要です。

### 3. データベーススキーマの更新

pgvector拡張とベクトル型の設定：

```bash
# SQLファイルを実行
psql $DATABASE_URL -f sql/update_embedding_schema.sql
```

または、直接SQL実行：

```sql
-- pgvector拡張を有効化
CREATE EXTENSION IF NOT EXISTS vector;

-- document_embeddingsテーブルのembeddingカラムをvector型に変更
ALTER TABLE document_embeddings
  ALTER COLUMN embedding TYPE vector(3072)
  USING embedding::vector;

-- HNSWインデックスを追加（高速ベクトル検索用）
CREATE INDEX IF NOT EXISTS document_embeddings_embedding_idx
  ON document_embeddings
  USING hnsw (embedding vector_cosine_ops);
```

**注意**: 実際のテーブル構造は以下の通りです：

```sql
CREATE TABLE public.document_embeddings (
  document_id text NOT NULL,  -- 主キー（チャンクの場合は "doc123_chunk_0" 形式）
  embedding vector(1536) NOT NULL,  -- MRL削減版（3072→1536次元）
  created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  snippet text,
  CONSTRAINT document_embeddings_pkey PRIMARY KEY (document_id)
);
```

### 4. エンベディングの生成・登録

既存のドキュメントからエンベディングを生成：

```bash
python embed_documents.py
```

このスクリプトは：
- `document_sources`テーブルから未処理のドキュメントを取得
- 長いドキュメントは8000文字ごとにチャンク分割
- Gemini Embedding APIでベクトルを生成
- `document_embeddings`テーブルに保存（チャンクIDで区別）

**チャンク化について**: 大きなドキュメントは自動的にチャンクに分割され、各チャンクは `original_doc_id_chunk_0`, `original_doc_id_chunk_1` のような一意なIDで保存されます。

### 5. システムの動作確認

#### ベクトル検索の動作テスト

```python
from modules.vector_search import get_vector_search_instance

# ベクトル検索インスタンスを取得
vector_search = get_vector_search_instance()

if vector_search:
    # テスト検索を実行
    results = vector_search.vector_similarity_search(
        query="クラウドコストを削減する方法",
        company_id="your_company_id",
        limit=5
    )
    
    for result in results:
        print(f"類似度: {result['similarity_score']:.3f}")
        print(f"ドキュメント: {result['document_name']}")
        print(f"チャンクID: {result['chunk_id']}")
        print(f"元ドキュメントID: {result['document_id']}")
        print(f"スニペット: {result['snippet']}")
        print("---")
```

#### チャット機能での統合テスト

通常のチャット機能を使用して、ベクトル検索が動作することを確認してください。ログに以下のメッセージが表示されれば正常に動作しています：

```
✅ ベクトル検索システムが利用可能です
🔍 ベクトル検索を試行中...
✅ ベクトル検索成功: XXXX文字の結果を取得
```

## 🔄 システム動作

### 検索の優先順位

1. **ベクトル検索** (最優先)
   - Gemini Embeddingによる意味的類似検索
   - company_idが指定されている場合のみ実行
   - チャンクレベルでの高精度検索

2. **従来のRAG検索** (フォールバック)
   - BM25 + TF-IDFベースの検索
   - ベクトル検索が利用できない場合や結果が不十分な場合

### 検索フロー

```
ユーザーの質問
      ↓
ベクトル検索利用可能？
  ├─ Yes → Gemini Embeddingで検索
  │         ├─ チャンクレベルで類似度計算
  │         ├─ 結果あり → 関連スニペットを組み合わせて回答生成
  │         └─ 結果なし → 従来RAG検索
  └─ No → 従来RAG検索
```

### チャンク化システム

- **自動分割**: 8000文字（約2000トークン）ごとに分割
- **一意ID**: `original_doc_id_chunk_0`, `original_doc_id_chunk_1`...
- **元情報保持**: 元のドキュメント情報は自動的に関連付け
- **スニペット保存**: 各チャンクの最初の200文字をスニペットとして保存

### 次元削減（MRL）システム

- **元の次元**: Gemini Embeddingは3072次元を生成
- **削減後**: 1536次元に削減（上位1536次元のみ使用）
- **理由**: データベースの制限とパフォーマンス向上のため
- **精度**: MRL（Matryoshka Representation Learning）により、削減後も高い検索精度を維持

## 🛠️ トラブルシューティング

### よくある問題と解決方法

#### 1. ベクトル検索が利用できない

**エラー**: `⚠️ ベクトル検索システムの設定が不完全です`

**解決方法**:
- 環境変数が正しく設定されているか確認
- Google API キーが有効か確認
- Supabase接続情報が正しいか確認

#### 2. pgvector拡張が利用できない

**エラー**: `CREATE EXTENSION IF NOT EXISTS vector`でエラー

**解決方法**:
- Supabaseでpgvector拡張が有効になっているか確認
- PostgreSQLのバージョンが11以上であることを確認

#### 3. エンベディング生成エラー

**エラー**: `❌ エンベディング生成エラー`

**解決方法**:
- Gemini API キーが有効で権限があることを確認
- ネットワーク接続を確認
- API制限に達していないか確認

#### 4. チャンク検索で結果が見つからない

**問題**: チャンク化されたドキュメントが検索で見つからない

**解決方法**:
- `embed_documents.py`を実行してエンベディングが正しく生成されているか確認
- データベースで `document_embeddings` テーブルの内容を確認:
  ```sql
  SELECT document_id, LENGTH(snippet) as snippet_length 
  FROM document_embeddings 
  WHERE document_id LIKE '%_chunk_%' 
  LIMIT 10;
  ```

#### 5. JOIN エラー

**エラー**: `LEFT JOIN` でドキュメント情報が取得できない

**解決方法**:
- チャンクIDから元のドキュメントIDが正しく抽出されているか確認
- `SPLIT_PART` 関数がSupabaseで利用可能であることを確認

### デバッグモード

詳細なログを確認するには：

```bash
# 環境変数でデバッグモードを有効化
export RAG_DEBUG=true
```

## 📊 パフォーマンス最適化

### 1. インデックスの調整

必要に応じてHNSWインデックスのパラメータを調整：

```sql
-- インデックスパラメータの調整例
ALTER INDEX document_embeddings_embedding_idx 
SET (m = 16, ef_construction = 64);
```

### 2. チャンクサイズの最適化

`embed_documents.py`のチャンクサイズを調整：

```python
# デフォルト: 8000文字（約2000トークン）
def chunks(text, chunk_size=8000):
```

### 3. 検索結果数の調整

ベクトル検索の結果数を調整：

```python
# modules/vector_search.py で調整
def get_document_content_by_similarity(self, query: str, company_id: str = None, max_results: int = 10):
```

## 🔄 定期メンテナンス

### 新しいドキュメントの処理

新しいドキュメントが追加された際は、定期的にエンベディング生成を実行：

```bash
# 定期実行（例：毎日）
python embed_documents.py
```

### パフォーマンス監視

- ベクトル検索の使用率
- 平均応答時間
- チャンク数とエラー率
- エンベディング生成の成功率

の監視を推奨します。

### データベースメンテナンス

```sql
-- 埋め込み統計の確認
SELECT 
    COUNT(*) as total_embeddings,
    COUNT(*) FILTER (WHERE document_id LIKE '%_chunk_%') as chunk_embeddings,
    COUNT(*) FILTER (WHERE document_id NOT LIKE '%_chunk_%') as original_embeddings
FROM document_embeddings;

-- 孤立したエンベディングの確認
SELECT de.document_id 
FROM document_embeddings de
LEFT JOIN document_sources ds ON ds.id = CASE 
    WHEN de.document_id LIKE '%_chunk_%' THEN 
        SPLIT_PART(de.document_id, '_chunk_', 1)
    ELSE de.document_id
END
WHERE ds.id IS NULL;
```

## 🎯 次のステップ

1. **運用監視**: ベクトル検索の精度と性能を監視
2. **チューニング**: 必要に応じてパラメータを調整
3. **スケーリング**: 大量データでの性能最適化
4. **機能拡張**: より高度な検索機能の追加（ハイブリッド検索の改良等）

---

## 🆘 サポート

問題が発生した場合は、以下を確認してください：

1. ログファイルの確認
2. 環境変数の設定確認  
3. データベース接続の確認
4. API制限の確認
5. チャンク化の動作確認

それでも解決しない場合は、開発チームまでお問い合わせください。 