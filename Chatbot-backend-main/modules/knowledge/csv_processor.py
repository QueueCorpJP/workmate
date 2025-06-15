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
    """CSVファイルの文字エンコーディングを検出する"""
    try:
        # chardetが利用可能な場合は使用
        if CHARDET_AVAILABLE:
            result = chardet.detect(content)
            encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0)
            
            print(f"検出されたエンコーディング: {encoding} (信頼度: {confidence:.2f})")
            
            # 信頼度が低い場合は一般的なエンコーディングを試行
            if confidence < 0.7:
                common_encodings = ['utf-8', 'shift_jis', 'cp932', 'euc-jp', 'iso-2022-jp']
                for enc in common_encodings:
                    try:
                        content.decode(enc)
                        print(f"フォールバックエンコーディング使用: {enc}")
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
                    content.decode(enc)
                    print(f"検出されたエンコーディング: {enc}")
                    return enc
                except UnicodeDecodeError:
                    continue
            
            # どれも成功しなかった場合はutf-8をデフォルトとして使用
            print("エンコーディング検出に失敗、utf-8を使用")
            return 'utf-8'
        
    except Exception as e:
        print(f"エンコーディング検出エラー: {str(e)}")
        return 'utf-8'

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
        
        # 空の行を削除
        df = df.dropna(how='all')
        
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
    """Gemini OCRを使用してCSVファイルを処理する"""
    try:
        from ..config import setup_gemini
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        logger.info(f"CSVファイル処理開始（Gemini OCR使用）: {filename}")
        
        # Geminiモデルをセットアップ
        model = setup_gemini()
        if not model:
            logger.error("Geminiモデルの初期化に失敗")
            return process_csv_file(contents, filename)
        
        # CSVコンテンツをテキストとして読み込み
        try:
            # エンコーディングを検出
            encoding = detect_csv_encoding(contents)
            content_str = contents.decode(encoding, errors='ignore')
        except Exception as e:
            logger.error(f"CSV読み込みエラー: {str(e)}")
            return process_csv_file(contents, filename)
        
        # CSVテキストを画像に変換
        def create_csv_image(csv_text: str) -> Image.Image:
            lines = csv_text.split('\n')[:50]  # 最初の50行まで
            
            # 画像サイズを計算
            font_size = 12
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            max_width = 0
            line_height = font_size + 4
            
            # 最大幅を計算
            for line in lines:
                if font:
                    bbox = font.getbbox(line)
                    width = bbox[2] - bbox[0]
                else:
                    width = len(line) * 8  # 概算
                max_width = max(max_width, width)
            
            # 画像を作成
            img_width = min(max_width + 40, 1200)  # 最大幅制限
            img_height = len(lines) * line_height + 40
            
            image = Image.new('RGB', (img_width, img_height), 'white')
            draw = ImageDraw.Draw(image)
            
            # テキストを描画
            y = 20
            for line in lines:
                if line.strip():  # 空行をスキップ
                    draw.text((20, y), line, fill='black', font=font)
                y += line_height
            
            return image
        
        # CSVを画像に変換
        csv_image = create_csv_image(content_str)
        
        # Gemini OCRでテキスト抽出
        prompt = """
        このCSVデータの内容を正確に抽出してください。以下の形式で出力してください：

        1. 表の構造を理解して、カラム名とデータを識別
        2. 各行のデータを正確に抽出
        3. 数値データと文字列データを区別
        4. 空のセルは空白として扱う

        出力形式：
        ヘッダー行: [カラム1, カラム2, カラム3, ...]
        データ行1: [値1, 値2, 値3, ...]
        データ行2: [値1, 値2, 値3, ...]
        ...

        特に日本語の文字化けに注意して、正確に読み取ってください。
        """
        
        def sync_gemini_call():
            try:
                response = model.generate_content([prompt, csv_image])
                return response.text if response.text else ""
            except Exception as e:
                logger.error(f"Gemini OCR呼び出しエラー: {str(e)}")
                return ""
        
        extracted_text = await asyncio.to_thread(sync_gemini_call)
        
        if not extracted_text:
            logger.warning("Gemini OCRからテキストを抽出できませんでした")
            return process_csv_file(contents, filename)
        
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
            csv_reader = csv.reader(io.StringIO(gemini_text))
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
        print(f"CSVファイル処理開始: {filename}")
        
        # ライブラリ不足の警告（ただし処理は継続）
        if not CHARDET_AVAILABLE:
            print("警告: chardetライブラリが不足しています。エンコーディング検出精度が低下する可能性があります。")
        
        # エンコーディングを検出
        encoding = detect_csv_encoding(contents)
        
        # バイトデータを文字列に変換
        try:
            content_str = contents.decode(encoding)
        except UnicodeDecodeError as e:
            print(f"エンコーディングエラー ({encoding}): {str(e)}")
            # フォールバック: エラーを無視して読み込み
            content_str = contents.decode(encoding, errors='ignore')
        
        # 区切り文字を検出
        delimiter = detect_csv_delimiter(content_str)
        
        # CSVを読み込み
        try:
            # pandasでCSVを読み込み
            csv_file = StringIO(content_str)
            df = pd.read_csv(csv_file, delimiter=delimiter, encoding=None)
            
            # 空の行を削除
            df = df.dropna(how='all')
            
            # カラム名を文字列に変換
            df.columns = [ensure_string(col) for col in df.columns]
            
            print(f"CSV読み込み完了: {len(df)} 行, {len(df.columns)} 列")
            print(f"カラム名: {list(df.columns)}")
            
        except Exception as pandas_error:
            print(f"pandas読み込みエラー: {str(pandas_error)}")
            # フォールバック: 標準ライブラリのcsvモジュールを使用
            try:
                csv_file = StringIO(content_str)
                reader = csv.DictReader(csv_file, delimiter=delimiter)
                rows = list(reader)
                
                if rows:
                    df = pd.DataFrame(rows)
                    # 空の行を削除
                    df = df.dropna(how='all')
                    print(f"csvモジュールでの読み込み完了: {len(df)} 行")
                else:
                    raise ValueError("CSVファイルにデータが含まれていません")
                    
            except Exception as csv_error:
                print(f"csvモジュール読み込みエラー: {str(csv_error)}")
                raise ValueError(f"CSVファイルの読み込みに失敗しました: {str(csv_error)}")
        
        # データの検証
        if df.empty:
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
        
        print(f"CSV処理完了: {len(result_df)} レコード")
        return result_df, sections, extracted_text
        
    except Exception as e:
        print(f"CSVファイル処理エラー: {str(e)}")
        print(traceback.format_exc())
        
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