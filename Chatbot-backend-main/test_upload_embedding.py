#!/usr/bin/env python3
"""
アップロード時のembedding生成テストスクリプト
"""

import asyncio
import tempfile
import os
from fastapi import UploadFile
from io import BytesIO
from dotenv import load_dotenv
from modules.document_processor import DocumentProcessor

# 環境変数を読み込み
load_dotenv()

async def test_embedding_generation():
    """embedding生成のテストを実行"""
    print("🧪 embedding生成テスト開始...")
    
    # テスト用のテキストファイルを作成
    test_content = """
    これはテスト用のドキュメントです。
    
    このファイルはembedding生成のテストに使用されます。
    複数の段落を含んでいて、チャンク分割とembedding生成の動作を確認できます。
    
    日本語のテキストが正しく処理されることを確認します。
    """
    
    # BytesIOを使ってUploadFileオブジェクトを模擬
    file_content = test_content.encode('utf-8')
    file_obj = BytesIO(file_content)
    
    # UploadFileオブジェクトを作成
    class MockUploadFile:
        def __init__(self, content, filename):
            self.file = BytesIO(content)
            self.filename = filename
            
        async def read(self):
            return self.file.getvalue()
            
        async def seek(self, position):
            self.file.seek(position)
    
    mock_file = MockUploadFile(file_content, "test_document.txt")
    
    try:
        # DocumentProcessorを初期化
        processor = DocumentProcessor()
        print(f"📄 使用するembeddingモデル: {processor.embedding_model}")
        
        # ファイル処理を実行
        result = await processor.process_uploaded_file(
            file=mock_file,
            user_id="test-user-id",
            company_id="test-company-id"
        )
        
        print("✅ 処理結果:")
        print(f"  - ドキュメントID: {result['document_id']}")
        print(f"  - ファイル名: {result['filename']}")
        print(f"  - テキスト長: {result['text_length']} 文字")
        print(f"  - 総チャンク数: {result['total_chunks']}")
        print(f"  - 保存チャンク数: {result['saved_chunks']}")
        print(f"  - 成功embedding数: {result['successful_embeddings']}")
        print(f"  - 失敗embedding数: {result['failed_embeddings']}")
        
        if result['successful_embeddings'] > 0:
            print("🎉 embedding生成が正常に動作しています！")
            return True
        else:
            print("❌ embedding生成に失敗しました")
            return False
            
    except Exception as e:
        print(f"❌ テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 環境変数の確認
    google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not google_api_key:
        print("❌ GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
        exit(1)
    
    print(f"🔑 Google API Key: {'設定済み' if google_api_key else '未設定'}")
    
    # テスト実行
    success = asyncio.run(test_embedding_generation())
    
    if success:
        print("\n✅ embedding生成テスト完了 - アップロード時のembedding生成が正常に動作します")
    else:
        print("\n❌ embedding生成テスト失敗 - 設定を確認してください")