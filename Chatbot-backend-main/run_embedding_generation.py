#!/usr/bin/env python3
"""
🚀 Embedding生成実行スクリプト
既存のembedding未生成チャンクに対してGemini Flash Embedding APIでembeddingを生成

使用方法:
python run_embedding_generation.py [制限数]

例:
python run_embedding_generation.py        # 全チャンク処理
python run_embedding_generation.py 100    # 100チャンクまで処理
"""

import sys
import asyncio
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from generate_embeddings_enhanced import main as enhanced_main
from embed_documents import generate_embeddings as simple_generate

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_usage():
    """使用方法を表示"""
    print("=" * 60)
    print("🧠 Embedding生成スクリプト")
    print("=" * 60)
    print("使用方法:")
    print("  python run_embedding_generation.py [オプション]")
    print("")
    print("オプション:")
    print("  --simple              シンプル版を使用（embed_documents.py）")
    print("  --enhanced [制限数]   強化版を使用（generate_embeddings_enhanced.py）")
    print("  --help, -h           このヘルプを表示")
    print("")
    print("例:")
    print("  python run_embedding_generation.py --simple")
    print("  python run_embedding_generation.py --enhanced")
    print("  python run_embedding_generation.py --enhanced 100")
    print("=" * 60)

async def run_enhanced_version(limit=None):
    """強化版embedding生成を実行"""
    logger.info("🚀 強化版embedding生成を開始します")
    
    # コマンドライン引数を設定
    original_argv = sys.argv.copy()
    sys.argv = ['generate_embeddings_enhanced.py']
    if limit:
        sys.argv.append(str(limit))
    
    try:
        await enhanced_main()
    finally:
        # 元のargvを復元
        sys.argv = original_argv

def run_simple_version():
    """シンプル版embedding生成を実行"""
    logger.info("🚀 シンプル版embedding生成を開始します")
    try:
        generate_embeddings()
        logger.info("✅ シンプル版embedding生成完了")
    except Exception as e:
        logger.error(f"❌ シンプル版embedding生成エラー: {e}")
        raise

async def main():
    """メイン処理"""
    args = sys.argv[1:]
    
    if not args or '--help' in args or '-h' in args:
        print_usage()
        return
    
    try:
        if '--simple' in args:
            run_simple_version()
        elif '--enhanced' in args:
            # 制限数の取得
            limit = None
            enhanced_index = args.index('--enhanced')
            if enhanced_index + 1 < len(args):
                try:
                    limit = int(args[enhanced_index + 1])
                    logger.info(f"📋 処理制限: {limit}チャンク")
                except ValueError:
                    logger.warning("⚠️ 無効な制限数が指定されました。全チャンクを処理します。")
            
            await run_enhanced_version(limit)
        else:
            # デフォルトは強化版
            limit = None
            if args:
                try:
                    limit = int(args[0])
                    logger.info(f"📋 処理制限: {limit}チャンク")
                except ValueError:
                    logger.warning("⚠️ 無効な制限数が指定されました。全チャンクを処理します。")
            
            await run_enhanced_version(limit)
            
    except KeyboardInterrupt:
        logger.info("⏹️ ユーザーによって中断されました")
    except Exception as e:
        logger.error(f"💥 実行エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🧠 Gemini Flash Embedding生成スクリプト")
    print(f"📋 モデル: gemini-embedding-exp-03-07")
    print("=" * 50)
    
    asyncio.run(main())