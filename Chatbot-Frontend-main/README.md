# チャットボットフロントエンド

# ローカル開発セットアップ

## 1. プロジェクトをクローンする

まず、GitHub からプロジェクトをクローンします：

```bash
git clone https://github.com/QueueCorpJP/Chatbot-Frontend.git
cd Chatbot-Frontend
```

## 2. npm モジュールのインストール

プロジェクトに必要な npm モジュールをインストールします：

```bash
npm install
```

## 3. ローカル開発サーバーの起動

ローカル開発環境でフロントエンドを実行するには、以下のコマンドを実行します：

```bash
npm run dev --host
```

これで、http://localhost:3000 でフロントエンドアプリケーションが動作していることが確認できます。

# Vercel へのデプロイ

## 1. 初期設定

GitHub リポジトリを Vercel に接続:

- Vercel にサインインして、GitHub リポジトリを接続します。

ルートディレクトリをフロントエンドフォルダに設定:

- Vercel の設定で、frontend フォルダをルートディレクトリとして指定します。

ビルドコマンドの設定:

- npm run build をビルドコマンドとして設定します。

出力ディレクトリの設定:

- 出力ディレクトリを dist に設定します。

## 2. 設定

vite.config.ts でローカル開発用のプロキシターゲット URL を設定:

```ts
proxy: {
  "/chatbot/api": {
    target: `http://localhost:${process.env.VITE_BACKEND_PORT || 8083}`, // 環境変数からポート取得
    changeOrigin: true,
    secure: false,
  },
},
```

本番環境での API リクエストのルーティング: 本番環境では、API リクエストは Vercel の rewrites を通じてリダイレクトされます。vercel.json をプロジェクトのルートに作成または更新します：

```json
{
  "rewrites": [
    {
      "source": "/chatbot/api/:path*",
      "destination": "https://ec2-3-112-74-4.ap-northeast-1.compute.amazonaws.com/chatbot/api/:path*"
    }
  ]
}
```

<b>注意:</b> これにより、フロントエンドからの /chatbot/api/\* リクエストは、AWS EC2 にデプロイされた FastAPI バックエンドにリダイレクトされます。

## 3. デプロイ

変更を main ブランチにプッシュ:

- main ブランチに変更をプッシュすると、自動的にデプロイがトリガーされます。

Vercel ダッシュボードから再デプロイ:

- Vercel のダッシュボードから手動で再デプロイをトリガーすることもできます。

# AWS EC2 上で アプリケーションを構築・デプロイする手順

# 1. AWS EC2 インスタンスの作成（Amazon Linux 2023 + g4dn.2xlarge）

## (1) AWS にログイン：

https://aws.amazon.com/console/ にアクセスしてログインします。

## (2) EC2 ダッシュボードへ移動：

「EC2」と検索し、ダッシュボードを開きます。

## (3) インスタンスの起動：

「インスタンスを起動」をクリックします。

## (4) Amazon マシンイメージ（AMI）を選択：

Amazon Linux 2023 を選択してください。

## (5) インスタンスタイプを選択：

g4dn.2xlarge を選択します（NVIDIA T4 GPU 搭載、GPU ベースのアプリに最適）。

## (6) キーペアを作成または選択：

SSH 接続用に既存のキーペアを選ぶか、新しく作成してください。

## (7) ストレージ設定：

必要に応じて EBS（SSD）のサイズを増やすことを推奨します（例：50GB〜100GB 以上）。

## (8) セキュリティグループ設定：

以下のポートを開放します：

- 22（SSH）

- 80（HTTP）

- 443（HTTPS）

- 8083（FastAPI のバックエンド）

## (9) インスタンスの起動と接続：

.pem ファイルを使って以下のように SSH 接続します：

```bash
chmod 400 your-key.pem
ssh -i "your-key.pem" ec2-user@your-ec2-ip
```

# 2. AWS EC2 インスタンスへの アプリケーションのデプロイ手順

## (1) プロジェクトをクローンする

最初に、EC2 インスタンスに SSH 接続し、GitHub からプロジェクトをクローンします：

```git
git clone https://github.com/QueueCorpJP/Chatbot-Frontend.git
cd Chatbot-Frontend
```

## (2) 依存関係のインストールとビルド

必要なパッケージをインストールし、ビルドを行います。

```bash
npm install
npm run build
```

## (3) ビルドされたファイルを Nginx ディレクトリに移動

dist/ ディレクトリ（ビルド結果）を Nginx のルートディレクトリに移動します。

```bash
sudo mv dist/ /var/www/chatbot-frontend
```

## (4) パーミッションの設定

Nginx が正しくファイルを読み込めるように、所有権とパーミッションを設定します。

```bash
sudo chown -R nginx:nginx /var/www/chatbot-frontend
sudo chmod -R 755 /var/www/chatbot-frontend
```

## (5) Nginx の設定

- Nginx の設定を編集：

```bash
sudo nano /etc/nginx/nginx.conf
```

- Nginx の設定ファイルを編集し、フロントエンドが正しく配信されるようにします。

```nginx
server {
    listen 80;
    server_name your_domain_or_ip;

    location /chatbot-frontend {
        root /var/www/;
        index index.html;
        try_files $uri $uri/ /chatbot-frontend/index.html;  # Fallback to index.html for SPA
    }

    location /assets/ {
        alias /var/www/chatbot-frontend/assets/;
    }

    location /images/ {
        alias /var/www/chatbot-frontend/images/;
    }
}
```

your_domain_or_ip を実際のドメイン名または EC2 のパブリック IP に置き換えてください。

## (6) Nginx 設定の確認

Nginx の設定が正しいかを確認します。

```bash
sudo nginx -t
```

## (7) Nginx の再起動

Nginx を再起動して設定を反映します。

```bash
sudo systemctl restart nginx
```

### デプロイ完了！

フロントエンドは以下の URL でアクセスできるようになります：
http://your_domain_or_ip/chatbot-frontend
