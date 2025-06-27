-- 🧩 chunksテーブル作成スクリプト
-- ファイル全体のテキストを小さなチャンク（300〜500トークン）に分割し、RAG検索用に保存

-- chunksテーブルの作成
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- チャンク一意ID（UUID）
    doc_id TEXT NOT NULL,                           -- 紐づく document_sources.id（親）
    chunk_index INTEGER NOT NULL,                   -- チャンクの順序（0, 1, 2, …）
    content TEXT NOT NULL,                          -- チャンク本文（300-500トークン）
    embedding VECTOR(768),                          -- チャンクのベクトル（768次元）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 登録日時
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 更新日時
    company_id TEXT,                                -- 所属企業ID
    
    -- 外部キー制約
    CONSTRAINT fk_chunks_doc_id FOREIGN KEY (doc_id) REFERENCES document_sources(id) ON DELETE CASCADE,
    CONSTRAINT fk_chunks_company_id FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- インデックスの作成（検索パフォーマンス向上）
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_chunks_company_id ON chunks(company_id);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_chunk_index ON chunks(doc_id, chunk_index);

-- ベクトル検索用のインデックス（pgvector拡張が必要）
-- CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- コメント追加
COMMENT ON TABLE chunks IS 'ドキュメントのチャンク分割データ（RAG検索用）';
COMMENT ON COLUMN chunks.id IS 'チャンク一意ID（UUID）';
COMMENT ON COLUMN chunks.doc_id IS '親ドキュメントID（document_sources.id）';
COMMENT ON COLUMN chunks.chunk_index IS 'ドキュメント内でのチャンク順序';
COMMENT ON COLUMN chunks.content IS 'チャンクのテキスト内容（300-500トークン）';
COMMENT ON COLUMN chunks.embedding IS 'Vertex AI生成の768次元ベクトル（text-multilingual-embedding-002）';
COMMENT ON COLUMN chunks.company_id IS '所属企業ID';

-- document_sourcesテーブルからcontentカラムを削除（最適化）
-- 注意: 本番環境では事前にデータ移行が必要
-- ALTER TABLE document_sources DROP COLUMN IF EXISTS content;
-- ALTER TABLE document_sources DROP COLUMN IF EXISTS embedding;

-- 統計情報更新
ANALYZE chunks;