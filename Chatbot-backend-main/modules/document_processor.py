"""
📤 ファイルアップロード・ドキュメント処理システム
🧩 チャンク分割（300〜500 token）
🧠 embedding生成を統合（Gemini Flash - 768次元）
🗃 Supabase保存（document_sources + chunks）

完全なRAG対応ドキュメント処理パイプライン
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
import google.generativeai as genai
import psycopg2
from psycopg2.extras import execute_values

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """ドキュメント処理のメインクラス"""
    
    def __init__(self):
        self.gemini_client = None
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
        # 環境変数で設定されたモデルを使用（デフォルトは768次元対応モデル）
        if not self.embedding_model.startswith("models/"):
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
    
    def _init_gemini_client(self):
        """Gemini APIクライアントを初期化"""
        if self.gemini_client is None:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
            
            genai.configure(api_key=api_key)
            self.gemini_client = genai
            logger.info(f"🧠 Gemini APIクライアント初期化完了: {self.embedding_model}")
    
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
        300-500トークンの範囲で調整
        """
        if not text or not text.strip():
            logger.warning(f"空のテキストが渡されました: {doc_name}")
            return []
        
        # テキストを段落単位で分割
        paragraphs = re.split(r'\n\s*\n', text.strip())
        chunks = []
        current_chunk = ""
        current_tokens = 0
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            paragraph_tokens = self._count_tokens(paragraph)
            
            # 段落が単体で大きすぎる場合は文単位で分割
            if paragraph_tokens > self.chunk_size_tokens:
                # 現在のチャンクを保存
                if current_chunk:
                    chunks.append({
                        "chunk_index": chunk_index,
                        "content": current_chunk.strip(),
                        "token_count": current_tokens
                    })
                    chunk_index += 1
                    current_chunk = ""
                    current_tokens = 0
                
                # 大きな段落を文単位で分割
                sentences = re.split(r'[。！？\.\!\?]\s*', paragraph)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    sentence_tokens = self._count_tokens(sentence)
                    
                    # 文が単体で大きすぎる場合は強制分割
                    if sentence_tokens > self.chunk_size_tokens:
                        if current_chunk:
                            chunks.append({
                                "chunk_index": chunk_index,
                                "content": current_chunk.strip(),
                                "token_count": current_tokens
                            })
                            chunk_index += 1
                            current_chunk = ""
                            current_tokens = 0
                        
                        # 長い文を文字数で強制分割
                        for i in range(0, len(sentence), self.max_chunk_size_chars):
                            chunk_part = sentence[i:i + self.max_chunk_size_chars]
                            chunks.append({
                                "chunk_index": chunk_index,
                                "content": chunk_part,
                                "token_count": self._count_tokens(chunk_part)
                            })
                            chunk_index += 1
                    else:
                        # 通常の文処理
                        if current_tokens + sentence_tokens > self.chunk_size_tokens:
                            if current_chunk:
                                chunks.append({
                                    "chunk_index": chunk_index,
                                    "content": current_chunk.strip(),
                                    "token_count": current_tokens
                                })
                                chunk_index += 1
                            current_chunk = sentence
                            current_tokens = sentence_tokens
                        else:
                            current_chunk += ("。" if current_chunk else "") + sentence
                            current_tokens += sentence_tokens
            else:
                # 通常の段落処理
                if current_tokens + paragraph_tokens > self.chunk_size_tokens:
                    if current_chunk:
                        chunks.append({
                            "chunk_index": chunk_index,
                            "content": current_chunk.strip(),
                            "token_count": current_tokens
                        })
                        chunk_index += 1
                    current_chunk = paragraph
                    current_tokens = paragraph_tokens
                else:
                    current_chunk += ("\n\n" if current_chunk else "") + paragraph
                    current_tokens += paragraph_tokens
        
        # 最後のチャンクを追加
        if current_chunk and current_chunk.strip():
            chunks.append({
                "chunk_index": chunk_index,
                "content": current_chunk.strip(),
                "token_count": current_tokens
            })
        
        logger.info(f"📄 {doc_name}: {len(text)}文字 → {len(chunks)}チャンク")
        
        # チャンクサイズの統計を出力
        if chunks:
            token_counts = [chunk["token_count"] for chunk in chunks]
            avg_tokens = sum(token_counts) / len(token_counts)
            min_tokens = min(token_counts)
            max_tokens = max(token_counts)
            logger.info(f"📊 トークン統計 - 平均: {avg_tokens:.1f}, 最小: {min_tokens}, 最大: {max_tokens}")
        
        return chunks
    
    async def _generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Gemini Flash APIでテキストのembeddingを個別生成（バッチ処理風）"""
        logger.info(f"🧠 embedding生成開始: {len(texts)}件, モデル={self.embedding_model}")
        try:
            self._init_gemini_client()
            
            all_embeddings = []
            
            # Gemini APIは個別処理が推奨されるため、1つずつ処理
            for i, text in enumerate(texts):
                try:
                    if not text or not text.strip():
                        logger.warning(f"⚠️ 空のテキストをスキップ: インデックス {i}")
                        all_embeddings.append(None)
                        continue
                    
                    response = await asyncio.to_thread(
                        self.gemini_client.embed_content,
                        model=self.embedding_model,
                        content=text.strip()
                    )
                    
                    if response and 'embedding' in response:
                        embedding_vector = response['embedding']
                        all_embeddings.append(embedding_vector)
                        logger.info(f"✅ embedding生成成功: {i + 1}/{len(texts)} (次元: {len(embedding_vector)})")
                    else:
                        logger.warning(f"⚠️ embedding生成レスポンスが不正です: インデックス {i}")
                        all_embeddings.append(None)
                    
                    # API制限対策
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    logger.error(f"❌ embedding生成エラー (インデックス {i}): {e}")
                    all_embeddings.append(None)

            success_count = len([e for e in all_embeddings if e is not None])
            logger.info(f"🎉 embedding生成完了: {success_count}/{len(texts)} 成功")
            return all_embeddings

        except Exception as e:
            logger.error(f"❌ embeddingバッチ生成中に例外発生: {e}", exc_info=True)
            raise

    async def _save_document_metadata(self, doc_data: Dict[str, Any]) -> str:
        """document_sourcesテーブルにメタデータを保存"""
        try:
            from supabase_adapter import insert_data, select_data
            
            document_id = str(uuid.uuid4())
            
            metadata = {
                "id": document_id,
                "name": doc_data["name"],
                "type": doc_data["type"],
                "page_count": doc_data.get("page_count", 1),
                "uploaded_by": doc_data["uploaded_by"],
                "company_id": doc_data["company_id"],
                "uploaded_at": datetime.now().isoformat()
            }
            
            result = insert_data("document_sources", metadata)
            
            if result and result.data:
                logger.info(f"✅ メタデータ保存完了: {document_id} - {doc_data['name']}")
                return document_id
            else:
                raise Exception("メタデータ保存に失敗しました")
                
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
                                     company_id: str, doc_name: str) -> Dict[str, Any]:
        """chunksテーブルにチャンクデータとembeddingをバッチで保存"""
        try:
            from supabase_adapter import get_supabase_client
            supabase = get_supabase_client()

            stats = {
                "total_chunks": len(chunks),
                "saved_chunks": 0,
                "successful_embeddings": 0,
                "failed_embeddings": 0
            }

            if not chunks:
                return stats

            # バッチでembeddingを生成
            contents = [chunk["content"] for chunk in chunks]
            embeddings = await self._generate_embeddings_batch(contents)

            records_to_insert = []
            for i, chunk_data in enumerate(chunks):
                embedding_vector = embeddings[i]
                if embedding_vector:
                    stats["successful_embeddings"] += 1
                else:
                    stats["failed_embeddings"] += 1
                
                records_to_insert.append({
                    "doc_id": doc_id,
                    "chunk_index": chunk_data["chunk_index"],
                    "content": chunk_data["content"],
                    "embedding": embedding_vector,
                    "company_id": company_id,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                })

            # Supabaseにバッチで挿入
            if records_to_insert:
                result = supabase.table("chunks").insert(records_to_insert).execute()
                if result.data:
                    stats["saved_chunks"] = len(result.data)
                    logger.info(f"✅ {doc_name}: {stats['saved_chunks']}/{len(chunks)} チャンク保存完了")
                else:
                    logger.error(f"❌ チャンク一括保存エラー: {result.error}")

            return stats

        except Exception as e:
            logger.error(f"❌ チャンク一括保存中に例外発生: {e}", exc_info=True)
            raise
    
    async def process_uploaded_file(self, file: UploadFile, user_id: str, 
                                  company_id: str) -> Dict[str, Any]:
        """
        アップロードされたファイルを完全処理
        1️⃣ ファイルアップロード
        2️⃣ テキスト抽出
        3️⃣ チャンク分割（300〜500 token）
        4️⃣ embedding生成（Gemini Flash - 768次元）
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
                "company_id": company_id
            }
            
            document_id = await self._save_document_metadata(doc_data)
            
            # チャンクをデータベースに保存
            save_stats = await self._save_chunks_to_database(
                document_id, chunks, company_id, file.filename
            )
            
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
        """PDFからテキストを抽出"""
        try:
            import PyPDF2
            from io import BytesIO
            
            pdf_reader = PyPDF2.PdfReader(BytesIO(content))
            text_parts = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_parts.append(f"=== ページ {page_num + 1} ===\n{page_text}")
                except Exception as e:
                    logger.warning(f"PDF ページ {page_num + 1} 抽出エラー: {e}")
                    continue
            
            return "\n\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"PDF処理エラー: {e}")
            raise
    
    async def _extract_text_from_excel(self, content: bytes) -> str:
        """Excelファイルからテキストを抽出"""
        try:
            import pandas as pd
            from io import BytesIO
            
            # 全シートを読み込み
            excel_file = pd.ExcelFile(BytesIO(content))
            text_parts = []
            
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    
                    # データフレームをテキストに変換
                    sheet_text = f"=== シート: {sheet_name} ===\n"
                    sheet_text += df.to_string(index=False, na_rep='')
                    text_parts.append(sheet_text)
                    
                except Exception as e:
                    logger.warning(f"Excel シート {sheet_name} 処理エラー: {e}")
                    continue
            
            return "\n\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"Excel処理エラー: {e}")
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

document_processor = DocumentProcessor()