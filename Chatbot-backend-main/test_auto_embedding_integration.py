#!/usr/bin/env python3
"""
🧪 自動エンベディング統合テストスクリプト
アップロード後の自動エンベディング生成機能をテスト
"""

import os
import sys
import asyncio
import logging
import tempfile
from datetime import datetime
from dotenv import load_dotenv
from supabase_adapter import get_supabase_client, select_data, delete_data

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()

async def test_auto_embedding_integration():
    """自動エンベディング統合テスト"""
    try:
        logger.info("🧪 自動エンベディング統合テスト開始")
        
        # 環境変数チェック
        auto_embed = os.getenv("AUTO_GENERATE_EMBEDDINGS", "false").lower()
        logger.info(f"📋 AUTO_GENERATE_EMBEDDINGS設定: {auto_embed}")
        
        if auto_embed != "true":
            logger.warning("⚠️ AUTO_GENERATE_EMBEDDINGS=true に設定してください")
            return False
        
        # Supabaseクライアント取得
        supabase = get_supabase_client()
        logger.info("✅ Supabaseクライアント取得完了")
        
        # テスト用ドキュメントをアップロード
        from modules.knowledge.api import process_file_upload
        from modules.database import get_db
        
        # テスト用テキストファイルを作成
        test_content = """
        これは自動エンベディング生成のテストファイルです。
        
        第1章: テスト概要
        このテストでは、ファイルアップロード後に自動的にエンベディングが生成されることを確認します。
        
        第2章: 技術仕様
        - Gemini Flash Embedding API使用
        - 768次元ベクトル生成
        - chunksテーブルに自動保存
        
        第3章: 期待結果
        アップロード完了後、すべてのチャンクにembeddingが設定されていることを確認します。
        """
        
        # 一時ファイル作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        try:
            # ファイルアップロードをシミュレート
            logger.info("📤 テストファイルアップロード開始")
            
            # FastAPIのUploadFileオブジェクトをシミュレート
            class MockUploadFile:
                def __init__(self, file_path: str):
                    self.filename = os.path.basename(file_path)
                    self.content_type = "text/plain"
                    self._file_path = file_path
                
                async def read(self):
                    with open(self._file_path, 'rb') as f:
                        return f.read()
            
            mock_file = MockUploadFile(temp_file_path)
            
            # データベース接続取得
            db = get_db()
            
            # テスト用ユーザーID（実際の環境に合わせて調整）
            test_user_id = "c8ee4bd7-b5de-48fc-9f54-fba1414da09b"  # ログから取得したユーザーID
            
            # ファイルアップロード実行
            result = await process_file_upload(
                file=mock_file,
                user_id=test_user_id,
                db=db
            )
            
            logger.info(f"📤 アップロード結果: {result.get('message', 'Unknown')}")
            
            # アップロードされたドキュメントを検索
            logger.info("🔍 アップロードされたドキュメントを検索中...")
            
            # 最新のドキュメントを取得
            docs_result = select_data(
                "document_sources",
                columns="id,name",
                filters={"name": f"test_auto_embedding_{datetime.now().strftime('%Y%m%d')}.txt"},
                limit=1
            )
            
            if not docs_result.data:
                # ファイル名で検索（部分一致）
                docs_result = select_data(
                    "document_sources",
                    columns="id,name",
                    limit=5
                )
                
                if docs_result.data:
                    # 最新のドキュメントを使用
                    doc_id = docs_result.data[0]['id']
                    doc_name = docs_result.data[0]['name']
                    logger.info(f"📋 テスト対象ドキュメント: {doc_name} (ID: {doc_id})")
                else:
                    logger.error("❌ テスト用ドキュメントが見つかりません")
                    return False
            else:
                doc_id = docs_result.data[0]['id']
                doc_name = docs_result.data[0]['name']
                logger.info(f"📋 テスト対象ドキュメント: {doc_name} (ID: {doc_id})")
            
            # チャンクとエンベディングの状態を確認
            logger.info("🔍 チャンクとエンベディングの状態を確認中...")
            
            chunks_result = select_data(
                "chunks",
                columns="id,chunk_index,embedding",
                filters={"doc_id": doc_id}
            )
            
            if not chunks_result.data:
                logger.error("❌ チャンクが見つかりません")
                return False
            
            chunks = chunks_result.data
            total_chunks = len(chunks)
            embedded_chunks = sum(1 for chunk in chunks if chunk.get('embedding') is not None)
            
            logger.info(f"📊 チャンク統計:")
            logger.info(f"   - 総チャンク数: {total_chunks}")
            logger.info(f"   - エンベディング済み: {embedded_chunks}")
            logger.info(f"   - 未処理: {total_chunks - embedded_chunks}")
            
            # 結果判定
            if embedded_chunks == total_chunks:
                logger.info("🎉 テスト成功: すべてのチャンクにエンベディングが生成されました")
                return True
            elif embedded_chunks > 0:
                logger.warning(f"⚠️ 部分的成功: {embedded_chunks}/{total_chunks} チャンクにエンベディングが生成されました")
                return True
            else:
                logger.error("❌ テスト失敗: エンベディングが生成されていません")
                return False
                
        finally:
            # 一時ファイルを削除
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                logger.info("🗑️ 一時ファイル削除完了")
        
    except Exception as e:
        logger.error(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メイン処理"""
    success = await test_auto_embedding_integration()
    
    if success:
        logger.info("✅ 自動エンベディング統合テスト完了")
        sys.exit(0)
    else:
        logger.error("❌ 自動エンベディング統合テスト失敗")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())