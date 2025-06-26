#!/usr/bin/env python3
"""
🧪 text-embedding-005 モデルテストスクリプト
新しいembeddingモデルの動作確認用
"""

import os
import logging
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai

# 環境変数読み込み
load_dotenv()

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_text_embedding_005():
    """text-embedding-005 モデルのテスト"""
    try:
        # API設定
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("❌ GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
            return False
        
        genai.configure(api_key=api_key)
        
        # テストデータ
        test_texts = [
            "これはテスト用のテキストです。",
            "Hello, this is a test text for embedding generation.",
            "日本語と英語が混在したテキストです。This is mixed language text.",
            "短いテキスト",
            "もう少し長いテキストで、複数の文を含んでいます。このようなテキストでもembeddingが正常に生成されるかをテストします。"
        ]
        
        model_name = "models/text-embedding-005"
        logger.info(f"🧠 {model_name} モデルテスト開始")
        
        success_count = 0
        total_count = len(test_texts)
        
        for i, text in enumerate(test_texts, 1):
            try:
                logger.info(f"📝 テスト {i}/{total_count}: {text[:50]}...")
                
                # embedding生成
                response = await asyncio.to_thread(
                    genai.embed_content,
                    model=model_name,
                    content=text
                )
                
                if response and 'embedding' in response:
                    embedding_vector = response['embedding']
                    logger.info(f"✅ 成功: {len(embedding_vector)}次元のembedding生成")
                    logger.info(f"   最初の5要素: {embedding_vector[:5]}")
                    success_count += 1
                else:
                    logger.error(f"❌ 失敗: 無効なレスポンス")
                
                # API制限対策
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ テスト {i} でエラー: {e}")
        
        # 結果サマリー
        logger.info("=" * 60)
        logger.info(f"🎯 テスト結果: {success_count}/{total_count} 成功")
        logger.info(f"📊 成功率: {success_count/total_count*100:.1f}%")
        
        if success_count == total_count:
            logger.info("🎉 全テスト成功！text-embedding-005 モデルは正常に動作しています")
            return True
        else:
            logger.warning(f"⚠️ {total_count - success_count}件のテストが失敗しました")
            return False
            
    except Exception as e:
        logger.error(f"❌ テスト実行中にエラー: {e}")
        return False

async def test_embedding_dimensions():
    """embedding次元数の確認"""
    try:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        
        model_name = "models/text-embedding-005"
        test_text = "次元数確認用のテストテキスト"
        
        logger.info(f"🔍 {model_name} の次元数確認")
        
        response = await asyncio.to_thread(
            genai.embed_content,
            model=model_name,
            content=test_text
        )
        
        if response and 'embedding' in response:
            embedding_vector = response['embedding']
            dimensions = len(embedding_vector)
            logger.info(f"📏 embedding次元数: {dimensions}")
            
            # 期待される次元数（text-embedding-005は768次元）
            expected_dimensions = 768
            if dimensions == expected_dimensions:
                logger.info(f"✅ 期待される次元数 ({expected_dimensions}) と一致")
                return True
            else:
                logger.warning(f"⚠️ 期待される次元数 ({expected_dimensions}) と異なります")
                return False
        else:
            logger.error("❌ embedding生成に失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 次元数確認中にエラー: {e}")
        return False

async def main():
    """メイン実行関数"""
    logger.info("🚀 text-embedding-005 モデル総合テスト開始")
    logger.info("=" * 60)
    
    # 基本テスト
    basic_test_result = await test_text_embedding_005()
    
    # 次元数テスト
    dimension_test_result = await test_embedding_dimensions()
    
    # 最終結果
    logger.info("=" * 60)
    if basic_test_result and dimension_test_result:
        logger.info("🎉 全テスト成功！text-embedding-005 モデルは正常に動作しています")
        logger.info("✅ システムでtext-embedding-005を使用する準備が整いました")
    else:
        logger.error("❌ 一部のテストが失敗しました")
        logger.error("🔧 設定を確認してください")
    
    return basic_test_result and dimension_test_result

if __name__ == "__main__":
    asyncio.run(main())