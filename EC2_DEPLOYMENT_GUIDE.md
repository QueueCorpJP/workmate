# EC2環境でのWorkMate AI Chatbot デプロイメントガイド

## 問題の概要

ローカル環境では正常に動作するが、EC2環境で404エラーが発生する問題の解決方法を説明します。

## 主な問題点

1. **ポート設定の不整合**: Nginxが期待するポート（8083）とバックエンドが実際に使用するポートの不一致
2. **環境変数の設定不備**: 本番環境での環境変数が正しく設定されていない
3. **FastAPIのドキュメントエンドポイント設定**: `/docs`エンドポイントが正しく設定されていない

## 解決手順

### 1. バックエンドサーバーの設定確認

```bash
# EC2にSSH接続
ssh -i your-key.pem ubuntu@your-ec2-ip

# プロジェクトディレクトリに移動
cd /path/to/workmate

# 現在のプロセスを確認
ps aux | grep python
netstat -tlnp | grep 808
```

### 2. 環境変数の設定

```bash
# 本番環境用の環境変数を設定
export ENVIRONMENT=production
export NODE_ENV=production
export PORT=8083

# 環境変数を確認
printenv | grep -E '(ENVIRONMENT|PORT|NODE_ENV)'
```

### 3. バックエンドサーバーの再起動

```bash
# 既存のプロセスを停止
sudo pkill -f "python.*main.py"

# 本番環境設定を使用してサーバーを起動
cd Chatbot-backend-main
source venv/bin/activate
cp .env.production .env
python main.py
```

### 4. Nginxの設定確認

```bash
# Nginx設定をテスト
sudo nginx -t

# Nginxを再起動
sudo systemctl restart nginx

# Nginxのステータス確認
sudo systemctl status nginx
```

### 5. ファイアウォール設定

```bash
# ポート8083を開放
sudo ufw allow 8083

# ファイアウォールステータス確認
sudo ufw status
```

## トラブルシューティング

### APIエンドポイントのテスト

```bash
# ローカルでAPIをテスト
curl -I http://localhost:8083/chatbot/api/docs
curl -I http://localhost:8083/chatbot/api/auth/login

# 外部からのアクセステスト
curl -I https://workmatechat.com/chatbot/api/docs
```

### ログの確認

```bash
# バックエンドログ
tail -f backend.log

# Nginxログ
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# PM2を使用している場合
pm2 logs workmate-backend
```

### 診断スクリプトの実行

```bash
# 診断スクリプトを実行
python diagnose_ec2.py
```

## PM2を使用した本番デプロイメント

```bash
# PM2をインストール（未インストールの場合）
npm install -g pm2

# アプリケーションを起動
pm2 start main.py --name workmate-backend --interpreter python3

# PM2の設定を保存
pm2 save
pm2 startup

# ステータス確認
pm2 status
pm2 logs workmate-backend
```

## 設定ファイルの確認事項

### 1. `.env.production`ファイル
- `PORT=8083`が設定されていること
- `ENVIRONMENT=production`が設定されていること
- 必要なAPIキーが全て設定されていること

### 2. Nginx設定（`/etc/nginx/conf.d/workmatechat.com.conf`）
```nginx
upstream chatbot_backend {
    server 127.0.0.1:8083 max_fails=1 fail_timeout=5s;
    server 127.0.0.1:8085 backup;
}
```

### 3. FastAPI設定（`main.py`）
```python
app = FastAPI(
    title="WorkMate Chatbot API",
    description="WorkMate AI Chatbot Backend API",
    version="1.0.0",
    docs_url="/chatbot/api/docs",
    redoc_url="/chatbot/api/redoc",
    openapi_url="/chatbot/api/openapi.json"
)
```

## よくある問題と解決方法

### 問題1: 404 Not Found エラー
**原因**: バックエンドサーバーが起動していない、または間違ったポートで起動している
**解決**: 上記の手順でサーバーを正しく起動する

### 問題2: 502 Bad Gateway エラー
**原因**: Nginxは動作しているがバックエンドサーバーに接続できない
**解決**: バックエンドサーバーのポート設定を確認し、ファイアウォール設定を確認する

### 問題3: 環境変数が読み込まれない
**原因**: `.env.production`ファイルが正しく読み込まれていない
**解決**: 環境変数を手動で設定するか、ファイルパスを確認する

## 自動デプロイメントスクリプト

本番環境での自動デプロイメントには以下のスクリプトを使用してください：

```bash
# 本番環境起動スクリプト
./scripts/start-production.sh
```

このスクリプトは以下を自動実行します：
- 依存関係のインストール
- フロントエンドのビルド
- 本番環境設定の適用
- バックエンドサーバーの起動
- ヘルスチェック

## 監視とメンテナンス

### 定期的なヘルスチェック
```bash
# APIの応答確認
curl -f https://workmatechat.com/chatbot/api/docs

# サーバーリソース確認
htop
df -h
```

### ログローテーション
```bash
# logrotateの設定
sudo nano /etc/logrotate.d/workmate
```

## サポート

問題が解決しない場合は、以下の情報を収集してサポートに連絡してください：

1. `diagnose_ec2.py`の実行結果
2. Nginxエラーログ
3. バックエンドログ
4. システムリソース使用状況
5. 環境変数の設定状況