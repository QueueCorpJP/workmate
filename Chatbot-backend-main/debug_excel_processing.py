#!/usr/bin/env python3
"""
Excel処理でのデータ損失問題を調査するデバッグスクリプト
実際のExcelファイル処理の各段階でデータがどのように変化するかを追跡
"""

import sys
import os
import logging
import pandas as pd
from io import BytesIO
import json

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_excel_processing(excel_file_path: str):
    """Excel処理の各段階でデータの変化を詳細に追跡"""
    
    if not os.path.exists(excel_file_path):
        logger.error(f"❌ Excelファイルが見つかりません: {excel_file_path}")
        return
    
    # ファイルを読み込み
    with open(excel_file_path, 'rb') as f:
        content = f.read()
    
    logger.info(f"📊 Excelファイル読み込み完了: {excel_file_path} ({len(content)} bytes)")
    
    # 1. 生のpandas読み込みでの全データ確認
    logger.info("\n=== 1. 生のpandas読み込み（全データ保持） ===")
    try:
        excel_file = pd.ExcelFile(BytesIO(content))
        logger.info(f"📋 シート一覧: {excel_file.sheet_names}")
        
        original_data = {}
        for sheet_name in excel_file.sheet_names:
            try:
                # ヘッダーなしで全データを読み込み
                df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                logger.info(f"📊 シート '{sheet_name}': {df.shape[0]}行 x {df.shape[1]}列")
                
                # 非空セルの数をカウント
                non_empty_cells = df.notna().sum().sum()
                total_cells = df.shape[0] * df.shape[1]
                logger.info(f"   非空セル: {non_empty_cells}/{total_cells} ({non_empty_cells/total_cells*100:.1f}%)")
                
                # データの一部をサンプル表示
                logger.info(f"   データサンプル (最初の5行5列):")
                sample_data = []
                for i in range(min(5, df.shape[0])):
                    row_sample = []
                    for j in range(min(5, df.shape[1])):
                        cell_value = df.iloc[i, j]
                        if pd.notna(cell_value):
                            cell_str = str(cell_value)[:50]  # 最初の50文字
                            row_sample.append(cell_str)
                        else:
                            row_sample.append("[空]")
                    sample_data.append(row_sample)
                    logger.info(f"     行{i+1}: {row_sample}")
                
                original_data[sheet_name] = df
                
            except Exception as e:
                logger.error(f"❌ シート '{sheet_name}' 読み込みエラー: {e}")
        
    except Exception as e:
        logger.error(f"❌ pandas読み込みエラー: {e}")
        return
    
    # 2. 各Excel cleanerでの処理結果を比較
    logger.info("\n=== 2. Excel Cleaner 処理結果比較 ===")
    
    cleaners = [
        ("Enhanced", "modules.excel_data_cleaner_enhanced", "ExcelDataCleanerEnhanced"),
        ("Ultra Conservative", "modules.excel_data_cleaner_ultra_conservative", "ExcelDataCleanerUltraConservative"),
        ("Fixed", "modules.excel_data_cleaner_fixed", "ExcelDataCleanerFixed"),
        ("Original", "modules.excel_data_cleaner", "ExcelDataCleaner")
    ]
    
    cleaner_results = {}
    
    for cleaner_name, module_name, class_name in cleaners:
        try:
            logger.info(f"\n--- {cleaner_name} Cleaner テスト ---")
            
            # モジュールを動的にインポート
            module = __import__(module_name, fromlist=[class_name])
            cleaner_class = getattr(module, class_name)
            cleaner = cleaner_class()
            
            # クリーニング実行
            cleaned_text = cleaner.clean_excel_data(content)
            
            logger.info(f"✅ {cleaner_name}: 処理完了")
            logger.info(f"   出力文字数: {len(cleaned_text)}")
            newline_count = cleaned_text.count('\n') + 1
            logger.info(f"   出力行数: {newline_count}")
            
            # 出力の最初の500文字を表示
            preview = cleaned_text[:500].replace('\n', '\\\\n')
            logger.info(f"   出力プレビュー: {preview}...")
            
            cleaner_results[cleaner_name] = {
                "text": cleaned_text,
                "length": len(cleaned_text),
                "lines": cleaned_text.count('\n') + 1
            }
            
        except ImportError:
            logger.warning(f"⚠️ {cleaner_name} cleaner が利用できません")
        except Exception as e:
            logger.error(f"❌ {cleaner_name} cleaner エラー: {e}")
    
    # 3. 結果の比較分析
    logger.info("\n=== 3. 処理結果比較分析 ===")
    
    if cleaner_results:
        # 文字数の比較
        lengths = [(name, result["length"]) for name, result in cleaner_results.items()]
        lengths.sort(key=lambda x: x[1], reverse=True)
        
        logger.info("📊 出力文字数ランキング:")
        for i, (name, length) in enumerate(lengths):
            logger.info(f"   {i+1}. {name}: {length:,} 文字")
        
        # 最も長い出力と最も短い出力の差を分析
        if len(lengths) >= 2:
            longest_name, longest_length = lengths[0]
            shortest_name, shortest_length = lengths[-1]
            
            loss_ratio = (longest_length - shortest_length) / longest_length * 100
            logger.info(f"📉 データ損失率: {loss_ratio:.1f}% ({longest_name} vs {shortest_name})")
            
            # 具体的な差分を分析
            longest_text = cleaner_results[longest_name]["text"]
            shortest_text = cleaner_results[shortest_name]["text"]
            
            # 最長版にあって最短版にない内容を探す
            longest_lines = set(longest_text.split('\n'))
            shortest_lines = set(shortest_text.split('\n'))
            missing_lines = longest_lines - shortest_lines
            
            if missing_lines:
                logger.info(f"🔍 {shortest_name}で失われた行数: {len(missing_lines)}")
                logger.info("   失われた行の例（最初の5行）:")
                for i, line in enumerate(list(missing_lines)[:5]):
                    if line.strip():
                        logger.info(f"     {i+1}. {line[:100]}...")
    
    # 4. 推奨事項
    logger.info("\n=== 4. 推奨事項 ===")
    
    if cleaner_results:
        # 最もデータを保持しているクリーナーを推奨
        best_cleaner = max(cleaner_results.items(), key=lambda x: x[1]["length"])
        logger.info(f"🏆 推奨クリーナー: {best_cleaner[0]} ({best_cleaner[1]['length']:,} 文字)")
        
        # データ損失が大きい場合の警告
        if len(cleaner_results) >= 2:
            lengths = [result["length"] for result in cleaner_results.values()]
            max_length = max(lengths)
            min_length = min(lengths)
            
            if (max_length - min_length) / max_length > 0.1:  # 10%以上の差
                logger.warning("⚠️ クリーナー間で大きなデータ損失が発生しています")
                logger.warning("   Ultra Conservative クリーナーの使用を検討してください")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python debug_excel_processing.py <excel_file_path>")
        print("例: python debug_excel_processing.py 01_ISP案件一覧.xlsx")
        sys.exit(1)
    
    excel_file_path = sys.argv[1]
    debug_excel_processing(excel_file_path)