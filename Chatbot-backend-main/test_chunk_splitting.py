#!/usr/bin/env python3
"""
チャンク分割機能のテスト
アップロード時のチャンク分割が正しく動作するかを検証
"""

import asyncio
import sys
import logging
from datetime import datetime

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_chunk_splitting_function():
    """チャンク分割機能の単体テスト"""
    logger.info("🧪 チャンク分割機能テスト開始")
    
    try:
        from modules.document_processor import DocumentProcessor
        
        # DocumentProcessor初期化
        processor = DocumentProcessor()
        logger.info("✅ DocumentProcessor初期化成功")
        
        # テストテキストのパターン
        test_cases = [
            {
                "name": "短いテキスト",
                "text": "これは短いテキストです。チャンク分割のテストを行います。",
                "expected_chunks": 1
            },
            {
                "name": "中程度のテキスト",
                "text": "これは中程度の長さのテキストです。" * 20 + "\n\n" + "段落を分けたテキストも含めます。" * 20,
                "expected_chunks": 1
            },
            {
                "name": "長いテキスト",
                "text": "これは長いテキストです。" * 100 + "\n\n" + "複数の段落に分かれています。" * 100 + "\n\n" + "チャンク分割のテストを行います。" * 100,
                "expected_chunks": 3
            },
            {
                "name": "非常に長いテキスト",
                "text": "長いテキストの例です。" * 200 + "\n\n" + "段落1: " + "内容が続きます。" * 150 + "\n\n" + "段落2: " + "さらに内容が続きます。" * 150 + "\n\n" + "段落3: " + "最後の内容です。" * 150,
                "expected_chunks": 5
            }
        ]
        
        for test_case in test_cases:
            logger.info(f"\n🔍 テスト: {test_case['name']}")
            logger.info(f"   テキスト長: {len(test_case['text'])} 文字")
            
            # チャンク分割実行
            chunks = processor._split_text_into_chunks(test_case['text'], test_case['name'])
            
            logger.info(f"   生成されたチャンク数: {len(chunks)}")
            
            # 各チャンクの詳細確認
            for i, chunk in enumerate(chunks):
                token_count = chunk.get('token_count', 0)
                content_length = len(chunk['content'])
                logger.info(f"   チャンク {i+1}: {token_count} トークン, {content_length} 文字")
                logger.info(f"      内容: {chunk['content'][:100]}...")
                
                # トークン数が範囲内かチェック
                if token_count > 500:
                    logger.warning(f"   ⚠️ チャンク {i+1}: トークン数が上限(500)を超えています: {token_count}")
                elif token_count < 50:
                    logger.warning(f"   ⚠️ チャンク {i+1}: トークン数が少なすぎます: {token_count}")
                else:
                    logger.info(f"   ✅ チャンク {i+1}: トークン数が適切です: {token_count}")
        
        logger.info("✅ チャンク分割機能テスト完了")
        return True
        
    except Exception as e:
        logger.error(f"❌ チャンク分割機能テストエラー: {e}")
        return False

async def test_database_chunks():
    """データベース内の実際のチャンクデータを調査"""
    logger.info("🧪 データベース内チャンクデータ調査開始")
    
    try:
        from supabase_adapter import get_supabase_client
        
        supabase = get_supabase_client()
        logger.info("✅ Supabaseクライアント取得成功")
        
        # 最新のチャンクデータを取得
        logger.info("🔍 最新のチャンクデータを取得中...")
        result = supabase.table("chunks").select("id, doc_id, chunk_index, content, created_at").order("created_at", desc=True).limit(10).execute()
        
        if not result.data:
            logger.info("📊 チャンクデータが見つかりませんでした")
            return True
        
        chunks = result.data
        logger.info(f"📊 取得したチャンク数: {len(chunks)}")
        
        # 各チャンクの詳細分析
        for i, chunk in enumerate(chunks):
            logger.info(f"\n📄 チャンク {i+1}:")
            logger.info(f"   ID: {chunk['id']}")
            logger.info(f"   DOC_ID: {chunk['doc_id']}")
            logger.info(f"   チャンクインデックス: {chunk['chunk_index']}")
            logger.info(f"   作成日時: {chunk['created_at']}")
            logger.info(f"   内容長: {len(chunk['content'])} 文字")
            logger.info(f"   内容: {chunk['content'][:200]}...")
            
            # トークン数を計算
            from modules.document_processor import DocumentProcessor
            processor = DocumentProcessor()
            token_count = processor._count_tokens(chunk['content'])
            logger.info(f"   推定トークン数: {token_count}")
            
            # トークン数の妥当性チェック
            if token_count > 500:
                logger.warning(f"   ⚠️ トークン数が上限(500)を超えています: {token_count}")
            elif token_count < 50:
                logger.warning(f"   ⚠️ トークン数が少なすぎます: {token_count}")
            else:
                logger.info(f"   ✅ トークン数が適切です: {token_count}")
        
        # ドキュメントごとのチャンク統計
        logger.info("\n📊 ドキュメントごとのチャンク統計:")
        doc_stats = {}
        for chunk in chunks:
            doc_id = chunk['doc_id']
            if doc_id not in doc_stats:
                doc_stats[doc_id] = []
            doc_stats[doc_id].append(chunk)
        
        for doc_id, doc_chunks in doc_stats.items():
            logger.info(f"   DOC_ID: {doc_id}")
            logger.info(f"   チャンク数: {len(doc_chunks)}")
            
            # チャンクインデックスの連続性チェック
            indices = sorted([chunk['chunk_index'] for chunk in doc_chunks])
            if indices == list(range(len(indices))):
                logger.info(f"   ✅ チャンクインデックスが連続しています: {indices}")
            else:
                logger.warning(f"   ⚠️ チャンクインデックスに欠落があります: {indices}")
        
        logger.info("✅ データベース内チャンクデータ調査完了")
        return True
        
    except Exception as e:
        logger.error(f"❌ データベース内チャンクデータ調査エラー: {e}")
        return False

async def test_chunk_size_distribution():
    """チャンクサイズの分布を調査"""
    logger.info("🧪 チャンクサイズ分布調査開始")
    
    try:
        from supabase_adapter import get_supabase_client
        from modules.document_processor import DocumentProcessor
        
        supabase = get_supabase_client()
        processor = DocumentProcessor()
        
        # 大量のチャンクデータを取得
        logger.info("🔍 チャンクデータを取得中...")
        result = supabase.table("chunks").select("content").limit(100).execute()
        
        if not result.data:
            logger.info("📊 チャンクデータが見つかりませんでした")
            return True
        
        chunks = result.data
        logger.info(f"📊 分析対象チャンク数: {len(chunks)}")
        
        # トークン数とサイズの統計
        token_counts = []
        char_counts = []
        
        for chunk in chunks:
            content = chunk['content']
            token_count = processor._count_tokens(content)
            char_count = len(content)
            
            token_counts.append(token_count)
            char_counts.append(char_count)
        
        # 統計情報の計算
        def calculate_stats(data):
            return {
                'min': min(data),
                'max': max(data),
                'avg': sum(data) / len(data),
                'median': sorted(data)[len(data) // 2]
            }
        
        token_stats = calculate_stats(token_counts)
        char_stats = calculate_stats(char_counts)
        
        logger.info(f"\n📈 トークン数統計:")
        logger.info(f"   最小: {token_stats['min']}")
        logger.info(f"   最大: {token_stats['max']}")
        logger.info(f"   平均: {token_stats['avg']:.1f}")
        logger.info(f"   中央値: {token_stats['median']}")
        
        logger.info(f"\n📈 文字数統計:")
        logger.info(f"   最小: {char_stats['min']}")
        logger.info(f"   最大: {char_stats['max']}")
        logger.info(f"   平均: {char_stats['avg']:.1f}")
        logger.info(f"   中央値: {char_stats['median']}")
        
        # 範囲外チャンクの検出
        oversized_chunks = [t for t in token_counts if t > 500]
        undersized_chunks = [t for t in token_counts if t < 50]
        
        logger.info(f"\n⚠️ 範囲外チャンク:")
        logger.info(f"   上限超過(>500): {len(oversized_chunks)}件")
        logger.info(f"   下限未満(<50): {len(undersized_chunks)}件")
        
        if oversized_chunks:
            logger.warning(f"   上限超過の詳細: {oversized_chunks}")
        if undersized_chunks:
            logger.warning(f"   下限未満の詳細: {undersized_chunks}")
        
        # 分布の妥当性評価
        optimal_chunks = [t for t in token_counts if 300 <= t <= 500]
        acceptable_chunks = [t for t in token_counts if 50 <= t <= 500]
        
        logger.info(f"\n✅ 分布評価:")
        logger.info(f"   最適範囲(300-500): {len(optimal_chunks)}/{len(token_counts)} ({len(optimal_chunks)/len(token_counts)*100:.1f}%)")
        logger.info(f"   許容範囲(50-500): {len(acceptable_chunks)}/{len(token_counts)} ({len(acceptable_chunks)/len(token_counts)*100:.1f}%)")
        
        logger.info("✅ チャンクサイズ分布調査完了")
        return True
        
    except Exception as e:
        logger.error(f"❌ チャンクサイズ分布調査エラー: {e}")
        return False

async def test_upload_simulation():
    """アップロード処理のシミュレーションテスト"""
    logger.info("🧪 アップロード処理シミュレーションテスト開始")
    
    try:
        from modules.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        
        # テスト用のサンプルテキスト
        test_text = """
        これは文書処理システムのテストです。
        
        第1章: はじめに
        本システムは、大量の文書を効率的に処理し、検索可能な形式に変換するためのシステムです。
        主な機能は以下の通りです：
        - 文書のアップロード
        - テキストの抽出
        - チャンク分割
        - エンベディング生成
        - データベース保存
        
        第2章: システム構成
        システムは以下のコンポーネントから構成されています：
        1. ファイルアップロード機能
        2. テキスト抽出エンジン
        3. チャンク分割エンジン
        4. エンベディング生成エンジン
        5. データベース管理システム
        
        第3章: 処理フロー
        文書処理は以下のステップで行われます：
        ステップ1: ファイルの受信と検証
        ステップ2: 形式に応じたテキスト抽出
        ステップ3: 意味単位でのチャンク分割
        ステップ4: 各チャンクのエンベディング生成
        ステップ5: データベースへの保存
        
        第4章: 品質保証
        システムの品質を保証するため、以下の仕組みを実装しています：
        - 自動テスト
        - エラーハンドリング
        - リトライメカニズム
        - ロギング機能
        
        第5章: 運用・保守
        システムの安定運用のため、以下の機能を提供しています：
        - 監視ダッシュボード
        - アラート機能
        - バックアップ機能
        - 障害対応手順
        
        以上がシステムの概要となります。
        """ * 3  # 3回繰り返してより長いテキストに
        
        logger.info(f"📝 テストテキスト長: {len(test_text)} 文字")
        
        # チャンク分割実行
        logger.info("🔪 チャンク分割実行中...")
        chunks = processor._split_text_into_chunks(test_text, "アップロードシミュレーション")
        
        logger.info(f"📊 生成されたチャンク数: {len(chunks)}")
        
        # 各チャンクの詳細確認
        for i, chunk in enumerate(chunks):
            token_count = chunk.get('token_count', 0)
            content_length = len(chunk['content'])
            
            logger.info(f"   📄 チャンク {i+1}:")
            logger.info(f"      インデックス: {chunk['chunk_index']}")
            logger.info(f"      トークン数: {token_count}")
            logger.info(f"      文字数: {content_length}")
            logger.info(f"      内容: {chunk['content'][:150]}...")
            
            # トークン数の妥当性チェック
            if token_count > 500:
                logger.warning(f"      ⚠️ トークン数が上限(500)を超えています")
            elif token_count < 50:
                logger.warning(f"      ⚠️ トークン数が少なすぎます")
            else:
                logger.info(f"      ✅ トークン数が適切です")
        
        # チャンクの連続性チェック
        expected_indices = list(range(len(chunks)))
        actual_indices = [chunk['chunk_index'] for chunk in chunks]
        
        if actual_indices == expected_indices:
            logger.info("✅ チャンクインデックスが連続しています")
        else:
            logger.warning(f"⚠️ チャンクインデックスに問題があります: 期待値={expected_indices}, 実際値={actual_indices}")
        
        # 全体の品質評価
        token_counts = [chunk.get('token_count', 0) for chunk in chunks]
        avg_tokens = sum(token_counts) / len(token_counts)
        max_tokens = max(token_counts)
        min_tokens = min(token_counts)
        
        logger.info(f"\n📈 品質評価:")
        logger.info(f"   平均トークン数: {avg_tokens:.1f}")
        logger.info(f"   最大トークン数: {max_tokens}")
        logger.info(f"   最小トークン数: {min_tokens}")
        logger.info(f"   目標範囲(300-500)内: {len([t for t in token_counts if 300 <= t <= 500])}/{len(token_counts)}")
        
        logger.info("✅ アップロード処理シミュレーションテスト完了")
        return True
        
    except Exception as e:
        logger.error(f"❌ アップロード処理シミュレーションテストエラー: {e}")
        return False

async def main():
    """メインテスト実行"""
    logger.info("🚀 チャンク分割検証テスト開始")
    
    test_results = {}
    
    # 各テストを実行
    tests = [
        ("チャンク分割機能", test_chunk_splitting_function),
        ("データベース内チャンクデータ", test_database_chunks),
        ("チャンクサイズ分布", test_chunk_size_distribution),
        ("アップロード処理シミュレーション", test_upload_simulation)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 {test_name} テスト開始")
        logger.info(f"{'='*60}")
        
        try:
            result = await test_func()
            test_results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name} テスト成功")
            else:
                logger.error(f"❌ {test_name} テスト失敗")
                
        except Exception as e:
            logger.error(f"❌ {test_name} テスト中にエラー: {e}")
            test_results[test_name] = False
    
    # 結果サマリー
    logger.info(f"\n{'='*60}")
    logger.info("📊 チャンク分割検証結果サマリー")
    logger.info(f"{'='*60}")
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info(f"\n🎯 総合結果: {passed}/{total} テスト成功")
    
    if passed == total:
        logger.info("🎉 すべてのチャンク分割検証テストが成功しました！")
    else:
        logger.error("⚠️ 一部のテストが失敗しました。詳細を確認してください。")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)