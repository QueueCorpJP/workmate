#!/usr/bin/env python3
"""
document_sourcesテーブルのスキーマキャッシュ問題を修正するスクリプト（実際のユーザーIDを使用）
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
import uuid
from datetime import datetime

load_dotenv()

def main():
    try:
        # Supabaseクライアントを新しく作成
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        print(f"🔄 Supabaseクライアント初期化中...")
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # 既存のdocument_sourcesからユーザーIDとcompany_idを取得
        existing_docs = supabase.table("document_sources").select("uploaded_by, company_id").limit(1).execute()
        
        if not existing_docs.data:
            print("❌ 既存のdocument_sourcesデータが見つかりません")
            return
            
        existing_doc = existing_docs.data[0]
        user_id = existing_doc["uploaded_by"]
        company_id = existing_doc["company_id"]
        
        print(f"📋 既存データから取得: user_id={user_id}, company_id={company_id}")
        
        # テストデータを作成
        test_data = {
            "id": str(uuid.uuid4()),
            "name": "test_schema_cache_fix.txt",
            "type": "Text",
            "page_count": 1,
            "uploaded_by": user_id,  # 実際のユーザーIDを使用
            "company_id": company_id,  # 実際のcompany_idを使用
            "uploaded_at": datetime.now().isoformat(),
            "active": True,
            "special": "Schema cache test",
            "parent_id": None,
            "doc_id": None
        }
        
        print(f"🧪 テストデータでdocument_sourcesテーブルへの挿入をテスト...")
        
        # データを挿入してみる
        result = supabase.table("document_sources").insert(test_data).execute()
        
        if result and result.data:
            print(f"✅ テスト挿入成功!")
            
            # 挿入したテストデータを削除
            delete_result = supabase.table("document_sources").delete().eq("id", test_data["id"]).execute()
            if delete_result:
                print(f"🗑️ テストデータ削除完了")
            
            print(f"🎉 document_sourcesテーブルのスキーマキャッシュ問題は解決されました！")
            print(f"📝 元のファイルアップロード処理を再試行してください。")
        else:
            print(f"❌ テスト挿入失敗")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        print(f"詳細: {type(e).__name__}")
        
        # エラーの詳細を表示
        if hasattr(e, 'details'):
            print(f"詳細情報: {e.details}")
        if hasattr(e, 'message'):
            print(f"メッセージ: {e.message}")
        if hasattr(e, 'code'):
            print(f"エラーコード: {e.code}")

if __name__ == "__main__":
    main()