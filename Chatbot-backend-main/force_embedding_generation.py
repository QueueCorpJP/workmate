#!/usr/bin/env python3
"""
強制的にエンベディングを生成するスクリプト
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# 🔧 エンベディング生成を強制的に有効にする
os.environ["AUTO_GENERATE_EMBEDDINGS"] = "true"

# プロジェクトルートをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_adapter import get_supabase_client, select_data, update_data
from modules.auto_embedding import AutoEmbeddingGenerator
from modules.batch_embedding import BatchEmbeddingGenerator

async def main():
    """メイン処理"""
    print("🚀 強制エンベディング生成開始...")
    print("💡 AUTO_GENERATE_EMBEDDINGS を強制的に有効にしました")
    
    try:
        # BatchEmbeddingGeneratorを使用（より効率的）
        batch_generator = BatchEmbeddingGenerator()
        
        # 環境変数を強制的に設定
        batch_generator.auto_generate = True
        
        # NULLエンベディングを持つチャンクを取得
        print("📊 NULLエンベディングを持つチャンクを検索中...")
        result = select_data("chunks", columns="id, content, doc_id", limit=1000)
        
        if not result.success or not result.data:
            print("❌ チャンクが見つかりません")
            return
        
        null_embedding_chunks = []
        print(f"📋 {len(result.data)}個のチャンクをチェック中...")
        
        for i, chunk in enumerate(result.data):
            if i % 100 == 0:
                print(f"  進捗: {i}/{len(result.data)}")
            
            # エンベディングがNULLのチャンクを特定
            embedding_result = select_data("chunks", columns="embedding", filters={"id": chunk["id"]})
            if embedding_result.success and embedding_result.data:
                embedding = embedding_result.data[0].get("embedding")
                if embedding is None:
                    null_embedding_chunks.append(chunk)
        
        print(f"📈 処理対象: {len(null_embedding_chunks)}個のチャンク")
        
        if len(null_embedding_chunks) == 0:
            print("✅ 全てのチャンクにエンベディングが設定済みです")
            return
        
        # バッチエンベディング生成を実行
        print("🔄 バッチエンベディング生成を開始します...")
        success = await batch_generator.generate_embeddings_for_all_pending(limit=500)
        
        if success:
            print("🎉 エンベディング生成が成功しました！")
            print("✅ チャット検索が改善されるはずです。")
            
            # 生成後の統計を表示
            result_after = select_data("chunks", columns="id")
            if result_after.success:
                total_chunks = len(result_after.data)
                
                # エンベディングありのチャンクをカウント
                embedded_count = 0
                for chunk in result_after.data:
                    embedding_result = select_data("chunks", columns="embedding", filters={"id": chunk["id"]})
                    if embedding_result.success and embedding_result.data:
                        embedding = embedding_result.data[0].get("embedding")
                        if embedding is not None:
                            embedded_count += 1
                
                print(f"📊 最終結果: {embedded_count}/{total_chunks} チャンクにエンベディング生成完了")
                print(f"📈 エンベディング生成率: {embedded_count/total_chunks*100:.1f}%")
        else:
            print("❌ エンベディング生成に失敗しました。")
            
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())