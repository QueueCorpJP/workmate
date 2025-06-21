-- chat_historyテーブルに新しい料金体系用のカラムを追加

-- プロンプト参照数カラムを追加
ALTER TABLE chat_history 
ADD COLUMN IF NOT EXISTS prompt_references INTEGER DEFAULT 0;

-- 基本コスト（トークンベース）カラムを追加
ALTER TABLE chat_history 
ADD COLUMN IF NOT EXISTS base_cost_usd DECIMAL(10,6) DEFAULT 0.000000;

-- プロンプト参照コストカラムを追加
ALTER TABLE chat_history 
ADD COLUMN IF NOT EXISTS prompt_cost_usd DECIMAL(10,6) DEFAULT 0.000000;

-- 既存データの確認用クエリ（実行後に確認してください）
-- SELECT COUNT(*) as total_records, 
--        COUNT(prompt_references) as with_prompt_refs,
--        COUNT(base_cost_usd) as with_base_cost,
--        COUNT(prompt_cost_usd) as with_prompt_cost
-- FROM chat_history; 