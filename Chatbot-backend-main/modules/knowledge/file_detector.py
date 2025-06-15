"""
ファイル形式検知モジュール
ファイルの内容とMIMEタイプに基づいて適切な処理方式を選択します
"""
import mimetypes
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def detect_file_type(filename: str, content: bytes) -> Dict[str, Any]:
    """
    ファイル名と内容からファイル形式を検知し、適切な処理方式を決定する
    
    Args:
        filename: ファイル名
        content: ファイルの内容（バイト列）
    
    Returns:
        dict: ファイル形式と推奨処理方式の情報
    """
    result = {
        'extension': '',
        'mime_type': '',
        'file_type': 'unknown',
        'processor': 'default',
        'confidence': 0.0
    }
    
    try:
        # ファイル拡張子を取得
        if '.' in filename:
            result['extension'] = filename.split('.')[-1].lower()
        
        # MIMEタイプを取得
        mime_type, _ = mimetypes.guess_type(filename)
        result['mime_type'] = mime_type or ''
        
        # ファイル先頭の署名（マジックナンバー）をチェック
        magic_signature = detect_magic_signature(content)
        
        # CSVファイルの検知
        if is_csv_file(filename, content, magic_signature):
            result.update({
                'file_type': 'csv',
                'processor': 'google_sheets_api',
                'confidence': 0.9
            })
            
        # Excelファイルの検知
        elif is_excel_file(filename, content, magic_signature):
            result.update({
                'file_type': 'excel',
                'processor': 'excel_processor',
                'confidence': 0.95
            })
            
        # PDFファイルの検知
        elif is_pdf_file(filename, content, magic_signature):
            result.update({
                'file_type': 'pdf',
                'processor': 'pdf_processor',
                'confidence': 0.95
            })
            
        # 画像ファイルの検知
        elif is_image_file(filename, content, magic_signature):
            result.update({
                'file_type': 'image',
                'processor': 'gemini_ocr',
                'confidence': 0.9
            })
            
        # Wordファイルの検知
        elif is_word_file(filename, content, magic_signature):
            result.update({
                'file_type': 'word',
                'processor': 'word_processor',
                'confidence': 0.9
            })
            
        # テキストファイルの検知
        elif is_text_file(filename, content, magic_signature):
            result.update({
                'file_type': 'text',
                'processor': 'text_processor',
                'confidence': 0.8
            })
            
        # ビデオファイルの検知
        elif is_video_file(filename, content, magic_signature):
            result.update({
                'file_type': 'video',
                'processor': 'video_processor',
                'confidence': 0.9
            })
        
        logger.info(f"ファイル形式検知結果: {filename} -> {result['file_type']} (信頼度: {result['confidence']})")
        
    except Exception as e:
        logger.error(f"ファイル形式検知エラー: {str(e)}")
        result['confidence'] = 0.0
    
    return result

def detect_magic_signature(content: bytes) -> str:
    """ファイルの先頭バイトからマジックナンバーを検出"""
    if len(content) < 4:
        return ''
    
    # 最初の16バイトをチェック
    header = content[:16]
    
    # PDF
    if header.startswith(b'%PDF'):
        return 'pdf'
    
    # ZIP系（Excel, Word, PowerPoint等）
    if header.startswith(b'PK\x03\x04') or header.startswith(b'PK\x05\x06') or header.startswith(b'PK\x07\x08'):
        return 'zip'
    
    # 古いExcel
    if header.startswith(b'\xd0\xcf\x11\xe0'):
        return 'ole2'
    
    # JPEG
    if header.startswith(b'\xff\xd8\xff'):
        return 'jpeg'
    
    # PNG
    if header.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    
    # GIF
    if header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
        return 'gif'
    
    # BMP
    if header.startswith(b'BM'):
        return 'bmp'
    
    # TIFF
    if header.startswith(b'II*\x00') or header.startswith(b'MM\x00*'):
        return 'tiff'
    
    # WebP
    if header.startswith(b'RIFF') and b'WEBP' in header:
        return 'webp'
    
    # AVI
    if header.startswith(b'RIFF') and b'AVI ' in header:
        return 'avi'
    
    # MP4
    if b'ftyp' in header:
        return 'mp4'
    
    # WebM
    if header.startswith(b'\x1a\x45\xdf\xa3'):
        return 'webm'
    
    return ''

def is_csv_file(filename: str, content: bytes, magic: str) -> bool:
    """CSVファイルかどうかを判定"""
    # 拡張子チェック
    if filename.lower().endswith('.csv'):
        return True
    
    # MIMEタイプチェック
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type in ['text/csv', 'application/csv']:
        return True
    
    # 内容チェック（テキストファイルでカンマ区切り）
    try:
        # UTF-8で読めるかチェック
        text_content = content.decode('utf-8', errors='ignore')
        lines = text_content.split('\n')[:10]  # 最初の10行をチェック
        
        comma_count = 0
        for line in lines:
            if ',' in line:
                comma_count += 1
        
        # 半分以上の行にカンマがあればCSVと判定
        return comma_count >= len(lines) / 2
    except:
        return False

def is_excel_file(filename: str, content: bytes, magic: str) -> bool:
    """Excelファイルかどうかを判定"""
    # 拡張子チェック
    if filename.lower().endswith(('.xlsx', '.xls')):
        return True
    
    # マジックナンバーチェック
    if magic in ['zip', 'ole2']:
        return True
    
    # MIMEタイプチェック
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type and 'excel' in mime_type.lower():
        return True
    
    return False

def is_pdf_file(filename: str, content: bytes, magic: str) -> bool:
    """PDFファイルかどうかを判定"""
    if filename.lower().endswith('.pdf'):
        return True
    
    if magic == 'pdf':
        return True
    
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type == 'application/pdf':
        return True
    
    return False

def is_image_file(filename: str, content: bytes, magic: str) -> bool:
    """画像ファイルかどうかを判定"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
    if any(filename.lower().endswith(ext) for ext in image_extensions):
        return True
    
    image_magics = {'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp'}
    if magic in image_magics:
        return True
    
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type and mime_type.startswith('image/'):
        return True
    
    return False

def is_word_file(filename: str, content: bytes, magic: str) -> bool:
    """Wordファイルかどうかを判定"""
    if filename.lower().endswith(('.doc', '.docx')):
        return True
    
    if magic in ['zip', 'ole2']:
        # ZIPの場合、Wordの特徴的なファイルがあるかチェック
        try:
            import zipfile
            from io import BytesIO
            
            with zipfile.ZipFile(BytesIO(content)) as zf:
                word_files = ['word/document.xml', '[Content_Types].xml']
                for word_file in word_files:
                    if word_file in zf.namelist():
                        return True
        except:
            pass
    
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type and 'word' in mime_type.lower():
        return True
    
    return False

def is_text_file(filename: str, content: bytes, magic: str) -> bool:
    """テキストファイルかどうかを判定"""
    if filename.lower().endswith('.txt'):
        return True
    
    # バイナリファイルでないことをチェック
    try:
        content.decode('utf-8')
        return True
    except UnicodeDecodeError:
        try:
            content.decode('shift_jis')
            return True
        except UnicodeDecodeError:
            return False

def is_video_file(filename: str, content: bytes, magic: str) -> bool:
    """ビデオファイルかどうかを判定"""
    video_extensions = {'.avi', '.mp4', '.webm', '.mov', '.wmv', '.flv', '.mkv'}
    if any(filename.lower().endswith(ext) for ext in video_extensions):
        return True
    
    video_magics = {'avi', 'mp4', 'webm'}
    if magic in video_magics:
        return True
    
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type and mime_type.startswith('video/'):
        return True
    
    return False

def get_recommended_processor(file_type: str) -> str:
    """ファイル形式に対応する推奨プロセッサーを取得"""
    processors = {
        'csv': 'google_sheets_api',
        'excel': 'excel_processor',
        'pdf': 'pdf_processor',
        'image': 'gemini_ocr',
        'word': 'word_processor',
        'text': 'text_processor',
        'video': 'video_processor'
    }
    
    return processors.get(file_type, 'default')