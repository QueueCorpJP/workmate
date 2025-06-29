# Top-K拡大による検索精度向上対応

## 問題の概要

「貸倒解放に伴い、ISPを再発行した会社は？」という質問に対して、時々正しい答え（株式会社 MITSUKI）が返されるが、時々「見当たりませんでした」という回答になってしまう不安定さがありました。

## 原因分析

ベクトル検索システムでのTop-K（取得する類似チャンク数）の値が小さすぎることが原因でした。従来の設定では、関連する情報が検索結果の上位に含まれない場合があり、結果として「見つからない」という回答になっていました。

## 実施した修正

### 1. リアルタイムRAGシステム (`modules/realtime_rag.py`)
- `step3_similarity_search`: `top_k=10` → `top_k=20`
- `process_realtime_rag`: `top_k=10` → `top_k=20`
- `process_question_realtime`: `top_k=10` → `top_k=20`

### 2. ベクトル検索システム (`modules/vector_search.py`)
- `vector_similarity_search`: `limit=5` → `limit=20`
- `get_document_content_by_similarity`: `max_results=10` → `max_results=20`

### 3. 並列ベクトル検索システム (`modules/parallel_vector_search.py`)
- `parallel_comprehensive_search`: `max_results=15` → `max_results=25`

### 4. チャットモジュール (`modules/chat.py`)
- `realtime_rag_search`: リアルタイムRAG呼び出し時に `top_k=max_results * 2` に設定
- `simple_rag_search_fallback`: `max_results=5` → `max_results=20`
- フォールバック検索での重複拡大を削除（`max_results * 2` → `max_results`）

## 期待される効果

1. **検索精度の向上**: より多くの候補チャンクを検索することで、関連情報を見逃すリスクが大幅に減少
2. **回答の安定性向上**: 同じ質問に対して一貫した回答が得られるように
3. **情報の網羅性向上**: より幅広い関連情報から最適な回答を生成

## 技術的詳細

### 修正前の設定
- リアルタイムRAG: Top-K = 10
- ベクトル検索: Limit = 5, Max Results = 10
- 並列検索: Max Results = 15
- フォールバック: Max Results = 5

### 修正後の設定
- リアルタイムRAG: Top-K = 20
- ベクトル検索: Limit = 20, Max Results = 20
- 並列検索: Max Results = 25
- フォールバック: Max Results = 20

## 注意事項

1. **パフォーマンス**: より多くのチャンクを処理するため、若干の処理時間増加が予想されます
2. **コスト**: LLMへの入力トークン数が増加する可能性があります
3. **メモリ使用量**: より多くのデータを一時的に保持するため、メモリ使用量が増加します

## 検証方法

以下の質問で検証を行ってください：

```
質問: 貸倒解放に伴い、ISPを再発行した会社は？
期待される回答: 株式会社 MITSUKI
```

この質問を複数回実行して、一貫して正しい回答が得られることを確認してください。

## 実装日時

2025年6月30日 00:01 (JST)

## 関連ファイル

- `modules/realtime_rag.py`
- `modules/vector_search.py`
- `modules/parallel_vector_search.py`
- `modules/chat.py`