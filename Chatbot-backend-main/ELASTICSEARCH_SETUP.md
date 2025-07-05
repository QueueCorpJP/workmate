# Elasticsearch + Fuzziness セットアップガイド

## 概要
WorkMateにElasticsearchを統合して、高度なFuzzy Search機能を実装します。

## 🚀 セットアップ手順

### 1. Elasticsearchのインストール

#### Option A: Docker Compose (推奨)
```yaml
# docker-compose.elasticsearch.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: workmate-elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
      - "9300:9300"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - workmate-network

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: workmate-kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    networks:
      - workmate-network

volumes:
  elasticsearch_data:
    driver: local

networks:
  workmate-network:
    driver: bridge
```

#### Option B: ローカルインストール
```bash
# macOS
brew install elasticsearch

# Ubuntu/Debian
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-8.x.list
sudo apt-get update && sudo apt-get install elasticsearch

# Windows
# https://www.elastic.co/downloads/elasticsearch からダウンロード
```

### 2. Elasticsearchの起動

```bash
# Docker Compose使用
docker-compose -f docker-compose.elasticsearch.yml up -d

# ローカルインストール
# macOS/Linux
elasticsearch

# Windows
bin\elasticsearch.bat
```

### 3. 環境変数の設定

`.env`ファイルに以下を追加：

```bash
# Elasticsearch設定
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_SCHEME=http
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASSWORD=changeme
ELASTICSEARCH_INDEX=workmate_documents

# 既存設定は維持
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
DB_PASSWORD=your_db_password
GOOGLE_API_KEY=your_google_api_key
```

### 4. 依存関係のインストール

```bash
cd Chatbot-backend-main
pip install -r requirements.txt
```

### 5. データの同期

```python
# Python実行例
import asyncio
from modules.elasticsearch_search import get_elasticsearch_manager

async def sync_data():
    es_manager = get_elasticsearch_manager()
    if es_manager:
        success = await es_manager.sync_database_to_elasticsearch()
        print(f"データ同期: {'成功' if success else '失敗'}")

# 実行
asyncio.run(sync_data())
```

## 🔍 Fuzzy Search機能

### 基本的な使用方法

```python
from modules.elasticsearch_search import get_elasticsearch_fuzzy_search

# Fuzzy Search実行
es_search = get_elasticsearch_fuzzy_search()
results = await es_search.fuzzy_search(
    query="パソコンの価格",
    company_id="your_company_id",
    fuzziness="AUTO",  # "0", "1", "2", "AUTO"
    limit=10
)
```

### Fuzziness設定

- `"0"`: 完全一致のみ
- `"1"`: 1文字の差を許容
- `"2"`: 2文字の差を許容
- `"AUTO"`: 自動調整（推奨）

### 高度な検索オプション

```python
# 高度な検索
results = await es_search.advanced_search(
    query="安いパソコン",
    company_id="your_company_id",
    search_type="multi_match",  # "phrase", "wildcard", "regex"
    fuzziness="AUTO",
    limit=10
)
```

## 🎯 検索タイプ別の使い分け

### 1. Multi-Match (推奨)
```python
# 複数フィールドでの高度な検索
search_type="multi_match"
```

### 2. Phrase Search
```python
# 完全なフレーズ検索
search_type="phrase"
query="安いパソコンを探している"
```

### 3. Wildcard Search
```python
# ワイルドカード検索
search_type="wildcard"
query="*パソコン*"
```

### 4. Regex Search
```python
# 正規表現検索
search_type="regex"
query="パソコン.*価格"
```

## 🔧 統合システムでの使用

### 既存検索システムとの連携
```python
from modules.chat_search_systems import elasticsearch_fuzzy_search_system

# チャット検索システム経由
results = await elasticsearch_fuzzy_search_system(
    query="パソコンの価格",
    company_id="your_company_id",
    fuzziness="AUTO",
    limit=10
)
```

### フォールバック検索
```python
# 複数システムでの検索（Elasticsearchが優先）
results = await fallback_search_system(
    query="パソコンの価格",
    limit=10
)
```

## 🎛️ 日本語対応

### Kuromoji プラグイン
```bash
# Elasticsearchに日本語解析プラグインをインストール
elasticsearch-plugin install analysis-kuromoji
```

### インデックス設定
システムが自動的に以下の設定を適用：
- `kuromoji_tokenizer`: 日本語形態素解析
- `ngram_analyzer`: N-gram解析
- `japanese_analyzer`: 日本語専用解析

## 📊 パフォーマンス最適化

### インデックス設定
```json
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "analysis": {
      "analyzer": {
        "japanese_analyzer": {
          "tokenizer": "kuromoji_tokenizer",
          "filter": ["kuromoji_baseform", "lowercase"]
        }
      }
    }
  }
}
```

### 検索速度向上のヒント
1. **適切なfuzziness設定**: `AUTO`が最適
2. **フィールドブースト**: 重要なフィールドに重み付け
3. **結果数制限**: 必要な分だけ取得
4. **キャッシュ活用**: 同じクエリの再実行を避ける

## 🔍 トラブルシューティング

### よくある問題

#### 1. Elasticsearch接続エラー
```bash
# 接続確認
curl -X GET "localhost:9200/_cluster/health?pretty"
```

#### 2. インデックスが作成されない
```bash
# インデックス確認
curl -X GET "localhost:9200/_cat/indices?v"
```

#### 3. 検索結果が返らない
```bash
# データ確認
curl -X GET "localhost:9200/workmate_documents/_search?pretty"
```

### ログ確認
```bash
# Elasticsearchログ
docker logs workmate-elasticsearch

# Kibanaログ
docker logs workmate-kibana
```

## 🎯 実際の使用例

### 1. あいまい検索
```python
# 「パソコン」と入力したが「パソコンの」や「PC」も検索
query = "パソコン"
fuzziness = "AUTO"
```

### 2. 表記ゆれ対応
```python
# 「コンピューター」「コンピュータ」「PC」を統一して検索
query = "コンピューター"
fuzziness = "1"
```

### 3. 部分一致検索
```python
# 「安い」を含む文書を検索
query = "安い"
search_type = "wildcard"
```

## 🚀 本番環境での運用

### セキュリティ設定
```yaml
# 本番用docker-compose.yml
environment:
  - xpack.security.enabled=true
  - ELASTIC_PASSWORD=your_secure_password
```

### 監視設定
```yaml
# Kibanaダッシュボード
# - 検索パフォーマンス
# - インデックス使用量
# - エラー率
```

## 🎉 完了

これで、WorkMateにElasticsearchのFuzzy Search機能が統合されました！

### 次のステップ
1. データの同期実行
2. 検索機能のテスト
3. パフォーマンスの最適化
4. 本番環境でのデプロイ 