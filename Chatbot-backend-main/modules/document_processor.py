"""
📤 ファイルアップロード・ドキュメント処理システム
🧩 チャンク分割（300〜500 token）
🧠 embedding生成を統合（Gemini Flash - 3072次元）
🗃 Supabase保存（document_sources + chunks）

完全なRAG対応ドキュメント処理パイプライン
"""

import os
import uuid
import logging
import asyncio
import tempfile
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
import re
import tiktoken
from fastapi import HTTPException, UploadFile
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.error("❌ google-genai SDK not available. Please install: pip install -U google-genai")
import psycopg2
from psycopg2.extras import execute_values
from .multi_api_embedding import get_multi_api_embedding_client, multi_api_embedding_available

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """ドキュメント処理のメインクラス"""
    
    def __init__(self):
        self.gemini_client = None
        self.multi_api_client = None
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
        
        # Gemini API使用時はmodels/プレフィックスを追加
        if not self.embedding_model.startswith("models/"):
            self.embedding_model = f"models/{self.embedding_model}"
            
        self.min_chunk_size_chars = 600  # 🎯 最小チャンクサイズ（FAQなど短いコンテンツ用）
        self.max_chunk_size_chars = 800  # 🎯 最大チャンクサイズ（詳細説明など長いコンテンツ用）
        self.target_chunk_size_chars = 700  # 🎯 目標チャンクサイズ（600-800文字範囲の中央値）
        self.chunk_size_tokens = 250  # 参考トークン数（動的調整されます）
        self.chunk_overlap_chars = 50  # 🎯 固定50文字オーバーラップ（サイズ制御）
        
        # トークンカウンター初期化
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"tiktoken初期化失敗: {e}")
            self.tokenizer = None
        
        # 複数API対応を最優先、次にGemini API
        if multi_api_embedding_available():
            self.multi_api_client = get_multi_api_embedding_client()
            # 🎯 APIキー数に応じた最大リトライ回数を設定
            self.max_retries = len(self.multi_api_client.api_keys) if self.multi_api_client else 10
            logger.info(f"✅ 複数API対応エンベディングクライアント使用 (最大リトライ: {self.max_retries}回)")
        else:
            self.max_retries = 3  # フォールバック時のデフォルト値
            self._init_gemini_client()
    
    
    def _init_gemini_client(self):
        """Gemini APIクライアントを初期化（新しいSDK）"""
        if self.gemini_client is None:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
            
            # 新しいSDKのクライアント初期化
            self.gemini_client = genai.Client(api_key=api_key)
            logger.info(f"🧠 Gemini APIクライアント初期化完了（新SDK）: {self.embedding_model}")
    
    def _count_tokens(self, text: str) -> int:
        """テキストのトークン数をカウント"""
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"トークンカウントエラー: {e}")
        
        # フォールバック: 文字数ベースの推定（日本語対応）
        # 日本語: 1文字 ≈ 1.5トークン, 英語: 4文字 ≈ 1トークン
        japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text))
        other_chars = len(text) - japanese_chars
        estimated_tokens = int(japanese_chars * 1.5 + other_chars * 0.25)
        return estimated_tokens
    
    def _split_text_into_chunks(self, text: str, doc_name: str = "") -> List[Dict[str, Any]]:
        """
        テキストを意味単位でチャンクに分割
        600-800文字の範囲で厳密に制御
        """
        if not text or not text.strip():
            logger.warning(f"空のテキストが渡されました: {doc_name}")
            return []
        
        # 🎯 目標チャンクサイズ（700文字）での分割を使用
        from .chat_utils import chunk_knowledge_base
        chunk_texts = chunk_knowledge_base(
            text,
            chunk_size=self.target_chunk_size_chars  # 目標値（700文字）を使用
        )
        
        # チャンクデータに変換とサイズ検証
        chunks = []
        oversized_chunks = 0
        undersized_chunks = 0
        
        for i, chunk_text in enumerate(chunk_texts):
            if chunk_text.strip():
                chunk_content = chunk_text.strip()
                char_count = len(chunk_content)
                token_count = self._count_tokens(chunk_content)
                
                # 🎯 サイズ範囲チェック
                if char_count > self.max_chunk_size_chars:
                    oversized_chunks += 1
                    logger.warning(f"⚠️ チャンク {i} がサイズ超過: {char_count}文字 (最大{self.max_chunk_size_chars}文字)")
                elif char_count < self.min_chunk_size_chars:
                    undersized_chunks += 1
                    logger.debug(f"📏 チャンク {i} が小サイズ: {char_count}文字 (最小{self.min_chunk_size_chars}文字)")
                
                chunks.append({
                    "chunk_index": i,
                    "content": chunk_content,
                    "token_count": token_count,
                    "char_count": char_count
                })
        
        # 統計情報をログ出力
        total_chunks = len(chunks)
        valid_chunks = total_chunks - oversized_chunks
        logger.info(f"✅ {doc_name}: {total_chunks}個のチャンクに分割完了")
        logger.info(f"📊 サイズ統計 - 適正: {valid_chunks}, 超過: {oversized_chunks}, 小サイズ: {undersized_chunks}")
        
        if oversized_chunks > 0:
            logger.warning(f"⚠️ {oversized_chunks}個のチャンクが800文字を超過しています")
        
        return chunks
    

    async def _generate_embeddings_multi_api(self, texts: List[str], failed_indices: List[int] = None) -> List[Optional[List[float]]]:
        """複数API対応クライアントでテキストのembeddingを生成"""
        if not self.multi_api_client:
            raise ValueError("複数API対応クライアントが初期化されていません")
        
        all_embeddings = []
        failed_embeddings = []
        
        # 処理対象のインデックスを決定
        if failed_indices is None:
            process_indices = list(range(len(texts)))
            all_embeddings = [None] * len(texts)
        else:
            process_indices = failed_indices
            all_embeddings = [None] * len(texts)
        
        # 複数API対応クライアントで個別処理
        for idx, i in enumerate(process_indices):
            try:
                text = texts[i]
                if not text or not text.strip():
                    logger.warning(f"⚠️ 空のテキストをスキップ: インデックス {i}")
                    all_embeddings[i] = None
                    failed_embeddings.append(i)
                    continue
                
                # 複数API対応クライアントでembedding生成
                embedding_vector = await self.multi_api_client.generate_embedding(text.strip())
                
                expected_dims = (
                    self.multi_api_client.expected_dimensions if self.multi_api_client else 3072
                )

                if embedding_vector and len(embedding_vector) == expected_dims:
                    all_embeddings[i] = embedding_vector
                    logger.debug(f"✅ 複数API embedding生成成功: インデックス {i} ({len(embedding_vector)}次元)")
                else:
                    all_embeddings[i] = None
                    failed_embeddings.append(i)
                    logger.warning(f"⚠️ 複数API embedding生成失敗: インデックス {i}")
                
                # API制限対策：最小限の待機
                if idx < len(process_indices) - 1:
                    await asyncio.sleep(0.01)  # 0.1→0.01秒に短縮
                    
            except Exception as e:
                logger.error(f"❌ 複数API embedding生成エラー: インデックス {i} - {e}")
                all_embeddings[i] = None
                failed_embeddings.append(i)
        
        # 結果の統計を出力
        success_count = len(process_indices) - len(failed_embeddings)
        logger.info(f"📊 複数API embedding生成完了: {success_count}/{len(process_indices)} 成功")
        
        if failed_embeddings:
            logger.warning(f"⚠️ 複数API embedding生成失敗: {len(failed_embeddings)}件")
        
        return all_embeddings
    
    async def _generate_embeddings_batch(self, texts: List[str], failed_indices: List[int] = None) -> List[Optional[List[float]]]:
        """複数API対応、Vertex AI または Gemini APIでテキストのembeddingを個別生成（バッチ処理風）"""
        if failed_indices is None:
            logger.info(f"🧠 embedding生成開始: {len(texts)}件, モデル={self.embedding_model}")
        else:
            logger.info(f"🔄 embedding再生成開始: {len(failed_indices)}件の失敗分, モデル={self.embedding_model}")
        
        try:
            # 複数API対応を最優先で使用
            if self.multi_api_client:
                return await self._generate_embeddings_multi_api(texts, failed_indices)
            elif self.use_vertex_ai:
                return await self._generate_embeddings_vertex_ai(texts, failed_indices)
            else:
                return await self._generate_embeddings_gemini_api(texts, failed_indices)
                
        except Exception as e:
            logger.error(f"❌ embeddingバッチ生成中に例外発生: {e}", exc_info=True)
            raise
    
    async def _generate_embeddings_vertex_ai(self, texts: List[str], failed_indices: List[int] = None) -> List[Optional[List[float]]]:
        """Vertex AI でテキストのembeddingを生成"""
        if not self.vertex_ai_client:
            raise ValueError("Vertex AI クライアントが初期化されていません")
        
        all_embeddings = []
        failed_embeddings = []
        
        # 処理対象のインデックスを決定
        if failed_indices is None:
            process_indices = list(range(len(texts)))
            all_embeddings = [None] * len(texts)
        else:
            process_indices = failed_indices
            all_embeddings = [None] * len(texts)
        
        # Vertex AI は個別処理
        for idx, i in enumerate(process_indices):
            try:
                text = texts[i]
                if not text or not text.strip():
                    logger.warning(f"⚠️ 空のテキストをスキップ: インデックス {i}")
                    all_embeddings[i] = None
                    failed_embeddings.append(i)
                    continue
                
                # Vertex AI クライアントでembedding生成
                embedding_vector = await asyncio.to_thread(
                    self.vertex_ai_client.generate_embedding,
                    text.strip()
                )
                
                if embedding_vector:
                    all_embeddings[i] = embedding_vector
                    logger.info(f"✅ embedding生成成功: {idx + 1}/{len(process_indices)} (インデックス {i}, 次元: {len(embedding_vector)})")
                else:
                    logger.warning(f"⚠️ embedding生成失敗: インデックス {i}")
                    all_embeddings[i] = None
                    failed_embeddings.append(i)
                
                # API制限対策（最小限）
                await asyncio.sleep(0.01)  # 0.1→0.01秒に短縮
                
            except Exception as e:
                logger.error(f"❌ embedding生成エラー (インデックス {i}): {e}")
                all_embeddings[i] = None
                failed_embeddings.append(i)
        
        success_count = len([e for e in all_embeddings if e is not None])
        total_count = len(texts)
        
        if failed_indices is None:
            logger.info(f"🎉 Vertex AI embedding生成完了: {success_count}/{total_count} 成功")
        else:
            logger.info(f"🎉 Vertex AI embedding再生成完了: {success_count - (total_count - len(failed_indices))}/{len(failed_indices)} 成功")
        
        if failed_embeddings:
            logger.warning(f"⚠️ 失敗したインデックス: {failed_embeddings}")
        
        return all_embeddings
    
    async def _generate_embeddings_gemini_api(self, texts: List[str], failed_indices: List[int] = None) -> List[Optional[List[float]]]:
        """Gemini API でテキストのembeddingを生成"""
        self._init_gemini_client()
        
        all_embeddings = []
        failed_embeddings = []
        
        # 処理対象のインデックスを決定
        if failed_indices is None:
            process_indices = list(range(len(texts)))
            all_embeddings = [None] * len(texts)
        else:
            process_indices = failed_indices
            all_embeddings = [None] * len(texts)
        
        # Gemini APIは個別処理が推奨されるため、1つずつ処理
        for idx, i in enumerate(process_indices):
            try:
                text = texts[i]
                if not text or not text.strip():
                    logger.warning(f"⚠️ 空のテキストをスキップ: インデックス {i}")
                    all_embeddings[i] = None
                    failed_embeddings.append(i)
                    continue
                
                response = await asyncio.to_thread(
                    self.gemini_client.models.embed_content,
                    model=self.embedding_model,
                    contents=text.strip()
                )
                
                if response and hasattr(response, 'embeddings') and response.embeddings and len(response.embeddings) > 0:
                    embedding_vector = response.embeddings[0].values
                    all_embeddings[i] = embedding_vector
                    logger.info(f"✅ embedding生成成功: {idx + 1}/{len(process_indices)} (インデックス {i}, 次元: {len(embedding_vector)})")
                else:
                    logger.warning(f"⚠️ embedding生成レスポンスが不正です: インデックス {i}")
                    all_embeddings[i] = None
                    failed_embeddings.append(i)
                
                # API制限対策（最小限）
                await asyncio.sleep(0.01)  # 0.2→0.01秒に短縮
                
            except Exception as e:
                logger.error(f"❌ embedding生成エラー (インデックス {i}): {e}")
                all_embeddings[i] = None
                failed_embeddings.append(i)

        success_count = len([e for e in all_embeddings if e is not None])
        total_count = len(texts)
        
        if failed_indices is None:
            logger.info(f"🎉 Gemini API embedding生成完了: {success_count}/{total_count} 成功")
        else:
            logger.info(f"🎉 Gemini API embedding再生成完了: {success_count - (total_count - len(failed_indices))}/{len(failed_indices)} 成功")
        
        if failed_embeddings:
            logger.warning(f"⚠️ 失敗したインデックス: {failed_embeddings}")
        
        return all_embeddings

    async def _save_document_metadata(self, doc_data: Dict[str, Any]) -> str:
        """document_sourcesテーブルにメタデータを保存"""
        try:
            from supabase_adapter import insert_data, select_data
            
            document_id = str(uuid.uuid4())
            
            # document_sourcesテーブルに必要なフィールドのみを含める（contentとembeddingは削除済み）
            metadata = {
                "id": document_id,
                "name": doc_data["name"],
                "type": doc_data["type"],
                "page_count": doc_data.get("page_count", 1),
                "uploaded_by": doc_data["uploaded_by"],
                "company_id": doc_data["company_id"],
                "uploaded_at": datetime.now().isoformat(),  # uploaded_atフィールドを使用
                "active": True,  # activeフィールドを追加
                "parent_id": doc_data.get("parent_id"),  # 親ドキュメント（階層構造）
                "doc_id": document_id,  # ドキュメント識別子として自身のIDを設定
                "metadata": doc_data.get("metadata")  # metadataフィールドを追加
            }
            
            logger.info(f"保存するmetadata: {metadata.get('metadata')}")
            
            # metadataが文字列かどうかを確認
            if metadata.get('metadata'):
                logger.info(f"metadataの型: {type(metadata.get('metadata'))}")
                if isinstance(metadata.get('metadata'), str):
                    # JSON文字列として有効かどうかを確認
                    try:
                        import json
                        parsed = json.loads(metadata.get('metadata'))
                        logger.info(f"metadata JSON解析成功: {parsed}")
                    except Exception as json_error:
                        logger.error(f"metadata JSON解析失敗: {json_error}")
                        # 無効なJSONの場合は基本的なmetadataに置き換え
                        metadata['metadata'] = '{"error": "invalid json"}'
            else:
                logger.warning("metadataが空またはNone")
            
            # specialコラムは絶対に設定しない（ユーザーの要求通り）
            
            logger.info(f"🔄 document_sourcesテーブルへの保存開始: {document_id} - {doc_data['name']}")
            result = insert_data("document_sources", metadata)
            
            if result and result.data:
                logger.info(f"✅ document_sourcesテーブル保存完了: {document_id} - {doc_data['name']}")
                # 保存後に実際のデータを確認
                try:
                    from supabase_adapter import select_data
                    check_result = select_data("document_sources", filters={"id": document_id})
                    if check_result.success and check_result.data:
                        saved_metadata = check_result.data[0].get('metadata')
                        logger.info(f"✅ 保存確認 - 実際のmetadata: {saved_metadata}")
                    else:
                        logger.warning(f"⚠️ 保存確認失敗: {check_result.error}")
                except Exception as check_error:
                    logger.warning(f"⚠️ 保存確認エラー: {check_error}")
                return document_id
            else:
                logger.error(f"❌ document_sourcesテーブル保存失敗: result={result}")
                raise Exception("document_sourcesテーブルへのメタデータ保存に失敗しました")
                
        except Exception as main_error:
            logger.error(f"❌ メタデータ保存エラー: {main_error}")
            
            # 外部キー制約エラーの場合はユーザー情報を確認
            error_str = str(main_error)
            if "document_sources_uploaded_by_fkey" in error_str:
                logger.warning(f"ユーザー '{doc_data['uploaded_by']}' が存在しません - company_idで代替保存を試行")
                try:
                    # company_idから代替ユーザーを検索
                    company_users = select_data(
                        "users",
                        columns="id",
                        filters={"company_id": doc_data["company_id"]}
                    )
                    
                    if company_users.data and len(company_users.data) > 0:
                        alternative_user_id = company_users.data[0]["id"]
                        logger.info(f"代替ユーザーを発見: {alternative_user_id}")
                        
                        # 代替ユーザーIDで再保存
                        metadata["uploaded_by"] = alternative_user_id
                        result = insert_data("document_sources", metadata)
                        
                        if result and result.data:
                            logger.info(f"✅ 代替ユーザーでメタデータ保存完了: {document_id}")
                            return document_id
                        else:
                            raise Exception("代替ユーザーでのメタデータ保存に失敗しました")
                    else:
                        # 会社にユーザーが存在しない場合は、テスト用のダミーユーザーを作成
                        logger.warning(f"会社 '{doc_data['company_id']}' にユーザーが存在しません - テスト用ユーザーを作成")
                        test_user_data = {
                            "id": doc_data["uploaded_by"],
                            "company_id": doc_data["company_id"],
                            "name": "Test User",
                            "email": "test@example.com",
                            "created_at": datetime.now().isoformat()
                        }
                        
                        user_result = insert_data("users", test_user_data)
                        if user_result and user_result.data:
                            logger.info(f"✅ テスト用ユーザー作成完了: {doc_data['uploaded_by']}")
                            
                            # 元のメタデータで再保存
                            result = insert_data("document_sources", metadata)
                            if result and result.data:
                                logger.info(f"✅ メタデータ保存完了: {document_id}")
                                return document_id
                            else:
                                raise Exception("テスト用ユーザー作成後のメタデータ保存に失敗しました")
                        else:
                            raise Exception("テスト用ユーザーの作成に失敗しました")
                            
                except Exception as fallback_error:
                    logger.error(f"❌ 代替保存処理エラー: {fallback_error}")
                    raise Exception(f"メタデータ保存に失敗しました: {fallback_error}")
            else:
                raise main_error
    
    async def _save_chunks_to_database(self, doc_id: str, chunks: List[Dict[str, Any]],
                                     company_id: str, doc_name: str, max_retries: int = None) -> Dict[str, Any]:
        """chunksテーブルにチャンクデータとembeddingを50個単位でリアルタイム保存"""
        # 🎯 APIキー数に応じたリトライ回数を使用
        if max_retries is None:
            max_retries = self.max_retries
            
        try:
            from supabase_adapter import get_supabase_client
            supabase = get_supabase_client()

            stats = {
                "total_chunks": len(chunks),
                "saved_chunks": 0,
                "successful_embeddings": 0,
                "failed_embeddings": 0,
                "retry_attempts": 0,
                "failed_chunks": []  # 失敗したチャンクを記録
            }

            if not chunks:
                return stats

            batch_size = 50
            total_batches = (len(chunks) + batch_size - 1) // batch_size
            
            logger.info(f"🚀 {doc_name}: {len(chunks)}個のチャンクを{batch_size}個単位で処理開始")
            logger.info(f"📊 予想バッチ数: {total_batches}")

            # 50個単位でembedding生成→即座にinsert
            for batch_num in range(0, len(chunks), batch_size):
                batch_chunks = chunks[batch_num:batch_num + batch_size]
                current_batch = (batch_num // batch_size) + 1
                
                logger.info(f"🧠 バッチ {current_batch}/{total_batches}: {len(batch_chunks)}個のembedding生成開始")
                
                # このバッチのembedding生成
                batch_contents = [chunk["content"] for chunk in batch_chunks]
                batch_embeddings = await self._generate_embeddings_batch(batch_contents)
                
                # 失敗したembeddingのリトライ処理
                failed_indices = [i for i, emb in enumerate(batch_embeddings) if emb is None]
                retry_count = 0
                
                while failed_indices and retry_count < max_retries:
                    retry_count += 1
                    logger.info(f"🔄 バッチ {current_batch} embedding再生成 (試行 {retry_count}/{max_retries}): {len(failed_indices)}件")
                    
                    retry_embeddings = await self._generate_embeddings_batch(batch_contents, failed_indices)
                    
                    for i in failed_indices:
                        if retry_embeddings[i] is not None:
                            batch_embeddings[i] = retry_embeddings[i]
                    
                    failed_indices = [i for i in failed_indices if batch_embeddings[i] is None]
                    
                    if failed_indices:
                        logger.warning(f"⚠️ バッチ {current_batch} 再試行後も失敗: {len(failed_indices)}件")
                        await asyncio.sleep(1.0)
                    else:
                        logger.info(f"✅ バッチ {current_batch} 再試行成功")
                        break
                
                # 統計更新
                for embedding in batch_embeddings:
                    if embedding:
                        stats["successful_embeddings"] += 1
                    else:
                        stats["failed_embeddings"] += 1
                
                if retry_count > 0:
                    stats["retry_attempts"] = max(stats["retry_attempts"], retry_count)
                
                # 成功したembeddingのみでレコード準備、失敗したものは記録
                records_to_insert = []
                for i, chunk_data in enumerate(batch_chunks):
                    embedding_vector = batch_embeddings[i]
                    if embedding_vector:  # 成功したembeddingのみ
                        records_to_insert.append({
                            "doc_id": doc_id,
                            "chunk_index": chunk_data["chunk_index"],
                            "content": chunk_data["content"],
                            "embedding": embedding_vector,
                            "company_id": company_id,
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat()
                        })
                    else:
                        # 失敗したチャンクをembeddingなしで保存（後で再処理用）
                        failed_record = {
                            "doc_id": doc_id,
                            "chunk_index": chunk_data["chunk_index"],
                            "content": chunk_data["content"],
                            "embedding": None,
                            "company_id": company_id,
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat()
                        }
                        records_to_insert.append(failed_record)
                        stats["failed_chunks"].append(failed_record)
                
                # 即座にSupabaseに挿入
                if records_to_insert:
                    try:
                        logger.info(f"💾 バッチ {current_batch}/{total_batches}: {len(records_to_insert)}件を即座に保存中...")
                        result = supabase.table("chunks").insert(records_to_insert).execute()
                        
                        if result.data:
                            batch_saved = len(result.data)
                            stats["saved_chunks"] += batch_saved
                            logger.info(f"✅ バッチ {current_batch}/{total_batches}: {batch_saved}件保存完了")
                        else:
                            logger.error(f"❌ バッチ {current_batch}/{total_batches} 保存エラー: {result.error}")
                            
                    except Exception as batch_error:
                        logger.error(f"❌ バッチ {current_batch}/{total_batches} 保存中に例外発生: {batch_error}")
                        # バッチエラーでも次のバッチ処理を続行
                        continue
                else:
                    logger.warning(f"⚠️ バッチ {current_batch}/{total_batches}: 保存可能なレコードがありません")
                
                # バッチ完了ログ
                logger.info(f"🎯 バッチ {current_batch}/{total_batches} 完了: embedding {len(batch_embeddings) - len(failed_indices)}/{len(batch_embeddings)} 成功, 保存 {len(records_to_insert)} 件")

            # 最終結果のサマリー
            logger.info(f"🏁 {doc_name}: 全処理完了")
            logger.info(f"📈 最終結果: 保存 {stats['saved_chunks']}/{stats['total_chunks']} チャンク")
            logger.info(f"🧠 embedding: 成功 {stats['successful_embeddings']}, 失敗 {stats['failed_embeddings']}")
            
            if stats["failed_embeddings"] > 0:
                logger.warning(f"⚠️ 最終結果: {stats['successful_embeddings']}/{stats['total_chunks']} embedding成功, {stats['retry_attempts']}回再試行")
                logger.info(f"📋 失敗したチャンク数: {len(stats['failed_chunks'])}件 - 後で再処理予定")
            else:
                logger.info(f"🎉 全embedding生成成功: {stats['successful_embeddings']}/{stats['total_chunks']}")

            return stats

        except Exception as e:
            logger.error(f"❌ リアルタイムバッチ保存中に例外発生: {e}", exc_info=True)
            raise
    
    async def process_uploaded_file(self, file: UploadFile, user_id: str, 
                                  company_id: str) -> Dict[str, Any]:
        """
        アップロードされたファイルを完全処理
        1️⃣ ファイルアップロード
        2️⃣ テキスト抽出
        3️⃣ チャンク分割（300〜500 token）
        4️⃣ embedding生成（Gemini Flash - 3072次元）
        5️⃣ Supabase保存
        """
        try:
            logger.info(f"🚀 ファイル処理開始: {file.filename}")
            
            # ファイル内容を読み込み
            file_content = await file.read()
            file_size_mb = len(file_content) / (1024 * 1024)
            
            logger.info(f"📁 ファイルサイズ: {file_size_mb:.2f} MB")
            
            # ファイル形式に応じてテキスト抽出
            extracted_text = await self._extract_text_from_file(file, file_content)
            
            if not extracted_text or not extracted_text.strip():
                raise HTTPException(status_code=400, detail="ファイルからテキストを抽出できませんでした")
            
            logger.info(f"📝 抽出テキスト: {len(extracted_text)} 文字")
            
            # チャンク分割
            chunks = self._split_text_into_chunks(extracted_text, file.filename)
            
            if not chunks:
                raise HTTPException(status_code=400, detail="テキストをチャンクに分割できませんでした")
            
            # ドキュメントメタデータを保存
            doc_data = {
                "name": file.filename,
                "type": self._detect_file_type(file.filename),
                "page_count": self._estimate_page_count(extracted_text),
                "uploaded_by": user_id,
                "company_id": company_id,
                "special": f"テキスト長: {len(extracted_text)}文字"  # 特殊属性として記録
            }
            
            document_id = await self._save_document_metadata(doc_data)
            
            # チャンクをデータベースに保存
            save_stats = await self._save_chunks_to_database(
                document_id, chunks, company_id, file.filename
            )
            
            # 失敗したembeddingがある場合は全処理完了後に再処理
            if save_stats["failed_embeddings"] > 0:
                logger.info(f"🔄 {file.filename}: 失敗したembedding {save_stats['failed_embeddings']}件の再処理を開始")
                retry_stats = await self._retry_failed_embeddings_post_processing(
                    document_id, company_id, file.filename
                )
                
                # 統計を更新
                save_stats["successful_embeddings"] += retry_stats["successful"]
                save_stats["failed_embeddings"] = retry_stats["still_failed"]
                save_stats["retry_attempts"] = max(save_stats["retry_attempts"], retry_stats["retry_attempts"])
                
                logger.info(f"🔄 {file.filename}: 再処理完了 - 追加成功 {retry_stats['successful']}件, 最終失敗 {retry_stats['still_failed']}件")
            
            # 処理結果を返す
            result = {
                "success": True,
                "document_id": document_id,
                "filename": file.filename,
                "file_size_mb": round(file_size_mb, 2),
                "text_length": len(extracted_text),
                "total_chunks": save_stats["total_chunks"],
                "saved_chunks": save_stats["saved_chunks"],
                "successful_embeddings": save_stats["successful_embeddings"],
                "failed_embeddings": save_stats["failed_embeddings"],
                "message": f"✅ {file.filename} の処理・embedding生成が完了しました"
            }
            
            logger.info(f"🎉 ファイル処理完了: {file.filename}")
            return result
            
        except Exception as e:
            logger.error(f"❌ ファイル処理エラー: {e}")
            raise HTTPException(status_code=500, detail=f"ファイル処理中にエラーが発生しました: {str(e)}")
    
    async def _extract_text_from_file(self, file: UploadFile, content: bytes) -> str:
        """ファイル形式に応じてテキストを抽出"""
        filename = file.filename.lower()
        
        try:
            if filename.endswith(('.pdf',)):
                return await self._extract_text_from_pdf(content)
            elif filename.endswith(('.xlsx', '.xls')):
                return await self._extract_text_from_excel(content)
            elif filename.endswith(('.docx', '.doc')):
                return await self._extract_text_from_word(content)
            elif filename.endswith(('.txt', '.csv')):
                return await self._extract_text_from_text(content)
            elif filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                return await self._extract_text_from_image(content)
            else:
                # フォールバック: テキストとして読み込み
                return content.decode('utf-8', errors='ignore')
                
        except Exception as e:
            logger.error(f"テキスト抽出エラー ({filename}): {e}")
            raise
    
    async def _extract_text_from_pdf(self, content: bytes) -> str:
        """PDF からテキストを抽出する（Gemini 2.5 Flash OCR完璧版）
        
        1. Gemini 2.5 Flash OCR（最高品質）
        2. PyMuPDF（フォールバック）
        3. PyPDF2（最終フォールバック）
        """
        
        logger.info("🚀 PDF抽出開始 - Gemini 2.5 Flash OCR優先")
        
        try:
            # まずGemini 2.5 Flash OCRを試行（最高品質）
            logger.info("🔄 Gemini 2.5 Flash OCRでテキスト抽出を試行中...")
            
            try:
                from .knowledge.gemini_flash_ocr import ocr_pdf_with_gemini_flash
                
                ocr_text = await ocr_pdf_with_gemini_flash(content)
                
                if ocr_text and ocr_text.strip() and not ocr_text.startswith("OCR処理エラー"):
                    # OCR成功時の品質チェック
                    quality_score = self._evaluate_text_quality(ocr_text)
                    page_count = ocr_text.count("--- ページ") or 1
                    
                    logger.info(f"✅ Gemini 2.5 Flash OCR成功:")
                    logger.info(f"   - 総文字数: {len(ocr_text):,}")
                    logger.info(f"   - 品質スコア: {quality_score}/100")
                    logger.info(f"   - ページ数: {page_count}")
                    logger.info(f"   - 平均文字/ページ: {len(ocr_text)/page_count:.0f}")
                    
                    return ocr_text
                else:
                    logger.warning("⚠️ Gemini 2.5 Flash OCRが失敗またはエラーを返しました")
                    raise Exception("Gemini 2.5 Flash OCR failed")
                    
            except ImportError as e:
                logger.warning(f"⚠️ Gemini Flash OCRモジュールをインポートできません: {e}")
                raise Exception(f"Gemini Flash OCR module not available: {e}")
            except Exception as ocr_error:
                logger.warning(f"⚠️ Gemini 2.5 Flash OCR処理失敗: {ocr_error}")
                raise Exception(f"Gemini Flash OCR failed: {ocr_error}")
                
        except Exception as primary_error:
            logger.error(f"❌ Gemini 2.5 Flash OCR処理失敗: {primary_error}")
            logger.info("🔄 PyMuPDFフォールバックを使用")
            
            # PyMuPDFフォールバック
            try:
                import fitz  # PyMuPDF
                
                # PyMuPDFでPDF処理
                with fitz.open(stream=content, filetype="pdf") as doc:
                    full_text = ""
                    page_count = len(doc)
                    
                    for page_num, page in enumerate(doc, start=1):
                        try:
                            # テキスト抽出
                            page_text = page.get_text("text") or ""
                            
                            if page_text.strip():
                                # 文字化け修正を適用
                                from .knowledge.pdf import fix_mojibake_text
                                fixed_text = fix_mojibake_text(page_text)
                                full_text += f"=== ページ {page_num} ===\n{fixed_text}\n\n"
                            else:
                                logger.debug(f"ページ {page_num} でテキストが抽出できませんでした")
                                
                        except Exception as page_error:
                            logger.warning(f"ページ {page_num} の処理エラー: {page_error}")
                            continue
                    
                    if full_text.strip():
                        # PyMuPDF成功時の品質チェック
                        quality_score = self._evaluate_text_quality(full_text)
                        
                        logger.info(f"✅ PyMuPDFフォールバック成功:")
                        logger.info(f"   - 総文字数: {len(full_text):,}")
                        logger.info(f"   - 品質スコア: {quality_score}/100")
                        logger.info(f"   - ページ数: {page_count}")
                        logger.info(f"   - 平均文字/ページ: {len(full_text)/page_count:.0f}")
                        
                        return full_text
                    else:
                        logger.warning("⚠️ PyMuPDFでテキストを抽出できませんでした")
                        raise Exception("PyMuPDF extraction failed - no text found")
                        
            except ImportError:
                logger.warning("⚠️ PyMuPDF (fitz) が利用できません")
                logger.info("🔄 PyPDF2最終フォールバックを使用")
            except Exception as pymupdf_error:
                logger.warning(f"⚠️ PyMuPDF処理失敗: {pymupdf_error}")
                logger.info("🔄 PyPDF2最終フォールバックを使用")
            
            # PyPDF2最終フォールバック
            fallback_text = await self._extract_text_from_pdf_fallback(content)
            return fallback_text
    
    def _evaluate_text_quality(self, text: str) -> int:
        """テキスト品質を0-100のスコアで評価（より詳細版）"""
        if not text or not text.strip():
            return 0
            
        try:
            import re
            
            # 基本統計
            total_chars = len(text)
            lines = text.splitlines()
            non_empty_lines = [line for line in lines if line.strip()]
            
            if total_chars == 0:
                return 0
            
            # 1. 文字種別の品質評価
            japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text))
            english_chars = len(re.findall(r'[a-zA-Z]', text))
            numeric_chars = len(re.findall(r'[0-9]', text))
            valid_chars = japanese_chars + english_chars + numeric_chars
            valid_char_ratio = valid_chars / total_chars if total_chars > 0 else 0
            
            # 2. 文字化け検出（より厳密）
            mojibake_patterns = [
                r'[縺繧繝]',  # 典型的な文字化け
                r'\(cid:\d+\)',  # PDF CID文字化け
                r'[\\ufffd]',  # 置換文字
                r'[\\x00-\\x1f\\x7f-\\x9f]',  # 制御文字など
            ]
            mojibake_count = sum(len(re.findall(pattern, text)) for pattern in mojibake_patterns)
            mojibake_penalty = min(mojibake_count * 2, 40)  # 文字化け1つにつき2点減点
            
            # 3. 構造的品質評価
            has_headers = len(re.findall(r'^#{1,3}\s', text, re.MULTILINE)) > 0
            has_lists = len(re.findall(r'^[\s]*[•\-\*\d+\.]\s', text, re.MULTILINE)) > 0
            has_tables = '|' in text and text.count('|') > 10
            has_pages = '=== ページ' in text
            
            structure_score = 0
            if has_headers: structure_score += 10
            if has_lists: structure_score += 10
            if has_tables: structure_score += 15
            if has_pages: structure_score += 5
            
            # 4. 意味のある内容の比率
            meaningful_lines = 0
            for line in non_empty_lines:
                line = line.strip()
                if len(line) > 5 and re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAFa-zA-Z]', line):
                    meaningful_lines += 1
            
            line_quality = (meaningful_lines / len(non_empty_lines)) * 100 if non_empty_lines else 0
            
            # 5. 長さ品質評価
            length_score = min(len(text) / 100, 20)  # 100文字で1点、最大20点
            
            # 最終スコア計算
            base_score = (
                valid_char_ratio * 30 +  # 有効文字比率（30点満点）
                line_quality * 0.2 +     # 有意義な行の比率（20点満点）
                structure_score +        # 構造的品質（40点満点）
                length_score             # 長さ品質（20点満点）
            )
            
            final_score = max(0, int(base_score - mojibake_penalty))
            
            # 詳細ログ
            logger.debug(f"📊 品質評価詳細:")
            logger.debug(f"   - 有効文字比率: {valid_char_ratio:.2f} ({valid_char_ratio*30:.1f}点)")
            logger.debug(f"   - 行品質: {line_quality:.1f} ({line_quality*0.2:.1f}点)")
            logger.debug(f"   - 構造スコア: {structure_score}点")
            logger.debug(f"   - 長さスコア: {length_score:.1f}点")
            logger.debug(f"   - 文字化けペナルティ: -{mojibake_penalty}点")
            logger.debug(f"   - 最終スコア: {final_score}点")
            
            return min(100, final_score)
            
        except Exception as e:
            logger.warning(f"品質評価エラー: {e}")
            return 50  # デフォルトスコア
    
    async def _extract_text_from_pdf_fallback(self, content: bytes) -> str:
        """PyPDF2フォールバック + 文字化け修復処理（完全版）"""
        logger.info("🔄 PyPDF2フォールバック抽出開始")
        
        try:
            import PyPDF2
            from io import BytesIO
            
            # 文字化け修復辞書（完全版）
            MOJIBAKE_MAPPING = {
                # ユーザー報告の文字化けパターン
                'ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½': '会社名不明',
                'ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½': '請求書',
                'ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½': '支払い',
                # 一般的な文字化けパターン
                'ï¿½': '',  # 空文字に置換
                '': '',    # 空文字除去
                # 半角カタカナの正規化
                'ｶ': 'カ', 'ﾀ': 'タ', 'ﾅ': 'ナ', 'ﾊ': 'ハ', 'ﾏ': 'マ', 'ﾔ': 'ヤ', 'ﾗ': 'ラ', 'ﾜ': 'ワ',
                'ｷ': 'キ', 'ﾁ': 'チ', 'ﾆ': 'ニ', 'ﾋ': 'ヒ', 'ﾐ': 'ミ', 'ﾘ': 'リ',
                'ｸ': 'ク', 'ﾂ': 'ツ', 'ﾇ': 'ヌ', 'ﾌ': 'フ', 'ﾑ': 'ム', 'ﾕ': 'ユ', 'ﾙ': 'ル',
                'ｹ': 'ケ', 'ﾃ': 'テ', 'ﾈ': 'ネ', 'ﾍ': 'ヘ', 'ﾒ': 'メ', 'ﾖ': 'ヨ', 'ﾚ': 'レ',
                'ｺ': 'コ', 'ﾄ': 'ト', 'ﾉ': 'ノ', 'ﾎ': 'ホ', 'ﾓ': 'モ', 'ﾛ': 'ロ', 'ﾝ': 'ン',
                'ｶﾞ': 'ガ', 'ｷﾞ': 'ギ', 'ｸﾞ': 'グ', 'ｹﾞ': 'ゲ', 'ｺﾞ': 'ゴ',
                'ｻ': 'サ', 'ｼ': 'シ', 'ｽ': 'ス', 'ｾ': 'セ', 'ｿ': 'ソ',
                'ｻﾞ': 'ザ', 'ｼﾞ': 'ジ', 'ｽﾞ': 'ズ', 'ｾﾞ': 'ゼ', 'ｿﾞ': 'ゾ',
                'ｱ': 'ア', 'ｲ': 'イ', 'ｳ': 'ウ', 'ｴ': 'エ', 'ｵ': 'オ',
                'ﾀﾞ': 'ダ', 'ﾁﾞ': 'ヂ', 'ﾂﾞ': 'ヅ', 'ﾃﾞ': 'デ', 'ﾄﾞ': 'ド',
                'ﾊﾞ': 'バ', 'ﾋﾞ': 'ビ', 'ﾌﾞ': 'ブ', 'ﾍﾞ': 'ベ', 'ﾎﾞ': 'ボ',
                'ﾊﾟ': 'パ', 'ﾋﾟ': 'ピ', 'ﾌﾟ': 'プ', 'ﾍﾟ': 'ペ', 'ﾎﾟ': 'ポ',
                'ｧ': 'ァ', 'ｨ': 'ィ', 'ｩ': 'ゥ', 'ｪ': 'ェ', 'ｫ': 'ォ',
                'ｬ': 'ャ', 'ｭ': 'ュ', 'ｮ': 'ョ', 'ｯ': 'ッ',
                'ｰ': 'ー', '･': '・',
            }
            
            def fix_mojibake_text(text):
                """文字化けテキストを修復"""
                if not text:
                    return text
                
                # 長いパターンから順に置換（より具体的なパターンを優先）
                sorted_patterns = sorted(MOJIBAKE_MAPPING.items(), key=lambda x: len(x[0]), reverse=True)
                
                fixed_text = text
                for pattern, replacement in sorted_patterns:
                    if pattern in fixed_text:
                        fixed_text = fixed_text.replace(pattern, replacement)
                
                # 追加のクリーンアップ
                fixed_text = fixed_text.replace('\ufffd', '')  # Unicode replacement character
                
                return fixed_text
            
            def check_text_corruption(text):
                """テキストの文字化け度を判定"""
                if not text or len(text) < 10:
                    return False, 0, 0
                
                import re
                
                # 文字化けパターン
                corruption_patterns = [
                    r'ï¿½+',  # UTF-8文字化け
                    r'[]{10,}',  # 長い空文字列
                    r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]{3,}',  # 制御文字
                    r'[^\w\s\u3000-\u30ff\u4e00-\u9faf\u3400-\u4dbf]{10,}',  # 連続記号
                    r'\d+\(\)\[',  # 数字+()[ パターン
                ]
                
                corruption_count = 0
                for pattern in corruption_patterns:
                    matches = re.findall(pattern, text)
                    corruption_count += len(matches)
                
                corruption_ratio = corruption_count / len(text) * 100
                
                # 閾値を下げて敏感に検出
                is_corrupted = corruption_ratio > 2.0 or corruption_count > 5
                
                return is_corrupted, corruption_ratio, corruption_count
            
            # PDFリーダーを作成
            pdf_reader = PyPDF2.PdfReader(BytesIO(content))
            extracted_pages = []
            total_pages = len(pdf_reader.pages)
            corrupted_pages = 0
            
            logger.info(f"📄 PyPDF2で{total_pages}ページの抽出開始")
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    # テキスト抽出
                    page_text = page.extract_text()
                    
                    if page_text and page_text.strip():
                        # 文字化け修復
                        fixed_text = fix_mojibake_text(page_text)
                        
                        # 文字化けチェック
                        is_corrupted, corruption_ratio, corruption_count = check_text_corruption(fixed_text)
                        
                        if is_corrupted:
                            corrupted_pages += 1
                            logger.warning(f"⚠️ ページ{page_num + 1}: 文字化け検出 ({corruption_ratio:.1f}%)")
                        
                        extracted_pages.append(f"\n--- ページ {page_num + 1} ---\n{fixed_text}")
                    else:
                        logger.warning(f"⚠️ ページ{page_num + 1}: テキストなし")
                        extracted_pages.append(f"\n--- ページ {page_num + 1} ---\n[テキストなし]")
                        
                except Exception as page_error:
                    logger.error(f"❌ ページ{page_num + 1}抽出エラー: {page_error}")
                    extracted_pages.append(f"\n--- ページ {page_num + 1} ---\n[抽出エラー: {str(page_error)}]")
            
            # 結果統計
            final_text = "\n".join(extracted_pages)
            logger.info(f"✅ PyPDF2フォールバック完了:")
            logger.info(f"   - 総ページ数: {total_pages}")
            logger.info(f"   - 文字化けページ: {corrupted_pages}")
            logger.info(f"   - 抽出文字数: {len(final_text)}")
            
            return final_text
            
        except Exception as e:
            logger.error(f"❌ PyPDF2フォールバック失敗: {e}")
            return f"PyPDF2フォールバック処理エラー: {str(e)}"
    
    async def _extract_text_from_excel(self, content: bytes) -> str:
        """Excelファイルからテキストを抽出（クリーニングなし・生データ保持）"""
        try:
            import pandas as pd
            from io import BytesIO
            
            # ExcelファイルをBytesIOオブジェクトに変換
            excel_buffer = BytesIO(content)
            
            # 全シートを読み込み
            excel_file = pd.ExcelFile(excel_buffer)
            extracted_text = ""
            
            for sheet_name in excel_file.sheet_names:
                try:
                    # シートをそのまま読み込み（クリーニング一切なし）
                    df = pd.read_excel(excel_buffer, sheet_name=sheet_name, header=None)
                    
                    extracted_text += f"\n=== シート: {sheet_name} ===\n"
                    
                    # 全セルの内容をそのまま保持
                    for index, row in df.iterrows():
                        row_content = []
                        for col_idx, raw_value in enumerate(row):
                            try:
                                # pandas Series エラー対策: 安全に値を取得
                                if hasattr(raw_value, 'item'):
                                    value = raw_value.item() if not pd.isna(raw_value.item()) else None
                                else:
                                    value = raw_value if not pd.isna(raw_value) else None
                                
                                if value is not None:
                                    row_content.append(str(value))
                            except Exception as col_error:
                                logger.debug(f"Excel列処理エラー (行 {index}, 列 {col_idx}): {col_error}")
                                continue
                        if row_content:
                            extracted_text += " | ".join(row_content) + "\n"
                    
                    logger.info(f"📄 シート '{sheet_name}' 処理完了: {len(df)} 行 x {len(df.columns)} 列")
                    
                except Exception as sheet_error:
                    logger.warning(f"⚠️ シート '{sheet_name}' 読み込みエラー: {sheet_error}")
                    extracted_text += f"\n=== シート: {sheet_name} (エラー) ===\nエラー: {str(sheet_error)}\n"
                    continue
            
            logger.info(f"✅ Excel処理完了（生データ保持）: {len(extracted_text)} 文字")
            return extracted_text
            
        except Exception as e:
            logger.error(f"❌ Excel処理エラー（生データ保持）: {e}")
            # エラー発生時は、データ抽出を断念し、空文字列を返すか、適切なエラーメッセージを返す
            # ここではエラーを再raiseして、上位でハンドリングさせることを推奨
            raise
    
    async def _extract_text_from_word(self, content: bytes) -> str:
        """Wordファイルからテキストを抽出"""
        try:
            import docx
            from io import BytesIO
            
            doc = docx.Document(BytesIO(content))
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            return "\n\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"Word処理エラー: {e}")
            raise
    
    async def _extract_text_from_text(self, content: bytes) -> str:
        """テキストファイルから内容を抽出"""
        try:
            # 複数のエンコーディングを試行
            encodings = ['utf-8', 'shift_jis', 'cp932', 'euc-jp', 'iso-2022-jp']
            
            for encoding in encodings:
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            
            # すべて失敗した場合はエラーを無視して読み込み
            return content.decode('utf-8', errors='ignore')
            
        except Exception as e:
            logger.error(f"テキスト処理エラー: {e}")
            raise
    
    async def _extract_text_from_image(self, content: bytes) -> str:
        """画像からOCRでテキストを抽出"""
        try:
            # Gemini Vision APIを使用してOCR
            self._init_gemini_client()
            
            # 画像をbase64エンコード
            import base64
            image_b64 = base64.b64encode(content).decode('utf-8')
            
            # Gemini Vision APIでOCR（実装は環境に応じて調整）
            # ここでは簡単な実装例
            logger.info("🖼️ 画像OCR処理（Gemini Vision API）")
            
            # OCR結果のプレースホルダー
            return "画像からのテキスト抽出（OCR処理が必要）"
            
        except Exception as e:
            logger.error(f"画像OCR処理エラー: {e}")
            return "画像ファイル（テキスト抽出不可）"
    
    def _detect_file_type(self, filename: str) -> str:
        """ファイル拡張子からタイプを判定"""
        filename = filename.lower()
        
        if filename.endswith('.pdf'):
            return 'PDF'
        elif filename.endswith(('.xlsx', '.xls')):
            return 'Excel'
        elif filename.endswith(('.docx', '.doc')):
            return 'Word'
        elif filename.endswith('.csv'):
            return 'CSV'
        elif filename.endswith('.txt'):
            return 'Text'
        elif filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
            return 'Image'
        else:
            return 'Unknown'

    def _estimate_page_count(self, text: str) -> int:
        """テキストからページ数を推定"""
        # 1ページあたり約500トークンと仮定
        tokens = self._count_tokens(text)
        return max(1, (tokens + 499) // 500)

    async def retry_failed_embeddings(self, doc_id: str = None, company_id: str = None, max_retries: int = 10) -> Dict[str, Any]:
        """
        既存のチャンクで失敗したembeddingを再生成
        doc_id: 特定のドキュメントのみ処理（Noneの場合は全て）
        company_id: 特定の会社のみ処理（Noneの場合は全て）
        """
        try:
            from supabase_adapter import get_supabase_client
            supabase = get_supabase_client()
            
            logger.info(f"🔍 失敗したembeddingの検索開始 (doc_id: {doc_id}, company_id: {company_id})")
            
            # 失敗したチャンクを検索（embeddingがNullのもの）
            query = supabase.table("chunks").select("*").is_("embedding", "null")
            
            if doc_id:
                query = query.eq("doc_id", doc_id)
            if company_id:
                query = query.eq("company_id", company_id)
            
            result = query.execute()
            
            if not result.data:
                logger.info("✅ 失敗したembeddingは見つかりませんでした")
                return {
                    "total_failed": 0,
                    "processed": 0,
                    "successful": 0,
                    "still_failed": 0,
                    "retry_attempts": 0
                }
            
            failed_chunks = result.data
            logger.info(f"🔍 失敗したチャンクを発見: {len(failed_chunks)}件")
            
            stats = {
                "total_failed": len(failed_chunks),
                "processed": 0,
                "successful": 0,
                "still_failed": 0,
                "retry_attempts": 0
            }
            
            # チャンクをバッチで処理（50件ずつ）
            batch_size = 50
            for batch_start in range(0, len(failed_chunks), batch_size):
                batch_end = min(batch_start + batch_size, len(failed_chunks))
                batch_chunks = failed_chunks[batch_start:batch_end]
                
                logger.info(f"📦 バッチ処理: {batch_start + 1}-{batch_end}/{len(failed_chunks)}")
                
                # バッチのテキストを抽出
                batch_contents = [chunk["content"] for chunk in batch_chunks]
                batch_indices = list(range(len(batch_contents)))
                
                # embedding生成（リトライ付き）
                embeddings = await self._generate_embeddings_batch(batch_contents)
                
                # 失敗したものを再試行
                failed_indices = [i for i, emb in enumerate(embeddings) if emb is None]
                retry_count = 0
                
                while failed_indices and retry_count < max_retries:
                    retry_count += 1
                    stats["retry_attempts"] = max(stats["retry_attempts"], retry_count)
                    
                    logger.info(f"🔄 バッチ再試行 {retry_count}/{max_retries}: {len(failed_indices)}件")
                    
                    retry_embeddings = await self._generate_embeddings_batch(batch_contents, failed_indices)
                    
                    # 結果をマージ
                    for i in failed_indices:
                        if retry_embeddings[i] is not None:
                            embeddings[i] = retry_embeddings[i]
                    
                    failed_indices = [i for i in failed_indices if embeddings[i] is None]
                    
                    if failed_indices:
                        await asyncio.sleep(2.0)  # リトライ間隔
                
                # データベースを更新
                for i, chunk in enumerate(batch_chunks):
                    embedding_vector = embeddings[i]
                    chunk_id = chunk["id"]
                    
                    try:
                        if embedding_vector:
                            # embeddingを更新
                            update_result = supabase.table("chunks").update({
                                "embedding": embedding_vector,
                                "updated_at": datetime.now().isoformat()
                            }).eq("id", chunk_id).execute()
                            
                            if update_result.data:
                                stats["successful"] += 1
                                logger.info(f"✅ embedding更新成功: chunk_id={chunk_id}")
                            else:
                                stats["still_failed"] += 1
                                logger.error(f"❌ embedding更新失敗: chunk_id={chunk_id}")
                        else:
                            stats["still_failed"] += 1
                            logger.warning(f"⚠️ embedding生成失敗: chunk_id={chunk_id}")
                        
                        stats["processed"] += 1
                        
                    except Exception as update_error:
                        logger.error(f"❌ チャンク更新エラー (chunk_id={chunk_id}): {update_error}")
                        stats["still_failed"] += 1
                        stats["processed"] += 1
                
                # バッチ間の待機
                if batch_end < len(failed_chunks):
                    await asyncio.sleep(1.0)
            
            # 最終結果
            logger.info(f"🎉 embedding修復完了:")
            logger.info(f"   - 処理対象: {stats['total_failed']}件")
            logger.info(f"   - 処理完了: {stats['processed']}件")
            logger.info(f"   - 成功: {stats['successful']}件")
            logger.info(f"   - 失敗: {stats['still_failed']}件")
            logger.info(f"   - 最大再試行回数: {stats['retry_attempts']}回")
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ embedding修復処理エラー: {e}", exc_info=True)
            raise
    
    async def _retry_failed_embeddings_post_processing(self, doc_id: str, company_id: str, 
                                                     doc_name: str, max_retries: int = 5) -> Dict[str, Any]:
        """
        全処理完了後に失敗したembeddingを再処理する
        レートリミット回避のため、より慎重な再試行を行う
        """
        try:
            from supabase_adapter import get_supabase_client
            supabase = get_supabase_client()
            
            logger.info(f"🔄 {doc_name}: 失敗したembeddingの再処理開始")
            
            # 失敗したチャンクを検索（embeddingがNullのもの）
            query = supabase.table("chunks").select("*").eq("doc_id", doc_id).is_("embedding", "null")
            result = query.execute()
            
            if not result.data:
                logger.info(f"✅ {doc_name}: 再処理が必要なチャンクはありません")
                return {
                    "total_failed": 0,
                    "processed": 0,
                    "successful": 0,
                    "still_failed": 0,
                    "retry_attempts": 0
                }
            
            failed_chunks = result.data
            logger.info(f"🔍 {doc_name}: 再処理対象チャンク {len(failed_chunks)}件")
            
            stats = {
                "total_failed": len(failed_chunks),
                "processed": 0,
                "successful": 0,
                "still_failed": 0,
                "retry_attempts": 0
            }
            
            # レートリミット回避のため、より小さなバッチで処理
            batch_size = 10  # 通常の50から10に減らす
            
            for batch_start in range(0, len(failed_chunks), batch_size):
                batch_end = min(batch_start + batch_size, len(failed_chunks))
                batch_chunks = failed_chunks[batch_start:batch_end]
                
                logger.info(f"🔄 {doc_name}: 再処理バッチ {batch_start + 1}-{batch_end}/{len(failed_chunks)}")
                
                # レートリミット回避のため、バッチ間に長めの待機
                if batch_start > 0:
                    await asyncio.sleep(2.0)
                
                # バッチのテキストを抽出
                batch_contents = [chunk["content"] for chunk in batch_chunks]
                
                # embedding生成（より慎重なリトライ）
                embeddings = await self._generate_embeddings_batch(batch_contents)
                
                # 失敗したものを段階的に再試行
                failed_indices = [i for i, emb in enumerate(embeddings) if emb is None]
                retry_count = 0
                
                while failed_indices and retry_count < max_retries:
                    retry_count += 1
                    stats["retry_attempts"] = max(stats["retry_attempts"], retry_count)
                    
                    # レートリミット回避のため、再試行間隔を段階的に増加
                    sleep_time = min(retry_count * 2.0, 10.0)
                    logger.info(f"🔄 {doc_name}: 再試行 {retry_count}/{max_retries} - {len(failed_indices)}件 ({sleep_time}秒待機)")
                    await asyncio.sleep(sleep_time)
                    
                    retry_embeddings = await self._generate_embeddings_batch(batch_contents, failed_indices)
                    
                    # 結果をマージ
                    for i in failed_indices:
                        if retry_embeddings[i] is not None:
                            embeddings[i] = retry_embeddings[i]
                    
                    failed_indices = [i for i in failed_indices if embeddings[i] is None]
                    
                    if not failed_indices:
                        logger.info(f"✅ {doc_name}: 再試行バッチ完全成功")
                        break
                
                # データベースを更新
                for i, chunk in enumerate(batch_chunks):
                    embedding_vector = embeddings[i]
                    chunk_id = chunk["id"]
                    
                    try:
                        if embedding_vector:
                            # embeddingを更新
                            update_result = supabase.table("chunks").update({
                                "embedding": embedding_vector,
                                "updated_at": datetime.now().isoformat()
                            }).eq("id", chunk_id).execute()
                            
                            if update_result.data:
                                stats["successful"] += 1
                                logger.debug(f"✅ {doc_name}: embedding更新成功 chunk_id={chunk_id}")
                            else:
                                stats["still_failed"] += 1
                                logger.error(f"❌ {doc_name}: embedding更新失敗 chunk_id={chunk_id}")
                        else:
                            stats["still_failed"] += 1
                            logger.warning(f"⚠️ {doc_name}: embedding生成最終失敗 chunk_id={chunk_id}")
                        
                        stats["processed"] += 1
                        
                    except Exception as update_error:
                        logger.error(f"❌ {doc_name}: チャンク更新エラー chunk_id={chunk_id}: {update_error}")
                        stats["still_failed"] += 1
                        stats["processed"] += 1
            
            # 最終結果
            logger.info(f"🏁 {doc_name}: embedding再処理完了")
            logger.info(f"   - 処理対象: {stats['total_failed']}件")
            logger.info(f"   - 成功: {stats['successful']}件")
            logger.info(f"   - 失敗: {stats['still_failed']}件")
            logger.info(f"   - 最大再試行: {stats['retry_attempts']}回")
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ {doc_name}: 失敗embedding再処理エラー: {e}", exc_info=True)
            raise

document_processor = DocumentProcessor()