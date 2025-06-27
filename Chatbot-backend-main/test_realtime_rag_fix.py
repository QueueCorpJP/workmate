#!/usr/bin/env python3
"""
リアルタイムRAGシステムの修正テスト
LLM回答生成の response.text エラー修正を検証
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.realtime_rag import get_realtime_rag_processor, process_question_realtime

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_realtime_rag_fix():
    """リアルタイムRAG修正テスト"""
    print("🚀 リアルタイムRAG修正テスト開始...")
    
    # 環境変数の読み込み
    load_dotenv()
    
    # 必要な環境変数をチェック
    required_vars = ["GOOGLE_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 必要な環境変数が設定されていません: {missing_vars}")
        return False
    
    try:
        # テスト質問
        test_questions = [
            "会社の休暇制度について教えてください",
            "給与の支払い方法はどうなっていますか",
            "新入社員の研修プログラムについて",
            "テレワークの規定について知りたいです"
        ]
        
        print(f"📝 テスト質問数: {len(test_questions)}")
        
        # 各質問でテスト実行
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- テスト {i}/{len(test_questions)} ---")
            print(f"質問: {question}")
            
            try:
                # リアルタイムRAG処理を実行
                result = await process_question_realtime(
                    question=question,
                    company_id=None,  # テスト用
                    company_name="テスト会社",
                    top_k=5
                )
                
                if result and result.get("status") == "completed":
                    answer = result.get("answer", "")
                    chunks_used = result.get("chunks_used", 0)
                    top_similarity = result.get("top_similarity", 0.0)
                    
                    print(f"✅ 成功: {len(answer)}文字の回答生成")
                    print(f"   使用チャンク数: {chunks_used}")
                    print(f"   最高類似度: {top_similarity:.3f}")
                    print(f"   回答プレビュー: {answer[:100]}...")
                    
                elif result and result.get("status") == "error":
                    error_msg = result.get("error", "不明なエラー")
                    print(f"❌ エラー: {error_msg}")
                    
                    # 特定のエラーをチェック
                    if "response.text" in error_msg:
                        print("⚠️  response.text エラーが依然として発生しています")
                        return False
                    
                else:
                    print(f"⚠️  予期しない結果: {result}")
                
            except Exception as e:
                print(f"❌ 例外発生: {e}")
                
                # 特定のエラーをチェック
                if "response.text" in str(e):
                    print("⚠️  response.text エラーが依然として発生しています")
                    return False
                
                continue
            
            # 次のテストまで少し待機
            await asyncio.sleep(1)
        
        print(f"\n🎉 リアルタイムRAG修正テスト完了")
        print("✅ response.text エラーは修正されました")
        return True
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        return False

async def test_processor_initialization():
    """プロセッサ初期化テスト"""
    print("\n🔧 プロセッサ初期化テスト...")
    
    try:
        processor = get_realtime_rag_processor()
        
        if processor:
            print("✅ リアルタイムRAGプロセッサ初期化成功")
            print(f"   エンベディングモデル: {processor.embedding_model}")
            print(f"   チャットモデル: {processor.chat_model}")
            print(f"   Vertex AI使用: {processor.use_vertex_ai}")
            return True
        else:
            print("❌ プロセッサ初期化失敗")
            return False
            
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        return False

async def main():
    """メイン実行関数"""
    print("=" * 60)
    print("🧪 リアルタイムRAGシステム修正テスト")
    print("=" * 60)
    
    # 1. プロセッサ初期化テスト
    init_success = await test_processor_initialization()
    
    if not init_success:
        print("❌ 初期化に失敗したため、テストを中止します")
        return
    
    # 2. リアルタイムRAG修正テスト
    test_success = await test_realtime_rag_fix()
    
    print("\n" + "=" * 60)
    if test_success:
        print("🎉 全テスト成功: response.text エラーは修正されました")
    else:
        print("❌ テスト失敗: 修正が必要です")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())