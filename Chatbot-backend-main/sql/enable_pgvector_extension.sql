-- 🔧 pgvector拡張機能有効化スクリプト
-- PostgreSQLでベクトル検索を使用するために必要な拡張機能を有効化

-- pgvector拡張機能を有効化
CREATE EXTENSION IF NOT EXISTS vector;

-- 既存のembeddingカラムの型を確認・修正
DO $$
BEGIN
    -- chunksテーブルのembeddingカラムが存在するかチェック
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'chunks' 
        AND column_name = 'embedding'
    ) THEN
        -- 既存のembeddingカラムを削除して再作成（型の不整合を解決）
        ALTER TABLE chunks DROP COLUMN IF EXISTS embedding;
        ALTER TABLE chunks ADD COLUMN embedding VECTOR(768);
        
        RAISE NOTICE 'embeddingカラムを768次元のVECTOR型で再作成しました';
    ELSE
        -- embeddingカラムが存在しない場合は新規作成
        ALTER TABLE chunks ADD COLUMN embedding VECTOR(768);
        
        RAISE NOTICE '新しいembeddingカラムを768次元のVECTOR型で作成しました';
    END IF;
END $$;

-- ベクトル検索用のインデックスを作成
-- IVFFlat インデックス（高速検索用）
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_ivfflat 
ON chunks USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- HNSW インデックス（より高精度な検索用、PostgreSQL 14+）
-- CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw 
-- ON chunks USING hnsw (embedding vector_cosine_ops) 
-- WITH (m = 16, ef_construction = 64);

-- 会社IDとembeddingの複合インデックス
CREATE INDEX IF NOT EXISTS idx_chunks_company_embedding 
ON chunks(company_id) 
WHERE embedding IS NOT NULL;

-- コメント更新
COMMENT ON COLUMN chunks.embedding IS 'Vertex AI生成の768次元ベクトル（text-multilingual-embedding-002）- pgvector VECTOR型';

-- 統計情報更新
ANALYZE chunks;

-- 確認クエリ
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'chunks' 
AND indexname LIKE '%embedding%';

-- pgvector拡張機能の確認
SELECT 
    extname,
    extversion,
    extrelocatable
FROM pg_extension 
WHERE extname = 'vector';

-- embeddingカラムの型確認
SELECT 
    column_name, 
    data_type, 
    udt_name,
    column_default
FROM information_schema.columns 
WHERE table_name = 'chunks' 
AND column_name = 'embedding';