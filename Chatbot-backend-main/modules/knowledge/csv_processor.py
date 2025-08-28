"""
CSVファイル処理モジュール
Google Sheets APIを使用してCSVファイルの読み込みと処理を行います
"""
import pandas as pd
import csv
import traceback
import tempfile
import os
import logging
from io import StringIO, BytesIO
from typing import Optional, Dict, Any, Tuple
import asyncio
from ..database import ensure_string
from .unnamed_column_handler import UnnamedColumnHandler

# ロガーの設定
logger = logging.getLogger(__name__)

try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False
    print("chardetがインストールされていません。pip install chardetを実行することを推奨します。")

# Google Sheets API設定
try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    GOOGLE_SHEETS_AVAILABLE = True
    logger.info("Google Sheets APIライブラリが利用可能です")
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    logger.warning("Google Sheets APIライブラリが見つかりません。pip install google-api-python-clientを実行してください。")

def detect_csv_encoding(content: bytes) -> str:
    """CSVファイルの文字エンコーディングを検出する（文字化け判定強化版）"""
    try:
        # chardetが利用可能な場合は使用
        if CHARDET_AVAILABLE:
            result = chardet.detect(content)
            encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0)
            
            print(f"検出されたエンコーディング: {encoding} (信頼度: {confidence:.2f})")
            
            # 文字化け判定を実行
            mojibake_detected = detect_mojibake_in_content(content, encoding)
            
            # 文字化けが検出された場合、または信頼度が低い場合は一般的なエンコーディングを試行
            if mojibake_detected or confidence < 0.7:
                print(f"文字化けまたは低信頼度検出。代替エンコーディングを試行します")
                common_encodings = ['utf-8', 'shift_jis', 'cp932', 'euc-jp', 'iso-2022-jp']
                for enc in common_encodings:
                    try:
                        decoded_text = content.decode(enc)
                        # 各エンコーディングで文字化けチェック
                        if not detect_mojibake_in_text(decoded_text):
                            print(f"文字化けのないエンコーディング発見: {enc}")
                            return enc
                    except UnicodeDecodeError:
                        continue
            
            return encoding if encoding else 'utf-8'
        else:
            # chardetが利用できない場合は一般的なエンコーディングを順次試行
            print("chardetが利用できないため、一般的なエンコーディングを試行します")
            common_encodings = ['utf-8', 'shift_jis', 'cp932', 'euc-jp', 'iso-2022-jp', 'latin-1']
            for enc in common_encodings:
                try:
                    decoded_text = content.decode(enc)
                    # 文字化けチェック
                    if not detect_mojibake_in_text(decoded_text):
                        print(f"文字化けのないエンコーディング発見: {enc}")
                        return enc
                except UnicodeDecodeError:
                    continue
            
            # どれも成功しなかった場合はutf-8をデフォルトとして使用
            print("エンコーディング検出に失敗、utf-8を使用")
            return 'utf-8'
        
    except Exception as e:
        print(f"エンコーディング検出エラー: {str(e)}")
        return 'utf-8'

def detect_mojibake_in_content(content: bytes, encoding: str) -> bool:
    """バイトコンテンツを指定エンコーディングでデコードして文字化けを検出"""
    try:
        decoded_text = content.decode(encoding, errors='ignore')
        return detect_mojibake_in_text(decoded_text)
    except Exception:
        return True  # デコードできない場合は文字化けとして扱う

def detect_mojibake_in_text(text: str) -> bool:
    """テキストの文字化けを検出する（強化版）"""
    try:
        # 実際の文字化けパターンのみに限定
        mojibake_patterns = [
            r'\?{5,}',  # 5個以上の連続する?記号
            r'[\uFFFD]{3,}',  # 3個以上の置換文字の連続
            # 明確な日本語文字化けパターンのみ
            r'繧\x92繧\x93',  # よくある文字化けパターン
            r'縺\x84縺\x86',  # 
            r'讒\x81讒\x82',  # 
            r'繝\x81繝\x82',  # 
            r'縺ゅ→縺',  # あと → 縺ゅ→縺
            r'迺ｾ遶',  # 環境 → 迺ｾ遶
            r'荳\?蟋',  # 会社 → 荳?蟋
            r'繧ｳ繝ｳ繝斐Η繝ｼ繧ｿ',  # コンピュータ
            r'\(cid:\d+\)',  # PDFのCIDエラー
        ]
        
        import re
        for pattern in mojibake_patterns:
            if re.search(pattern, text):
                return True
        
        # 文字の統計的分析
        if len(text) > 50:  # 十分な長さのテキストでのみ分析
            # 制御文字の割合チェック（条件を厳しく）
            control_chars = sum(1 for c in text if ord(c) < 32 and c not in '\n\r\t')
            control_ratio = control_chars / len(text)
            if control_ratio > 0.15:  # 15%以上が制御文字（条件を緩和）
                return True
            
            # 非ASCII文字の連続パターンチェック
            non_ascii_sequence_count = 0
            in_sequence = False
            for c in text:
                if ord(c) > 127:
                    if not in_sequence:
                        non_ascii_sequence_count += 1
                        in_sequence = True
                else:
                    in_sequence = False
            
            # 異常に多い非ASCII文字列の断片がある場合（条件を緩和）
            # 日本語テキストでは非ASCII文字が多いのは正常なので、条件を厳しくする
            if non_ascii_sequence_count > len(text) / 3:
                return True
        
        # タイトル行だけでなく、全体的な文字化けを検出
        lines = text.split('\n')
        mojibake_lines = 0
        
        for line in lines[:10]:  # 最初の10行をチェック
            if line.strip():
                # 行ごとに文字化けパターンをチェック
                line_has_mojibake = False
                for pattern in mojibake_patterns:
                    if re.search(pattern, line):
                        line_has_mojibake = True
                        break
                
                if line_has_mojibake:
                    mojibake_lines += 1
        
        # 複数行で文字化けが検出された場合（条件を厳しく）
        # 少なくとも3行以上で文字化けが検出された場合のみ文字化けと判定
        if mojibake_lines >= 3:
            return True
        
        return False
        
    except Exception as e:
        print(f"文字化け検出エラー: {str(e)}")
        return False

def detect_csv_delimiter(content_str: str) -> str:
    """CSVファイルの区切り文字を検出する"""
    try:
        # pandas で自動検出を試行
        sample_lines = content_str.split('\n')[:10]  # 最初の10行をサンプル
        sample = '\n'.join(sample_lines)
        
        # 一般的な区切り文字を試行
        delimiters = [',', ';', '\t', '|', ' ']
        delimiter_scores = {}
        
        for delimiter in delimiters:
            try:
                reader = csv.reader(sample.split('\n'), delimiter=delimiter)
                rows = list(reader)
                if len(rows) > 1:
                    # 各行の列数の一貫性をチェック
                    col_counts = [len(row) for row in rows if row]
                    if col_counts and len(set(col_counts)) <= 2:  # 最大2つの異なる列数を許可
                        delimiter_scores[delimiter] = max(col_counts)
            except Exception:
                continue
        
        if delimiter_scores:
            # 最も多くの列を持つ区切り文字を選択
            best_delimiter = max(delimiter_scores, key=delimiter_scores.get)
            print(f"検出された区切り文字: '{best_delimiter}' (列数: {delimiter_scores[best_delimiter]})")
            return best_delimiter
        
        # デフォルトはカンマ
        print("区切り文字の自動検出に失敗、カンマを使用")
        return ','
        
    except Exception as e:
        print(f"区切り文字検出エラー: {str(e)}")
        return ','

def get_google_sheets_service(access_token: str = None, service_account_file: str = None):
    """Google Sheets APIサービスオブジェクトを取得"""
    try:
        if not GOOGLE_SHEETS_AVAILABLE:
            logger.error("Google Sheets APIライブラリが利用できません")
            return None
            
        if service_account_file and os.path.exists(service_account_file):
            # サービスアカウントキーを使用
            logger.info("サービスアカウントを使用してGoogle Sheets APIに接続")
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file,
                scopes=['https://www.googleapis.com/auth/spreadsheets', 
                       'https://www.googleapis.com/auth/drive']
            )
            service = build('sheets', 'v4', credentials=credentials)
            return service
            
        elif access_token:
            # OAuth2アクセストークンを使用
            logger.info("OAuth2トークンを使用してGoogle Sheets APIに接続")
            credentials = Credentials(token=access_token)
            service = build('sheets', 'v4', credentials=credentials)
            return service
            
        else:
            logger.error("認証情報が提供されていません")
            return None
            
    except Exception as e:
        logger.error(f"Google Sheets APIサービス取得エラー: {str(e)}")
        return None

async def upload_csv_to_google_sheets(contents: bytes, filename: str, access_token: str = None, service_account_file: str = None) -> Optional[str]:
    """CSVファイルをGoogle Sheetsにアップロードし、スプレッドシートIDを返す"""
    try:
        logger.info(f"CSVファイルをGoogle Sheetsにアップロード開始: {filename}")
        
        if not GOOGLE_SHEETS_AVAILABLE:
            logger.error("Google Sheets APIライブラリが利用できません")
            return None
        
        # Google Sheets APIサービスを取得
        def create_sheets_service():
            return get_google_sheets_service(access_token, service_account_file)
        
        service = await asyncio.to_thread(create_sheets_service)
        if not service:
            return None
        
        # CSVデータを解析
        content_str = contents.decode('utf-8', errors='ignore')
        csv_reader = csv.reader(StringIO(content_str))
        csv_data = list(csv_reader)
        
        if not csv_data:
            logger.error("CSVファイルにデータがありません")
            return None
        
        # 新しいスプレッドシートを作成
        def create_spreadsheet():
            spreadsheet_body = {
                'properties': {
                    'title': f"{filename}_processed"
                }
            }
            spreadsheet = service.spreadsheets().create(body=spreadsheet_body).execute()
            return spreadsheet.get('spreadsheetId')
        
        spreadsheet_id = await asyncio.to_thread(create_spreadsheet)
        
        # データをスプレッドシートに書き込み
        def write_data():
            range_name = 'Sheet1!A1'
            value_input_option = 'RAW'
            body = {
                'values': csv_data
            }
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()
            return result
        
        await asyncio.to_thread(write_data)
        
        logger.info(f"Google Sheetsアップロード成功: {spreadsheet_id}")
        return spreadsheet_id
        
    except Exception as e:
        logger.error(f"Google Sheetsアップロード中のエラー: {str(e)}")
        return None

async def extract_text_from_google_sheets(spreadsheet_id: str, access_token: str = None, service_account_file: str = None) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Google Sheetsからテキストデータを抽出する"""
    try:
        logger.info(f"Google Sheetsからテキスト抽出開始: {spreadsheet_id}")
        
        if not GOOGLE_SHEETS_AVAILABLE:
            logger.error("Google Sheets APIライブラリが利用できません")
            return None, "Google Sheets APIライブラリが利用できません"
        
        # Google Sheets APIサービスを取得
        def create_sheets_service():
            return get_google_sheets_service(access_token, service_account_file)
        
        service = await asyncio.to_thread(create_sheets_service)
        if not service:
            return None, "Google Sheets APIサービスの取得に失敗しました"
        
        # スプレッドシートからデータを取得
        def get_sheet_data():
            range_name = 'Sheet1!A:ZZ'
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            return result.get('values', [])
        
        values = await asyncio.to_thread(get_sheet_data)
        
        if not values:
            logger.warning("Google Sheetsにデータが見つかりません")
            return None, "Google Sheetsにデータが見つかりませんでした"
        
        # データフレームを作成
        if len(values) > 1:
            # 最初の行をヘッダーとして使用
            headers_row = values[0]
            data_rows = values[1:]
            
            # データフレームを作成（行の長さを統一）
            max_cols = max(len(row) for row in data_rows) if data_rows else len(headers_row)
            
            # ヘッダーの長さを調整
            while len(headers_row) < max_cols:
                headers_row.append(f"Column_{len(headers_row) + 1}")
            
            # データ行の長さを調整
            normalized_data = []
            for row in data_rows:
                normalized_row = row + [''] * (max_cols - len(row))
                normalized_data.append(normalized_row)
            
            df = pd.DataFrame(normalized_data, columns=headers_row[:max_cols])
        else:
            # ヘッダーのみの場合
            df = pd.DataFrame(columns=values[0])
        
        # 空の行削除を無効化 - 生データ保持
        # df = df.dropna(how='all')
        
        # カラム名を文字列に変換
        df.columns = [ensure_string(col) for col in df.columns]
        
        logger.info(f"Google Sheetsデータ抽出完了: {len(df)} 行, {len(df.columns)} 列")
        
        # テキスト抽出
        extracted_text = f"=== Google Sheets データ ===\n\n"
        extracted_text += f"行数: {len(df)}, 列数: {len(df.columns)}\n\n"
        
        # 各列の情報を追加
        for col in df.columns:
            col_str = ensure_string(col)
            non_null_count = df[col].notna().sum()
            extracted_text += f"=== 列: {col_str} ===\n"
            extracted_text += f"データ数: {non_null_count}\n"
            
            # サンプルデータを追加
            if non_null_count > 0:
                sample_values = df[col].dropna().head(5).tolist()
                sample_text = ', '.join([ensure_string(val) for val in sample_values])
                extracted_text += f"サンプル: {sample_text}\n"
            extracted_text += "\n"
        
        return df, extracted_text
        
    except Exception as e:
        logger.error(f"Google Sheetsテキスト抽出中のエラー: {str(e)}")
        return None, f"Google Sheetsテキスト抽出中にエラーが発生しました: {str(e)}"

async def process_csv_with_gemini_ocr(contents: bytes, filename: str):
    """Gemini OCRを使用してCSVファイルを処理する（生ファイル直接送信版）"""
    try:
        from ..config import setup_gemini
        import tempfile
        import os
        
        logger.info(f"CSVファイル処理開始（Gemini生ファイル解析使用）: {filename}")
        
        # Geminiモデルをセットアップ
        model = setup_gemini()
        if not model:
            logger.error("Geminiモデルの初期化に失敗")
            return process_csv_file(contents, filename)
        
        # 生のCSVファイルを一時ファイルとして保存
        try:
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_file:
                tmp_file.write(contents)
                tmp_file_path = tmp_file.name
            
            # Geminiに生ファイルを直接送信
            logger.info("生のCSVファイルをGeminiに送信して文字化け復元を実行")
            
        except Exception as e:
            logger.error(f"一時ファイル作成エラー: {str(e)}")
            return process_csv_file(contents, filename)
        
        # 生ファイルをGeminiに送信するためのファイルオブジェクトを作成
        def upload_file_to_gemini():
            try:
                import google.generativeai as genai
                
                # ファイルをGeminiにアップロード
                uploaded_file = genai.upload_file(tmp_file_path)
                logger.info(f"Geminiにファイルアップロード完了: {uploaded_file.name}")
                return uploaded_file
            except Exception as e:
                logger.error(f"Geminiファイルアップロードエラー: {str(e)}")
                return None
        
        # 生ファイル用のプロンプト（文字化け対応特化）
        prompt = """
        このCSVファイルには文字化けしたデータが含まれている可能性があります。
        ファイルの内容を正確に読み取り、文字化けがあれば適切に復元してください。

        **重要な指示：**
        1. ファイルの正しいエンコーディングを自動判定して読み取ってください
        2. 文字化け文字が見つかった場合は、文脈から推測して正しい日本語に復元してください
        3. CSVの区切り文字（カンマ、セミコロン、タブ等）を正確に識別してください
        4. 表の構造（ヘッダー行、データ行）を正確に識別してください
        5. 数値データは文字化けしにくいので正確に抽出してください

        **出力形式：**
        以下の形式で復元されたCSVデータを出力してください：
        
        ヘッダー行: [カラム1, カラム2, カラム3, ...]
        データ行1: [値1, 値2, 値3, ...]
        データ行2: [値1, 値2, 値3, ...]
        ...

        **文字化け復元の例：**
        - 縺ゅ→縺 → あと
        - 迺ｾ遶 → 環境  
        - 荳?蟋 → 会社
        - 繧ｳ繝ｳ繝斐Η繝ｼ繧ｿ → コンピュータ

        復元できない文字化けは [文字化け] と明記してください。
        """
        
        def sync_gemini_call():
            try:
                # ファイルをGeminiにアップロード
                uploaded_file = upload_file_to_gemini()
                if not uploaded_file:
                    return ""
                
                # アップロードされたファイルを使ってコンテンツ生成
                response = model.generate_content([prompt, uploaded_file])
                
                # ファイル処理後にクリーンアップ
                try:
                    import google.generativeai as genai
                    genai.delete_file(uploaded_file.name)
                    logger.info("Geminiアップロードファイルを削除しました")
                except:
                    pass
                
                return response.text if response.text else ""
            except Exception as e:
                logger.error(f"Gemini生ファイル処理エラー: {str(e)}")
                return ""
            finally:
                # 一時ファイルを削除
                try:
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
                        logger.info("一時ファイルを削除しました")
                except:
                    pass
        
        extracted_text = await asyncio.to_thread(sync_gemini_call)
        
        if not extracted_text:
            logger.warning("Gemini生ファイル処理からテキストを抽出できませんでした")
            return process_csv_file(contents, filename)
        
        logger.info(f"Gemini生ファイル処理結果（最初の500文字）: {extracted_text[:500]}...")
        logger.info("文字化け検出によりGemini生ファイル処理を使用して処理しました")
        
        # 抽出したテキストからDataFrameを作成
        df = parse_gemini_csv_output(extracted_text, filename)
        
        if df is None or df.empty:
            logger.warning("Gemini OCR結果の解析に失敗")
            return process_csv_file(contents, filename)
        
        # セクション情報を作成
        sections = {}
        for col in df.columns:
            col_str = ensure_string(col)
            non_null_values = df[col].dropna()
            if len(non_null_values) > 0:
                sample_values = non_null_values.head(10).tolist()
                sample_text = ', '.join([ensure_string(val) for val in sample_values])
                if len(non_null_values) > 10:
                    sample_text += f" ... (他 {len(non_null_values) - 10} 項目)"
                sections[f"列: {col_str}"] = sample_text
        
        sections["ファイル情報"] = f"行数: {len(df)}, 列数: {len(df.columns)}, ファイル名: {filename} (Gemini OCR経由)"
        
        # 結果用のデータフレームを作成
        result_data = []
        for index, row in df.iterrows():
            row_content = []
            for col in df.columns:
                value = row[col]
                if pd.notna(value):
                    row_content.append(f"{ensure_string(col)}: {ensure_string(value)}")
            
            if row_content:
                result_data.append({
                    'section': f"行 {index + 1}",
                    'content': ' | '.join(row_content),
                    'source': 'CSV (Gemini OCR)',
                    'file': filename,
                    'url': None
                })
        
        result_df = pd.DataFrame(result_data)
        for col in result_df.columns:
            result_df[col] = result_df[col].apply(ensure_string)
        
        # 完全なテキスト情報
        full_text = f"=== ファイル: {filename} (Gemini OCR処理) ===\n\n"
        full_text += f"=== ファイル情報 ===\n行数: {len(df)}, 列数: {len(df.columns)}\n\n"
        full_text += f"=== 抽出されたテキスト ===\n{extracted_text}\n\n"
        
        logger.info(f"CSV処理完了（Gemini OCR使用）: {len(result_df)} レコード")
        return result_df, sections, full_text
        
    except Exception as e:
        logger.error(f"Gemini OCR CSV処理エラー: {str(e)}")
        logger.info("従来の処理にフォールバック")
        return process_csv_file(contents, filename)

def parse_gemini_csv_output(gemini_text: str, filename: str) -> Optional[pd.DataFrame]:
    """Geminiの出力からDataFrameを作成"""
    try:
        lines = gemini_text.strip().split('\n')
        headers = None
        data_rows = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('ヘッダー行:') or line.startswith('Header:'):
                # ヘッダー行を抽出
                header_part = line.split(':', 1)[1].strip()
                # [カラム1, カラム2, ...] の形式から抽出
                if header_part.startswith('[') and header_part.endswith(']'):
                    header_part = header_part[1:-1]
                headers = [col.strip().strip('"').strip("'") for col in header_part.split(',')]
                
            elif line.startswith('データ行') or line.startswith('Data:'):
                # データ行を抽出
                data_part = line.split(':', 1)[1].strip()
                if data_part.startswith('[') and data_part.endswith(']'):
                    data_part = data_part[1:-1]
                row_data = [val.strip().strip('"').strip("'") for val in data_part.split(',')]
                data_rows.append(row_data)
        
        if headers and data_rows:
            # データ行の長さを統一
            max_cols = len(headers)
            normalized_rows = []
            for row in data_rows:
                normalized_row = row + [''] * (max_cols - len(row))
                normalized_rows.append(normalized_row[:max_cols])
            
            df = pd.DataFrame(normalized_rows, columns=headers)
            return df
        else:
            # フォールバック: 単純にCSVとして解析
            csv_reader = csv.reader(StringIO(gemini_text))
            rows = list(csv_reader)
            if len(rows) > 1:
                df = pd.DataFrame(rows[1:], columns=rows[0])
                return df
                
        return None
        
    except Exception as e:
        logger.error(f"Gemini出力解析エラー: {str(e)}")
        return None

async def process_csv_file_with_sheets_api(contents: bytes, filename: str, access_token: str = None, service_account_file: str = None):
    """Google Sheets APIを使用してCSVファイルを処理する"""
    try:
        logger.info(f"CSVファイル処理開始（Google Sheets API使用）: {filename}")
        
        if not access_token and not service_account_file:
            # 認証情報がない場合は従来の方法にフォールバック
            logger.warning("Google Sheets認証情報が提供されていません。従来の処理にフォールバック")
            return process_csv_file(contents, filename)
        
        # OAuth2トークンの優先度を上げる（組織ポリシー対応）
        if access_token:
            logger.info("OAuth2アクセストークンを使用してGoogle Sheets APIに接続")
        elif service_account_file:
            logger.info("サービスアカウントファイルを使用してGoogle Sheets APIに接続")
        
        # 環境変数からサービスアカウントファイルパスを取得
        if not service_account_file:
            service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
        
        # CSVをGoogle Sheetsにアップロード
        spreadsheet_id = await upload_csv_to_google_sheets(contents, filename, access_token, service_account_file)
        
        if not spreadsheet_id:
            logger.warning("Google Sheetsアップロードに失敗。従来の処理にフォールバック")
            return process_csv_file(contents, filename)
        
        # Google Sheetsからテキストを抽出
        df_from_sheets, extracted_text = await extract_text_from_google_sheets(spreadsheet_id, access_token, service_account_file)
        
        if df_from_sheets is None:
            logger.warning("Google Sheetsからのデータ抽出に失敗。従来の処理にフォールバック")
            return process_csv_file(contents, filename)
        
        # セクション情報を作成
        sections = {}
        
        # 各列をセクションとして作成
        for col in df_from_sheets.columns:
            col_str = ensure_string(col)
            non_null_values = df_from_sheets[col].dropna()
            if len(non_null_values) > 0:
                # 列の値をサンプリング（最初の10個まで）
                sample_values = non_null_values.head(10).tolist()
                sample_text = ', '.join([ensure_string(val) for val in sample_values])
                if len(non_null_values) > 10:
                    sample_text += f" ... (他 {len(non_null_values) - 10} 項目)"
                sections[f"列: {col_str}"] = sample_text
        
        # 統計情報をセクションに追加
        sections["ファイル情報"] = f"行数: {len(df_from_sheets)}, 列数: {len(df_from_sheets.columns)}, ファイル名: {filename} (Google Sheets経由)"
        
        # 結果用のデータフレームを作成
        result_data = []
        
        # 各行をレコードとして追加
        for index, row in df_from_sheets.iterrows():
            row_content = []
            for col in df_from_sheets.columns:
                value = row[col]
                if pd.notna(value):
                    row_content.append(f"{ensure_string(col)}: {ensure_string(value)}")
            
            if row_content:
                result_data.append({
                    'section': f"行 {index + 1}",
                    'content': ' | '.join(row_content),
                    'source': 'CSV (Google Sheets)',
                    'file': filename,
                    'url': None
                })
        
        # データフレームが空の場合の処理
        if not result_data:
            result_data.append({
                'section': "データなし",
                'content': "CSVファイルに有効なデータが見つかりませんでした",
                'source': 'CSV (Google Sheets)',
                'file': filename,
                'url': None
            })
        
        result_df = pd.DataFrame(result_data)
        
        # すべての列の値を文字列に変換
        for col in result_df.columns:
            result_df[col] = result_df[col].apply(ensure_string)
        
        logger.info(f"CSV処理完了（Google Sheets API使用）: {len(result_df)} レコード")
        return result_df, sections, extracted_text
        
    except Exception as e:
        logger.error(f"Google Sheets API使用のCSV処理エラー: {str(e)}")
        logger.info("従来の処理にフォールバック")
        return process_csv_file(contents, filename)

def process_csv_file(contents: bytes, filename: str):
    """従来のCSVファイル処理（フォールバック用）"""
    try:
        logger.info(f"CSVファイル処理開始: {filename}, サイズ: {len(contents)}バイト")
        
        # ライブラリ不足の警告（ただし処理は継続）
        if not CHARDET_AVAILABLE:
            logger.warning("chardetライブラリが不足しています。エンコーディング検出精度が低下する可能性があります。")
        
        # エンコーディングを検出
        logger.info("エンコーディング検出開始")
        encoding = detect_csv_encoding(contents)
        logger.info(f"検出されたエンコーディング: {encoding}")
        
        # バイトデータを文字列に変換
        try:
            content_str = contents.decode(encoding)
            logger.info(f"ファイルデコード成功: {len(content_str)}文字")
        except UnicodeDecodeError as e:
            logger.error(f"エンコーディングエラー ({encoding}): {str(e)}")
            # フォールバック: エラーを無視して読み込み
            content_str = contents.decode(encoding, errors='ignore')
            logger.info(f"フォールバックデコード完了: {len(content_str)}文字")
        
        # 区切り文字を検出
        logger.info("区切り文字検出開始")
        delimiter = detect_csv_delimiter(content_str)
        logger.info(f"検出された区切り文字: '{delimiter}'")
        
        # CSVを読み込み
        try:
            logger.info("pandas CSVリーダーでの読み込み開始")
            # pandasでCSVを読み込み
            csv_file = StringIO(content_str)
            df = pd.read_csv(csv_file, delimiter=delimiter, encoding=None)
            logger.info(f"pandas読み込み成功: 初期行数={len(df)}, 列数={len(df.columns)}")
            
            # 空の行削除を無効化 - 生データ保持
            # df = df.dropna(how='all')
            logger.info(f"生データ保持: {len(df)} 行")
            
            # カラム名を文字列に変換
            df.columns = [ensure_string(col) for col in df.columns]
            
            # ガイドの指針に基づいてUnnamedカラム問題を修正
            handler = UnnamedColumnHandler()
            df, modifications = handler.fix_dataframe(df, filename)
            
            if modifications:
                logger.info(f"Unnamedカラム修正: {', '.join(modifications)}")
            
            logger.info(f"CSV読み込み完了: {len(df)} 行, {len(df.columns)} 列")
            logger.info(f"修正後カラム名: {list(df.columns)}")
            
        except Exception as pandas_error:
            logger.error(f"pandas読み込みエラー: {str(pandas_error)}")
            # フォールバック: 標準ライブラリのcsvモジュールを使用
            try:
                logger.info("標準CSVモジュールでの読み込み開始")
                csv_file = StringIO(content_str)
                reader = csv.DictReader(csv_file, delimiter=delimiter)
                rows = list(reader)
                logger.info(f"CSV辞書リーダー読み込み: {len(rows)} 行")
                
                if rows:
                    df = pd.DataFrame(rows)
                    # 空の行削除を無効化 - 生データ保持
                    # df = df.dropna(how='all')
                    
                    # カラム名を文字列に変換
                    df.columns = [ensure_string(col) for col in df.columns]
                    
                    # ガイドの指針に基づいてUnnamedカラム問題を修正
                    handler = UnnamedColumnHandler()
                    df, modifications = handler.fix_dataframe(df, filename)
                    
                    if modifications:
                        logger.info(f"Unnamedカラム修正（csv）: {', '.join(modifications)}")
                    
                    logger.info(f"csvモジュールでの読み込み完了: {len(df)} 行")
                else:
                    logger.error("CSVファイルにデータが含まれていません")
                    raise ValueError("CSVファイルにデータが含まれていません")
                    
            except Exception as csv_error:
                logger.error(f"csvモジュール読み込みエラー: {str(csv_error)}")
                raise ValueError(f"CSVファイルの読み込みに失敗しました: {str(csv_error)}")
        
        # データの検証
        if df.empty:
            logger.error("CSVデータフレームが空です")
            raise ValueError("CSVファイルにデータが含まれていません")
        
        # セクション情報を作成
        sections = {}
        
        # 各列をセクションとして作成
        for col in df.columns:
            col_str = ensure_string(col)
            non_null_values = df[col].dropna()
            if len(non_null_values) > 0:
                # 列の値をサンプリング（最初の10個まで）
                sample_values = non_null_values.head(10).tolist()
                sample_text = ', '.join([ensure_string(val) for val in sample_values])
                if len(non_null_values) > 10:
                    sample_text += f" ... (他 {len(non_null_values) - 10} 項目)"
                sections[f"列: {col_str}"] = sample_text
        
        # 統計情報をセクションに追加
        sections["ファイル情報"] = f"行数: {len(df)}, 列数: {len(df.columns)}, ファイル名: {filename}"
        
        # テキスト抽出
        extracted_text = f"=== ファイル: {filename} ===\n\n"
        extracted_text += f"=== ファイル情報 ===\n行数: {len(df)}, 列数: {len(df.columns)}\n\n"
        
        # 各列の情報を追加
        for col in df.columns:
            col_str = ensure_string(col)
            non_null_count = df[col].notna().sum()
            extracted_text += f"=== 列: {col_str} ===\n"
            extracted_text += f"データ数: {non_null_count}\n"
            
            # サンプルデータを追加
            if non_null_count > 0:
                sample_values = df[col].dropna().head(5).tolist()
                sample_text = ', '.join([ensure_string(val) for val in sample_values])
                extracted_text += f"サンプル: {sample_text}\n"
            extracted_text += "\n"
        
        # 結果用のデータフレームを作成
        result_data = []
        
        # 各行をレコードとして追加
        for index, row in df.iterrows():
            row_content = []
            for col in df.columns:
                value = row[col]
                if pd.notna(value):
                    row_content.append(f"{ensure_string(col)}: {ensure_string(value)}")
            
            if row_content:
                result_data.append({
                    'section': f"行 {index + 1}",
                    'content': ' | '.join(row_content),
                    'source': 'CSV',
                    'file': filename,
                    'url': None
                })
        
        # データフレームが空の場合の処理
        if not result_data:
            result_data.append({
                'section': "データなし",
                'content': "CSVファイルに有効なデータが見つかりませんでした",
                'source': 'CSV',
                'file': filename,
                'url': None
            })
        
        result_df = pd.DataFrame(result_data)
        
        # すべての列の値を文字列に変換
        for col in result_df.columns:
            result_df[col] = result_df[col].apply(ensure_string)
        
        logger.info(f"CSV処理完了: {len(result_df)} レコード, sections: {len(sections)}, extracted_text: {len(extracted_text)}文字")
        return result_df, sections, extracted_text
        
    except Exception as e:
        logger.error(f"CSVファイル処理エラー: {str(e)}")
        logger.error(traceback.format_exc())
        
        # エラーが発生しても最低限のデータを返す
        error_message = f"CSVファイル処理中にエラーが発生しました: {str(e)}"
        empty_df = pd.DataFrame({
            'section': ["エラー"],
            'content': [error_message],
            'source': ['CSV'],
            'file': [filename],
            'url': [None]
        })
        empty_sections = {"エラー": error_message}
        error_text = f"=== ファイル: {filename} ===\n\n=== エラー ===\n{error_message}\n\n"
        
        return empty_df, empty_sections, error_text

def is_csv_file(filename: str) -> bool:
    """ファイルがCSV形式かどうかを判定する"""
    return filename.lower().endswith('.csv')

def check_csv_dependencies() -> dict:
    """CSV処理に必要な依存関係をチェックする"""
    return {
        'chardet': CHARDET_AVAILABLE,
        'pandas': True,  # 基本的に利用可能
        'csv': True,     # 標準ライブラリ
    }