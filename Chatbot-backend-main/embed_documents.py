"""
エンベディング生成・登録スクリプト
Gemini Embedding APIを使用してdocument_sourcesからdocument_embeddingsにベクトルを格納する
"""

import os
import sys
import textwrap
from dotenv import load_dotenv
from google import genai
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
    
    model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-exp-03-07")
    
    return api_key, db_url, model

def chunks(text, chunk_size=8000):
    """テキストをチャンクに分割する（約2000トークン相当）"""
    text = str(text) if text else ""
    for i in range(0, len(text), chunk_size):
        yield text[i:i+chunk_size]

def generate_embeddings():
    """メイン処理：エンベディングを生成してデータベースに保存"""
    try:
        # 環境変数の取得
        api_key, db_url, model = get_env_vars()
        
        # Gemini APIクライアントの初期化
        logger.info(f"Gemini APIクライアント初期化中... モデル: {model}")
        client = genai.Client(api_key=api_key)
        
        # データベース接続
        logger.info("データベースに接続中...")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # まだ埋め込みが無いドキュメントを取得
        logger.info("埋め込みが未生成のドキュメントを検索中...")
        cur.execute("""
            SELECT id, content, name
            FROM document_sources
            WHERE active = true
              AND content IS NOT NULL
              AND content != ''
              AND id NOT IN (
                  SELECT DISTINCT document_id 
                  FROM document_embeddings 
                  WHERE document_id IS NOT NULL
              );
        """)
        rows = cur.fetchall()
        
        if not rows:
            logger.info("✅ 新しく処理すべきドキュメントはありません")
            return
        
        logger.info(f"📄 {len(rows)}個のドキュメントの埋め込みを生成します")
        
        # 埋め込み生成・保存
        records = []
        processed_count = 0
        
        for doc_id, content, name in rows:
            logger.info(f"📋 処理中: {name} (ID: {doc_id})")
            
            try:
                # コンテンツをチャンクに分割
                chunk_list = list(chunks(content, chunk_size=8000))
                logger.info(f"  - {len(chunk_list)}個のチャンクに分割")
                
                for i, chunk_content in enumerate(chunk_list):
                    if not chunk_content.strip():
                        continue
                    
                    # 埋め込み生成
                    logger.info(f"  - チャンク {i+1}/{len(chunk_list)} の埋め込み生成中...")
                    
                    try:
                        response = client.models.embed_content(
                            model=model, 
                            contents=chunk_content
                        )
                        
                        if response.embeddings and len(response.embeddings) > 0:
                            # 3072次元のベクトルを取得
                            full_embedding = response.embeddings[0].values
                            # MRL（次元削減）: 3072 → 1536次元に削減
                            embedding_vector = full_embedding[:1536]
                            snippet = chunk_content[:200] + "..." if len(chunk_content) > 200 else chunk_content
                            
                            # チャンクの場合は一意なIDを生成（document_idとして使用）
                            chunk_doc_id = f"{doc_id}_chunk_{i}" if len(chunk_list) > 1 else doc_id
                            
                            records.append((chunk_doc_id, embedding_vector, snippet))
                            logger.info(f"  - ✅ チャンク {i+1} 完了 (次元: {len(embedding_vector)})")
                        else:
                            logger.warning(f"  - ⚠️ チャンク {i+1} の埋め込み生成に失敗")
                    
                    except Exception as e:
                        logger.error(f"  - ❌ チャンク {i+1} でエラー: {e}")
                        continue
                
                processed_count += 1
                logger.info(f"📄 ドキュメント完了: {name} ({processed_count}/{len(rows)})")
                
            except Exception as e:
                logger.error(f"❌ ドキュメント {name} 処理エラー: {e}")
                continue
        
        # データベースに一括挿入
        if records:
            logger.info(f"💾 {len(records)}個の埋め込みをデータベースに保存中...")
            
            # 実際のテーブル構造に合わせて調整
            # document_embeddings (document_id, embedding, snippet)
            execute_values(cur, """
                INSERT INTO document_embeddings (document_id, embedding, snippet)
                VALUES %s
                ON CONFLICT (document_id) DO UPDATE
                SET embedding = EXCLUDED.embedding,
                    snippet = EXCLUDED.snippet,
                    created_at = CURRENT_TIMESTAMP;
            """, records, template=None, page_size=100)
            
            conn.commit()
            logger.info(f"✅ {len(records)}個の埋め込みを正常に保存しました")
        else:
            logger.warning("⚠️ 保存すべき埋め込みがありませんでした")
        
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
    logger.info("🚀 エンベディング生成スクリプト開始")
    try:
        generate_embeddings()
        logger.info("🎉 エンベディング生成完了")
    except Exception as e:
        logger.error(f"💥 スクリプト実行エラー: {e}")
        sys.exit(1) 