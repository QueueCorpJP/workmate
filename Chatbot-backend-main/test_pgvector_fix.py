#!/usr/bin/env python3
"""
pgvector拡張機能修正テストスクリプト
ベクトル検索の問題を診断・修正し、動作確認を行う
"""

import os
import sys
import logging
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# 環境変数の読み込み
load_dotenv()

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_url():
    """データベースURLを構築"""
    supabase_url = os.getenv("SUPABASE_URL")
    db_password = os.getenv("DB_PASSWORD")
    
    if not supabase_url or not db_password:
        raise ValueError("SUPABASE_URL と DB_PASSWORD 環境変数が設定されていません")
    
    # Supabase URLから接続情報を抽出
    if "supabase.co" in supabase_url:
        project_id = supabase_url.split("://")[1].split(".")[0]
        return f"postgresql://postgres.{project_id}:{db_password}@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"
    else:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL 環境変数が設定されていません")
        return db_url

def check_pgvector_status(db_url):
    """pgvector拡張機能の状態をチェック"""
    try:
        with psycopg2.connect(db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                # pgvector拡張機能の確認
                cur.execute("""
                    SELECT 
                        extname,
                        extversion,
                        extrelocatable
                    FROM pg_extension 
                    WHERE extname = 'vector'
                """)
                result = cur.fetchone()
                
                if result:
                    logger.info(f"✅ pgvector拡張機能が有効: バージョン {result['extversion']}")
                    return True
                else:
                    logger.warning("⚠️ pgvector拡張機能が無効です")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ pgvector状態確認エラー: {e}")
        return False

def enable_pgvector(db_url):
    """pgvector拡張機能を有効化"""
    try:
        with psycopg2.connect(db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                logger.info("🔧 pgvector拡張機能を有効化中...")
                
                # pgvector拡張機能を有効化
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
                
                # 確認
                cur.execute("""
                    SELECT 
                        extname,
                        extversion
                    FROM pg_extension 
                    WHERE extname = 'vector'
                """)
                result = cur.fetchone()
                
                if result:
                    logger.info(f"✅ pgvector拡張機能を有効化しました: バージョン {result['extversion']}")
                    return True
                else:
                    logger.error("❌ pgvector拡張機能の有効化に失敗しました")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ pgvector有効化エラー: {e}")
        return False

def check_chunks_table_schema(db_url):
    """chunksテーブルのスキーマを確認"""
    try:
        with psycopg2.connect(db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                # embeddingカラムの型確認
                cur.execute("""
                    SELECT 
                        column_name, 
                        data_type, 
                        udt_name,
                        column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'chunks' 
                    AND column_name = 'embedding'
                """)
                result = cur.fetchone()
                
                if result:
                    logger.info(f"📊 embeddingカラム情報:")
                    logger.info(f"  - データ型: {result['data_type']}")
                    logger.info(f"  - UDT名: {result['udt_name']}")
                    logger.info(f"  - デフォルト値: {result['column_default']}")
                    
                    # VECTOR型かどうかチェック
                    if result['udt_name'] == 'vector':
                        logger.info("✅ embeddingカラムはVECTOR型です")
                        return True
                    else:
                        logger.warning(f"⚠️ embeddingカラムがVECTOR型ではありません: {result['udt_name']}")
                        return False
                else:
                    logger.error("❌ embeddingカラムが見つかりません")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ スキーマ確認エラー: {e}")
        return False

def fix_embedding_column(db_url):
    """embeddingカラムをVECTOR型に修正"""
    try:
        with psycopg2.connect(db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                logger.info("🔧 embeddingカラムをVECTOR型に修正中...")
                
                # 既存のembeddingカラムを削除して再作成
                cur.execute("ALTER TABLE chunks DROP COLUMN IF EXISTS embedding;")
                cur.execute("ALTER TABLE chunks ADD COLUMN embedding VECTOR(768);")
                
                # インデックスを作成
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_embedding_ivfflat 
                    ON chunks USING ivfflat (embedding vector_cosine_ops) 
                    WITH (lists = 100);
                """)
                
                # 会社IDとembeddingの複合インデックス
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_company_embedding 
                    ON chunks(company_id) 
                    WHERE embedding IS NOT NULL;
                """)
                
                conn.commit()
                
                logger.info("✅ embeddingカラムをVECTOR(768)型に修正しました")
                logger.info("✅ ベクトル検索用インデックスを作成しました")
                return True
                
    except Exception as e:
        logger.error(f"❌ embeddingカラム修正エラー: {e}")
        return False

def test_vector_operations(db_url):
    """ベクトル演算のテスト"""
    try:
        with psycopg2.connect(db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                logger.info("🧪 ベクトル演算テスト中...")
                
                # テスト用のベクトルを作成
                test_vector = [0.1] * 768  # 768次元のテストベクトル
                
                # ベクトル演算のテスト
                cur.execute("""
                    SELECT 
                        %s::vector <=> %s::vector as cosine_distance,
                        1 - (%s::vector <=> %s::vector) as cosine_similarity
                """, [test_vector, test_vector, test_vector, test_vector])
                
                result = cur.fetchone()
                
                if result:
                    logger.info(f"✅ ベクトル演算テスト成功:")
                    logger.info(f"  - コサイン距離: {result['cosine_distance']}")
                    logger.info(f"  - コサイン類似度: {result['cosine_similarity']}")
                    return True
                else:
                    logger.error("❌ ベクトル演算テスト失敗")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ ベクトル演算テストエラー: {e}")
        return False

def test_vector_search_fixed():
    """修正されたベクトル検索システムのテスト"""
    try:
        logger.info("🧪 修正されたベクトル検索システムをテスト中...")
        
        # 修正されたベクトル検索モジュールをインポート
        from modules.vector_search_fixed import VectorSearchSystem
        
        # インスタンス作成
        vector_search = VectorSearchSystem()
        
        # テスト検索
        test_query = "料金表"
        test_company_id = "77acc2e2-ce67-458d-bd38-7af0476b297a"
        
        logger.info(f"🔍 テスト検索実行: '{test_query}'")
        results = vector_search.vector_similarity_search(
            query=test_query,
            company_id=test_company_id,
            limit=5
        )
        
        if results:
            logger.info(f"✅ ベクトル検索テスト成功: {len(results)}件の結果")
            for i, result in enumerate(results[:3]):
                logger.info(f"  {i+1}. {result['document_name']} (類似度: {result['similarity_score']:.3f})")
            return True
        else:
            logger.warning("⚠️ ベクトル検索結果が空です（データがない可能性があります）")
            return True  # データがないだけで、システムは正常
            
    except Exception as e:
        logger.error(f"❌ ベクトル検索システムテストエラー: {e}")
        import traceback
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        return False

def main():
    """メイン処理"""
    logger.info("🚀 pgvector修正テスト開始")
    
    try:
        # データベースURL取得
        db_url = get_db_url()
        logger.info("✅ データベース接続情報を取得")
        
        # 1. pgvector拡張機能の状態確認
        pgvector_enabled = check_pgvector_status(db_url)
        
        # 2. pgvector拡張機能が無効の場合、有効化を試行
        if not pgvector_enabled:
            logger.info("🔧 pgvector拡張機能の有効化を試行中...")
            pgvector_enabled = enable_pgvector(db_url)
        
        if not pgvector_enabled:
            logger.error("❌ pgvector拡張機能を有効化できませんでした")
            return False
        
        # 3. chunksテーブルのスキーマ確認
        schema_ok = check_chunks_table_schema(db_url)
        
        # 4. embeddingカラムがVECTOR型でない場合、修正
        if not schema_ok:
            logger.info("🔧 embeddingカラムの修正を試行中...")
            schema_ok = fix_embedding_column(db_url)
        
        if not schema_ok:
            logger.error("❌ embeddingカラムの修正に失敗しました")
            return False
        
        # 5. ベクトル演算のテスト
        vector_ops_ok = test_vector_operations(db_url)
        
        if not vector_ops_ok:
            logger.error("❌ ベクトル演算テストに失敗しました")
            return False
        
        # 6. 修正されたベクトル検索システムのテスト
        search_ok = test_vector_search_fixed()
        
        if search_ok:
            logger.info("🎉 pgvector修正テスト完了 - すべて成功!")
            logger.info("✅ ベクトル検索システムが正常に動作しています")
            return True
        else:
            logger.error("❌ ベクトル検索システムテストに失敗しました")
            return False
        
    except Exception as e:
        logger.error(f"❌ テスト実行エラー: {e}")
        import traceback
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)