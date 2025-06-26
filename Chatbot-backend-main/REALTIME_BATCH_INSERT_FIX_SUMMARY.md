# リアルタイムバッチ挿入修正レポート

## 問題の概要

### 元の問題
- 大量のチャンクデータを一度にSupabaseに挿入する際に`statement timeout`エラーが発生
- ユーザーの要求: **「50個単位でembedding完成→即座にinsert」**

### 従来の実装の問題点
1. **全embedding生成後に一括処理**: 全てのembeddingを生成してから最後にバッチ処理
2. **リアルタイム性の欠如**: 50個完成しても、全体完了まで待機
3. **メモリ使用量**: 大量データを一度にメモリに保持

## 実装した解決策

### 1. リアルタイムバッチ処理アーキテクチャ

#### 変更前のフロー
```
全チャンク → 全embedding生成 → 50個単位でinsert
     ↓              ↓              ↓
   1000個         1000個         20バッチ
```

#### 変更後のフロー（リアルタイム）
```
50個チャンク → 50個embedding → 即座にinsert
     ↓              ↓              ↓
   次50個         次50個         即座にinsert
     ↓              ↓              ↓
   残20個         残20個         即座にinsert
```

### 2. 修正したファイル
- `modules/document_processor.py` の `_save_chunks_to_database` メソッド

### 3. 実装の詳細

#### 新しい処理フロー
```python
# 50個単位でembedding生成→即座にinsert
for batch_num in range(0, len(chunks), batch_size):
    batch_chunks = chunks[batch_num:batch_num + batch_size]
    
    # 1. このバッチのembedding生成
    batch_embeddings = await self._generate_embeddings_batch(batch_contents)
    
    # 2. 失敗分のリトライ処理
    # ... リトライロジック ...
    
    # 3. 成功したembeddingのみでレコード準備
    records_to_insert = [成功したembeddingのみ]
    
    # 4. 即座にSupabaseに挿入
    result = supabase.table("chunks").insert(records_to_insert).execute()
```

#### キーポイント
1. **50個完成時点で即座にinsert**: 全体完了を待たない
2. **失敗分のスキップ**: 失敗したembeddingは保存せず、次のバッチに進む
3. **詳細ログ**: バッチごとの進捗をリアルタイム表示
4. **エラー耐性**: 一部バッチの失敗でも処理継続

## 修正内容の比較

### 変更前のコード
```python
# 全embedding生成
embeddings = await self._generate_embeddings_batch(contents)

# 全レコード準備
records_to_insert = [全チャンク分]

# 50個単位でバッチ挿入
for batch_num in range(0, len(records_to_insert), batch_size):
    # 挿入処理
```

### 変更後のコード
```python
# 50個単位でembedding生成→即座にinsert
for batch_num in range(0, len(chunks), batch_size):
    batch_chunks = chunks[batch_num:batch_num + batch_size]
    
    # このバッチのembedding生成
    batch_embeddings = await self._generate_embeddings_batch(batch_contents)
    
    # 即座にSupabaseに挿入
    if records_to_insert:
        result = supabase.table("chunks").insert(records_to_insert).execute()
```

## 期待される動作ログ

### リアルタイム処理の例
```
🚀 テスト文書: 120個のチャンクを50個単位で処理開始
📊 予想バッチ数: 3

🧠 バッチ 1/3: 50個のembedding生成開始
💾 バッチ 1/3: 50件を即座に保存中...
✅ バッチ 1/3: 50件保存完了
🎯 バッチ 1/3 完了: embedding 50/50 成功, 保存 50 件

🧠 バッチ 2/3: 50個のembedding生成開始
💾 バッチ 2/3: 50件を即座に保存中...
✅ バッチ 2/3: 50件保存完了
🎯 バッチ 2/3 完了: embedding 50/50 成功, 保存 50 件

🧠 バッチ 3/3: 20個のembedding生成開始
💾 バッチ 3/3: 20件を即座に保存中...
✅ バッチ 3/3: 20件保存完了
🎯 バッチ 3/3 完了: embedding 20/20 成功, 保存 20 件

🏁 テスト文書: 全処理完了
📈 最終結果: 保存 120/120 チャンク
```

## テスト方法

### 新しいテストスクリプト
`test_realtime_batch_insert.py` を作成し、以下のテストを実装:

1. **小リアルタイムバッチテスト**: 75個のチャンク（50個+25個）
2. **大リアルタイムバッチテスト**: 120個のチャンク（50個×2+20個）

### テスト実行
```bash
cd workmate/Chatbot-backend-main
python test_realtime_batch_insert.py
```

### 期待される結果
- 50個のembedding完成と同時にinsertが実行される
- 全体完了を待たずに、部分的にデータが保存される
- タイムアウトエラーが解消される

## 修正の利点

### 1. リアルタイム性の向上
- **即座の保存**: 50個完成時点で即座にinsert
- **進捗の可視化**: バッチごとの進捗がリアルタイムで確認可能
- **部分的成功**: 一部のembeddingが失敗しても、成功分は保存される

### 2. メモリ効率の改善
- **メモリ使用量削減**: 50個単位での処理でメモリ使用量を抑制
- **ガベージコレクション**: バッチ完了後にメモリが解放される

### 3. エラー耐性の強化
- **部分的失敗対応**: 一部バッチの失敗でも全体処理が継続
- **詳細エラー情報**: バッチ単位でのエラー詳細を記録

### 4. パフォーマンスの最適化
- **タイムアウト回避**: 小さなバッチサイズでデータベース負荷を軽減
- **並行処理対応**: 他の処理への影響を最小化

## 運用上の注意点

### 1. バッチサイズの調整
- 現在は50個に固定
- 必要に応じて環境変数等で調整可能

### 2. エラー監視
- バッチ単位でのエラー率を監視
- 連続失敗時のアラート設定を推奨

### 3. パフォーマンス監視
- バッチ処理時間の監視
- embedding生成とinsert処理の時間比較

## 今後の改善案

### 1. 動的バッチサイズ
- embedding生成速度に応じたバッチサイズの自動調整
- エラー率に基づくバッチサイズの動的変更

### 2. 並列バッチ処理
- 複数バッチの並列実行による高速化
- embedding生成とinsert処理の並列化

### 3. 進捗通知機能
- WebSocketを使用したリアルタイム進捗通知
- フロントエンドでの進捗バー表示

### 4. 失敗分の再処理機能
- 失敗したembeddingの後処理機能
- バックグラウンドでの再試行処理

## 技術的詳細

### embedding生成の最適化
- バッチ単位でのAPI呼び出し最適化
- レート制限対応の改善

### データベース接続の最適化
- 接続プールの活用
- トランザクション管理の改善

### ログ出力の改善
- 構造化ログの導入
- メトリクス収集の強化

---

**修正日**: 2025-06-26  
**修正者**: Roo  
**影響範囲**: ファイルアップロード機能、チャンクデータ保存処理  
**テスト状況**: リアルタイムバッチ処理実装完了、テストスクリプト作成済み  
**重要な変更**: 50個単位でembedding完成→即座にinsertを実現