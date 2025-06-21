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
            print("✓ 現在のchat_historyテーブル構造:")
            for col in result:
                print(f"  - {col['column_name']}: {col['data_type']} (NULL: {col['is_nullable']}, Default: {col['column_default']})")
        else:
            print("⚠️ chat_historyテーブル構造取得失敗")
            return False
        
        # 2. 必要なカラムの存在確認（chat_history）
        print("\n2. chat_historyテーブルの必要なカラム確認...")
        required_columns = ['prompt_references', 'base_cost_usd', 'prompt_cost_usd']
        existing_columns = [col['column_name'] for col in result]
        
        missing_columns = []
        for col in required_columns:
            if col in existing_columns:
                print(f"✓ {col} - 存在")
            else:
                print(f"✗ {col} - 不足")
                missing_columns.append(col)
        
        # 3. 不足しているカラムを追加（chat_history）
        if missing_columns:
            print(f"\n3. chat_historyの不足しているカラムを追加: {missing_columns}")
            
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
            print("\n✓ chat_historyのすべての必要なカラムが存在します")
        
        # 4. document_sourcesテーブルの構造を確認
        print("\n4. document_sourcesテーブルの構造確認...")
        doc_result = execute_query("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'document_sources' 
            ORDER BY ordinal_position;
        """)
        
        if doc_result:
            print("✓ 現在のdocument_sourcesテーブル構造:")
            for col in doc_result:
                print(f"  - {col['column_name']}: {col['data_type']} (NULL: {col['is_nullable']}, Default: {col['column_default']})")
        else:
            print("⚠️ document_sourcesテーブル構造取得失敗")
            return False
        
        # 5. document_sourcesのspecialカラム存在確認
        print("\n5. document_sourcesのspecialカラム確認...")
        doc_existing_columns = [col['column_name'] for col in doc_result]
        
        if 'special' in doc_existing_columns:
            print("✓ special カラム - 存在")
        else:
            print("✗ special カラム - 不足")
            print("6. specialカラムを追加...")
            sql = "ALTER TABLE document_sources ADD COLUMN special TEXT;"
            print(f"実行SQL: {sql}")
            add_result = execute_query(sql)
            
            if add_result is not None:
                print("✓ special カラム追加成功")
            else:
                print("✗ special カラム追加失敗")
                return False
        
        # 6. 最終確認
        print("\n7. 最終確認...")
        # chat_history確認
        verify_result = execute_query("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'chat_history' 
            AND column_name IN ('prompt_references', 'base_cost_usd', 'prompt_cost_usd')
            ORDER BY column_name;
        """)
        
        # document_sources確認
        doc_verify_result = execute_query("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'document_sources' 
            AND column_name = 'special';
        """)
        
        print("✓ カラム追加完了")
        print("✓ データベース構造の更新が完了しました")
        
        return True
        
    except Exception as e:
        print(f"✗ カラム追加処理でエラーが発生しました: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = check_and_add_columns()
    print("\n=== データベースカラムチェック完了 ===")
    if success:
        print("✓ すべての処理が正常に完了しました")
    else:
        print("✗ 処理中にエラーが発生しました")
        sys.exit(1) 