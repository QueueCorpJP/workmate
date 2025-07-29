#!/usr/bin/env python3
"""
PDF文字化け修復のテストスクリプト
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from knowledge.pdf import fix_mojibake_text, check_text_corruption

def test_pdf_fix():
    """ユーザー報告の文字化けテキストをテスト"""
    
    # ユーザー報告の文字化けテキスト
    corrupted_text = """
˔جຊΞΠςϜ υϥΠϒʗ%7%ϚϧνυϥΠϒ 
 Ϟχλʔʗ%)'ܕӷথ 
˔ඪ४౥ࡌιϑτ 0GpDF)PNF#VTJOFTT ʢ104"൛ʣ 
 "QQ(VBSE4PMP  $BOPOJNBHF8"3&%FTLUPQ 
˔֎ܗੇ๏ɾ ࣭ྔ ʢ8
ʷ ʢ)
ʷ ʢ%
ᶱ 
 ໿LH ʢόοςϦʔؚΉʣ˔εϖοΫ 04ʗ8JOEPXT1SPCJU 
 $16ʗ$PSF6MUSB6()[  ϝϞϦʗ%%3(#  σΟεΫʗ44%(#
"""
    
    print("=== PDF文字化け修復テスト ===")
    print(f"元のテキスト:\n{corrupted_text}")
    print("\n" + "="*50 + "\n")
    
    # 文字化け検出テスト
    is_corrupted = check_text_corruption(corrupted_text)
    print(f"文字化け検出結果: {is_corrupted}")
    
    # 文字化け修復テスト
    fixed_text = fix_mojibake_text(corrupted_text)
    print(f"修復後のテキスト:\n{fixed_text}")
    
    print("\n" + "="*50 + "\n")
    
    # 期待される結果
    expected_keywords = [
        "マルチドライブ", "DVDマルチドライブ", "モニター", "型番",
        "標準搭載ソフト", "PDF", "HOME", "BUSINESS", "POS版",
        "AppGuard", "Solo", "Canonimage", "WARE", "Desktop",
        "外形寸法", "質量", "約", "kg", "バッテリー含む",
        "スペック", "OS", "Windows", "Pro", "bit",
        "CPU", "Core", "Ultra", "GHz", "メモリー", "DDR", "GB",
        "ディスク", "SSD"
    ]
    
    print("期待されるキーワード:")
    for keyword in expected_keywords:
        if keyword in fixed_text:
            print(f"✅ '{keyword}' - 修復成功")
        else:
            print(f"❌ '{keyword}' - 修復失敗")
    
    return fixed_text

if __name__ == "__main__":
    test_pdf_fix() 