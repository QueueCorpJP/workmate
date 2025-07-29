# Workmate 質問処理フロー完全解説

## 📋 概要

Workmateは、ユーザーからの質問を受け取ってから最終的な回答を生成するまでに、複数の高度なAI技術を組み合わせた処理フローを実行しています。このドキュメントでは、その全プロセスを詳細に解説します。

---

## 🔄 処理フロー全体図

```
👤 ユーザー質問入力
    ↓
🔐 認証・利用制限チェック
    ↓
🧠 質問意図分析・複雑さ判定
    ↓
📊 RAGシステム選択
    ↓
🔍 検索・埋め込み処理
    ↓
🤖 LLM回答生成
    ↓
💾 履歴保存・使用量記録
    ↓
📤 最終回答返却
```

---

## 📝 詳細処理ステップ

### 1. 🚪 エントリーポイント - チャットAPI

**エンドポイント**: `POST /chatbot/api/chat`  
**処理ファイル**: `main.py:1276-1320`

```python
# メインのチャットエンドポイント
@app.post("/chatbot/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, current_user, db):
    # Enhanced RAG統合システムを使用
    enhanced_chat = EnhancedChatIntegration()
    result = await enhanced_chat.process_chat_with_enhanced_rag(message, db, current_user)
```

**処理内容**:
- ユーザー認証情報の取得
- 現在の利用制限状況の確認
- Enhanced RAG統合システムの初期化

---

### 2. 🔐 認証・利用制限チェック

**処理ファイル**: `modules/chat_processing.py:24-60`

#### 2.1 使用量制限チェック
```python
def check_usage_limit(user_id: str) -> bool:
    # 1時間以内の使用回数をカウント
    # USAGE_LIMIT_PER_HOUR（デフォルト50回）と比較
```

**チェック項目**:
- ✅ **時間制限**: 1時間あたりの質問回数制限
- ✅ **ユーザー追跡**: 個別ユーザーごとの使用量管理
- ✅ **制限超過時**: HTTP 429エラーを返却

#### 2.2 ユーザー情報設定
- `message.user_id = current_user["id"]`
- `message.employee_name = current_user["name"]`
- 会社ID（`company_id`）の取得

---

### 3. 🧠 質問意図分析・複雑さ判定

**処理ファイル**: `modules/enhanced_chat_integration.py:48-86`

#### 3.1 複雑さ判定指標
```python
complexity_indicators = [
    # 比較を求める質問
    ('と' in question and ('違い' in question or '比較' in question)),
    # 複数の情報を求める質問
    ('また' in question or 'さらに' in question),
    # 手順や段階的な説明を求める質問
    ('手順' in question or 'やり方' in question),
    # 複数の疑問符
    question.count('？') > 1,
    # 長い質問（100文字以上）
    len(question) > 100,
    # 複数の要素を含む質問
    ('について' in question and question.count('について') > 1),
    # 詳細な説明を求める質問
    ('詳しく' in question or '具体的に' in question),
]
```

#### 3.2 判定結果
- **複雑さスコア**: 0.0-1.0の数値
- **閾値**: 0.6以上で拡張RAG使用
- **最小質問長**: 50文字未満は基本RAG

---

### 4. 📊 RAGシステム選択

Workmateには3つの主要なRAGシステムがあります：

#### 4.1 🚀 Enhanced RAG（拡張RAG）
**適用条件**: 複雑な質問（複雑さスコア ≥ 0.6）  
**処理ファイル**: `modules/enhanced_realtime_rag.py`

**特徴**:
- 4段階処理フロー
- 質問の自動分割
- サブタスク並列処理
- 最終統合回答

#### 4.2 📝 Basic RAG（基本RAG）
**適用条件**: シンプルな質問  
**処理ファイル**: `modules/realtime_rag.py`

**特徴**:
- 標準的なRAG処理
- ベクトル検索 + キーワード検索
- 高速処理

#### 4.3 🎯 Ultra Accurate RAG（超高精度RAG）
**適用条件**: 特別な高精度要求時  
**処理ファイル**: `modules/ultra_accurate_rag.py`

**特徴**:
- 最高精度の検索
- 動的閾値計算
- 結果強化処理

---

### 5. 🔍 Enhanced RAG 詳細処理フロー

#### Step 1: ✏️ 質問分析・分割
**処理ファイル**: `enhanced_realtime_rag.py:86-180`

```python
async def step1_parse_and_divide_question(self, question: str):
    # Gemini 2.5 Flashで質問を分析
    analysis_prompt = f"""
    以下の質問を分析し、複雑な質問かどうかを判定してください。
    複雑な質問の場合は、適切なサブタスクに分割してください。
    
    質問: 「{question}」
    """
```

**出力結果**:
- `is_complex`: 複雑さ判定（boolean）
- `complexity_score`: 複雑さスコア（0.0-1.0）
- `subtasks`: サブタスクリスト（2-5個）
- 各サブタスクには優先度・カテゴリ・期待回答タイプを設定

#### Step 2: 🧠 個別埋め込み検索
**処理ファイル**: `enhanced_realtime_rag.py:200-280`

```python
async def step2_individual_embedding_retrieval(self, subtasks, company_id, top_k):
    # 各サブタスクに対して並列でベクトル検索を実行
    for subtask in subtasks:
        # 埋め込み生成
        embedding = await self.generate_embedding(subtask.question)
        # ベクトル類似検索
        results = await self.similarity_search(embedding, company_id, top_k)
```

**検索方式**:
- **並列処理**: 複数サブタスクの同時検索
- **ベクトル検索**: pgvector使用（768次元）
- **会社フィルタ**: 企業別データ分離
- **Top-K取得**: 各サブタスクでtop_k=15件

#### Step 3: 💡 サブ回答生成
**処理ファイル**: `enhanced_realtime_rag.py:350-450`

```python
async def step3_generate_sub_answers(self, subtask_results, company_name, company_id):
    # 各サブタスクの検索結果から個別回答を生成
    for subtask_id, search_results in subtask_results.items():
        # コンテキスト構築
        context = self.build_context(search_results)
        # Gemini Flash 2.5で回答生成
        sub_answer = await self.generate_answer(subtask.question, context)
```

**特徴**:
- 各サブタスクで独立した回答を生成
- 検索結果をコンテキストとして活用
- 回答品質の個別評価

#### Step 4: 🏁 最終統合
**処理ファイル**: `enhanced_realtime_rag.py:500-598`

```python
async def step4_final_integration(self, analysis, sub_results):
    # Chain-of-Thoughtアプローチで最終回答を統合
    integration_prompt = f"""
    以下のサブ回答を論理的に結合し、構造化された1つの回答を生成してください：
    
    元の質問: {analysis.original_question}
    サブ回答: {sub_results}
    """
```

**統合方式**:
- **Chain-of-Thought**: 論理的思考プロセス
- **構造化**: 表形式・リスト形式での整理
- **一貫性確保**: サブ回答間の矛盾解決

---

### 6. 🔍 Basic RAG 詳細処理フロー

#### Step 1: 📥 質問受付
**処理ファイル**: `realtime_rag.py:60-90`

```python
async def step1_receive_question(self, question: str, company_id: str):
    # 質問の前処理とクリーニング
    processed_question = self.preprocess_question(question)
    return {"processed_question": processed_question}
```

#### Step 2: 🧮 埋め込み生成
**処理ファイル**: `realtime_rag.py:153-180`

```python
async def step2_generate_embedding(self, question: str):
    # Multi-API Embedding使用（3072次元）
    embedding_vector = await self.multi_api_client.generate_embedding(question)
    return embedding_vector
```

**埋め込み仕様**:
- **モデル**: text-multilingual-embedding-002
- **次元数**: 3072次元
- **言語**: 日本語対応

#### Step 3: 🔍 類似検索
**処理ファイル**: `realtime_rag.py:180-221`

```python
async def step3_similarity_search(self, query_embedding, company_id, top_k):
    # ベクトル検索とキーワード検索を並列実行
    search_tasks = [
        self.vector_similarity_search(query_embedding, company_id, top_k),
        self.keyword_search(processed_question, company_id, 5)
    ]
    results = await asyncio.gather(*search_tasks)
```

**検索方式**:
- **ベクトル検索**: pgvector使用
- **キーワード検索**: SQL LIKE検索
- **並列実行**: 2つの検索方式を同時実行
- **結果統合**: 重複除去とスコア統合

#### Step 4: 🤖 回答生成
**処理ファイル**: `realtime_rag.py:420-608`

```python
async def step4_generate_answer(self, question: str, similar_chunks: List[Dict]):
    # コンテキスト構築（最大80,000文字）
    context = self.build_context(similar_chunks, max_length=80000)
    
    # Gemini Flash 2.5で回答生成
    response = self.chat_client.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.2,
            max_output_tokens=4096,
            top_p=0.9,
            top_k=50
        )
    )
```

---

### 7. 🔍 ベクトル検索システム詳細

**処理ファイル**: `modules/vector_search.py`

#### 7.1 埋め込み生成
```python
async def generate_query_embedding(self, query: str) -> List[float]:
    # Multi-API Embedding使用
    embedding_vector = await self.multi_api_client.generate_embedding(query)
    # 3072次元ベクトルを生成
```

#### 7.2 ベクトル類似検索
```python
async def vector_similarity_search(self, query: str, company_id: str, limit: int):
    # pgvector使用の高速検索
    similarity_sql = "1 - (c.embedding <=> %s::vector)"
    order_sql = "c.embedding <=> %s::vector"
```

**検索SQL**:
```sql
SELECT 
    c.id as chunk_id,
    c.content,
    c.chunk_index,
    ds.name as document_name,
    1 - (c.embedding <=> %s::vector) as similarity_score
FROM chunks c
JOIN document_sources ds ON c.document_source_id = ds.id
WHERE ds.company_id = %s OR ds.company_id IS NULL
ORDER BY c.embedding <=> %s::vector
LIMIT %s
```

---

### 8. 🤖 LLM回答生成詳細

#### 8.1 コンテキスト構築
**処理ファイル**: `realtime_rag.py:429-465`

```python
# コンテキスト構築（原文ベース）
context_parts = []
total_length = 0
max_context_length = 80000  # 8万文字制限

for chunk in similar_chunks:
    chunk_content = f"【参考資料{i+1}: {chunk['document_name']} - チャンク{chunk['chunk_index']}】\n{chunk['content']}\n"
    if total_length + len(chunk_content) <= max_context_length:
        context_parts.append(chunk_content)
        total_length += len(chunk_content)
```

#### 8.2 プロンプト構築
**処理ファイル**: `chat_processing.py:396-481`

```python
def build_response_prompt(message, search_results, conversation_context, intent_info):
    prompt_parts = [
        "あなたは親切で知識豊富なAIアシスタントです。",
        "以下の検索結果を参考にして、ユーザーの質問に有用な回答を日本語で提供してください。",
        f"\n【参考情報】\n{search_results}\n",
        f"\n【ユーザーの質問】\n{message}\n",
        "\n【回答】"
    ]
    return ''.join(prompt_parts)
```

#### 8.3 Gemini設定
```python
generation_config=genai.GenerationConfig(
    temperature=0.2,      # 創造性レベル
    max_output_tokens=4096,  # 最大出力トークン
    top_p=0.9,           # 多様性制御
    top_k=50             # 候補数制御
)
```

---

### 9. 💾 履歴保存・使用量記録

#### 9.1 チャット履歴保存
**処理ファイル**: `chat_processing.py:81-147`

```python
async def save_chat_history(user_id, user_message, bot_response, **kwargs):
    data = {
        "id": str(uuid.uuid4()),
        "user_message": user_message,
        "bot_response": bot_response,
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "company_id": company_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "model_name": "gemini-2.5-flash",
        "cost_usd": cost_usd,
    }
    result = insert_data("chat_history", data)
```

**保存データ**:
- 💬 **会話内容**: 質問・回答ペア
- 🏢 **企業情報**: company_id, employee_id
- 📊 **使用量**: トークン数、コスト
- 📝 **メタデータ**: ソース文書、ページ番号
- ⏰ **タイムスタンプ**: ISO形式

#### 9.2 使用量記録
```python
def record_usage(user_id: str, response_length: int):
    # 使用量トラッカーに記録
    usage_tracker[user_id].append(current_time)
```

---

### 10. 📤 最終回答返却

#### 10.1 レスポンス形式
```python
class ChatResponse:
    response: str           # 生成された回答
    source: str            # ソース文書情報
    remaining_questions: Optional[int]  # 残り質問数
    limit_reached: Optional[bool]       # 制限到達フラグ
```

#### 10.2 ソース情報生成
```python
# sourcesフィールドからsource文字列を生成
source_text = ""
if hasattr(result, 'sources') and result.sources:
    source_names = []
    for source in result.sources[:3]:  # 最大3つのソース
        source_name = source.get('name', '')
        if source_name:
            source_names.append(source_name)
    source_text = ", ".join(source_names)
```

---

## 🔧 技術仕様

### システム構成
- **フロントエンド**: React + TypeScript
- **バックエンド**: Python FastAPI
- **データベース**: Supabase PostgreSQL + pgvector
- **LLM**: Google Gemini 2.5 Flash
- **埋め込み**: text-multilingual-embedding-002 (3072次元)

### パフォーマンス指標
- **処理時間**: 通常3-8秒
- **コンテキスト長**: 最大80,000文字
- **検索件数**: Basic RAG 20件、Enhanced RAG 15件/サブタスク
- **同時処理**: 並列検索・サブタスク処理

### 制限・制約
- **使用量制限**: 1時間あたり50回（デフォルト）
- **質問長制限**: 最大10,000文字
- **出力トークン**: 最大4,096トークン
- **会社データ分離**: company_idによる厳密な分離

---

## 🚨 エラーハンドリング

### 主要なエラーケース
1. **使用量制限超過**: HTTP 429エラー
2. **認証失敗**: HTTP 401エラー
3. **検索結果なし**: デフォルト回答を返却
4. **LLM生成失敗**: フォールバック応答
5. **データベース接続エラー**: 一時的な応答

### フォールバック機能
- Enhanced RAG → Basic RAG → Ultra Accurate RAG
- ベクトル検索 → キーワード検索
- pgvector → フォールバック検索
- Multi-API → 単一API

---

## 📈 監視・ログ

### ログレベル
- **INFO**: 正常な処理フロー
- **WARNING**: 非致命的な問題
- **ERROR**: 処理失敗・例外

### 監視項目
- 🕐 **処理時間**: 各ステップの実行時間
- 📊 **検索結果数**: 取得できたチャンク数
- 💰 **コスト**: トークン使用量・API呼び出し回数
- 🎯 **精度**: 類似度スコア・回答品質

---

## 🔮 今後の拡張予定

### 機能拡張
- **マルチモーダル対応**: 画像・音声入力
- **リアルタイム学習**: ユーザーフィードバック反映
- **カスタムプロンプト**: 企業別プロンプトテンプレート
- **A/Bテスト**: 複数回答の比較評価

### パフォーマンス改善
- **キャッシュシステム**: 頻繁な質問の高速化
- **インデックス最適化**: 検索速度の向上
- **並列処理拡張**: より多くの並列タスク
- **GPU加速**: 埋め込み生成の高速化

---

この処理フローにより、Workmateは高精度で高速な質問応答システムを実現しています。各ステップが相互に連携し、ユーザーに最適な回答を提供する仕組みが構築されています。 