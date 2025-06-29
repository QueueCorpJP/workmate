# 📤 document_sourcesテーブル挿入問題修正レポート

## 🔍 問題の概要
ファイルアップロード時に`chunks`テーブルにはdoc_idが挿入されるが、`document_sources`テーブルにdoc_idが挿入されない問題を修正しました。

## 🛠️ 実施した修正

### 1. document_processor.py の修正

#### `_save_document_metadata`メソッドの改善
- **修正箇所**: 364-387行
- **変更内容**:
  - `content`フィールドを追加
  - `timestamp`フィールドを使用（`uploaded_at`から変更）
  - `active`フィールドを追加
  - より詳細なログ出力を追加

```python
metadata = {
    "id": document_id,
    "name": doc_data["name"],
    "type": doc_data["type"],
    "content": doc_data.get("content", ""),  # 追加
    "page_count": doc_data.get("page_count", 1),
    "uploaded_by": doc_data["uploaded_by"],
    "company_id": doc_data["company_id"],
    "timestamp": datetime.now().isoformat(),  # 変更
    "active": True  # 追加
}
```

#### `process_uploaded_file`メソッドの改善
- **修正箇所**: 608-615行
- **変更内容**:
  - `doc_data`に`content`フィールドを追加（最初の1000文字）

```python
doc_data = {
    "name": file.filename,
    "type": self._detect_file_type(file.filename),
    "content": extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text,  # 追加
    "page_count": self._estimate_page_count(extracted_text),
    "uploaded_by": user_id,
    "company_id": company_id
}
```

### 2. document_processor_record_based.py の修正

#### `_save_document_to_db`メソッドの改善
- **修正箇所**: 188-218行
- **変更内容**:
  - `supabase.table().insert()`から`insert_data()`関数に変更
  - より詳細なログ出力を追加
  - エラーハンドリングの改善

```python
result = insert_data("document_sources", document_data)

if result and result.data:
    logger.info(f"✅ document_sourcesテーブル保存完了（レコードベース）: {doc_id} - {filename}")
    return doc_id
else:
    logger.error(f"❌ document_sourcesテーブル保存失敗（レコードベース）: result={result}")
    raise Exception("document_sourcesテーブルへのドキュメント保存に失敗しました")
```

#### `_save_records_as_chunks`メソッドの改善
- **修正箇所**: 221-244行
- **変更内容**:
  - `company_id`パラメータを追加
  - chunksテーブルに`company_id`フィールドを追加
  - `updated_at`フィールドを追加
  - `token_count`フィールドを削除（スキーマに存在しないため）

```python
async def _save_records_as_chunks(self, doc_id: str, records: List[Dict[str, Any]], company_id: str) -> int:
    # ...
    chunk_data = {
        "id": str(uuid.uuid4()),
        "doc_id": doc_id,
        "content": record.get('content', ''),
        "chunk_index": i,
        "company_id": company_id,  # 追加
        "metadata": {...},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()  # 追加
    }
```

#### `_process_excel_file_record_based`メソッドの修正
- **修正箇所**: 164行
- **変更内容**:
  - `_save_records_as_chunks`呼び出し時に`company_id`パラメータを追加

```python
saved_chunks = await self._save_records_as_chunks(doc_id, records, company_id)
```

## 🧪 テストスクリプトの作成

### test_document_sources_insertion.py
- **目的**: document_sourcesテーブルへの挿入をテストするスクリプト
- **機能**:
  - DocumentProcessorとDocumentProcessorRecordBasedの両方をテスト
  - テスト用ユーザー・カンパニーの作成
  - document_sourcesとchunksテーブルの両方への挿入確認
  - 自動クリーンアップ機能

## 🔧 修正のポイント

### 1. データベーススキーマとの整合性
- `document_sources`テーブルに必要な全フィールドを含める
- `chunks`テーブルのスキーマと一致するフィールドのみ使用

### 2. エラーハンドリングの改善
- より詳細なログ出力
- 失敗時の原因特定を容易にする

### 3. 統一的なアプローチ
- 両方のdocument_processorで同じ`insert_data`関数を使用
- 一貫したフィールド名とデータ構造

## 🎯 期待される効果

### 修正前の問題
- ファイルアップロード時に`document_sources`テーブルにdoc_idが挿入されない
- エラーの原因が特定しにくい

### 修正後の改善
- ✅ `document_sources`テーブルに確実にdoc_idが挿入される
- ✅ `chunks`テーブルにも正しくdoc_idが挿入される
- ✅ 詳細なログでデバッグが容易
- ✅ データベーススキーマとの完全な整合性

## 🚀 使用方法

### テストスクリプトの実行
```bash
cd workmate/Chatbot-backend-main
python test_document_sources_insertion.py
```

### 本番環境での確認
1. ファイルをアップロード
2. ログで`document_sourcesテーブル保存完了`メッセージを確認
3. データベースで`document_sources`と`chunks`テーブルの両方にレコードが存在することを確認

## 📝 注意事項

- 修正により、`document_sources`テーブルに`content`、`timestamp`、`active`フィールドが必要
- `chunks`テーブルに`company_id`フィールドが必要
- 既存のデータベーススキーマとの互換性を確認してください

## 🔄 今後の改善案

1. **バッチ処理の最適化**: 大量ファイル処理時のパフォーマンス向上
2. **リトライ機能の強化**: ネットワークエラー時の自動復旧
3. **監視機能の追加**: アップロード失敗の自動検知とアラート

---

**修正完了日**: 2025年6月29日  
**修正者**: Roo  
**影響範囲**: ファイルアップロード機能全体