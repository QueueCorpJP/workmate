"""
📤 レコードベース ドキュメント処理システム
🧩 1レコード（1行）単位でのチャンク分割
🧠 embedding生成を統合（Gemini Flash - 768次元）
🗃 Supabase保存（document_sources + chunks）

構造化データ（Excel）専用の完全なRAG対応ドキュメント処理パイプライン
"""

import os
import uuid
import logging
import asyncio
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
import tiktoken
from fastapi import HTTPException, UploadFile
from google import genai
import psycopg2
from psycopg2.extras import execute_values

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentProcessorRecordBased:
    """レコードベースドキュメント処理のメインクラス"""
    
    def __init__(self):
        self.gemini_client = None
        self.vertex_ai_client = None
        self.use_vertex_ai = os.getenv("USE_VERTEX_AI", "true").lower() == "true"
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
        
        # Vertex AI使用時はモデル名をそのまま使用、Gemini API使用時はmodels/プレフィックスを追加
        if not self.use_vertex_ai and not self.embedding_model.startswith("models/"):
            self.embedding_model = f"models/{self.embedding_model}"
            
        self.chunk_size_tokens = 400  # 300-500トークンの中間値
        self.chunk_overlap_tokens = 50  # チャンク間のオーバーラップ
        self.max_chunk_size_chars = 2000  # 文字数での上限
        
        # トークンカウンター初期化
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"tiktoken初期化失敗: {e}")
            self.tokenizer = None
        
        # Vertex AIが利用できない場合はGemini APIにフォールバック
        if self.use_vertex_ai:
            try:
                self._init_vertex_ai_client()
            except Exception as e:
                logger.warning(f"⚠️ Vertex AI初期化失敗、Gemini APIにフォールバック: {e}")
                self.use_vertex_ai = False
                self._init_gemini_client()
        else:
            self._init_gemini_client()
    
    def _init_vertex_ai_client(self):
        """Vertex AI クライアントを初期化"""
        try:
            from modules.vertex_ai_embedding import get_vertex_ai_embedding_client, vertex_ai_embedding_available
            
            if not vertex_ai_embedding_available():
                logger.error("❌ Vertex AI Embeddingが利用できません")
                raise ValueError("Vertex AI Embeddingが利用できません")
            
            self.vertex_ai_client = get_vertex_ai_embedding_client()
            if not self.vertex_ai_client:
                raise ValueError("Vertex AI クライアントの取得に失敗しました")
            
            logger.info(f"🧠 Vertex AI クライアント初期化完了: {self.embedding_model} (3072次元)")
            
        except Exception as e:
            logger.error(f"❌ Vertex AI クライアント初期化エラー: {e}")
            raise
    
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
    
    async def process_uploaded_file(self, file: UploadFile, user_id: str, company_id: str) -> Dict[str, Any]:
        """
        アップロードされたファイルを処理（レコードベース）
        
        Args:
            file: アップロードファイル
            user_id: ユーザーID
            company_id: 会社ID
            
        Returns:
            処理結果の辞書
        """
        try:
            logger.info(f"📤 レコードベースファイル処理開始: {file.filename}")
            
            # ファイル内容を読み取り
            file_content = await file.read()
            file_size_mb = len(file_content) / (1024 * 1024)
            
            # ファイル拡張子を取得
            file_extension = '.' + file.filename.split('.')[-1].lower()
            
            # Excelファイルの場合はレコードベース処理
            if file_extension in ['.xlsx', '.xls']:
                return await self._process_excel_file_record_based(
                    file_content, file.filename, user_id, company_id, file_size_mb
                )
            else:
                # 他のファイル形式は従来の処理にフォールバック
                logger.info(f"⚠️ {file_extension} はレコードベース処理対象外、従来処理にフォールバック")
                from modules.document_processor import DocumentProcessor
                fallback_processor = DocumentProcessor()
                return await fallback_processor.process_uploaded_file(file, user_id, company_id)
                
        except Exception as e:
            logger.error(f"❌ レコードベースファイル処理エラー: {e}")
            raise HTTPException(status_code=500, detail=f"ファイル処理中にエラーが発生しました: {str(e)}")
    
    async def _process_excel_file_record_based(self, content: bytes, filename: str, user_id: str, company_id: str, file_size_mb: float) -> Dict[str, Any]:
        """Excelファイルをレコードベースで処理"""
        try:
            logger.info(f"📊 Excelファイルレコードベース処理開始: {filename}")
            
            # レコードベースExcelクリーナーでデータを取得
            from modules.excel_data_cleaner_record_based import ExcelDataCleanerRecordBased
            cleaner = ExcelDataCleanerRecordBased()
            records = cleaner.clean_excel_data(content)
            
            if not records:
                raise ValueError("Excelファイルから有効なレコードが抽出できませんでした")
            
            logger.info(f"📋 抽出されたレコード数: {len(records)}")
            
            # ドキュメントをデータベースに保存
            doc_id = await self._save_document_to_db(filename, user_id, company_id, file_size_mb, len(records))
            
            # レコードをチャンクとして保存
            saved_chunks = await self._save_records_as_chunks(doc_id, records, company_id)
            
            # Embeddingを生成
            embedding_result = await self._generate_embeddings_for_records(doc_id, records)
            
            result = {
                "document_id": doc_id,
                "filename": filename,
                "file_size_mb": file_size_mb,
                "text_length": sum(len(record.get('content', '')) for record in records),
                "total_chunks": len(records),
                "saved_chunks": saved_chunks,
                "successful_embeddings": embedding_result.get("successful_embeddings", 0),
                "failed_embeddings": embedding_result.get("failed_embeddings", 0)
            }
            
            logger.info(f"✅ Excelレコードベース処理完了: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Excelレコードベース処理エラー: {e}")
            raise
    
    async def _save_document_to_db(self, filename: str, user_id: str, company_id: str, file_size_mb: float, record_count: int) -> str:
        """ドキュメント情報をデータベースに保存"""
        try:
            from supabase_adapter import insert_data
            
            doc_id = str(uuid.uuid4())
            
            document_data = {
                "id": doc_id,
                "name": filename,
                "type": "excel_record_based",
                "page_count": record_count,
                "company_id": company_id,
                "uploaded_by": user_id,
                "uploaded_at": datetime.now().isoformat(),
                "active": True,
                "doc_id": doc_id  # ドキュメント識別子として自身のIDを設定
            }
            
            # specialコラムは絶対に設定しない（ユーザーの要求通り）
            
            logger.info(f"🔄 document_sourcesテーブルへの保存開始（レコードベース）: {doc_id} - {filename}")
            result = insert_data("document_sources", document_data)
            
            if result and result.data:
                logger.info(f"✅ document_sourcesテーブル保存完了（レコードベース）: {doc_id} - {filename}")
                return doc_id
            else:
                logger.error(f"❌ document_sourcesテーブル保存失敗（レコードベース）: result={result}")
                raise Exception("document_sourcesテーブルへのドキュメント保存に失敗しました")
                
        except Exception as e:
            logger.error(f"❌ document_sourcesテーブル保存エラー（レコードベース）: {e}")
            raise
    
    async def _save_records_as_chunks(self, doc_id: str, records: List[Dict[str, Any]], company_id: str) -> int:
        """レコードをチャンクとしてデータベースに保存"""
        try:
            from supabase_adapter import get_supabase_client
            supabase = get_supabase_client()
            
            chunks_data = []
            
            for i, record in enumerate(records):
                chunk_data = {
                    "id": str(uuid.uuid4()),
                    "doc_id": doc_id,
                    "content": record.get('content', ''),
                    "chunk_index": i,
                    "company_id": company_id,  # company_idフィールドを追加
                    "metadata": {
                        "source_sheet": record.get('source_sheet', ''),
                        "record_index": record.get('record_index', i),
                        "record_type": record.get('record_type', 'single'),
                        "chunk_index": record.get('chunk_index', 0) if record.get('record_type') == 'split' else None
                    },
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                chunks_data.append(chunk_data)
            
            # バッチでチャンクを保存
            batch_size = 100
            saved_count = 0
            
            for i in range(0, len(chunks_data), batch_size):
                batch = chunks_data[i:i + batch_size]
                result = supabase.table("chunks").insert(batch).execute()
                
                if result.data:
                    saved_count += len(result.data)
                    logger.info(f"📦 チャンクバッチ保存: {len(result.data)}件 ({saved_count}/{len(chunks_data)})")
                else:
                    logger.warning(f"⚠️ チャンクバッチ保存失敗: バッチ {i//batch_size + 1}")
            
            logger.info(f"✅ 全チャンク保存完了: {saved_count}/{len(chunks_data)}")
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ チャンク保存エラー: {e}")
            raise
    
    async def _generate_embeddings_for_records(self, doc_id: str, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """レコードのEmbeddingを生成"""
        try:
            logger.info(f"🧠 レコードEmbedding生成開始: {len(records)}件")
            
            # 自動Embedding生成が有効かチェック
            auto_generate = os.getenv("AUTO_GENERATE_EMBEDDINGS", "false").lower() == "true"
            if not auto_generate:
                logger.info("🔄 AUTO_GENERATE_EMBEDDINGS=false のため、Embedding生成をスキップ")
                return {"successful_embeddings": 0, "failed_embeddings": 0}
            
            # 自動Embedding生成を実行
            from modules.auto_embedding import auto_generate_embeddings_for_document
            success = await auto_generate_embeddings_for_document(doc_id, max_chunks=len(records))
            
            if success:
                # 成功したEmbedding数を取得
                from supabase_adapter import get_supabase_client
                supabase = get_supabase_client()
                
                result = supabase.table("chunks").select("id,embedding").eq("doc_id", doc_id).execute()
                
                if result.data:
                    successful_count = len([chunk for chunk in result.data if chunk.get('embedding')])
                    failed_count = len(result.data) - successful_count
                    
                    logger.info(f"🎉 レコードEmbedding生成完了: {successful_count}成功, {failed_count}失敗")
                    return {"successful_embeddings": successful_count, "failed_embeddings": failed_count}
            
            return {"successful_embeddings": 0, "failed_embeddings": len(records)}
            
        except Exception as e:
            logger.error(f"❌ レコードEmbedding生成エラー: {e}")
            return {"successful_embeddings": 0, "failed_embeddings": len(records)}

# グローバルインスタンス
document_processor_record_based = DocumentProcessorRecordBased()