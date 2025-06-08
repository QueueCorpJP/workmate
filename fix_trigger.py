#!/usr/bin/env python3
import sys
import os
sys.path.append('.')
sys.path.append('./Chatbot-backend-main')

# 環境変数を読み込み
from dotenv import load_dotenv
load_dotenv('./Chatbot-backend-main/.env')

from Chatbot-backend-main.supabase_adapter import get_connection

def fix_trigger():
    """トリガー関数にnullチェックを追加"""
    try:
        # Supabase接続を取得
        conn = get_connection()
        print('Supabase接続成功')
        
        cursor = conn.cursor()
        
        # 既存のトリガーと関数を削除
        print('既存のトリガーと関数を削除中...')
        cursor.execute('DROP TRIGGER IF EXISTS update_monthly_usage_on_insert ON chat_history;')
        cursor.execute('DROP FUNCTION IF EXISTS update_monthly_usage_trigger();')
        
        # 新しいトリガー関数を作成（null チェック付き）
        print('新しいトリガー関数を作成中...')
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_monthly_usage_trigger()
            RETURNS TRIGGER AS $$
            BEGIN
                -- company_id または user_id が null の場合は処理をスキップ
                IF NEW.company_id IS NULL OR NEW.user_id IS NULL THEN
                    RAISE WARNING 'company_id (%) または user_id (%) が null のため月次集計をスキップします', NEW.company_id, NEW.user_id;
                    RETURN NEW;
                END IF;
                
                -- トークン関連の値が null または 0 の場合もスキップ
                IF NEW.total_tokens IS NULL OR NEW.total_tokens = 0 THEN
                    RETURN NEW;
                END IF;
                
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
                    COALESCE(NEW.input_tokens, 0),
                    COALESCE(NEW.output_tokens, 0),
                    COALESCE(NEW.total_tokens, 0),
                    COALESCE(NEW.cost_usd, 0),
                    1,
                    CURRENT_TIMESTAMP
                )
                ON CONFLICT (company_id, user_id, year_month)
                DO UPDATE SET
                    total_input_tokens = monthly_token_usage.total_input_tokens + COALESCE(NEW.input_tokens, 0),
                    total_output_tokens = monthly_token_usage.total_output_tokens + COALESCE(NEW.output_tokens, 0),
                    total_tokens = monthly_token_usage.total_tokens + COALESCE(NEW.total_tokens, 0),
                    total_cost_usd = monthly_token_usage.total_cost_usd + COALESCE(NEW.cost_usd, 0),
                    conversation_count = monthly_token_usage.conversation_count + 1,
                    updated_at = CURRENT_TIMESTAMP;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # トリガーを再作成
        print('トリガーを作成中...')
        cursor.execute("""
            CREATE TRIGGER update_monthly_usage_on_insert
                AFTER INSERT ON chat_history
                FOR EACH ROW
                EXECUTE FUNCTION update_monthly_usage_trigger();
        """)
        
        conn.commit()
        print('✅ トリガー関数の修正が完了しました')
        
    except Exception as e:
        print(f'❌ エラー: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_trigger() 