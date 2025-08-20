-- 株式会社No.1用Premium Plan設定を追加
-- 実行日: 2025年1月

-- 1. company_settingsテーブルに月額固定プラン関連カラムを追加
ALTER TABLE company_settings ADD COLUMN IF NOT EXISTS plan_type VARCHAR(50) DEFAULT 'pay_per_use';
ALTER TABLE company_settings ADD COLUMN IF NOT EXISTS monthly_fixed_price_jpy INTEGER DEFAULT 0;
ALTER TABLE company_settings ADD COLUMN IF NOT EXISTS plan_start_date DATE;
ALTER TABLE company_settings ADD COLUMN IF NOT EXISTS plan_end_date DATE;
ALTER TABLE company_settings ADD COLUMN IF NOT EXISTS is_unlimited BOOLEAN DEFAULT FALSE;
ALTER TABLE company_settings ADD COLUMN IF NOT EXISTS plan_description TEXT;

-- 2. 株式会社No.1のPremium Planレコードを挿入・更新
INSERT INTO company_settings (
    company_id,
    plan_type,
    monthly_fixed_price_jpy,
    plan_start_date,
    plan_end_date,
    is_unlimited,
    plan_description,
    pricing_tier,
    monthly_token_limit,
    created_at,
    updated_at
) VALUES (
    '77acc2e2-ce67-458d-bd38-7af0476b297a',
    'premium_fixed',
    30000,
    CURRENT_DATE,
    CURRENT_DATE + INTERVAL '3 months',
    TRUE,
    'Premium Plan - 株式会社No.1 専用プラン: ¥30,000/月固定料金、AI質問・回答無制限、専用サポート対応、プレミアム機能フルアクセス',
    'premium',
    999999999,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (company_id) DO UPDATE SET
    plan_type = EXCLUDED.plan_type,
    monthly_fixed_price_jpy = EXCLUDED.monthly_fixed_price_jpy,
    plan_start_date = EXCLUDED.plan_start_date,
    plan_end_date = EXCLUDED.plan_end_date,
    is_unlimited = EXCLUDED.is_unlimited,
    plan_description = EXCLUDED.plan_description,
    pricing_tier = EXCLUDED.pricing_tier,
    monthly_token_limit = EXCLUDED.monthly_token_limit,
    updated_at = CURRENT_TIMESTAMP;

-- 3. プラン変更履歴を記録（no1株式会社の代表ユーザー用）
INSERT INTO plan_history (
    id,
    user_id,
    from_plan,
    to_plan,
    changed_at,
    duration_days
) VALUES (
    gen_random_uuid()::text,
    '14876158-f0ee-47e6-8023-ac3635ce301e',
    'basic',
    'premium_fixed',
    CURRENT_TIMESTAMP,
    90
);

-- 4. 確認用クエリ
SELECT 
    company_id,
    plan_type,
    monthly_fixed_price_jpy,
    plan_start_date,
    plan_end_date,
    is_unlimited,
    plan_description,
    pricing_tier
FROM company_settings 
WHERE company_id = '77acc2e2-ce67-458d-bd38-7af0476b297a';
