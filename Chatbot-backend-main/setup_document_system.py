"""
🚀 ドキュメント処理システム セットアップスクリプト
完全なRAG対応システムの初期化・デプロイ

実行内容:
1️⃣ chunksテーブル作成
2️⃣ 必要な拡張機能インストール（pgvector）
3️⃣ インデックス作成
4️⃣ 既存データの移行（document_sources → chunks）
5️⃣ システム動作確認
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('setup_document_system.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()

class DocumentSystemSetup:
    """ドキュメント処理システムセットアップクラス"""
    
    def __init__(self):
        self.db_connection = None
        self.setup_stats = {
            "start_time": None,
            "end_time": None,
            "tables_created": 0,
            "indexes_created": 0,
            "data_migrated": 0,
            "errors": []
        }
    
    def _get_database_url(self) -> str:
        """データベース接続URL取得"""
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
        
        return db_url
    
    def _init_database(self):
        """データベース接続初期化"""
        try:
            db_url = self._get_database_url()
            self.db_connection = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
            self.db_connection.autocommit = False
            logger.info("✅ データベース接続完了")
        except Exception as e:
            logger.error(f"❌ データベース接続エラー: {e}")
            raise
    
    def _execute_sql_file(self, file_path: str, description: str) -> bool:
        """SQLファイルを実行"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"⚠️ SQLファイルが見つかりません: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            cursor = self.db_connection.cursor()
            cursor.execute(sql_content)
            self.db_connection.commit()
            
            logger.info(f"✅ {description} 完了")
            return True
            
        except Exception as e:
            logger.error(f"❌ {description} エラー: {e}")
            self.db_connection.rollback()
            self.setup_stats["errors"].append(f"{description}: {str(e)}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def _check_table_exists(self, table_name: str) -> bool:
        """テーブル存在確認"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            
            exists = cursor.fetchone()[0]
            return exists
            
        except Exception as e:
            logger.error(f"❌ テーブル存在確認エラー: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def _check_extension_exists(self, extension_name: str) -> bool:
        """拡張機能存在確認"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_extension 
                    WHERE extname = %s
                );
            """, (extension_name,))
            
            exists = cursor.fetchone()[0]
            return exists
            
        except Exception as e:
            logger.error(f"❌ 拡張機能確認エラー: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def _install_pgvector_extension(self) -> bool:
        """pgvector拡張機能インストール"""
        try:
            if self._check_extension_exists("vector"):
                logger.info("✅ pgvector拡張機能は既にインストール済みです")
                return True
            
            cursor = self.db_connection.cursor()
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            self.db_connection.commit()
            
            logger.info("✅ pgvector拡張機能インストール完了")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ pgvector拡張機能インストールエラー: {e}")
            logger.info("💡 Supabaseでpgvectorが利用できない場合は、管理画面から有効化してください")
            self.db_connection.rollback()
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def _create_chunks_table(self) -> bool:
        """chunksテーブル作成"""
        try:
            if self._check_table_exists("chunks"):
                logger.info("✅ chunksテーブルは既に存在します")
                return True
            
            # chunksテーブル作成SQL
            create_table_sql = """
                CREATE TABLE IF NOT EXISTS chunks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    doc_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding VECTOR(768),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    company_id TEXT,
                    active BOOLEAN DEFAULT true,
                    special TEXT,
                    
                    CONSTRAINT fk_chunks_doc_id FOREIGN KEY (doc_id) REFERENCES document_sources(id) ON DELETE CASCADE
                );
            """
            
            cursor = self.db_connection.cursor()
            cursor.execute(create_table_sql)
            self.db_connection.commit()
            
            self.setup_stats["tables_created"] += 1
            logger.info("✅ chunksテーブル作成完了")
            return True
            
        except Exception as e:
            logger.error(f"❌ chunksテーブル作成エラー: {e}")
            self.db_connection.rollback()
            self.setup_stats["errors"].append(f"chunksテーブル作成: {str(e)}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def _create_indexes(self) -> bool:
        """インデックス作成"""
        try:
            indexes = [
                ("idx_chunks_doc_id", "CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);"),
                ("idx_chunks_company_id", "CREATE INDEX IF NOT EXISTS idx_chunks_company_id ON chunks(company_id);"),
                # Note: chunks table doesn't have active column - active status is managed in document_sources
                ("idx_chunks_doc_chunk_index", "CREATE INDEX IF NOT EXISTS idx_chunks_doc_chunk_index ON chunks(doc_id, chunk_index);"),
            ]
            
            cursor = self.db_connection.cursor()
            
            for index_name, index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                    logger.info(f"✅ インデックス作成: {index_name}")
                    self.setup_stats["indexes_created"] += 1
                except Exception as e:
                    logger.warning(f"⚠️ インデックス作成エラー ({index_name}): {e}")
            
            # ベクトル検索用インデックス（pgvectorが利用可能な場合）
            if self._check_extension_exists("vector"):
                try:
                    vector_index_sql = """
                        CREATE INDEX IF NOT EXISTS idx_chunks_embedding 
                        ON chunks USING ivfflat (embedding vector_cosine_ops) 
                        WITH (lists = 100);
                    """
                    cursor.execute(vector_index_sql)
                    logger.info("✅ ベクトル検索インデックス作成完了")
                    self.setup_stats["indexes_created"] += 1
                except Exception as e:
                    logger.warning(f"⚠️ ベクトル検索インデックス作成エラー: {e}")
            
            self.db_connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ インデックス作成エラー: {e}")
            self.db_connection.rollback()
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def _migrate_existing_data(self) -> bool:
        """既存データの移行（document_sources → chunks）"""
        try:
            cursor = self.db_connection.cursor()
            
            # contentカラムがあるdocument_sourcesレコードを確認
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'document_sources' 
                AND column_name = 'content'
            """)
            
            has_content_column = cursor.fetchone()[0] > 0
            
            if not has_content_column:
                logger.info("✅ document_sourcesにcontentカラムがありません（移行済み）")
                return True
            
            # contentがあるレコードを取得
            cursor.execute("""
                SELECT id, content, company_id, name
                FROM document_sources 
                WHERE content IS NOT NULL 
                AND content != ''
                AND id NOT IN (SELECT DISTINCT doc_id FROM chunks WHERE doc_id IS NOT NULL)
            """)
            
            documents_to_migrate = cursor.fetchall()
            
            if not documents_to_migrate:
                logger.info("✅ 移行すべきドキュメントはありません")
                return True
            
            logger.info(f"📋 {len(documents_to_migrate)}件のドキュメントを移行します")
            
            # 各ドキュメントをチャンクに分割して移行
            from .document_processor import document_processor
            
            migrated_count = 0
            for doc in documents_to_migrate:
                try:
                    # テキストをチャンクに分割
                    chunks = document_processor._split_text_into_chunks(
                        doc['content'], 
                        doc['name']
                    )
                    
                    # chunksテーブルに保存
                    for chunk_data in chunks:
                        insert_sql = """
                            INSERT INTO chunks (doc_id, chunk_index, content, company_id)
                            VALUES (%s, %s, %s, %s)
                        """
                        cursor.execute(insert_sql, (
                            doc['id'],
                            chunk_data['chunk_index'],
                            chunk_data['content'],
                            doc['company_id']
                        ))
                    
                    migrated_count += 1
                    logger.info(f"✅ 移行完了: {doc['name']} ({len(chunks)}チャンク)")
                    
                except Exception as e:
                    logger.error(f"❌ ドキュメント移行エラー ({doc['name']}): {e}")
                    continue
            
            self.db_connection.commit()
            self.setup_stats["data_migrated"] = migrated_count
            logger.info(f"✅ データ移行完了: {migrated_count}件")
            return True
            
        except Exception as e:
            logger.error(f"❌ データ移行エラー: {e}")
            self.db_connection.rollback()
            self.setup_stats["errors"].append(f"データ移行: {str(e)}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def _verify_system(self) -> bool:
        """システム動作確認"""
        try:
            cursor = self.db_connection.cursor()
            
            # chunksテーブルの統計情報取得
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_chunks,
                    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as chunks_with_embedding,
                    COUNT(CASE WHEN active = true THEN 1 END) as active_chunks,
                    COUNT(DISTINCT doc_id) as unique_documents
                FROM chunks
            """)
            
            stats = cursor.fetchone()
            
            logger.info("📊 システム統計:")
            logger.info(f"  - 総チャンク数: {stats['total_chunks']}")
            logger.info(f"  - embedding済み: {stats['chunks_with_embedding']}")
            logger.info(f"  - アクティブ: {stats['active_chunks']}")
            logger.info(f"  - ユニークドキュメント: {stats['unique_documents']}")
            
            # document_sourcesテーブルの統計
            cursor.execute("SELECT COUNT(*) FROM document_sources")
            doc_count = cursor.fetchone()[0]
            logger.info(f"  - document_sources: {doc_count}件")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ システム確認エラー: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def _print_final_report(self):
        """最終レポート表示"""
        total_time = self.setup_stats["end_time"] - self.setup_stats["start_time"]
        
        logger.info("=" * 60)
        logger.info("🎉 ドキュメント処理システム セットアップ完了")
        logger.info("=" * 60)
        logger.info(f"📊 作成テーブル数: {self.setup_stats['tables_created']}")
        logger.info(f"📊 作成インデックス数: {self.setup_stats['indexes_created']}")
        logger.info(f"📊 移行ドキュメント数: {self.setup_stats['data_migrated']}")
        logger.info(f"⏱️ 総処理時間: {total_time:.1f}秒")
        
        if self.setup_stats["errors"]:
            logger.warning("⚠️ エラー一覧:")
            for error in self.setup_stats["errors"]:
                logger.warning(f"  - {error}")
        else:
            logger.info("✅ エラーなし")
        
        logger.info("=" * 60)
        logger.info("🚀 次のステップ:")
        logger.info("1. python generate_embeddings_enhanced.py でembedding生成")
        logger.info("2. APIサーバー起動でファイルアップロード機能利用可能")
        logger.info("=" * 60)
    
    async def setup_system(self):
        """システムセットアップメイン処理"""
        try:
            self.setup_stats["start_time"] = time.time()
            logger.info("🚀 ドキュメント処理システム セットアップ開始")
            
            # データベース接続
            self._init_database()
            
            # 1. pgvector拡張機能インストール
            logger.info("📦 pgvector拡張機能インストール...")
            self._install_pgvector_extension()
            
            # 2. chunksテーブル作成
            logger.info("🗃️ chunksテーブル作成...")
            if not self._create_chunks_table():
                raise Exception("chunksテーブル作成に失敗しました")
            
            # 3. インデックス作成
            logger.info("📇 インデックス作成...")
            self._create_indexes()
            
            # 4. 既存データ移行
            logger.info("📋 既存データ移行...")
            self._migrate_existing_data()
            
            # 5. システム動作確認
            logger.info("🔍 システム動作確認...")
            self._verify_system()
            
            self.setup_stats["end_time"] = time.time()
            self._print_final_report()
            
        except Exception as e:
            logger.error(f"❌ セットアップエラー: {e}")
            raise
        
        finally:
            if self.db_connection:
                self.db_connection.close()
                logger.info("🔒 データベース接続を閉じました")

async def main():
    """メイン関数"""
    logger.info("🚀 ドキュメント処理システム セットアップスクリプト開始")
    
    try:
        setup = DocumentSystemSetup()
        await setup.setup_system()
        logger.info("🎉 セットアップ完了")
        
    except Exception as e:
        logger.error(f"💥 セットアップエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())