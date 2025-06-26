# 🚀 リアルタイムRAG処理フロー実装ガイド

## 概要

新しいリアルタイムRAG（Retrieval-Augmented Generation）処理フローを実装しました。このシステムは、ユーザーの質問に対してリアルタイムで最適な回答を生成する5ステップのプロセスを提供します。

## ✅ 実装されたRAGフロー

### Step 1. 質問入力 ✏️
- ユーザーがチャットボットに質問を入力
- 例：「返品したいときはどこに連絡すればいいですか？」

### Step 2. embedding 生成 🧠
- **Gemini Vectors API（gemini-embedding-exp-03-07）** を使用
- 質問文を **3072次元のベクトル** に変換
- 高精度な意味理解を実現

### Step 3. 類似チャンク検索（Top-K） 🔍
- **Supabaseの chunks テーブル** から検索
- **pgvector** を使用したベクトル距離計算
- SQL例：
```sql
SELECT * FROM chunks
ORDER BY embedding <#> '[質問のベクトル]'
LIMIT 10;
```

### Step 4. LLMへ送信 💡
- Top-K チャンクと元の質問を **Gemini Flash 2.5** に送信
- **要約せずに「原文ベース」** で回答を生成
- 正確性を最優先

### Step 5. 回答表示 ⚡️
- 最終的な回答をユーザーに表示
- メタデータ（類似度、使用チャンク数等）も含む

## 📁 ファイル構成

### 新規作成ファイル

1. **`modules/realtime_rag.py`** - メインのリアルタイムRAG処理システム
2. **`modules/chat_realtime_rag.py`** - チャット機能との統合モジュール
3. **`test_realtime_rag.py`** - テストスクリプト
4. **`REALTIME_RAG_GUIDE.md`** - このドキュメント

### 修正ファイル

1. **`modules/chat.py`** - 既存チャットモジュールにリアルタイムRAG統合

## 🔧 技術仕様

### 使用技術
- **Gemini Embedding API**: `gemini-embedding-exp-03-07` (3072次元)
- **Gemini Chat API**: `gemini-2.5-flash`
- **データベース**: Supabase PostgreSQL + pgvector
- **言語**: Python 3.8+

### 依存関係
```python
google-generativeai
psycopg2-binary
supabase
python-dotenv
fastapi
```

### 環境変数
```bash
GOOGLE_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
DB_PASSWORD=your_db_password
```

## 🚀 使用方法

### 1. 基本的な使用方法

```python
from modules.realtime_rag import process_question_realtime

# リアルタイムRAG処理を実行
result = await process_question_realtime(
    question="返品について教えてください",
    company_id="company_123",
    company_name="サンプル会社",
    top_k=10
)

print(f"回答: {result['answer']}")
print(f"使用チャンク数: {result['chunks_used']}")
print(f"最高類似度: {result['top_similarity']}")
```

### 2. チャット機能での使用

```python
from modules.chat_realtime_rag import process_chat_with_realtime_rag

# チャットメッセージを処理
response = await process_chat_with_realtime_rag(message, db, current_user)
```

### 3. ステップ別実行

```python
from modules.realtime_rag import get_realtime_rag_processor

processor = get_realtime_rag_processor()

# Step 1: 質問入力
step1_result = await processor.step1_receive_question("質問内容")

# Step 2: エンベディング生成
embedding = await processor.step2_generate_embedding("質問内容")

# Step 3: 類似検索
chunks = await processor.step3_similarity_search(embedding, top_k=5)

# Step 4: 回答生成
answer = await processor.step4_generate_answer("質問内容", chunks)

# Step 5: 回答表示
result = await processor.step5_display_answer(answer)
```

## 🧪 テスト方法

### 1. 基本テスト
```bash
cd workmate/Chatbot-backend-main
python test_realtime_rag.py
```

### 2. 個別ステップテスト
```python
# test_realtime_rag.py内のtest_step_by_step()関数を実行
```

### 3. システム状態確認
```python
from modules.chat_realtime_rag import get_realtime_rag_status

status = get_realtime_rag_status()
print(status)
```

## 📊 パフォーマンス特性

### 処理時間（目安）
- Step 1 (質問入力): < 1ms
- Step 2 (エンベディング生成): 200-500ms
- Step 3 (類似検索): 50-200ms
- Step 4 (LLM回答生成): 1-3秒
- Step 5 (回答表示): < 1ms

**総処理時間**: 約1.5-4秒

### 精度向上のポイント
1. **3072次元エンベディング**: 高精度な意味理解
2. **原文ベース回答**: 要約による情報損失を防止
3. **Top-K検索**: 関連性の高いチャンクのみを使用
4. **pgvector最適化**: 高速なベクトル検索

## 🔄 フォールバック機能

リアルタイムRAGが利用できない場合、自動的に従来のRAGシステムにフォールバックします：

1. **並列ベクトル検索**
2. **単一ベクトル検索**
3. **従来のハイブリッド検索**

## ⚠️ 注意事項

### 制限事項
1. **API制限**: Gemini APIの利用制限に注意
2. **データベース接続**: Supabaseの接続制限
3. **メモリ使用量**: 大量のチャンクを処理する際の注意

### エラーハンドリング
- 各ステップで適切なエラーハンドリングを実装
- フォールバック機能により可用性を確保
- 詳細なログ出力でデバッグを支援

## 🔧 カスタマイズ

### パラメータ調整
```python
# Top-K値の調整
top_k = 15  # デフォルト: 10

# 類似度閾値の調整
similarity_threshold = 0.7  # デフォルト: なし

# 最大コンテキスト長
max_context_length = 100000  # デフォルト: 100,000文字
```

### プロンプトカスタマイズ
```python
# Step 4のプロンプトをカスタマイズ
custom_prompt = f"""あなたは{company_name}のAIアシスタントです。
【カスタム指示】
1. より詳細な回答を提供してください
2. 関連する追加情報も含めてください
...
"""
```

## 📈 今後の拡張予定

1. **キャッシュ機能**: 頻繁な質問のキャッシュ
2. **A/Bテスト**: 複数のRAG手法の比較
3. **リアルタイム学習**: ユーザーフィードバックによる改善
4. **多言語対応**: 英語等の他言語サポート

## 🆘 トラブルシューティング

### よくある問題

1. **エンベディング生成失敗**
   - API キーの確認
   - ネットワーク接続の確認

2. **データベース接続エラー**
   - Supabase設定の確認
   - pgvector拡張の有効化確認

3. **チャンクが見つからない**
   - chunksテーブルのデータ確認
   - company_idフィルタの確認

### デバッグ方法
```python
# ログレベルを上げる
import logging
logging.basicConfig(level=logging.DEBUG)

# 詳細なデバッグ情報を出力
from modules.realtime_rag import get_realtime_rag_processor
processor = get_realtime_rag_processor()
# 各ステップの詳細ログが出力される
```

## 📞 サポート

問題が発生した場合は、以下の情報を含めてお問い合わせください：

1. エラーメッセージ
2. 実行環境（Python版、OS等）
3. 設定ファイル（機密情報は除く）
4. 再現手順

---

**実装完了日**: 2025年6月26日  
**バージョン**: 1.0.0  
**作成者**: Roo (Claude Sonnet 4)