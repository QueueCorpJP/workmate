-- 🗑️ カスケード削除制約の確認・設定スクリプト
-- ドキュメント削除時にchunksテーブルの関連レコードも自動削除されるように設定

-- 1. 現在の外部キー制約を確認
SELECT 
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
    JOIN information_schema.referential_constraints AS rc
      ON tc.constraint_name = rc.constraint_name
      AND tc.table_schema = rc.constraint_schema
WHERE 
    tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_name = 'chunks'
    AND kcu.column_name = 'doc_id';

-- 2. 既存の制約を削除（存在する場合）
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_chunks_doc_id' 
        AND table_name = 'chunks'
    ) THEN
        ALTER TABLE chunks DROP CONSTRAINT fk_chunks_doc_id;
        RAISE NOTICE '既存の外部キー制約 fk_chunks_doc_id を削除しました';
    END IF;
END $$;

-- 3. ON DELETE CASCADE制約を追加
ALTER TABLE chunks 
ADD CONSTRAINT fk_chunks_doc_id 
FOREIGN KEY (doc_id) 
REFERENCES document_sources(id) 
ON DELETE CASCADE;

-- 4. 制約が正しく設定されたかを確認
SELECT 
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
    JOIN information_schema.referential_constraints AS rc
      ON tc.constraint_name = rc.constraint_name
      AND tc.table_schema = rc.constraint_schema
WHERE 
    tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_name = 'chunks'
    AND kcu.column_name = 'doc_id';

-- 5. インデックスの確認・作成
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);

-- 6. テスト用のコメント
COMMENT ON CONSTRAINT fk_chunks_doc_id ON chunks IS 
'ドキュメント削除時にchunksも自動削除するカスケード制約';

-- 7. 統計情報の更新
ANALYZE chunks;
ANALYZE document_sources;

-- 完了メッセージ
SELECT 'カスケード削除制約の設定が完了しました。document_sourcesのレコードを削除すると、関連するchunksも自動的に削除されます。' AS status;