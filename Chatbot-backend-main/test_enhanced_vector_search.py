"""
強化されたベクトル検索システムのテストスクリプト
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('enhanced_vector_search_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

async def test_enhanced_vector_search():
    """強化ベクトル検索システムのテスト"""
    try:
        # 強化ベクトル検索システムのインポート
        from modules.vector_search_enhanced import get_enhanced_vector_search_instance, enhanced_vector_search_available
        
        # 利用可能性チェック
        if not enhanced_vector_search_available():
            logger.error("❌ 強化ベクトル検索システムが利用できません")
            return False
        
        # インスタンス取得
        search_system = get_enhanced_vector_search_instance()
        if not search_system:
            logger.error("❌ 強化ベクトル検索システムのインスタンス取得に失敗")
            return False
        
        logger.info("✅ 強化ベクトル検索システム初期化成功")
        
        # テストクエリ
        test_queries = [
            "料金について教えてください",
            "申し込み方法を知りたい",
            "問い合わせ先はどこですか",
            "サービスの特徴は何ですか",
            "トラブルが発生した場合の対処法"
        ]
        
        # 各クエリでテスト実行
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n🔍 テスト {i}: '{query}'")
            
            try:
                # 強化ベクトル検索実行
                start_time = datetime.now()
                results = await search_system.enhanced_vector_search(
                    query=query,
                    company_id=None,  # テスト用にNone
                    max_results=10
                )
                end_time = datetime.now()
                
                search_time = (end_time - start_time).total_seconds()
                logger.info(f"⏱️ 検索時間: {search_time:.2f}秒")
                logger.info(f"📊 検索結果数: {len(results)}件")
                
                if results:
                    logger.info("📋 上位3件の結果:")
                    for j, result in enumerate(results[:3], 1):
                        logger.info(f"  {j}. {result.document_name} [チャンク{result.chunk_index}]")
                        logger.info(f"     関連度: {result.relevance_score:.3f}")
                        logger.info(f"     類似度: {result.similarity_score:.3f}")
                        logger.info(f"     品質: {result.quality_score:.3f}")
                        logger.info(f"     コンテキスト: {result.context_bonus:.3f}")
                        logger.info(f"     内容: {result.content[:100]}...")
                else:
                    logger.warning("⚠️ 検索結果が見つかりませんでした")
                
            except Exception as e:
                logger.error(f"❌ テスト {i} でエラー: {e}")
                import traceback
                logger.error(f"詳細エラー: {traceback.format_exc()}")
        
        logger.info("\n✅ 強化ベクトル検索システムのテスト完了")
        return True
        
    except Exception as e:
        logger.error(f"❌ テスト実行エラー: {e}")
        import traceback
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        return False

async def test_enhanced_realtime_rag():
    """強化リアルタイムRAGシステムのテスト"""
    try:
        # 強化リアルタイムRAGシステムのインポート
        from modules.realtime_rag_enhanced import process_question_enhanced_realtime, enhanced_realtime_rag_available
        
        # 利用可能性チェック
        if not enhanced_realtime_rag_available():
            logger.error("❌ 強化リアルタイムRAGシステムが利用できません")
            return False
        
        logger.info("✅ 強化リアルタイムRAGシステム利用可能")
        
        # テストクエリ
        test_queries = [
            "料金プランについて詳しく教えてください",
            "申し込みの手順を教えてください",
            "問題が発生した場合の連絡先を教えてください"
        ]
        
        # 各クエリでテスト実行
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n🚀 RAGテスト {i}: '{query}'")
            
            try:
                # 強化リアルタイムRAG実行
                start_time = datetime.now()
                result = await process_question_enhanced_realtime(
                    question=query,
                    company_id=None,  # テスト用にNone
                    company_name="テスト会社",
                    top_k=15
                )
                end_time = datetime.now()
                
                processing_time = (end_time - start_time).total_seconds()
                logger.info(f"⏱️ 処理時間: {processing_time:.2f}秒")
                
                if result and result.get("status") == "completed":
                    answer = result.get("answer", "")
                    logger.info(f"✅ 回答生成成功: {len(answer)}文字")
                    logger.info(f"📊 使用チャンク数: {result.get('chunks_used', 0)}")
                    logger.info(f"📊 最高関連度: {result.get('top_relevance', 0.0):.3f}")
                    logger.info(f"📊 質問タイプ: {result.get('question_type', 'unknown')}")
                    logger.info(f"📝 回答: {answer[:200]}...")
                else:
                    logger.error(f"❌ RAG処理失敗: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                logger.error(f"❌ RAGテスト {i} でエラー: {e}")
                import traceback
                logger.error(f"詳細エラー: {traceback.format_exc()}")
        
        logger.info("\n✅ 強化リアルタイムRAGシステムのテスト完了")
        return True
        
    except Exception as e:
        logger.error(f"❌ RAGテスト実行エラー: {e}")
        import traceback
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        return False

async def test_comparison_with_original():
    """元のシステムとの比較テスト"""
    try:
        logger.info("\n🔄 元システムとの比較テスト開始")
        
        # 元のシステムのインポート
        from modules.vector_search import get_vector_search_instance, vector_search_available
        from modules.realtime_rag import process_question_realtime, realtime_rag_available
        
        # 強化システムのインポート
        from modules.vector_search_enhanced import get_enhanced_vector_search_instance, enhanced_vector_search_available
        from modules.realtime_rag_enhanced import process_question_enhanced_realtime, enhanced_realtime_rag_available
        
        test_query = "料金について教えてください"
        
        # 元のシステムでテスト
        if vector_search_available():
            logger.info("📊 元のベクトル検索システムでテスト")
            original_search = get_vector_search_instance()
            if original_search:
                start_time = datetime.now()
                original_results = original_search.vector_similarity_search(test_query, limit=10)
                original_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"元システム - 検索時間: {original_time:.2f}秒, 結果数: {len(original_results)}")
        
        # 強化システムでテスト
        if enhanced_vector_search_available():
            logger.info("📊 強化ベクトル検索システムでテスト")
            enhanced_search = get_enhanced_vector_search_instance()
            if enhanced_search:
                start_time = datetime.now()
                enhanced_results = await enhanced_search.enhanced_vector_search(test_query, max_results=10)
                enhanced_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"強化システム - 検索時間: {enhanced_time:.2f}秒, 結果数: {len(enhanced_results)}")
        
        # RAGシステムの比較
        if realtime_rag_available():
            logger.info("📊 元のRAGシステムでテスト")
            start_time = datetime.now()
            original_rag_result = await process_question_realtime(test_query, company_name="テスト会社")
            original_rag_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"元RAG - 処理時間: {original_rag_time:.2f}秒")
            if original_rag_result.get("answer"):
                logger.info(f"元RAG - 回答長: {len(original_rag_result['answer'])}文字")
        
        if enhanced_realtime_rag_available():
            logger.info("📊 強化RAGシステムでテスト")
            start_time = datetime.now()
            enhanced_rag_result = await process_question_enhanced_realtime(test_query, company_name="テスト会社")
            enhanced_rag_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"強化RAG - 処理時間: {enhanced_rag_time:.2f}秒")
            if enhanced_rag_result.get("answer"):
                logger.info(f"強化RAG - 回答長: {len(enhanced_rag_result['answer'])}文字")
        
        logger.info("✅ 比較テスト完了")
        return True
        
    except Exception as e:
        logger.error(f"❌ 比較テスト実行エラー: {e}")
        import traceback
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        return False

async def main():
    """メイン実行関数"""
    logger.info("🚀 強化ベクトル検索システム総合テスト開始")
    logger.info(f"⏰ 開始時刻: {datetime.now()}")
    
    # 環境変数チェック
    required_env_vars = ["GOOGLE_API_KEY", "SUPABASE_URL", "SUPABASE_KEY", "USE_VERTEX_AI"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ 必要な環境変数が設定されていません: {missing_vars}")
        return
    
    logger.info("✅ 環境変数チェック完了")
    
    # テスト実行
    tests = [
        ("強化ベクトル検索システム", test_enhanced_vector_search),
        ("強化リアルタイムRAGシステム", test_enhanced_realtime_rag),
        ("元システムとの比較", test_comparison_with_original)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 {test_name}のテスト開始")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results[test_name] = result
            status = "✅ 成功" if result else "❌ 失敗"
            logger.info(f"📊 {test_name}: {status}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"❌ {test_name}でエラー: {e}")
    
    # 結果サマリー
    logger.info(f"\n{'='*50}")
    logger.info("📊 テスト結果サマリー")
    logger.info(f"{'='*50}")
    
    for test_name, result in results.items():
        status = "✅ 成功" if result else "❌ 失敗"
        logger.info(f"{test_name}: {status}")
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    logger.info(f"\n📈 総合結果: {success_count}/{total_count} テスト成功")
    logger.info(f"⏰ 終了時刻: {datetime.now()}")
    
    if success_count == total_count:
        logger.info("🎉 全テスト成功！強化システムは正常に動作しています。")
    else:
        logger.warning("⚠️ 一部のテストが失敗しました。ログを確認してください。")

if __name__ == "__main__":
    asyncio.run(main())