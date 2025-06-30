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

# 既存のプロセスを停止
echo "既存のプロセスを停止中..."
if command -v pm2 &> /dev/null; then
    pm2 stop workmate-backend 2>/dev/null || true
    pm2 delete workmate-backend 2>/dev/null || true
else
    if [ -f backend.pid ]; then
        kill $(cat backend.pid) 2>/dev/null || true
        rm -f backend.pid
    fi
fi

# ポート8083が使用中の場合は停止
lsof -ti:8083 | xargs kill -9 2>/dev/null || true

# PM2がインストールされている場合はPM2で起動、そうでなければ直接起動
if command -v pm2 &> /dev/null; then
    echo "🚀 PM2でバックエンドを起動中（ポート8083）..."
    pm2 start main.py --name "workmate-backend" --interpreter python3 --env production
else
    echo "🚀 バックエンドを直接起動中（ポート8083）..."
    export ENVIRONMENT=production
    export NODE_ENV=production
    export PORT=8083
    nohup python main.py > backend.log 2>&1 &
    echo $! > backend.pid
fi

# サーバーが起動するまで待機
echo "サーバー起動を待機中..."
sleep 5

# ヘルスチェック
echo "ヘルスチェック実行中..."
for i in {1..10}; do
    if curl -f http://localhost:8083/chatbot/api/docs >/dev/null 2>&1; then
        echo "✅ サーバーが正常に起動しました"
        break
    else
        echo "⏳ サーバー起動待機中... ($i/10)"
        sleep 2
    fi
done

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