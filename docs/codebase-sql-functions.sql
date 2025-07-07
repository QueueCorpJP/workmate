-- ===============================================
-- SQL関数完全一覧（コードベース vs Supabase）
-- ===============================================
-- 最終更新: 2025年1月
-- ===============================================

-- ■■■ コードベース内のSQL関数 ■■■
-- ファイル: Chatbot-backend-main/sql/token_tracking_schema_postgresql.sql

-- トリガー関数：月次トークン使用量自動集計
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
        total_input_tokens = monthly_token_usage.total_input_tokens + EXCLUDED.total_input_tokens,
        total_output_tokens = monthly_token_usage.total_output_tokens + EXCLUDED.total_output_tokens,
        total_tokens = monthly_token_usage.total_tokens + EXCLUDED.total_tokens,
        total_cost_usd = monthly_token_usage.total_cost_usd + EXCLUDED.total_cost_usd,
        conversation_count = monthly_token_usage.conversation_count + EXCLUDED.conversation_count,
        updated_at = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ■■■ Supabase側のSQL関数（検索関連） ■■■
-- 確認日: 2025年1月
-- MCP経由で実際に確認済み

-- 【カスタム検索関数】
-- ① テキスト正規化関数（プロジェクト専用）
-- normalize_text(input text) RETURNS text
-- 機能: 日本語テキストの正規化（全角→半角、会社形態統一、特殊文字統一）
-- 使用例: normalize_text('ＴＥＳＴカンパニー株式会社') → 'testカンパニー(株)'

-- 【PostgreSQL pg_trgm拡張関数群 v1.6】
-- ② 基本類似度関数
-- similarity(text, text) RETURNS real
-- 機能: 2つのテキスト間のtrigram類似度計算（0.0-1.0）

-- ③ 単語類似度関数群
-- word_similarity(text, text) RETURNS real
-- strict_word_similarity(text, text) RETURNS real
-- 機能: 単語レベルでの類似度計算

-- ④ 距離計算関数群
-- similarity_dist(text, text) RETURNS real
-- word_similarity_dist_op(text, text) RETURNS real
-- strict_word_similarity_dist_op(text, text) RETURNS real

-- ⑤ 比較演算子関数群
-- similarity_op(text, text) RETURNS boolean
-- word_similarity_op(text, text) RETURNS boolean
-- strict_word_similarity_op(text, text) RETURNS boolean

-- ⑥ trigram表示・設定関数
-- show_trgm(text) RETURNS text[]
-- set_limit(real) RETURNS real
-- show_limit() RETURNS real

-- ⑦ GINインデックス内部関数群（15個）
-- gin_extract_query_trgm, gin_extract_value_trgm, gin_trgm_consistent, 
-- gin_trgm_triconsistent, gtrgm_compress, gtrgm_consistent, gtrgm_decompress,
-- gtrgm_distance, gtrgm_in, gtrgm_options, gtrgm_out, gtrgm_penalty,
-- gtrgm_picksplit, gtrgm_same, gtrgm_union

-- 【PostgreSQL fuzzystrmatch拡張関数群】
-- ⑧ レーベンシュタイン距離
-- levenshtein(text, text) RETURNS integer
-- levenshtein(text, text, integer, integer, integer) RETURNS integer
-- levenshtein_less_equal(text, text, integer) RETURNS integer
-- levenshtein_less_equal(text, text, integer, integer, integer, integer) RETURNS integer

-- ⑨ 音韻検索関数群
-- soundex(text) RETURNS text
-- text_soundex(text) RETURNS text
-- metaphone(text, integer) RETURNS text
-- dmetaphone(text) RETURNS text
-- dmetaphone_alt(text) RETURNS text
-- difference(text, text) RETURNS integer

-- 【その他のデータベース関数】
-- ⑩ 汎用トリガー関数
-- update_updated_at_column() RETURNS trigger

-- ===============================================
-- 関数分類サマリー
-- ===============================================
-- コードベース関数: 1個（トークン管理）
-- Supabase検索関数: 40個（検索・類似度計算）
--   ├─ カスタム: 1個（normalize_text）
--   ├─ pg_trgm: 25個（trigram類似度）
--   ├─ fuzzystrmatch: 13個（音韻・距離）
--   └─ その他: 1個（トリガー）
-- 
-- 結論: 検索関連は全てSupabase側、
--       コードベースは課金管理のみ 