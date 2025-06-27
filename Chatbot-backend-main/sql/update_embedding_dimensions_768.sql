-- 🔧 Embedding次元数修正スクリプト (768次元)
-- text-multilingual-embedding-002モデルは768次元のベクトルを生成するため、
-- データベーススキーマを3072次元から768次元に更新

-- 既存のembeddingカラムを削除して再作成
ALTER TABLE chunks DROP COLUMN IF EXISTS embedding;

-- 新しい768次元のembeddingカラムを追加
ALTER TABLE chunks ADD COLUMN embedding VECTOR(768);

-- インデックスを再作成（pgvector拡張が必要）
-- CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- コメント更新
COMMENT ON COLUMN chunks.embedding IS 'Vertex AI生成の768次元ベクトル（text-multilingual-embedding-002）';

-- 統計情報更新
ANALYZE chunks;

-- 確認クエリ
SELECT 
    column_name, 
    data_type, 
    character_maximum_length,
    column_default
FROM information_schema.columns 
WHERE table_name = 'chunks' AND column_name = 'embedding';