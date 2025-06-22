@echo off
echo ===================================
echo WorkMate AI - ローカル開発環境起動
echo ===================================
echo.

echo [1/3] バックエンド起動中...
cd /d "%~dp0\Chatbot-backend-main"
start "WorkMate Backend (Port 8085)" cmd /k "python main.py"

echo [2/3] フロントエンド依存関係確認中...
cd /d "%~dp0\Chatbot-Frontend-main"
if not exist node_modules (
    echo Node.js依存関係をインストール中...
    npm install
)

echo [3/3] フロントエンド起動中...
start "WorkMate Frontend (Port 3025)" cmd /k "npm run dev"

echo.
echo ===================================
echo 🚀 WorkMate AI ローカル環境起動完了
echo ===================================
echo.
echo 📌 アクセスURL:
echo    フロントエンド: http://localhost:3025
echo    バックエンドAPI: http://localhost:8085/chatbot/api
echo    APIドキュメント: http://localhost:8085/docs
echo.
echo ✨ Ctrl+Cで各サーバーを停止できます
echo.
pause