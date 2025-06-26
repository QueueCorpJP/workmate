-- 🔧 Embedding次元数修正スクリプト
-- gemini-embedding-exp-03-07モデルは3072次元のベクトルを生成するため、
-- データベーススキーマを768次元から3072次元に更新

-- 既存のembeddingカラムを削除して再作成
ALTER TABLE chunks DROP COLUMN IF EXISTS embedding;

-- 新しい3072次元のembeddingカラムを追加
ALTER TABLE chunks ADD COLUMN embedding VECTOR(3072);

-- インデックスを再作成（pgvector拡張が必要）
-- CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- コメント更新
COMMENT ON COLUMN chunks.embedding IS 'Gemini Flash生成の3072次元ベクトル（gemini-embedding-exp-03-07）';

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