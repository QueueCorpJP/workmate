#!/usr/bin/env python3
"""
Clear Python Cache and Restart Script
このスクリプトはPythonキャッシュをクリアして問題を解決します
"""

import os
import shutil
import sys
from pathlib import Path

def clear_python_cache():
    """Pythonキャッシュファイルを削除する"""
    print("🧹 Pythonキャッシュをクリア中...")
    
    current_dir = Path(".")
    cache_dirs_removed = 0
    pyc_files_removed = 0
    
    # __pycache__ ディレクトリを削除
    for pycache_dir in current_dir.rglob("__pycache__"):
        try:
            shutil.rmtree(pycache_dir)
            cache_dirs_removed += 1
            print(f"🗑️ 削除: {pycache_dir}")
        except Exception as e:
            print(f"❌ 削除失敗: {pycache_dir} - {e}")
    
    # .pyc ファイルを削除
    for pyc_file in current_dir.rglob("*.pyc"):
        try:
            pyc_file.unlink()
            pyc_files_removed += 1
            print(f"🗑️ 削除: {pyc_file}")
        except Exception as e:
            print(f"❌ 削除失敗: {pyc_file} - {e}")
    
    print(f"✅ キャッシュクリア完了:")
    print(f"   - __pycache__ ディレクトリ: {cache_dirs_removed}個")
    print(f"   - .pyc ファイル: {pyc_files_removed}個")

def check_problematic_files():
    """問題のあるファイルをチェックする"""
    print("\n🔍 問題のあるコードパターンをチェック中...")
    
    problematic_patterns = [
        'chunks.*active.*eq.*True',
        'chunks.*select.*active',
        '&active=eq.True'
    ]
    
    python_files = list(Path(".").rglob("*.py"))
    issues_found = []
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern in problematic_patterns:
                import re
                if re.search(pattern, content):
                    issues_found.append(f"{py_file}: {pattern}")
        except Exception as e:
            print(f"⚠️ ファイル読み込みエラー: {py_file} - {e}")
    
    if issues_found:
        print("❌ 問題のあるコードが見つかりました:")
        for issue in issues_found:
            print(f"   - {issue}")
        return False
    else:
        print("✅ 問題のあるコードパターンは見つかりませんでした")
        return True

def main():
    """メイン実行関数"""
    print("🔧 Clear Cache and Restart Script")
    print("=" * 50)
    
    # 1. Pythonキャッシュをクリア
    clear_python_cache()
    
    # 2. 問題のあるファイルをチェック
    code_ok = check_problematic_files()
    
    print("\n📋 推奨アクション:")
    print("=" * 50)
    
    if code_ok:
        print("✅ コードは修正済みです")
        print("💡 次の手順を実行してください:")
        print("   1. アプリケーションサーバーを停止")
        print("   2. このスクリプトでキャッシュをクリア済み")
        print("   3. アプリケーションサーバーを再起動")
        print("   4. 問題が解決されているかテスト")
    else:
        print("❌ まだ問題のあるコードが残っています")
        print("💡 上記の問題を修正してから再実行してください")
    
    print("\n🚀 アプリケーション再起動コマンド:")
    print("   python main.py")
    print("   または")
    print("   uvicorn main:app --reload")

if __name__ == "__main__":
    main()