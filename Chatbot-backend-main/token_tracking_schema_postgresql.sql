-- PostgreSQL用トークン使用量追跡のためのデータベーススキーマ拡張
-- 実行日: 2025年1月

-- 1. chat_historyテーブルにトークン使用量関連のカラムを追加
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS input_tokens INTEGER DEFAULT 0;
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS output_tokens INTEGER DEFAULT 0;
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS total_tokens INTEGER DEFAULT 0;
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS model_name VARCHAR(50) DEFAULT 'gpt-4o-mini';
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS cost_usd NUMERIC(10,6) DEFAULT 0.000000;
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS company_id VARCHAR(255);

-- 2. 月次トークン使用量集計テーブルを作成
CREATE TABLE IF NOT EXISTS monthly_token_usage (
    id VARCHAR(255) PRIMARY KEY,
    company_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    year_month VARCHAR(7) NOT NULL, -- 'YYYY-MM' format
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd NUMERIC(10,6) DEFAULT 0.000000,
    conversation_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, user_id, year_month)
);

-- 3. 会社設定テーブルにトークン設定を追加
CREATE TABLE IF NOT EXISTS company_settings (
    company_id VARCHAR(255) PRIMARY KEY,
    monthly_token_limit INTEGER DEFAULT 25000000, -- 25M tokens
    warning_threshold_percentage INTEGER DEFAULT 80, -- 80%で警告
    critical_threshold_percentage INTEGER DEFAULT 95, -- 95%で重要警告
    pricing_tier VARCHAR(20) DEFAULT 'basic', -- basic, pro, enterprise
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 現在の月の集計用ビュー
CREATE OR REPLACE VIEW current_month_usage AS
SELECT 
    company_id,
    user_id,
    SUM(total_tokens) as current_month_tokens,
    COUNT(*) as current_month_conversations,
    SUM(cost_usd) as current_month_cost_usd
FROM chat_history 
WHERE TO_CHAR(timestamp::timestamp, 'YYYY-MM') = TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')
GROUP BY company_id, user_id;

-- 5. 会社全体の今月使用量ビュー
CREATE OR REPLACE VIEW company_current_month_summary AS
SELECT 
    c.id as company_id,
    c.name as company_name,
    COALESCE(SUM(cmu.current_month_tokens), 0) as total_current_month_tokens,
    COALESCE(SUM(cmu.current_month_conversations), 0) as total_current_month_conversations,
    COALESCE(SUM(cmu.current_month_cost_usd), 0) as total_current_month_cost_usd,
    COUNT(DISTINCT cmu.user_id) as active_users_this_month
FROM companies c
LEFT JOIN current_month_usage cmu ON c.id = cmu.company_id
GROUP BY c.id, c.name;

-- 6. インデックスの作成（パフォーマンス最適化）
CREATE INDEX IF NOT EXISTS idx_chat_history_company_timestamp ON chat_history(company_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_timestamp ON chat_history(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_chat_history_tokens ON chat_history(total_tokens);
CREATE INDEX IF NOT EXISTS idx_monthly_usage_company_month ON monthly_token_usage(company_id, year_month);
CREATE INDEX IF NOT EXISTS idx_monthly_usage_user_month ON monthly_token_usage(user_id, year_month);

-- 7. 既存データのトークン推定値更新（既存のチャット履歴がある場合）
-- 文字数ベースでの推定トークン数を計算
UPDATE chat_history 
SET 
    input_tokens = CAST((LENGTH(user_message) * 1.3) AS INTEGER),
    output_tokens = CAST((LENGTH(bot_response) * 1.3) AS INTEGER),
    total_tokens = CAST(((LENGTH(user_message) + LENGTH(bot_response)) * 1.3) AS INTEGER),
    model_name = 'gpt-4o-mini',
    cost_usd = CAST(((LENGTH(user_message) + LENGTH(bot_response)) * 1.3 * 0.00000015) AS NUMERIC(10,6))
WHERE input_tokens IS NULL OR input_tokens = 0;

-- 8. トリガー作成：chat_historyにデータ挿入時に月次集計を自動更新
CREATE OR REPLACE FUNCTION update_monthly_usage_trigger()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO monthly_token_usage (
        id,
        company_id,
        user_id,
        year_month,
        total_input_tokens,
        total_output_tokens,
        total_tokens,
        total_cost_usd,
        conversation_count,
        updated_at
    )
    VALUES (
        gen_random_uuid()::text,
        NEW.company_id,
        NEW.user_id,
        TO_CHAR(NEW.timestamp::timestamp, 'YYYY-MM'),
        NEW.input_tokens,
        NEW.output_tokens,
        NEW.total_tokens,
        NEW.cost_usd,
        1,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (company_id, user_id, year_month)
    DO UPDATE SET
        total_input_tokens = monthly_token_usage.total_input_tokens + NEW.input_tokens,
        total_output_tokens = monthly_token_usage.total_output_tokens + NEW.output_tokens,
        total_tokens = monthly_token_usage.total_tokens + NEW.total_tokens,
        total_cost_usd = monthly_token_usage.total_cost_usd + NEW.cost_usd,
        conversation_count = monthly_token_usage.conversation_count + 1,
        updated_at = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- トリガーを作成
DROP TRIGGER IF EXISTS update_monthly_usage_on_insert ON chat_history;
CREATE TRIGGER update_monthly_usage_on_insert
    AFTER INSERT ON chat_history
    FOR EACH ROW
    EXECUTE FUNCTION update_monthly_usage_trigger();

-- 9. 初期設定データの挿入
INSERT INTO company_settings (company_id)
SELECT id FROM companies
ON CONFLICT (company_id) DO NOTHING;

-- 10. 外部キー制約の追加（必要に応じて）
-- ALTER TABLE chat_history ADD CONSTRAINT fk_chat_history_user_id FOREIGN KEY (user_id) REFERENCES users (id);
-- ALTER TABLE chat_history ADD CONSTRAINT fk_chat_history_company_id FOREIGN KEY (company_id) REFERENCES companies (id);
-- ALTER TABLE monthly_token_usage ADD CONSTRAINT fk_monthly_usage_company_id FOREIGN KEY (company_id) REFERENCES companies (id);
-- ALTER TABLE monthly_token_usage ADD CONSTRAINT fk_monthly_usage_user_id FOREIGN KEY (user_id) REFERENCES users (id);
-- ALTER TABLE company_settings ADD CONSTRAINT fk_company_settings_company_id FOREIGN KEY (company_id) REFERENCES companies (id); 