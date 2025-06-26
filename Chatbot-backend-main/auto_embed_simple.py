#!/usr/bin/env python3
"""
🧠 簡単な自動Embedding生成スクリプト
Supabaseクライアントを使用してembedding未生成のチャンクを処理
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from supabase_adapter import get_supabase_client

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()

def main():
    """メイン処理"""
    try:
        logger.info("🚀 簡単なEmbedding生成スクリプト開始")
        
        # 環境変数チェック
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
        
        # Gemini API初期化
        genai.configure(api_key=api_key)
        # 3072次元のembeddingモデルを使用（環境変数から取得）
        embedding_model = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
        # 環境変数で設定されたモデルを使用
        if not embedding_model.startswith("models/"):
            embedding_model = f"models/{embedding_model}"
        logger.info(f"🧠 Gemini API初期化完了: {embedding_model} (3072次元)")
        
        # Supabaseクライアント取得
        supabase = get_supabase_client()
        logger.info("✅ Supabaseクライアント取得完了")
        
        # embedding未生成のチャンクを取得（制限付き）
        limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
        logger.info(f"📋 処理制限: {limit}チャンク")
        
        chunks_query = supabase.table("chunks").select("id,content,chunk_index,doc_id").is_("embedding", "null").limit(limit)
        chunks_result = chunks_query.execute()
        
        if not chunks_result.data:
            logger.info("✅ embedding未生成のチャンクはありません")
            return
        
        chunks = chunks_result.data
        logger.info(f"🧩 {len(chunks)}個のチャンクを処理します")
        
        # 統計情報
        stats = {
            "total": len(chunks),
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # 各チャンクを処理
        for i, chunk in enumerate(chunks, 1):
            try:
                logger.info(f"📋 処理中 ({i}/{len(chunks)}): chunk {chunk.get('chunk_index', 'N/A')}")
                
                content = chunk.get("content", "").strip()
                if not content:
                    logger.warning(f"⚠️ 空のコンテンツをスキップ: {chunk['id']}")
                    stats["skipped"] += 1
                    continue
                
                # Embedding生成
                response = genai.embed_content(
                    model=embedding_model,
                    content=content
                )
                
                if response and 'embedding' in response:
                    embedding_vector = response['embedding']
                    
                    # データベース更新
                    update_result = supabase.table("chunks").update({
                        "embedding": embedding_vector
                    }).eq("id", chunk["id"]).execute()
                    
                    if update_result.data:
                        stats["success"] += 1
                        logger.info(f"✅ embedding更新完了: chunk {chunk.get('chunk_index', 'N/A')}")
                    else:
                        stats["failed"] += 1
                        logger.warning(f"⚠️ embedding更新失敗: chunk {chunk.get('chunk_index', 'N/A')}")
                else:
                    stats["failed"] += 1
                    logger.warning(f"⚠️ embedding生成失敗: chunk {chunk.get('chunk_index', 'N/A')}")
                
                # API制限対策
                time.sleep(0.2)
                
            except Exception as chunk_error:
                stats["failed"] += 1
                logger.error(f"❌ chunk処理エラー: {chunk['id']} - {chunk_error}")
                continue
        
        # 結果表示
        success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
        logger.info("=" * 50)
        logger.info("🎉 処理完了 - 結果")
        logger.info("=" * 50)
        logger.info(f"📊 総チャンク数: {stats['total']}")
        logger.info(f"✅ 成功: {stats['success']}")
        logger.info(f"❌ 失敗: {stats['failed']}")
        logger.info(f"⏭️ スキップ: {stats['skipped']}")
        logger.info(f"📈 成功率: {success_rate:.1f}%")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"💥 スクリプト実行エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()