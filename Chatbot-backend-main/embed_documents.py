"""
エンベディング生成・登録スクリプト
🧠 各チャンクを Gemini Flash Embedding API（Vectors API）でベクトル化（768次元）
モデル: gemini-embedding-exp-03-07
"""

import os
import sys
import textwrap
from dotenv import load_dotenv
import google.generativeai as genai
import psycopg2
from psycopg2.extras import execute_values
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv()

def get_env_vars():
    """環境変数を取得して検証する"""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
    
    # Supabase接続情報を構築
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL と SUPABASE_KEY 環境変数が設定されていません")
    
    # PostgreSQL接続URLを構築（Supabase用）
    # Supabase URLから接続情報を抽出
    if "supabase.co" in supabase_url:
        project_id = supabase_url.split("://")[1].split(".")[0]
        db_url = f"postgresql://postgres.{project_id}:{os.getenv('DB_PASSWORD', '')}@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"
    else:
        # カスタムデータベースURLの場合
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL 環境変数が設定されていません")
    
    # ✅ 修正: Gemini Flash Embedding API（768次元）
    model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-exp-03-07")
    
    return api_key, db_url, model

def generate_embeddings():
    """メイン処理：chunksテーブルからエンベディングを生成してchunksテーブルに保存"""
    try:
        # 環境変数の取得
        api_key, db_url, model = get_env_vars()
        
        # Gemini APIクライアントの初期化
        logger.info(f"🧠 Gemini Flash Embedding API初期化中... モデル: {model}")
        genai.configure(api_key=api_key)
        
        # データベース接続
        logger.info("データベースに接続中...")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # ✅ 修正: chunksテーブルから埋め込みが未生成のチャンクを取得
        logger.info("埋め込みが未生成のチャンクを検索中...")
        cur.execute("""
            SELECT id, doc_id, chunk_index, content
            FROM chunks
            WHERE content IS NOT NULL
              AND content != ''
              AND embedding IS NULL;
        """)
        rows = cur.fetchall()
        
        if not rows:
            logger.info("✅ 新しく処理すべきチャンクはありません")
            return
        
        logger.info(f"🧩 {len(rows)}個のチャンクの埋め込みを生成します")
        
        # 埋め込み生成・保存
        processed_count = 0
        
        for chunk_id, doc_id, chunk_index, content in rows:
            logger.info(f"📋 処理中: Chunk {chunk_index} (ID: {chunk_id})")
            
            try:
                if not content.strip():
                    logger.warning(f"⚠️ 空のコンテンツをスキップ: {chunk_id}")
                    continue
                
                # 🧠 Gemini Flash Embedding API でベクトル化（768次元）
                logger.info(f"  - チャンク {chunk_index} のエンベディング生成中...")
                
                response = genai.embed_content(
                    model=model,
                    content=content
                )
                
                if response and 'embedding' in response:
                    # 768次元のベクトルを取得
                    embedding_vector = response['embedding']
                    logger.info(f"  - ✅ エンベディング生成完了 (次元: {len(embedding_vector)})")
                    
                    # chunksテーブルのembeddingカラムを更新
                    cur.execute("""
                        UPDATE chunks 
                        SET embedding = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (embedding_vector, chunk_id))
                    
                    processed_count += 1
                    logger.info(f"📄 チャンク完了: {chunk_index} ({processed_count}/{len(rows)})")
                else:
                    logger.warning(f"  - ⚠️ チャンク {chunk_index} のエンベディング生成に失敗")
            
            except Exception as e:
                logger.error(f"  - ❌ チャンク {chunk_index} でエラー: {e}")
                continue
        
        # データベースに変更をコミット
        if processed_count > 0:
            conn.commit()
            logger.info(f"✅ {processed_count}個のチャンクのエンベディングを正常に保存しました")
        else:
            logger.warning("⚠️ 保存すべきエンベディングがありませんでした")
        
    except Exception as e:
        logger.error(f"❌ メイン処理でエラー: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise
    
    finally:
        # リソースのクリーンアップ
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()
        logger.info("🔒 データベース接続を閉じました")

if __name__ == "__main__":
    logger.info("🚀 Gemini Flash Embedding生成スクリプト開始")
    try:
        generate_embeddings()
        logger.info("🎉 エンベディング生成完了")
    except Exception as e:
        logger.error(f"💥 スクリプト実行エラー: {e}")
        sys.exit(1) 