"""
日本時間（JST）でのタイムスタンプ処理を統一するユーティリティモジュール
全てのデータ更新、保存時に日本時間を使用するためのヘルパー関数を提供
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Union
import pytz

# 日本時間のタイムゾーンオブジェクト
JST = timezone(timedelta(hours=9))
TOKYO_TZ = pytz.timezone('Asia/Tokyo')

def now_jst() -> datetime:
    """
    現在の日本時間（JST）を取得
    
    Returns:
        datetime: 日本時間のdatetimeオブジェクト
    """
    return datetime.now(JST)

def now_jst_isoformat() -> str:
    """
    現在の日本時間をISO形式の文字列で取得
    
    Returns:
        str: ISO形式の日本時間文字列（例: "2024-01-15T09:30:45+09:00"）
    """
    return now_jst().isoformat()

def now_jst_simple() -> str:
    """
    現在の日本時間をシンプルな形式で取得（タイムゾーン情報なし）
    既存のコードとの互換性を保つため
    
    Returns:
        str: ISO形式の日本時間文字列（例: "2024-01-15T09:30:45"）
    """
    return now_jst().replace(tzinfo=None).isoformat()

def to_jst(dt: Union[datetime, str]) -> datetime:
    """
    任意のdatetimeオブジェクトまたは文字列を日本時間に変換
    
    Args:
        dt: 変換対象のdatetimeオブジェクトまたはISO形式文字列
        
    Returns:
        datetime: 日本時間に変換されたdatetimeオブジェクト
    """
    if isinstance(dt, str):
        # 文字列の場合はパース
        if dt.endswith('Z'):
            dt = dt.replace('Z', '+00:00')
        dt = datetime.fromisoformat(dt)
    
    # タイムゾーン情報がない場合はUTCとして扱う
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # 日本時間に変換
    return dt.astimezone(JST)

def format_jst_for_display(dt: Union[datetime, str], include_seconds: bool = True) -> str:
    """
    日本時間での表示用フォーマット
    
    Args:
        dt: フォーマット対象のdatetimeオブジェクトまたは文字列
        include_seconds: 秒を含めるかどうか
        
    Returns:
        str: 表示用にフォーマットされた日本時間文字列
    """
    if isinstance(dt, str):
        dt = to_jst(dt)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc).astimezone(JST)
    else:
        dt = dt.astimezone(JST)
    
    if include_seconds:
        return dt.strftime('%Y-%m-%d %H:%M:%S JST')
    else:
        return dt.strftime('%Y-%m-%d %H:%M JST')

def get_jst_date_range(days: int) -> tuple[datetime, datetime]:
    """
    現在から指定日数前までの日本時間での日付範囲を取得
    
    Args:
        days: 過去何日分を取得するか
        
    Returns:
        tuple: (開始日時, 終了日時) の日本時間
    """
    end_date = now_jst()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date

def validate_and_convert_timestamp(timestamp: Optional[str]) -> Optional[datetime]:
    """
    タイムスタンプ文字列を検証し、日本時間のdatetimeオブジェクトに変換
    
    Args:
        timestamp: 検証対象のタイムスタンプ文字列
        
    Returns:
        datetime: 日本時間のdatetimeオブジェクト、無効な場合はNone
    """
    if not timestamp:
        return None
    
    try:
        return to_jst(timestamp)
    except (ValueError, TypeError):
        return None

def create_timestamp_for_db() -> str:
    """
    データベース保存用のタイムスタンプを作成
    
    Returns:
        str: データベース保存用の日本時間タイムスタンプ
    """
    return now_jst_simple()

# レガシーコード互換性のためのエイリアス
def get_current_jst_timestamp() -> str:
    """レガシーコード互換性のためのエイリアス"""
    return now_jst_simple()

def get_current_jst_datetime() -> datetime:
    """レガシーコード互換性のためのエイリアス"""
    return now_jst() 