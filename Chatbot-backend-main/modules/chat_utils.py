"""
チャットユーティリティ関数
チャット機能で使用する共通のユーティリティ関数を管理します
"""
import re
from .utils import safe_print, safe_safe_print

def safe_print(text):
    """Windows環境でのUnicode文字エンコーディング問題を回避する安全なprint関数"""
    try:
        print(text)
    except UnicodeEncodeError:
        # エンコーディングエラーが発生した場合は、問題のある文字を置換
        try:
            safe_text = str(text).encode('utf-8', errors='replace').decode('utf-8')
            print(safe_text)
        except:
            # それでも失敗する場合はエラーメッセージのみ出力
            print("[出力エラー: Unicode文字を含むメッセージ]")

def safe_safe_print(text):
    """Windows環境でのUnicode文字エンコーディング問題を回避する安全なsafe_print関数"""
    safe_print(text)

def chunk_knowledge_base(text: str, chunk_size: int = 700) -> list[str]:  # 🎯 デフォルト700文字（600-800文字範囲の中央値）
    """
    知識ベースを指定されたサイズでチャンク化する（600-800文字厳守）
    CSV構造を検出して顧客境界を保護する高精度分割
    
    Args:
        text: チャンク化するテキスト
        chunk_size: チャンクのサイズ（文字数）デフォルト700文字（600-800文字範囲）
    
    Returns:
        チャンク化されたテキストのリスト（各チャンク600-800文字以内）
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    # 🎯 CSV構造検出と分割戦略の選択
    if _is_csv_structure(text):
        return _csv_aware_chunking(text, chunk_size)
    else:
        return _traditional_chunking(text, chunk_size)


def _is_csv_structure(text: str) -> bool:
    """CSV構造を検出（顧客番号、物件番号、区切り文字の存在）"""
    # CSV構造の特徴を検出
    customer_pattern = r'SS\d{7}'  # 顧客番号パターン
    property_pattern = r'WP[DN]\d{7}'  # 物件番号パターン
    separator_pattern = r'\s*\|\s*'  # CSV区切り文字
    
    has_customer_numbers = len(re.findall(customer_pattern, text)) >= 2
    has_property_numbers = len(re.findall(property_pattern, text)) >= 2
    has_separators = len(re.findall(separator_pattern, text)) >= 5
    
    return has_customer_numbers and has_property_numbers and has_separators


def _csv_aware_chunking(text: str, chunk_size: int) -> list[str]:
    """CSV構造認識分割 - 顧客境界を絶対保護"""
    chunks = []
    lines = text.split('\n')
    current_chunk = ""
    current_customer = None
    max_chunk_size = 800  # 絶対最大サイズ
    min_chunk_size = 400  # CSV用最小サイズ（顧客境界優先）
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 🎯 顧客番号検出
        customer_match = re.search(r'SS\d{7}', line)
        line_customer = customer_match.group() if customer_match else None
        
        # 顧客境界での分割判定
        should_split_for_customer = False
        if (current_customer and line_customer and 
            current_customer != line_customer and 
            len(current_chunk) >= min_chunk_size):
            should_split_for_customer = True
        
        # サイズ制限での分割判定
        potential_chunk = current_chunk + ('\n' + line if current_chunk else line)
        should_split_for_size = len(potential_chunk) > chunk_size
        
        # 🎯 分割決定（顧客境界優先）
        if should_split_for_customer:
            # 顧客境界で分割（最優先）
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = line
            current_customer = line_customer
        elif should_split_for_size and len(current_chunk) >= min_chunk_size:
            # サイズ制限で分割
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = line
            current_customer = line_customer or current_customer
        elif len(potential_chunk) > max_chunk_size:
            # 絶対最大サイズで強制分割
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = line
            current_customer = line_customer or current_customer
        else:
            # 継続
            current_chunk = potential_chunk
            if line_customer:
                current_customer = line_customer
    
    # 最後のチャンクを追加
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks if chunks else [text]


def _traditional_chunking(text: str, chunk_size: int) -> list[str]:
    """従来の分割方式（PDF、Word等の非構造化テキスト用）"""
    chunks = []
    start = 0
    max_chunk_size = 800  # 🎯 絶対最大サイズ
    min_chunk_size = 600  # 🎯 最小サイズ
    overlap = 50  # 🎯 固定50文字オーバーラップ（サイズ制御のため）
    
    while start < len(text):
        # 基本的なチャンクサイズを設定
        end = min(start + chunk_size, len(text))
        
        # チャンクの境界を調整（文の途中で切れないように）
        if end < len(text):
            # 最後の改行を探す（検索範囲を制限）
            search_start = max(start, end - 50)  # 🎯 50文字前から検索（サイズ制御）
            last_newline = text.rfind('\n', search_start, end)
            if last_newline > start:
                end = last_newline + 1
            else:
                # 改行がない場合は最後のスペースを探す
                last_space = text.rfind(' ', search_start, end)
                if last_space > start:
                    end = last_space + 1
        
        # 🎯 チャンクサイズが最大値を超える場合は強制的に切断
        if end - start > max_chunk_size:
            end = start + max_chunk_size
            # 文字の途中で切れないように最後のスペースまで戻る
            last_space = text.rfind(' ', start, end)
            if last_space > start:
                end = last_space
        
        chunk = text[start:end].strip()
        
        # 🎯 チャンクサイズが範囲内かチェック
        if chunk:
            chunk_length = len(chunk)
            if chunk_length <= max_chunk_size:  # 800文字以下なら追加
                chunks.append(chunk)
            else:
                # 800文字を超える場合は強制分割
                while len(chunk) > max_chunk_size:
                    sub_chunk = chunk[:max_chunk_size]
                    # 最後のスペースで切る
                    last_space = sub_chunk.rfind(' ')
                    if last_space > min_chunk_size:  # 600文字以上の位置にスペースがある場合
                        sub_chunk = sub_chunk[:last_space]
                    chunks.append(sub_chunk)
                    chunk = chunk[len(sub_chunk):].strip()
                
                # 残りのチャンクも追加
                if chunk:
                    chunks.append(chunk)
        
        # 次の開始位置（オーバーラップを考慮）
        if end < len(text):
            start = max(start + min_chunk_size, end - overlap)  # 🎯 最小600文字は進む
        else:
            start = end
    
    return chunks

def expand_query(query: str) -> str:
    """
    クエリ拡張 - 類義語や関連用語を追加して検索精度を向上
    """
    # 基本的なクエリ拡張のマッピング
    expansion_map = {
        '方法': ['手順', 'やり方', 'プロセス', '流れ'],
        '手順': ['方法', 'ステップ', 'プロセス', '流れ'],
        '問題': ['課題', 'トラブル', 'エラー', '不具合'],
        '設定': ['構成', 'コンフィグ', '設定値', 'セットアップ'],
        '使い方': ['利用方法', '操作方法', '使用方法', '操作手順'],
        'エラー': ['問題', 'トラブル', '不具合', 'バグ'],
        '料金': ['価格', '費用', 'コスト', '値段'],
        '機能': ['特徴', '仕様', '性能', '能力'],
    }
    
    expanded_terms = []
    query_words = query.split()
    
    for word in query_words:
        expanded_terms.append(word)
        if word in expansion_map:
            # 1つの類義語を追加（クエリが長くなりすぎないように）
            expanded_terms.append(expansion_map[word][0])
    
    expanded_query = ' '.join(expanded_terms)
    return expanded_query if len(expanded_query) <= len(query) * 2 else query