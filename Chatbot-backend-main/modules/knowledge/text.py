"""
テキストファイル処理モジュール
テキストファイルの読み込みと処理を行います
"""
import pandas as pd
import re
import traceback

def process_txt_file(contents, filename):
    """テキストファイルを処理してデータフレーム、セクション、テキストを返す"""
    try:
        # テキストを抽出
        try:
            text = contents.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = contents.decode('shift-jis')
            except UnicodeDecodeError:
                text = contents.decode('latin-1')
        
        # テキストをセクションに分割
        # 見出しパターン
        heading_pattern = r'^(?:\d+[\.\s]+|第\d+[章節]\s+|[\*\#]+\s+)?([A-Za-z\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]{2,}[：:、。])'
        
        # データを作成
        all_data = []
        sections = {}
        extracted_text = f"=== ファイル: {filename} ===\n\n"
        
        current_section = "一般情報"
        current_content = []
        
        # 必ずテキストが文字列であることを確認
        text = str(text) if text is not None else ""
        
        for line in text.split("\n"):
            line = str(line).strip()
            if not line:
                continue
            
            # 見出しかどうかを判定
            if re.search(heading_pattern, line):
                # 前のセクションを保存
                if current_content:
                    # 必ず文字列に変換してから結合
                    content_text = "\n".join([str(item) for item in current_content])
                    sections[str(current_section)] = content_text
                    extracted_text += f"=== {current_section} ===\n{content_text}\n\n"
                    all_data.append({
                        'section': str(current_section),
                        'content': content_text,
                        'source': 'TXT',
                        'file': filename,
                        'url': None
                    })
                
                # 新しいセクションを開始
                current_section = str(line)
                current_content = []
            else:
                current_content.append(str(line))
        
        # 最後のセクションを保存
        if current_content:
            # 必ず文字列に変換してから結合
            content_text = "\n".join([str(item) for item in current_content])
            sections[str(current_section)] = content_text
            extracted_text += f"=== {current_section} ===\n{content_text}\n\n"
            all_data.append({
                'section': str(current_section),
                'content': content_text,
                'source': 'TXT',
                'file': filename,
                'url': None
            })
        
        # データフレームを作成
        result_df = pd.DataFrame(all_data) if all_data else pd.DataFrame({
            'section': ["一般情報"],
            'content': [str(text)],
            'source': ['TXT'],
            'file': [filename],
            'url': [None]
        })
        
        return result_df, sections, extracted_text
    except Exception as e:
        print(f"テキストファイル処理エラー: {str(e)}")
        print(traceback.format_exc())
        
        # エラーが発生しても最低限のデータを返す
        empty_df = pd.DataFrame({
            'section': ["エラー"],
            'content': [f"テキストファイル処理中にエラーが発生しました: {str(e)}"],
            'source': ['TXT'],
            'file': [filename],
            'url': [None]
        })
        empty_sections = {"エラー": f"テキストファイル処理中にエラーが発生しました: {str(e)}"}
        error_text = f"=== ファイル: {filename} ===\n\n=== エラー ===\nテキストファイル処理中にエラーが発生しました: {str(e)}\n\n"
        
        return empty_df, empty_sections, error_text 