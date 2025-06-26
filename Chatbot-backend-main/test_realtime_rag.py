"""
🚀 リアルタイムRAG処理フローのテストスクリプト
新しいStep 1-5のRAGフローをテストします
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# パスの設定
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_realtime_rag():
    """リアルタイムRAGシステムのテスト"""
    print("🚀 リアルタイムRAGシステムテスト開始")
    
    try:
        # リアルタイムRAGモジュールのインポート
        from modules.realtime_rag import (
            process_question_realtime, 
            realtime_rag_available,
            get_realtime_rag_processor
        )
        
        # システムの利用可能性をチェック
        if not realtime_rag_available():
            print("❌ リアルタイムRAGシステムが利用できません")
            print("環境変数を確認してください:")
            print(f"  GOOGLE_API_KEY: {'設定済み' if os.getenv('GOOGLE_API_KEY') else '未設定'}")
            print(f"  GEMINI_API_KEY: {'設定済み' if os.getenv('GEMINI_API_KEY') else '未設定'}")
            print(f"  SUPABASE_URL: {'設定済み' if os.getenv('SUPABASE_URL') else '未設定'}")
            print(f"  SUPABASE_KEY: {'設定済み' if os.getenv('SUPABASE_KEY') else '未設定'}")
            return
        
        print("✅ リアルタイムRAGシステムが利用可能です")
        
        # プロセッサインスタンスの取得テスト
        processor = get_realtime_rag_processor()
        if not processor:
            print("❌ リアルタイムRAGプロセッサの初期化に失敗")
            return
        
        print("✅ リアルタイムRAGプロセッサ初期化成功")
        
        # テスト質問のリスト
        test_questions = [
            "返品したいときはどこに連絡すればいいですか？",
            "営業時間を教えてください",
            "サポートの連絡先は？",
            "製品の保証期間はどのくらいですか？",
            "こんにちは"  # 一般的な挨拶
        ]
        
        # 各質問をテスト
        for i, question in enumerate(test_questions, 1):
            print(f"\n📝 テスト {i}: '{question}'")
            print("-" * 50)
            
            try:
                # リアルタイムRAG処理を実行
                result = await process_question_realtime(
                    question=question,
                    company_id=None,  # テスト用
                    company_name="テスト会社",
                    top_k=5
                )
                
                if result:
                    print(f"✅ 処理成功")
                    print(f"📊 ステータス: {result.get('status', 'unknown')}")
                    print(f"📊 使用チャンク数: {result.get('chunks_used', 0)}")
                    print(f"📊 最高類似度: {result.get('top_similarity', 0.0):.3f}")
                    print(f"💬 回答: {result.get('answer', 'なし')[:200]}...")
                    
                    if result.get('error'):
                        print(f"⚠️ エラー: {result['error']}")
                else:
                    print("❌ 結果が空です")
                    
            except Exception as e:
                print(f"❌ テストエラー: {e}")
                import traceback
                print(f"詳細: {traceback.format_exc()}")
            
            # 次のテストまで少し待機
            await asyncio.sleep(1)
        
        print("\n🎉 リアルタイムRAGテスト完了")
        
    except ImportError as e:
        print(f"❌ モジュールインポートエラー: {e}")
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        print(f"詳細: {traceback.format_exc()}")

async def test_step_by_step():
    """Step 1-5の個別テスト"""
    print("\n🔍 Step-by-Stepテスト開始")
    
    try:
        from modules.realtime_rag import get_realtime_rag_processor
        
        processor = get_realtime_rag_processor()
        if not processor:
            print("❌ プロセッサが利用できません")
            return
        
        test_question = "返品について教えてください"
        
        # Step 1: 質問入力
        print("\n✏️ Step 1: 質問入力")
        step1_result = await processor.step1_receive_question(test_question)
        print(f"結果: {step1_result}")
        
        # Step 2: エンベディング生成
        print("\n🧠 Step 2: エンベディング生成")
        embedding = await processor.step2_generate_embedding(test_question)
        print(f"エンベディング次元: {len(embedding) if embedding else 0}")
        
        if embedding and len(embedding) == 768:
            print("✅ 768次元のエンベディング生成成功")
            
            # Step 3: 類似チャンク検索
            print("\n🔍 Step 3: 類似チャンク検索")
            similar_chunks = await processor.step3_similarity_search(embedding, top_k=5)
            print(f"取得チャンク数: {len(similar_chunks)}")
            
            for i, chunk in enumerate(similar_chunks[:3]):
                print(f"  {i+1}. 類似度: {chunk['similarity_score']:.3f}, 内容: {chunk['content'][:100]}...")
            
            # Step 4: LLM回答生成
            print("\n💡 Step 4: LLM回答生成")
            answer = await processor.step4_generate_answer(test_question, similar_chunks)
            print(f"回答: {answer[:200]}...")
            
            # Step 5: 回答表示
            print("\n⚡️ Step 5: 回答表示")
            final_result = await processor.step5_display_answer(answer)
            print(f"最終結果: {final_result}")
            
        else:
            print("❌ エンベディング生成に失敗")
        
    except Exception as e:
        print(f"❌ Step-by-Stepテストエラー: {e}")
        import traceback
        print(f"詳細: {traceback.format_exc()}")

async def test_chat_integration():
    """チャット統合テスト"""
    print("\n💬 チャット統合テスト開始")
    
    try:
        from modules.chat_realtime_rag import get_realtime_rag_status
        
        # システム状態の確認
        status = get_realtime_rag_status()
        print(f"システム状態: {status}")
        
        if status['realtime_rag_available']:
            print("✅ リアルタイムRAGが利用可能")
        elif status['fallback_available']:
            print("⚠️ フォールバックシステムのみ利用可能")
        else:
            print("❌ システムが利用できません")
        
    except Exception as e:
        print(f"❌ チャット統合テストエラー: {e}")

def main():
    """メイン関数"""
    print("🚀 リアルタイムRAGシステム総合テスト")
    print("=" * 60)
    
    # 環境変数の確認
    print("📋 環境変数チェック:")
    required_vars = ['GOOGLE_API_KEY', 'GEMINI_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY']
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: 設定済み")
        else:
            print(f"  ❌ {var}: 未設定")
    
    # 非同期テストの実行
    async def run_all_tests():
        await test_realtime_rag()
        await test_step_by_step()
        await test_chat_integration()
    
    try:
        asyncio.run(run_all_tests())
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")

if __name__ == "__main__":
    main()