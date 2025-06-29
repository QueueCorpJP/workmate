#!/usr/bin/env python3
"""
🗑️ 最適化されたカスケード削除設定スクリプト
document_resources テーブルと chunks テーブル間のカスケード削除を効率的に設定
"""

import asyncio
import sys
import os
from supabase_adapter import get_supabase_client

async def setup_optimized_cascade_delete():
    """最適化されたカスケード削除の設定"""
    try:
        supabase = get_supabase_client()
        
        print("🚀 最適化されたカスケード削除設定開始")
        print("=" * 60)
        
        # 1. 現在の制約状況を確認
        print("📊 現在の制約状況を確認中...")
        
        constraint_check_query = """
        SELECT 
            tc.constraint_name,
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            rc.delete_rule
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
            JOIN information_schema.referential_constraints AS rc
              ON tc.constraint_name = rc.constraint_name
        WHERE 
            tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_name = 'chunks'
            AND kcu.column_name = 'doc_id'
        """
        
        try:
            result = supabase.rpc('execute_sql', {'query': constraint_check_query}).execute()
            
            if result.data and len(result.data) > 0:
                print("✅ 既存の外部キー制約が見つかりました:")
                for constraint in result.data:
                    print(f"  📋 制約名: {constraint['constraint_name']}")
                    print(f"  🗑️ 削除ルール: {constraint['delete_rule']}")
                    
                    if constraint['delete_rule'] == 'CASCADE':
                        print("✅ カスケード削除は既に設定済みです！")
                        return True
                    else:
                        print("⚠️ カスケード削除が設定されていません。設定を更新します。")
            else:
                print("❌ 外部キー制約が見つかりません。新規作成します。")
        except Exception as e:
            print(f"⚠️ 制約確認でエラー（新規作成を続行）: {e}")
        
        # 2. 既存の制約を削除（存在する場合）
        print("\n🧹 既存制約のクリーンアップ...")
        
        drop_constraint_queries = [
            "ALTER TABLE chunks DROP CONSTRAINT IF EXISTS fk_chunks_doc_id;",
            "ALTER TABLE chunks DROP CONSTRAINT IF EXISTS chunks_doc_id_fkey;",
            "ALTER TABLE chunks DROP CONSTRAINT IF EXISTS fk_chunks_document_sources;"
        ]
        
        for query in drop_constraint_queries:
            try:
                supabase.rpc('execute_sql', {'query': query}).execute()
                print(f"✅ 制約削除実行: {query.split()[4]}")
            except Exception as e:
                print(f"⚠️ 制約削除スキップ（存在しない可能性）: {e}")
        
        # 3. 最適化されたカスケード削除制約を追加
        print("\n🔧 最適化されたカスケード削除制約を追加...")
        
        add_constraint_query = """
        ALTER TABLE chunks 
        ADD CONSTRAINT fk_chunks_doc_id_cascade 
        FOREIGN KEY (doc_id) 
        REFERENCES document_sources(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE;
        """
        
        try:
            supabase.rpc('execute_sql', {'query': add_constraint_query}).execute()
            print("✅ カスケード削除制約を正常に追加しました")
        except Exception as e:
            print(f"❌ カスケード削除制約の追加に失敗: {e}")
            return False
        
        # 4. インデックスの最適化
        print("\n📈 インデックスの最適化...")
        
        index_queries = [
            "CREATE INDEX IF NOT EXISTS idx_chunks_doc_id_optimized ON chunks(doc_id);",
            "CREATE INDEX IF NOT EXISTS idx_chunks_company_doc ON chunks(company_id, doc_id);",
            "CREATE INDEX IF NOT EXISTS idx_document_sources_id ON document_sources(id);"
        ]
        
        for query in index_queries:
            try:
                supabase.rpc('execute_sql', {'query': query}).execute()
                print(f"✅ インデックス作成: {query.split()[5]}")
            except Exception as e:
                print(f"⚠️ インデックス作成スキップ: {e}")
        
        # 5. 設定確認
        print("\n🔍 設定確認...")
        
        verification_query = """
        SELECT 
            tc.constraint_name,
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            rc.delete_rule,
            rc.update_rule
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
            JOIN information_schema.referential_constraints AS rc
              ON tc.constraint_name = rc.constraint_name
        WHERE 
            tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_name = 'chunks'
            AND kcu.column_name = 'doc_id'
        """
        
        try:
            result = supabase.rpc('execute_sql', {'query': verification_query}).execute()
            
            if result.data and len(result.data) > 0:
                print("✅ カスケード削除制約の設定確認:")
                for constraint in result.data:
                    print(f"  📋 制約名: {constraint['constraint_name']}")
                    print(f"  📊 テーブル: {constraint['table_name']} -> {constraint['foreign_table_name']}")
                    print(f"  🔗 カラム: {constraint['column_name']} -> {constraint['foreign_column_name']}")
                    print(f"  🗑️ 削除ルール: {constraint['delete_rule']}")
                    print(f"  ✏️ 更新ルール: {constraint['update_rule']}")
                    
                    if constraint['delete_rule'] == 'CASCADE':
                        print("✅ カスケード削除が正常に設定されました！")
                        return True
            else:
                print("❌ 制約の確認に失敗しました")
                return False
        except Exception as e:
            print(f"❌ 設定確認エラー: {e}")
            return False
        
        # 6. 統計情報の更新
        print("\n📊 統計情報の更新...")
        
        analyze_queries = [
            "ANALYZE chunks;",
            "ANALYZE document_sources;"
        ]
        
        for query in analyze_queries:
            try:
                supabase.rpc('execute_sql', {'query': query}).execute()
                print(f"✅ 統計更新: {query.split()[1][:-1]}")
            except Exception as e:
                print(f"⚠️ 統計更新スキップ: {e}")
        
        print("\n🎉 カスケード削除設定が完了しました！")
        print("📋 効果:")
        print("  - document_sources のレコード削除時に関連する chunks も自動削除")
        print("  - データベースレベルでの整合性保証")
        print("  - アプリケーション側での手動削除処理が不要")
        print("  - 処理効率の向上")
        
        return True
        
    except Exception as e:
        print(f"❌ カスケード削除設定エラー: {e}")
        import traceback
        print(traceback.format_exc())
        return False

async def test_cascade_delete_simple():
    """シンプルなカスケード削除テスト"""
    try:
        supabase = get_supabase_client()
        
        print("\n🧪 カスケード削除テスト開始")
        print("=" * 50)
        
        # テスト用データの作成
        test_doc_id = f"test_cascade_{int(asyncio.get_event_loop().time())}"
        
        # 1. テスト用ドキュメントを作成
        print(f"📄 テスト用ドキュメント作成: {test_doc_id}")
        
        doc_data = {
            "id": test_doc_id,
            "name": "カスケード削除テスト用ドキュメント",
            "type": "text",
            "company_id": "test_company",
            "active": True
        }
        
        try:
            doc_result = supabase.table("document_sources").insert(doc_data).execute()
            if not doc_result.data:
                print("❌ テスト用ドキュメントの作成に失敗")
                return False
            print("✅ テスト用ドキュメント作成成功")
        except Exception as e:
            print(f"❌ ドキュメント作成エラー: {e}")
            return False
        
        # 2. テスト用chunksを作成
        print("🧩 テスト用chunks作成...")
        
        chunks_data = [
            {
                "doc_id": test_doc_id,
                "chunk_index": 0,
                "content": "テスト用チャンク1",
                "company_id": "test_company"
            },
            {
                "doc_id": test_doc_id,
                "chunk_index": 1,
                "content": "テスト用チャンク2",
                "company_id": "test_company"
            }
        ]
        
        try:
            chunks_result = supabase.table("chunks").insert(chunks_data).execute()
            if not chunks_result.data:
                print("❌ テスト用chunksの作成に失敗")
                return False
            print(f"✅ テスト用chunks作成成功: {len(chunks_result.data)}件")
        except Exception as e:
            print(f"❌ chunks作成エラー: {e}")
            return False
        
        # 3. 削除前の確認
        doc_count = len(supabase.table("document_sources").select("id").eq("id", test_doc_id).execute().data)
        chunks_count = len(supabase.table("chunks").select("id").eq("doc_id", test_doc_id).execute().data)
        
        print(f"📊 削除前: ドキュメント {doc_count}件, chunks {chunks_count}件")
        
        # 4. ドキュメント削除（カスケード削除テスト）
        print(f"🗑️ ドキュメント削除実行...")
        
        try:
            delete_result = supabase.table("document_sources").delete().eq("id", test_doc_id).execute()
            print("✅ ドキュメント削除実行完了")
        except Exception as e:
            print(f"❌ ドキュメント削除エラー: {e}")
            return False
        
        # 5. 削除後の確認
        doc_count_after = len(supabase.table("document_sources").select("id").eq("id", test_doc_id).execute().data)
        chunks_count_after = len(supabase.table("chunks").select("id").eq("doc_id", test_doc_id).execute().data)
        
        print(f"📊 削除後: ドキュメント {doc_count_after}件, chunks {chunks_count_after}件")
        
        # 6. 結果判定
        if doc_count_after == 0 and chunks_count_after == 0:
            print("✅ カスケード削除テスト成功！")
            print("  - ドキュメントが削除されました")
            print("  - 関連するchunksも自動的に削除されました")
            return True
        else:
            print("❌ カスケード削除テスト失敗")
            print(f"  - 残存ドキュメント: {doc_count_after}件")
            print(f"  - 残存chunks: {chunks_count_after}件")
            return False
            
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        print(traceback.format_exc())
        return False

async def main():
    """メイン関数"""
    print("🚀 カスケード削除最適化スクリプト開始")
    print("=" * 70)
    
    # 1. カスケード削除設定
    setup_success = await setup_optimized_cascade_delete()
    
    if setup_success:
        # 2. テスト実行
        test_success = await test_cascade_delete_simple()
        
        if test_success:
            print("\n🎉 カスケード削除の設定とテストが完了しました！")
            print("📋 これで document_sources のレコード削除時に")
            print("   関連する chunks も自動的に削除されます。")
        else:
            print("\n⚠️ 設定は完了しましたが、テストで問題が発生しました。")
    else:
        print("\n❌ カスケード削除の設定に失敗しました。")
    
    print("\n🏁 処理完了")

if __name__ == "__main__":
    asyncio.run(main())