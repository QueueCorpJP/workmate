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
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY環境変数が設定されていません")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
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
    return int(os.getenv("PORT", 8083))