# Elasticsearch Fuzzy Search クイックスタート

## 🚀 5分で始める手順

### 1. Elasticsearchを起動

```bash
# Docker Composeで起動
cd Chatbot-backend-main
docker-compose -f docker-compose.elasticsearch.yml up -d
```

### 2. 依存関係をインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数を設定

`.env`ファイルに追加：

```bash
# Elasticsearch設定
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_SCHEME=http
ELASTICSEARCH_INDEX=workmate_documents
```

### 4. テスト実行

```bash
python test_elasticsearch.py
```

## 🔍 基本的な使用例

```python
from modules.elasticsearch_search import get_elasticsearch_fuzzy_search

# Fuzzy Search
es_search = get_elasticsearch_fuzzy_search()
results = await es_search.fuzzy_search(
    query="パソコン",
    fuzziness="AUTO",
    limit=10
)

# 結果表示
for result in results:
    print(f"📄 {result['document_name']}")
    print(f"🎯 スコア: {result['similarity_score']:.2f}")
    print(f"📝 内容: {result['content'][:100]}...")
    print()
```

## 🎯 Fuzziness設定

| 設定 | 説明 | 使用例 |
|------|------|--------|
| `"AUTO"` | 自動調整（推奨） | `fuzziness="AUTO"` |
| `"0"` | 完全一致のみ | `fuzziness="0"` |
| `"1"` | 1文字違いまで許容 | `fuzziness="1"` |
| `"2"` | 2文字違いまで許容 | `fuzziness="2"` |

## 📊 検索タイプ

| タイプ | 説明 | 適用場面 |
|--------|------|----------|
| `multi_match` | 複数フィールド検索 | 一般的な検索 |
| `phrase` | フレーズ検索 | 完全な文章検索 |
| `wildcard` | ワイルドカード検索 | 部分一致検索 |
| `regex` | 正規表現検索 | 高度なパターン検索 |

## 🔧 統合システム

```python
from modules.chat_search_systems import elasticsearch_fuzzy_search_system

# チャット検索システム経由
results = await elasticsearch_fuzzy_search_system(
    query="安いパソコン",
    company_id="your_company_id",
    fuzziness="AUTO",
    limit=10
)
```

## 📝 データ同期

```python
from modules.elasticsearch_search import get_elasticsearch_manager

# データベースからElasticsearchに同期
es_manager = get_elasticsearch_manager()
await es_manager.sync_database_to_elasticsearch()
```

## 🎉 完了！

これで、ElasticsearchのFuzzy Search機能が使用できます。

詳細な設定は `ELASTICSEARCH_SETUP.md` を参照してください。 