#!/usr/bin/env python3
"""
Chunks Active Column Fix Script
このスクリプトは chunks テーブルの active カラム問題を修正します
"""

import os
import sys
from supabase_adapter import get_supabase_client

def check_chunks_table_schema():
    """chunksテーブルのスキーマを確認する"""
    try:
        supabase = get_supabase_client()
        
        # chunksテーブルの構造を確認
        print("🔍 chunksテーブルの構造を確認中...")
        
        # まず、chunksテーブルからサンプルデータを取得してカラム構造を確認
        result = supabase.table("chunks").select("*").limit(1).execute()
        
        if result.data:
            print("✅ chunksテーブルが存在します")
            print(f"📋 利用可能なカラム: {list(result.data[0].keys())}")
            
            # activeカラムが存在するかチェック
            if 'active' in result.data[0]:
                print("⚠️ chunksテーブルにactiveカラムが存在します - これが問題の原因です")
                return True
            else:
                print("✅ chunksテーブルにactiveカラムは存在しません - 正常です")
                return False
        else:
            print("⚠️ chunksテーブルにデータがありません")
            # 空のテーブルの場合、スキーマ情報を別の方法で取得
            try:
                # 空のクエリでエラーメッセージからカラム情報を推測
                test_result = supabase.table("chunks").select("active").limit(1).execute()
                print("⚠️ activeカラムが存在する可能性があります")
                return True
            except Exception as e:
                if "column chunks.active does not exist" in str(e):
                    print("✅ activeカラムは存在しません - 正常です")
                    return False
                else:
                    print(f"❌ スキーマ確認中にエラー: {str(e)}")
                    return False
                    
    except Exception as e:
        print(f"❌ chunksテーブル確認エラー: {str(e)}")
        if "column chunks.active does not exist" in str(e):
            print("✅ activeカラムは存在しません - 正常です")
            return False
        return True

def check_document_sources_schema():
    """document_sourcesテーブルのactiveカラムを確認する"""
    try:
        supabase = get_supabase_client()
        
        print("🔍 document_sourcesテーブルのactiveカラムを確認中...")
        
        result = supabase.table("document_sources").select("active").limit(1).execute()
        print("✅ document_sourcesテーブルのactiveカラムは正常に存在します")
        return True
        
    except Exception as e:
        print(f"❌ document_sourcesテーブル確認エラー: {str(e)}")
        return False

def test_fixed_query():
    """修正されたクエリをテストする"""
    try:
        supabase = get_supabase_client()
        
        print("🧪 修正されたクエリをテスト中...")
        
        # まずアクティブなdocument_sourcesを取得
        doc_sources = supabase.table("document_sources").select("id").eq("active", True).limit(1).execute()
        
        if doc_sources.data:
            doc_id = doc_sources.data[0]['id']
            print(f"📄 テスト用ドキュメントID: {doc_id}")
            
            # 修正されたクエリ: activeカラムを使わずにchunksを取得
            chunks_result = supabase.table("chunks").select("content,chunk_index").eq("doc_id", doc_id).order("chunk_index").execute()
            
            print(f"✅ chunksクエリ成功: {len(chunks_result.data)}個のチャンクを取得")
            return True
        else:
            print("⚠️ アクティブなドキュメントが見つかりません")
            return False
            
    except Exception as e:
        print(f"❌ クエリテストエラー: {str(e)}")
        return False
        return False

def main():
    """メイン実行関数"""
    print("🔧 Chunks Active Column Fix Script")
    print("=" * 50)
    
    # 1. chunksテーブルのスキーマ確認
    chunks_has_active = check_chunks_table_schema()
    
    # 2. document_sourcesテーブルの確認
    doc_sources_ok = check_document_sources_schema()
    
    # 3. 修正されたクエリのテスト
    query_test_ok = test_fixed_query()
    
    print("\n📊 診断結果:")
    print("=" * 50)
    
    if not chunks_has_active and doc_sources_ok and query_test_ok:
        print("✅ すべて正常です！")
        print("💡 問題が解決されている可能性があります。")
        print("💡 アプリケーションを再起動してキャッシュをクリアしてください。")
    elif chunks_has_active:
        print("⚠️ chunksテーブルにactiveカラムが存在します")
        print("💡 これが問題の原因です。データベース管理者に連絡してactiveカラムを削除してください。")
        print("💡 または、コードでactiveカラムを使用しないように修正が必要です。")
    else:
        print("❌ 他の問題が存在する可能性があります")
        print("💡 ログを確認して詳細なエラー情報を調べてください。")
    
    print("\n🔄 推奨アクション:")
    print("1. アプリケーションサーバーを再起動")
    print("2. Python キャッシュファイル (__pycache__) を削除")
    print("3. 必要に応じてデータベーススキーマを修正")

if __name__ == "__main__":
    main()