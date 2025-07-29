#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF文字化け修正テスト
"""

import sys
import os

# 'Chatbot-backend-main' ディレクトリを Python のパスに追加して、
# 'modules' をトップレベルパッケージとしてインポートできるようにします
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from modules.knowledge.pdf import fix_mojibake_text, check_text_corruption

def test_pdf_fix():
    # ユーザーから報告された文字化けテキスト
    corrupted_text = """˔εϖοΫ 04ʗ8JOEPXT1SPCJU 
 $16ʗ$PSFJ()[  ϝϞϦʗ1$	%%3
(#  σΟεΫʗ44%(#。 
˔جຊΞΠςϜ υϥΠϒʗ%7%ϚϧνυϥΠϒ ˔ඪ४౥ࡌιϑτ 0GpDF)PNF#VTJOFTT ʢ104"൛ʣ 
 "QQ(VBSE4PMP  $BOPOJNBHF8"3&%FTLUPQ 
(16૿ઃ ʢ/7*%*""ʣ ˠˇ ʢ੫=ࠐʣ ɹ˔εϖοΫ 04ʗ8JOEPXT1SPCJU 
 $16ʗ$PSFJ6()[  ϝϞϦʗ%%3(#  σΟεΫʗ44%(#"""
    
    print("=== PDF文字化け修正テスト ===")
    print(f"元のテキスト:\n{corrupted_text}\n")
    
    # 文字化けチェック
    is_corrupted = check_text_corruption(corrupted_text)
    print(f"文字化け検出: {'はい' if is_corrupted else 'いいえ'}")
    
    if is_corrupted:
        # 修復実行
        fixed_text = fix_mojibake_text(corrupted_text)
        print(f"修復後のテキスト:\n{fixed_text}\n")
        
        # 期待されるキーワードをチェック
        expected_keywords = ['Windows', 'マルチドライブ', 'BUSINESS', 'スペック', 'PC', 'メモリ', 'ディスク']
        found_keywords = [kw for kw in expected_keywords if kw in fixed_text]
        
        print(f"期待されるキーワード: {expected_keywords}")
        print(f"見つかったキーワード: {found_keywords}")
        print(f"修復成功率: {len(found_keywords)}/{len(expected_keywords)} ({len(found_keywords)/len(expected_keywords)*100:.1f}%)")
        
        # 再度文字化けチェック
        still_corrupted = check_text_corruption(fixed_text)
        print(f"修復後の文字化け: {'まだあり' if still_corrupted else 'なし'}")
    else:
        print("文字化けが検出されませんでした。")

if __name__ == "__main__":
    test_pdf_fix() 