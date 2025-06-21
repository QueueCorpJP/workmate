#!/usr/bin/env python3
"""
データベースのカラム存在確認と追加スクリプト
"""

import sys
sys.path.append('.')

def check_and_add_columns():
    """データベースのカラムをチェックして必要なカラムを追加する"""
    print("=== データベースカラムチェック開始 ===")
    
    try:
        from supabase_adapter import execute_query
        
        # 1. 現在のchat_historyテーブルの構造を確認
        print("1. chat_historyテーブルの構造確認...")
        result = execute_query("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'chat_history' 
            ORDER BY ordinal_position;
        """)
        
        if result:
            print("✓ 現在のテーブル構造:")
            for col in result:
                print(f"  - {col['column_name']}: {col['data_type']} (NULL: {col['is_nullable']}, Default: {col['column_default']})")
        else:
            print("⚠️ テーブル構造取得失敗")
            return False
        
        # 2. 必要なカラムの存在確認
        print("\n2. 必要な新カラムの存在確認...")
        required_columns = ['prompt_references', 'base_cost_usd', 'prompt_cost_usd']
        existing_columns = [col['column_name'] for col in result]
        
        missing_columns = []
        for col in required_columns:
            if col in existing_columns:
                print(f"✓ {col} - 存在")
            else:
                print(f"✗ {col} - 不足")
                missing_columns.append(col)
        
        # 3. 不足しているカラムを追加
        if missing_columns:
            print(f"\n3. 不足しているカラムを追加: {missing_columns}")
            
            for col in missing_columns:
                if col == 'prompt_references':
                    sql = "ALTER TABLE chat_history ADD COLUMN prompt_references INTEGER DEFAULT 0;"
                elif col == 'base_cost_usd':
                    sql = "ALTER TABLE chat_history ADD COLUMN base_cost_usd DECIMAL(10,6) DEFAULT 0.000000;"
                elif col == 'prompt_cost_usd':
                    sql = "ALTER TABLE chat_history ADD COLUMN prompt_cost_usd DECIMAL(10,6) DEFAULT 0.000000;"
                
                print(f"実行SQL: {sql}")
                add_result = execute_query(sql)
                
                if add_result is not None:
                    print(f"✓ {col} カラム追加成功")
                else:
                    print(f"✗ {col} カラム追加失敗")
                    return False
        else:
            print("\n✓ すべての必要なカラムが存在します")
        
        # 4. 追加後の確認
        print("\n4. 追加後の確認...")
        verify_result = execute_query("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'chat_history' 
            AND column_name IN ('prompt_references', 'base_cost_usd', 'prompt_cost_usd')
            ORDER BY column_name;
        """)
        
        if verify_result:
            verified_columns = [row['column_name'] for row in verify_result]
            print(f"✓ 確認された新カラム: {verified_columns}")
            
            if len(verified_columns) == 3:
                print("✓ すべてのカラムが正常に追加されました")
                return True
            else:
                print(f"⚠️ 一部のカラムが不足: {set(required_columns) - set(verified_columns)}")
                return False
        else:
            print("⚠️ 追加後の確認に失敗")
            return False
            
    except Exception as e:
        print(f"✗ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_new_columns():
    """新しいカラムの動作をテストする"""
    print("\n=== 新カラムの動作テスト ===")
    
    try:
        from supabase_adapter import execute_query
        
        # テストデータの挿入
        print("1. テストデータ挿入...")
        test_sql = """
            INSERT INTO chat_history (
                id, user_message, bot_response, user_id, company_id,
                prompt_references, base_cost_usd, prompt_cost_usd,
                input_tokens, output_tokens, total_tokens
            ) VALUES (
                'test-' || extract(epoch from now())::text,
                'テストメッセージ',
                'テスト回答',
                'test-user',
                'test-company',
                5,
                0.001500,
                0.005000,
                100,
                200,
                300
            ) RETURNING id;
        """
        
        insert_result = execute_query(test_sql)
        if insert_result:
            test_id = insert_result[0]['id']
            print(f"✓ テストデータ挿入成功: ID={test_id}")
            
            # データの確認
            verify_sql = f"""
                SELECT prompt_references, base_cost_usd, prompt_cost_usd
                FROM chat_history 
                WHERE id = '{test_id}';
            """
            
            verify_result = execute_query(verify_sql)
            if verify_result:
                data = verify_result[0]
                print(f"✓ データ確認成功:")
                print(f"  - prompt_references: {data['prompt_references']}")
                print(f"  - base_cost_usd: {data['base_cost_usd']}")
                print(f"  - prompt_cost_usd: {data['prompt_cost_usd']}")
                
                # テストデータの削除
                delete_sql = f"DELETE FROM chat_history WHERE id = '{test_id}';"
                execute_query(delete_sql)
                print("✓ テストデータ削除完了")
                
                return True
            else:
                print("✗ データ確認失敗")
                return False
        else:
            print("✗ テストデータ挿入失敗")
            return False
            
    except Exception as e:
        print(f"✗ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("データベースカラム確認・追加スクリプト")
    
    # カラムの確認と追加
    if check_and_add_columns():
        print("\n" + "="*50)
        # 新カラムの動作テスト
        if test_new_columns():
            print("\n✓ すべての処理が正常に完了しました")
            sys.exit(0)
        else:
            print("\n✗ テスト処理でエラーが発生しました")
            sys.exit(1)
    else:
        print("\n✗ カラム追加処理でエラーが発生しました")
        sys.exit(1) 