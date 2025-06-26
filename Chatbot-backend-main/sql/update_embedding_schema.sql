-- エンベディングシステム用のスキーマ更新
-- pgvector拡張がまだなら有効にする
CREATE EXTENSION IF NOT EXISTS vector;

-- document_embeddings.embeddingをvector型に変更（1536次元のMRL削減版Gemini Embedding用）
ALTER TABLE document_embeddings
  ALTER COLUMN embedding TYPE vector(1536)
  USING embedding::vector;

-- HNSWインデックスを追加（コサイン類似度用）
CREATE INDEX IF NOT EXISTS document_embeddings_embedding_idx
  ON document_embeddings
  USING hnsw (embedding vector_cosine_ops);

-- インデックスのパフォーマンス設定（1536次元に最適化、必要に応じて調整）
-- ALTER INDEX document_embeddings_embedding_idx SET (m = 16, ef_construction = 64);

-- 既存のembeddingデータが存在する場合はリセット（必要に応じて）
-- DELETE FROM document_embeddings WHERE embedding IS NULL; 