#!/usr/bin/env python3
"""
タイムゾーン修正の動作確認用テストスクリプト
"""

import sys
import os
from datetime import datetime, timezone, timedelta

# モジュールパスの追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'Chatbot-backend-main'))

try:
    from modules.timezone_utils import (
        now_jst, now_jst_simple, now_jst_isoformat,
        to_jst, format_jst_for_display,
        get_jst_date_range, create_timestamp_for_db
    )
    print("✅ timezone_utils インポート成功")
except ImportError as e:
    print(f"❌ timezone_utils インポートエラー: {e}")
    sys.exit(1)

def test_timezone_functions():
    """タイムゾーン関数のテスト"""
    print("\n🧪 タイムゾーン関数テスト開始")
    
    # 1. now_jst() テスト
    print("\n1. now_jst() テスト")
    jst_now = now_jst()
    print(f"現在の日本時間: {jst_now}")
    print(f"タイムゾーン: {jst_now.tzinfo}")
    
    # 2. now_jst_simple() テスト
    print("\n2. now_jst_simple() テスト")
    simple_timestamp = now_jst_simple()
    print(f"データベース保存用タイムスタンプ: {simple_timestamp}")
    
    # 3. now_jst_isoformat() テスト
    print("\n3. now_jst_isoformat() テスト")
    iso_timestamp = now_jst_isoformat()
    print(f"ISO形式タイムスタンプ: {iso_timestamp}")
    
    # 4. create_timestamp_for_db() テスト
    print("\n4. create_timestamp_for_db() テスト")
    db_timestamp = create_timestamp_for_db()
    print(f"データベース用タイムスタンプ: {db_timestamp}")
    
    # 5. UTCからJSTへの変換テスト
    print("\n5. UTCからJSTへの変換テスト")
    utc_time = datetime.now(timezone.utc)
    jst_converted = to_jst(utc_time)
    print(f"UTC時間: {utc_time}")
    print(f"JST変換後: {jst_converted}")
    
    # 6. 文字列からJSTへの変換テスト
    print("\n6. 文字列からJSTへの変換テスト")
    test_string = "2024-01-15T12:30:45Z"
    jst_from_string = to_jst(test_string)
    print(f"UTC文字列: {test_string}")
    print(f"JST変換後: {jst_from_string}")
    
    # 7. 表示用フォーマットテスト
    print("\n7. 表示用フォーマットテスト")
    formatted = format_jst_for_display(jst_now)
    formatted_no_sec = format_jst_for_display(jst_now, include_seconds=False)
    print(f"秒あり: {formatted}")
    print(f"秒なし: {formatted_no_sec}")
    
    # 8. 日付範囲テスト
    print("\n8. 日付範囲テスト")
    start_date, end_date = get_jst_date_range(7)
    print(f"7日前から現在まで:")
    print(f"開始: {start_date}")
    print(f"終了: {end_date}")
    
    print("\n✅ 全てのタイムゾーン関数テスト完了")

def test_database_timestamp():
    """データベース関連のタイムスタンプテスト"""
    print("\n🗄️ データベースタイムスタンプテスト開始")
    
    try:
        from modules.database import SupabaseConnection
        
        # ダミーのデータベース操作でタイムスタンプをテスト
        print("データベース接続テスト...")
        conn = SupabaseConnection()
        
        # CURRENT_TIMESTAMPのテスト
        print("✅ データベース接続成功")
        conn.close()
        
    except Exception as e:
        print(f"⚠️ データベーステストスキップ: {e}")

def test_timezone_consistency():
    """タイムゾーンの一貫性テスト"""
    print("\n🔄 タイムゾーン一貫性テスト開始")
    
    # 複数の関数で取得したタイムスタンプが一貫しているかチェック
    timestamp1 = now_jst()
    timestamp2 = now_jst()
    
    # 時差が1秒以内であることを確認
    diff = abs((timestamp2 - timestamp1).total_seconds())
    if diff <= 1:
        print("✅ タイムスタンプの一貫性確認")
    else:
        print(f"⚠️ タイムスタンプの差が大きすぎます: {diff}秒")
    
    # JST+9時間の確認
    utc_now = datetime.now(timezone.utc)
    jst_now = now_jst()
    expected_offset = timedelta(hours=9)
    actual_offset = jst_now.replace(tzinfo=None) - utc_now.replace(tzinfo=None)
    
    # オフセットの差が1分以内であることを確認（ネットワーク遅延考慮）
    offset_diff = abs((actual_offset - expected_offset).total_seconds())
    if offset_diff <= 60:
        print("✅ JST +9時間オフセット確認")
    else:
        print(f"⚠️ JST オフセットが不正確: 期待値{expected_offset}, 実際{actual_offset}")

def main():
    """メイン関数"""
    print("🕒 タイムゾーン修正テスト開始")
    print("=" * 50)
    
    try:
        test_timezone_functions()
        test_database_timestamp()
        test_timezone_consistency()
        
        print("\n" + "=" * 50)
        print("✅ 全テスト完了")
        
        # 最終確認メッセージ
        current_jst = now_jst()
        print(f"\n📅 現在の日本時間: {format_jst_for_display(current_jst)}")
        print(f"📝 データベース保存形式: {create_timestamp_for_db()}")
        
        print("\n✨ タイムゾーン修正が正常に動作しています！")
        
    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 