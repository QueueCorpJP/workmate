#!/bin/bash

echo "==================================="
echo "WorkMate AI - 本番環境起動"
echo "==================================="
echo

# 環境変数設定
export NODE_ENV=production
export ENVIRONMENT=production

echo "[1/4] 本番環境設定確認中..."
if [ ! -f "Chatbot-backend-main/.env.production" ]; then
    echo "❌ .env.productionファイルが見つかりません"
    exit 1
fi

if [ ! -f "Chatbot-Frontend-main/.env.production" ]; then
    echo "❌ フロントエンドの.env.productionファイルが見つかりません"
    exit 1
fi

echo "[2/4] バックエンド準備中..."
cd Chatbot-backend-main
if [ ! -d "venv" ]; then
    echo "Python仮想環境を作成中..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

echo "[3/4] フロントエンドビルド中..."
cd ../Chatbot-Frontend-main
npm install
npm run build

echo "[4/4] 本番サーバー起動中..."
cd ../Chatbot-backend-main
source venv/bin/activate

# 本番環境設定をコピー
cp .env.production .env

# PM2がインストールされている場合はPM2で起動、そうでなければ直接起動
if command -v pm2 &> /dev/null; then
    echo "🚀 PM2でバックエンドを起動中（ポート8083）..."
    pm2 start main.py --name "workmate-backend" --interpreter python3
else
    echo "🚀 バックエンドを直接起動中（ポート8083）..."
    nohup python main.py > backend.log 2>&1 &
    echo $! > backend.pid
fi

echo
echo "==================================="
echo "✅ WorkMate AI 本番環境起動完了"
echo "==================================="
echo
echo "📌 アクセスURL:"
echo "   サービス: https://workmatechat.com"
echo "   API: https://workmatechat.com/chatbot/api"
echo "   APIドキュメント: https://workmatechat.com/docs"
echo
echo "📋 ログ確認:"
if command -v pm2 &> /dev/null; then
    echo "   pm2 logs workmate-backend"
else
    echo "   tail -f backend.log"
fi
echo
echo "🛑 停止方法:"
if command -v pm2 &> /dev/null; then
    echo "   pm2 stop workmate-backend"
else
    echo "   kill \$(cat backend.pid)"
fi
echo