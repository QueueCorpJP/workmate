#!/bin/bash

# QAT (Quality Assurance Testing) 実行スクリプト
# 全種類のテストを順次実行し、レポートを生成

set -e

# 色付きログ関数
log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

log_warning() {
    echo -e "\033[33m[WARNING]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# 環境設定
export ENVIRONMENT=test
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# レポートディレクトリ作成
mkdir -p reports
mkdir -p htmlcov

log_info "QAT (Quality Assurance Testing) を開始します..."

# テスト環境の準備
log_info "テスト環境を準備中..."
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.test.yml up -d
    log_info "テスト用データベースが起動しました"
    sleep 10  # データベース起動待機
else
    log_warning "Docker Composeが見つかりません。ローカル環境でテストを実行します。"
fi

# 依存関係インストール
log_info "テスト依存関係をインストール中..."
pip install -r requirements-test.txt

# 1. 単体テスト実行
log_info "===================="
log_info "単体テスト実行中..."
log_info "===================="
pytest tests/unit/ -v -m unit --tb=short --cov=modules --cov-report=term-missing

if [ $? -eq 0 ]; then
    log_info "単体テスト: 成功"
else
    log_error "単体テスト: 失敗"
    exit 1
fi

# 2. 統合テスト実行
log_info "======================"
log_info "統合テスト実行中..."
log_info "======================"
pytest tests/integration/ -v -m integration --tb=short

if [ $? -eq 0 ]; then
    log_info "統合テスト: 成功"
else
    log_error "統合テスト: 失敗"
    exit 1
fi

# 3. APIテスト実行
log_info "=================="
log_info "APIテスト実行中..."
log_info "=================="
pytest tests/api/ -v -m api --tb=short

if [ $? -eq 0 ]; then
    log_info "APIテスト: 成功"
else
    log_error "APIテスト: 失敗"
    exit 1
fi

# 4. セキュリティテスト実行
log_info "========================"
log_info "セキュリティテスト実行中..."
log_info "========================"
pytest tests/security/ -v -m security --tb=short

if [ $? -eq 0 ]; then
    log_info "セキュリティテスト: 成功"
else
    log_error "セキュリティテスト: 失敗"
    exit 1
fi

# 5. パフォーマンステスト実行
log_info "============================"
log_info "パフォーマンステスト実行中..."
log_info "============================"
pytest tests/performance/ -v -m performance --tb=short

if [ $? -eq 0 ]; then
    log_info "パフォーマンステスト: 成功"
else
    log_warning "パフォーマンステスト: 警告あり（継続）"
fi

# 6. E2Eテスト実行
log_info "===================="
log_info "E2Eテスト実行中..."
log_info "===================="
pytest tests/e2e/ -v -m e2e --tb=short

if [ $? -eq 0 ]; then
    log_info "E2Eテスト: 成功"
else
    log_warning "E2Eテスト: 警告あり（継続）"
fi

# 7. 全テスト実行（詳細レポート生成）
log_info "=========================="
log_info "全テスト実行とレポート生成..."
log_info "=========================="
pytest tests/ -v --tb=short \
    --cov=modules \
    --cov-report=html:htmlcov \
    --cov-report=xml:reports/coverage.xml \
    --cov-report=term-missing \
    --html=reports/test_report.html \
    --self-contained-html \
    --json-report --json-report-file=reports/test_report.json

# 8. テストカバレッジ確認
log_info "===================="
log_info "カバレッジ結果確認..."
log_info "===================="
coverage report --show-missing

# カバレッジが80%未満の場合は警告
COVERAGE=$(coverage report | tail -1 | awk '{print $4}' | sed 's/%//')
if [ "$COVERAGE" -lt 80 ]; then
    log_warning "コードカバレッジが80%未満です: ${COVERAGE}%"
else
    log_info "コードカバレッジ: ${COVERAGE}%"
fi

# 9. テスト結果サマリー生成
log_info "==================="
log_info "テスト結果サマリー"
log_info "==================="

echo "QAT実行完了: $(date)" > reports/test_summary.txt
echo "カバレッジ: ${COVERAGE}%" >> reports/test_summary.txt
echo "" >> reports/test_summary.txt

# JSONレポートからテスト結果を抽出
if [ -f "reports/test_report.json" ]; then
    python3 -c "
import json
with open('reports/test_report.json', 'r') as f:
    data = json.load(f)
    
print(f\"総テスト数: {data['summary']['total']}\")
print(f\"成功: {data['summary']['passed']}\")
print(f\"失敗: {data['summary']['failed']}\")
print(f\"スキップ: {data['summary']['skipped']}\")
print(f\"実行時間: {data['duration']:.2f}秒\")
" >> reports/test_summary.txt
fi

cat reports/test_summary.txt

# 10. クリーンアップ
log_info "環境クリーンアップ中..."
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.test.yml down
    log_info "テスト環境をクリーンアップしました"
fi

log_info "================================"
log_info "QAT実行完了!"
log_info "レポートは以下で確認できます:"
log_info "- HTML: htmlcov/index.html"
log_info "- テストレポート: reports/test_report.html"
log_info "- サマリー: reports/test_summary.txt"
log_info "================================"

exit 0