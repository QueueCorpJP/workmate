"""
テキストファイル処理モジュール
テキストファイルの読み込みと処理を行います（文字化け対応強化版）
"""
import pandas as pd
import re
import traceback
import asyncio
import logging
import tempfile
import os
from ..database import ensure_string

logger = logging.getLogger(__name__)

async def process_txt_file(contents, filename):
    """テキストファイルを処理してデータフレーム、セクション、テキストを返す（文字化け対応版）"""
    try:
        # CSV処理から文字化け検出機能をインポート
        from .csv_processor import detect_csv_encoding, detect_mojibake_in_content
        
        # エンコーディング検出と文字化けチェック
        detected_encoding = detect_csv_encoding(contents)
        has_mojibake = detect_mojibake_in_content(contents, detected_encoding)
        
        if has_mojibake:
            logger.info(f"テキストファイルで文字化け検出 - Gemini生ファイル処理を使用: {filename}")
            # Gemini生ファイル処理を実行
            gemini_result = await process_txt_with_gemini(contents, filename)
            if gemini_result:
                return gemini_result
            logger.warning("Gemini処理失敗 - 従来処理にフォールバック")
        
        # 従来のエンコーディング試行
        try:
            text = contents.decode(detected_encoding)
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

async def process_txt_with_gemini(contents: bytes, filename: str):
    """Gemini生ファイル処理を使用してテキストファイルを処理する"""
    try:
        from ..config import setup_gemini
        
        logger.info(f"テキストファイル処理開始（Gemini生ファイル解析使用）: {filename}")
        
        # Geminiモデルをセットアップ
        model = setup_gemini()
        if not model:
            logger.error("Geminiモデルの初期化に失敗")
            return None
        
        # 生のテキストファイルを一時ファイルとして保存
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
            tmp_file.write(contents)
            tmp_file_path = tmp_file.name
        
        # Gemini用プロンプト（テキストファイル特化）
        prompt = """
        このテキストファイルには文字化けしたデータが含まれている可能性があります。
        ファイルの内容を正確に読み取り、文字化けがあれば適切に復元してください。

        **重要な指示：**
        1. ファイルの正しいエンコーディングを自動判定して読み取ってください
        2. 文字化け文字が見つかった場合は、文脈から推測して正しい日本語に復元してください
        3. 段落構造、改行、見出しなどの文書構造を正確に保持してください
        4. 箇条書きや番号付きリストの構造も保持してください

        **文字化け復元の例：**
        - 縺ゅ→縺 → あと
        - 迺ｾ遶 → 環境  
        - 荳?蟋 → 会社
        - 繧ｳ繝ｳ繝斐Η繝ｼ繧ｿ → コンピュータ

        **出力形式：**
        元の文書構造を保った形で、復元されたテキストを出力してください。
        復元できない文字化けは [文字化け] と明記してください。
        """
        
        def sync_gemini_call():
            try:
                import google.generativeai as genai
                
                # テキストファイルを直接読み込んでGeminiで処理
                with open(tmp_file_path, 'rb') as f:
                    file_content = f.read()
                
                # テキストとしてデコード
                try:
                    from .csv_processor import detect_csv_encoding
                    encoding = detect_csv_encoding(file_content)
                    text_content = file_content.decode(encoding)
                except:
                    try:
                        text_content = file_content.decode('utf-8')
                    except:
                        text_content = file_content.decode('shift-jis', errors='ignore')
                
                # プロンプトにテキスト内容を含めて処理
                full_prompt = f"{prompt}\n\n以下が復元が必要なテキストファイルの内容です：\n\n{text_content}"
                response = model.generate_content(full_prompt)
                
                return response.text if response.text else ""
            except Exception as e:
                logger.error(f"Gemini生ファイル処理エラー: {str(e)}")
                return ""
            finally:
                # 一時ファイルを削除
                try:
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
                except:
                    pass
        
        extracted_text = await asyncio.to_thread(sync_gemini_call)
        
        if not extracted_text:
            logger.warning("Gemini生ファイル処理からテキストを抽出できませんでした")
            return None
        
        logger.info(f"Gemini生ファイル処理結果（最初の500文字）: {extracted_text[:500]}...")
        
        # 抽出したテキストからDataFrameを作成
        sections = {}
        all_data = []
        
        # テキストをセクションに分割（見出しパターン）
        heading_pattern = r'^(?:\d+[\.\s]+|第\d+[章節]\s+|[\*\#]+\s+)?([A-Za-z\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]{2,}[：:、。])'
        
        current_section = "復元されたテキスト"
        current_content = []
        
        for line in extracted_text.split("\n"):
            line = ensure_string(line).strip()
            if not line:
                continue
            
            # 見出しかどうかを判定
            if re.search(heading_pattern, line):
                # 前のセクションを保存
                if current_content:
                    content_text = "\n".join([ensure_string(item) for item in current_content])
                    sections[ensure_string(current_section)] = content_text
                    all_data.append({
                        'section': ensure_string(current_section),
                        'content': content_text,
                        'source': 'TXT (Gemini復元)',
                        'file': filename,
                        'url': None
                    })
                
                # 新しいセクションを開始
                current_section = ensure_string(line)
                current_content = []
            else:
                current_content.append(ensure_string(line))
        
        # 最後のセクションを保存
        if current_content:
            content_text = "\n".join([ensure_string(item) for item in current_content])
            sections[ensure_string(current_section)] = content_text
            all_data.append({
                'section': ensure_string(current_section),
                'content': content_text,
                'source': 'TXT (Gemini復元)',
                'file': filename,
                'url': None
            })
        
        # データフレームが空の場合の対応
        if not all_data:
            all_data.append({
                'section': "復元されたテキスト",
                'content': ensure_string(extracted_text),
                'source': 'TXT (Gemini復元)',
                'file': filename,
                'url': None
            })
            sections["復元されたテキスト"] = ensure_string(extracted_text)
        
        result_df = pd.DataFrame(all_data)
        
        # すべての列の値を文字列に変換
        for col in result_df.columns:
            result_df[col] = result_df[col].apply(ensure_string)
        
        # 完全なテキスト情報
        full_text = f"=== ファイル: {filename} (Gemini文字化け復元) ===\n\n"
        for section_name, content in sections.items():
            full_text += f"=== {section_name} ===\n{content}\n\n"
        
        logger.info(f"テキストファイル処理完了（Gemini復元）: {len(result_df)} セクション")
        return result_df, sections, full_text
        
    except Exception as e:
        logger.error(f"Geminiテキストファイル処理エラー: {str(e)}")
        return None 