"""
チャットユーティリティ関数
チャット機能で使用する共通のユーティリティ関数を管理します
"""
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

def chunk_knowledge_base(text: str, chunk_size: int = 1200) -> list[str]:
    """
    知識ベースを指定されたサイズでチャンク化する
    
    Args:
        text: チャンク化するテキスト
        chunk_size: チャンクのサイズ（文字数）デフォルト1200文字（task.yaml推奨）
    
    Returns:
        チャンク化されたテキストのリスト
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    overlap = int(chunk_size * 0.5)  # 50%のオーバーラップ（task.yaml推奨）
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        
        # チャンクの境界を調整（文の途中で切れないように）
        if end < len(text):
            # 最後の改行を探す
            search_start = max(start, end - 200)  # 200文字前から検索（1200文字チャンクに適正化）
            last_newline = text.rfind('\n', search_start, end)
            if last_newline > start:
                end = last_newline + 1
            else:
                # 改行がない場合は最後のスペースを探す
                last_space = text.rfind(' ', search_start, end)
                if last_space > start:
                    end = last_space + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # 次の開始位置（オーバーラップを考慮）
        if end < len(text):
            start = max(start + 1, end - overlap)
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