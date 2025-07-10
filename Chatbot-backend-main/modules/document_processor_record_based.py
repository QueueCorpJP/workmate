"""
📤 レコードベースドキュメント処理システム
🗃 Excel・CSV等の構造化データを行単位で処理
🧠 各レコードごとにembedding生成
🔍 表形式データの検索・質問応答に最適化

Excelファイルなどの構造化データを行（レコード）単位で処理し、
テキストチャンクではなく、データベースのレコードとして扱う
"""

import os
import uuid
import logging
import asyncio
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
from fastapi import HTTPException, UploadFile
from .document_processor import DocumentProcessor
from .excel_data_cleaner import ExcelDataCleaner
from .multi_api_embedding import get_multi_api_embedding_client, multi_api_embedding_available

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentProcessorRecordBased:
    """レコードベースドキュメント処理のメインクラス"""
    
    def __init__(self):
        # 基本的なDocumentProcessorの設定を継承
        self.base_processor = DocumentProcessor()
        self.excel_cleaner = ExcelDataCleaner()
        
        # レコードベース処理固有の設定
        self.max_record_length = 1000  # 1レコードの最大文字数
        self.min_meaningful_columns = 2  # 意味のある列の最小数
        
        logger.info("✅ レコードベースドキュメントプロセッサー初期化完了")
    
    async def process_uploaded_file(self, file: UploadFile, user_id: str, 
                                  company_id: str) -> Dict[str, Any]:
        """
        アップロードされたファイルをレコードベースで処理
        1️⃣ Excelファイル読み込み
        2️⃣ 行単位でデータ抽出
        3️⃣ 各レコードのembedding生成
        4️⃣ レコード単位でSupabase保存
        """
        try:
            logger.info(f"🚀 レコードベースファイル処理開始: {file.filename}")
            
            # ファイル内容を読み込み
            file_content = await file.read()
            file_size_mb = len(file_content) / (1024 * 1024)
            
            logger.info(f"📁 ファイルサイズ: {file_size_mb:.2f} MB")
            
            # Excel形式のみサポート
            if not self._is_excel_file(file.filename):
                raise HTTPException(
                    status_code=400, 
                    detail="レコードベース処理はExcelファイル（.xlsx, .xls）のみサポートしています"
                )
            
            # Excelファイルをレコード単位で処理
            records = await self._extract_records_from_excel(file_content, file.filename)
            
            if not records:
                raise HTTPException(
                    status_code=400, 
                    detail="Excelファイルから有効なレコードを抽出できませんでした"
                )
            
            logger.info(f"📊 抽出レコード数: {len(records)}")
            
            # ドキュメントメタデータを保存
            doc_data = {
                "name": file.filename,
                "type": "Excel (レコードベース)",
                "page_count": self._calculate_page_count(records),
                "uploaded_by": user_id,
                "company_id": company_id,
                "special": f"レコード数: {len(records)}"
            }
            
            document_id = await self.base_processor._save_document_metadata(doc_data)
            
            # レコードをデータベースに保存
            save_stats = await self._save_records_to_database(
                document_id, records, company_id, file.filename
            )
            
            # 処理結果を返す
            result = {
                "success": True,
                "document_id": document_id,
                "filename": file.filename,
                "file_size_mb": round(file_size_mb, 2),
                "text_length": save_stats.get("total_text_length", 0),  # 追加
                "record_count": len(records),
                "saved_records": save_stats["saved_chunks"],
                "successful_embeddings": save_stats["successful_embeddings"],
                "failed_embeddings": save_stats["failed_embeddings"],
                "processing_type": "record_based",
                "message": f"✅ {file.filename} のレコードベース処理・embedding生成が完了しました"
            }
            
            logger.info(f"🎉 レコードベースファイル処理完了: {file.filename}")
            return result
            
        except Exception as e:
            logger.error(f"❌ レコードベースファイル処理エラー: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"レコードベースファイル処理中にエラーが発生しました: {str(e)}"
            )
    
    async def _extract_records_from_excel(self, content: bytes, filename: str) -> List[Dict[str, Any]]:
        """Excelファイルからレコードを抽出"""
        try:
            logger.info(f"📊 Excel レコード抽出開始: {filename}")
            
            # ExcelDataCleanerを使用してデータを構造化
            cleaned_text = self.excel_cleaner.clean_excel_data(content)
            
            # pandas でExcelファイルを直接読み込み
            excel_file = pd.ExcelFile(content)
            all_records = []
            
            for sheet_name in excel_file.sheet_names:
                try:
                    logger.info(f"📋 シート処理開始: {sheet_name}")
                    
                    # シートをDataFrameとして読み込み
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=0)
                    
                    if df.empty:
                        logger.warning(f"⚠️ シート {sheet_name} は空です")
                        continue
                    
                    # 空の行・列を削除
                    df = df.dropna(how='all').dropna(axis=1, how='all')
                    
                    if df.empty:
                        continue
                    
                    # シートのレコードを抽出
                    sheet_records = self._extract_records_from_dataframe(df, sheet_name)
                    all_records.extend(sheet_records)
                    
                    logger.info(f"✅ シート {sheet_name}: {len(sheet_records)} レコード抽出")
                    
                except Exception as e:
                    logger.warning(f"⚠️ シート {sheet_name} 処理エラー: {e}")
                    continue
            
            if not all_records:
                logger.warning("⚠️ 全シートでレコード抽出に失敗")
                return []
            
            logger.info(f"🎉 Excel レコード抽出完了: {len(all_records)} レコード")
            return all_records
            
        except Exception as e:
            logger.error(f"❌ Excel レコード抽出エラー: {e}")
            raise
    
    def _extract_records_from_dataframe(self, df: pd.DataFrame, sheet_name: str) -> List[Dict[str, Any]]:
        """DataFrameからレコードを抽出"""
        records = []
        
        try:
            # 列名を正規化
            df.columns = [self._normalize_column_name(str(col)) for col in df.columns]
            
            # 各行をレコードとして処理
            for index, row in df.iterrows():
                try:
                    # 空の行をスキップ
                    if row.isna().all():
                        continue
                    
                    # レコードの内容を構築
                    record_data = {}
                    record_parts = []
                    meaningful_columns = 0
                    
                    for col in df.columns:
                        value = row[col]
                        if pd.notna(value) and str(value).strip():
                            clean_value = str(value).strip()
                            record_data[col] = clean_value
                            record_parts.append(f"{col}: {clean_value}")
                            meaningful_columns += 1
                    
                    # 意味のある列が少ない場合はスキップ
                    if meaningful_columns < self.min_meaningful_columns:
                        continue
                    
                    # レコードの内容を作成
                    record_content = " | ".join(record_parts)
                    
                    # レコードの長さ制限
                    if len(record_content) > self.max_record_length:
                        record_content = record_content[:self.max_record_length] + "..."
                    
                    # メタデータを追加
                    record = {
                        "chunk_index": len(records),  # chunks テーブルとの互換性のため
                        "content": record_content,
                        "token_count": self.base_processor._count_tokens(record_content),
                        "sheet_name": sheet_name,
                        "row_index": index,
                        "record_data": record_data,
                        "column_count": meaningful_columns
                    }
                    
                    records.append(record)
                    
                except Exception as e:
                    logger.warning(f"⚠️ 行 {index} 処理エラー: {e}")
                    continue
            
            return records
            
        except Exception as e:
            logger.error(f"❌ DataFrame レコード抽出エラー: {e}")
            return []
    
    def _normalize_column_name(self, column_name: str) -> str:
        """列名を正規化"""
        # 無意味な列名を意味のあるものに置換
        if not column_name or column_name.startswith('Unnamed'):
            return f"列_{uuid.uuid4().hex[:8]}"
        
        # 文字列を清潔に
        normalized = str(column_name).strip()
        
        # 空白を置換
        normalized = normalized.replace('\n', ' ').replace('\r', ' ')
        
        return normalized
    
    async def _save_records_to_database(self, doc_id: str, records: List[Dict[str, Any]],
                                      company_id: str, doc_name: str, max_retries: int = 3) -> Dict[str, Any]:
        """レコードをデータベースに保存（chunksテーブルを使用）"""
        try:
            from supabase_adapter import get_supabase_client
            supabase = get_supabase_client()

            stats = {
                "total_chunks": len(records),
                "saved_chunks": 0,
                "successful_embeddings": 0,
                "failed_embeddings": 0,
                "retry_attempts": 0,
                "total_text_length": 0  # 新しく追加
            }

            if not records:
                return stats

            batch_size = 20  # レコードベースでは小さなバッチサイズを使用
            total_batches = (len(records) + batch_size - 1) // batch_size
            
            logger.info(f"🚀 {doc_name}: {len(records)}レコードを{batch_size}個単位で処理開始")
            logger.info(f"📊 予想バッチ数: {total_batches}")

            # レコード単位でembedding生成→即座にinsert
            for batch_num in range(0, len(records), batch_size):
                batch_records = records[batch_num:batch_num + batch_size]
                current_batch = (batch_num // batch_size) + 1
                
                logger.info(f"🧠 バッチ {current_batch}/{total_batches}: {len(batch_records)}レコードのembedding生成開始")
                
                # このバッチのembedding生成
                batch_contents = [record["content"] for record in batch_records]
                batch_embeddings = await self.base_processor._generate_embeddings_batch(batch_contents)
                
                # 失敗したembeddingのリトライ処理
                failed_indices = [i for i, emb in enumerate(batch_embeddings) if emb is None]
                retry_count = 0
                
                while failed_indices and retry_count < max_retries:
                    retry_count += 1
                    logger.info(f"🔄 バッチ {current_batch} embedding再生成 (試行 {retry_count}/{max_retries}): {len(failed_indices)}件")
                    
                    retry_embeddings = await self.base_processor._generate_embeddings_batch(batch_contents, failed_indices)
                    
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
                
                # 成功したembeddingのみでレコード準備
                records_to_insert = []
                for i, record_data in enumerate(batch_records):
                    embedding_vector = batch_embeddings[i]
                    if embedding_vector:  # 成功したembeddingのみ
                        stats["total_text_length"] += len(record_data["content"])
                        # chunksテーブルに挿入するためのレコード形式
                        records_to_insert.append({
                            "doc_id": doc_id,
                            "chunk_index": record_data["chunk_index"],
                            "content": record_data["content"],
                            "embedding": embedding_vector,
                            "company_id": company_id,
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat()
                        })
                
                # 即座にSupabaseに挿入
                if records_to_insert:
                    try:
                        logger.info(f"💾 バッチ {current_batch}/{total_batches}: {len(records_to_insert)}レコードを即座に保存中...")
                        result = supabase.table("chunks").insert(records_to_insert).execute()
                        
                        if result.data:
                            batch_saved = len(result.data)
                            stats["saved_chunks"] += batch_saved
                            logger.info(f"✅ バッチ {current_batch}/{total_batches}: {batch_saved}レコード保存完了")
                        else:
                            logger.error(f"❌ バッチ {current_batch}/{total_batches} 保存エラー: {result.error}")
                            
                    except Exception as batch_error:
                        logger.error(f"❌ バッチ {current_batch}/{total_batches} 保存中に例外発生: {batch_error}")
                        # バッチエラーでも次のバッチ処理を続行
                        continue
                else:
                    logger.warning(f"⚠️ バッチ {current_batch}/{total_batches}: 保存可能なレコードがありません")
                
                # バッチ完了ログ
                logger.info(f"🎯 バッチ {current_batch}/{total_batches} 完了: embedding {len(batch_embeddings) - len(failed_indices)}/{len(batch_embeddings)} 成功, 保存 {len(records_to_insert)} レコード")

            # 最終結果のサマリー
            logger.info(f"🏁 {doc_name}: レコードベース処理完了")
            logger.info(f"📈 最終結果: 保存 {stats['saved_chunks']}/{stats['total_chunks']} レコード")
            logger.info(f"🧠 embedding: 成功 {stats['successful_embeddings']}, 失敗 {stats['failed_embeddings']}")
            
            if stats["failed_embeddings"] > 0:
                logger.warning(f"⚠️ 最終結果: {stats['successful_embeddings']}/{stats['total_chunks']} embedding成功, {stats['retry_attempts']}回再試行")
            else:
                logger.info(f"🎉 全embedding生成成功: {stats['successful_embeddings']}/{stats['total_chunks']}")

            return stats

        except Exception as e:
            logger.error(f"❌ レコードベース保存中に例外発生: {e}", exc_info=True)
            raise
    
    def _is_excel_file(self, filename: str) -> bool:
        """ファイルがExcel形式かどうかを判定"""
        return filename.lower().endswith(('.xlsx', '.xls'))
    
    def _calculate_page_count(self, records: List[Dict[str, Any]]) -> int:
        """レコード数からページ数を推定（1ページ=50レコード）"""
        return max(1, (len(records) + 49) // 50)

# グローバルインスタンス
document_processor_record_based = DocumentProcessorRecordBased()