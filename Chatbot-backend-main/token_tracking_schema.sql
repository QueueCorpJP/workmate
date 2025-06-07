-- トークン使用量追跡のためのデータベーススキーマ拡張
-- 実行日: 2025年1月

-- 1. chat_historyテーブルにトークン使用量関連のカラムを追加
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS input_tokens INTEGER DEFAULT 0;
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS output_tokens INTEGER DEFAULT 0;
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS total_tokens INTEGER DEFAULT 0;
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS model_name TEXT DEFAULT 'gpt-4o-mini';
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS cost_usd DECIMAL(10,6) DEFAULT 0.000000;
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS user_id TEXT;
ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS company_id TEXT;

-- 2. 月次トークン使用量集計テーブルを作成
CREATE TABLE IF NOT EXISTS monthly_token_usage (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    year_month TEXT NOT NULL, -- 'YYYY-MM' format
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10,6) DEFAULT 0.000000,
    conversation_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (company_id) REFERENCES companies (id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(company_id, user_id, year_month)
);

-- 3. リアルタイム集計用のビューを作成
CREATE VIEW IF NOT EXISTS company_monthly_usage AS
SELECT 
    c.id as company_id,
    c.name as company_name,
    mtu.year_month,
    SUM(mtu.total_input_tokens) as total_input_tokens,
    SUM(mtu.total_output_tokens) as total_output_tokens,
    SUM(mtu.total_tokens) as total_tokens,
    SUM(mtu.total_cost_usd) as total_cost_usd,
    SUM(mtu.conversation_count) as total_conversations,
    COUNT(DISTINCT mtu.user_id) as active_users
FROM companies c
LEFT JOIN monthly_token_usage mtu ON c.id = mtu.company_id
GROUP BY c.id, c.name, mtu.year_month;

-- 4. 現在の月の集計用ビュー
CREATE VIEW IF NOT EXISTS current_month_usage AS
SELECT 
    company_id,
    user_id,
    SUM(total_tokens) as current_month_tokens,
    COUNT(*) as current_month_conversations,
    SUM(cost_usd) as current_month_cost_usd
FROM chat_history 
WHERE strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')
GROUP BY company_id, user_id;

-- 5. 会社全体の今月使用量ビュー
CREATE VIEW IF NOT EXISTS company_current_month_summary AS
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
    cost_usd = CAST(((LENGTH(user_message) + LENGTH(bot_response)) * 1.3 * 0.00000015) AS DECIMAL(10,6))
WHERE input_tokens IS NULL OR input_tokens = 0;

-- 8. トリガー作成：chat_historyにデータ挿入時に月次集計を自動更新
CREATE TRIGGER IF NOT EXISTS update_monthly_usage_on_insert
AFTER INSERT ON chat_history
BEGIN
    INSERT OR REPLACE INTO monthly_token_usage (
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
    SELECT 
        COALESCE(mtu.id, lower(hex(randomblob(16)))),
        NEW.company_id,
        NEW.user_id,
        strftime('%Y-%m', NEW.timestamp) as year_month,
        COALESCE(mtu.total_input_tokens, 0) + NEW.input_tokens,
        COALESCE(mtu.total_output_tokens, 0) + NEW.output_tokens,
        COALESCE(mtu.total_tokens, 0) + NEW.total_tokens,
        COALESCE(mtu.total_cost_usd, 0) + NEW.cost_usd,
        COALESCE(mtu.conversation_count, 0) + 1,
        datetime('now')
    FROM (SELECT 1) dummy
    LEFT JOIN monthly_token_usage mtu ON 
        mtu.company_id = NEW.company_id AND 
        mtu.user_id = NEW.user_id AND 
        mtu.year_month = strftime('%Y-%m', NEW.timestamp);
END;

-- 9. 会社設定テーブルにトークン設定を追加（オプション）
CREATE TABLE IF NOT EXISTS company_settings (
    company_id TEXT PRIMARY KEY,
    monthly_token_limit INTEGER DEFAULT 25000000, -- 25M tokens
    warning_threshold_percentage INTEGER DEFAULT 80, -- 80%で警告
    critical_threshold_percentage INTEGER DEFAULT 95, -- 95%で重要警告
    pricing_tier TEXT DEFAULT 'basic', -- basic, pro, enterprise
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (company_id) REFERENCES companies (id)
);

-- 10. 初期設定データの挿入
INSERT OR IGNORE INTO company_settings (company_id)
SELECT id FROM companies; 