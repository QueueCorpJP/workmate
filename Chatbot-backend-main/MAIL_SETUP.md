# WorkMate メール設定ガイド

## 概要
WorkMateは、アカウント作成時にユーザーにメール通知を送信する機能を提供します。
メール送信にはResend APIを使用しています。

## 現在の設定
- 送信元アドレス: `queue@queue-tech.jp`（認証済み）
- 任意のメールアドレスに送信可能

## 設定方法

### 1. 環境変数の設定

```bash
# 必須の環境変数
RESEND_API_KEY=your_resend_api_key
FRONTEND_URL=https://workmatechat.com

# オプション
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 2. 現在の動作
- `queue@queue-tech.jp` から任意のメールアドレスに送信可能
- ドメイン認証済みのため、制限なし

## テスト方法

```bash
# バックエンドディレクトリで実行
cd Chatbot-backend-main
python test_email.py
```

## トラブルシューティング

### エラー: "validation_error" (403)
- 原因: Resend APIキーが無効、または認証に問題がある
- 解決策: RESEND_API_KEYが正しく設定されているか確認

### エラー: "RESEND_API_KEY が未設定"
- 原因: 環境変数が設定されていない
- 解決策: `.env` ファイルまたは環境変数を設定

## 参考リンク
- [Resend API Documentation](https://resend.com/docs)
- [Resend Domain Verification](https://resend.com/domains) 