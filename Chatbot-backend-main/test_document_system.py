"""
🧪 ドキュメント処理システム テストスクリプト
システムの動作確認・デバッグ用

テスト項目:
1️⃣ データベース接続確認
2️⃣ chunksテーブル存在確認
3️⃣ embedding生成テスト
4️⃣ チャンク分割テスト
5️⃣ 統計情報表示
"""

import os
import sys
import asyncio
import tempfile
import logging
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()

class DocumentSystemTester:
    """ドキュメント処理システムテストクラス"""
    
    def __init__(self):
        self.db_connection = None
        self.test_results = {
            "database_connection": False,
            "chunks_table_exists": False,
            "embedding_generation": False,
            "chunk_splitting": False,
            "system_stats": {}
        }
    
    def _get_database_url(self) -> str:
        """データベース接続URL取得"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL と SUPABASE_KEY 環境変数が設定されていません")
        
        if "supabase.co" in supabase_url:
            project_id = supabase_url.split("://")[1].split(".")[0]
            db_url = f"postgresql://postgres.{project_id}:{os.getenv('DB_PASSWORD', '')}@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"
        else:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL 環境変数が設定されていません")
        
        return db_url
    
    def test_database_connection(self) -> bool:
        """データベース接続テスト"""
        try:
            logger.info("🔍 データベース接続テスト...")
            
            db_url = self._get_database_url()
            self.db_connection = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
            
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            logger.info(f"✅ データベース接続成功")
            logger.info(f"📊 PostgreSQL版: {version}")
            
            self.test_results["database_connection"] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ データベース接続エラー: {e}")
            self.test_results["database_connection"] = False
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def test_chunks_table(self) -> bool:
        """chunksテーブル存在確認"""
        try:
            logger.info("🔍 chunksテーブル確認...")
            
            cursor = self.db_connection.cursor()
            
            # テーブル存在確認
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'chunks'
                );
            """)
            
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                # テーブル構造確認
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'chunks'
                    ORDER BY ordinal_position;
                """)
                
                columns = cursor.fetchall()
                logger.info("✅ chunksテーブル存在確認")
                logger.info("📋 テーブル構造:")
                for col in columns:
                    logger.info(f"  - {col['column_name']}: {col['data_type']} ({'NULL可' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
                
                # レコード数確認
                cursor.execute("SELECT COUNT(*) FROM chunks;")
                record_count = cursor.fetchone()[0]
                logger.info(f"📊 レコード数: {record_count}")
                
                self.test_results["chunks_table_exists"] = True
                return True
            else:
                logger.error("❌ chunksテーブルが存在しません")
                self.test_results["chunks_table_exists"] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ chunksテーブル確認エラー: {e}")
            self.test_results["chunks_table_exists"] = False
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    async def test_embedding_generation(self) -> bool:
        """embedding生成テスト"""
        try:
            logger.info("🔍 embedding生成テスト...")
            
            # DocumentProcessorをインポート
            from modules.document_processor import document_processor
            
            # テストテキスト
            test_text = "これはembedding生成のテストです。Gemini Flash APIが正常に動作するかを確認します。"
            
            # embedding生成
            embedding = await document_processor._generate_embedding(test_text)
            
            if embedding and len(embedding) == 768:
                logger.info(f"✅ embedding生成成功 (次元: {len(embedding)})")
                logger.info(f"📊 ベクトル例: [{embedding[0]:.6f}, {embedding[1]:.6f}, ...]")
                
                self.test_results["embedding_generation"] = True
                return True
            else:
                logger.error("❌ embedding生成失敗または次元数不正")
                self.test_results["embedding_generation"] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ embedding生成テストエラー: {e}")
            self.test_results["embedding_generation"] = False
            return False
    
    def test_chunk_splitting(self) -> bool:
        """チャンク分割テスト"""
        try:
            logger.info("🔍 チャンク分割テスト...")
            
            from modules.document_processor import document_processor
            
            # テストテキスト（長文）
            test_text = """
            これは長いテストドキュメントです。チャンク分割機能が正常に動作するかを確認します。
            
            第1章：はじめに
            このシステムは、ファイルアップロードから高度なRAG検索まで、完全なドキュメント処理パイプラインを提供します。
            主な機能には、テキスト抽出、チャンク分割、embedding生成、データベース保存が含まれます。
            
            第2章：技術仕様
            システムはPython、FastAPI、Supabase、Gemini APIを使用して構築されています。
            チャンクサイズは300-500トークンに設定され、意味単位での分割を行います。
            embedding生成にはGemini Flash APIを使用し、768次元のベクトルを生成します。
            
            第3章：運用方法
            システムの運用には、定期的なメンテナンスと監視が必要です。
            ログファイルを確認し、エラーが発生した場合は適切に対処してください。
            パフォーマンスの最適化も重要な要素です。
            """
            
            # チャンク分割実行
            chunks = document_processor._split_text_into_chunks(test_text, "test_document.txt")
            
            if chunks and len(chunks) > 0:
                logger.info(f"✅ チャンク分割成功")
                logger.info(f"📊 生成チャンク数: {len(chunks)}")
                
                for i, chunk in enumerate(chunks[:3]):  # 最初の3チャンクを表示
                    logger.info(f"📄 チャンク {i}: {chunk['token_count']}トークン")
                    logger.info(f"   内容: {chunk['content'][:100]}...")
                
                self.test_results["chunk_splitting"] = True
                return True
            else:
                logger.error("❌ チャンク分割失敗")
                self.test_results["chunk_splitting"] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ チャンク分割テストエラー: {e}")
            self.test_results["chunk_splitting"] = False
            return False
    
    def get_system_stats(self) -> Dict[str, Any]:
        """システム統計情報取得"""
        try:
            logger.info("🔍 システム統計情報取得...")
            
            cursor = self.db_connection.cursor()
            
            stats = {}
            
            # chunksテーブル統計
            if self.test_results["chunks_table_exists"]:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_chunks,
                        COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as chunks_with_embedding,
                        COUNT(CASE WHEN active = true THEN 1 END) as active_chunks,
                        COUNT(DISTINCT doc_id) as unique_documents,
                        COUNT(DISTINCT company_id) as companies
                    FROM chunks;
                """)
                
                chunk_stats = cursor.fetchone()
                stats["chunks"] = dict(chunk_stats)
            
            # document_sourcesテーブル統計
            cursor.execute("SELECT COUNT(*) as total_documents FROM document_sources;")
            doc_stats = cursor.fetchone()
            stats["documents"] = dict(doc_stats)
            
            # 会社統計
            cursor.execute("SELECT COUNT(*) as total_companies FROM companies;")
            company_stats = cursor.fetchone()
            stats["companies"] = dict(company_stats)
            
            # ユーザー統計
            cursor.execute("SELECT COUNT(*) as total_users FROM users;")
            user_stats = cursor.fetchone()
            stats["users"] = dict(user_stats)
            
            self.test_results["system_stats"] = stats
            
            logger.info("📊 システム統計:")
            for category, data in stats.items():
                logger.info(f"  {category}: {data}")
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ システム統計取得エラー: {e}")
            return {}
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def print_test_summary(self):
        """テスト結果サマリー表示"""
        logger.info("=" * 60)
        logger.info("🧪 ドキュメント処理システム テスト結果")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results) - 1  # system_statsを除く
        passed_tests = sum(1 for k, v in self.test_results.items() if k != "system_stats" and v)
        
        logger.info(f"📊 テスト結果: {passed_tests}/{total_tests} 成功")
        
        for test_name, result in self.test_results.items():
            if test_name == "system_stats":
                continue
            
            status = "✅ 成功" if result else "❌ 失敗"
            logger.info(f"  - {test_name}: {status}")
        
        if passed_tests == total_tests:
            logger.info("🎉 全テスト成功！システムは正常に動作しています。")
        else:
            logger.warning("⚠️ 一部テストが失敗しました。設定を確認してください。")
        
        logger.info("=" * 60)
    
    async def run_all_tests(self):
        """全テスト実行"""
        try:
            logger.info("🚀 ドキュメント処理システム テスト開始")
            
            # 1. データベース接続テスト
            if not self.test_database_connection():
                logger.error("❌ データベース接続に失敗しました。テストを中止します。")
                return
            
            # 2. chunksテーブル確認
            self.test_chunks_table()
            
            # 3. embedding生成テスト
            await self.test_embedding_generation()
            
            # 4. チャンク分割テスト
            self.test_chunk_splitting()
            
            # 5. システム統計取得
            self.get_system_stats()
            
            # 6. テスト結果サマリー
            self.print_test_summary()
            
        except Exception as e:
            logger.error(f"❌ テスト実行エラー: {e}")
        
        finally:
            if self.db_connection:
                self.db_connection.close()
                logger.info("🔒 データベース接続を閉じました")

async def main():
    """メイン関数"""
    logger.info("🧪 ドキュメント処理システム テストスクリプト開始")
    
    try:
        tester = DocumentSystemTester()
        await tester.run_all_tests()
        
    except Exception as e:
        logger.error(f"💥 テストスクリプトエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())