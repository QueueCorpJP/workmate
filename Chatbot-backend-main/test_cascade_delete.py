#!/usr/bin/env python3
"""
🗑️ カスケード削除のテストスクリプト
ドキュメント削除時にchunksテーブルの関連レコードも自動削除されることを確認
"""

import asyncio
import sys
import os
from supabase_adapter import get_supabase_client

async def test_cascade_delete():
    """カスケード削除のテスト"""
    try:
        # Supabaseクライアントを取得
        supabase = get_supabase_client()
        
        print("🧪 カスケード削除テスト開始")
        print("=" * 50)
        
        # 1. テスト用のドキュメントを作成
        test_doc_id = "test_cascade_delete_doc"
        test_doc_data = {
            "id": test_doc_id,
            "name": "テスト用ドキュメント（削除テスト）",
            "type": "text",
            "uploaded_by": "test_user",
            "company_id": "test_company",
            "active": True
        }
        
        print(f"📄 テスト用ドキュメントを作成: {test_doc_id}")
        doc_result = supabase.table("document_sources").insert(test_doc_data).execute()
        
        if not doc_result.data:
            print("❌ テスト用ドキュメントの作成に失敗")
            return
        
        # 2. テスト用のchunksを作成
        test_chunks = [
            {
                "doc_id": test_doc_id,
                "chunk_index": 0,
                "content": "これはテスト用のチャンク1です。",
                "company_id": "test_company"
            },
            {
                "doc_id": test_doc_id,
                "chunk_index": 1,
                "content": "これはテスト用のチャンク2です。",
                "company_id": "test_company"
            },
            {
                "doc_id": test_doc_id,
                "chunk_index": 2,
                "content": "これはテスト用のチャンク3です。",
                "company_id": "test_company"
            }
        ]
        
        print(f"🧩 テスト用chunksを作成: {len(test_chunks)}件")
        chunks_result = supabase.table("chunks").insert(test_chunks).execute()
        
        if not chunks_result.data:
            print("❌ テスト用chunksの作成に失敗")
            return
        
        print(f"✅ 作成されたchunks: {len(chunks_result.data)}件")
        
        # 3. 削除前の状態を確認
        print("\n📊 削除前の状態確認")
        
        # ドキュメント確認
        doc_check = supabase.table("document_sources").select("*").eq("id", test_doc_id).execute()
        print(f"  📄 ドキュメント: {len(doc_check.data)}件")
        
        # chunks確認
        chunks_check = supabase.table("chunks").select("*").eq("doc_id", test_doc_id).execute()
        print(f"  🧩 chunks: {len(chunks_check.data)}件")
        
        # 4. ドキュメントを削除（カスケード削除のテスト）
        print(f"\n🗑️ ドキュメント削除実行: {test_doc_id}")
        delete_result = supabase.table("document_sources").delete().eq("id", test_doc_id).execute()
        
        if delete_result.data:
            print(f"✅ ドキュメント削除成功: {len(delete_result.data)}件")
        else:
            print("❌ ドキュメント削除失敗")
            return
        
        # 5. 削除後の状態を確認
        print("\n📊 削除後の状態確認")
        
        # ドキュメント確認
        doc_check_after = supabase.table("document_sources").select("*").eq("id", test_doc_id).execute()
        print(f"  📄 ドキュメント: {len(doc_check_after.data)}件")
        
        # chunks確認
        chunks_check_after = supabase.table("chunks").select("*").eq("doc_id", test_doc_id).execute()
        print(f"  🧩 chunks: {len(chunks_check_after.data)}件")
        
        # 6. 結果判定
        print("\n🎯 テスト結果")
        print("=" * 50)
        
        if len(doc_check_after.data) == 0 and len(chunks_check_after.data) == 0:
            print("✅ カスケード削除テスト成功！")
            print("   - ドキュメントが削除されました")
            print("   - 関連するchunksも自動的に削除されました")
            print("   - ON DELETE CASCADE制約が正常に動作しています")
        else:
            print("❌ カスケード削除テスト失敗")
            if len(doc_check_after.data) > 0:
                print(f"   - ドキュメントが残っています: {len(doc_check_after.data)}件")
            if len(chunks_check_after.data) > 0:
                print(f"   - chunksが残っています: {len(chunks_check_after.data)}件")
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        print(traceback.format_exc())
        
        # エラー時のクリーンアップ
        try:
            print("\n🧹 クリーンアップ実行")
            supabase.table("chunks").delete().eq("doc_id", test_doc_id).execute()
            supabase.table("document_sources").delete().eq("id", test_doc_id).execute()
            print("✅ テストデータをクリーンアップしました")
        except:
            print("⚠️ クリーンアップに失敗しました（手動でテストデータを削除してください）")

async def test_real_delete_function():
    """実際の削除関数のテスト"""
    try:
        from modules.resource import remove_resource_by_id
        
        print("\n🔧 実際の削除関数テスト")
        print("=" * 50)
        
        # テスト用のドキュメントとchunksを作成
        supabase = get_supabase_client()
        test_doc_id = "test_real_delete_function"
        
        # ドキュメント作成
        test_doc_data = {
            "id": test_doc_id,
            "name": "実関数テスト用ドキュメント",
            "type": "text",
            "uploaded_by": "test_user",
            "company_id": "test_company",
            "active": True
        }
        
        doc_result = supabase.table("document_sources").insert(test_doc_data).execute()
        
        # chunks作成
        test_chunks = [
            {
                "doc_id": test_doc_id,
                "chunk_index": 0,
                "content": "実関数テスト用チャンク1",
                "company_id": "test_company"
            },
            {
                "doc_id": test_doc_id,
                "chunk_index": 1,
                "content": "実関数テスト用チャンク2",
                "company_id": "test_company"
            }
        ]
        
        chunks_result = supabase.table("chunks").insert(test_chunks).execute()
        print(f"📄 テストデータ作成完了: ドキュメント1件、chunks{len(chunks_result.data)}件")
        
        # 実際の削除関数を呼び出し
        print(f"🗑️ remove_resource_by_id関数を実行: {test_doc_id}")
        result = await remove_resource_by_id(test_doc_id, None)
        
        print(f"📋 削除結果: {result}")
        
        # 削除後の確認
        doc_check = supabase.table("document_sources").select("*").eq("id", test_doc_id).execute()
        chunks_check = supabase.table("chunks").select("*").eq("doc_id", test_doc_id).execute()
        
        print(f"📊 削除後確認: ドキュメント{len(doc_check.data)}件、chunks{len(chunks_check.data)}件")
        
        if len(doc_check.data) == 0 and len(chunks_check.data) == 0:
            print("✅ 実関数テスト成功！削除関数が正常に動作しています")
        else:
            print("❌ 実関数テスト失敗")
        
    except Exception as e:
        print(f"❌ 実関数テストエラー: {e}")
        import traceback
        print(traceback.format_exc())

async def main():
    """メイン関数"""
    print("🚀 カスケード削除テストスイート開始")
    print("=" * 60)
    
    # 基本的なカスケード削除テスト
    await test_cascade_delete()
    
    # 実際の削除関数テスト
    await test_real_delete_function()
    
    print("\n🏁 全テスト完了")

if __name__ == "__main__":
    asyncio.run(main())