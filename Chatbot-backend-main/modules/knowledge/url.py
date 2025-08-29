"""
URL処理モジュール
URLからのテキスト抽出と処理を行います
"""
import pandas as pd
from ..utils import transcribe_youtube_video, extract_text_from_html, extract_text_from_pdf
from ..database import ensure_string

async def extract_text_from_url(url: str) -> str:
    """URLからテキストコンテンツを抽出する（ユーザーフレンドリーなエラー対応）"""
    try:
        # URLの基本バリデーション
        if not url or not isinstance(url, str):
            return f"❌ 無効なURLが指定されました\n• URLを正しく入力してください\n• 例: https://example.com"
        
        # URLが有効かチェック
        original_url = url
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            print(f"URLにプロトコルを追加: {original_url} → {url}")
        
        # URL形式の簡易チェック
        if not ('.' in url and len(url) > 10):
            return f"❌ URLの形式が正しくありません\n• 正しいURL形式で入力してください\n• 例: https://example.com\n• 入力されたURL: {original_url}"
        
        # URLタイプ別の処理
        if 'youtube.com' in url or 'youtu.be' in url:
            return transcribe_youtube_video(url)
        elif url.lower().endswith('.pdf') or '/pdf' in url.lower():
            return await extract_text_from_pdf(url)
        else:
            return await extract_text_from_html(url)
            
    except Exception as e:
        print(f"URLからのテキスト抽出エラー: {str(e)}")
        return f"❌ URL処理中に予期しないエラーが発生しました\n• 詳細: {str(e)}\n• URLが正しいか確認してください\n• しばらく時間をおいて再試行してください\n• URL: {url}"

async def process_url_content(url: str, extracted_text: str):
    """URLから抽出したテキストを処理する"""
    try:
        # テキストをセクションに分割
        sections = {}
        current_section = "メインコンテンツ"
        section_text = []
        
        # Ensure extracted_text is a string
        extracted_text_str = ensure_string(extracted_text)
        
        for line in extracted_text_str.split('\n'):
            line = ensure_string(line)  # 確実に文字列に変換
            if line.startswith('=== ') and line.endswith(' ==='):
                # 新しいセクションの開始
                if section_text:
                    sections[current_section] = "\n".join([ensure_string(item) for item in section_text])
                    section_text = []
                current_section = line.strip('= ')
            else:
                section_text.append(line)
        
        # 最後のセクションを追加
        if section_text:
            sections[current_section] = "\n".join([ensure_string(item) for item in section_text])
        
        # データフレームを作成
        data = []
        for section_name, content in sections.items():
            data.append({
                'section': ensure_string(section_name),
                'content': ensure_string(content),
                'source': 'URL',
                'url': url,
                'file': None  # ファイルフィールドを明示的に追加
            })
        
        df = pd.DataFrame(data)
        
        # すべての列の値を文字列に変換
        for col in df.columns:
            df[col] = df[col].apply(ensure_string)
            
        return df, sections, extracted_text
    except Exception as e:
        print(f"URL処理エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # ユーザーフレンドリーなエラーメッセージを生成
        error_str = str(e).lower()
        
        if 'memory' in error_str or 'out of memory' in error_str:
            user_error_msg = f"❌ メモリ不足でURL処理を完了できませんでした\n• URLから取得したデータが大きすぎます\n• 別のより小さなページで試してみてください\n• URL: {url}"
        elif 'encoding' in error_str or 'decode' in error_str:
            user_error_msg = f"❌ 文字エンコーディングエラーが発生しました\n• ページの文字コードに問題があります\n• 一部の文字が正しく処理できませんでした\n• URL: {url}"
        elif 'pandas' in error_str or 'dataframe' in error_str:
            user_error_msg = f"❌ データ処理中にエラーが発生しました\n• 抽出されたテキストの構造に問題があります\n• 別のURLで試してみてください\n• URL: {url}"
        else:
            user_error_msg = f"❌ URL処理中にエラーが発生しました\n• 詳細: {str(e)}\n• URLが正しいか確認してください\n• 別のURLで試してみてください\n• URL: {url}"
        
        # エラーが発生しても最低限のデータを返す
        empty_df = pd.DataFrame({
            'section': ["処理エラー"],
            'content': [user_error_msg],
            'source': ['URL'],
            'url': [url],
            'file': [None]
        })
        empty_sections = {"処理エラー": user_error_msg}
        error_text = f"=== URL: {url} ===\n\n=== 処理エラー ===\n{user_error_msg}\n\n"
        
        return empty_df, empty_sections, error_text 