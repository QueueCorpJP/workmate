# 🧠 バッチエンベディングシステム ガイド

## 概要

新しいバッチエンベディングシステムは、チャンクを10件ずつまとめてバッチで送信し、APIの負荷軽減とレート制限（429エラー）の回避を実現します。また、エラー回復機能により、確実にembeddingを完了させることができます。

## 主な特徴

### 🚀 バッチ処理
- **10件ずつのバッチ処理**: チャンクを10件ずつまとめて処理
- **API負荷軽減**: 個別処理から一括処理への変更
- **レート制限対策**: 適切な待機時間とリトライ機能

### 🔄 エラー回復機能
- **自動リトライ**: 失敗したチャンクを自動的に再処理
- **指数バックオフ**: レート制限時の適応的待機
- **失敗チャンク追跡**: エラーになったチャンクのみを対象とした再実行

### 📊 進捗管理
- **リアルタイム進捗表示**: 処理状況の可視化
- **詳細統計**: 成功率、処理時間、エラー数の追跡
- **ログ出力**: 詳細なログファイル生成

## ファイル構成

```
workmate/Chatbot-backend-main/
├── modules/
│   └── batch_embedding.py              # バッチエンベディング生成モジュール
├── batch_embedding_processor.py        # スタンドアロン処理スクリプト
├── test_batch_embedding.py            # テストスクリプト
├── fix_missing_embeddings.py          # 修復スクリプト（バッチ対応）
└── BATCH_EMBEDDING_GUIDE.md           # このガイド
```

## 使用方法

### 1. 自動バッチ処理（ファイルアップロード時）

ファイルアップロード後、自動的にバッチエンベディング生成が実行されます：

```python
# modules/knowledge/api.py で自動実行
from ..batch_embedding import batch_generate_embeddings_for_document

# チャンク保存後に自動実行
embedding_success = await batch_generate_embeddings_for_document(doc_id, len(chunks_list))
```

### 2. スタンドアロンスクリプト

#### 全ての未処理チャンクを処理
```bash
python batch_embedding_processor.py
```

#### 処理数を制限
```bash
python batch_embedding_processor.py --limit 100
```

#### 特定のドキュメントのみ処理
```bash
python batch_embedding_processor.py --doc-id abc123-def456-ghi789
```

#### 失敗したチャンクのみ再処理
```bash
python batch_embedding_processor.py --retry-only
```

#### 処理状況の確認
```bash
python batch_embedding_processor.py --status
```

### 3. プログラムからの呼び出し

```python
from modules.batch_embedding import batch_generate_embeddings_for_document, batch_generate_embeddings_for_all_pending

# 特定ドキュメントの処理
success = await batch_generate_embeddings_for_document(doc_id, max_chunks)

# 全未処理チャンクの処理
success = await batch_generate_embeddings_for_all_pending(limit=100)
```

## 設定

### 環境変数

```bash
# 必須設定
GOOGLE_API_KEY=your_gemini_api_key
AUTO_GENERATE_EMBEDDINGS=true

# オプション設定
EMBEDDING_MODEL=models/text-embedding-004
```

### バッチ処理パラメータ

```python
# modules/batch_embedding.py で設定可能
class BatchEmbeddingGenerator:
    def __init__(self):
        self.batch_size = 10      # バッチサイズ（10件ずつ）
        self.max_retries = 3      # 最大リトライ回数
        self.retry_delay = 2      # リトライ間隔（秒）
        self.api_delay = 1        # API呼び出し間隔（秒）
```

## エラー処理フロー

### 1. 初回バッチ処理
```
チャンク取得 → 10件ずつバッチ処理 → 成功/失敗を記録
```

### 2. エラー回復処理
```
失敗チャンク収集 → 5件ずつ再処理 → 最終結果確認
```

### 3. レート制限対応
```
429エラー検出 → 指数バックオフ待機 → 自動リトライ
```

## ログ出力例

```
2025-06-26 18:55:00 - INFO - 🧠 バッチエンベディング生成開始: test_document.pdf
2025-06-26 18:55:01 - INFO - 📋 45個のチャンクをバッチ処理します
2025-06-26 18:55:02 - INFO - 📦 バッチ 1/5 処理開始 (10チャンク)
2025-06-26 18:55:05 - INFO - 📊 バッチ進捗: 1/5 | 成功: 10 | 失敗: 0 | 経過時間: 3.2秒
2025-06-26 18:55:10 - INFO - 🎉 バッチエンベディング生成完了 - 最終統計
2025-06-26 18:55:10 - INFO - 📊 総チャンク数: 45
2025-06-26 18:55:10 - INFO - ✅ 成功: 43
2025-06-26 18:55:10 - INFO - ❌ 失敗: 2
2025-06-26 18:55:10 - INFO - 📈 成功率: 95.6%
```

## パフォーマンス比較

### 従来システム vs バッチシステム

| 項目 | 従来システム | バッチシステム |
|------|-------------|---------------|
| 処理方式 | 1件ずつ個別処理 | 10件ずつバッチ処理 |
| API呼び出し回数 | チャンク数と同じ | チャンク数 ÷ 10 |
| レート制限リスク | 高い | 低い |
| エラー回復 | 手動 | 自動 |
| 進捗可視化 | 限定的 | 詳細 |
| 処理速度 | 遅い | 高速 |

### 期待される改善効果

- **API呼び出し回数**: 90%削減
- **レート制限エラー**: 大幅減少
- **処理時間**: 30-50%短縮
- **成功率**: 95%以上

## トラブルシューティング

### よくある問題と解決方法

#### 1. レート制限エラー（429）
```bash
# 解決方法: バッチサイズを小さくする
# modules/batch_embedding.py で batch_size を 5 に変更
```

#### 2. メモリ不足
```bash
# 解決方法: 処理制限を設ける
python batch_embedding_processor.py --limit 50
```

#### 3. 一部チャンクの処理失敗
```bash
# 解決方法: 失敗チャンクのみ再処理
python batch_embedding_processor.py --retry-only
```

#### 4. 環境変数未設定
```bash
# 解決方法: .env ファイルを確認
AUTO_GENERATE_EMBEDDINGS=true
GOOGLE_API_KEY=your_api_key
```

## テスト方法

### 1. システムテスト
```bash
python test_batch_embedding.py
```

### 2. 小規模テスト
```bash
python batch_embedding_processor.py --limit 10
```

### 3. 状況確認
```bash
python batch_embedding_processor.py --status
```

## 監視とメンテナンス

### 定期的な確認項目

1. **未処理チャンク数の監視**
   ```bash
   python batch_embedding_processor.py --status
   ```

2. **ログファイルの確認**
   ```bash
   tail -f batch_embedding.log
   ```

3. **エラー率の監視**
   - 成功率が90%を下回る場合は調査が必要

4. **API使用量の監視**
   - Gemini APIの使用量とレート制限の確認

## 今後の拡張予定

### Phase 2: 高度な最適化
- **動的バッチサイズ**: API応答時間に基づく自動調整
- **並列処理**: 複数バッチの同時実行
- **キャッシュ機能**: 重複コンテンツの検出と再利用

### Phase 3: 運用支援
- **Webダッシュボード**: 処理状況の可視化
- **アラート機能**: エラー率上昇時の通知
- **自動スケジューリング**: 定期的な未処理チャンク処理

## サポート

問題が発生した場合は、以下の情報を含めてお問い合わせください：

1. エラーメッセージ
2. ログファイル（batch_embedding.log）
3. 実行したコマンド
4. 環境変数設定（API キーは除く）

---

**注意**: このシステムは既存の個別処理システムと併用可能ですが、バッチ処理システムの使用を推奨します。