#!/usr/bin/env python3
"""
全埋め込みベクトルを gemini-embedding-exp-03-07 (3072次元) で再生成
- chunksテーブルの全埋め込みを再生成
- 3072次元に統一
- 並列処理で高速化
"""

import sys
import os
import logging
import time
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import google.generativeai as genai
import psycopg2
from psycopg2.extras import RealDictCursor

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

class EmbeddingRegenerator:
    """埋め込みベクトル再生成システム"""
    
    def __init__(self):
        """初期化"""
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model = "models/gemini-embedding-exp-03-07"  # 3072次元モデル
        self.db_url = self._get_db_url()
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
        
        # Gemini APIクライアントの初期化
        genai.configure(api_key=self.api_key)
        
        logger.info(f"✅ 埋め込み再生成システム初期化: モデル={self.model}")
        
    def _get_db_url(self) -> str:
        """データベースURLを構築"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL と SUPABASE_KEY 環境変数が設定されていません")
        
        if "supabase.co" in supabase_url:
            project_id = supabase_url.split("://")[1].split(".")[0]
            return f"postgresql://postgres.{project_id}:{os.getenv('DB_PASSWORD', '')}@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"
        else:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL 環境変数が設定されていません")
            return db_url

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """テキストの埋め込みベクトルを生成 (3072次元)"""
        try:
            if not text or len(text.strip()) == 0:
                logger.warning("空のテキストが渡されました")
                return None
            
            response = genai.embed_content(
                model=self.model,
                content=text
            )
            
            # レスポンスからエンベディングベクトルを取得
            embedding_vector = None
            
            if isinstance(response, dict) and 'embedding' in response:
                embedding_vector = response['embedding']
            elif hasattr(response, 'embedding') and response.embedding:
                embedding_vector = response.embedding
            else:
                logger.error(f"予期しないレスポンス形式: {type(response)}")
                return None
            
            if embedding_vector and len(embedding_vector) > 0:
                logger.debug(f"埋め込み生成完了: {len(embedding_vector)}次元")
                return embedding_vector
            else:
                logger.error("埋め込み生成に失敗しました")
                return None
        
        except Exception as e:
            logger.error(f"埋め込み生成エラー: {e}")
            return None

    def get_all_chunks(self) -> List[Dict]:
        """chunksテーブルから全チャンクを取得"""
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT
                            id,
                            content,
                            doc_id,
                            chunk_index,
                            company_id,
                            CASE
                                WHEN embedding IS NOT NULL THEN vector_dims(embedding)
                                ELSE 0
                            END as current_dim
                        FROM chunks
                        WHERE content IS NOT NULL
                        AND content != ''
                        ORDER BY id
                    """)
                    chunks = cur.fetchall()
                    
                    logger.info(f"📊 取得したチャンク数: {len(chunks)}")
                    
                    # 現在の次元分布を表示
                    dim_counts = {}
                    for chunk in chunks:
                        dim = chunk['current_dim'] or 0
                        dim_counts[dim] = dim_counts.get(dim, 0) + 1
                    
                    logger.info("📊 現在の埋め込み次元分布:")
                    for dim, count in sorted(dim_counts.items()):
                        logger.info(f"  {dim}次元: {count}チャンク")
                    
                    return chunks
        
        except Exception as e:
            logger.error(f"チャンク取得エラー: {e}")
            return []

    def update_chunk_embedding(self, chunk_id: str, embedding: List[float]) -> bool:
        """チャンクの埋め込みベクトルを更新"""
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE chunks 
                        SET embedding = %s::vector
                        WHERE id = %s
                    """, (embedding, chunk_id))
                    
                    if cur.rowcount > 0:
                        conn.commit()
                        return True
                    else:
                        logger.warning(f"チャンクID {chunk_id} の更新に失敗")
                        return False
        
        except Exception as e:
            logger.error(f"埋め込み更新エラー (ID: {chunk_id}): {e}")
            return False

    def process_single_chunk(self, chunk: Dict) -> Dict:
        """単一チャンクの埋め込みを処理"""
        chunk_id = chunk['id']
        content = chunk['content']
        current_dim = chunk['current_dim'] or 0
        
        try:
            # 埋め込み生成
            embedding = self.generate_embedding(content)
            
            if embedding is None:
                return {
                    'chunk_id': chunk_id,
                    'success': False,
                    'error': '埋め込み生成失敗',
                    'current_dim': current_dim,
                    'new_dim': 0
                }
            
            # データベース更新
            success = self.update_chunk_embedding(chunk_id, embedding)
            
            return {
                'chunk_id': chunk_id,
                'success': success,
                'error': None if success else '更新失敗',
                'current_dim': current_dim,
                'new_dim': len(embedding)
            }
        
        except Exception as e:
            return {
                'chunk_id': chunk_id,
                'success': False,
                'error': str(e),
                'current_dim': current_dim,
                'new_dim': 0
            }

    def regenerate_all_embeddings(self, max_workers: int = 3) -> Dict:
        """全埋め込みベクトルを並列で再生成"""
        logger.info("🚀 全埋め込みベクトル再生成開始")
        start_time = time.time()
        
        # 全チャンクを取得
        chunks = self.get_all_chunks()
        if not chunks:
            logger.error("処理対象のチャンクが見つかりません")
            return {'success': False, 'error': 'チャンクなし'}
        
        total_chunks = len(chunks)
        logger.info(f"📝 処理対象: {total_chunks}チャンク")
        
        # 並列処理で埋め込み再生成
        results = []
        success_count = 0
        error_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 全チャンクを並列処理に投入
            future_to_chunk = {
                executor.submit(self.process_single_chunk, chunk): chunk 
                for chunk in chunks
            }
            
            # 結果を収集
            for i, future in enumerate(as_completed(future_to_chunk), 1):
                chunk = future_to_chunk[future]
                
                try:
                    result = future.result(timeout=60)  # 60秒タイムアウト
                    results.append(result)
                    
                    if result['success']:
                        success_count += 1
                        logger.info(f"✅ {i}/{total_chunks} - チャンク {result['chunk_id']}: {result['current_dim']}→{result['new_dim']}次元")
                    else:
                        error_count += 1
                        logger.error(f"❌ {i}/{total_chunks} - チャンク {result['chunk_id']}: {result['error']}")
                    
                    # 進捗表示
                    if i % 10 == 0 or i == total_chunks:
                        progress = (i / total_chunks) * 100
                        logger.info(f"📊 進捗: {i}/{total_chunks} ({progress:.1f}%) - 成功: {success_count}, 失敗: {error_count}")
                
                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ {i}/{total_chunks} - チャンク処理エラー: {e}")
        
        elapsed_time = time.time() - start_time
        
        # 結果サマリー
        logger.info("\n" + "="*60)
        logger.info("📊 埋め込み再生成完了サマリー")
        logger.info("="*60)
        logger.info(f"総処理時間: {elapsed_time:.2f}秒")
        logger.info(f"処理対象: {total_chunks}チャンク")
        logger.info(f"成功: {success_count}チャンク")
        logger.info(f"失敗: {error_count}チャンク")
        logger.info(f"成功率: {(success_count/total_chunks)*100:.1f}%")
        
        # 次元分布の確認
        self.verify_embedding_dimensions()
        
        return {
            'success': True,
            'total_chunks': total_chunks,
            'success_count': success_count,
            'error_count': error_count,
            'elapsed_time': elapsed_time,
            'results': results
        }

    def verify_embedding_dimensions(self):
        """埋め込み次元の確認"""
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT
                            vector_dims(embedding) as dim_count,
                            COUNT(*) as chunk_count
                        FROM chunks
                        WHERE embedding IS NOT NULL
                        GROUP BY vector_dims(embedding)
                        ORDER BY dim_count
                    """)
                    results = cur.fetchall()
                    
                    logger.info("\n📊 更新後の埋め込み次元分布:")
                    for row in results:
                        logger.info(f"  {row['dim_count']}次元: {row['chunk_count']}チャンク")
        
        except Exception as e:
            logger.error(f"次元確認エラー: {e}")

def main():
    """メイン処理"""
    try:
        logger.info("🚀 埋め込みベクトル再生成スクリプト開始")
        
        # 再生成システム初期化
        regenerator = EmbeddingRegenerator()
        
        # 確認プロンプト
        print("\n" + "="*60)
        print("⚠️  重要: 全埋め込みベクトルを再生成します")
        print("="*60)
        print(f"使用モデル: {regenerator.model}")
        print("対象: chunksテーブルの全レコード")
        print("予想次元: 3072次元")
        print("処理時間: 数分〜数十分（データ量による）")
        print("="*60)
        
        confirm = input("続行しますか？ (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            logger.info("処理をキャンセルしました")
            return
        
        # 埋め込み再生成実行
        result = regenerator.regenerate_all_embeddings(max_workers=3)
        
        if result['success']:
            logger.info("🎉 埋め込みベクトル再生成が完了しました！")
        else:
            logger.error("❌ 埋め込みベクトル再生成に失敗しました")
            
    except KeyboardInterrupt:
        logger.info("⚠️ ユーザーによって処理が中断されました")
    except Exception as e:
        logger.error(f"❌ 予期しないエラー: {e}")
        import traceback
        logger.error(f"詳細: {traceback.format_exc()}")

if __name__ == "__main__":
    main()