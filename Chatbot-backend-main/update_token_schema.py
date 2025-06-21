#!/usr/bin/env python3
"""
データベースのchat_historyテーブルに新しいトークン料金体系用のカラムを追加するスクリプト
"""

from supabase_adapter import execute_sql, select_data
import sys

def update_database_schema():
    """データベーススキーマを更新してプロンプト参照カラムを追加"""
    
    print("🔄 データベーススキーマ更新開始...")
    
    try:
        # 1. プロンプト参照数カラムを追加
        print("📝 prompt_references カラムを追加中...")
        execute_sql("ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS prompt_references INTEGER DEFAULT 0;")
        print("✅ prompt_references カラム追加完了")
        
        # 2. 基本コスト（トークンベース）カラムを追加
        print("📝 base_cost_usd カラムを追加中...")
        execute_sql("ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS base_cost_usd DECIMAL(10,6) DEFAULT 0.000000;")
        print("✅ base_cost_usd カラム追加完了")
        
        # 3. プロンプト参照コストカラムを追加
        print("📝 prompt_cost_usd カラムを追加中...")
        execute_sql("ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS prompt_cost_usd DECIMAL(10,6) DEFAULT 0.000000;")
        print("✅ prompt_cost_usd カラム追加完了")
        
        # 4. 既存データの確認
        print("📊 既存データを確認中...")
        result = select_data("chat_history", limit=1)
        if result and result.data:
            sample_record = result.data[0]
            print("✅ サンプルレコード:")
            print(f"  - prompt_references: {sample_record.get('prompt_references', 'NOT_FOUND')}")
            print(f"  - base_cost_usd: {sample_record.get('base_cost_usd', 'NOT_FOUND')}")
            print(f"  - prompt_cost_usd: {sample_record.get('prompt_cost_usd', 'NOT_FOUND')}")
        else:
            print("ℹ️  既存データがありません（新規テーブル）")
        
        # 5. 統計情報の表示
        count_result = select_data("chat_history", columns="COUNT(*) as total")
        if count_result and count_result.data:
            total_records = count_result.data[0].get('total', 0)
            print(f"📊 総チャット履歴数: {total_records}")
        
        print("🎉 データベーススキーマ更新完了！")
        return True
        
    except Exception as e:
        print(f"❌ スキーマ更新エラー: {e}")
        import traceback
        print(f"🔍 詳細エラー: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 トークン料金体系用データベーススキーマ更新ツール")
    print("=" * 50)
    
    success = update_database_schema()
    
    if success:
        print("\n✅ 更新成功！新しいトークン料金体系が利用可能になりました。")
        print("\n📝 追加されたカラム:")
        print("  - prompt_references: プロンプト参照数")
        print("  - base_cost_usd: 基本コスト（USD）")
        print("  - prompt_cost_usd: プロンプト参照コスト（USD）")
        print("\n💡 これで以下の料金設定が有効になります:")
        print("  - Input: $0.30 per 1M tokens")
        print("  - Output: $2.50 per 1M tokens") 
        print("  - プロンプト参照: $0.001 per reference")
        sys.exit(0)
    else:
        print("\n❌ 更新失敗！エラーを確認してください。")
        sys.exit(1) 