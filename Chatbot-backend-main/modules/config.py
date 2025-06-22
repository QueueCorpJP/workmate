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
    # 最新のGemini 2.5 Flashモデルを使用
    model = genai.GenerativeModel('gemini-2.5-flash')
    return model

def get_db_params():
    """SQLiteデータベースのパラメータを取得します"""
    # SQLiteデータベースのパスを返す
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chatbot.db")
    return {
        "database": db_path
    }

# ポート設定
def get_environment():
    """現在の実行環境を判定します"""
    # 環境変数NODE_ENVまたはENVIRONMENTをチェック
    env = os.getenv("NODE_ENV", "").lower()
    if not env:
        env = os.getenv("ENVIRONMENT", "").lower()
    
    # 本番環境の判定条件
    if env in ["production", "prod"]:
        return "production"
    elif env in ["development", "dev"]:
        return "development"
    else:
        # デフォルトでローカル開発環境として判定
        # 本番環境特有の環境変数やホスト名をチェック
        is_heroku = os.getenv("DYNO") is not None
        is_aws = os.getenv("AWS_REGION") is not None
        is_production_domain = os.getenv("HOST", "").endswith("workmatechat.com")
        
        if is_heroku or is_aws or is_production_domain:
            return "production"
        else:
            return "development"

def get_port():
    """サーバーのポート番号を環境別に取得します"""
    environment = get_environment()
    
    # 環境変数PORTが明示的に設定されている場合は優先
    port_env = os.getenv("PORT")
    
    if port_env:
        # 明示的にPORTが設定されている場合
        try:
            port = int(port_env)
            if port < 1 or port > 65535:
                raise ValueError(f"ポート番号が無効です: {port}. 1-65535の範囲で指定してください。")
            print(f"🌐 ポート設定: {port} (環境変数PORT指定)")
            return port
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(f"PORT環境変数は数値である必要があります: {port_env}")
            raise e
    else:
        # 環境に応じてデフォルトポートを設定
        if environment == "production":
            default_port = 8083  # 本番環境デフォルト
            print(f"🌐 ポート設定: {default_port} (本番環境デフォルト)")
        else:
            default_port = 8085  # ローカル開発環境デフォルト
            print(f"🌐 ポート設定: {default_port} (ローカル開発環境デフォルト)")
        
        return default_port

def get_cors_origins():
    """環境に応じたCORS許可オリジンを取得します"""
    environment = get_environment()
    
    if environment == "production":
        # 本番環境のオリジン
        return [
            "https://workmatechat.com",
            "https://www.workmatechat.com",
            "https://workmate-frontend.vercel.app"
        ]
    else:
        # ローカル開発環境のオリジン
        frontend_ports = os.getenv("FRONTEND_PORTS", "3000,3025,5173")
        ports = [port.strip() for port in frontend_ports.split(",")]
        
        origins = []
        for port in ports:
            if port.isdigit():
                origins.extend([
                    f"http://localhost:{port}",
                    f"http://127.0.0.1:{port}"
                ])
        
        return origins