#!/usr/bin/env python3
"""
🔍 Embedding問題診断スクリプト
提供された原因分析に基づいて、システムの状態を詳細に診断
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from supabase_adapter import get_supabase_client

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()

class EmbeddingDiagnostics:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
        
        if not self.embedding_model.startswith("models/"):
            self.embedding_model = f"models/{self.embedding_model}"
    
    async def check_api_connectivity(self):
        """原因② Gemini APIが呼び出されているかチェック"""
        logger.info("🔍 原因② Gemini API接続性チェック")
        
        try:
            if not self.api_key:
                logger.error("❌ GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が未設定")
                return False
            
            genai.configure(api_key=self.api_key)
            logger.info(f"🧠 使用モデル: {self.embedding_model}")
            
            # テストテキストでembedding生成
            test_text = "これはAPI接続テストです。"
            response = genai.embed_content(
                model=self.embedding_model,
                content=test_text
            )
            
            if response and 'embedding' in response:
                embedding_vector = response['embedding']
                logger.info(f"✅ Gemini API正常動作 - 次元数: {len(embedding_vector)}")
                return True, len(embedding_vector)
            else:
                logger.error(f"❌ Gemini APIレスポンス異常: {response}")
                return False, 0
                
        except Exception as e:
            logger.error(f"❌ Gemini API接続エラー: {e}")
            return False, 0
    
    def check_database_schema(self):
        """原因④ chunksテーブルのembeddingカラム状態チェック"""
        logger.info("🔍 原因④ データベーススキーマチェック")
        
        try:
            # chunksテーブルの構造を確認
            schema_query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'chunks' 
            AND column_name IN ('embedding', 'content', 'id', 'doc_id')
            ORDER BY column_name;
            """
            
            result = self.supabase.rpc("execute_sql", {"sql_query": schema_query}).execute()
            
            if result.data:
                logger.info("📋 chunksテーブル構造:")
                embedding_nullable = None
                for col in result.data:
                    logger.info(f"  - {col['column_name']}: {col['data_type']} (NULL許可: {col['is_nullable']})")
                    if col['column_name'] == 'embedding':
                        embedding_nullable = col['is_nullable'] == 'YES'
                
                if embedding_nullable is not None:
                    if embedding_nullable:
                        logger.warning("⚠️ embeddingカラムはNULL許可 - 失敗が目立たない可能性")
                    else:
                        logger.info("✅ embeddingカラムはNOT NULL制約")
                    return embedding_nullable
                else:
                    logger.error("❌ embeddingカラムが見つかりません")
                    return None
            else:
                logger.error("❌ スキーマ情報取得失敗")
                return None
                
        except Exception as e:
            logger.error(f"❌ スキーマチェックエラー: {e}")
            return None
    
    def check_pending_chunks(self):
        """原因④ embedding未生成チャンクの確認"""
        logger.info("🔍 原因④ Embedding未生成チャンクチェック")
        
        try:
            # embedding未生成のチャンクを取得（activeカラムを除外）
            chunks_result = self.supabase.table("chunks").select(
                "id,content,chunk_index,doc_id,created_at"
            ).is_("embedding", "null").limit(10).execute()
            
            if chunks_result.data:
                logger.warning(f"⚠️ Embedding未生成チャンク: {len(chunks_result.data)}件")
                for chunk in chunks_result.data[:3]:  # 最初の3件を表示
                    content_preview = chunk.get("content", "")[:50] + "..." if len(chunk.get("content", "")) > 50 else chunk.get("content", "")
                    logger.info(f"  - ID: {chunk['id'][:8]}..., Index: {chunk.get('chunk_index', 'N/A')}, 作成日: {chunk.get('created_at', 'N/A')}")
                    logger.info(f"    Content: {content_preview}")
                return chunks_result.data
            else:
                logger.info("✅ Embedding未生成のチャンクはありません")
                return []
                
        except Exception as e:
            logger.error(f"❌ チャンクチェックエラー: {e}")
            return []
    
    def check_recent_uploads(self):
        """最近のアップロード状況をチェック"""
        logger.info("🔍 最近のアップロード状況チェック")
        
        try:
            # 最近のドキュメントを取得
            docs_result = self.supabase.table("document_sources").select(
                "id,name,uploaded_at"
            ).order("uploaded_at", desc=True).limit(5).execute()
            
            if docs_result.data:
                logger.info(f"📄 最近のアップロード: {len(docs_result.data)}件")
                for doc in docs_result.data:
                    doc_id = doc['id']
                    doc_name = doc['name']
                    upload_time = doc['uploaded_at']
                    
                    # このドキュメントのチャンク数とembedding状況を確認
                    chunks_result = self.supabase.table("chunks").select(
                        "id,embedding"
                    ).eq("doc_id", doc_id).execute()
                    
                    if chunks_result.data:
                        total_chunks = len(chunks_result.data)
                        embedded_chunks = len([c for c in chunks_result.data if c.get('embedding') is not None])
                        logger.info(f"  - {doc_name} ({upload_time}): {embedded_chunks}/{total_chunks} チャンクにembedding")
                    else:
                        logger.warning(f"  - {doc_name} ({upload_time}): チャンクが見つかりません")
                
                return docs_result.data
            else:
                logger.info("📄 最近のアップロードはありません")
                return []
                
        except Exception as e:
            logger.error(f"❌ アップロード状況チェックエラー: {e}")
            return []
    
    def check_gemini_rate_limits(self):
        """原因③ Gemini API制限チェック"""
        logger.info("🔍 原因③ Gemini API制限チェック")
        
        try:
            # 複数回のAPI呼び出しでレート制限をテスト
            test_texts = [
                "テスト1: 短いテキスト",
                "テスト2: もう少し長いテキストでAPIの応答を確認します。",
                "テスト3: さらに長いテキストを使用してGemini APIのレート制限や応答時間をテストします。これで制限に引っかかるかどうか確認できます。"
            ]
            
            genai.configure(api_key=self.api_key)
            success_count = 0
            
            for i, text in enumerate(test_texts, 1):
                try:
                    response = genai.embed_content(
                        model=self.embedding_model,
                        content=text
                    )
                    
                    if response and 'embedding' in response:
                        success_count += 1
                        logger.info(f"✅ API呼び出し {i}/3 成功")
                    else:
                        logger.warning(f"⚠️ API呼び出し {i}/3 レスポンス異常")
                    
                    # 短い待機時間
                    await asyncio.sleep(0.1)
                    
                except Exception as api_error:
                    if "429" in str(api_error) or "Too Many Requests" in str(api_error):
                        logger.error(f"❌ レート制限エラー検出: {api_error}")
                        return False
                    else:
                        logger.error(f"❌ API呼び出しエラー {i}/3: {api_error}")
            
            if success_count == len(test_texts):
                logger.info("✅ Gemini APIレート制限問題なし")
                return True
            else:
                logger.warning(f"⚠️ API成功率: {success_count}/{len(test_texts)}")
                return False
                
        except Exception as e:
            logger.error(f"❌ レート制限チェックエラー: {e}")
            return False
    
    async def run_full_diagnosis(self):
        """完全診断の実行"""
        logger.info("🚀 Embedding問題完全診断開始")
        logger.info("=" * 60)
        
        diagnosis_results = {}
        
        # 原因② Gemini API接続性
        api_ok, dimensions = await self.check_api_connectivity()
        diagnosis_results['api_connectivity'] = api_ok
        diagnosis_results['embedding_dimensions'] = dimensions
        
        # 原因④ データベーススキーマ
        embedding_nullable = self.check_database_schema()
        diagnosis_results['embedding_nullable'] = embedding_nullable
        
        # 原因④ 未生成チャンク
        pending_chunks = self.check_pending_chunks()
        diagnosis_results['pending_chunks'] = len(pending_chunks) if pending_chunks else 0
        diagnosis_results['pending_chunk_data'] = pending_chunks[:3] if pending_chunks else []
        
        # 最近のアップロード状況
        recent_uploads = self.check_recent_uploads()
        diagnosis_results['recent_uploads'] = len(recent_uploads) if recent_uploads else 0
        
        # 原因③ レート制限
        rate_limit_ok = await self.check_gemini_rate_limits()
        diagnosis_results['rate_limit_ok'] = rate_limit_ok
        
        # 診断結果サマリー
        logger.info("=" * 60)
        logger.info("📊 診断結果サマリー")
        logger.info("=" * 60)
        
        # 問題の特定
        issues_found = []
        
        if not diagnosis_results['api_connectivity']:
            issues_found.append("② Gemini APIが呼び出されていない")
        
        if diagnosis_results['embedding_dimensions'] != 3072:
            issues_found.append(f"③ 次元数不一致 (期待: 3072, 実際: {diagnosis_results['embedding_dimensions']})")
        
        if diagnosis_results['embedding_nullable']:
            issues_found.append("④ embeddingカラムがnull許容で失敗が目立たない")
        
        if diagnosis_results['pending_chunks'] > 0:
            issues_found.append(f"④ embedding未生成チャンクが {diagnosis_results['pending_chunks']} 件存在")
        
        if not diagnosis_results['rate_limit_ok']:
            issues_found.append("③ Gemini APIレート制限の問題")
        
        if issues_found:
            logger.error("❌ 検出された問題:")
            for issue in issues_found:
                logger.error(f"   - {issue}")
        else:
            logger.info("✅ 重大な問題は検出されませんでした")
        
        # 推奨対策
        logger.info("=" * 60)
        logger.info("💡 推奨対策")
        logger.info("=" * 60)
        
        if diagnosis_results['pending_chunks'] > 0:
            logger.info("🔧 未生成embeddingの修正:")
            logger.info("   python auto_embed_simple.py 10")
        
        if diagnosis_results['embedding_nullable']:
            logger.info("🔧 スキーマ改善:")
            logger.info("   ALTER TABLE chunks ALTER COLUMN embedding SET NOT NULL;")
        
        if not diagnosis_results['rate_limit_ok']:
            logger.info("🔧 レート制限対策:")
            logger.info("   - API呼び出し間隔を増やす (0.5秒以上)")
            logger.info("   - バッチサイズを小さくする")
        
        return diagnosis_results

async def main():
    """メイン処理"""
    diagnostics = EmbeddingDiagnostics()
    results = await diagnostics.run_full_diagnosis()
    
    # 結果をファイルに保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"embedding_diagnosis_report_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"Embedding診断レポート - {datetime.now()}\n")
        f.write("=" * 60 + "\n")
        f.write(f"API接続性: {'✅' if results['api_connectivity'] else '❌'}\n")
        f.write(f"Embedding次元数: {results['embedding_dimensions']}\n")
        f.write(f"Embeddingカラムnull許可: {'⚠️' if results['embedding_nullable'] else '✅'}\n")
        f.write(f"未生成チャンク数: {results['pending_chunks']}\n")
        f.write(f"最近のアップロード数: {results['recent_uploads']}\n")
        f.write(f"レート制限問題: {'❌' if not results['rate_limit_ok'] else '✅'}\n")
    
    logger.info(f"📄 診断レポートを保存: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())