"""
🧠 強化版エンベディング生成スクリプト
chunksテーブル対応・バッチ処理・エラー回復機能付き

機能:
- chunksテーブルからembedding未生成のチャンクを検索
- Gemini Flash Embedding API（768次元）でベクトル化
- バッチ処理でパフォーマンス向上
- エラー回復・リトライ機能
- 進捗表示・統計レポート
"""

import os
import sys
import time
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from dotenv import load_dotenv
import google.generativeai as genai
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('embedding_generation.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()

class EnhancedEmbeddingGenerator:
    """強化版エンベディング生成クラス"""
    
    def __init__(self):
        self.gemini_client = None
        self.db_connection = None
        self.embedding_model = "gemini-embedding-exp-03-07"
        self.batch_size = 10  # バッチサイズ
        self.max_retries = 3  # 最大リトライ回数
        self.retry_delay = 2  # リトライ間隔（秒）
        
        # 統計情報
        self.stats = {
            "total_chunks": 0,
            "processed_chunks": 0,
            "successful_embeddings": 0,
            "failed_embeddings": 0,
            "skipped_chunks": 0,
            "start_time": None,
            "end_time": None
        }
    
    def _get_env_vars(self) -> Dict[str, str]:
        """環境変数を取得・検証"""
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
        
        # Supabase接続情報
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL と SUPABASE_KEY 環境変数が設定されていません")
        
        # PostgreSQL接続URL構築
        if "supabase.co" in supabase_url:
            project_id = supabase_url.split("://")[1].split(".")[0]
            db_url = f"postgresql://postgres.{project_id}:{os.getenv('DB_PASSWORD', '')}@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"
        else:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL 環境変数が設定されていません")
        
        return {
            "api_key": api_key,
            "db_url": db_url,
            "model": os.getenv("EMBEDDING_MODEL", self.embedding_model)
        }
    
    def _init_gemini_client(self, api_key: str):
        """Gemini APIクライアント初期化"""
        try:
            genai.configure(api_key=api_key)
            self.gemini_client = genai
            logger.info(f"🧠 Gemini APIクライアント初期化完了: {self.embedding_model}")
        except Exception as e:
            logger.error(f"❌ Gemini APIクライアント初期化エラー: {e}")
            raise
    
    def _init_database(self, db_url: str):
        """データベース接続初期化"""
        try:
            self.db_connection = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
            logger.info("✅ データベース接続完了")
        except Exception as e:
            logger.error(f"❌ データベース接続エラー: {e}")
            raise
    
    def _get_pending_chunks(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """embedding未生成のチャンクを取得"""
        try:
            cursor = self.db_connection.cursor()
            
            query = """
                SELECT 
                    c.id,
                    c.doc_id,
                    c.chunk_index,
                    c.content,
                    c.company_id,
                    ds.name as document_name
                FROM chunks c
                LEFT JOIN document_sources ds ON c.doc_id = ds.id
                WHERE c.content IS NOT NULL
                  AND c.content != ''
                  AND c.embedding IS NULL
                ORDER BY c.created_at ASC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            chunks = cursor.fetchall()
            
            logger.info(f"📋 embedding未生成チャンク: {len(chunks)}件")
            return [dict(chunk) for chunk in chunks]
            
        except Exception as e:
            logger.error(f"❌ チャンク取得エラー: {e}")
            raise
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    async def _generate_embedding_with_retry(self, text: str, chunk_id: str) -> Optional[List[float]]:
        """リトライ機能付きembedding生成"""
        for attempt in range(self.max_retries):
            try:
                if not text or not text.strip():
                    logger.warning(f"⚠️ 空のテキスト: {chunk_id}")
                    return None
                
                response = self.gemini_client.embed_content(
                    model=self.embedding_model,
                    content=text.strip()
                )
                
                if response and 'embedding' in response:
                    embedding_vector = response['embedding']
                    logger.debug(f"✅ embedding生成成功: {chunk_id} (次元: {len(embedding_vector)})")
                    return embedding_vector
                else:
                    logger.warning(f"⚠️ embedding生成レスポンス空: {chunk_id}")
                    return None
                    
            except Exception as e:
                logger.warning(f"⚠️ embedding生成エラー (試行 {attempt + 1}/{self.max_retries}): {chunk_id} - {e}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))  # 指数バックオフ
                else:
                    logger.error(f"❌ embedding生成最終失敗: {chunk_id}")
                    return None
    
    def _update_chunk_embedding(self, chunk_id: str, embedding: List[float]) -> bool:
        """チャンクのembeddingを更新"""
        try:
            cursor = self.db_connection.cursor()
            
            update_query = """
                UPDATE chunks 
                SET embedding = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            
            cursor.execute(update_query, (embedding, chunk_id))
            
            if cursor.rowcount > 0:
                logger.debug(f"✅ embedding更新成功: {chunk_id}")
                return True
            else:
                logger.warning(f"⚠️ embedding更新失敗（行が見つからない）: {chunk_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ embedding更新エラー: {chunk_id} - {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    async def _process_chunk_batch(self, chunks: List[Dict[str, Any]]) -> Dict[str, int]:
        """チャンクバッチを処理"""
        batch_stats = {"success": 0, "failed": 0, "skipped": 0}
        
        # 並行処理でembedding生成
        embedding_tasks = []
        for chunk in chunks:
            task = self._generate_embedding_with_retry(chunk["content"], chunk["id"])
            embedding_tasks.append((chunk, task))
        
        # 全てのembedding生成を並行実行
        for chunk, task in embedding_tasks:
            try:
                embedding = await task
                
                if embedding:
                    # データベース更新
                    if self._update_chunk_embedding(chunk["id"], embedding):
                        batch_stats["success"] += 1
                        self.stats["successful_embeddings"] += 1
                    else:
                        batch_stats["failed"] += 1
                        self.stats["failed_embeddings"] += 1
                else:
                    batch_stats["skipped"] += 1
                    self.stats["skipped_chunks"] += 1
                
                self.stats["processed_chunks"] += 1
                
            except Exception as e:
                logger.error(f"❌ チャンク処理エラー: {chunk['id']} - {e}")
                batch_stats["failed"] += 1
                self.stats["failed_embeddings"] += 1
        
        return batch_stats
    
    def _print_progress(self, current: int, total: int, batch_stats: Dict[str, int]):
        """進捗表示"""
        progress_percent = (current / total * 100) if total > 0 else 0
        elapsed_time = time.time() - self.stats["start_time"]
        
        logger.info(f"📊 進捗: {current}/{total} ({progress_percent:.1f}%) | "
                   f"成功: {batch_stats['success']} | "
                   f"失敗: {batch_stats['failed']} | "
                   f"スキップ: {batch_stats['skipped']} | "
                   f"経過時間: {elapsed_time:.1f}秒")
    
    def _print_final_stats(self):
        """最終統計表示"""
        total_time = self.stats["end_time"] - self.stats["start_time"]
        success_rate = (self.stats["successful_embeddings"] / self.stats["total_chunks"] * 100) if self.stats["total_chunks"] > 0 else 0
        
        logger.info("=" * 60)
        logger.info("🎉 エンベディング生成完了 - 最終統計")
        logger.info("=" * 60)
        logger.info(f"📊 総チャンク数: {self.stats['total_chunks']}")
        logger.info(f"✅ 成功: {self.stats['successful_embeddings']}")
        logger.info(f"❌ 失敗: {self.stats['failed_embeddings']}")
        logger.info(f"⏭️ スキップ: {self.stats['skipped_chunks']}")
        logger.info(f"📈 成功率: {success_rate:.1f}%")
        logger.info(f"⏱️ 総処理時間: {total_time:.1f}秒")
        logger.info(f"⚡ 平均処理速度: {self.stats['total_chunks'] / total_time:.2f} チャンク/秒")
        logger.info("=" * 60)
    
    async def generate_embeddings(self, limit: Optional[int] = None):
        """メイン処理：embedding生成"""
        try:
            self.stats["start_time"] = time.time()
            
            # 環境変数取得
            env_vars = self._get_env_vars()
            
            # 初期化
            self._init_gemini_client(env_vars["api_key"])
            self._init_database(env_vars["db_url"])
            
            # 処理対象チャンク取得
            pending_chunks = self._get_pending_chunks(limit)
            
            if not pending_chunks:
                logger.info("✅ 処理すべきチャンクはありません")
                return
            
            self.stats["total_chunks"] = len(pending_chunks)
            logger.info(f"🚀 embedding生成開始: {self.stats['total_chunks']}チャンク")
            
            # バッチ処理
            for i in range(0, len(pending_chunks), self.batch_size):
                batch = pending_chunks[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (len(pending_chunks) + self.batch_size - 1) // self.batch_size
                
                logger.info(f"📦 バッチ {batch_num}/{total_batches} 処理開始 ({len(batch)}チャンク)")
                
                # バッチ処理実行
                batch_stats = await self._process_chunk_batch(batch)
                
                # データベースコミット
                self.db_connection.commit()
                
                # 進捗表示
                self._print_progress(i + len(batch), len(pending_chunks), batch_stats)
                
                # バッチ間の待機（API制限対策）
                if i + self.batch_size < len(pending_chunks):
                    await asyncio.sleep(1)
            
            self.stats["end_time"] = time.time()
            self._print_final_stats()
            
        except Exception as e:
            logger.error(f"❌ メイン処理エラー: {e}")
            if self.db_connection:
                self.db_connection.rollback()
            raise
        
        finally:
            # リソースクリーンアップ
            if self.db_connection:
                self.db_connection.close()
                logger.info("🔒 データベース接続を閉じました")

async def main():
    """メイン関数"""
    logger.info("🚀 強化版エンベディング生成スクリプト開始")
    
    try:
        generator = EnhancedEmbeddingGenerator()
        
        # コマンドライン引数で制限数を指定可能
        limit = None
        if len(sys.argv) > 1:
            try:
                limit = int(sys.argv[1])
                logger.info(f"📋 処理制限: {limit}チャンク")
            except ValueError:
                logger.warning("⚠️ 無効な制限数が指定されました。全チャンクを処理します。")
        
        await generator.generate_embeddings(limit)
        logger.info("🎉 スクリプト実行完了")
        
    except Exception as e:
        logger.error(f"💥 スクリプト実行エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())