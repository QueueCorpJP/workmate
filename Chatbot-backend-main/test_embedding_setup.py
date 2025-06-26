#!/usr/bin/env python3
"""
エンベディングシステム設定確認スクリプト
必要な環境変数とデータベース接続をチェックします
"""

import os
import sys
import logging
from dotenv import load_dotenv

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment_variables():
    """環境変数のチェック"""
    print("🔍 環境変数チェック中...")
    
    # .envファイルの読み込み
    load_dotenv()
    
    # 必要な環境変数リスト
    required_vars = {
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"), 
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD"),
    }
    
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if var_value:
            print(f"  ✅ {var_name}: 設定済み")
        else:
            print(f"  ❌ {var_name}: 未設定")
            missing_vars.append(var_name)
    
    # Google API Keyのチェック（どちらか一つでOK）
    google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if google_api_key:
        print(f"  ✅ Google API Key: 利用可能")
    else:
        print(f"  ❌ Google API Key: GOOGLE_API_KEY または GEMINI_API_KEY が必要")
        if "GOOGLE_API_KEY" in missing_vars:
            missing_vars.remove("GOOGLE_API_KEY")
        if "GEMINI_API_KEY" in missing_vars:
            missing_vars.remove("GEMINI_API_KEY")
        if not google_api_key:
            missing_vars.append("GOOGLE_API_KEY または GEMINI_API_KEY")
    
    return len(missing_vars) == 0, missing_vars

def test_package_imports():
    """必要なパッケージのインポートテスト"""
    print("\n📦 パッケージインポートテスト中...")
    
    try:
        from google import genai
        print("  ✅ google-genai: インポート成功")
    except ImportError as e:
        print(f"  ❌ google-genai: インポートエラー - {e}")
        return False
    
    try:
        import pgvector
        print("  ✅ pgvector: インポート成功")
    except ImportError as e:
        print(f"  ❌ pgvector: インポートエラー - {e}")
        return False
    
    try:
        import psycopg2
        print("  ✅ psycopg2: インポート成功")
    except ImportError as e:
        print(f"  ❌ psycopg2: インポートエラー - {e}")
        return False
    
    return True

def test_database_connection():
    """データベース接続テスト"""
    print("\n🔌 データベース接続テスト中...")
    
    try:
        import psycopg2
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # データベースURL構築
        supabase_url = os.getenv("SUPABASE_URL")
        if supabase_url and "supabase.co" in supabase_url:
            project_id = supabase_url.split("://")[1].split(".")[0]
            db_url = f"postgresql://postgres.{project_id}:{os.getenv('DB_PASSWORD', '')}@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"
        else:
            db_url = os.getenv("DATABASE_URL")
        
        if not db_url:
            print("  ❌ データベースURL: 構築できません")
            return False
        
        # 接続テスト
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # バージョン確認
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"  ✅ PostgreSQL接続: 成功 ({version.split()[0]})")
        
        # pgvector拡張の確認
        cur.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');")
        has_vector = cur.fetchone()[0]
        if has_vector:
            print("  ✅ pgvector拡張: 有効")
        else:
            print("  ⚠️ pgvector拡張: 無効（SQLで有効化が必要）")
        
        # document_embeddingsテーブルの確認
        cur.execute("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'document_embeddings'
            );
        """)
        has_table = cur.fetchone()[0]
        if has_table:
            print("  ✅ document_embeddingsテーブル: 存在")
            
            # カラム構造の確認
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'document_embeddings'
                ORDER BY ordinal_position;
            """)
            columns = cur.fetchall()
            print("    テーブル構造:", [f"{col[0]} ({col[1]})" for col in columns])
        else:
            print("  ❌ document_embeddingsテーブル: 存在しません")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ データベース接続エラー: {e}")
        return False

def test_gemini_api():
    """Gemini API接続テスト"""
    print("\n🤖 Gemini API接続テスト中...")
    
    try:
        from google import genai
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            print("  ❌ APIキー: 未設定")
            return False
        
        client = genai.Client(api_key=api_key)
        
        # テスト埋め込みの生成
        test_text = "これはテスト用のテキストです。"
        response = client.models.embed_content(
            model="gemini-embedding-exp-03-07",
            contents=test_text
        )
        
        if response.embeddings and len(response.embeddings) > 0:
            # 3072次元のベクトルを取得
            full_embedding = response.embeddings[0].values
            # MRL（次元削減）: 3072 → 1536次元に削減
            embedding = full_embedding[:1536]
            print(f"  ✅ エンベディング生成: 成功 (元次元: {len(full_embedding)} → 削減後: {len(embedding)})")
            return True
        else:
            print("  ❌ エンベディング生成: 失敗（レスポンスが空）")
            return False
            
    except Exception as e:
        print(f"  ❌ Gemini API接続エラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("🚀 エンベディングシステム設定確認を開始します...\n")
    
    # 各テストの実行
    env_ok, missing_vars = test_environment_variables()
    packages_ok = test_package_imports()
    db_ok = test_database_connection()
    api_ok = test_gemini_api()
    
    print("\n" + "="*50)
    print("📊 テスト結果まとめ")
    print("="*50)
    
    if env_ok:
        print("✅ 環境変数: すべて設定済み")
    else:
        print(f"❌ 環境変数: 以下が未設定 - {', '.join(missing_vars)}")
    
    print(f"{'✅' if packages_ok else '❌'} パッケージ: {'すべて利用可能' if packages_ok else 'インポートエラーあり'}")
    print(f"{'✅' if db_ok else '❌'} データベース: {'接続可能' if db_ok else '接続エラー'}")
    print(f"{'✅' if api_ok else '❌'} Gemini API: {'利用可能' if api_ok else 'エラー'}")
    
    all_ok = env_ok and packages_ok and db_ok and api_ok
    
    print("\n" + "="*50)
    if all_ok:
        print("🎉 すべてのテストが成功しました！")
        print("エンベディングシステムを使用する準備が整いました。")
        print("\n次のステップ:")
        print("1. python embed_documents.py を実行してエンベディングを生成")
        print("2. チャットシステムでベクトル検索をテスト")
    else:
        print("⚠️ 一部のテストが失敗しました。")
        print("上記のエラーを修正してから再度テストしてください。")
        if not env_ok:
            print("\n💡 .envファイルの作成方法:")
            print("GOOGLE_API_KEY=your_api_key_here")
            print("SUPABASE_URL=your_supabase_url")  
            print("SUPABASE_KEY=your_supabase_key")
            print("DB_PASSWORD=your_db_password")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 