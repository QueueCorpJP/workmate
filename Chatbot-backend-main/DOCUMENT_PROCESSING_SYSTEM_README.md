# 📤 ファイルアップロード・ドキュメント処理システム

完全なRAG対応ドキュメント処理パイプライン

## 🎯 システム概要

このシステムは、ファイルアップロードから高度なRAG（Retrieval-Augmented Generation）検索まで、完全なドキュメント処理パイプラインを提供します。

### 🔄 処理フロー

```
1️⃣ ファイルアップロード（PDF / XLS など）
     ↓
2️⃣ document_sources テーブルに メタ情報保存
     ↓
3️⃣ テキスト抽出・チャンク分割（300〜500 token）
     ↓
4️⃣ Gemini Flash embedding生成（768次元）
     ↓
5️⃣ chunks テーブルに保存（RAG用）
```

## 📁 ファイル構成

### 🗃️ データベーススキーマ
- [`sql/chunks_table_schema.sql`](sql/chunks_table_schema.sql) - chunksテーブル定義
- [`Workmate_Database_Schema_Guide.md`](../Workmate_Database_Schema_Guide.md) - 完全なDB設計ガイド

### 🔧 コアモジュール
- [`modules/document_processor.py`](modules/document_processor.py) - メインドキュメント処理エンジン
- [`modules/upload_api.py`](modules/upload_api.py) - ファイルアップロードAPI
- [`modules/resource.py`](modules/resource.py) - リソース管理（既存）

### 🧠 Embedding処理
- [`generate_embeddings_enhanced.py`](generate_embeddings_enhanced.py) - 強化版embedding生成
- [`embed_documents.py`](embed_documents.py) - 既存embedding処理

### 🚀 セットアップ
- [`setup_document_system.py`](setup_document_system.py) - システム初期化スクリプト

## 🛠️ セットアップ手順

### 1. 環境変数設定

`.env`ファイルに以下を設定：

```bash
# Gemini API
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_API_KEY=your_gemini_api_key  # 代替

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
DB_PASSWORD=your_db_password

# Database (オプション)
DATABASE_URL=postgresql://user:pass@host:port/db
EMBEDDING_MODEL=gemini-2.5-flash-exp
```

### 2. 依存関係インストール

```bash
pip install -r requirements.txt

# 追加パッケージ
pip install tiktoken python-docx PyPDF2 pandas openpyxl
```

### 3. システム初期化

```bash
# データベーススキーマ作成・データ移行
python setup_document_system.py
```

### 4. Embedding生成

```bash
# 全チャンクのembedding生成
python generate_embeddings_enhanced.py

# 制限付き実行（テスト用）
python generate_embeddings_enhanced.py 100
```

## 📊 データベース設計

### 🏢 document_sources テーブル（メタデータ）

```sql
CREATE TABLE document_sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,              -- ファイル名
    type TEXT NOT NULL,              -- ファイル種別
    page_count INTEGER,              -- ページ数
    uploaded_by TEXT NOT NULL,       -- アップロード者
    company_id TEXT NOT NULL,        -- 所属企業
    uploaded_at TIMESTAMP NOT NULL,  -- アップロード日時
    active BOOLEAN DEFAULT true,     -- 有効フラグ
    special TEXT                     -- 特殊属性
);
```

### 🧩 chunks テーブル（RAG用）

```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id TEXT NOT NULL,            -- 親ドキュメントID
    chunk_index INTEGER NOT NULL,    -- チャンク順序
    content TEXT NOT NULL,           -- チャンク本文（300-500トークン）
    embedding VECTOR(768),           -- 768次元ベクトル
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    company_id TEXT,                 -- 所属企業ID
    active BOOLEAN DEFAULT true,     -- 有効フラグ
    special TEXT,                    -- 特殊属性
    
    FOREIGN KEY (doc_id) REFERENCES document_sources(id) ON DELETE CASCADE
);
```

## 🔌 API エンドポイント

### 📤 ファイルアップロード

```http
POST /api/v1/upload-document
Content-Type: multipart/form-data

{
  "file": "document.pdf"
}
```

**レスポンス:**
```json
{
  "success": true,
  "message": "✅ document.pdf のアップロード・処理が完了しました",
  "document": {
    "id": "uuid",
    "filename": "document.pdf",
    "file_size_mb": 2.5,
    "text_length": 15000,
    "total_chunks": 30,
    "saved_chunks": 30
  },
  "processing_stats": {
    "chunks_created": 30,
    "chunks_saved": 30,
    "success_rate": "100.0%"
  }
}
```

### 📋 ドキュメント一覧

```http
GET /api/v1/documents
```

**レスポンス:**
```json
{
  "success": true,
  "documents": [
    {
      "id": "uuid",
      "name": "document.pdf",
      "type": "PDF",
      "page_count": 10,
      "uploaded_at": "2025-01-26T15:30:00Z",
      "active": true,
      "chunks": {
        "total_chunks": 30,
        "active_chunks": 30,
        "inactive_chunks": 0
      }
    }
  ],
  "total_count": 1
}
```

### 🗑️ ドキュメント削除

```http
DELETE /api/v1/documents/{doc_id}
```

### 🔄 ドキュメント有効/無効切り替え

```http
POST /api/v1/documents/{doc_id}/toggle
```

## 🧠 DocumentProcessor クラス

### 主要機能

1. **ファイル形式対応**
   - PDF, Excel, Word, CSV, テキスト, 画像
   - 自動形式検出・適切な抽出方法選択

2. **インテリジェントチャンク分割**
   - 300-500トークンの最適サイズ
   - 意味単位での分割（段落・文単位）
   - 日本語対応トークンカウント

3. **Gemini Flash Embedding**
   - 768次元高精度ベクトル
   - バッチ処理・エラー回復
   - API制限対応

### 使用例

```python
from modules.document_processor import document_processor

# ファイル処理
result = await document_processor.process_uploaded_file(
    file=uploaded_file,
    user_id="user123",
    company_id="company456"
)

print(f"処理完了: {result['total_chunks']}チャンク生成")
```

## 🔍 RAG検索システム

### チャンク検索

```python
from modules.resource import get_active_resources_content_by_ids

# アクティブなリソースのコンテンツ取得
content = await get_active_resources_content_by_ids(
    resource_ids=["doc1", "doc2"],
    db=db_connection
)
```

### Embedding検索（実装例）

```sql
-- 類似チャンク検索（pgvector使用）
SELECT 
    c.content,
    c.doc_id,
    ds.name as document_name,
    1 - (c.embedding <=> %s) as similarity
FROM chunks c
JOIN document_sources ds ON c.doc_id = ds.id
WHERE c.active = true
  AND c.company_id = %s
ORDER BY c.embedding <=> %s
LIMIT 5;
```

## 📈 パフォーマンス最適化

### インデックス戦略

```sql
-- 基本インデックス
CREATE INDEX idx_chunks_doc_id ON chunks(doc_id);
CREATE INDEX idx_chunks_company_id ON chunks(company_id);
CREATE INDEX idx_chunks_active ON chunks(active);

-- ベクトル検索インデックス（pgvector）
CREATE INDEX idx_chunks_embedding 
ON chunks USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

### バッチ処理設定

```python
# generate_embeddings_enhanced.py
BATCH_SIZE = 10          # 同時処理チャンク数
MAX_RETRIES = 3          # 最大リトライ回数
RETRY_DELAY = 2          # リトライ間隔（秒）
```

## 🔧 運用・管理

### 統計情報取得

```sql
-- システム統計
SELECT 
    COUNT(*) as total_chunks,
    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as chunks_with_embedding,
    COUNT(CASE WHEN active = true THEN 1 END) as active_chunks,
    COUNT(DISTINCT doc_id) as unique_documents,
    COUNT(DISTINCT company_id) as companies
FROM chunks;
```

### メンテナンス

```bash
# embedding再生成
python generate_embeddings_enhanced.py

# システム統計確認
python -c "
from setup_document_system import DocumentSystemSetup
import asyncio
setup = DocumentSystemSetup()
asyncio.run(setup._verify_system())
"
```

## 🚨 トラブルシューティング

### よくある問題

1. **pgvector拡張機能エラー**
   ```
   解決: Supabase管理画面でpgvector拡張を有効化
   ```

2. **embedding生成失敗**
   ```bash
   # API制限確認
   python generate_embeddings_enhanced.py 1
   ```

3. **チャンク分割問題**
   ```python
   # デバッグモード
   document_processor.tokenizer = None  # フォールバック使用
   ```

### ログ確認

```bash
# セットアップログ
tail -f setup_document_system.log

# embedding生成ログ
tail -f embedding_generation.log
```

## 🔮 今後の拡張

### 予定機能

1. **高度なチャンク分割**
   - セマンティック分割
   - 文書構造認識

2. **マルチモーダル対応**
   - 画像・動画コンテンツ
   - OCR精度向上

3. **検索精度向上**
   - ハイブリッド検索（キーワード + ベクトル）
   - リランキング機能

4. **管理機能強化**
   - リアルタイム統計ダッシュボード
   - 自動最適化

## 📞 サポート

問題が発生した場合は、以下の情報と共にお問い合わせください：

1. エラーメッセージ
2. ログファイル（`setup_document_system.log`, `embedding_generation.log`）
3. 環境情報（Python版、依存関係）
4. 処理対象ファイル情報

---

**🎉 完全なRAG対応ドキュメント処理システムをお楽しみください！**