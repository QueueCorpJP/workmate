#!/usr/bin/env python3
"""
🔄 text-multilingual-embedding-002 (768次元) 埋め込み再生成スクリプト
gemini-embedding-001 (3072次元) から text-multilingual-embedding-002 (768次元) への移行
"""

import os
import sys
import logging
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def regenerate_embeddings():
    """全チャンクの埋め込みを768次元で再生成"""
    try:
        from modules.vertex_ai_embedding import get_vertex_ai_embedding_client
        from supabase import create_client
        
        logger.info("🔄 text-multilingual-embedding-002 埋め込み再生成開始")
        
        # Supabase接続
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("❌ Supabase設定が不足しています")
            return False
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Vertex AI クライアント取得
        embedding_client = get_vertex_ai_embedding_client()
        if not embedding_client:
            logger.error("❌ Vertex AI クライアントの取得に失敗")
            return False
        
        # 全チャンクを取得
        logger.info("📊 既存チャンクデータを取得中...")
        response = supabase.table("chunks").select("id, content").execute()
        
        if not response.data:
            logger.warning("⚠️ 処理対象のチャンクが見つかりません")
            return True
        
        chunks = response.data
        total_chunks = len(chunks)
        logger.info(f"📦 処理対象: {total_chunks}件のチャンク")
        
        # バッチサイズ
        batch_size = 10
        success_count = 0
        error_count = 0
        
        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size
            
            logger.info(f"🔄 バッチ {batch_num}/{total_batches} 処理中... ({len(batch)}件)")
            
            try:
                # バッチで埋め込み生成
                texts = [chunk["content"] for chunk in batch]
                embeddings = embedding_client.generate_embeddings_batch(texts)
                
                # データベース更新
                for j, (chunk, embedding) in enumerate(zip(batch, embeddings)):
                    if embedding and len(embedding) == 768:
                        try:
                            supabase.table("chunks").update({
                                "embedding": embedding
                            }).eq("id", chunk["id"]).execute()
                            success_count += 1
                        except Exception as e:
                            logger.error(f"❌ チャンク {chunk['id']} 更新エラー: {e}")
                            error_count += 1
                    else:
                        logger.error(f"❌ チャンク {chunk['id']} 埋め込み生成失敗")
                        error_count += 1
                
                logger.info(f"✅ バッチ {batch_num} 完了 (成功: {len([e for e in embeddings if e])}/{len(batch)})")
                
            except Exception as e:
                logger.error(f"❌ バッチ {batch_num} 処理エラー: {e}")
                error_count += len(batch)
        
        # 結果サマリー
        logger.info("=" * 60)
        logger.info(f"📊 埋め込み再生成完了")
        logger.info(f"✅ 成功: {success_count}件")
        logger.info(f"❌ 失敗: {error_count}件")
        logger.info(f"📈 成功率: {success_count/(success_count+error_count)*100:.1f}%")
        
        if error_count == 0:
            logger.info("🎉 全ての埋め込みが正常に再生成されました！")
            return True
        else:
            logger.warning(f"⚠️ {error_count}件のエラーがありました")
            return False
            
    except Exception as e:
        logger.error(f"❌ 埋め込み再生成エラー: {e}")
        return False

def verify_embeddings():
    """埋め込みの次元数を確認"""
    try:
        from supabase import create_client
        
        logger.info("🔍 埋め込み次元数確認中...")
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        supabase = create_client(supabase_url, supabase_key)
        
        # サンプルチャンクを取得
        response = supabase.table("chunks").select("id, embedding").limit(5).execute()
        
        if not response.data:
            logger.warning("⚠️ 確認対象のチャンクが見つかりません")
            return
        
        for chunk in response.data:
            if chunk["embedding"]:
                dimensions = len(chunk["embedding"])
                logger.info(f"📏 チャンク {chunk['id'][:8]}...: {dimensions}次元")
            else:
                logger.warning(f"⚠️ チャンク {chunk['id'][:8]}...: 埋め込みなし")
                
    except Exception as e:
        logger.error(f"❌ 埋め込み確認エラー: {e}")

def main():
    """メイン実行関数"""
    logger.info("🚀 text-multilingual-embedding-002 移行開始")
    logger.info("=" * 60)
    
    # 環境変数確認
    embedding_model = os.getenv("EMBEDDING_MODEL")
    if embedding_model != "text-multilingual-embedding-002":
        logger.error(f"❌ EMBEDDING_MODEL が正しく設定されていません: {embedding_model}")
        logger.info("✅ EMBEDDING_MODEL=text-multilingual-embedding-002 に設定してください")
        sys.exit(1)
    
    logger.info(f"✅ 埋め込みモデル: {embedding_model}")
    logger.info("=" * 60)
    
    # 埋め込み再生成実行
    if regenerate_embeddings():
        logger.info("=" * 60)
        verify_embeddings()
        logger.info("=" * 60)
        logger.info("🎉 text-multilingual-embedding-002 移行完了！")
    else:
        logger.error("❌ 移行に失敗しました")
        sys.exit(1)

if __name__ == "__main__":
    main()