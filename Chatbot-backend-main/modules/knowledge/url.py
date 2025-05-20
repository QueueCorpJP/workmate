"""
URL処理モジュール
URLからのテキスト抽出と処理を行います
"""
import pandas as pd
from ..utils import transcribe_youtube_video, extract_text_from_html, extract_text_from_pdf
from ..database import ensure_string

async def extract_text_from_url(url: str) -> str:
    """URLからテキストコンテンツを抽出する"""
    try:
        # URLが有効かチェック
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        if 'youtube.com' in url or 'youtu.be' in url:
            return transcribe_youtube_video(url)
        elif url.lower().endswith('.pdf'):
            return await extract_text_from_pdf(url)
        else:
            return await extract_text_from_html(url)
    except Exception as e:
        print(f"URLからのテキスト抽出エラー: {str(e)}")
        return f"URLからのテキスト抽出エラー: {str(e)} ===\n"

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
        
        # エラーが発生しても最低限のデータを返す
        empty_df = pd.DataFrame({
            'section': ["エラー"],
            'content': [f"URL処理中にエラーが発生しました: {str(e)}"],
            'source': ['URL'],
            'url': [url],
            'file': [None]
        })
        empty_sections = {"エラー": f"URL処理中にエラーが発生しました: {str(e)}"}
        error_text = f"=== URL: {url} ===\n\n=== エラー ===\nURL処理中にエラーが発生しました: {str(e)}\n\n"
        
        return empty_df, empty_sections, error_text 