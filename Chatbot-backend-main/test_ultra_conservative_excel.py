#!/usr/bin/env python3
"""
🧪 超保守版Excelクリーナーのテストスクリプト
データ損失を極限まで抑制できているかを検証
"""

import os
import sys
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ultra_conservative_excel_cleaner():
    """超保守版Excelクリーナーをテスト"""
    try:
        # Excelファイルのパス
        excel_file_path = "01_ISP案件一覧.xlsx"
        
        if not os.path.exists(excel_file_path):
            logger.error(f"❌ Excelファイルが見つかりません: {excel_file_path}")
            return False
        
        # ファイルを読み込み
        with open(excel_file_path, 'rb') as f:
            content = f.read()
        
        logger.info(f"📁 ファイル読み込み完了: {len(content)} bytes")
        
        # 超保守版クリーナーをテスト
        logger.info("🧪 超保守版Excelクリーナーをテスト開始")
        try:
            from modules.excel_data_cleaner_ultra_conservative import ExcelDataCleanerUltraConservative
            
            cleaner = ExcelDataCleanerUltraConservative()
            result_ultra = cleaner.clean_excel_data(content)
            
            logger.info(f"✅ 超保守版処理完了: {len(result_ultra)} 文字")
            
            # 結果をファイルに保存
            with open("excel_ultra_conservative_result.txt", "w", encoding="utf-8") as f:
                f.write(result_ultra)
            logger.info("📄 超保守版結果を excel_ultra_conservative_result.txt に保存")
            
        except Exception as e:
            logger.error(f"❌ 超保守版処理エラー: {e}")
            return False
        
        # 修正版クリーナーと比較
        logger.info("🔍 修正版Excelクリーナーと比較")
        try:
            from modules.excel_data_cleaner_fixed import ExcelDataCleanerFixed
            
            cleaner_fixed = ExcelDataCleanerFixed()
            result_fixed = cleaner_fixed.clean_excel_data(content)
            
            logger.info(f"✅ 修正版処理完了: {len(result_fixed)} 文字")
            
            # 結果をファイルに保存
            with open("excel_fixed_result.txt", "w", encoding="utf-8") as f:
                f.write(result_fixed)
            logger.info("📄 修正版結果を excel_fixed_result.txt に保存")
            
            # 文字数比較
            char_diff = len(result_ultra) - len(result_fixed)
            char_diff_percent = (char_diff / len(result_fixed) * 100) if len(result_fixed) > 0 else 0
            
            logger.info(f"📊 文字数比較:")
            logger.info(f"   超保守版: {len(result_ultra):,} 文字")
            logger.info(f"   修正版:   {len(result_fixed):,} 文字")
            logger.info(f"   差分:     {char_diff:+,} 文字 ({char_diff_percent:+.1f}%)")
            
            if char_diff > 0:
                logger.info("🎉 超保守版の方が多くのデータを保持しています！")
            elif char_diff == 0:
                logger.info("⚖️ 両バージョンで同じ文字数です")
            else:
                logger.warning("⚠️ 超保守版の方が文字数が少なくなっています")
            
        except Exception as e:
            logger.error(f"❌ 修正版処理エラー: {e}")
        
        # 従来版クリーナーとも比較
        logger.info("🔍 従来版Excelクリーナーとも比較")
        try:
            from modules.excel_data_cleaner import ExcelDataCleaner
            
            cleaner_original = ExcelDataCleaner()
            result_original = cleaner_original.clean_excel_data(content)
            
            logger.info(f"✅ 従来版処理完了: {len(result_original)} 文字")
            
            # 結果をファイルに保存
            with open("excel_original_result.txt", "w", encoding="utf-8") as f:
                f.write(result_original)
            logger.info("📄 従来版結果を excel_original_result.txt に保存")
            
            # 全バージョン比較
            logger.info(f"📊 全バージョン比較:")
            logger.info(f"   超保守版: {len(result_ultra):,} 文字")
            logger.info(f"   修正版:   {len(result_fixed):,} 文字")
            logger.info(f"   従来版:   {len(result_original):,} 文字")
            
            # 最大値を基準とした保持率
            max_chars = max(len(result_ultra), len(result_fixed), len(result_original))
            ultra_retention = (len(result_ultra) / max_chars * 100) if max_chars > 0 else 0
            fixed_retention = (len(result_fixed) / max_chars * 100) if max_chars > 0 else 0
            original_retention = (len(result_original) / max_chars * 100) if max_chars > 0 else 0
            
            logger.info(f"📈 データ保持率:")
            logger.info(f"   超保守版: {ultra_retention:.1f}%")
            logger.info(f"   修正版:   {fixed_retention:.1f}%")
            logger.info(f"   従来版:   {original_retention:.1f}%")
            
        except Exception as e:
            logger.error(f"❌ 従来版処理エラー: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ テスト実行エラー: {e}")
        return False

def main():
    """メイン関数"""
    logger.info("🚀 超保守版Excelクリーナーテスト開始")
    
    success = test_ultra_conservative_excel_cleaner()
    
    if success:
        logger.info("🎉 テスト完了！")
        logger.info("📁 生成されたファイル:")
        logger.info("   - excel_ultra_conservative_result.txt (超保守版結果)")
        logger.info("   - excel_fixed_result.txt (修正版結果)")
        logger.info("   - excel_original_result.txt (従来版結果)")
        logger.info("💡 各ファイルを比較して、データ保持量の違いを確認してください。")
    else:
        logger.error("❌ テスト失敗")
        sys.exit(1)

if __name__ == "__main__":
    main()