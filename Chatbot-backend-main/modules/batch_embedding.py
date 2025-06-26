"""
🧠 バッチエンベディング生成モジュール
チャンクを10件ずつまとめてバッチで送信し、エラー回復機能付きでembeddingを生成
text-embedding-004使用（768次元）
"""

import os
import logging
import asyncio
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from supabase_adapter import get_supabase_client, select_data, update_data

# ロギング設定
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()

class BatchEmbeddingGenerator:
    """バッチエンベディング生成クラス"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.embedding_model = "models/text-embedding-004"  # 固定でtext-embedding-004を使用（768次元）
        self.auto_generate = os.getenv("AUTO_GENERATE_EMBEDDINGS", "false").lower() == "true"
        self.supabase = None
        
        # バッチ処理設定
        self.batch_size = 10  # 10件ずつ処理
        self.max_retries = 3  # 最大リトライ回数
        self.retry_delay = 2  # リトライ間隔（秒）
        self.api_delay = 1    # API呼び出し間隔（秒）
        
        # 統計情報
        self.stats = {
            "total_chunks": 0,
            "processed_chunks": 0,
            "successful_embeddings": 0,
            "failed_embeddings": 0,
            "retry_count": 0,
            "start_time": None,
            "end_time": None
        }
    
    def _init_clients(self):
        """APIクライアントを初期化"""
        if not self.api_key:
            logger.error("❌ GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
            return False
        
        try:
            # Gemini API初期化
            genai.configure(api_key=self.api_key)
            
            # Supabaseクライアント初期化
            self.supabase = get_supabase_client()
            
            logger.info(f"🧠 バッチエンベディング生成初期化完了: {self.embedding_model} (768次元)")
            return True
        except Exception as e:
            logger.error(f"❌ APIクライアント初期化エラー: {e}")
            return False
    
    def _get_pending_chunks(self, doc_id: str = None, limit: int = None) -> List[Dict]:
        """embedding未生成のチャンクを取得"""
        try:
            filters = {"embedding": None}
            if doc_id:
                filters["doc_id"] = doc_id
            
            chunks_result = select_data(
                "chunks",
                columns="id,content,chunk_index,doc_id",
                filters=filters,
                limit=limit
            )
            
            if not chunks_result.data:
                return []
            
            return chunks_result.data
            
        except Exception as e:
            logger.error(f"❌ チャンク取得エラー: {e}")
            return []
    
    async def _generate_embedding_with_retry(self, content: str, chunk_id: str) -> Optional[List[float]]:
        """リトライ機能付きembedding生成"""
        for attempt in range(self.max_retries):
            try:
                if not content or not content.strip():
                    logger.warning(f"⚠️ 空のコンテンツをスキップ: {chunk_id}")
                    return None
                
                response = genai.embed_content(
                    model=self.embedding_model,
                    content=content.strip()
                )
                
                embedding_vector = None
                
                # レスポンス形式の処理
                if isinstance(response, dict) and 'embedding' in response:
                    embedding_vector = response['embedding']
                elif hasattr(response, 'embedding') and response.embedding:
                    embedding_vector = response.embedding
                else:
                    logger.error(f"🔍 予期しないレスポンス形式: {type(response)}")
                    return None
                
                if embedding_vector and len(embedding_vector) > 0:
                    # 768次元であることを確認
                    if len(embedding_vector) != 768:
                        logger.warning(f"⚠️ 予期しない次元数: {len(embedding_vector)}次元（期待値: 768次元）")
                    logger.debug(f"✅ embedding生成成功: {chunk_id} (次元: {len(embedding_vector)})")
                    return embedding_vector
                else:
                    logger.warning(f"⚠️ 無効なembedding: {chunk_id}")
                    return None
                    
            except Exception as e:
                self.stats["retry_count"] += 1
                logger.warning(f"⚠️ embedding生成エラー (試行 {attempt + 1}/{self.max_retries}): {chunk_id} - {e}")
                
                # 429エラー（レート制限）の場合は長めに待機
                if "429" in str(e) or "rate limit" in str(e).lower():
                    wait_time = self.retry_delay * (2 ** attempt)  # 指数バックオフ
                    logger.info(f"⏳ レート制限検出、{wait_time}秒待機...")
                    await asyncio.sleep(wait_time)
                elif attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"❌ embedding生成最終失敗: {chunk_id}")
                    return None
        
        return None
    
    async def _process_chunk_batch(self, chunks: List[Dict]) -> Tuple[List[str], List[str]]:
        """チャンクバッチを処理し、成功・失敗したチャンクIDを返す"""
        successful_chunks = []
        failed_chunks = []
        
        logger.info(f"📦 バッチ処理開始: {len(chunks)}件のチャンク")
        
        for i, chunk in enumerate(chunks):
            try:
                chunk_id = chunk['id']
                content = chunk['content']
                chunk_index = chunk['chunk_index']
                
                logger.info(f"  [{i+1}/{len(chunks)}] チャンク {chunk_index} 処理中...")
                
                # embedding生成
                embedding_vector = await self._generate_embedding_with_retry(content, chunk_id)
                
                if embedding_vector:
                    # データベース更新
                    update_result = update_data(
                        "chunks",
                        {"embedding": embedding_vector},
                        "id",
                        chunk_id
                    )
                    
                    if update_result:
                        successful_chunks.append(chunk_id)
                        self.stats["successful_embeddings"] += 1
                        logger.info(f"  ✅ チャンク {chunk_index} 完了 ({len(embedding_vector)}次元)")
                    else:
                        failed_chunks.append(chunk_id)
                        self.stats["failed_embeddings"] += 1
                        logger.error(f"  ❌ チャンク {chunk_index} DB更新失敗")
                else:
                    failed_chunks.append(chunk_id)
                    self.stats["failed_embeddings"] += 1
                    logger.error(f"  ❌ チャンク {chunk_index} embedding生成失敗")
                
                self.stats["processed_chunks"] += 1
                
                # API制限対策：チャンク間で少し待機
                if i < len(chunks) - 1:
                    await asyncio.sleep(0.5)
                
            except Exception as e:
                failed_chunks.append(chunk['id'])
                self.stats["failed_embeddings"] += 1
                logger.error(f"  ❌ チャンク {chunk.get('chunk_index', 'unknown')} 処理エラー: {e}")
        
        return successful_chunks, failed_chunks
    
    async def _retry_failed_chunks(self, failed_chunk_ids: List[str]) -> List[str]:
        """失敗したチャンクを再処理"""
        if not failed_chunk_ids:
            return []
        
        logger.info(f"🔄 失敗チャンクの再処理開始: {len(failed_chunk_ids)}件")
        
        # 失敗したチャンクの詳細を取得
        retry_chunks = []
        for chunk_id in failed_chunk_ids:
            chunk_result = select_data(
                "chunks",
                columns="id,content,chunk_index,doc_id",
                filters={"id": chunk_id}
            )
            
            if chunk_result.data:
                retry_chunks.append(chunk_result.data[0])
        
        if not retry_chunks:
            logger.warning("⚠️ 再処理対象のチャンクが見つかりません")
            return failed_chunk_ids
        
        # 再処理実行（バッチサイズを小さくして慎重に処理）
        still_failed = []
        retry_batch_size = 5  # 再処理時は小さなバッチサイズ
        
        for i in range(0, len(retry_chunks), retry_batch_size):
            batch = retry_chunks[i:i + retry_batch_size]
            logger.info(f"🔄 再処理バッチ {i//retry_batch_size + 1}: {len(batch)}件")
            
            # より長い待機時間
            await asyncio.sleep(self.api_delay * 2)
            
            successful, failed = await self._process_chunk_batch(batch)
            still_failed.extend(failed)
            
            # バッチ間でより長く待機
            if i + retry_batch_size < len(retry_chunks):
                await asyncio.sleep(self.api_delay * 3)
        
        logger.info(f"🔄 再処理完了: {len(failed_chunk_ids) - len(still_failed)}件成功, {len(still_failed)}件失敗")
        return still_failed
    
    def _print_progress(self, current_batch: int, total_batches: int, batch_stats: Tuple[List[str], List[str]]):
        """進捗表示"""
        successful, failed = batch_stats
        elapsed_time = time.time() - self.stats["start_time"]
        
        logger.info(f"📊 バッチ進捗: {current_batch}/{total_batches} | "
                   f"成功: {len(successful)} | 失敗: {len(failed)} | "
                   f"経過時間: {elapsed_time:.1f}秒")
    
    def _print_final_stats(self):
        """最終統計表示"""
        total_time = self.stats["end_time"] - self.stats["start_time"]
        success_rate = (self.stats["successful_embeddings"] / self.stats["total_chunks"] * 100) if self.stats["total_chunks"] > 0 else 0
        
        logger.info("=" * 60)
        logger.info("🎉 バッチエンベディング生成完了 - 最終統計")
        logger.info("=" * 60)
        logger.info(f"📊 総チャンク数: {self.stats['total_chunks']}")
        logger.info(f"✅ 成功: {self.stats['successful_embeddings']}")
        logger.info(f"❌ 失敗: {self.stats['failed_embeddings']}")
        logger.info(f"🔄 リトライ回数: {self.stats['retry_count']}")
        logger.info(f"📈 成功率: {success_rate:.1f}%")
        logger.info(f"⏱️ 総処理時間: {total_time:.1f}秒")
        if self.stats['total_chunks'] > 0:
            logger.info(f"⚡ 平均処理速度: {self.stats['total_chunks'] / total_time:.2f} チャンク/秒")
        logger.info("=" * 60)
    
    async def generate_embeddings_for_document(self, doc_id: str, max_chunks: int = None) -> bool:
        """指定されたドキュメントのチャンクに対してバッチエンベディング生成"""
        if not self.auto_generate:
            logger.info("🔄 AUTO_GENERATE_EMBEDDINGS=false のため、自動エンベディング生成をスキップ")
            return True
        
        if not self._init_clients():
            return False
        
        try:
            self.stats["start_time"] = time.time()
            logger.info(f"🧠 ドキュメント {doc_id} のバッチエンベディング生成開始")
            
            # 該当ドキュメントのembedding未生成チャンクを取得
            pending_chunks = self._get_pending_chunks(doc_id, max_chunks)
            
            if not pending_chunks:
                logger.info("✅ 新しく処理すべきチャンクはありません")
                return True
            
            self.stats["total_chunks"] = len(pending_chunks)
            logger.info(f"📋 {self.stats['total_chunks']}個のチャンクをバッチ処理します")
            
            all_failed_chunks = []
            
            # バッチ処理実行
            total_batches = (len(pending_chunks) + self.batch_size - 1) // self.batch_size
            
            for i in range(0, len(pending_chunks), self.batch_size):
                batch = pending_chunks[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                
                logger.info(f"📦 バッチ {batch_num}/{total_batches} 処理開始 ({len(batch)}チャンク)")
                
                # バッチ処理実行
                successful, failed = await self._process_chunk_batch(batch)
                all_failed_chunks.extend(failed)
                
                # 進捗表示
                self._print_progress(batch_num, total_batches, (successful, failed))
                
                # バッチ間の待機（API制限対策）
                if i + self.batch_size < len(pending_chunks):
                    await asyncio.sleep(self.api_delay)
            
            # 失敗したチャンクの再処理
            if all_failed_chunks:
                logger.info(f"🔄 失敗したチャンクの再処理を開始: {len(all_failed_chunks)}件")
                final_failed = await self._retry_failed_chunks(all_failed_chunks)
                
                if final_failed:
                    logger.warning(f"⚠️ 最終的に失敗したチャンク: {len(final_failed)}件")
                    for chunk_id in final_failed:
                        logger.warning(f"  - 失敗チャンクID: {chunk_id}")
            
            self.stats["end_time"] = time.time()
            self._print_final_stats()
            
            return self.stats["successful_embeddings"] > 0
            
        except Exception as e:
            logger.error(f"❌ バッチエンベディング生成エラー: {e}")
            return False
    
    async def generate_embeddings_for_all_pending(self, limit: int = None) -> bool:
        """全ての未処理チャンクに対してバッチエンベディング生成"""
        if not self.auto_generate:
            logger.info("🔄 AUTO_GENERATE_EMBEDDINGS=false のため、自動エンベディング生成をスキップ")
            return True
        
        if not self._init_clients():
            return False
        
        try:
            self.stats["start_time"] = time.time()
            logger.info("🧠 全未処理チャンクのバッチエンベディング生成開始")
            
            # 全ての未処理チャンクを取得
            pending_chunks = self._get_pending_chunks(limit=limit)
            
            if not pending_chunks:
                logger.info("✅ 処理すべきチャンクはありません")
                return True
            
            self.stats["total_chunks"] = len(pending_chunks)
            logger.info(f"📋 {self.stats['total_chunks']}個のチャンクをバッチ処理します")
            
            all_failed_chunks = []
            
            # バッチ処理実行
            total_batches = (len(pending_chunks) + self.batch_size - 1) // self.batch_size
            
            for i in range(0, len(pending_chunks), self.batch_size):
                batch = pending_chunks[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                
                logger.info(f"📦 バッチ {batch_num}/{total_batches} 処理開始 ({len(batch)}チャンク)")
                
                # バッチ処理実行
                successful, failed = await self._process_chunk_batch(batch)
                all_failed_chunks.extend(failed)
                
                # 進捗表示
                self._print_progress(batch_num, total_batches, (successful, failed))
                
                # バッチ間の待機（API制限対策）
                if i + self.batch_size < len(pending_chunks):
                    await asyncio.sleep(self.api_delay)
            
            # 失敗したチャンクの再処理
            if all_failed_chunks:
                logger.info(f"🔄 失敗したチャンクの再処理を開始: {len(all_failed_chunks)}件")
                final_failed = await self._retry_failed_chunks(all_failed_chunks)
                
                if final_failed:
                    logger.warning(f"⚠️ 最終的に失敗したチャンク: {len(final_failed)}件")
            
            self.stats["end_time"] = time.time()
            self._print_final_stats()
            
            return self.stats["successful_embeddings"] > 0
            
        except Exception as e:
            logger.error(f"❌ バッチエンベディング生成エラー: {e}")
            return False

# グローバルインスタンス
batch_embedding_generator = BatchEmbeddingGenerator()

async def batch_generate_embeddings_for_document(doc_id: str, max_chunks: int = None) -> bool:
    """ドキュメントのバッチエンベディング生成（外部呼び出し用）"""
    return await batch_embedding_generator.generate_embeddings_for_document(doc_id, max_chunks)

async def batch_generate_embeddings_for_all_pending(limit: int = None) -> bool:
    """全未処理チャンクのバッチエンベディング生成（外部呼び出し用）"""
    return await batch_embedding_generator.generate_embeddings_for_all_pending(limit)