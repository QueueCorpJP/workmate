#!/usr/bin/env python3
"""
既存のchat_historyテーブルの質問を分析してカテゴリーを再分類するスクリプト
"""

import asyncio
import logging
from typing import List, Dict, Any
from modules.database import get_db_connection
from modules.question_categorizer import get_categorizer

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def recategorize_chat_history():
    """既存のチャット履歴のカテゴリーを再分類する"""
    
    # データベース接続
    db = get_db_connection()
    if not db:
        logger.error("データベース接続に失敗しました")
        return
    
    # カテゴライザーを取得
    categorizer = get_categorizer()
    
    try:
        # 既存のチャット履歴を取得
        query = """
        SELECT id, user_message, category
        FROM chat_history 
        WHERE user_message IS NOT NULL 
        AND user_message != ''
        ORDER BY timestamp DESC
        """
        
        result = db.table('chat_history').select('id,user_message,category').execute()
        
        if not result.data:
            logger.info("分析対象のチャット履歴が見つかりませんでした")
            return
        
        logger.info(f"分析対象: {len(result.data)}件のチャット履歴")
        
        # 進捗追跡
        updated_count = 0
        batch_size = 50
        
        for i in range(0, len(result.data), batch_size):
            batch = result.data[i:i+batch_size]
            
            for chat in batch:
                chat_id = chat['id']
                user_message = chat['user_message']
                current_category = chat['category']
                
                # 質問を分析
                category_result = categorizer.categorize_question(user_message)
                new_category = category_result['category']
                display_name = category_result['display_name']
                confidence = category_result['confidence']
                
                # カテゴリーが変更された場合のみ更新
                if new_category != current_category:
                    try:
                        # データベースを更新
                        update_result = db.table('chat_history').update({
                            'category': new_category
                        }).eq('id', chat_id).execute()
                        
                        if update_result.data:
                            updated_count += 1
                            logger.info(f"更新完了: ID={chat_id}, 質問='{user_message[:50]}...', {current_category} → {display_name} (信頼度: {confidence:.2f})")
                        else:
                            logger.warning(f"更新失敗: ID={chat_id}")
                            
                    except Exception as e:
                        logger.error(f"更新エラー: ID={chat_id}, エラー={str(e)}")
                        continue
                else:
                    logger.debug(f"変更なし: ID={chat_id}, カテゴリー={display_name}")
            
            # 進捗表示
            processed = min(i + batch_size, len(result.data))
            logger.info(f"進捗: {processed}/{len(result.data)} 件処理完了 (更新: {updated_count}件)")
            
            # 少し待機（API制限対策）
            await asyncio.sleep(0.1)
        
        logger.info(f"再分類完了: 合計 {len(result.data)} 件中 {updated_count} 件のカテゴリーを更新しました")
        
        # 結果サマリーを表示
        await show_category_summary(db)
        
    except Exception as e:
        logger.error(f"再分類処理エラー: {str(e)}")
        import traceback
        traceback.print_exc()

async def show_category_summary(db):
    """カテゴリー分布のサマリーを表示"""
    try:
        # カテゴリー別の件数を取得
        result = db.table('chat_history').select('category').execute()
        
        if result.data:
            category_counts = {}
            for chat in result.data:
                category = chat.get('category', 'unknown')
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # カテゴリー名のマッピング
            categorizer = get_categorizer()
            category_mapping = categorizer.categories
            
            logger.info("=== 更新後のカテゴリー分布 ===")
            for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                display_name = category_mapping.get(category, f"🔹 {category}")
                logger.info(f"{display_name}: {count}件")
            
            logger.info("=" * 40)
            
    except Exception as e:
        logger.error(f"サマリー表示エラー: {str(e)}")

async def preview_recategorization():
    """再分類の結果をプレビューする（実際の更新は行わない）"""
    
    # データベース接続
    db = get_db_connection()
    if not db:
        logger.error("データベース接続に失敗しました")
        return
    
    # カテゴライザーを取得
    categorizer = get_categorizer()
    
    try:
        # 代表的な質問をサンプル取得
        result = db.table('chat_history').select('user_message,category').limit(20).execute()
        
        if not result.data:
            logger.info("分析対象のチャット履歴が見つかりませんでした")
            return
        
        logger.info("=== 再分類プレビュー（上位20件） ===")
        
        for i, chat in enumerate(result.data, 1):
            user_message = chat['user_message']
            current_category = chat['category']
            
            if user_message:
                # 質問を分析
                category_result = categorizer.categorize_question(user_message)
                new_category = category_result['category']
                display_name = category_result['display_name']
                confidence = category_result['confidence']
                
                change_indicator = "🔄" if new_category != current_category else "✅"
                
                logger.info(f"{i:2d}. {change_indicator} 質問: '{user_message[:50]}{'...' if len(user_message) > 50 else ''}'")
                logger.info(f"    現在: {current_category} → 新規: {display_name} (信頼度: {confidence:.2f})")
                logger.info("")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"プレビューエラー: {str(e)}")

async def main():
    """メイン処理"""
    print("質問カテゴリー再分類ツール")
    print("=" * 40)
    print("1. プレビュー（実際の更新は行わない）")
    print("2. 実際に再分類を実行")
    print("3. 現在のカテゴリー分布を表示")
    
    choice = input("\n選択してください (1-3): ").strip()
    
    if choice == "1":
        print("\n🔍 プレビューを実行中...")
        await preview_recategorization()
    elif choice == "2":
        confirm = input("\n⚠️  実際にデータベースを更新します。よろしいですか？ (y/N): ").strip().lower()
        if confirm == 'y':
            print("\n🚀 再分類を実行中...")
            await recategorize_chat_history()
        else:
            print("キャンセルしました。")
    elif choice == "3":
        print("\n📊 現在のカテゴリー分布を表示中...")
        db = get_db_connection()
        if db:
            await show_category_summary(db)
    else:
        print("無効な選択です。")

if __name__ == "__main__":
    asyncio.run(main()) 