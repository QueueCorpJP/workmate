# アップロード時のdocument_sourcesテーブル修正サマリー

## 🔧 修正内容

### 問題
1. アップロード時にdocument_sourcesテーブルにdoc_idが適切にinsertされていない
2. specialコラムに勝手にデータがinsertされている
3. ユーザーの要求：specialコラムには絶対にinsertしないでほしい

### 修正したファイル

#### 1. `modules/document_processor.py`
**修正箇所**: 372-384行目
- `"special": doc_data.get("special")` を削除
- `"doc_id": document_id` に変更（自身のIDを設定）
- specialコラムは絶対に設定しないようにコメント追加

```python
# 修正前
"special": doc_data.get("special"),  # 特殊属性（メタデータ）
"doc_id": doc_data.get("doc_id")  # ドキュメント識別子

# 修正後
"doc_id": document_id  # ドキュメント識別子として自身のIDを設定
# specialコラムは絶対に設定しない（ユーザーの要求通り）
```

#### 2. `modules/document_processor_record_based.py`
**修正箇所**: 195-205行目
- `"special": f"レコードベース処理（{record_count}レコード）"` を削除
- `"doc_id": doc_id` を追加（自身のIDを設定）
- specialコラムは絶対に設定しないようにコメント追加

```python
# 修正前
"special": f"レコードベース処理（{record_count}レコード）"  # 特殊属性として記録

# 修正後
"doc_id": doc_id  # ドキュメント識別子として自身のIDを設定
# specialコラムは絶対に設定しない（ユーザーの要求通り）
```

#### 3. `test_fixed_supabase_adapter.py`
**修正箇所**: 32-45行目
- `"special": "Fixed adapter test"` を削除
- `"doc_id": test_doc_id` に変更（自身のIDを設定）
- specialコラムは絶対に設定しないようにコメント追加

```python
# 修正前
"special": "Fixed adapter test",
"doc_id": None

# 修正後
"doc_id": test_doc_id  # ドキュメント識別子として自身のIDを設定
# specialコラムは絶対に設定しない（ユーザーの要求通り）
```

## ✅ 修正結果

### 1. doc_idフィールドの適切な設定
- 全てのアップロード処理でdoc_idフィールドに適切な値（ドキュメント自身のID）が設定されるようになりました
- `doc_id = document_id` として、自身のIDを参照するように統一

### 2. specialコラムの完全除去
- 通常のドキュメント処理（document_processor.py）
- レコードベース処理（document_processor_record_based.py）
- テストコード（test_fixed_supabase_adapter.py）
- 全ての箇所でspecialコラムへの挿入を完全に停止

### 3. データ整合性の向上
- document_sourcesテーブルのdoc_idフィールドが常に適切な値を持つようになりました
- 不要なspecialコラムへのデータ挿入が完全に防止されました

## 🧪 テスト方法

1. 修正されたテストスクリプトを実行：
```bash
python test_fixed_supabase_adapter.py
```

2. 実際のファイルアップロードをテスト：
- 通常のファイル（PDF、Word、テキストなど）
- Excelファイル（レコードベース処理）

3. データベース確認：
```sql
-- document_sourcesテーブルの確認
SELECT id, name, doc_id, special FROM document_sources ORDER BY uploaded_at DESC LIMIT 10;

-- specialコラムがNULLであることを確認
SELECT COUNT(*) FROM document_sources WHERE special IS NOT NULL;
```

## 📝 注意事項

- この修正により、今後のアップロードではspecialコラムにデータが挿入されることはありません
- 既存のspecialコラムのデータは残りますが、新規アップロードには影響しません
- doc_idフィールドは常にドキュメント自身のIDが設定されるようになりました

## 🎯 期待される効果

1. **データ整合性の向上**: doc_idフィールドが常に適切な値を持つ
2. **不要データの防止**: specialコラムへの自動挿入を完全に停止
3. **ユーザー要求の実現**: specialコラムには絶対にinsertしない仕様を実装
4. **システムの安定性**: 予期しないデータ挿入による問題を防止

修正完了日: 2025年6月29日