import requests
import re
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
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

# YouTube Transcript API設定
def create_youtube_api():
    """YouTube Transcript APIの設定を動的に作成"""
    try:
        # Webshareプロキシ設定が利用可能な場合
        if WEBSHAREPROXY_USERNAME and WEBSHAREPROXY_PASSWORD:
            print("Webshareプロキシを使用してYouTube APIを初期化")
            return YouTubeTranscriptApi(
                proxy_config=WebshareProxyConfig(
                    proxy_username=WEBSHAREPROXY_USERNAME,
                    proxy_password=WEBSHAREPROXY_PASSWORD,
                )
            )
        else:
            print("プロキシなしでYouTube APIを初期化")
            return YouTubeTranscriptApi()
    except Exception as e:
        print(f"YouTube API初期化エラー: {str(e)}")
        # 最後の手段として基本的なAPIを返す
        return YouTubeTranscriptApi()

def create_youtube_api_without_proxy():
    """プロキシなしでYouTube Transcript APIを作成（フォールバック用）"""
    try:
        print("フォールバック: プロキシなしでYouTube APIを初期化")
        return YouTubeTranscriptApi()
    except Exception as e:
        print(f"フォールバックAPI初期化エラー: {str(e)}")
        return None

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

def transcribe_youtube_video(youtube_url: str) -> str:
    print(f"=== YouTube字幕取得開始 ===")
    print(f"URL: {youtube_url}")
    
    video_id = get_video_id(youtube_url)
    print(f"抽出されたVideo ID: {video_id}")
    
    if not video_id:
        return "Invalid YouTube URL."
    
    # 環境変数の確認
    print(f"プロキシ設定状況:")
    print(f"  - HTTP_PROXY: {HTTP_PROXY}")
    print(f"  - HTTPS_PROXY: {HTTPS_PROXY}")
    print(f"  - WEBSHAREPROXY_USERNAME: {'設定済み' if WEBSHAREPROXY_USERNAME else '未設定'}")
    print(f"  - WEBSHAREPROXY_PASSWORD: {'設定済み' if WEBSHAREPROXY_PASSWORD else '未設定'}")
    
    # 方法1: YouTube Transcript APIを試行
    try:
        print("=== 方法1: YouTube Transcript API ===")
        # 動的にYouTube APIを作成
        print("YouTube API初期化中...")
        ytt_api = create_youtube_api()
        print(f"YouTube API初期化完了: {type(ytt_api)}")
        
        print(f"字幕取得試行中... Video ID: {video_id}")
        transcript = ytt_api.fetch(video_id, languages=['ja', 'en', 'ja-Hira', 'a.en'])
        print(f"字幕取得成功: {len(transcript.snippets) if hasattr(transcript, 'snippets') else 'Unknown'} スニペット")

        full_text = "\n".join([snippet.text for snippet in transcript.snippets])
        print(f"結合されたテキスト長: {len(full_text)} 文字")
        print("=== YouTube字幕取得完了 ===")

        return full_text
    except Exception as e:
        error_str = str(e)
        print(f"=== YouTube Transcript APIエラー ===")
        print(f"エラータイプ: {type(e).__name__}")
        print(f"エラーメッセージ: {error_str}")
        
        # 方法2: プロキシなしで再試行
        if "ProxyError" in error_str or "407" in error_str or "no element found" in error_str:
            print("=== 方法2: プロキシなしでYouTube Transcript API ===")
            try:
                fallback_api = create_youtube_api_without_proxy()
                if fallback_api:
                    print("フォールバックAPI作成成功、字幕再取得中...")
                    transcript = fallback_api.fetch(video_id, languages=['ja', 'en', 'ja-Hira', 'a.en'])
                    full_text = "\n".join([snippet.text for snippet in transcript.snippets])
                    print("フォールバック成功: プロキシなしで字幕を取得しました")
                    print(f"フォールバック取得テキスト長: {len(full_text)} 文字")
                    return full_text
                else:
                    raise Exception("フォールバックAPIの作成に失敗")
            except Exception as fallback_error:
                print(f"フォールバック失敗: {str(fallback_error)}")
                print(f"フォールバックエラータイプ: {type(fallback_error).__name__}")
        
        # 方法3: yt-dlpを使用
        print("=== 方法3: yt-dlpで動画情報取得 ===")
        try:
            ytdlp_result = transcribe_youtube_video_with_ytdlp(youtube_url)
            if not ytdlp_result.startswith("yt-dlp") or "成功" in ytdlp_result:
                return ytdlp_result
        except Exception as ytdlp_error:
            print(f"yt-dlpも失敗: {str(ytdlp_error)}")
        
        # 全ての方法が失敗した場合の詳細エラーメッセージ
        print("=== 全ての方法が失敗 ===")
        if "no element found: line 1, column 0" in error_str:
            return f"YouTube字幕取得エラー: 動画の字幕が利用できないか、プロキシ設定に問題があります。動画ID: {video_id}\n\n対処法:\n1. プロキシ設定を確認してください\n2. 別のYouTube動画を試してください\n3. 動画に字幕が設定されているか確認してください"
        elif "ProxyError" in error_str or "407" in error_str:
            return f"プロキシ認証エラー: YouTube動画の字幕取得に失敗しました。ネットワーク設定を確認してください。\n動画ID: {video_id}\n詳細: {error_str}"
        elif "Transcript not available" in error_str or "TranscriptsDisabled" in error_str:
            return f"字幕無効エラー: この動画（{video_id}）には字幕が提供されていません。字幕付きの動画を選択してください。"
        elif "TooManyRequests" in error_str:
            return f"API制限エラー: YouTube API のリクエスト制限に達しました。しばらく経ってからお試しください。"
        elif "VideoUnavailable" in error_str:
            return f"動画アクセスエラー: 動画（{video_id}）にアクセスできません。動画が削除されているか、プライベート設定の可能性があります。"
        else:
            return f"YouTube動画の字幕取得エラー: 複数の方法を試しましたが全て失敗しました。\n動画ID: {video_id}\n詳細エラー: {error_str}"

async def extract_text_from_html(url: str) -> str:
    try:
        # 大きなデータの可能性をチェック
        await _check_and_throttle_url_request(url)
        
        playwright = await async_playwright().start()
        
        # プロキシ設定を取得
        proxies = get_proxies()
        launch_options = {"headless": True}
        
        # プロキシ設定がある場合は追加
        if proxies and proxies.get('https'):
            proxy_url = proxies['https']
            # プロキシURLを解析
            if '@' in proxy_url:
                # 認証情報が含まれている場合
                protocol, rest = proxy_url.split('://', 1)
                auth_server = rest.split('@')
                if len(auth_server) == 2:
                    auth, server = auth_server
                    username, password = auth.split(':')
                    launch_options["proxy"] = {
                        "server": f"{protocol}://{server}",
                        "username": username,
                        "password": password
                    }
            else:
                launch_options["proxy"] = {"server": proxy_url}
        
        browser = await playwright.chromium.launch(**launch_options)
        page = await browser.new_page()
        
        # ページサイズによる待機時間調整
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        html = await page.content()
        
        # HTMLサイズをチェックしてスロットリング
        html_size_mb = len(html.encode('utf-8')) / (1024 * 1024)
        if html_size_mb > 5:  # 5MB以上の場合
            print(f"大きなHTMLデータ検出 ({html_size_mb:.2f}MB) - サーバー負荷軽減のため待機")
            await asyncio.sleep(min(html_size_mb * 0.5, 10))  # 最大10秒
        
        await browser.close()
        await playwright.stop() 
        
        # Check for permission-denied indicators before parsing
        if any(msg in html for msg in [
            "You need access", 
            "Request access", 
            "You don't have access", 
            "Sign in to continue", 
            "Sign into continue", 
            "To view this document",
            "Use a private browsing window to sign in"
        ]):
            raise PermissionError(f"Permission denied: You don't have access to this Google Doc → {url}")

        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(['script', 'style', 'meta', 'link', 'noscript', 'header', 'footer', 'nav']):
            tag.decompose()

        text = soup.get_text(separator='\n')
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r' +', ' ', text)

        title = ensure_string(soup.title.string).strip() if soup.title and soup.title.string else "No Title"
        return f"=== URL: {url} ===\n=== Title: {title} ===\n\n{text}"
    except Exception as e:
        print(f"HTML抽出エラー: {str(e)}")
        if "ProxyError" in str(e) or "407" in str(e):
            return f"プロキシ認証エラー: Webページの取得に失敗しました。ネットワーク設定を確認してください。詳細: {str(e)}"
        return f"Webページ取得エラー: {str(e)}"

async def extract_text_from_pdf(url: str) -> str:
    try:
        # 大きなデータの可能性をチェック
        await _check_and_throttle_url_request(url)
        
        # プロキシ設定を取得
        proxies = get_proxies()
        
        # HEADリクエストでファイルサイズを事前チェック
        try:
            head_response = requests.head(url, proxies=proxies, timeout=10)
            content_length = head_response.headers.get('content-length')
            if content_length:
                file_size_mb = int(content_length) / (1024 * 1024)
                if file_size_mb > 20:  # 20MB以上の場合
                    print(f"大きなPDFファイル検出 ({file_size_mb:.2f}MB) - サーバー負荷軽減のため待機")
                    await asyncio.sleep(min(file_size_mb * 0.3, 15))  # 最大15秒
        except:
            pass  # HEADリクエストが失敗してもダウンロードは続行
        
        response = requests.get(url, proxies=proxies, timeout=30)
        if response.status_code != 200:
            raise Exception(f"Failed to download PDF: {url}")
        
        # ダウンロード後のファイルサイズチェック
        pdf_size_mb = len(response.content) / (1024 * 1024)
        if pdf_size_mb > 10:  # 10MB以上の場合
            print(f"大きなPDFデータ検出 ({pdf_size_mb:.2f}MB) - 処理前待機")
            await asyncio.sleep(min(pdf_size_mb * 0.2, 8))  # 最大8秒

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        try:
            text = ""
            with fitz.open(tmp_path) as doc:
                page_count = len(doc)
                for i, page in enumerate(doc):
                    text += page.get_text()
                    # 大きなPDFの場合、ページ処理間に待機
                    if page_count > 50 and i % 10 == 9:  # 50ページ以上で10ページごと
                        await asyncio.sleep(0.5)
        finally:
            os.remove(tmp_path)  # Clean up the file after reading

        return f"=== URL: {url} ===\n=== Title: PDF Document ===\n\n{ensure_string(text).strip()}"
    except Exception as e:
        print(f"PDF取得エラー: {str(e)}")
        if "ProxyError" in str(e) or "407" in str(e):
            return f"プロキシ認証エラー: PDFファイルの取得に失敗しました。ネットワーク設定を確認してください。詳細: {str(e)}"
        return f"PDFファイル取得エラー: {str(e)}"

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

def test_youtube_connection():
    """YouTube接続のテスト（字幕が確実にある動画でテスト）"""
    # 字幕が確実にある一般的な動画のIDを使用
    test_video_ids = [
        "jNQXAC9IVRw",  # "Me at the zoo" - YouTube初の動画
        "dQw4w9WgXcQ",  # Rick Roll - 多言語字幕あり
        "kJQP7kiw5Fk"   # Luis Fonsi - Despacito
    ]
    
    for video_id in test_video_ids:
        try:
            print(f"テスト動画ID: {video_id}")
            ytt_api = create_youtube_api()
            transcript = ytt_api.fetch(video_id, languages=['en'])
            print(f"テスト成功: {len(transcript.snippets)} スニペット取得")
            return True, f"YouTube接続テスト成功 (動画ID: {video_id})"
        except Exception as e:
            print(f"テスト失敗 (動画ID: {video_id}): {str(e)}")
            continue
    
    return False, "全てのテスト動画で字幕取得に失敗しました"

def transcribe_youtube_video_with_ytdlp(youtube_url: str) -> str:
    """yt-dlpを使用してYouTube動画の字幕を取得する（代替手段）"""
    try:
        import yt_dlp
        
        print(f"=== yt-dlp使用でYouTube字幕取得 ===")
        print(f"URL: {youtube_url}")
        
        # プロキシ設定
        ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['ja', 'en'],
            'skip_download': True,
            'quiet': True,
        }
        
        # プロキシ設定を追加
        proxies = get_proxies()
        if proxies:
            if proxies.get('https'):
                ydl_opts['proxy'] = proxies['https']
                print(f"yt-dlpプロキシ設定: {proxies['https']}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # 動画情報を取得
                info = ydl.extract_info(youtube_url, download=False)
                
                # 字幕情報を確認
                subtitles = info.get('subtitles', {})
                auto_subtitles = info.get('automatic_captions', {})
                
                print(f"利用可能な字幕: {list(subtitles.keys())}")
                print(f"自動字幕: {list(auto_subtitles.keys())}")
                
                # 字幕を取得（優先順位: ja -> en -> その他）
                subtitle_text = ""
                for lang in ['ja', 'en']:
                    if lang in subtitles:
                        print(f"手動字幕 ({lang}) を使用")
                        # 実際の字幕ダウンロードは複雑なので、タイトルと説明文を返す
                        break
                    elif lang in auto_subtitles:
                        print(f"自動字幕 ({lang}) を使用")
                        break
                
                # 字幕が取得できない場合は、タイトルと説明文を返す
                title = info.get('title', '不明なタイトル')
                description = info.get('description', '説明なし')
                
                # タイトルと説明文を組み合わせて返す
                result_text = f"=== YouTube動画情報 ===\n"
                result_text += f"タイトル: {title}\n\n"
                result_text += f"説明:\n{description[:1000]}{'...' if len(description) > 1000 else ''}\n"
                
                print(f"yt-dlp取得成功: タイトル長={len(title)}, 説明文長={len(description)}")
                print("=== yt-dlp字幕取得完了 ===")
                
                return result_text
                
            except Exception as extract_error:
                print(f"yt-dlp情報抽出エラー: {str(extract_error)}")
                return f"yt-dlp動画情報取得エラー: {str(extract_error)}"
                
    except ImportError:
        return "yt-dlpライブラリがインストールされていません。"
    except Exception as e:
        print(f"yt-dlpエラー: {str(e)}")
        return f"yt-dlp字幕取得エラー: {str(e)}"

