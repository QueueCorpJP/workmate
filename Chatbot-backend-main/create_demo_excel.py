#!/usr/bin/env python3
"""
デモ用ISP案件Excelファイル作成スクリプト
Excel データ損失修正の効果を検証するためのサンプルファイルを生成
"""

import pandas as pd
import os
from datetime import datetime, timedelta
import random

def create_demo_isp_excel():
    """ISP案件一覧のデモExcelファイルを作成"""
    
    # サンプルデータの定義
    statuses = ['新規', '進行中', '完了', '保留', '取消']
    customers = ['株式会社A', '有限会社B', 'C商事', 'D工業', 'E建設']
    isp_codes = [f'ISP{str(i).zfill(6)}' for i in range(100001, 100051)]
    ss_numbers = [f'SS{str(i).zfill(7)}' for i in range(1000001, 1000051)]
    
    # データ生成
    data = []
    base_date = datetime.now() - timedelta(days=365)
    
    for i in range(50):  # 50件のサンプルデータ
        row = {
            'ISP番号': isp_codes[i],
            'SS番号': ss_numbers[i],
            'ステータス': random.choice(statuses),
            '顧客名': random.choice(customers),
            '契約日': (base_date + timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d'),
            '獲得金額': random.randint(100000, 5000000),
            '担当者': f'担当者{chr(65 + i % 26)}',
            '備考': f'案件{i+1}の詳細情報。重要な業務データが含まれています。',
            '書類発行': '済' if random.random() > 0.3 else '未',
            '請求状況': '完了' if random.random() > 0.4 else '未完了',
            'mail送信': '済' if random.random() > 0.2 else '未',
            '解約予定': '無' if random.random() > 0.1 else '有'
        }
        data.append(row)
    
    # DataFrameに変換
    df = pd.DataFrame(data)
    
    # Excelファイルとして保存
    filename = '01_ISP案件一覧.xlsx'
    filepath = os.path.join(os.getcwd(), filename)
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # メインシート
        df.to_excel(writer, sheet_name='案件一覧', index=False)
        
        # 追加のメタデータシート（従来版では除外されがちなデータ）
        metadata_df = pd.DataFrame({
            'ID': ['A', 'B', 'C'],  # 短い識別子
            '値': [1, 2, 3],        # 数値のみ
            '記号': ['#', '*', '@'] # 記号のみ
        })
        metadata_df.to_excel(writer, sheet_name='メタデータ', index=False)
        
        # 統計シート
        stats_df = pd.DataFrame({
            '項目': ['総件数', '完了件数', '進行中件数'],
            '値': [len(df), len(df[df['ステータス'] == '完了']), len(df[df['ステータス'] == '進行中'])]
        })
        stats_df.to_excel(writer, sheet_name='統計', index=False)
    
    print(f"✅ デモExcelファイルを作成しました: {filepath}")
    print(f"📊 データ件数: {len(df)}件")
    print(f"📋 シート数: 3枚 (案件一覧, メタデータ, 統計)")
    
    return filepath

if __name__ == "__main__":
    create_demo_isp_excel()