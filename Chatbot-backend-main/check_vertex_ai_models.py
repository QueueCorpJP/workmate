#!/usr/bin/env python3
"""
🔍 Vertex AI で利用可能なembeddingモデルを確認するスクリプト
"""

import os
import logging
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_vertex_ai_models():
    """Vertex AIで利用可能なモデルを確認"""
    try:
        import vertexai
        from vertexai.language_models import TextEmbeddingModel
        
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "workmate-462302")
        location = "us-central1"
        
        logger.info(f"🔍 Vertex AI初期化中... (Project: {project_id}, Location: {location})")
        
        # Vertex AI初期化
        vertexai.init(project=project_id, location=location)
        
        # 試すモデル名のリスト
        models_to_test = [
            "gemini-embedding-001",
            "text-embedding-004", 
            "textembedding-gecko@003",
            "textembedding-gecko@002",
            "textembedding-gecko@001",
            "text-multilingual-embedding-002"
        ]
        
        available_models = []
        
        for model_name in models_to_test:
            try:
                logger.info(f"🧪 {model_name} をテスト中...")
                model = TextEmbeddingModel.from_pretrained(model_name)
                
                # テスト用のテキスト
                test_text = "これはテスト用のテキストです。"
                embeddings = model.get_embeddings([test_text])
                
                if embeddings and len(embeddings) > 0:
                    embedding_vector = embeddings[0].values
                    logger.info(f"✅ {model_name}: {len(embedding_vector)}次元のembedding生成成功")
                    available_models.append((model_name, len(embedding_vector)))
                else:
                    logger.error(f"❌ {model_name}: 無効なレスポンス")
                    
            except Exception as e:
                logger.error(f"❌ {model_name} テストエラー: {e}")
        
        logger.info("=" * 60)
        logger.info(f"🎯 利用可能なVertex AI Embeddingモデル: {len(available_models)}")
        for model_name, dimensions in available_models:
            logger.info(f"  - {model_name}: {dimensions}次元")
        
        return available_models
        
    except ImportError:
        logger.error("❌ Vertex AI ライブラリがインストールされていません")
        logger.info("pip install google-cloud-aiplatform でインストールしてください")
        return []
    except Exception as e:
        logger.error(f"❌ Vertex AI確認中にエラー: {e}")
        return []

def main():
    """メイン実行関数"""
    logger.info("🚀 Vertex AI 利用可能モデル確認開始")
    logger.info("=" * 60)
    
    # 環境変数確認
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    service_account = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if not project_id:
        logger.error("❌ GOOGLE_CLOUD_PROJECT 環境変数が設定されていません")
        return
    
    if not service_account or not os.path.exists(service_account):
        logger.error(f"❌ サービスアカウントファイルが見つかりません: {service_account}")
        return
    
    logger.info(f"✅ Project ID: {project_id}")
    logger.info(f"✅ Service Account: {service_account}")
    logger.info("=" * 60)
    
    # 利用可能なモデルを確認
    available_models = check_vertex_ai_models()
    
    if available_models:
        logger.info("=" * 60)
        logger.info("💡 推奨設定:")
        
        # 3072次元のモデルを探す
        high_dim_models = [model for model, dim in available_models if dim >= 3000]
        if high_dim_models:
            recommended = high_dim_models[0]
            logger.info(f"✅ 高次元モデル推奨: {recommended}")
            logger.info(f"   EMBEDDING_MODEL={recommended}")
        else:
            # 最初に見つかったモデルを推奨
            recommended = available_models[0][0]
            logger.info(f"✅ 利用可能モデル: {recommended}")
            logger.info(f"   EMBEDDING_MODEL={recommended}")
    else:
        logger.error("❌ 利用可能なVertex AI embeddingモデルが見つかりませんでした")

if __name__ == "__main__":
    main()