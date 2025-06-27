# ベクトル検索精度改善レポート

## 問題の特定

ユーザーから報告された「質問したときに情報があるのにないとか精度が著しく落ちてる」という問題について、以下の原因を特定しました：

### 1. 類似度閾値の問題
- **問題**: 現在の類似度閾値（0.02-0.2）が低すぎて、低品質な結果も含まれていた
- **影響**: 関連性の低い情報が回答に含まれ、精度が低下

### 2. 検索結果の重み付け不適切
- **問題**: 異なる検索手法（BM25、セマンティック検索）の結果が適切に統合されていない
- **影響**: 最適でない結果が上位に表示される

### 3. チャンク化戦略の最適化不足
- **問題**: 文書の構造を考慮したチャンク化が不十分
- **影響**: 文脈が分断され、重要な情報が見つからない

### 4. 並列検索での重複処理
- **問題**: 複数の検索戦略で同じ結果が重複している
- **影響**: 処理効率の低下と結果の偏り

## 実装した改善策

### 1. 強化されたベクトル検索システム (`vector_search_enhanced.py`)

#### 主な改善点：
- **適応的類似度閾値**: 検索結果の統計に基づいて動的に閾値を調整
- **品質スコアリング**: コンテンツの品質を多角的に評価
- **コンテキスト考慮**: 前後のチャンクを考慮した関連度計算
- **重複除去**: 同一文書からの結果数制限と内容重複の除去

#### 技術的特徴：
```python
# 適応的閾値計算
def calculate_adaptive_threshold(self, similarities: List[float]) -> float:
    top_quarter = similarities[:max(1, len(similarities) // 4)]
    avg_top = sum(top_quarter) / len(top_quarter)
    adaptive_threshold = max(self.min_similarity_threshold, avg_top * 0.6)
    return adaptive_threshold

# 品質スコア計算
def calculate_quality_score(self, content: str, query: str) -> float:
    # 長さ、キーワード含有率、構造的要素を総合評価
    quality_score = 0.0
    # 1. 長さによる品質評価
    # 2. クエリ用語の含有率
    # 3. 構造的要素の存在
    # 4. 情報密度
    return min(quality_score, 1.0)
```

### 2. 強化されたリアルタイムRAGシステム (`realtime_rag_enhanced.py`)

#### 主な改善点：
- **質問タイプ分析**: 質問の種類に応じた最適化された処理
- **キーワード抽出**: 重要語の自動抽出と重み付け
- **コンテキスト最適化**: 質問タイプに応じたコンテキスト構築
- **回答品質評価**: 生成された回答の品質を自動評価

#### 処理フロー：
```
Step 1: 質問入力と分析 (質問タイプ、キーワード抽出)
    ↓
Step 2: 強化ベクトル検索 (適応的閾値、品質評価)
    ↓
Step 3: コンテキスト最適化 (多様性確保、構造化)
    ↓
Step 4: 強化回答生成 (タイプ別プロンプト、品質改善)
    ↓
Step 5: 回答最終化 (メタデータ付与)
```

### 3. パフォーマンス最適化

#### 改善された指標：
- **最小類似度閾値**: 0.02 → 0.3 (15倍向上)
- **コンテキスト長**: 50,000文字 → 120,000文字 (2.4倍増加)
- **品質評価**: 新規実装（長さ、キーワード、構造、情報密度）
- **多様性確保**: 同一文書からの結果を最大3件に制限

## 設定パラメータ

### ベクトル検索システム
```python
self.min_similarity_threshold = 0.3  # 最小類似度閾値
self.adaptive_threshold_enabled = True  # 適応的閾値有効
self.context_window_size = 3  # 前後チャンク考慮範囲
self.quality_weight = 0.3  # 品質スコア重み
self.similarity_weight = 0.4  # 類似度重み
self.context_weight = 0.3  # コンテキスト重み
```

### RAGシステム
```python
self.max_context_length = 120000  # 最大コンテキスト長
self.min_chunk_relevance = 0.4  # 最小チャンク関連度
self.context_diversity_threshold = 0.7  # 多様性閾値
```

## 使用方法

### 1. 強化ベクトル検索の使用
```python
from modules.vector_search_enhanced import get_enhanced_vector_search_instance

search_system = get_enhanced_vector_search_instance()
results = await search_system.enhanced_vector_search(
    query="料金について教えてください",
    company_id="your_company_id",
    max_results=15
)
```

### 2. 強化リアルタイムRAGの使用
```python
from modules.realtime_rag_enhanced import process_question_enhanced_realtime

result = await process_question_enhanced_realtime(
    question="申し込み方法を教えてください",
    company_id="your_company_id",
    company_name="お客様の会社",
    top_k=15
)
```

## テスト方法

強化システムのテストを実行：
```bash
cd workmate/Chatbot-backend-main
python test_enhanced_vector_search.py
```

## 期待される改善効果

### 1. 検索精度の向上
- **適応的閾値**: 検索結果の品質に応じた動的調整
- **品質評価**: 多角的な品質指標による結果フィルタリング
- **コンテキスト考慮**: 前後の文脈を考慮した関連度計算

### 2. 回答品質の向上
- **質問タイプ別最適化**: 手順、情報、問題解決等に応じた処理
- **構造化回答**: 番号付きリスト、箇条書き等の構造的要素
- **品質自動改善**: 低品質回答の自動検出と改善試行

### 3. システム効率の向上
- **重複除去**: 同一内容の結果を効率的に除去
- **多様性確保**: 異なる文書からバランス良く情報を取得
- **処理時間最適化**: 並列処理と効率的なアルゴリズム

## 互換性

- **既存システムとの併用**: 元のシステムはそのまま残し、段階的移行が可能
- **フォールバック機能**: 強化システムが利用できない場合の自動切り替え
- **設定の柔軟性**: 各種パラメータの調整が容易

## 今後の改善予定

1. **機械学習による品質評価**: より高度な品質評価モデルの導入
2. **ユーザーフィードバック統合**: 回答評価に基づく学習機能
3. **リアルタイム性能監視**: 検索精度と処理時間のモニタリング
4. **A/Bテスト機能**: 異なる設定での性能比較

## 結論

本改善により、ベクトル検索の精度が大幅に向上し、「情報があるのに見つからない」という問題が解決されることが期待されます。適応的閾値、品質評価、コンテキスト考慮等の多角的なアプローチにより、より正確で有用な回答を提供できるようになります。

---

**作成日**: 2025年6月27日  
**バージョン**: v2.0  
**対象システム**: Workmate Chatbot Backend