"""
🚀 リアルタイムRAG処理フロー
質問受付〜RAG処理フロー（リアルタイム回答）の実装

ステップ:
✏️ Step 1. 質問入力 - ユーザーがチャットボットに質問を入力
🧠 Step 2. embedding 生成 - Vertex AI text-multilingual-embedding-002 を使って、質問文をベクトルに変換（768次元）
🔍 Step 3. 類似チャンク検索（Top-K） - Supabaseの chunks テーブルから、ベクトル距離が近いチャンクを pgvector を用いて取得
💡 Step 4. LLMへ送信 - Top-K チャンクと元の質問を Gemini Flash 2.5 に渡して、要約せずに「原文ベース」で回答を生成
⚡️ Step 5. 回答表示
"""

import os
import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
import google.generativeai as genai
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import urllib.parse  # 追加

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class RealtimeRAGProcessor:
    """リアルタイムRAG処理システム（Gemini質問分析統合版）"""
    
    def __init__(self):
        """初期化"""
        self.use_vertex_ai = os.getenv("USE_VERTEX_AI", "true").lower() == "true"
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-multilingual-embedding-002")  # Vertex AI text-multilingual-embedding-002を使用（768次元）
        self.expected_dimensions = 768 if "text-multilingual-embedding-002" in self.embedding_model else 3072
        
        # API キーの設定
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        self.chat_model = "gemini-2.5-flash"  # 最新のGemini Flash 2.5
        self.db_url = self._get_db_url()
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
        
        # Gemini APIクライアントの初期化（チャット用）
        genai.configure(api_key=self.api_key)
        self.chat_client = genai.GenerativeModel(self.chat_model)
        
        # Vertex AI Embeddingクライアントの初期化（埋め込み用）
        if self.use_vertex_ai:
            from .vertex_ai_embedding import get_vertex_ai_embedding_client, vertex_ai_embedding_available
            if vertex_ai_embedding_available():
                self.vertex_client = get_vertex_ai_embedding_client()
                logger.info(f"✅ Vertex AI Embedding初期化: {self.embedding_model} ({self.expected_dimensions}次元)")
            else:
                logger.error("❌ Vertex AI Embeddingが利用できません")
                raise ValueError("Vertex AI Embeddingの初期化に失敗しました")
        else:
            self.vertex_client = None
        
        # 🧠 Gemini質問分析システムの初期化
        self.gemini_analyzer = None
        try:
            from .gemini_question_analyzer import get_gemini_question_analyzer
            self.gemini_analyzer = get_gemini_question_analyzer()
            if self.gemini_analyzer:
                logger.info("✅ Gemini質問分析システム統合完了")
            else:
                logger.warning("⚠️ Gemini質問分析システムが利用できません（従来方式にフォールバック）")
        except ImportError as e:
            logger.warning(f"⚠️ Gemini質問分析システムのインポートに失敗: {e}")
        
        logger.info(f"✅ リアルタイムRAGプロセッサ初期化完了: エンベディング={self.embedding_model} ({self.expected_dimensions}次元)")
    
    def _get_db_url(self) -> str:
        """データベースURLを構築"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL と SUPABASE_KEY 環境変数が設定されていません")
        
        # Supabase URLから接続情報を抽出
        if "supabase.co" in supabase_url:
            project_id = supabase_url.split("://")[1].split(".")[0]
            return f"postgresql://postgres.{project_id}:{os.getenv('DB_PASSWORD', '')}@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"
        else:
            # カスタムデータベースURLの場合
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL 環境変数が設定されていません")
            return db_url
    
    async def step1_receive_question(self, question: str, company_id: str = None) -> Dict:
        """
        ✏️ Step 1. 質問入力
        ユーザーがチャットボットに質問を入力
        """
        logger.info(f"✏️ Step 1: 質問受付 - '{question[:50]}...'")
        
        if not question or not question.strip():
            raise ValueError("質問が空です")
        
        # 質問の前処理
        processed_question = question.strip()
        
        return {
            "original_question": question,
            "processed_question": processed_question,
            "company_id": company_id,
            "timestamp": datetime.now().isoformat(),
            "step": 1
        }
    
    async def step2_generate_embedding(self, question: str) -> List[float]:
        """
        🧠 Step 2. embedding 生成
        Vertex AI text-multilingual-embedding-002 を使って、質問文をベクトルに変換（768次元）
        """
        logger.info(f"🧠 Step 2: エンベディング生成中...")
        
        try:
            if self.use_vertex_ai and self.vertex_client:
                # Vertex AI使用
                embedding_vector = self.vertex_client.generate_embedding(question)
                
                if embedding_vector and len(embedding_vector) > 0:
                    # 次元数チェック
                    if len(embedding_vector) != self.expected_dimensions:
                        logger.warning(f"予期しない次元数: {len(embedding_vector)}次元（期待値: {self.expected_dimensions}次元）")
                    
                    logger.info(f"✅ Step 2完了: {len(embedding_vector)}次元のエンベディング生成成功")
                    return embedding_vector
                else:
                    raise ValueError("Vertex AI エンベディング生成に失敗しました")
            else:
                # フォールバック: Gemini API使用（非推奨）
                logger.warning("⚠️ Vertex AIが利用できないため、Gemini APIを使用")
                response = genai.embed_content(
                    model="models/text-embedding-004",  # 利用可能なモデルに変更
                    content=question
                )
                
                # レスポンスからエンベディングベクトルを取得
                embedding_vector = None
                if isinstance(response, dict) and 'embedding' in response:
                    embedding_vector = response['embedding']
                elif hasattr(response, 'embedding') and response.embedding:
                    embedding_vector = response.embedding
                else:
                    logger.error(f"予期しないレスポンス形式: {type(response)}")
                    raise ValueError("エンベディング生成に失敗しました")
                
                if not embedding_vector:
                    raise ValueError("エンベディングベクトルが空です")
                
                logger.info(f"✅ Step 2完了: {len(embedding_vector)}次元のエンベディング生成成功（フォールバック）")
                return embedding_vector
            
        except Exception as e:
            logger.error(f"❌ Step 2エラー: エンベディング生成失敗 - {e}")
            raise
    
    async def step3_similarity_search(self, query_embedding: List[float], company_id: str = None, top_k: int = 20) -> List[Dict]:
        """
        🔍 Step 3. 類似チャンク検索（Top-K）
        Supabaseの chunks テーブルから、ベクトル距離が近いチャンクを pgvector を用いて取得
        PDFファイルを含むすべてのファイルタイプを平等に検索対象とする
        """
        logger.info(f"🔍 Step 3: 類似チャンク検索開始 (Top-{top_k})")
        
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # 🔍 まず、埋め込みベクトルが利用可能なチャンクでベクトル類似検索
                    vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
                    
                    sql_vector = """
                    SELECT
                        c.id,
                        c.doc_id,
                        c.chunk_index,
                        c.content,
                        ds.name as document_name,
                        ds.type as document_type,
                        1 - (c.embedding <=> %s) as similarity_score,
                        'vector' as search_method
                    FROM chunks c
                    LEFT JOIN document_sources ds ON ds.id = c.doc_id
                    WHERE c.embedding IS NOT NULL
                      AND c.content IS NOT NULL
                      AND LENGTH(c.content) > 10
                    """
                    
                    params_vector = [vector_str]
                    
                    # 会社IDフィルタ（オプション）
                    if company_id:
                        sql_vector += " AND c.company_id = %s"
                        params_vector.append(company_id)
                    
                    # ベクトル距離順でソート
                    sql_vector += " ORDER BY c.embedding <=> %s LIMIT %s"
                    params_vector.extend([vector_str, top_k])
                    
                    logger.info(f"実行SQL: ベクトル類似検索 (Top-{top_k})")
                    cur.execute(sql_vector, params_vector)
                    vector_results = cur.fetchall()
                    
                    # 🔍 PDFファイルのベクトル検索結果を確認
                    pdf_vector_count = len([r for r in vector_results if r['document_type'] == 'pdf'])
                    excel_vector_count = len([r for r in vector_results if r['document_type'] == 'excel'])
                    
                    logger.info(f"ベクトル検索結果: PDF={pdf_vector_count}件, Excel={excel_vector_count}件, 総計={len(vector_results)}件")
                    
                    # 結果を辞書のリストに変換
                    similar_chunks = []
                    for row in vector_results:
                        similar_chunks.append({
                            'chunk_id': row['id'],
                            'doc_id': row['doc_id'],
                            'chunk_index': row['chunk_index'],
                            'content': row['content'],
                            'document_name': row['document_name'],
                            'document_type': row['document_type'],
                            'similarity_score': float(row['similarity_score']),
                            'search_method': row['search_method']
                        })
                    
                    # 🔍 PDFファイルの結果が少ない場合、フォールバック検索を実行
                    if pdf_vector_count < 3:  # PDFファイルの結果が3件未満の場合
                        logger.info("📄 PDFファイルの結果が少ないため、フォールバック検索を実行")
                        
                        # 埋め込みベクトルがないチャンクに対してテキスト検索を実行
                        sql_text = """
                        SELECT
                            c.id,
                            c.doc_id,
                            c.chunk_index,
                            c.content,
                            ds.name as document_name,
                            ds.type as document_type,
                            0.5 as similarity_score,
                            'text_fallback' as search_method
                        FROM chunks c
                        LEFT JOIN document_sources ds ON ds.id = c.doc_id
                        WHERE c.embedding IS NULL
                          AND c.content IS NOT NULL
                          AND LENGTH(c.content) > 10
                          AND ds.type = 'pdf'
                        """
                        
                        params_text = []
                        
                        # 会社IDフィルタ（オプション）
                        if company_id:
                            sql_text += " AND c.company_id = %s"
                            params_text.append(company_id)
                        
                        # ランダムサンプリング（埋め込みベクトルがない場合）
                        sql_text += " ORDER BY RANDOM() LIMIT %s"
                        params_text.append(min(10, top_k))
                        
                        logger.info("実行SQL: PDFファイル向けテキストフォールバック検索")
                        cur.execute(sql_text, params_text)
                        text_fallback_results = cur.fetchall()
                        
                        # フォールバック結果を追加
                        for row in text_fallback_results:
                            similar_chunks.append({
                                'chunk_id': row['id'],
                                'doc_id': row['doc_id'],
                                'chunk_index': row['chunk_index'],
                                'content': row['content'],
                                'document_name': row['document_name'],
                                'document_type': row['document_type'],
                                'similarity_score': float(row['similarity_score']),
                                'search_method': row['search_method']
                            })
                        
                        logger.info(f"フォールバック検索で{len(text_fallback_results)}件のPDFチャンクを追加")
                    
                    # 🔍 さらに、特定のファイルタイプが不足している場合の追加検索
                    file_type_distribution = {}
                    for chunk in similar_chunks:
                        doc_type = chunk['document_type'] or 'unknown'
                        file_type_distribution[doc_type] = file_type_distribution.get(doc_type, 0) + 1
                    
                    # PDFファイルの結果が依然として少ない場合
                    if file_type_distribution.get('pdf', 0) < 2:
                        logger.info("📄 PDFファイル結果が不足しているため、追加検索を実行")
                        
                        # 会社全体のPDFファイルから代表的なチャンクを取得
                        sql_pdf_supplement = """
                        SELECT
                            c.id,
                            c.doc_id,
                            c.chunk_index,
                            c.content,
                            ds.name as document_name,
                            ds.type as document_type,
                            0.4 as similarity_score,
                            'pdf_supplement' as search_method
                        FROM chunks c
                        LEFT JOIN document_sources ds ON ds.id = c.doc_id
                        WHERE c.content IS NOT NULL
                          AND LENGTH(c.content) > 10
                          AND ds.type = 'pdf'
                          AND ds.active = true
                        """
                        
                        params_pdf_supplement = []
                        
                        # 会社IDフィルタ（オプション）
                        if company_id:
                            sql_pdf_supplement += " AND c.company_id = %s"
                            params_pdf_supplement.append(company_id)
                        
                        # 最新のチャンクから優先的に取得
                        sql_pdf_supplement += " ORDER BY c.id DESC LIMIT %s"
                        params_pdf_supplement.append(5)
                        
                        logger.info("実行SQL: PDF補完検索")
                        cur.execute(sql_pdf_supplement, params_pdf_supplement)
                        pdf_supplement_results = cur.fetchall()
                        
                        # PDF補完結果を追加
                        for row in pdf_supplement_results:
                            # 重複チェック
                            if not any(chunk['chunk_id'] == row['id'] for chunk in similar_chunks):
                                similar_chunks.append({
                                    'chunk_id': row['id'],
                                    'doc_id': row['doc_id'],
                                    'chunk_index': row['chunk_index'],
                                    'content': row['content'],
                                    'document_name': row['document_name'],
                                    'document_type': row['document_type'],
                                    'similarity_score': float(row['similarity_score']),
                                    'search_method': row['search_method']
                                })
                        
                        logger.info(f"PDF補完検索で{len(pdf_supplement_results)}件のチャンクを追加")
                    
                    # 結果を類似度順でソート
                    similar_chunks.sort(key=lambda x: x['similarity_score'], reverse=True)
                    
                    # 最大チャンク数に制限
                    final_chunks = similar_chunks[:top_k]
                    
                    logger.info(f"✅ Step 3完了: {len(final_chunks)}個の類似チャンクを取得")
                    
                    # 🔍 詳細チャンク選択ログ（リアルタイムRAG）
                    print("\n" + "="*80)
                    print(f"🔍 【Step 3: 類似チャンク検索結果】")
                    print(f"📊 取得チャンク数: {len(final_chunks)}件 (Top-{top_k})")
                    print(f"🏢 会社IDフィルタ: {'適用 (' + company_id + ')' if company_id else '未適用（全データ検索）'}")
                    print(f"🧠 エンベディングモデル: {self.embedding_model} ({self.expected_dimensions}次元)")
                    
                    # ファイルタイプ別統計を表示
                    final_file_type_distribution = {}
                    for chunk in final_chunks:
                        doc_type = chunk['document_type'] or 'unknown'
                        final_file_type_distribution[doc_type] = final_file_type_distribution.get(doc_type, 0) + 1
                    
                    print(f"📁 ファイルタイプ別結果: {final_file_type_distribution}")
                    print("="*80)
                    
                    for i, chunk in enumerate(final_chunks):
                        similarity = chunk['similarity_score']
                        doc_name = chunk['document_name'] or 'Unknown'
                        chunk_idx = chunk['chunk_index']
                        content_preview = (chunk['content'] or '')[:150].replace('\n', ' ')
                        search_method = chunk['search_method']
                        
                        # 類似度に基づく評価
                        if similarity > 0.8:
                            evaluation = "🟢 非常に高い関連性"
                        elif similarity > 0.6:
                            evaluation = "🟡 高い関連性"
                        elif similarity > 0.4:
                            evaluation = "🟠 中程度の関連性"
                        elif similarity > 0.2:
                            evaluation = "🔴 低い関連性"
                        else:
                            evaluation = "⚫ 極めて低い関連性"
                        
                        print(f"  {i+1:2d}. 📄 {doc_name} ({chunk['document_type']})")
                        print(f"      🧩 チャンク#{chunk_idx} | 🎯 類似度: {similarity:.4f} | {evaluation}")
                        print(f"      🔍 検索方法: {search_method}")
                        print(f"      📝 内容: {content_preview}...")
                        print(f"      🔗 チャンクID: {chunk['chunk_id']} | 📄 ドキュメントID: {chunk['doc_id']}")
                        print()
                    
                    print("="*80 + "\n")
                    
                    return final_chunks
        
        except Exception as e:
            logger.error(f"❌ Step 3エラー: 類似検索失敗 - {e}")
            raise
    
    async def step4_generate_answer(self, question: str, similar_chunks: List[Dict], company_name: str = "お客様の会社", company_id: str = None) -> str:
        """
        💡 Step 4. LLMへ送信
        Top-K チャンクと元の質問を Gemini Flash 2.5 に渡して、要約せずに「原文ベース」で回答を生成
        """
        logger.info(f"💡 Step 4: LLM回答生成開始 ({len(similar_chunks)}個のチャンク使用)")
        
        if not similar_chunks:
            logger.warning("類似チャンクが見つからないため、一般的な回答を生成")
            return "申し訳ございませんが、ご質問に関連する情報が見つかりませんでした。より具体的な質問をしていただけますでしょうか。"
        
        try:
            # 🔍 Step 4: コンテキスト構築ログ
            print("\n" + "="*80)
            print(f"💡 【Step 4: LLM回答生成 - コンテキスト構築】")
            print(f"📊 利用可能チャンク数: {len(similar_chunks)}個")
            print(f"📏 最大コンテキスト長: {80000:,}文字")  # 制限を少し下げる
            print("="*80)
            
            # コンテキスト構築（原文ベース）
            context_parts = []
            total_length = 0
            max_context_length = 80000  # 8万文字に制限（安全のため）
            used_chunks = []
            
            for i, chunk in enumerate(similar_chunks):
                chunk_content = f"【参考資料{i+1}: {chunk['document_name']} - チャンク{chunk['chunk_index']}】\n{chunk['content']}\n"
                chunk_length = len(chunk_content)
                
                print(f"  {i+1:2d}. 📄 {chunk['document_name']} [チャンク#{chunk['chunk_index']}]")
                print(f"      🎯 類似度: {chunk['similarity_score']:.4f}")
                print(f"      📏 文字数: {chunk_length:,}文字")
                
                if total_length + chunk_length > max_context_length:
                    print(f"      ❌ 除外: コンテキスト長制限超過 (現在: {total_length:,}文字)")
                    print(f"         💡 {i}個のチャンクを最終的に使用")
                    break
                
                context_parts.append(chunk_content)
                total_length += chunk_length
                used_chunks.append(chunk)
                print(f"      ✅ 採用: 累計 {total_length:,}文字")
                print(f"      📝 内容プレビュー: {(chunk['content'] or '')[:100].replace(chr(10), ' ')}...")
                print()
            
            context = "\n".join(context_parts)
            
            print(f"📋 最終コンテキスト情報:")
            print(f"   ✅ 使用チャンク数: {len(used_chunks)}個")
            print(f"   �� 総文字数: {len(context):,}文字")
            print("="*80 + "\n")
            
            # 🎯 特別指示を取得してプロンプトの一番前に配置
            special_instructions_text = ""
            if company_id:
                try:
                    with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                        with conn.cursor() as cur:
                            # アクティブなリソースの特別指示を取得
                            sql = """
                            SELECT DISTINCT ds.name, ds.special
                            FROM document_sources ds 
                            WHERE ds.company_id = %s 
                            AND ds.active = true 
                            AND ds.special IS NOT NULL 
                            AND ds.special != ''
                            ORDER BY ds.name
                            """
                            cur.execute(sql, [company_id])
                            special_results = cur.fetchall()
                            
                            if special_results:
                                special_instructions = []
                                print(f"🎯 特別指示を取得しました: {len(special_results)}件")
                                for i, row in enumerate(special_results, 1):
                                    resource_name = row['name']
                                    special_instruction = row['special']
                                    special_instructions.append(f"{i}. 【{resource_name}】: {special_instruction}")
                                    print(f"   {i}. {resource_name}: {special_instruction}")
                                
                                special_instructions_text = "特別な回答指示（以下のリソースを参照する際は、各リソースの指示に従ってください）：\n" + "\n".join(special_instructions) + "\n\n"
                                print(f"✅ 特別指示をプロンプトに追加完了")
                            else:
                                print(f"ℹ️ 特別指示が設定されたリソースが見つかりませんでした")
                                
                except Exception as e:
                    print(f"⚠️ 特別指示取得エラー: {e}")
                    logger.warning(f"特別指示取得エラー: {e}")
            
            # 改善されたプロンプト構築（特別指示を一番前に配置）- より柔軟な検索対応
            prompt = f"""{special_instructions_text}あなたは{company_name}の社内向け丁寧で親切なアシスタントです。

【回答の際の重要な指針】
• 回答は丁寧な敬語で行ってください。
• **検索システムが関連すると判断した参考資料が提供されています。以下の基準で積極的に活用してください：**

**【柔軟な情報提供基準】**
• **会社名について：「株式会社あいう」を探している場合、「株式会社 いう」「株式会社　あい」「㈱あい」「(株)あい」なども同じ会社として扱ってください**
• **部分一致でも有効：質問のキーワードの一部でも参考資料に含まれていれば、関連情報として提供してください**
• **類似情報の提供：完全一致でなくても、似たような会社名、関連する業界情報、類似のサービスなどがあれば積極的に紹介してください**
• **推測と説明：参考資料から推測できることや、関連する内容があれば「参考資料には○○という情報がございます」として提供してください**
• **断片情報も活用：表形式データや一部の情報であっても、質問に関連する部分があれば意味のある情報として解釈してください**

**【回答パターン例】**
• 「株式会社であいう」について質問された場合：
  - 完全一致が見つからなくても、「株式会社」「あい」を含む会社があれば紹介する
  - 類似の名前の会社があれば「類似の会社名として○○がございます」と案内
  - 関連する業界の会社があれば参考情報として提供

**【避けるべき回答】**
• ❌「情報が見当たりません」「確認できませんでした」（参考資料がある場合）
• ❌ 完全一致のみを求める厳格な判断
• ✅ 代わりに：「参考資料を確認したところ、○○という情報がございます」

**【その他の指針】**
• 情報の出典としてファイル名は明示可能ですが、内部構造情報（行番号等）は出力しない
• 専門的な内容も分かりやすく説明
• 文末には「ご不明な点がございましたら、お気軽にお申し付けください。」を追加

ご質問：
{question}

参考となる資料：
{context}

上記の参考資料を基に、柔軟かつ積極的にご質問にお答えいたします："""

            logger.info("🤖 Gemini Flash 2.5に回答生成を依頼中...")
            logger.info(f"📏 プロンプト長: {len(prompt):,}文字")
            
            # Gemini Flash 2.5で回答生成（設定を調整）
            response = self.chat_client.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,  # 少し創造性を上げる
                    max_output_tokens=4096,  # 出力トークン数を増加
                    top_p=0.9,  # 多様性を少し上げる
                    top_k=50    # より多くの候補を考慮
                )
            )
            
            logger.info("📥 Geminiからのレスポンス受信完了")
            
            # レスポンス処理の改善（詳細なデバッグ情報付き）
            answer = None
            
            if response:
                logger.info(f"✅ レスポンスオブジェクト存在: {type(response)}")
                
                # 候補の確認
                if hasattr(response, 'candidates') and response.candidates:
                    logger.info(f"📋 候補数: {len(response.candidates)}")
                    
                    try:
                        # まず response.text を試す
                        answer = response.text
                        if answer:
                            answer = answer.strip()
                            logger.info("✅ response.textから回答を取得")
                        else:
                            logger.warning("⚠️ response.textが空")
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"⚠️ response.text使用不可: {e}")
                        
                        # partsから手動で抽出
                        try:
                            parts = []
                            for i, candidate in enumerate(response.candidates):
                                logger.info(f"   候補{i+1}: {type(candidate)}")
                                
                                if hasattr(candidate, 'content') and candidate.content:
                                    if hasattr(candidate.content, 'parts'):
                                        for j, part in enumerate(candidate.content.parts):
                                            logger.info(f"     パート{j+1}: {type(part)}")
                                            if hasattr(part, 'text') and part.text:
                                                parts.append(part.text)
                                                logger.info(f"     テキスト長: {len(part.text)}文字")
                            
                            if parts:
                                answer = ''.join(parts).strip()
                                logger.info("✅ partsから回答を抽出")
                            else:
                                logger.error("❌ partsからテキストを抽出できませんでした")
                        except Exception as parts_error:
                            logger.error(f"❌ parts抽出エラー: {parts_error}")
                else:
                    logger.error("❌ 候補が存在しません")
            else:
                logger.error("❌ レスポンスオブジェクトが空です")
            
            # 回答の検証と処理
            if answer and len(answer.strip()) > 0:
                logger.info(f"✅ Step 4完了: {len(answer)}文字の回答を生成")
                logger.info(f"📝 回答プレビュー: {answer[:100]}...")
                
                # 回答が短すぎる場合の処理
                if len(answer) < 50:
                    logger.warning(f"⚠️ 回答が短すぎます（{len(answer)}文字）- 補強処理を実行")
                    fallback_answer = f"""参考資料を確認いたしました。

{answer}

より詳細な情報が必要でしたら、具体的な項目をお教えください。参考資料から正確な情報を提供いたします。"""
                    return fallback_answer
                
                return answer
            else:
                logger.error("❌ LLMからの回答が空または取得できませんでした")
                logger.error(f"   レスポンス詳細: {response}")
                
                # フォールバック回答の生成（参考資料の情報を使用）
                fallback_parts = []
                fallback_parts.append("参考資料を確認いたしましたが、システム的な問題により詳細な回答を生成できませんでした。")
                
                # 最初のチャンクから部分的な情報を提供
                if used_chunks and used_chunks[0].get('content'):
                    first_chunk_content = used_chunks[0]['content'][:300]
                    fallback_parts.append(f"\n参考資料の一部をご紹介いたします：\n{first_chunk_content}...")
                
                fallback_parts.append("\nより詳細な情報については、改めてお問い合わせください。")
                
                return "\n".join(fallback_parts)
        
        except Exception as e:
            logger.error(f"❌ Step 4エラー: LLM回答生成失敗 - {e}")
            import traceback
            logger.error(f"詳細エラー: {traceback.format_exc()}")
            
            # エラー時でも可能な限り情報を提供
            error_response_parts = ["申し訳ございませんが、システムエラーが発生しました。"]
            
            if similar_chunks and len(similar_chunks) > 0:
                error_response_parts.append(f"\n検索では{len(similar_chunks)}件の関連資料が見つかりました。")
                if similar_chunks[0].get('content'):
                    first_content = similar_chunks[0]['content'][:200]
                    error_response_parts.append(f"関連情報の一部: {first_content}...")
            
            error_response_parts.append("\nしばらく時間をおいてから再度お試しください。")
            
            return "\n".join(error_response_parts)
    
    async def step5_display_answer(self, answer: str, metadata: Dict = None, used_chunks: List = None) -> Dict:
        """
        ⚡️ Step 5. 回答表示
        最終的な回答とメタデータを返す
        """
        logger.info(f"⚡️ Step 5: 回答表示準備完了")
        
        result = {
            "answer": answer,
            "timestamp": datetime.now().isoformat(),
            "step": 5,
            "status": "completed"
        }
        
        if metadata:
            result.update(metadata)
        
        # 使用されたチャンクの詳細情報を追加
        if used_chunks:
            source_documents = []
            for chunk in used_chunks[:5]:  # 最大5個のソース文書
                doc_info = {
                    "document_name": chunk.get('document_name', 'Unknown Document'),
                    "document_type": chunk.get('document_type', 'unknown'),
                    "chunk_id": chunk.get('chunk_id', ''),
                    "similarity_score": chunk.get('similarity_score', 0.0),
                    "content_preview": (chunk.get('content', '') or '')[:100] + "..." if chunk.get('content') else ""
                }
                source_documents.append(doc_info)
            
            result["source_documents"] = source_documents
            result["total_sources"] = len(used_chunks)
        
        logger.info(f"✅ リアルタイムRAG処理完了: {len(answer)}文字の回答")
        return result
    
    async def process_realtime_rag(self, question: str, company_id: str = None, company_name: str = "お客様の会社", top_k: int = 20) -> Dict:
        """
        🚀 リアルタイムRAG処理フロー全体の実行（Gemini質問分析統合版）
        新しい3段階アプローチ: Gemini分析 → SQL検索 → Embedding検索（フォールバック）
        """
        logger.info(f"🚀 リアルタイムRAG処理開始: '{question[:50]}...'")
        
        try:
            # Step 1: 質問入力
            step1_result = await self.step1_receive_question(question, company_id)
            processed_question = step1_result["processed_question"]
            
            # 🧠 新しい3段階検索システムを使用
            if self.gemini_analyzer:
                logger.info("🧠 Gemini質問分析システムを使用した3段階検索を実行")
                
                # Gemini質問分析 → SQL検索 → Embedding検索（フォールバック）
                search_results, analysis_result = await self.gemini_analyzer.intelligent_search(
                    question=processed_question,
                    company_id=company_id,
                    limit=top_k
                )
                
                # SearchResultオブジェクトを辞書形式に変換
                similar_chunks = []
                for result in search_results:
                    similar_chunks.append({
                        'chunk_id': result.chunk_id,
                        'doc_id': result.document_id,
                        'chunk_index': 0,  # SearchResultにはchunk_indexがないため0を設定
                        'content': result.content,
                        'document_name': result.document_name,
                        'document_type': 'unknown',  # SearchResultにはdocument_typeがないため'unknown'を設定
                        'similarity_score': result.score
                    })
                
                search_method = search_results[0].search_method if search_results else "no_results"
                
                logger.info(f"✅ 3段階検索完了: {search_method}で{len(similar_chunks)}個のチャンクを取得")
                
                # メタデータに検索方法を追加
                metadata = {
                    "original_question": question,
                    "processed_question": processed_question,
                    "chunks_used": len(similar_chunks),
                    "top_similarity": similar_chunks[0]["similarity_score"] if similar_chunks else 0.0,
                    "company_id": company_id,
                    "company_name": company_name,
                    "search_method": search_method,
                    "gemini_analysis": {
                        "intent": analysis_result.intent.value if analysis_result else "unknown",
                        "confidence": analysis_result.confidence if analysis_result else 0.0,
                        "target_entity": analysis_result.target_entity if analysis_result else "",
                        "keywords": analysis_result.keywords if analysis_result else [],
                        "reasoning": analysis_result.reasoning if analysis_result else ""
                    },
                    "keywords": analysis_result.keywords if analysis_result else []
                }
                
            else:
                # フォールバック: 従来のEmbedding検索のみ
                logger.warning("⚠️ Gemini質問分析システムが利用できないため、従来のEmbedding検索を使用")
                
                # Step 2: エンベディング生成
                query_embedding = await self.step2_generate_embedding(processed_question)
                
                # Step 3: 類似チャンク検索
                similar_chunks = await self.step3_similarity_search(query_embedding, company_id, top_k)
                
                metadata = {
                    "original_question": question,
                    "processed_question": processed_question,
                    "chunks_used": len(similar_chunks),
                    "top_similarity": similar_chunks[0]["similarity_score"] if similar_chunks else 0.0,
                    "company_id": company_id,
                    "company_name": company_name,
                    "search_method": "embedding_fallback"
                }
            
            # Step 4: LLM回答生成
            answer = await self.step4_generate_answer(processed_question, similar_chunks, company_name, company_id)
            
            # Step 5: 回答表示（使用されたチャンク情報を含める）
            result = await self.step5_display_answer(answer, metadata, similar_chunks)
            
            logger.info(f"🎉 リアルタイムRAG処理成功完了")
            return result
            
        except Exception as e:
            logger.error(f"❌ リアルタイムRAG処理エラー: {e}")
            error_result = {
                "answer": "申し訳ございませんが、システムエラーが発生しました。しばらく時間をおいてから再度お試しください。",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
            return error_result

# グローバルインスタンス
_realtime_rag_processor = None

def get_realtime_rag_processor() -> Optional[RealtimeRAGProcessor]:
    """リアルタイムRAGプロセッサのインスタンスを取得（シングルトンパターン）"""
    global _realtime_rag_processor
    
    if _realtime_rag_processor is None:
        try:
            _realtime_rag_processor = RealtimeRAGProcessor()
            logger.info("✅ リアルタイムRAGプロセッサ初期化完了")
        except Exception as e:
            logger.error(f"❌ リアルタイムRAGプロセッサ初期化エラー: {e}")
            return None
    
    return _realtime_rag_processor

async def process_question_realtime(question: str, company_id: str = None, company_name: str = "お客様の会社", top_k: int = 20) -> Dict:
    """
    リアルタイムRAG処理の外部呼び出し用関数
    
    Args:
        question: ユーザーの質問
        company_id: 会社ID（オプション）
        company_name: 会社名（回答生成用）
        top_k: 取得する類似チャンク数
    
    Returns:
        Dict: 処理結果（回答、メタデータ等）
    """
    processor = get_realtime_rag_processor()
    if not processor:
        return {
            "answer": "システムの初期化に失敗しました。管理者にお問い合わせください。",
            "error": "RealtimeRAGProcessor initialization failed",
            "timestamp": datetime.now().isoformat(),
            "status": "error"
        }
    
    return await processor.process_realtime_rag(question, company_id, company_name, top_k)

def realtime_rag_available() -> bool:
    """リアルタイムRAGが利用可能かチェック"""
    try:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        return bool(api_key and supabase_url and supabase_key)
    except Exception:
        return False