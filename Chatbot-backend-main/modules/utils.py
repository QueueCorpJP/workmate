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
        文字起こしされたテキスト
    """
    # 現在は簡単な実装のみ
    # 実際のYouTube API実装が必要な場合は後で追加
    return f"YouTube動画の処理は現在対応していません: {url}"

async def extract_text_from_pdf(url: str) -> str:
    """URLからPDFファイルを取得し、テキストを抽出する
    
    Args:
        url: PDFファイルのURL
        
    Returns:
        抽出されたテキスト
    """
    try:
        # URLからPDFファイルを取得
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # PyMuPDFを使用してPDFからテキストを抽出
        pdf_document = fitz.open(stream=response.content, filetype="pdf")
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text += page.get_text()
        pdf_document.close()
        return text
    except Exception as e:
        print(f"PDF抽出エラー: {e}")
        return f"PDF抽出エラー: {e}"

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

async def extract_text_from_html(url: str) -> str:
    """URLからHTMLコンテンツを取得し、テキストを抽出する
    
    Args:
        url: 抽出対象のURL
        
    Returns:
        抽出されたテキスト
    """
    try:
        # URLからHTMLコンテンツを取得
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
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
        
        return text
    except Exception as e:
        print(f"HTML抽出エラー: {e}")
        return f"HTML抽出エラー: {e}"

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

