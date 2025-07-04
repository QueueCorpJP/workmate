"""
🧠 自動エンベディング生成モジュール
アップロード後に自動的にエンベディングを生成する機能を提供
"""

import os
import logging
import asyncio
from typing import List, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from supabase_adapter import get_supabase_client, select_data, update_data
from .vertex_ai_embedding import get_vertex_ai_embedding_client, vertex_ai_embedding_available

# ロギング設定
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()

class AutoEmbeddingGenerator:
    """自動エンベディング生成クラス"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
        self.auto_generate = os.getenv("AUTO_GENERATE_EMBEDDINGS", "false").lower() == "true"
        self.use_vertex_ai = os.getenv("USE_VERTEX_AI", "true").lower() == "true"
        self.supabase = None
        self.vertex_ai_client = None
        
        # Vertex AI使用時はクライアントを初期化
        if self.use_vertex_ai and vertex_ai_embedding_available():
            self.vertex_ai_client = get_vertex_ai_embedding_client()
            logger.info(f"🧠 Vertex AI Embedding使用: {self.embedding_model}")
        else:
            # 標準Gemini API使用時のモデル名正規化
            if not self.embedding_model.startswith("models/"):
                self.embedding_model = f"models/{self.embedding_model}"
            logger.info(f"🧠 標準Gemini API使用: {self.embedding_model}")
    
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
            
            logger.info(f"🧠 自動エンベディング生成初期化完了: {self.embedding_model}")
            return True
        except Exception as e:
            logger.error(f"❌ APIクライアント初期化エラー: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ APIクライアント初期化エラー: {e}")
            return False
    
    async def generate_embeddings_for_document(self, doc_id: str, max_chunks: int = 50) -> bool:
        """指定されたドキュメントのチャンクに対してエンベディングを生成"""
        # 強制実行モードでは auto_generate チェックをスキップ
        if not self.auto_generate:
            logger.info("🔄 AUTO_GENERATE_EMBEDDINGS=false ですが、強制実行モードで処理を続行します")
            # return True をコメントアウトして処理を続行
        
        if not self._init_clients():
            return False
        
        try:
            logger.info(f"🧠 ドキュメント {doc_id} のエンベディング生成開始")
            
            # 該当ドキュメントのembedding未生成チャンクを取得
            chunks_result = select_data(
                "chunks",
                columns="id,content,chunk_index",
                filters={
                    "doc_id": doc_id,
                    "embedding": None
                },
                limit=max_chunks
            )
            
            if not chunks_result.data:
                logger.info("✅ 新しく処理すべきチャンクはありません")
                return True
            
            chunks = chunks_result.data
            logger.info(f"📋 {len(chunks)}個のチャンクのエンベディングを生成します")
            
            success_count = 0
            for chunk in chunks:
                try:
                    chunk_id = chunk['id']
                    content = chunk['content']
                    chunk_index = chunk['chunk_index']
                    
                    if not content or not content.strip():
                        logger.warning(f"⚠️ 空のコンテンツをスキップ: chunk_index={chunk_index}")
                        continue
                    
                    # エンベディング生成
                    logger.info(f"  - チャンク {chunk_index} のエンベディング生成中...")
                    
                    embedding_vector = None
                    
                    if self.use_vertex_ai and self.vertex_ai_client:
                        # Vertex AI使用
                        embedding_vector = self.vertex_ai_client.generate_embedding(content)
                    else:
                        # 標準Gemini API使用
                        response = genai.embed_content(
                            model=self.embedding_model,
                            content=content
                        )
                        
                        # gemini-embedding-exp-03-07は辞書形式で{'embedding': [...]}を返す
                        if isinstance(response, dict) and 'embedding' in response:
                            embedding_vector = response['embedding']
                        elif hasattr(response, 'embedding') and response.embedding:
                            embedding_vector = response.embedding
                        else:
                            logger.error(f"  🔍 予期しないレスポンス形式: {type(response)}")
                    
                    if embedding_vector and len(embedding_vector) > 0:
                        # データベースに保存
                        update_result = update_data(
                            "chunks",
                            {"embedding": embedding_vector},
                            "id",
                            chunk_id
                        )
                        
                        if update_result:
                            success_count += 1
                            logger.info(f"  ✅ チャンク {chunk_index} エンベディング保存完了 ({len(embedding_vector)}次元)")
                        else:
                            logger.error(f"  ❌ チャンク {chunk_index} エンベディング保存失敗")
                    else:
                        logger.error(f"  ❌ チャンク {chunk_index} エンベディング生成失敗: 無効なレスポンス")
                
                except Exception as chunk_error:
                    logger.error(f"  ❌ チャンク {chunk.get('chunk_index', 'unknown')} 処理エラー: {chunk_error}")
                    continue
            
            logger.info(f"🎉 エンベディング生成完了: {success_count}/{len(chunks)} 成功")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ エンベディング生成エラー: {e}")
            return False
    
    async def generate_chunk_embedding(self, chunk_id: str, content: str) -> bool:
        """単一チャンクのエンベディングを生成"""
        if not self._init_clients():
            return False
        
        try:
            if not content or not content.strip():
                logger.warning(f"⚠️ 空のコンテンツをスキップ: chunk_id={chunk_id}")
                return False
            
            embedding_vector = None
            
            if self.use_vertex_ai and self.vertex_ai_client:
                # Vertex AI使用
                embedding_vector = self.vertex_ai_client.generate_embedding(content)
            else:
                # 標準Gemini API使用
                response = genai.embed_content(
                    model=self.embedding_model,
                    content=content
                )
                
                # gemini-embedding-exp-03-07は辞書形式で{'embedding': [...]}を返す
                if isinstance(response, dict) and 'embedding' in response:
                    embedding_vector = response['embedding']
                elif hasattr(response, 'embedding') and response.embedding:
                    embedding_vector = response.embedding
                else:
                    logger.error(f"🔍 予期しないレスポンス形式: {type(response)}")
            
            if embedding_vector and len(embedding_vector) > 0:
                # データベースに保存
                update_result = update_data(
                    "chunks",
                    {"embedding": embedding_vector},
                    "id",
                    chunk_id
                )
                
                if update_result.success:
                    logger.info(f"✅ チャンク {chunk_id} エンベディング保存完了 ({len(embedding_vector)}次元)")
                    return True
                else:
                    logger.error(f"❌ チャンク {chunk_id} エンベディング保存失敗: {update_result.error}")
                    return False
            else:
                logger.error(f"❌ チャンク {chunk_id} エンベディング生成失敗: 無効なレスポンス")
                return False
                
        except Exception as e:
            logger.error(f"❌ チャンク {chunk_id} エンベディング生成エラー: {e}")
            return False
    
    async def generate_embeddings_for_chunks(self, chunk_ids: List[str]) -> bool:
        """指定されたチャンクIDリストに対してエンベディングを生成"""
        # 強制実行モードでは auto_generate チェックをスキップ
        if not self.auto_generate:
            logger.info("🔄 AUTO_GENERATE_EMBEDDINGS=false ですが、強制実行モードで処理を続行します")
            # return True をコメントアウトして処理を続行
        
        if not chunk_ids:
            logger.info("📋 処理対象のチャンクがありません")
            return True
        
        if not self._init_clients():
            return False
        
        try:
            logger.info(f"🧠 {len(chunk_ids)}個のチャンクのエンベディング生成開始")
            
            success_count = 0
            for chunk_id in chunk_ids:
                try:
                    # チャンク情報を取得
                    chunk_result = select_data(
                        "chunks",
                        columns="id,content,chunk_index,doc_id",
                        filters={"id": chunk_id}
                    )
                    
                    if not chunk_result.data:
                        logger.warning(f"⚠️ チャンク {chunk_id} が見つかりません")
                        continue
                    
                    chunk = chunk_result.data[0]
                    content = chunk['content']
                    chunk_index = chunk['chunk_index']
                    
                    if not content or not content.strip():
                        logger.warning(f"⚠️ 空のコンテンツをスキップ: chunk_id={chunk_id}")
                        continue
                    
                    # エンベディング生成
                    logger.info(f"  - チャンク {chunk_index} (ID: {chunk_id}) のエンベディング生成中...")
                    
                    embedding_vector = None
                    
                    if self.use_vertex_ai and self.vertex_ai_client:
                        # Vertex AI使用
                        embedding_vector = self.vertex_ai_client.generate_embedding(content)
                    else:
                        # 標準Gemini API使用
                        response = genai.embed_content(
                            model=self.embedding_model,
                            content=content
                        )
                        
                        # gemini-embedding-exp-03-07は辞書形式で{'embedding': [...]}を返す
                        if isinstance(response, dict) and 'embedding' in response:
                            embedding_vector = response['embedding']
                        elif hasattr(response, 'embedding') and response.embedding:
                            embedding_vector = response.embedding
                        else:
                            logger.error(f"  🔍 予期しないレスポンス形式: {type(response)}")
                    
                    if embedding_vector and len(embedding_vector) > 0:
                        # データベースに保存
                        update_result = update_data(
                            "chunks",
                            {"embedding": embedding_vector},
                            "id",
                            chunk_id
                        )
                        
                        if update_result:
                            success_count += 1
                            logger.info(f"  ✅ チャンク {chunk_index} エンベディング保存完了 ({len(embedding_vector)}次元)")
                        else:
                            logger.error(f"  ❌ チャンク {chunk_index} エンベディング保存失敗")
                    else:
                        logger.error(f"  ❌ チャンク {chunk_index} エンベディング生成失敗: 無効なレスポンス")
                
                except Exception as chunk_error:
                    logger.error(f"  ❌ チャンク {chunk_id} 処理エラー: {chunk_error}")
                    continue
            
            logger.info(f"🎉 エンベディング生成完了: {success_count}/{len(chunk_ids)} 成功")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ エンベディング生成エラー: {e}")
            return False

# グローバルインスタンス
auto_embedding_generator = AutoEmbeddingGenerator()

async def auto_generate_embeddings_for_document(doc_id: str, max_chunks: int = 50) -> bool:
    """ドキュメントの自動エンベディング生成（外部呼び出し用）"""
    return await auto_embedding_generator.generate_embeddings_for_document(doc_id, max_chunks)

async def auto_generate_embeddings_for_chunks(chunk_ids: List[str]) -> bool:
    """チャンクリストの自動エンベディング生成（外部呼び出し用）"""
    return await auto_embedding_generator.generate_embeddings_for_chunks(chunk_ids)