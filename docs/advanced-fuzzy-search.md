# 高度ファジー検索システム

## 概要

ワークメイトシステムに新しく実装された高度なPostgreSQLファジー検索システムです。`normalize_text()`関数と文字数差を考慮したスコア計算により、より精密な検索結果を提供します。

## 実装内容

ご質問いただいたPostgreSQLクエリの改良版を実装：

```sql
WITH normalized AS (
  SELECT
    *,
    normalize_text(content) AS norm_content,
    normalize_text(:query)  AS norm_query
  FROM chunks
  WHERE company_id = :company_id
)
SELECT *,
  similarity(norm_content, norm_query) AS sim,
  abs(length(norm_content) - length(norm_query)) AS len_diff,
  (
    similarity(norm_content, norm_query)
    - 0.012 * abs(length(norm_content) - length(norm_query))
    + CASE
        WHEN norm_content = norm_query THEN 0.4
        WHEN norm_content LIKE norm_query || '%' THEN 0.2
        ELSE 0
      END
  ) AS final_score
FROM normalized
WHERE similarity(norm_content, norm_query) > 0.45
ORDER BY final_score DESC
LIMIT 50;
```

## 主要機能

### 1. テキスト正規化（`normalize_text()`関数）

- **大文字小文字統一**: すべて小文字に変換
- **全角英数字→半角変換**: ＡＢＣ → ABC, １２３ → 123
- **会社形態統一**: 
  - 株式会社 → (株)
  - ㈱ → (株)
  - かぶしきがいしゃ → (株)
  - ｶﾌﾞｼｷｶﾞｲｼｬ → (株)
  - 有限会社 → (有)
  - 合同会社 → (同)
- **特殊文字統一**: （） → (), － → -, 〜 → ~
- **空白文字正規化**: 連続する空白を単一スペースに統一

### 2. 高度スコア計算

- **基本類似度**: PostgreSQL trigram類似度
- **文字数差ペナルティ**: `abs(length(正規化テキスト1) - length(正規化テキスト2))`
- **完全一致ブースト**: 正規化後の完全一致で+0.4点
- **前方一致ブースト**: 正規化後の前方一致で+0.2点
- **最終スコア**: `類似度 - (0.012 × 文字数差) + ボーナス`
- **動的閾値フィルタリング**: 指定したスコア以上の結果のみ返却

### 3. パフォーマンス最適化

- **WITH句による効率化**: 正規化処理を一度だけ実行
- **正規化テキスト用GINインデックス**: 高速trigram検索
- **文字数インデックス**: 長さベースの絞り込み最適化
- **関数のIMMUTABLE指定**: クエリ最適化対応

## 使用方法

### Python APIの使用

```python
from modules.advanced_fuzzy_search import advanced_fuzzy_search

# 基本的な使用
results = await advanced_fuzzy_search(
    query="株式会社テスト",
    threshold=0.45,
    length_penalty=0.012,
    limit=50
)

# 会社IDでフィルタリング
results = await advanced_fuzzy_search(
    query="連絡先",
    company_id="company_123",
    threshold=0.4,
    limit=10
)

# ペナルティ係数の調整
results = await advanced_fuzzy_search(
    query="電話番号",
    threshold=0.3,
    length_penalty=0.008,  # より緩いペナルティ
    limit=30
)
```

### レスポンス形式

```python
{
    'chunk_id': 'chunk_12345',
    'doc_id': 'doc_67890',
    'content': '検索対象のテキスト内容...',
    'document_name': 'ファイル名.pdf',
    'document_type': 'pdf',
    'similarity_score': 0.8245,      # 基本類似度
    'length_diff': 15,               # 文字数差
    'final_score': 0.7945,           # 最終スコア
    'normalized_content': '正規化されたテキスト',
    'normalized_query': '正規化されたクエリ',
    'chunk_index': 3,
    'company_id': 'company_123',
    'search_method': 'advanced_fuzzy_search'
}
```

### 直接SQLクエリの使用

```sql
-- PostgreSQL関数を直接使用
SELECT 
    content,
    normalize_text(content) as normalized_content,
    similarity(normalize_text(content), normalize_text('検索クエリ')) AS sim,
    abs(length(normalize_text(content)) - length(normalize_text('検索クエリ'))) AS len_diff,
    calculate_advanced_fuzzy_score(content, '検索クエリ', 1.0, 0.02) AS final_score
FROM chunks
WHERE calculate_advanced_fuzzy_score(content, '検索クエリ') > 0.45
ORDER BY final_score DESC
LIMIT 20;
```

## パラメータ調整ガイド

### threshold（閾値）
- **0.3-0.4**: 広範囲検索（多くの結果、精度は中程度）
- **0.45**: 推奨設定（バランスの取れた結果）
- **0.5-0.7**: 高精度検索（少数の高品質結果）

### length_penalty（文字数差ペナルティ）
- **0.008**: 軽いペナルティ（文字数差をあまり重視しない）
- **0.012**: 推奨設定（適度なペナルティ）
- **0.02**: 重いペナルティ（文字数差を重視）

## テスト方法

```bash
# 高度ファジー検索システムのテスト実行
python test_advanced_fuzzy_search.py
```

テストでは以下を確認：
1. `normalize_text()`関数の動作
2. 各種パラメータでの検索実行
3. 類似度分布分析
4. ご質問のクエリと同等の実行

## 初期設定

システム初回使用時に自動で以下が実行されます：

1. **PostgreSQL拡張の有効化**
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   ```

2. **関数の作成**
   - `normalize_text(input_text TEXT)`: テキスト正規化
   - `calculate_advanced_fuzzy_score(...)`: 高度スコア計算

3. **インデックスの作成**
   - 正規化テキスト用GINインデックス
   - 文字数インデックス

## 既存システムとの統合

高度ファジー検索は既存のワークメイト検索システムと並行して動作します：

- **Realtime RAG**: 従来のベクトル検索
- **Ultra Accurate RAG**: 意図ベース検索
- **Best Score Search**: 複数手法統合検索
- **Advanced Fuzzy Search**: 🆕 高度PostgreSQLファジー検索

## パフォーマンス特徴

- **高速**: PostgreSQL内でのネイティブ処理
- **正確**: テキスト正規化による表記揺れ対応
- **柔軟**: 文字数差を考慮した精密スコアリング
- **拡張可能**: パラメータ調整で様々な用途に対応

## ログ出力

検索実行時の詳細ログ例：
```
🔍 高度ファジー検索開始: '株式会社テスト' (閾値: 0.45, ペナルティ: 0.02)
✅ 高度ファジー検索完了: 8件の結果
📊 検索結果詳細:
  1. 会社情報.pdf - 最終スコア: 0.7245
      類似度: 0.8245, 文字数差: 5
      内容: 株式会社テストは東京都に本社を置く...
```

## 技術仕様

- **使用拡張**: pg_trgm（PostgreSQL Trigram）
- **対応言語**: 日本語、英語、数字
- **最小文字数**: 10文字以上のチャンクを対象
- **関数言語**: PL/pgSQL
- **インデックス**: GIN（Generalized Inverted Index）

---

## まとめ

ご質問いただいた高度なPostgreSQLファジー検索クエリが完全に実装され、ワークメイトシステムで利用可能になりました。`normalize_text()`関数による正規化と文字数差を考慮したスコア計算により、より精密で実用的な検索結果を提供します。 