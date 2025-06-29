#!/usr/bin/env python3
"""
修正されたsupabase_adapterをテストするスクリプト
"""

import os
import sys
import uuid
from datetime import datetime

# 修正されたsupabase_adapterをインポート
from supabase_adapter import insert_data, select_data, refresh_schema_cache

def test_document_sources_insertion():
    """document_sourcesテーブルへの挿入をテスト"""
    try:
        print("🧪 修正されたsupabase_adapterのテスト開始...")
        
        # 既存のdocument_sourcesからユーザーIDとcompany_idを取得
        existing_docs = select_data("document_sources", "uploaded_by, company_id")
        
        if not existing_docs or not existing_docs.data:
            print("❌ 既存のdocument_sourcesデータが見つかりません")
            return False
            
        existing_doc = existing_docs.data[0]
        user_id = existing_doc["uploaded_by"]
        company_id = existing_doc["company_id"]
        
        print(f"📋 既存データから取得: user_id={user_id}, company_id={company_id}")
        
        # テストデータを作成
        test_doc_id = str(uuid.uuid4())
        test_data = {
            "id": test_doc_id,
            "name": "test_fixed_adapter.txt",
            "type": "Text",
            "page_count": 1,
            "uploaded_by": user_id,
            "company_id": company_id,
            "uploaded_at": datetime.now().isoformat(),
            "active": True,
            "parent_id": None,
            "doc_id": test_doc_id  # ドキュメント識別子として自身のIDを設定
        }
        
        # specialコラムは絶対に設定しない（ユーザーの要求通り）
        
        print(f"🔄 テストデータでdocument_sourcesテーブルへの挿入をテスト...")
        
        # データを挿入してみる（自動リトライ機能付き）
        result = insert_data("document_sources", test_data)
        
        if result and result.data:
            print(f"✅ テスト挿入成功!")
            
            # 挿入したテストデータを削除
            from supabase_adapter import delete_data
            delete_result = delete_data("document_sources", {"id": test_data["id"]})
            if delete_result:
                print(f"🗑️ テストデータ削除完了")
            
            print(f"🎉 修正されたsupabase_adapterは正常に動作しています！")
            return True
        else:
            print(f"❌ テスト挿入失敗")
            return False
            
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
        
        return False

def test_schema_cache_refresh():
    """スキーマキャッシュのリフレッシュ機能をテスト"""
    try:
        print("🔄 スキーマキャッシュリフレッシュ機能のテスト...")
        
        # スキーマキャッシュを手動でリフレッシュ
        client = refresh_schema_cache()
        
        if client:
            print("✅ スキーマキャッシュリフレッシュ成功")
            return True
        else:
            print("❌ スキーマキャッシュリフレッシュ失敗")
            return False
            
    except Exception as e:
        print(f"❌ スキーマキャッシュリフレッシュエラー: {e}")
        return False

def main():
    print("🔧 修正されたSupabase Adapter テストツール")
    print("=" * 50)
    
    # スキーマキャッシュリフレッシュテスト
    cache_test = test_schema_cache_refresh()
    
    # document_sources挿入テスト
    insertion_test = test_document_sources_insertion()
    
    print("\n📊 テスト結果:")
    print(f"  - スキーマキャッシュリフレッシュ: {'✅ 成功' if cache_test else '❌ 失敗'}")
    print(f"  - document_sources挿入: {'✅ 成功' if insertion_test else '❌ 失敗'}")
    
    if cache_test and insertion_test:
        print("\n🎉 すべてのテストが成功しました！")
        print("📝 アプリケーションサーバーを再起動して、ファイルアップロード機能を再試行してください。")
        return True
    else:
        print("\n❌ 一部のテストが失敗しました。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)