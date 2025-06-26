#!/usr/bin/env python3
"""
🔍 利用可能なembeddingモデルを確認するスクリプト
"""

import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# 環境変数読み込み
load_dotenv()

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_available_models():
    """利用可能なモデルを確認"""
    try:
        # API設定
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("❌ GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
            return False
        
        genai.configure(api_key=api_key)
        
        logger.info("🔍 利用可能なモデルを確認中...")
        
        # 全モデルを取得
        models = genai.list_models()
        
        embedding_models = []
        text_models = []
        
        for model in models:
            model_name = model.name
            supported_methods = getattr(model, 'supported_generation_methods', [])
            
            if 'embedContent' in supported_methods:
                embedding_models.append(model_name)
                logger.info(f"📊 Embedding対応: {model_name}")
            elif 'generateContent' in supported_methods:
                text_models.append(model_name)
                logger.info(f"💬 Text生成対応: {model_name}")
        
        logger.info("=" * 60)
        logger.info(f"🎯 Embedding対応モデル数: {len(embedding_models)}")
        for model in embedding_models:
            logger.info(f"  - {model}")
        
        logger.info("=" * 60)
        logger.info(f"💬 Text生成対応モデル数: {len(text_models)}")
        for model in text_models[:5]:  # 最初の5つだけ表示
            logger.info(f"  - {model}")
        if len(text_models) > 5:
            logger.info(f"  ... 他 {len(text_models) - 5} モデル")
        
        return embedding_models
        
    except Exception as e:
        logger.error(f"❌ モデル確認中にエラー: {e}")
        return []

def test_embedding_model(model_name: str):
    """指定されたembeddingモデルをテスト"""
    try:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        
        test_text = "これはテスト用のテキストです。"
        
        logger.info(f"🧪 {model_name} をテスト中...")
        
        response = genai.embed_content(
            model=model_name,
            content=test_text
        )
        
        if response and 'embedding' in response:
            embedding_vector = response['embedding']
            logger.info(f"✅ {model_name}: {len(embedding_vector)}次元のembedding生成成功")
            return True
        else:
            logger.error(f"❌ {model_name}: 無効なレスポンス")
            return False
            
    except Exception as e:
        logger.error(f"❌ {model_name} テストエラー: {e}")
        return False

def main():
    """メイン実行関数"""
    logger.info("🚀 Gemini API 利用可能モデル確認開始")
    logger.info("=" * 60)
    
    # 利用可能なモデルを確認
    embedding_models = check_available_models()
    
    if embedding_models:
        logger.info("=" * 60)
        logger.info("🧪 Embeddingモデルのテスト開始")
        
        for model in embedding_models:
            test_embedding_model(model)
            
        # 推奨モデルの提案
        logger.info("=" * 60)
        logger.info("💡 推奨設定:")
        
        # text-embedding-004が利用可能かチェック
        if "models/text-embedding-004" in embedding_models:
            logger.info("✅ text-embedding-004 が利用可能です（推奨）")
            logger.info("   EMBEDDING_MODEL=text-embedding-004")
        else:
            # 最初に見つかったembeddingモデルを推奨
            if embedding_models:
                recommended = embedding_models[0].replace("models/", "")
                logger.info(f"✅ {recommended} が利用可能です")
                logger.info(f"   EMBEDDING_MODEL={recommended}")
    else:
        logger.error("❌ 利用可能なembeddingモデルが見つかりませんでした")

if __name__ == "__main__":
    main()