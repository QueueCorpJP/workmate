from supabase_adapter import execute_query

def disable_trigger():
    """トリガーを無効化する"""
    try:
        print('既存のトリガーと関数を削除中...')
        
        # 既存のトリガーと関数を削除
        execute_query('DROP TRIGGER IF EXISTS update_monthly_usage_on_insert ON chat_history;')
        execute_query('DROP FUNCTION IF EXISTS update_monthly_usage_trigger();')
        
        print('✅ トリガーが無効化されました')
        
    except Exception as e:
        print(f'❌ エラー: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    disable_trigger() 