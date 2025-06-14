"""
設定モジュール
アプリケーション全体の設定を管理します
"""
import os
import logging
import sys
from dotenv import load_dotenv, dotenv_values

# 環境変数の読み込み
for key in dotenv_values():
    os.environ.pop(key, None)
load_dotenv()

# ロギングの設定
def setup_logging():
    """ロギングの設定を行います"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    # 注意: ここでは会社名を使用しない
    logger = logging.getLogger("chatbot-assistant")
    logger.setLevel(logging.INFO)
    logger.info("バックエンドサーバーを起動しています...")
    return logger

# Gemini APIの設定
def setup_gemini():
    """Gemini APIの設定を行います"""
    import google.generativeai as genai
    
    # GEMINI_API_KEY（推奨）またはGOOGLE_API_KEY（後方互換）をサポート
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY環境変数が設定されていません")
    
    genai.configure(api_key=api_key)
    # より高いクォータ制限のあるモデルを使用
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model

def get_db_params():
    """SQLiteデータベースのパラメータを取得します"""
    # SQLiteデータベースのパスを返す
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chatbot.db")
    return {
        "database": db_path
    }

# ポート設定
def get_port():
    """サーバーのポート番号を取得します"""
    # 環境変数PORTから取得、未設定の場合はデフォルト値を使用
    port_env = os.getenv("PORT", "8085")  # デフォルト8085
    
    try:
        port = int(port_env)
        if port < 1 or port > 65535:
            raise ValueError(f"ポート番号が無効です: {port}. 1-65535の範囲で指定してください。")
        return port
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(f"PORT環境変数は数値である必要があります: {port_env}")
        raise e