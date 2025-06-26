# 🔧 Embedding生成問題修正レポート

## 📋 問題の概要
アップロード後にチャンクは作成されるが、embeddingが生成されない問題が発生していました。

## 🔍 根本原因の分析

### 1. 次元数の不一致
- **データベーススキーマ**: `VECTOR(768)` - 768次元を期待
- **実際のembeddingモデル**: `gemini-embedding-exp-03-07` - 3072次元を生成
- **結果**: 次元数の不一致により、embeddingの保存に失敗

### 2. バッチ処理の問題
- [`document_processor.py`](modules/document_processor.py)の`_generate_embeddings_batch()`メソッドで、Gemini APIのレスポンス構造を誤解
- バッチ処理ではなく、個別処理が必要

### 3. モデル設定の不整合
- 複数のファイルで異なるembeddingモデルが指定されていた
- 環境変数の設定が一部のスクリプトで反映されていなかった

## ✅ 実施した修正

### 1. データベーススキーマの更新
```sql
-- 768次元から3072次元に変更
ALTER TABLE chunks DROP COLUMN IF EXISTS embedding;
ALTER TABLE chunks ADD COLUMN embedding VECTOR(3072);
```

### 2. document_processor.pyの修正
- `_generate_embeddings_batch()`メソッドを個別処理に変更
- エラーハンドリングの改善
- 環境変数からのモデル設定を正しく処理

### 3. auto_embed_simple.pyの修正
- 環境変数からembeddingモデルを取得するように変更
- 3072次元対応に更新

### 4. スキーマファイルの更新
- [`chunks_table_schema.sql`](sql/chunks_table_schema.sql)を3072次元に更新
- コメントを正確な情報に更新

## 🧪 検証結果

### テスト実行結果
```
✅ Embedding生成テスト: 成功 (3072次元)
✅ 既存の未生成チャンク: 3件すべて修正完了
✅ 成功率: 100%
✅ 新規アップロード: embedding自動生成確認
```

### 修正前後の比較
| 項目 | 修正前 | 修正後 |
|------|--------|--------|
| Embedding生成 | ❌ 失敗 | ✅ 成功 |
| 次元数 | 768 vs 3072 (不一致) | 3072 (一致) |
| バッチ処理 | ❌ 不正なAPI使用 | ✅ 個別処理 |
| モデル設定 | ❌ 不整合 | ✅ 統一 |

## 📁 修正されたファイル

1. **[`modules/document_processor.py`](modules/document_processor.py)**
   - `_generate_embeddings_batch()`メソッドの完全書き換え
   - 環境変数からのモデル設定処理追加

2. **[`auto_embed_simple.py`](auto_embed_simple.py)**
   - 環境変数対応
   - 3072次元対応

3. **[`sql/chunks_table_schema.sql`](sql/chunks_table_schema.sql)**
   - VECTOR(768) → VECTOR(3072)に変更
   - コメント更新

4. **[`sql/update_embedding_dimensions.sql`](sql/update_embedding_dimensions.sql)** (新規作成)
   - データベース移行スクリプト

5. **[`test_embedding_fix.py`](test_embedding_fix.py)** (新規作成)
   - 問題検証・修正テスト用スクリプト

## 🚀 今後のアップロード処理

### 正常な処理フロー
1. **ファイルアップロード** → **テキスト抽出** → **チャンク分割**
2. **Embedding生成** (gemini-embedding-exp-03-07, 3072次元)
3. **データベース保存** (document_sources + chunks)
4. **✅ 完了**

### 監視ポイント
- Embedding生成成功率
- API制限エラーの監視
- 次元数の一致確認

## 🔧 メンテナンス

### 定期チェック
```bash
# Embedding未生成チャンクの確認
python test_embedding_fix.py

# 手動でembedding生成
python auto_embed_simple.py [制限数]
```

### トラブルシューティング
- Embedding生成失敗時は`test_embedding_fix.py --fix`で個別修正
- API制限エラー時は待機時間を調整
- 次元数エラー時はモデル設定を確認

---

**修正完了日**: 2025-06-26  
**修正者**: Roo  
**ステータス**: ✅ 完了・検証済み