#!/bin/bash

echo "=== WorkMate バックエンドサーバー診断 ==="
echo "実行時刻: $(date)"
echo ""

echo "1. システム情報"
echo "   OS: $(uname -a)"
echo "   Python: $(python3 --version 2>/dev/null || echo 'Python3が見つかりません')"
echo "   作業ディレクトリ: $(pwd)"
echo ""

echo "2. PM2プロセス状況"
if command -v pm2 >/dev/null 2>&1; then
    pm2 list
    echo ""
    echo "PM2ログ (最新10行):"
    pm2 logs chatbot-backend --lines 10 --nostream 2>/dev/null || echo "ログが見つかりません"
else
    echo "   PM2がインストールされていません"
fi
echo ""

echo "3. Pythonプロセス確認"
ps aux | grep -E '(python|main\.py|uvicorn)' | grep -v grep || echo "   Pythonプロセスが見つかりません"
echo ""

echo "4. ポート使用状況"
echo "   ポート8083:"
netstat -tlnp 2>/dev/null | grep :8083 || echo "   ポート8083は使用されていません"
echo "   すべてのWebサーバーポート:"
netstat -tlnp 2>/dev/null | grep -E ':(80|443|8000|8080|8083|3000)' || echo "   Webサーバーポートが見つかりません"
echo ""

echo "5. ファイル確認"
echo "   main.py: $([ -f main.py ] && echo '存在' || echo '見つかりません')"
echo "   .env: $([ -f .env ] && echo '存在' || echo '見つかりません')"
echo "   requirements.txt: $([ -f requirements.txt ] && echo '存在' || echo '見つかりません')"
echo "   venv: $([ -d venv ] && echo '存在' || echo '見つかりません')"
echo ""

echo "6. 環境変数"
echo "   PORT: ${PORT:-'未設定'}"
echo "   ENVIRONMENT: ${ENVIRONMENT:-'未設定'}"
echo "   GOOGLE_API_KEY: $([ -n "$GOOGLE_API_KEY" ] && echo '設定済み' || echo '未設定')"
echo ""

echo "7. ディスク容量"
df -h . 2>/dev/null || echo "   ディスク情報を取得できません"
echo ""

echo "8. 最近のエラーログ"
if [ -f "/home/ec2-user/.pm2/logs/chatbot-backend-error.log" ]; then
    echo "   PM2エラーログ (最新5行):"
    tail -5 /home/ec2-user/.pm2/logs/chatbot-backend-error.log 2>/dev/null || echo "   ログを読み取れません"
else
    echo "   PM2エラーログが見つかりません"
fi
echo ""

echo "9. 手動起動テスト"
echo "   Pythonでの直接起動テスト:"
if [ -f "main.py" ] && [ -d "venv" ]; then
    timeout 5s ./venv/bin/python -c "
import sys
sys.path.insert(0, '.')
try:
    from main import app
    print('   ✅ main.pyのインポート成功')
except Exception as e:
    print(f'   ❌ main.pyのインポートエラー: {e}')
    
try:
    from modules.config import get_port
    port = get_port()
    print(f'   ✅ ポート設定: {port}')
except Exception as e:
    print(f'   ❌ ポート設定エラー: {e}')
" 2>/dev/null || echo "   テスト実行できませんでした"
else
    echo "   必要なファイルが見つかりません"
fi
echo ""

echo "=== 診断完了 ==="
echo ""
echo "推奨対処法:"
echo "1. PM2でプロセスが起動していない場合:"
echo "   pm2 start ecosystem.config.js"
echo ""
echo "2. ポート8083が使用されていない場合:"
echo "   pm2 restart chatbot-backend"
echo ""
echo "3. エラーがある場合:"
echo "   pm2 logs chatbot-backend"
echo ""
echo "4. 手動起動テスト:"
echo "   cd /home/ec2-user/workmate/Chatbot-backend-main"
echo "   source venv/bin/activate"
echo "   python main.py" 