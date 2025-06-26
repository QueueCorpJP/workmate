#!/usr/bin/env python3
"""
🧪 Embedding生成修正テストスクリプト
アップロード後にembeddingが生成されない問題の検証・修正テスト
"""

import os
import sys
import asyncio
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

async def test_embedding_generation():
    """embedding生成のテスト"""
    try:
        logger.info("🧪 Embedding生成テスト開始")
        
        # 環境変数チェック
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
        
        # Gemini API初期化
        genai.configure(api_key=api_key)
        embedding_model = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
        
        # 環境変数で設定されたモデルを使用
        if not embedding_model.startswith("models/"):
            embedding_model = f"models/{embedding_model}"
            
        logger.info(f"🧠 使用モデル: {embedding_model}")
        
        # テストテキスト
        test_text = "これはembedding生成のテストです。日本語のテキストが正しく処理されるかを確認します。"
        
        # Embedding生成テスト
        logger.info("📝 テストテキストでembedding生成中...")
        response = genai.embed_content(
            model=embedding_model,
            content=test_text
        )
        
        if response and 'embedding' in response:
            embedding_vector = response['embedding']
            logger.info(f"✅ Embedding生成成功! 次元数: {len(embedding_vector)}")
            logger.info(f"📊 ベクトルの最初の5要素: {embedding_vector[:5]}")
            return True
        else:
            logger.error(f"❌ Embedding生成失敗: レスポンス = {response}")
            return False
            
    except Exception as e:
        logger.error(f"💥 テストエラー: {e}")
        return False

async def check_pending_chunks():
    """embedding未生成のチャンクをチェック"""
    try:
        logger.info("🔍 Embedding未生成チャンクをチェック中...")
        
        supabase = get_supabase_client()
        
        # embedding未生成のチャンクを取得
        chunks_query = supabase.table("chunks").select("id,content,chunk_index,doc_id").is_("embedding", "null").eq("active", True).limit(5)
        chunks_result = chunks_query.execute()
        
        if chunks_result.data:
            logger.info(f"📋 Embedding未生成チャンク: {len(chunks_result.data)}件")
            for chunk in chunks_result.data:
                content_preview = chunk.get("content", "")[:100] + "..." if len(chunk.get("content", "")) > 100 else chunk.get("content", "")
                logger.info(f"  - ID: {chunk['id']}, Index: {chunk.get('chunk_index', 'N/A')}, Content: {content_preview}")
            return chunks_result.data
        else:
            logger.info("✅ Embedding未生成のチャンクはありません")
            return []
            
    except Exception as e:
        logger.error(f"❌ チャンクチェックエラー: {e}")
        return []

async def fix_single_chunk(chunk_data):
    """単一チャンクのembeddingを修正"""
    try:
        chunk_id = chunk_data['id']
        content = chunk_data.get('content', '').strip()
        
        if not content:
            logger.warning(f"⚠️ 空のコンテンツをスキップ: {chunk_id}")
            return False
        
        logger.info(f"🔧 チャンク修正中: {chunk_id}")
        
        # 環境変数取得
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        embedding_model = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
        
        if not embedding_model.startswith("models/"):
            embedding_model = f"models/{embedding_model}"
        
        # Embedding生成
        response = genai.embed_content(
            model=embedding_model,
            content=content
        )
        
        if response and 'embedding' in response:
            embedding_vector = response['embedding']
            
            # データベース更新
            supabase = get_supabase_client()
            update_result = supabase.table("chunks").update({
                "embedding": embedding_vector
            }).eq("id", chunk_id).execute()
            
            if update_result.data:
                logger.info(f"✅ チャンク修正完了: {chunk_id} (次元: {len(embedding_vector)})")
                return True
            else:
                logger.error(f"❌ データベース更新失敗: {chunk_id}")
                return False
        else:
            logger.error(f"❌ Embedding生成失敗: {chunk_id}")
            return False
            
    except Exception as e:
        logger.error(f"❌ チャンク修正エラー: {chunk_id} - {e}")
        return False

async def main():
    """メイン処理"""
    logger.info("🚀 Embedding修正テストスクリプト開始")
    
    # 1. Embedding生成テスト
    if not await test_embedding_generation():
        logger.error("💥 Embedding生成テストに失敗しました")
        return
    
    # 2. 未生成チャンクをチェック
    pending_chunks = await check_pending_chunks()
    
    if not pending_chunks:
        logger.info("🎉 修正が必要なチャンクはありません")
        return
    
    # 3. 最初の1つのチャンクを修正してテスト
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        logger.info("🔧 最初のチャンクを修正します...")
        success = await fix_single_chunk(pending_chunks[0])
        if success:
            logger.info("✅ チャンク修正テスト成功!")
        else:
            logger.error("❌ チャンク修正テスト失敗")
    else:
        logger.info("💡 修正を実行するには --fix オプションを付けて実行してください")
        logger.info("   例: python test_embedding_fix.py --fix")

if __name__ == "__main__":
    asyncio.run(main())