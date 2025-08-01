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

def setup_gemini_with_cache():
    """コンテキストキャッシュ対応のGemini APIの設定"""
    import google.generativeai as genai
    
    # GEMINI_API_KEY（推奨）またはGOOGLE_API_KEY（後方互換）をサポート
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY環境変数が設定されていません")
    
    genai.configure(api_key=api_key)
    
    # コンテキストキャッシュ機能を有効化したGemini 2.5 Flashモデル
    model = genai.GenerativeModel('gemini-2.5-flash')
    # generation_configは generate_content 呼び出し時に指定
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
    print("🔍 環境判定開始...")
    
    # PM2で実行されているかを確認
    pm2_home = os.getenv("PM2_HOME")
    pm2_json = os.getenv("PM2_JSON_PROCESSING")
    print(f"🔍 PM2_HOME: {pm2_home}")
    print(f"🔍 PM2_JSON_PROCESSING: {pm2_json}")
    
    is_pm2 = pm2_home is not None or pm2_json is not None
    if is_pm2:
        print("✅ PM2環境を検出 -> production")
        return "production"

    # 環境変数NODE_ENVまたはENVIRONMENTをチェッ
    node_env = os.getenv("NODE_ENV", "").lower()
    env_var = os.getenv("ENVIRONMENT", "").lower()
    print(f"🔍 NODE_ENV: {node_env}")
    print(f"🔍 ENVIRONMENT: {env_var}")
    
    env = node_env if node_env else env_var
    
    # 本番環境の判定条件
    if env in ["production", "prod"]:
        print(f"✅ 環境変数で本番環境を検出 ({env}) -> production")
        return "production"
    elif env in ["development", "dev"]:
        print(f"✅ 環境変数で開発環境を検出 ({env}) -> development")
        return "development"
    else:
        print("🔍 環境変数による判定失敗、追加条件をチェック...")
        # デフォルトでローカル開発環境として判定
        # 本番環境特有の環境変数やホスト名をチェック
        is_heroku = os.getenv("DYNO") is not None
        is_aws = os.getenv("AWS_REGION") is not None
        is_production_domain = os.getenv("HOST", "").endswith("workmatechat.com")
        
        print(f"🔍 DYNO: {os.getenv('DYNO')}")
        print(f"🔍 AWS_REGION: {os.getenv('AWS_REGION')}")
        print(f"🔍 HOST: {os.getenv('HOST')}")
        
        if is_heroku or is_aws or is_production_domain:
            print("✅ 追加条件で本番環境を検出 -> production")
            return "production"
        else:
            print("❌ 全ての条件で本番環境を検出できず -> development")
            return "development"

def get_port():
    """サーバーのポート番号を環境別に取得します"""
    environment = get_environment()
    print(f"🔍 判定された環境: {environment}")
    
    # 環境変数PORTが明示的に設定されている場合は優先
    port_env = os.getenv("PORT")
    print(f"🔍 環境変数PORT: {port_env}")
    
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
    
    # 基本的な本番ドメイン
    production_origins = [
        "https://workmatechat.com",
        "https://www.workmatechat.com",
        "https://workmate-frontend.vercel.app"
    ]
    
    # ローカル開発用オリジン
    frontend_ports = os.getenv("FRONTEND_PORTS", "3000,3025,5173")
    ports = [port.strip() for port in frontend_ports.split(",")]
    
    local_origins = []
    for port in ports:
        if port.isdigit():
            local_origins.extend([
                f"http://localhost:{port}",
                f"http://127.0.0.1:{port}"
            ])
    
    if environment == "production":
        # 本番環境でもローカル開発からのアクセスを許可（開発・テスト用）
        return production_origins + local_origins
    else:
        # 開発環境では全てのオリジンを許可
        return local_origins + production_origins

# 🔄 ハイブリッド処理設定
HYBRID_PROCESSING_ENABLED = os.getenv("HYBRID_PROCESSING_ENABLED", "true").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PREFER_OPENAI_FOR_COMPLEX_DATA = os.getenv("PREFER_OPENAI_FOR_COMPLEX_DATA", "false").lower() == "true"

# 処理方法選択の優先順位
EXCEL_PROCESSING_PRIORITY = os.getenv("EXCEL_PROCESSING_PRIORITY", "hybrid").lower()
# 選択肢: "hybrid", "google_sheets", "openai", "auto"

def get_excel_processing_method() -> str:
    """Excel処理方法を動的に決定"""
    if EXCEL_PROCESSING_PRIORITY == "hybrid" and OPENAI_API_KEY and HYBRID_PROCESSING_ENABLED:
        return "hybrid"
    elif EXCEL_PROCESSING_PRIORITY == "openai" and OPENAI_API_KEY:
        return "openai"
    elif EXCEL_PROCESSING_PRIORITY == "google_sheets":
        return "google_sheets"
    elif EXCEL_PROCESSING_PRIORITY == "auto":
        # ファイルサイズや複雑さに基づいて自動選択
        return "hybrid" if OPENAI_API_KEY else "google_sheets"
    else:
        return "google_sheets"  # デフォルト

def setup_openai_client():
    """OpenAI APIクライアントの設定"""
    if not OPENAI_API_KEY:
        logger.warning("⚠️ OPENAI_API_KEY環境変数が設定されていません")
        return None
    
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        logger.info("✅ OpenAI APIクライアント初期化完了")
        return client
    except ImportError:
        logger.error("❌ OpenAI ライブラリが見つかりません。pip install openai を実行してください。")
        return None
    except Exception as e:
        logger.error(f"❌ OpenAI APIクライアント初期化エラー: {str(e)}")
        return None


