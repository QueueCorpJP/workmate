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

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class RealtimeRAGProcessor:
    """リアルタイムRAG処理システム"""
    
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
        
        logger.info(f"✅ リアルタイムRAGプロセッサ初期化完了: エンベディング={self.embedding_model} (3072次元)")
    
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
    
    async def step3_similarity_search(self, query_embedding: List[float], company_id: str = None, top_k: int = 10) -> List[Dict]:
        """
        🔍 Step 3. 類似チャンク検索（Top-K）
        Supabaseの chunks テーブルから、ベクトル距離が近いチャンクを pgvector を用いて取得
        """
        logger.info(f"🔍 Step 3: 類似チャンク検索開始 (Top-{top_k})")
        
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # pgvectorを使用したベクトル類似検索SQL
                    sql = """
                    SELECT
                        c.id,
                        c.doc_id,
                        c.chunk_index,
                        c.content,
                        ds.name as document_name,
                        ds.type as document_type,
                        1 - (c.embedding <=> %s) as similarity_score
                    FROM chunks c
                    LEFT JOIN document_sources ds ON ds.id = c.doc_id
                    WHERE c.embedding IS NOT NULL
                    """
                    
                    # ベクトルを文字列形式に変換
                    vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
                    params = [vector_str]
                    
                    # 会社IDフィルタ（オプション）
                    if company_id:
                        sql += " AND c.company_id = %s"
                        params.append(company_id)
                    
                    # ベクトル距離順でソート（Top-K取得）
                    sql += " ORDER BY c.embedding <=> %s LIMIT %s"
                    params.extend([vector_str, top_k])
                    
                    logger.info(f"実行SQL: ベクトル類似検索 (Top-{top_k})")
                    cur.execute(sql, params)
                    results = cur.fetchall()
                    
                    # 結果を辞書のリストに変換
                    similar_chunks = []
                    for row in results:
                        similar_chunks.append({
                            'chunk_id': row['id'],
                            'doc_id': row['doc_id'],
                            'chunk_index': row['chunk_index'],
                            'content': row['content'],
                            'document_name': row['document_name'],
                            'document_type': row['document_type'],
                            'similarity_score': float(row['similarity_score'])
                        })
                    
                    logger.info(f"✅ Step 3完了: {len(similar_chunks)}個の類似チャンクを取得")
                    
                    # デバッグ: 上位3件の類似度を表示
                    for i, chunk in enumerate(similar_chunks[:3]):
                        logger.info(f"  {i+1}. {chunk['document_name']} [チャンク{chunk['chunk_index']}] 類似度: {chunk['similarity_score']:.3f}")
                    
                    return similar_chunks
        
        except Exception as e:
            logger.error(f"❌ Step 3エラー: 類似検索失敗 - {e}")
            raise
    
    async def step4_generate_answer(self, question: str, similar_chunks: List[Dict], company_name: str = "お客様の会社") -> str:
        """
        💡 Step 4. LLMへ送信
        Top-K チャンクと元の質問を Gemini Flash 2.5 に渡して、要約せずに「原文ベース」で回答を生成
        """
        logger.info(f"💡 Step 4: LLM回答生成開始 ({len(similar_chunks)}個のチャンク使用)")
        
        if not similar_chunks:
            logger.warning("類似チャンクが見つからないため、一般的な回答を生成")
            return "申し訳ございませんが、ご質問に関連する情報が見つかりませんでした。より具体的な質問をしていただけますでしょうか。"
        
        try:
            # コンテキスト構築（原文ベース）
            context_parts = []
            total_length = 0
            max_context_length = 100000  # 10万文字制限
            
            for i, chunk in enumerate(similar_chunks):
                chunk_content = f"【参考資料{i+1}: {chunk['document_name']} - チャンク{chunk['chunk_index']}】\n{chunk['content']}\n"
                
                if total_length + len(chunk_content) > max_context_length:
                    logger.info(f"コンテキスト長制限により{i}個のチャンクを使用")
                    break
                
                context_parts.append(chunk_content)
                total_length += len(chunk_content)
            
            context = "\n".join(context_parts)
            
            # プロンプト構築（原文ベース重視）
            prompt = f"""あなたは{company_name}のAIアシスタントです。以下の参考資料を基に、ユーザーの質問に正確に回答してください。

【重要な指示】
1. 参考資料の内容を要約せず、原文の表現をそのまま活用してください
2. 参考資料に記載されている具体的な手順、連絡先、条件等は正確に伝えてください
3. 参考資料にない情報は推測せず、「資料に記載がありません」と明記してください
4. 回答は丁寧で分かりやすい日本語で行ってください

【参考資料】
{context}

【ユーザーの質問】
{question}

【回答】"""

            # Gemini Flash 2.5で回答生成
            response = self.chat_client.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,  # 一貫性重視
                    max_output_tokens=2048,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            if response and response.candidates:
                # 複数パートのレスポンスに対応
                try:
                    # まず response.text を試す（シンプルなレスポンスの場合）
                    answer = response.text.strip()
                except (ValueError, AttributeError):
                    # response.text が使えない場合は parts を使用
                    parts = []
                    for candidate in response.candidates:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                parts.append(part.text)
                    answer = ''.join(parts).strip()
                
                if answer:
                    logger.info(f"✅ Step 4完了: {len(answer)}文字の回答を生成")
                    return answer
                else:
                    logger.error("LLMからの回答が空です")
                    return "申し訳ございませんが、回答の生成に失敗しました。もう一度お試しください。"
            else:
                logger.error("LLMからの回答が空です")
                return "申し訳ございませんが、回答の生成に失敗しました。もう一度お試しください。"
        
        except Exception as e:
            logger.error(f"❌ Step 4エラー: LLM回答生成失敗 - {e}")
            return "申し訳ございませんが、システムエラーが発生しました。しばらく時間をおいてから再度お試しください。"
    
    async def step5_display_answer(self, answer: str, metadata: Dict = None) -> Dict:
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
        
        logger.info(f"✅ リアルタイムRAG処理完了: {len(answer)}文字の回答")
        return result
    
    async def process_realtime_rag(self, question: str, company_id: str = None, company_name: str = "お客様の会社", top_k: int = 10) -> Dict:
        """
        🚀 リアルタイムRAG処理フロー全体の実行
        Step 1〜5を順次実行してリアルタイム回答を生成
        """
        logger.info(f"🚀 リアルタイムRAG処理開始: '{question[:50]}...'")
        
        try:
            # Step 1: 質問入力
            step1_result = await self.step1_receive_question(question, company_id)
            processed_question = step1_result["processed_question"]
            
            # Step 2: エンベディング生成
            query_embedding = await self.step2_generate_embedding(processed_question)
            
            # Step 3: 類似チャンク検索
            similar_chunks = await self.step3_similarity_search(query_embedding, company_id, top_k)
            
            # Step 4: LLM回答生成
            answer = await self.step4_generate_answer(processed_question, similar_chunks, company_name)
            
            # Step 5: 回答表示
            metadata = {
                "original_question": question,
                "processed_question": processed_question,
                "chunks_used": len(similar_chunks),
                "top_similarity": similar_chunks[0]["similarity_score"] if similar_chunks else 0.0,
                "company_id": company_id,
                "company_name": company_name
            }
            
            result = await self.step5_display_answer(answer, metadata)
            
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

async def process_question_realtime(question: str, company_id: str = None, company_name: str = "お客様の会社", top_k: int = 10) -> Dict:
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