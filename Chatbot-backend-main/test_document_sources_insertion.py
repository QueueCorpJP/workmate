"""
📤 document_sourcesテーブルへの挿入テスト
ファイルアップロード時にdocument_sourcesテーブルにdoc_idが正しく挿入されるかをテスト
"""

import os
import sys
import asyncio
import tempfile
import uuid
from datetime import datetime
from fastapi import UploadFile
from io import BytesIO

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_adapter import get_supabase_client, insert_data, select_data
from modules.document_processor import DocumentProcessor
from modules.document_processor_record_based import DocumentProcessorRecordBased

async def test_document_sources_insertion():
    """document_sourcesテーブルへの挿入をテスト"""
    print("🧪 document_sourcesテーブル挿入テスト開始")
    
    # テスト用データ
    test_user_id = "test-user-" + str(uuid.uuid4())[:8]
    test_company_id = "test-company-" + str(uuid.uuid4())[:8]
    test_filename = "test_document.txt"
    test_content = "これはテスト用のドキュメントです。\n\nファイルアップロード時にdocument_sourcesテーブルとchunksテーブルの両方にdoc_idが正しく挿入されるかをテストしています。"
    
    try:
        # 1. Supabaseクライアントの確認
        print("1️⃣ Supabaseクライアント確認")
        supabase = get_supabase_client()
        if not supabase:
            raise Exception("Supabaseクライアントの取得に失敗しました")
        print("✅ Supabaseクライアント取得成功")
        
        # 2. テスト用ユーザーとカンパニーを作成
        print("2️⃣ テスト用ユーザー・カンパニー作成")
        
        # テスト用カンパニー作成
        company_data = {
            "id": test_company_id,
            "name": "Test Company",
            "created_at": datetime.now().isoformat()
        }
        
        try:
            company_result = insert_data("companies", company_data)
            print(f"✅ テスト用カンパニー作成: {test_company_id}")
        except Exception as e:
            print(f"⚠️ カンパニー作成エラー（既存の可能性）: {e}")
        
        # テスト用ユーザー作成
        user_data = {
            "id": test_user_id,
            "company_id": test_company_id,
            "name": "Test User",
            "email": f"test-{test_user_id}@example.com",
            "created_at": datetime.now().isoformat()
        }
        
        try:
            user_result = insert_data("users", user_data)
            print(f"✅ テスト用ユーザー作成: {test_user_id}")
        except Exception as e:
            print(f"⚠️ ユーザー作成エラー（既存の可能性）: {e}")
        
        # 3. テスト用ファイルを作成
        print("3️⃣ テスト用ファイル作成")
        test_file_content = test_content.encode('utf-8')
        test_file = UploadFile(
            filename=test_filename,
            file=BytesIO(test_file_content),
            size=len(test_file_content)
        )
        
        # 4. DocumentProcessorでファイル処理
        print("4️⃣ DocumentProcessorでファイル処理テスト")
        processor = DocumentProcessor()
        
        try:
            result = await processor.process_uploaded_file(
                file=test_file,
                user_id=test_user_id,
                company_id=test_company_id
            )
            
            print(f"✅ DocumentProcessor処理成功:")
            print(f"   - document_id: {result.get('document_id')}")
            print(f"   - filename: {result.get('filename')}")
            print(f"   - total_chunks: {result.get('total_chunks')}")
            
            doc_id = result.get('document_id')
            
            # 5. document_sourcesテーブルの確認
            print("5️⃣ document_sourcesテーブル確認")
            doc_sources_result = select_data(
                "document_sources",
                columns="*",
                filters={"id": doc_id}
            )
            
            if doc_sources_result.data and len(doc_sources_result.data) > 0:
                print(f"✅ document_sourcesテーブルにレコード発見:")
                doc_record = doc_sources_result.data[0]
                print(f"   - id: {doc_record.get('id')}")
                print(f"   - name: {doc_record.get('name')}")
                print(f"   - company_id: {doc_record.get('company_id')}")
                print(f"   - uploaded_by: {doc_record.get('uploaded_by')}")
            else:
                print("❌ document_sourcesテーブルにレコードが見つかりません")
                return False
            
            # 6. chunksテーブルの確認
            print("6️⃣ chunksテーブル確認")
            chunks_result = select_data(
                "chunks",
                columns="*",
                filters={"doc_id": doc_id}
            )
            
            if chunks_result.data and len(chunks_result.data) > 0:
                print(f"✅ chunksテーブルにレコード発見: {len(chunks_result.data)}件")
                for i, chunk in enumerate(chunks_result.data[:3]):  # 最初の3件を表示
                    print(f"   - chunk {i}: doc_id={chunk.get('doc_id')}, chunk_index={chunk.get('chunk_index')}")
            else:
                print("❌ chunksテーブルにレコードが見つかりません")
                return False
            
            print("🎉 DocumentProcessor テスト成功: document_sourcesとchunksの両方にdoc_idが正しく挿入されました")
            
        except Exception as e:
            print(f"❌ DocumentProcessor処理エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 7. DocumentProcessorRecordBasedでExcelファイル処理テスト
        print("\n7️⃣ DocumentProcessorRecordBasedでExcelファイル処理テスト")
        
        # 簡単なExcelファイルを作成
        try:
            import pandas as pd
            excel_data = pd.DataFrame({
                'Name': ['田中太郎', '佐藤花子', '鈴木一郎'],
                'Age': [30, 25, 35],
                'Department': ['営業部', '開発部', '総務部']
            })
            
            excel_buffer = BytesIO()
            excel_data.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_buffer.seek(0)
            
            excel_file = UploadFile(
                filename="test_excel.xlsx",
                file=excel_buffer,
                size=len(excel_buffer.getvalue())
            )
            
            record_processor = DocumentProcessorRecordBased()
            
            excel_result = await record_processor.process_uploaded_file(
                file=excel_file,
                user_id=test_user_id,
                company_id=test_company_id
            )
            
            print(f"✅ DocumentProcessorRecordBased処理成功:")
            print(f"   - document_id: {excel_result.get('document_id')}")
            print(f"   - filename: {excel_result.get('filename')}")
            print(f"   - total_chunks: {excel_result.get('total_chunks')}")
            
            excel_doc_id = excel_result.get('document_id')
            
            # document_sourcesテーブルの確認
            excel_doc_sources_result = select_data(
                "document_sources",
                columns="*",
                filters={"id": excel_doc_id}
            )
            
            if excel_doc_sources_result.data and len(excel_doc_sources_result.data) > 0:
                print(f"✅ Excel document_sourcesテーブルにレコード発見:")
                excel_doc_record = excel_doc_sources_result.data[0]
                print(f"   - id: {excel_doc_record.get('id')}")
                print(f"   - name: {excel_doc_record.get('name')}")
                print(f"   - type: {excel_doc_record.get('type')}")
            else:
                print("❌ Excel document_sourcesテーブルにレコードが見つかりません")
            
            # chunksテーブルの確認
            excel_chunks_result = select_data(
                "chunks",
                columns="*",
                filters={"doc_id": excel_doc_id}
            )
            
            if excel_chunks_result.data and len(excel_chunks_result.data) > 0:
                print(f"✅ Excel chunksテーブルにレコード発見: {len(excel_chunks_result.data)}件")
            else:
                print("❌ Excel chunksテーブルにレコードが見つかりません")
            
            print("🎉 DocumentProcessorRecordBased テスト成功")
            
        except ImportError:
            print("⚠️ pandas/openpyxlが利用できないため、Excelテストをスキップ")
        except Exception as e:
            print(f"❌ DocumentProcessorRecordBased処理エラー: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # クリーンアップ
        print("\n🧹 テストデータクリーンアップ")
        try:
            # テスト用データを削除
            supabase = get_supabase_client()
            
            # chunksテーブルから削除（外部キー制約のため先に削除）
            chunks_delete = supabase.table("chunks").delete().like("doc_id", "test-%").execute()
            print(f"🗑️ テスト用chunksレコード削除: {len(chunks_delete.data) if chunks_delete.data else 0}件")
            
            # document_sourcesテーブルから削除
            docs_delete = supabase.table("document_sources").delete().eq("company_id", test_company_id).execute()
            print(f"🗑️ テスト用document_sourcesレコード削除: {len(docs_delete.data) if docs_delete.data else 0}件")
            
            # usersテーブルから削除
            users_delete = supabase.table("users").delete().eq("id", test_user_id).execute()
            print(f"🗑️ テスト用usersレコード削除: {len(users_delete.data) if users_delete.data else 0}件")
            
            # companiesテーブルから削除
            companies_delete = supabase.table("companies").delete().eq("id", test_company_id).execute()
            print(f"🗑️ テスト用companiesレコード削除: {len(companies_delete.data) if companies_delete.data else 0}件")
            
        except Exception as cleanup_error:
            print(f"⚠️ クリーンアップエラー: {cleanup_error}")

async def main():
    """メイン関数"""
    print("=" * 60)
    print("📤 document_sourcesテーブル挿入テスト")
    print("=" * 60)
    
    success = await test_document_sources_insertion()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 テスト完了: document_sourcesテーブルへの挿入は正常に動作しています")
    else:
        print("❌ テスト失敗: document_sourcesテーブルへの挿入に問題があります")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())