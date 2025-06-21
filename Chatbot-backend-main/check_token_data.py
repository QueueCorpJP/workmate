#!/usr/bin/env python3
"""
データベースのchat_historyテーブルの現在の状態とトークン・料金データを確認するスクリプト
"""

from supabase_adapter import select_data
import sys

def check_token_data():
    """データベースのトークン・料金データを確認"""
    
    print("🔍 データベース確認開始...")
    
    try:
        # 1. テーブル構造の確認（サンプル1件取得）
        print("📊 テーブル構造確認...")
        sample_result = select_data("chat_history", limit=1)
        if sample_result and sample_result.data:
            sample = sample_result.data[0]
            print("✅ 利用可能なカラム:")
            for key in sample.keys():
                print(f"  - {key}: {sample.get(key)}")
        else:
            print("⚠️ チャット履歴データが見つかりません")
            return
        
        # 2. 最新の数件のデータを確認
        print("\n📝 最新データ確認（5件）...")
        recent_result = select_data(
            "chat_history", 
            columns="id,total_tokens,cost_usd,prompt_references,base_cost_usd,prompt_cost_usd,created_at,user_id",
            limit=5,
            order="created_at desc"
        )
        
        if recent_result and recent_result.data:
            for i, chat in enumerate(recent_result.data):
                print(f"\n📄 記録 {i+1}:")
                print(f"  ID: {chat.get('id', 'N/A')}")
                print(f"  トークン数: {chat.get('total_tokens', 'N/A')}")
                print(f"  コスト(USD): {chat.get('cost_usd', 'N/A')}")
                print(f"  プロンプト参照: {chat.get('prompt_references', 'N/A')}")
                print(f"  基本コスト(USD): {chat.get('base_cost_usd', 'N/A')}")
                print(f"  プロンプトコスト(USD): {chat.get('prompt_cost_usd', 'N/A')}")
                print(f"  作成日時: {chat.get('created_at', 'N/A')}")
        
        # 3. 統計情報の確認
        print("\n📊 統計情報...")
        all_result = select_data(
            "chat_history", 
            columns="total_tokens,cost_usd,prompt_references,base_cost_usd,prompt_cost_usd",
            limit=1000
        )
        
        if all_result and all_result.data:
            chats = all_result.data
            
            total_records = len(chats)
            total_tokens_sum = sum(chat.get('total_tokens', 0) or 0 for chat in chats)
            total_cost_sum = sum(float(chat.get('cost_usd', 0) or 0) for chat in chats)
            
            # 新しいカラムの存在確認
            has_prompt_refs = any(chat.get('prompt_references') is not None for chat in chats)
            has_base_cost = any(chat.get('base_cost_usd') is not None for chat in chats)
            has_prompt_cost = any(chat.get('prompt_cost_usd') is not None for chat in chats)
            
            print(f"  📈 総レコード数: {total_records}")
            print(f"  📊 総トークン数: {total_tokens_sum:,}")
            print(f"  💰 総コスト: ${total_cost_sum:.6f}")
            print(f"  🔗 プロンプト参照カラム存在: {has_prompt_refs}")
            print(f"  💵 基本コストカラム存在: {has_base_cost}")
            print(f"  💴 プロンプトコストカラム存在: {has_prompt_cost}")
            
            # 新しいカラムの値が設定されているレコード数
            if has_prompt_refs:
                prompt_refs_count = sum(1 for chat in chats if (chat.get('prompt_references', 0) or 0) > 0)
                print(f"  🔢 プロンプト参照数 > 0 のレコード: {prompt_refs_count}")
            
            if has_base_cost:
                base_cost_count = sum(1 for chat in chats if (chat.get('base_cost_usd', 0) or 0) > 0)
                print(f"  💰 基本コスト > 0 のレコード: {base_cost_count}")
            
            if has_prompt_cost:
                prompt_cost_count = sum(1 for chat in chats if (chat.get('prompt_cost_usd', 0) or 0) > 0)
                print(f"  💳 プロンプトコスト > 0 のレコード: {prompt_cost_count}")
        
        # 4. カラムが存在しない場合の対応案を提示
        if not has_prompt_refs or not has_base_cost or not has_prompt_cost:
            print("\n⚠️ 新しい料金計算カラムが見つかりません！")
            print("📝 以下のコマンドでデータベースを更新してください：")
            print("   python update_token_schema.py")
        
        return True
        
    except Exception as e:
        print(f"❌ データ確認エラー: {e}")
        import traceback
        print(f"🔍 詳細エラー: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🔍 トークン・料金データ確認ツール")
    print("=" * 50)
    
    success = check_token_data()
    
    if success:
        print("\n✅ データ確認完了！")
    else:
        print("\n❌ データ確認失敗！")
    
    sys.exit(0) 