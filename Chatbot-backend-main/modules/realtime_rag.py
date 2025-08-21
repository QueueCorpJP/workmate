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

import asyncio
import time
import logging
from typing import List, Dict, Optional, Tuple, Any
from dotenv import load_dotenv
import os
from datetime import datetime
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from supabase import create_client, Client
from modules.database import SupabaseConnection
from modules.token_counter import TokenCounter
from modules.models import ChatResponse, ChatMessage
import urllib.parse  # 追加
import re # 追加
from modules.config import setup_gemini
from modules.multi_gemini_client import get_multi_gemini_client, multi_gemini_available
import json

# 環境変数の読み込み
load_dotenv()

# Geminiモデルの初期化（従来版）
try:
    model = setup_gemini()
except Exception as e:
    logging.error(f"Geminiモデルの初期化に失敗: {e}")
    model = None

# Multi Gemini Clientの初期化（遅延初期化）
multi_gemini_client = None

def get_or_init_multi_gemini_client():
    """Multi Gemini Clientの取得または初期化"""
    global multi_gemini_client
    if multi_gemini_client is None:
        try:
            multi_gemini_client = get_multi_gemini_client()
            logger.info("✅ Multi Gemini Client初期化完了")
        except Exception as e:
            logger.error(f"Multi Gemini Client初期化に失敗: {e}")
            multi_gemini_client = False  # 初期化失敗をマーク
    return multi_gemini_client if multi_gemini_client is not False else None

try:
    from modules.question_splitter import question_splitter
except ImportError:
    logging.warning("question_splitterのインポートに失敗しました。質問分割機能は無効化されます。")
    question_splitter = None

logger = logging.getLogger(__name__)

# safe_print関数の定義（Windows環境でのUnicode対応）
def safe_print(text):
    """Windows環境でのUnicode文字エンコーディング問題を回避する安全なprint関数"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('utf-8', errors='replace').decode('utf-8'))
    except Exception as e:
        print(f"Print error: {e}")

class RealtimeRAGProcessor:
    """リアルタイムRAG処理システム（Gemini質問分析統合版）"""
    
    def __init__(self):
        """初期化"""
        self.use_vertex_ai = False  # Vertex AIを無効化
        self.embedding_model = "gemini-embedding-001"  # Geminiエンベディングモデルを使用
        self.expected_dimensions = 3072  # gemini-embedding-001は3072次元
        
        # API キーの設定
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        self.chat_model = "gemini-2.5-flash"  # 最新のGemini Flash 2.5
        self.db_url = self._get_db_url()
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
        
        # Gemini API の直接呼び出し用URL
        self.api_base_url = "https://generativelanguage.googleapis.com/v1beta"
        
        # Gemini Embeddingクライアントの初期化（埋め込み用）
        try:
            from .multi_api_embedding import get_multi_api_embedding_client, multi_api_embedding_available
            if multi_api_embedding_available():
                self.embedding_client = get_multi_api_embedding_client()
                logger.info(f"✅ Embedding Client初期化: {self.embedding_model} ({self.expected_dimensions}次元)")
            else:
                logger.error("❌ Embedding Clientが利用できません")
                raise ValueError("Embedding Clientの初期化に失敗しました")
        except ImportError:
            logger.error("❌ multi_api_embedding モジュールが見つかりません")
            raise ValueError("Embedding Clientの初期化に失敗しました")
        
        # 🧠 Gemini質問分析システムを無効化（エンベディング検索のみ使用）
        self.gemini_analyzer = None
        logger.info("✅ エンベディング検索のみを使用（Gemini質問分析システムは無効化）")
        
        logger.info(f"✅ リアルタイムRAGプロセッサ初期化完了: エンベディング={self.embedding_model} ({self.expected_dimensions}次元)")

    async def _keyword_search(self, query: str, company_id: Optional[str], limit: int = 40) -> List[Dict]:
        """
        キーワードベースの検索（ILIKEを使用）
        """
        logger.info(f"🔑 Step 3-Keyword: キーワード検索開始 (Top-{limit})")
        # クエリからキーワードを抽出（例：WPD4100389）
        keywords = re.findall(r'[A-Z]+\d+', query)
        if not keywords:
            logger.info("キーワードが見つからないため、キーワード検索をスキップします。")
            return []
        
        search_term = keywords[0] # 簡単のため最初のキーワードを使用
        
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    sql_keyword = """
                    SELECT
                        c.id, c.doc_id, c.chunk_index, c.content,
                        ds.name as document_name, ds.type as document_type,
                        0.9 as similarity_score, -- キーワード検索は高スコア
                        'keyword' as search_method
                    FROM chunks c
                    LEFT JOIN document_sources ds ON ds.id = c.doc_id
                    WHERE c.content ILIKE %s
                    AND ds.active = true
                    """
                    params_keyword = [f"%{search_term}%"]

                    if company_id:
                        sql_keyword += " AND c.company_id = %s"
                        params_keyword.append(company_id)
                    
                    sql_keyword += " LIMIT %s"
                    params_keyword.append(limit)
                    
                    cur.execute(sql_keyword, params_keyword)
                    results = cur.fetchall()
                    logger.info(f"キーワード '{search_term}' で {len(results)} 件ヒットしました。")
                    return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"❌ キーワード検索エラー: {e}")
            return []

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
        # ChatMessageオブジェクトから文字列を取得
        if hasattr(question, 'text'):
            question_text = question.text
        else:
            question_text = str(question)
        
        logger.info(f"✏️ Step 1: 質問受付 - '{question_text[:50]}...'")
        
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
        Gemini embedding-001 を使って、質問文をベクトルに変換（3072次元）
        """
        logger.info(f"🧠 Step 2: エンベディング生成中...")
        
        try:
            # gemini-embedding-001モデルで3072次元を生成
            embedding_vector = await self.embedding_client.generate_embedding(
                question
            )
            
            if embedding_vector and len(embedding_vector) > 0:
                # 次元数チェック
                if len(embedding_vector) != self.expected_dimensions:
                    logger.warning(f"予期しない次元数: {len(embedding_vector)}次元（期待値: {self.expected_dimensions}次元）")
                
                logger.info(f"✅ Step 2完了: {len(embedding_vector)}次元のエンベディング生成成功")
                return embedding_vector
            else:
                raise ValueError("エンベディング生成に失敗しました")
            
        except Exception as e:
            logger.error(f"❌ Step 2エラー: エンベディング生成失敗 - {e}")
            raise
    
    async def step3_similarity_search(self, query_embedding: List[float], company_id: str = None, top_k: int = 50) -> List[Dict]:
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
                    
                    # Convert query vector to proper string format and cast to vector type
                    vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
                    
                    sql_vector = f"""
                    SELECT
                        c.id,
                        c.doc_id,
                        c.chunk_index,
                        c.content,
                        ds.name as document_name,
                        ds.type as document_type,
                        1 - (c.embedding <=> '{vector_str}'::vector) as similarity_score,
                        'vector' as search_method
                    FROM chunks c
                    LEFT JOIN document_sources ds ON ds.id = c.doc_id
                    WHERE c.embedding IS NOT NULL
                      AND c.content IS NOT NULL
                      AND LENGTH(c.content) > 10
                      AND ds.active = true
                    """
                    
                    params_vector = []
                    
                    # 会社IDフィルタ（オプション）
                    if company_id:
                        sql_vector += " AND c.company_id = %s"
                        params_vector.append(company_id)
                    
                    # ベクトル距離順でソート
                    sql_vector += f" ORDER BY c.embedding <=> '{vector_str}'::vector LIMIT %s"
                    params_vector.append(top_k)
                    
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
                    if pdf_vector_count < 10:  # PDFファイルの結果が10件未満の場合
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
                    if file_type_distribution.get('pdf', 0) < 5:
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
    
    async def step4_generate_answer(self, question: str, similar_chunks: List[Dict], company_name: str = "お客様の会社", company_id: str = None) -> Dict[str, Any]:
        """
        💡 Step 4. LLMへ送信
        Top-K チャンクと元の質問を Gemini Flash 2.5 に渡して、要約せずに「原文ベース」で回答を生成
        """
        logger.info(f"💡 Step 4: LLM回答生成開始 ({len(similar_chunks) if similar_chunks else 0}個のチャンク使用)")
        
        if not similar_chunks or len(similar_chunks) == 0:
            logger.warning("類似チャンクが見つからないため、一般的な回答を生成")
            return {
                "answer": "申し訳ございませんが、ご質問に関連する情報が見つかりませんでした。より具体的な質問をしていただけますでしょうか。",
                "used_chunks": []
            }
        
        try:
            # 🔍 Step 4: コンテキスト構築ログ
            print("\n" + "="*80)
            print(f"💡 【Step 4: LLM回答生成 - コンテキスト構築】")
            print(f"📊 利用可能チャンク数: {len(similar_chunks)}個")
            
            # 動的コンテキスト長制限の計算
            question_length = len(question)
            base_limit = 300000  # 基本制限を30万文字に増加（50チャンク対応）
            
            if question_length > 5000:
                # 長い質問の場合、コンテキスト制限を増やす
                max_context_length = min(800000, base_limit + (question_length * 3))  # 最大80万文字
                print(f"📏 動的コンテキスト長: {max_context_length:,}文字 (長い質問対応)")
            elif question_length > 2000:
                max_context_length = min(600000, base_limit + (question_length * 2))  # 最大60万文字
                print(f"📏 動的コンテキスト長: {max_context_length:,}文字 (中程度の質問)")
            else:
                max_context_length = base_limit  # 30万文字
                print(f"📏 標準コンテキスト長: {max_context_length:,}文字")
            
            print("="*80)
            
            # コンテキスト構築（原文ベース）
            context_parts = []
            total_length = 0
            used_chunks = []
            
            for i, chunk in enumerate(similar_chunks):
                chunk_content = f"【{chunk['document_name']}】\n{chunk['content']}\n"
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
            
            # プロンプト長の最適化（長すぎる場合は短縮）
            if len(context) > 200000:  # 20万文字を超える場合（50チャンク対応のため増加）
                logger.warning(f"⚠️ コンテキストが長すぎます ({len(context):,}文字) - 短縮処理を実行")
                # 各チャンクを短縮
                shortened_parts = []
                for part in context_parts[:70]:  # 最大70チャンク（増加）
                    if len(part) > 5000:  # チャンク当たりの制限も緩和
                        shortened_parts.append(part[:5000] + "...(省略)")
                    else:
                        shortened_parts.append(part)
                context = "\n".join(shortened_parts)
                logger.info(f"📏 短縮後コンテキスト長: {len(context):,}文字")
            
            print(f"📋 最終コンテキスト情報:")
            print(f"   ✅ 使用チャンク数: {len(used_chunks)}個")
            print(f"   📏 総文字数: {len(context):,}文字")
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
            
            # 🎯 複雑な質問の検出（表形式、複数条件など）
            complex_indicators = [
                '表形式', '表で', 'テーブル', '一覧表', '詳細を表', 
                '×', '✕', '物件番号ごと',
                '条件:', '指示:', '注意事項', '表示条件'
            ]
            
            is_complex_query = any(indicator in question for indicator in complex_indicators)
            is_table_query = any(table in question for table in ['表形式', '表で', 'テーブル', '物件番号ごと'])
            
            logger.info(f"🔍 質問分析: 複雑={is_complex_query}, 表形式={is_table_query}")
            
            # 複雑な質問用の簡潔なプロンプト
            if is_complex_query or is_table_query:
                logger.info("📊 複雑な質問検出 - 専用プロンプトを使用")
                prompt = f"""{special_instructions_text}あなたは{company_name}の専門アシスタントです。

【重要な指針】
• 提供された参考資料を正確に分析してください
• 表形式での回答が求められた場合、正確な表形式で出力してください
• ファイル名のみを出典として記載してください（例：「○○.xlsx」「○○.csv」）

【質問】
{question}

【参考資料】
{context}

上記の参考資料に基づいて、正確かつ詳細にお答えいたします："""
            
            else:
                # 通常の質問用プロンプト（従来通り）
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

**【情報の出典・引用に関する重要なルール】**
• ファイル名のみ言及可能：「○○.xlsx」「○○.csv」「○○.pdf」など
• ❌ 絶対に出力してはいけない内容：
  - チャンク番号（例：「チャンク232」「チャンク#45」）
  - 行番号（例：「行12」「12行目」）
  - 内部ID（例：「chunk_id: 123」）
  - データベース構造情報（例：「テーブル名」「カラム名」）
  - システム内部情報（例：「参考資料1:」「参考資料2:」など）

• 専門的な内容も分かりやすく説明
• 実際に参照した資料のファイル名を自然な文章の中で言及してください
• 文末には「ご不明な点がございましたら、お気軽にお申し付けください。」を追加

ご質問：
{question}

参考となる資料：
{context}

上記の参考資料を基に、柔軟かつ積極的にご質問にお答えいたします："""

            logger.info("🤖 Gemini Flash 2.5に回答生成を依頼中...")
            logger.info(f"📏 プロンプト長: {len(prompt):,}文字")
            
            # Multi Gemini Client を使用した API 呼び出し（レート制限対応）
            generation_config = {
                "temperature": 0.05 if (is_complex_query or is_table_query) else 0.1,  # 複雑な質問は更に確定的に
                "maxOutputTokens": 1048576,  # 1Mトークン（実質無制限）
                "topP": 0.7 if (is_complex_query or is_table_query) else 0.8,  # より集中的な応答
                "topK": 20 if (is_complex_query or is_table_query) else 40  # 選択肢を絞る
            }
            
            try:
                # Multi Gemini Client を使用（複数APIキー対応）
                client = get_or_init_multi_gemini_client()
                if client and multi_gemini_available():
                    logger.info("🔄 Multi Gemini Client使用でAPI呼び出し開始")
                    response_data = await client.generate_content(prompt, generation_config)
                    logger.info("📥 Multi Gemini Clientからのレスポンス受信完了")
                else:
                    # フォールバック: 従来の単一APIキー方式
                    logger.warning("⚠️ Multi Gemini Client利用不可、従来方式でフォールバック")
                    api_url = f"{self.api_base_url}/models/{self.chat_model}:generateContent"
                    
                    headers = {
                        "Content-Type": "application/json",
                        "x-goog-api-key": self.api_key
                    }
                    
                    request_data = {
                        "contents": [
                            {
                                "parts": [
                                    {
                                        "text": prompt
                                    }
                                ]
                            }
                        ],
                        "generationConfig": generation_config
                    }
                    
                    response = requests.post(api_url, headers=headers, json=request_data, timeout=600)
                    response.raise_for_status()
                    response_data = response.json()
                logger.info(f"🔍 Geminiレスポンス構造: {list(response_data.keys())}")
                
                answer = None
                
                if "candidates" in response_data and response_data["candidates"]:
                    logger.info(f"📋 候補数: {len(response_data['candidates'])}")
                    
                    try:
                        candidate = response_data["candidates"][0]
                        if "finishReason" in candidate:
                            logger.info(f"🔍 finishReason: {candidate['finishReason']}")
                        
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            if parts and "text" in parts[0]:
                                answer = parts[0]["text"]
                                logger.info(f"✅ 回答取得成功: {len(answer)}文字")
                                
                                # 🎯 実際に使用されたソースの特定（回答内容との照合）
                                actually_used_sources = []
                                actually_used_chunks = []
                                
                                if answer and len(answer.strip()) > 0:
                                    logger.info("🔍 回答内容と照合して実際に使用されたソースを特定中...")
                                    
                                    for chunk in used_chunks:
                                        chunk_content = chunk.get('content', '')
                                        chunk_doc_name = chunk.get('document_name', '')
                                        
                                        if not chunk_content or not chunk_doc_name or chunk_doc_name == 'None':
                                            continue
                                        
                                        # チャンク内容が実際に回答で使用されているかをチェック
                                        is_used = self._is_chunk_actually_used(answer, chunk_content, chunk)
                                        
                                        if is_used:
                                            actually_used_chunks.append(chunk)
                                            if chunk_doc_name not in actually_used_sources:
                                                actually_used_sources.append(chunk_doc_name)
                                                logger.info(f"✅ 実使用ソース確定: {chunk_doc_name}")
                                        else:
                                            logger.info(f"❌ 未使用ソース除外: {chunk_doc_name}")
                                    
                                    # 実際に使用されたチャンクがない場合の安全装置（より制限的に）
                                    if not actually_used_sources and used_chunks:
                                        logger.warning("⚠️ 実使用ソースが特定できませんでした - 上位2つのチャンクのみ使用")
                                        for chunk in used_chunks[:2]:
                                            chunk_doc_name = chunk.get('document_name', '')
                                            if chunk_doc_name and chunk_doc_name.strip() and chunk_doc_name != 'None':
                                                if chunk_doc_name not in actually_used_sources:
                                                    actually_used_sources.append(chunk_doc_name)
                                                    actually_used_chunks.append(chunk)
                                else:
                                    # 回答が空の場合も制限的に（フォールバック）
                                    logger.warning("⚠️ 回答が空のため、上位5つのチャンクをソースとして使用")
                                    for chunk in used_chunks[:5]:
                                        chunk_doc_name = chunk.get('document_name', '')
                                        if chunk_doc_name and chunk_doc_name.strip() and chunk_doc_name != 'None':
                                            if chunk_doc_name not in actually_used_sources:
                                                actually_used_sources.append(chunk_doc_name)
                                                actually_used_chunks.append(chunk)
                                
                                # 使用されたチャンクを更新
                                used_chunks = actually_used_chunks
                                
                                logger.info(f"📁 実際に使用されたソース: {actually_used_sources}")
                                logger.info(f"🎯 実際に使用されたチャンク数: {len(actually_used_chunks)}件")
                                
                            else:
                                logger.warning("⚠️ partsが空または'text'キーがありません")
                        else:
                            logger.warning("⚠️ candidate に 'content' または 'parts' がありません")
                    
                    except Exception as parse_error:
                        logger.error(f"❌ レスポンス解析エラー: {parse_error}")
                        answer = None
                
                else:
                    logger.warning("⚠️ 無効なレスポンスまたは候補なし")
                    
            except Exception as e:
                logger.error(f"❌ LLM回答生成エラー: {e}")
                
                # Multi Gemini Clientの状態情報をログ出力
                client = get_or_init_multi_gemini_client()
                if client:
                    try:
                        status_info = client.get_status_info()
                        logger.info("📊 Multi Gemini Client状態:")
                        for client_name, info in status_info.items():
                            logger.info(f"   {client_name}: {info['status']} (リトライ: {info['retry_count']}/{client.max_retries})")
                    except Exception as status_error:
                        logger.error(f"状態情報取得エラー: {status_error}")
                
                # HTTPExceptionとして再発生（FastAPIが適切に処理）
                from fastapi import HTTPException
                if "429" in str(e) or "rate limit" in str(e).lower() or "quota exceeded" in str(e).lower():
                    raise HTTPException(status_code=429, detail="API制限のため、しばらく待ってから再度お試しください")
                else:
                    raise HTTPException(status_code=500, detail=f"LLM回答生成失敗: {str(e)}")
            
            # 回答の検証と処理
            if answer and len(answer.strip()) > 0:
                logger.info(f"✅ Step 4完了: {len(answer)}文字の回答を生成")
                logger.info(f"📝 回答プレビュー: {answer[:100]}...")
                
                # 🎯 回答の長さ制限（21万文字は長すぎる）
                max_answer_length = 6000  # 6千文字制限（さらに短縮）
                if len(answer) > max_answer_length:
                    logger.warning(f"⚠️ 回答が長すぎます ({len(answer):,}文字) - {max_answer_length:,}文字に短縮")
                    # 文章の切れ目で短縮する
                    truncated = answer[:max_answer_length]
                    last_period = truncated.rfind('。')
                    last_newline = truncated.rfind('\n')
                    cut_point = max(last_period, last_newline)
                    if cut_point > max_answer_length - 1000:  # 切れ目が近い場合
                        answer = answer[:cut_point + 1] + "\n\n...(回答が長いため省略されました。より具体的な質問をしていただくと、詳細な回答を提供できます)"
                    else:
                        answer = answer[:max_answer_length] + "\n\n...(回答が長いため省略されました。より具体的な質問をしていただくと、詳細な回答を提供できます)"
                    logger.info(f"📏 短縮後回答長: {len(answer):,}文字")
                
                # 回答が短すぎる場合の処理
                if len(answer) < 50:
                    logger.warning(f"⚠️ 回答が短すぎます（{len(answer)}文字）- 補強処理を実行")
                    fallback_answer = f"""参考資料を確認いたしました。

{answer}

より詳細な情報が必要でしたら、具体的な項目をお教えください。参考資料から正確な情報を提供いたします。"""
                    return {
                        "answer": fallback_answer,
                        "used_chunks": used_chunks
                    }
                
                return {
                    "answer": answer,
                    "used_chunks": used_chunks
                }
            else:
                logger.error("❌ LLMからの回答が空または取得できませんでした")
                # response変数が定義されているかチェック
                if 'response' in locals() and response is not None:
                    logger.error(f"   レスポンス詳細: {response}")
                else:
                    logger.error("   レスポンス詳細: レスポンスが取得できませんでした（タイムアウトまたは接続エラー）")
                
                # 🛠️ 構造化フォールバック - 複雑な質問に対する代替処理
                fallback_parts = []
                
                # エラーの詳細分析
                question_length = len(question)
                context_length = len(context) if 'context' in locals() else 0
                
                # 複雑な質問の場合の特別な構造化フォールバック
                if is_complex_query or is_table_query:
                    logger.info("🛠️ 複雑な質問用の構造化フォールバック開始")
                    
                    # 顧客情報を抽出
                    customer_info = self._extract_customer_info(question, used_chunks)
                    if customer_info:
                        fallback_parts.append("📋 **検索結果の概要**")
                        fallback_parts.append(f"顧客コード: {customer_info.get('code', '不明')}")
                        fallback_parts.append(f"会社名: {customer_info.get('name', '不明')}")
                        fallback_parts.append("")
                    
                    # 関連データを構造化して表示
                    extracted_data = self._extract_structured_data(used_chunks, question)
                    if extracted_data:
                        fallback_parts.append("📊 **関連情報**")
                        for data_item in extracted_data[:5]:  # 最大5件
                            fallback_parts.append(f"• {data_item}")
                        fallback_parts.append("")
                    
                    fallback_parts.append("⚠️ **処理状況**")
                    fallback_parts.append("処理でエラーが発生しました。以下の代替案をご提案いたします：")
                    fallback_parts.append("")
                    fallback_parts.append("📝 **推奨アプローチ**")
                    fallback_parts.append("1. 顧客コードと会社名での基本検索を先に実行")
                    fallback_parts.append("2. 契約情報の確認を段階的に実施")
                    
                else:
                    # 通常の質問のフォールバック
                    if question_length > 8000:
                        fallback_parts.append("質問が非常に長いため、処理に問題が発生しました。")
                        fallback_parts.append("以下の方法をお試しください：")
                        fallback_parts.append("1. 質問を複数の小さな質問に分割してください")
                        fallback_parts.append("2. 最も重要な部分から順番にお聞きください")
                        fallback_parts.append("3. 具体的な項目名やキーワードを含めてください")
                    elif context_length > 300000:  # 30万文字以上
                        fallback_parts.append("参考資料が大量にあるため、処理に時間がかかっています。")
                        fallback_parts.append("より具体的なキーワードで絞り込んだ質問をしていただけますか？")
                    else:
                        fallback_parts.append("システム的な問題により詳細な回答を生成できませんでした。")
                
                # 検索できた参考資料の情報を提供
                if used_chunks:
                    fallback_parts.append(f"\n検索では{len(used_chunks)}件の関連資料が見つかりました：")
                    
                    # 複数のチャンクから情報を抽出
                    for i, chunk in enumerate(used_chunks[:3]):  # 最大3つのチャンク
                        if chunk.get('content'):
                            content_preview = chunk['content'][:200].replace('\n', ' ')
                            doc_name = chunk.get('document_name', f'資料{i+1}')
                            fallback_parts.append(f"\n【{doc_name}】")
                            fallback_parts.append(f"{content_preview}...")
                    
                    if len(used_chunks) > 3:
                        fallback_parts.append(f"\n他にも{len(used_chunks) - 3}件の関連資料があります。")
                
                fallback_parts.append("\n💡 改善提案：")
                fallback_parts.append("• より具体的な質問にしてください")
                fallback_parts.append("• 知りたい項目を明確にしてください")  
                fallback_parts.append("• 質問を分割して段階的にお聞きください")
                
                # フォールバック時にも実際に使用されたソース情報を構築
                fallback_sources = []
                seen_names = set()
                for chunk in used_chunks[:3]:  # 最大3つのソース
                    doc_name = chunk.get('document_name', 'Unknown Document')
                    if doc_name not in seen_names and doc_name not in ['システム回答', 'unknown', 'Unknown']:
                        fallback_sources.append({
                            "name": doc_name,
                            "document_name": doc_name,
                            "document_type": chunk.get('document_type', 'unknown'),
                            "similarity_score": chunk.get('similarity_score', 0.0)
                        })
                        seen_names.add(doc_name)
                
                return {
                    "answer": "\n".join(fallback_parts),
                    "used_chunks": used_chunks,
                    "sources": fallback_sources,
                    "source_documents": fallback_sources
                }
        
        except Exception as e:
            logger.error(f"❌ Step 4エラー: LLM回答生成失敗 - {e}")
            import traceback
            logger.error(f"詳細エラー: {traceback.format_exc()}")
            
            # エラー時でも可能な限り情報を提供
            error_response_parts = ["申し訳ございませんが、システムエラーが発生しました。"]
            
            if used_chunks and len(used_chunks) > 0:
                error_response_parts.append(f"\n検索では{len(used_chunks)}件の関連資料が見つかりました。")
                if used_chunks[0].get('content'):
                    first_content = used_chunks[0]['content'][:200]
                    error_response_parts.append(f"関連情報の一部: {first_content}...")
            
            error_response_parts.append("\nしばらく時間をおいてから再度お試しください。")
            
            # エラー時にも可能な限りソース情報を構築
            error_sources = []
            seen_names = set()
            for chunk in used_chunks[:2]:  # エラー時は最大2つのソース
                doc_name = chunk.get('document_name', 'Unknown Document')
                if doc_name not in seen_names and doc_name not in ['システム回答', 'unknown', 'Unknown']:
                    error_sources.append({
                        "name": doc_name,
                        "document_name": doc_name,
                        "document_type": chunk.get('document_type', 'unknown'),
                        "similarity_score": chunk.get('similarity_score', 0.0)
                    })
                    seen_names.add(doc_name)
            
            return {
                "answer": "\n".join(error_response_parts),
                "used_chunks": [],  # エラー時は空のリスト
                "sources": error_sources,
                "source_documents": error_sources
            }
    
    def _extract_customer_info(self, question: str, chunks: List[Dict]) -> Dict[str, str]:
        """質問とチャンクから顧客情報を抽出"""
        customer_info = {}
        
        # 質問から顧客コードを抽出
        import re
        code_match = re.search(r'SS\d{7}', question)
        if code_match:
            customer_info['code'] = code_match.group()
        
        # 質問から会社名を抽出
        company_patterns = [
            r'会社名：「([^」]+)」',
            r'会社名:「([^」]+)」',
            r'株式会社[^\s」]+',
            r'㈱[^\s」]+',
            r'\(株\)[^\s」]+'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, question)
            if match:
                customer_info['name'] = match.group(1) if match.groups() else match.group()
                break
        
        # チャンクからも情報を補完
        if not customer_info.get('name'):
            for chunk in chunks[:3]:  # 最初の3つのチャンクをチェック
                content = chunk.get('content', '')
                if '株式会社' in content:
                    # 株式会社を含む部分を抽出
                    company_match = re.search(r'株式会社[^\s,、|]+', content)
                    if company_match:
                        customer_info['name'] = company_match.group()
                        break
        
        return customer_info
    
    def _extract_structured_data(self, chunks: List[Dict], question: str) -> List[str]:
        """チャンクから構造化されたデータを抽出"""
        extracted_data = []
        
        # 重要なキーワード
        important_keywords = ['設置', '完了', '契約', '月額', '期間', 'WPC', 'CB', 'ステータス']
        
        for chunk in chunks[:5]:  # 最大5つのチャンク
            content = chunk.get('content', '')
            doc_name = chunk.get('document_name', 'Unknown')
            
            # キーワードマッチング
            for keyword in important_keywords:
                if keyword in content and keyword.lower() in question.lower():
                    # キーワード周辺の文脈を抽出
                    lines = content.split('\n')
                    for line in lines:
                        if keyword in line and len(line.strip()) > 10:
                            # データっぽい行を抽出
                            if any(char in line for char in [':', '：', '|', ',']):
                                extracted_data.append(f"{doc_name}: {line.strip()}")
                                break
                    break
            
            if len(extracted_data) >= 5:  # 最大5件
                break
        
        return list(set(extracted_data))  # 重複除去
    
    def _is_chunk_actually_used(self, answer: str, chunk_content: str, chunk: Dict) -> bool:
        """回答の内容とチャンクの内容を照合して、実際に使用されているかを判定"""
        if not answer or not chunk_content:
            return False
        
        # 1. キーワードマッチング（重要な単語やフレーズの照合）
        import re
        
        # チャンクから重要なキーワードを抽出（3文字以上の単語）
        chunk_keywords = re.findall(r'\b\w{3,}\b', chunk_content)
        # 数値パターン（日付、金額、コードなど）も抽出
        chunk_numbers = re.findall(r'\b\d+\b', chunk_content)
        # 特殊なパターン（会社名、コードなど）
        chunk_patterns = re.findall(r'[A-Z]{2}\d{7}|株式会社[^\s,、]+|㈱[^\s,、]+', chunk_content)
        
        all_chunk_elements = chunk_keywords + chunk_numbers + chunk_patterns
        
        if not all_chunk_elements:
            return False
        
        # 2. 回答内での一致率を計算
        matched_elements = 0
        total_elements = len(all_chunk_elements[:20])  # 最大20要素で判定
        
        for element in all_chunk_elements[:20]:
            if len(element) >= 3:  # 3文字以上の要素のみ
                # 完全一致
                if element in answer:
                    matched_elements += 1
                # 部分一致（6文字以上の要素の場合）
                elif len(element) >= 6:
                    if any(element in word or word in element for word in answer.split()):
                        matched_elements += 0.5
        
        match_ratio = matched_elements / total_elements if total_elements > 0 else 0
        
        # 3. 特別なパターンでの重み付け
        special_bonus = 0
        
        # 会社名や顧客コードなどの重要情報が一致する場合
        for pattern in chunk_patterns:
            if pattern in answer:
                special_bonus += 0.3
        
        # 日付や金額などの具体的な数値が一致する場合
        important_numbers = [num for num in chunk_numbers if len(num) >= 4]  # 4桁以上の数字
        for num in important_numbers:
            if num in answer:
                special_bonus += 0.2
        
        final_score = match_ratio + special_bonus
        
        # 4. 判定閾値（一律で厳格にしてチャンク数を削減）
        threshold = 0.3  # 全て統一した閾値で判定
        
        is_used = final_score >= threshold
        
        # デバッグログ
        chunk_doc_name = chunk.get('document_name', 'Unknown')
        if is_used:
            logger.info(f"   ✅ チャンク使用確認: {chunk_doc_name} (スコア: {final_score:.2f}, 閾値: {threshold})")
        else:
            logger.info(f"   ❌ チャンク未使用: {chunk_doc_name} (スコア: {final_score:.2f}, 閾値: {threshold})")
        
        return is_used
    
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
        
        # 使用されたチャンクの詳細情報を追加 - main.pyが期待する形式で返す
        if used_chunks:
            source_documents = []
            seen_names = set()
            for chunk in used_chunks[:5]:  # 最大5個のソース文書
                doc_name = chunk.get('document_name', 'Unknown Document')
                # 重複する名前は除外し、システム回答等は除外
                if doc_name not in seen_names and doc_name not in ['システム回答', 'unknown', 'Unknown']:
                    doc_info = {
                        "name": doc_name,  # main.pyが期待するフィールド名
                        "filename": doc_name,  # 後方互換性
                        "document_name": doc_name,  # 後方互換性
                        "document_type": chunk.get('document_type', 'unknown'),
                        "similarity_score": chunk.get('similarity_score', 0.0)
                    }
                    source_documents.append(doc_info)
                    seen_names.add(doc_name)
            
            result["sources"] = source_documents  # main.pyが期待するフィールド名
            result["source_documents"] = source_documents  # 後方互換性のため残す
            result["total_sources"] = len(used_chunks)
        
        logger.info(f"✅ リアルタイムRAG処理完了: {len(answer)}文字の回答")
        return result
    
    async def process_realtime_rag(self, question: str, company_id: str = None, company_name: str = "お客様の会社", top_k: int = 50) -> Dict:
        """
        🚀 リアルタイムRAG処理フロー全体の実行（Gemini質問分析統合版）
        新しい3段階アプローチ: Gemini分析 → SQL検索 → Embedding検索（フォールバック）
        """
        # ChatMessageオブジェクトから文字列を取得
        if hasattr(question, 'text'):
            question_text = question.text
        else:
            question_text = str(question)
        
        logger.info(f"🚀 リアルタイムRAG処理開始: '{question_text[:50]}...'")
        
        # 長い質問の自動分割処理
        if question_splitter and question_splitter.should_split_question(question_text):
            logger.info(f"📝 長い質問を検出（{len(question_text)}文字）- 自動分割処理を開始")
            
            try:
                # 質問を分割
                segments = question_splitter.split_question(question_text)
                logger.info(f"✂️ 質問を{len(segments)}個のセグメントに分割")
                
                # 各セグメントを並列処理
                segment_responses = []
                for i, segment in enumerate(segments):
                    logger.info(f"🔍 セグメント{i+1}処理: {segment.text[:50]}...")
                    try:
                        # 分割されたセグメントを再帰的に処理（分割は1回のみ）
                        response = await self._process_single_segment(segment.text, company_id, company_name, top_k)
                        segment_responses.append(response)
                    except Exception as e:
                        logger.error(f"❌ セグメント{i+1}処理エラー: {e}")
                        # エラーの場合はスキップして続行
                        continue
                
                # 回答をマージ
                if segment_responses:
                    merged_result = question_splitter.merge_segments_responses(segment_responses)
                    logger.info(f"✅ 分割質問処理完了: {len(merged_result['answer'])}文字の統合回答")
                    return merged_result
                else:
                    logger.warning("⚠️ 全セグメント処理失敗 - 通常処理にフォールバック")
                    # フォールバックして通常処理
            
            except Exception as e:
                logger.error(f"❌ 質問分割処理エラー: {e} - 通常処理にフォールバック")
                # エラーの場合は通常処理にフォールバック
        
        # 通常の処理フロー（分割しない場合または分割失敗時）
        return await self._process_single_segment(question_text, company_id, company_name, top_k)
    
    async def _process_single_segment(self, question_text: str, company_id: str = None, company_name: str = "お客様の会社", top_k: int = 50) -> Dict:
        """単一セグメントの処理（従来のprocess_realtime_ragの内容）"""
        try:
            # Step 1: 質問入力
            step1_result = await self.step1_receive_question(question_text, company_id)
            processed_question = step1_result["processed_question"]
            
            # Step 2: エンベディング生成
            query_embedding = await self.step2_generate_embedding(processed_question)

            # Step 3: ベクトル検索とキーワード検索を並列実行
            search_tasks = [
                self.step3_similarity_search(query_embedding, company_id, top_k),
                self._keyword_search(processed_question, company_id, 30) # キーワード検索は30件まで
            ]
            results_list = await asyncio.gather(*search_tasks, return_exceptions=True)

            vector_results = results_list[0] if not isinstance(results_list[0], Exception) else []
            keyword_results = results_list[1] if not isinstance(results_list[1], Exception) else []

            # 結果の統合と重複除去
            all_chunks = {r['chunk_id']: r for r in vector_results}
            for r in keyword_results:
                # キーワード検索結果を優先的に上書き
                all_chunks[r['id']] = {
                    'chunk_id': r['id'],
                    'doc_id': r['doc_id'],
                    'chunk_index': r['chunk_index'],
                    'content': r['content'],
                    'document_name': r['document_name'],
                    'document_type': r['document_type'],
                    'similarity_score': float(r['similarity_score']),
                    'search_method': r['search_method']
                }

            # スコアでソート
            sorted_chunks = sorted(all_chunks.values(), key=lambda x: x['similarity_score'], reverse=True)
            
            # 最終的なチャンクリスト
            similar_chunks = sorted_chunks[:top_k]
            
            metadata = {
                "original_question": question_text, # セグメントの質問をメタデータに含める
                "processed_question": processed_question,
                "chunks_used": len(similar_chunks),
                "top_similarity": similar_chunks[0]["similarity_score"] if similar_chunks else 0.0,
                "company_id": company_id,
                "company_name": company_name,
                "search_method": "hybrid_search" # ハイブリッド検索に変更
            }
            
            # Step 4: LLM回答生成
            generation_result = await self.step4_generate_answer(processed_question, similar_chunks, company_name, company_id)
            answer = generation_result["answer"]
            actually_used_chunks = generation_result["used_chunks"]
            
            # Step 5: 回答表示（実際に使用されたチャンク情報を含める）
            result = await self.step5_display_answer(answer, metadata, actually_used_chunks)
            
            logger.info(f"🎉 リアルタイムRAG処理成功完了")
            return result
            
        except Exception as e:
            logger.error(f"❌ リアルタイムRAG処理エラー: {e}")
            
            # エラー時でも可能な限りソース情報を提供
            error_sources = []
            if 'similar_chunks' in locals() and similar_chunks:
                seen_names = set()
                for chunk in similar_chunks[:2]:  # エラー時は最大2つのソース
                    doc_name = chunk.get('document_name', 'Unknown Document')
                    if doc_name not in seen_names and doc_name not in ['システム回答', 'unknown', 'Unknown']:
                        error_sources.append({
                            "name": doc_name,
                            "document_name": doc_name,
                            "document_type": chunk.get('document_type', 'unknown'),
                            "similarity_score": chunk.get('similarity_score', 0.0)
                        })
                        seen_names.add(doc_name)
            
            error_result = {
                "answer": "申し訳ございませんが、システムエラーが発生しました。しばらく時間をおいてから再度お試しください。",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "sources": error_sources,
                "source_documents": error_sources
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

async def process_question_realtime(question: str, company_id: str = None, company_name: str = "お客様の会社", top_k: int = 50) -> Dict:
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