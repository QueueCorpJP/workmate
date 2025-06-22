#!/bin/bash

echo "=== WorkMate バックエンドサーバー修復スクリプト ==="
echo "実行時刻: $(date)"
echo ""

# 作業ディレクトリ確認
EXPECTED_DIR="/home/ec2-user/workmate/Chatbot-backend-main"
if [ "$(pwd)" != "$EXPECTED_DIR" ]; then
    echo "作業ディレクトリを変更します: $EXPECTED_DIR"
    cd "$EXPECTED_DIR" || {
        echo "❌ 作業ディレクトリに移動できません: $EXPECTED_DIR"
        exit 1
    }
fi

echo "現在の作業ディレクトリ: $(pwd)"
echo ""

# 1. 既存のプロセスを停止
echo "1. 既存プロセスの停止"
if command -v pm2 >/dev/null 2>&1; then
    echo "   PM2プロセスを停止中..."
    pm2 stop chatbot-backend 2>/dev/null || echo "   (chatbot-backendプロセスが見つかりません)"
    pm2 delete chatbot-backend 2>/dev/null || echo "   (削除するプロセスがありません)"
else
    echo "   PM2が見つかりません"
fi

# Pythonプロセスも強制終了
echo "   Pythonプロセスを強制終了..."
pkill -f "main.py" 2>/dev/null || echo "   (該当するプロセスがありません)"
pkill -f "uvicorn" 2>/dev/null || echo "   (該当するプロセスがありません)"

echo ""

# 2. 必要なファイルの確認
echo "2. 必要ファイルの確認"
FILES_OK=true

if [ ! -f "main.py" ]; then
    echo "   ❌ main.py が見つかりません"
    FILES_OK=false
else
    echo "   ✅ main.py 存在"
fi

if [ ! -f "ecosystem.config.js" ]; then
    echo "   ❌ ecosystem.config.js が見つかりません"
    FILES_OK=false
else
    echo "   ✅ ecosystem.config.js 存在"
fi

if [ ! -d "venv" ]; then
    echo "   ❌ venv ディレクトリが見つかりません"
    FILES_OK=false
else
    echo "   ✅ venv ディレクトリ 存在"
fi

if [ ! -f "requirements.txt" ]; then
    echo "   ❌ requirements.txt が見つかりません"
    FILES_OK=false
else
    echo "   ✅ requirements.txt 存在"
fi

if [ "$FILES_OK" = false ]; then
    echo ""
    echo "❌ 必要なファイルが不足しています。リポジトリの再取得が必要かもしれません。"
    exit 1
fi

echo ""

# 3. 仮想環境の確認と依存関係インストール
echo "3. 仮想環境と依存関係の確認"
if [ -f "venv/bin/activate" ]; then
    echo "   仮想環境をアクティベート中..."
    source venv/bin/activate
    
    echo "   Python環境確認:"
    echo "     Python: $(python --version)"
    echo "     pip: $(pip --version)"
    
    echo "   依存関係を更新中..."
    pip install -r requirements.txt --quiet
    
    if [ $? -eq 0 ]; then
        echo "   ✅ 依存関係のインストール完了"
    else
        echo "   ❌ 依存関係のインストールに失敗しました"
        exit 1
    fi
else
    echo "   ❌ 仮想環境が正しく設定されていません"
    exit 1
fi

echo ""

# 4. 環境変数の確認
echo "4. 環境変数の確認"
if [ -f ".env" ]; then
    echo "   ✅ .env ファイル存在"
    # APIキーの存在確認（値は表示しない）
    if grep -q "GOOGLE_API_KEY" .env && grep -q "SUPABASE_" .env; then
        echo "   ✅ 主要な環境変数が設定されています"
    else
        echo "   ⚠️ 一部の環境変数が不足している可能性があります"
    fi
else
    echo "   ❌ .env ファイルが見つかりません"
    echo "   .env.example から .env ファイルを作成し、適切な値を設定してください"
    exit 1
fi

echo ""

# 5. インポートテスト
echo "5. Pythonモジュールのインポートテスト"
python -c "
import sys
sys.path.insert(0, '.')
try:
    from main import app
    print('   ✅ main.py インポート成功')
except Exception as e:
    print(f'   ❌ main.py インポートエラー: {e}')
    sys.exit(1)
    
try:
    from modules.config import get_port
    port = get_port()
    print(f'   ✅ ポート設定: {port}')
except Exception as e:
    print(f'   ❌ ポート設定エラー: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "   ❌ インポートテストに失敗しました"
    exit 1
fi

echo ""

# 6. PM2での起動
echo "6. PM2での起動"
if command -v pm2 >/dev/null 2>&1; then
    echo "   PM2でアプリケーションを起動中..."
    pm2 start ecosystem.config.js
    
    if [ $? -eq 0 ]; then
        echo "   ✅ PM2起動成功"
        
        # 少し待ってからステータス確認
        sleep 3
        echo ""
        echo "   プロセス状況:"
        pm2 list
        
        echo ""
        echo "   ポート確認:"
        netstat -tlnp 2>/dev/null | grep :8083 || echo "   ⚠️ ポート8083がリッスンしていません"
        
    else
        echo "   ❌ PM2起動に失敗しました"
        echo "   ログを確認してください: pm2 logs chatbot-backend"
        exit 1
    fi
else
    echo "   ❌ PM2が見つかりません"
    echo "   手動起動を試行します..."
    nohup python main.py > backend.log 2>&1 &
    PID=$!
    echo "   プロセスID: $PID"
    
    # 少し待ってからプロセス確認
    sleep 3
    if kill -0 $PID 2>/dev/null; then
        echo "   ✅ 手動起動成功"
        echo "   ログファイル: backend.log"
    else
        echo "   ❌ 手動起動に失敗しました"
        echo "   ログを確認してください: cat backend.log"
        exit 1
    fi
fi

echo ""

# 7. 動作確認
echo "7. 動作確認"
echo "   APIエンドポイントをテスト中..."

# シンプルなヘルスチェック
timeout 10s curl -s http://localhost:8083/chatbot/api/test-simple >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ APIレスポンス正常"
else
    echo "   ⚠️ APIレスポンステストに失敗（タイムアウトまたはエラー）"
    echo "   しばらく待ってから手動で確認してください："
    echo "   curl http://localhost:8083/chatbot/api/test-simple"
fi

echo ""

# 8. 最終確認と推奨事項
echo "8. 最終確認"
echo "   ✅ バックエンドサーバーの修復作業が完了しました"
echo ""
echo "確認事項:"
echo "1. PM2プロセス状況: pm2 list"
echo "2. ログ確認: pm2 logs chatbot-backend"
echo "3. APIテスト: curl http://localhost:8083/chatbot/api/test-simple"
echo "4. フロントエンドからのテスト: ファイルアップロード機能を試してください"
echo ""
echo "問題が続く場合:"
echo "1. pm2 logs chatbot-backend でエラーログを確認"
echo "2. ./debug_production.sh で詳細診断を実行"
echo "3. nginx設定の確認: sudo nginx -t"
echo "4. nginx再読み込み: sudo systemctl reload nginx"

echo ""
echo "=== 修復スクリプト完了 ===" 