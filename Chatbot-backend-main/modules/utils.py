import requests
import re
from bs4 import BeautifulSoup
from io import BytesIO
import pandas as pd
import time
from dotenv import load_dotenv
import os
from playwright.async_api import async_playwright
import fitz
import tempfile
import asyncio
from .database import ensure_string

load_dotenv()

def transcribe_youtube_video(url: str) -> str:
    """YouTube動画の音声を文字起こしする
    
    Args:
        url: YouTube動画のURL
        
    Returns:
        文字起こしされたテキストまたは対応状況メッセージ
    """
    return f"🎥 YouTube動画の処理は現在対応していません\n• 動画の音声文字起こし機能は開発中です\n• 代わりに動画の説明文やタイトルをテキストで提供してください\n• または、文字起こしされたテキストファイルをアップロードしてください\n• URL: {url}"

def _get_user_friendly_pdf_error(error: Exception, url: str) -> str:
    """PDFエラーをユーザーフレンドリーなメッセージに変換"""
    error_str = str(error).lower()
    
    # HTTP ステータスコードエラー
    if hasattr(error, 'response') and error.response is not None:
        status_code = error.response.status_code
        if status_code == 404:
            return f"❌ このPDFファイルは見つかりません（404エラー）\n• URLが正しいか確認してください\n• ファイルが削除されている可能性があります\n• URL: {url}"
        elif status_code == 403:
            return f"❌ このPDFファイルへのアクセスが拒否されました（403エラー）\n• ファイルがアクセス制限されています\n• ログインが必要な場合があります\n• URL: {url}"
    
    # PDFファイル固有のエラー
    if 'pdf' in error_str and ('corrupt' in error_str or 'damaged' in error_str):
        return f"📄 PDFファイルが破損しています\n• ファイルが正しくダウンロードされていない可能性があります\n• 元のファイルが破損している可能性があります\n• URL: {url}"
    
    if 'password' in error_str or 'encrypted' in error_str:
        return f"🔒 このPDFファイルはパスワード保護されています\n• パスワードが必要なPDFファイルは処理できません\n• パスワードを解除してからアップロードしてください\n• URL: {url}"
    
    if 'timeout' in error_str:
        return f"⏰ PDFファイルのダウンロードがタイムアウトしました\n• ファイルサイズが大きすぎる可能性があります\n• ネットワーク接続を確認してください\n• URL: {url}"
    
    # ファイル形式エラー
    if 'not a pdf' in error_str or 'invalid pdf' in error_str:
        return f"📄 このファイルは有効なPDFファイルではありません\n• URLが正しいPDFファイルを指しているか確認してください\n• ファイル拡張子が.pdfでも実際は別の形式の可能性があります\n• URL: {url}"
    
    return f"❌ PDFファイル処理中にエラーが発生しました\n• 詳細: {str(error)}\n• ファイルが正しいPDFか確認してください\n• 別のPDFファイルで試してみてください\n• URL: {url}"

async def extract_text_from_pdf(url: str) -> str:
    """URLからPDFファイルを取得し、テキストを抽出する
    
    Args:
        url: PDFファイルのURL
        
    Returns:
        抽出されたテキストまたはユーザーフレンドリーなエラーメッセージ
    """
    try:
        # URLからPDFファイルを取得
        response = requests.get(url, timeout=60, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # レスポンスが空でないか確認
        if not response.content:
            return f"❌ PDFファイルのダウンロードに失敗しました\n• ファイルが空です\n• URLを確認してください\n• URL: {url}"
        
        # Content-Typeの確認
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type and len(response.content) < 1000:
            return f"❌ このURLは有効なPDFファイルを指していません\n• Content-Type: {content_type}\n• PDFファイルの直接リンクを使用してください\n• URL: {url}"
        
        # PyMuPDFを使用してPDFからテキストを抽出
        pdf_document = fitz.open(stream=response.content, filetype="pdf")
        
        # PDFが空でないか確認
        if len(pdf_document) == 0:
            pdf_document.close()
            return f"❌ このPDFファイルにはページがありません\n• 空のPDFファイルです\n• URL: {url}"
        
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            page_text = page.get_text()
            text += page_text
        
        pdf_document.close()
        
        # 抽出されたテキストが空でないか確認
        if not text or len(text.strip()) < 10:
            return f"❌ PDFからテキストを抽出できませんでした\n• 画像のみのPDFファイルの可能性があります\n• スキャンされたPDFは現在対応していません\n• URL: {url}"
        
        return text
    except Exception as e:
        error_message = _get_user_friendly_pdf_error(e, url)
        print(f"PDF抽出エラー: {e}")
        return error_message

def extract_text_from_pdf_bytes(content: bytes) -> str:
    """PDFファイルのバイト内容からテキストを抽出する
    
    Args:
        content: PDFファイルのバイト内容
        
    Returns:
        抽出されたテキスト
    """
    try:
        # PyMuPDFを使用してPDFからテキストを抽出
        pdf_document = fitz.open(stream=content, filetype="pdf")
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text += page.get_text()
        pdf_document.close()
        return text
    except Exception as e:
        print(f"PDF抽出エラー: {e}")
        return ""

def _get_user_friendly_url_error(error: Exception, url: str) -> str:
    """URLエラーをユーザーフレンドリーなメッセージに変換"""
    import requests
    
    error_str = str(error).lower()
    
    # HTTP ステータスコードエラー
    if hasattr(error, 'response') and error.response is not None:
        status_code = error.response.status_code
        if status_code == 404:
            return f"❌ このURLは存在しません（404エラー）\n• URLが正しいか確認してください\n• ページが削除されている可能性があります\n• URL: {url}"
        elif status_code == 403:
            return f"❌ このURLへのアクセスが拒否されました（403エラー）\n• サイトがアクセス制限を設けています\n• ログインが必要なページの可能性があります\n• URL: {url}"
        elif status_code == 401:
            return f"❌ このURLは認証が必要です（401エラー）\n• ログインが必要なページです\n• 認証情報を確認してください\n• URL: {url}"
        elif status_code == 500:
            return f"❌ サーバーでエラーが発生しています（500エラー）\n• サイト側の問題です\n• 時間をおいて再試行してください\n• URL: {url}"
        else:
            return f"❌ HTTPエラーが発生しました（{status_code}エラー）\n• サーバーから予期しない応答が返されました\n• URL: {url}"
    
    # タイムアウトエラー
    if 'timeout' in error_str or 'timed out' in error_str:
        return f"⏰ URLの読み込みがタイムアウトしました\n• サイトの応答が遅すぎます\n• ネットワーク接続を確認してください\n• 大きなファイルの場合は時間がかかることがあります\n• URL: {url}"
    
    # SSL証明書エラー
    if 'ssl' in error_str or 'certificate' in error_str:
        return f"🔒 SSL証明書エラーが発生しました\n• サイトのセキュリティ証明書に問題があります\n• HTTPSではなくHTTPでアクセスできるか確認してください\n• URL: {url}"
    
    # 接続エラー
    if 'connection' in error_str or 'resolve' in error_str or 'network' in error_str:
        return f"🌐 ネットワーク接続エラーが発生しました\n• インターネット接続を確認してください\n• URLが正しいか確認してください\n• サイトが一時的にダウンしている可能性があります\n• URL: {url}"
    
    # 文字エンコーディングエラー
    if 'encoding' in error_str or 'decode' in error_str:
        return f"📝 文字エンコーディングエラーが発生しました\n• ページの文字コードに問題があります\n• 一部の文字が正しく読み取れない可能性があります\n• URL: {url}"
    
    # その他の一般的なエラー
    return f"❌ URL処理中にエラーが発生しました\n• 詳細: {str(error)}\n• URLが正しいか確認してください\n• 別のURLで試してみてください\n• URL: {url}"

async def extract_text_from_html(url: str) -> str:
    """URLからHTMLコンテンツを取得し、テキストを抽出する
    
    Args:
        url: 抽出対象のURL
        
    Returns:
        抽出されたテキストまたはユーザーフレンドリーなエラーメッセージ
    """
    try:
        # URLからHTMLコンテンツを取得
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # レスポンスが空でないか確認
        if not response.content:
            return f"❌ このURLには内容がありません\n• ページが空白です\n• 別のURLで試してみてください\n• URL: {url}"
        
        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # スクリプトとスタイルタグを削除
        for script in soup(["script", "style"]):
            script.decompose()
        
        # テキストを抽出
        text = soup.get_text()
        
        # 改行や空白を整理
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # 抽出されたテキストが空でないか確認
        if not text or len(text.strip()) < 10:
            return f"❌ このURLから有効なテキストを抽出できませんでした\n• ページがJavaScriptで動的に生成されている可能性があります\n• 画像やメディアファイルのみのページの可能性があります\n• URL: {url}"
        
        return text
    except Exception as e:
        error_message = _get_user_friendly_url_error(e, url)
        print(f"HTML抽出エラー: {e}")
        return error_message

def safe_print(text):
    """安全な出力関数"""
    try:
        print(text)
    except Exception as e:
        print(f"出力エラー: {str(e)}")

def safe_safe_print(text):
    """より安全な出力関数"""
    try:
        print(text)
    except Exception:
        pass  # エラーが発生しても無視

# プロキシ設定を環境変数から取得
WEBSHAREPROXY_USERNAME = os.getenv("WEBSHAREPROXY_USERNAME")
WEBSHAREPROXY_PASSWORD = os.getenv("WEBSHAREPROXY_PASSWORD")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
HTTP_PROXY = os.getenv("HTTP_PROXY")
HTTPS_PROXY = os.getenv("HTTPS_PROXY")

# requestsのプロキシ設定
def get_proxies():
    """環境に応じたプロキシ設定を取得"""
    proxies = {}
    if HTTP_PROXY:
        proxies['http'] = HTTP_PROXY
    if HTTPS_PROXY:
        proxies['https'] = HTTPS_PROXY
    return proxies if proxies else None

async def _check_and_throttle_url_request(url: str):
    """URLリクエスト前のサイズ推定とスロットリング"""
    try:
        # 大きなデータが予想されるURLパターンをチェック
        large_data_indicators = [
            'drive.google.com',  # Google Drive
            'dropbox.com',       # Dropbox
            'onedrive.live.com', # OneDrive
            'mega.nz',           # Mega
            'archive.org',       # Internet Archive
            'youtube.com',       # YouTube (動画)
            'vimeo.com',         # Vimeo
            'slideshare.net',    # SlideShare
            'scribd.com',        # Scribd
            '.pdf',              # PDF files
            'docs.google.com',   # Google Docs
            'sheets.google.com', # Google Sheets
        ]
        
        url_lower = url.lower()
        
        # 大きなデータの可能性があるURLの場合は事前に遅延
        for indicator in large_data_indicators:
            if indicator in url_lower:
                delay_seconds = 2.0
                print(f"大きなデータの可能性があるURL検出: {indicator} - {delay_seconds}秒待機")
                await asyncio.sleep(delay_seconds)
                break
        
        # 特に大きなファイルが予想される場合の追加遅延
        high_risk_indicators = [
            'drive.google.com/file/d/',  # Google Drive直接ファイル
            'dropbox.com/s/',            # Dropbox共有ファイル
            '.pdf',                      # PDF
            'archive.org/download/',     # Archive.orgダウンロード
        ]
        
        for indicator in high_risk_indicators:
            if indicator in url_lower:
                additional_delay = 3.0
                print(f"高リスクURL検出: {indicator} - 追加{additional_delay}秒待機")
                await asyncio.sleep(additional_delay)
                break
                
    except Exception as e:
        print(f"URL事前チェックエラー: {str(e)}")
        # エラーが発生しても処理は続行

# Function to extract video ID from a full YouTube URL
def get_video_id(youtube_url):
    """YouTube URLから動画IDを抽出する（改良版）"""
    import re
    
    # より包括的なパターンで動画IDを抽出
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',  # 標準的なパターン
        r'youtu\.be\/([0-9A-Za-z_-]{11})',  # 短縮URL
        r'embed\/([0-9A-Za-z_-]{11})',      # 埋め込みURL
        r'watch\?v=([0-9A-Za-z_-]{11})'     # 標準的なwatch URL
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            video_id = match.group(1)
            print(f"パターン '{pattern}' で動画ID抽出: {video_id}")
            return video_id
    
    print(f"動画ID抽出失敗: {youtube_url}")
    return None

def _process_video_file(contents, filename):
    """動画ファイルを処理してデータフレーム、セクション、テキストを返す"""
    try:
        video_file = BytesIO(contents)
        
        transcription = transcribe_video_file(video_file)
        # Ensure transcription is a string
        transcription_text = str(transcription) if transcription is not None else ""
        
        sections = {"トランスクリプション": transcription_text}
        extracted_text = f"=== ファイル: {filename} ===\n\n=== トランスクリプション ===\n{transcription_text}\n\n"

        result_df = pd.DataFrame({
            'section': ["トランスクリプション"],
            'content': [transcription_text],
            'source': ['Video'],
            'file': [filename],
            'url': [None]
        })
        
        return result_df, sections, extracted_text
    except Exception as e:
        print(f"Videoファイル処理エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise

# Headers for AssemblyAI API
HEADERS = {
    "authorization": ASSEMBLYAI_API_KEY,
    "content-type": "application/json"
}

def upload_to_assemblyai(video_file: BytesIO) -> str:
    """
    Uploads video file to AssemblyAI and returns the upload URL.
    """
    upload_url = "https://api.assemblyai.com/v2/upload"
    proxies = get_proxies()

    response = requests.post(
        upload_url,
        headers={"authorization": ASSEMBLYAI_API_KEY},
        data=video_file,
        proxies=proxies,
        timeout=300
    )

    response.raise_for_status()
    return response.json()['upload_url']

def start_transcription(upload_url: str) -> str:
    """
    Starts the transcription job and returns the transcript ID.
    """
    transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
    json_data = {
        "audio_url": upload_url
    }
    proxies = get_proxies()

    response = requests.post(transcript_endpoint, json=json_data, headers=HEADERS, proxies=proxies, timeout=60)
    response.raise_for_status()
    return response.json()["id"]

def poll_transcription(transcript_id: str) -> dict:
    """
    Polls the transcript endpoint until transcription is completed.
    """
    polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    proxies = get_proxies()

    while True:
        response = requests.get(polling_endpoint, headers=HEADERS, proxies=proxies, timeout=60)
        response.raise_for_status()
        data = response.json()

        if data["status"] == "completed":
            return data
        elif data["status"] == "error":
            raise RuntimeError(f"Transcription failed: {data['error']}")

        time.sleep(3)  # Wait a few seconds before checking again

def transcribe_video_file(video_file: BytesIO) -> str:
    """
    Main function to handle the full transcription pipeline.
    """
    print("Uploading video...")
    upload_url = upload_to_assemblyai(video_file)

    print("Starting transcription...")
    transcript_id = start_transcription(upload_url)

    print("Waiting for transcription to complete...")
    transcript_data = poll_transcription(transcript_id)

    # Ensure we return a string, not None or an int
    text = transcript_data.get("text", "")
    return ensure_string(text)

def create_default_usage_limits(user_id: str, user_email: str, user_role: str = None) -> dict:
    """
    ユーザーのデフォルト利用制限を生成する共通関数
    
    Args:
        user_id: ユーザーID
        user_email: ユーザーのメールアドレス
        user_role: ユーザーのロール（オプション）
    
    Returns:
        デフォルトの利用制限設定
    """
    # 特別管理者の判定
    is_unlimited = user_email == "queue@queueu-tech.jp"
    
    return {
        "user_id": user_id,
        "document_uploads_used": 0,
        "document_uploads_limit": 999999 if is_unlimited else 2,
        "questions_used": 0,
        "questions_limit": 999999 if is_unlimited else 10,
        "is_unlimited": is_unlimited
    }

def get_permission_flags(current_user: dict) -> dict:
    """
    ユーザーの権限フラグを生成する共通関数
    
    Args:
        current_user: 現在のユーザー情報
    
    Returns:
        権限フラグの辞書
    """
    # 特別管理者メールアドレスの統一定義
    special_admin_emails = ["queue@queuefood.co.jp", "queue@queueu-tech.jp"]
    
    return {
        "is_special_admin": current_user["email"] in special_admin_emails and current_user.get("is_special_admin", False),
        "is_admin_user": current_user["role"] == "admin_user",
        "is_user": current_user["role"] == "user",
        "user_email": current_user["email"],
        "user_role": current_user["role"]
    }

