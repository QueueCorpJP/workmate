#!/usr/bin/env python3
"""
並列ベクトル検索システムの修正テスト
- client属性エラーの修正確認
- データベース接続の確認
- エンベディング生成の確認
"""

import sys
import os
import logging
import asyncio
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 環境変数の読み込み
load_dotenv()

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_parallel_vector_search_initialization():
    """並列ベクトル検索システムの初期化テスト"""
    try:
        from modules.parallel_vector_search import ParallelVectorSearchSystem
        
        logger.info("🧪 並列ベクトル検索システム初期化テスト開始")
        
        # インスタンス作成
        search_system = ParallelVectorSearchSystem()
        
        logger.info("✅ 並列ベクトル検索システム初期化成功")
        return search_system
        
    except Exception as e:
        logger.error(f"❌ 並列ベクトル検索システム初期化失敗: {e}")
        import traceback
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        return None

def test_database_connection():
    """データベース接続テスト"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        logger.info("🧪 データベース接続テスト開始")
        
        # 環境変数から接続情報を取得
        supabase_url = os.getenv("SUPABASE_URL")
        db_password = os.getenv("DB_PASSWORD")
        
        if not supabase_url or not db_password:
            logger.error("❌ 環境変数が不足しています")
            return False
        
        # 接続URL構築
        project_id = supabase_url.split("://")[1].split(".")[0]
        db_url = f"postgresql://postgres.{project_id}:{db_password}@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"
        
        logger.info(f"接続先: {project_id}.supabase.co")
        
        # 接続テスト
        with psycopg2.connect(db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 as test")
                result = cur.fetchone()
                
                if result and result['test'] == 1:
                    logger.info("✅ データベース接続成功")
                    
                    # chunksテーブルの存在確認
                    cur.execute("""
                        SELECT COUNT(*) as chunk_count 
                        FROM chunks 
                        WHERE embedding IS NOT NULL
                    """)
                    chunk_result = cur.fetchone()
                    logger.info(f"📊 埋め込み済みチャンク数: {chunk_result['chunk_count']}")
                    
                    return True
                else:
                    logger.error("❌ データベース接続テスト失敗")
                    return False
        
    except Exception as e:
        logger.error(f"❌ データベース接続エラー: {e}")
        import traceback
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        return False

def test_embedding_generation():
    """エンベディング生成テスト"""
    try:
        import google.generativeai as genai
        
        logger.info("🧪 エンベディング生成テスト開始")
        
        # API設定
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("❌ Google API Key が設定されていません")
            return False
        
        genai.configure(api_key=api_key)
        model = "models/gemini-embedding-exp-03-07"
        
        # テストクエリ
        test_query = "テスト用のクエリです"
        
        logger.info(f"テストクエリ: {test_query}")
        
        # エンベディング生成
        response = genai.embed_content(
            model=model,
            content=test_query
        )
        
        # レスポンス解析
        embedding_vector = None
        
        if isinstance(response, dict) and 'embedding' in response:
            embedding_vector = response['embedding']
        elif hasattr(response, 'embedding') and response.embedding:
            embedding_vector = response.embedding
        else:
            logger.error(f"❌ 予期しないレスポンス形式: {type(response)}")
            return False
        
        if embedding_vector and len(embedding_vector) > 0:
            logger.info(f"✅ エンベディング生成成功: {len(embedding_vector)}次元")
            return True
        else:
            logger.error("❌ エンベディング生成失敗")
            return False
        
    except Exception as e:
        logger.error(f"❌ エンベディング生成エラー: {e}")
        import traceback
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        return False

def test_sync_parallel_search():
    """同期並列検索テスト"""
    try:
        logger.info("🧪 同期並列検索テスト開始")
        
        # 並列ベクトル検索システム初期化
        search_system = test_parallel_vector_search_initialization()
        if not search_system:
            return False
        
        # テストクエリ
        test_query = "5000円以下"
        company_id = "77acc2e2-ce67-458d-bd38-7af0476b297a"
        
        logger.info(f"テストクエリ: {test_query}")
        logger.info(f"会社ID: {company_id}")
        
        # 同期並列検索実行
        result = search_system.parallel_comprehensive_search_sync(
            query=test_query,
            company_id=company_id,
            max_results=10
        )
        
        if result:
            logger.info(f"✅ 同期並列検索成功: {len(result)}文字の結果")
            logger.info(f"結果の先頭200文字: {result[:200]}...")
            return True
        else:
            logger.warning("⚠️ 同期並列検索は成功したが、結果が空です")
            return True  # エラーではないので成功とする
        
    except Exception as e:
        logger.error(f"❌ 同期並列検索エラー: {e}")
        import traceback
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        return False

async def test_async_parallel_search():
    """非同期並列検索テスト"""
    try:
        logger.info("🧪 非同期並列検索テスト開始")
        
        # 並列ベクトル検索システム初期化
        search_system = test_parallel_vector_search_initialization()
        if not search_system:
            return False
        
        # テストクエリ
        test_query = "5000円以下"
        company_id = "77acc2e2-ce67-458d-bd38-7af0476b297a"
        
        logger.info(f"テストクエリ: {test_query}")
        logger.info(f"会社ID: {company_id}")
        
        # 非同期並列検索実行
        result = await search_system.parallel_comprehensive_search(
            query=test_query,
            company_id=company_id,
            max_results=10
        )
        
        if result:
            logger.info(f"✅ 非同期並列検索成功: {len(result)}文字の結果")
            logger.info(f"結果の先頭200文字: {result[:200]}...")
            return True
        else:
            logger.warning("⚠️ 非同期並列検索は成功したが、結果が空です")
            return True  # エラーではないので成功とする
        
    except Exception as e:
        logger.error(f"❌ 非同期並列検索エラー: {e}")
        import traceback
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        return False

def main():
    """メインテスト実行"""
    logger.info("🚀 並列ベクトル検索修正テスト開始")
    
    test_results = []
    
    # 1. 初期化テスト
    logger.info("\n" + "="*50)
    logger.info("1. 初期化テスト")
    logger.info("="*50)
    init_result = test_parallel_vector_search_initialization()
    test_results.append(("初期化", init_result is not None))
    
    # 2. データベース接続テスト
    logger.info("\n" + "="*50)
    logger.info("2. データベース接続テスト")
    logger.info("="*50)
    db_result = test_database_connection()
    test_results.append(("データベース接続", db_result))
    
    # 3. エンベディング生成テスト
    logger.info("\n" + "="*50)
    logger.info("3. エンベディング生成テスト")
    logger.info("="*50)
    embedding_result = test_embedding_generation()
    test_results.append(("エンベディング生成", embedding_result))
    
    # 4. 同期並列検索テスト
    logger.info("\n" + "="*50)
    logger.info("4. 同期並列検索テスト")
    logger.info("="*50)
    sync_result = test_sync_parallel_search()
    test_results.append(("同期並列検索", sync_result))
    
    # 5. 非同期並列検索テスト
    logger.info("\n" + "="*50)
    logger.info("5. 非同期並列検索テスト")
    logger.info("="*50)
    async_result = asyncio.run(test_async_parallel_search())
    test_results.append(("非同期並列検索", async_result))
    
    # 結果サマリー
    logger.info("\n" + "="*50)
    logger.info("📊 テスト結果サマリー")
    logger.info("="*50)
    
    for test_name, result in test_results:
        status = "✅ 成功" if result else "❌ 失敗"
        logger.info(f"{test_name}: {status}")
    
    success_count = sum(1 for _, result in test_results if result)
    total_count = len(test_results)
    
    logger.info(f"\n🎯 総合結果: {success_count}/{total_count} テスト成功")
    
    if success_count == total_count:
        logger.info("🎉 すべてのテストが成功しました！")
        return True
    else:
        logger.warning("⚠️ 一部のテストが失敗しました")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)