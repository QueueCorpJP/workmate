"""
🎯 超高精度RAGシステム
「ほっとらいふ」などの固有名詞検索に特化した最高精度のRAG処理
"""

import os
import logging
import asyncio
import re
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
# 新しいGoogle GenAI SDKをインポート
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    types = None
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class UltraAccurateRAGProcessor:
    """超高精度RAG処理システム"""
    
    def __init__(self):
        """初期化"""
        self.use_vertex_ai = os.getenv("USE_VERTEX_AI", "true").lower() == "true"
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-multilingual-embedding-002")
        self.expected_dimensions = 768 if "text-multilingual-embedding-002" in self.embedding_model else 3072
        
        # API キーの設定
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        self.chat_model = "gemini-2.5-flash"
        self.db_url = self._get_db_url()
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
        
        # Gemini APIクライアントの初期化（チャット用）
        genai.configure(api_key=self.api_key)
        self.chat_client = genai.GenerativeModel(self.chat_model)
        
        # 超高精度検索システムの初期化
        try:
            from .ultra_accurate_search import get_ultra_accurate_search_instance, ultra_accurate_search_available
            if ultra_accurate_search_available():
                self.ultra_search = get_ultra_accurate_search_instance()
                logger.info(f"✅ 超高精度検索システム統合: {self.embedding_model} ({self.expected_dimensions}次元)")
            else:
                logger.error("❌ 超高精度検索システムが利用できません")
                raise ValueError("超高精度検索システムの初期化に失敗しました")
        except ImportError as e:
            logger.error(f"❌ 超高精度検索システムのインポートエラー: {e}")
            raise ValueError("超高精度検索システムが利用できません")
        
        # 回答品質パラメータ
        self.max_context_length = 150000  # コンテキスト長を大幅に増加
        self.min_confidence_threshold = 0.1  # 信頼度閾値を下げる
        self.context_diversity_threshold = 0.8  # コンテキストの多様性閾値
        
        logger.info(f"✅ 超高精度RAGプロセッサ初期化完了")
    
    def _get_db_url(self) -> str:
        """データベースURLを構築"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL と SUPABASE_KEY 環境変数が設定されていません")
        
        if "supabase.co" in supabase_url:
            project_id = supabase_url.split("://")[1].split(".")[0]
            return f"postgresql://postgres.{project_id}:{os.getenv('DB_PASSWORD', '')}@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"
        else:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL 環境変数が設定されていません")
            return db_url
    
    def analyze_query_intent(self, question: str) -> Dict:
        """クエリの意図分析"""
        intent_analysis = {
            'query_type': 'general',
            'is_company_specific': False,
            'is_contact_inquiry': False,
            'is_service_inquiry': False,
            'confidence_boost': 1.0,
            'search_strategy': 'standard'
        }
        
        question_lower = question.lower()
        
        # 会社名・固有名詞の検出
        company_patterns = [
            'ほっとらいふ', 'ホットライフ', 'hotlife', 'hot life',
            'ntt', 'エヌティティ', 'ドコモ', 'docomo'
        ]
        
        for pattern in company_patterns:
            if pattern in question_lower:
                intent_analysis['is_company_specific'] = True
                intent_analysis['confidence_boost'] = 0.5  # 閾値を大幅に下げる
                intent_analysis['search_strategy'] = 'company_focused'
                break
        
        # 連絡先問い合わせの検出
        contact_patterns = [
            '連絡先', '電話', 'tel', 'メール', 'mail', '問い合わせ', 'お問い合わせ',
            '連絡', 'コンタクト', 'contact', '窓口'
        ]
        
        for pattern in contact_patterns:
            if pattern in question_lower:
                intent_analysis['is_contact_inquiry'] = True
                intent_analysis['query_type'] = 'contact'
                break
        
        # サービス問い合わせの検出
        service_patterns = [
            'サービス', 'service', '提供', '利用', '使用', '機能', '料金', '価格'
        ]
        
        for pattern in service_patterns:
            if pattern in question_lower:
                intent_analysis['is_service_inquiry'] = True
                intent_analysis['query_type'] = 'service'
                break
        
        logger.info(f"🧠 クエリ意図分析: {intent_analysis}")
        return intent_analysis
    
    async def step1_receive_question(self, question: str, company_id: str = None) -> Dict:
        """
        ✏️ Step 1. 質問入力（超高精度版）
        質問の前処理と意図分析を実行
        """
        # ChatMessageオブジェクトから文字列を取得
        if hasattr(question, 'text'):
            question_text = question.text
        else:
            question_text = str(question)
        
        logger.info(f"✏️ Step 1: 超高精度質問受付 - '{question_text[:50]}...'")
        
        if not question or not question.strip():
            raise ValueError("質問が空です")
        
        # 質問の前処理
        processed_question = question.strip()
        
        # 意図分析
        intent_analysis = self.analyze_query_intent(processed_question)
        
        return {
            'original_question': question,
            'processed_question': processed_question,
            'company_id': company_id,
            'intent_analysis': intent_analysis,
            'timestamp': datetime.now().isoformat(),
            'step': 'question_received'
        }
    
    async def step2_ultra_accurate_search(self, question_data: Dict) -> Dict:
        """
        🔍 Step 2. 超高精度ベクトル検索
        意図に基づいた最適化された検索を実行
        """
        logger.info(f"🔍 Step 2: 超高精度ベクトル検索開始")
        
        question = question_data['processed_question']
        company_id = question_data.get('company_id')
        intent_analysis = question_data['intent_analysis']
        
        try:
            # 検索戦略に基づいた結果数調整
            if intent_analysis['is_company_specific']:
                max_results = 120  # 会社特化の場合は多めに取得
            elif intent_analysis['is_contact_inquiry']:
                max_results = 100
            else:
                max_results = 80
            
            # 超高精度検索実行
            search_results = await self.ultra_search.ultra_accurate_search(
                question, 
                company_id=company_id, 
                max_results=max_results
            )
            
            if not search_results:
                logger.warning("超高精度検索で結果が見つかりませんでした")
                return {
                    **question_data,
                    'search_results': [],
                    'search_success': False,
                    'step': 'search_completed'
                }
            
            # 結果の品質分析
            high_confidence_results = [r for r in search_results if r.confidence_score >= 0.3]
            medium_confidence_results = [r for r in search_results if 0.1 <= r.confidence_score < 0.3]
            
            logger.info(f"✅ 超高精度検索完了: {len(search_results)}件")
            logger.info(f"   高信頼度: {len(high_confidence_results)}件")
            logger.info(f"   中信頼度: {len(medium_confidence_results)}件")
            
            return {
                **question_data,
                'search_results': search_results,
                'high_confidence_count': len(high_confidence_results),
                'medium_confidence_count': len(medium_confidence_results),
                'search_success': True,
                'step': 'search_completed'
            }
        
        except Exception as e:
            logger.error(f"❌ 超高精度検索エラー: {e}")
            return {
                **question_data,
                'search_results': [],
                'search_success': False,
                'search_error': str(e),
                'step': 'search_failed'
            }
    
    def build_ultra_context(self, search_data: Dict) -> str:
        """
        📝 Step 3. 超高精度コンテキスト構築
        検索結果から最適なコンテキストを構築
        """
        logger.info(f"📝 Step 3: 超高精度コンテキスト構築開始")
        
        search_results = search_data.get('search_results', [])
        intent_analysis = search_data['intent_analysis']
        
        if not search_results:
            logger.warning("検索結果がないため、コンテキストを構築できません")
            return ""
        
        context_parts = []
        total_length = 0
        
        # 意図に基づいたコンテキスト構築戦略
        if intent_analysis['is_company_specific']:
            context_intro = f"以下は「{search_data['processed_question']}」に関する詳細情報です：\n\n"
        elif intent_analysis['is_contact_inquiry']:
            context_intro = "以下は連絡先・問い合わせに関する情報です：\n\n"
        else:
            context_intro = "以下は関連する情報です：\n\n"
        
        context_parts.append(context_intro)
        total_length += len(context_intro)
        
        # 結果を信頼度順でソート
        sorted_results = sorted(search_results, key=lambda x: x.confidence_score, reverse=True)
        
        for i, result in enumerate(sorted_results):
            if total_length >= self.max_context_length:
                break
            
            # コンテキストピースの構築
            context_piece = f"""
【参考資料{i+1}: {result.document_name}】
信頼度: {result.confidence_score:.3f} | 関連度: {result.relevance_score:.3f}

{result.content}

---
"""
            
            if total_length + len(context_piece) <= self.max_context_length:
                context_parts.append(context_piece)
                total_length += len(context_piece)
                logger.info(f"  {i+1}. 追加: {result.document_name} (セクション{result.chunk_index}) ({len(context_piece)}文字)")
            else:
                logger.info(f"  {i+1}. 文字数制限により除外")
                break
        
        final_context = "".join(context_parts)
        logger.info(f"✅ 超高精度コンテキスト構築完了: {len(context_parts)}個の参考資料、{len(final_context)}文字")
        
        return final_context
    
    def build_ultra_prompt(self, search_data: Dict, context: str) -> str:
        """
        🎯 Step 4. 超高精度プロンプト構築
        意図に基づいた最適化されたプロンプトを構築
        """
        logger.info(f"🎯 Step 4: 超高精度プロンプト構築開始")
        
        question = search_data['processed_question']
        intent_analysis = search_data['intent_analysis']
        
        # 基本プロンプト
        base_prompt = f"""あなたは社内の丁寧で親切なアシスタントです。

ご質問：
{question}

参考となる資料：
{context}

回答の際の重要な指針：
• 回答は丁寧な敬語で行ってください
• 情報の出典として「ファイル名」や「資料名」までは明示して構いませんが、列番号、行番号、チャンク番号、データベースのIDなどの内部的な構造情報は一切出力しないでください
• 代表者名や会社名など、ユーザーが聞いている情報だけを端的に答え、表形式やファイル構造の言及は不要です
• 情報が見つからない場合も、失礼のない自然な日本語で「現在の資料には該当情報がございません」と案内してください
• 文末には「ご不明な点がございましたら、お気軽にお申し付けください。」と添えてください

それでは、ご質問にお答えいたします："""
        
        # 意図に基づいたプロンプト調整
        if intent_analysis['is_company_specific']:
            specific_instruction = """
特に重要なポイント：
• 会社名やサービス名は正確にお伝えし、その特徴や強みも分かりやすくご説明します
• お客様が知りたいサービスの詳細について、具体的で実用的な情報をお伝えします
• ご連絡先やお問い合わせ方法についても、必要に応じてご案内いたします
"""
            base_prompt = base_prompt.replace("それでは、ご質問にお答えいたします：", specific_instruction + "\nそれでは、ご質問にお答えいたします：")
        
        elif intent_analysis['is_contact_inquiry']:
            contact_instruction = """
お問い合わせに関する特別なご案内：
• 電話番号、メールアドレス、住所など、必要な連絡先を分かりやすくお伝えします
• 営業時間や最適なお問い合わせ方法についても詳しくご案内します
• 複数の連絡手段がある場合は、お客様の状況に応じて最適な方法をご提案します
"""
            base_prompt = base_prompt.replace("それでは、ご質問にお答えいたします：", contact_instruction + "\nそれでは、ご質問にお答えいたします：")
        
        logger.info(f"✅ 超高精度プロンプト構築完了: {len(base_prompt)}文字")
        return base_prompt
    
    async def step5_generate_ultra_response(self, search_data: Dict, context: str, prompt: str) -> Dict:
        """
        🤖 Step 5. 超高精度回答生成
        最適化されたプロンプトで高品質な回答を生成
        """
        logger.info(f"🤖 Step 5: 超高精度回答生成開始")
        
        try:
            # Gemini APIで回答生成
            response = await asyncio.to_thread(
                self.chat_client.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # より一貫した回答のため低めに設定
                    top_p=0.8,
                    top_k=50,
                    max_output_tokens=16384,  # 16Kトークンに増加
                )
            )
            
            if response and response.text:
                generated_answer = response.text.strip()
                
                # 回答品質の評価
                quality_score = self._evaluate_answer_quality(
                    generated_answer, 
                    search_data['processed_question'],
                    search_data.get('search_results', [])
                )
                
                logger.info(f"✅ 超高精度回答生成完了: {len(generated_answer)}文字 (品質スコア: {quality_score:.3f})")
                
                return {
                    **search_data,
                    'context': context,
                    'prompt': prompt,
                    'generated_answer': generated_answer,
                    'quality_score': quality_score,
                    'generation_success': True,
                    'step': 'response_generated'
                }
            else:
                logger.error("❌ 回答生成に失敗: 空の応答")
                return {
                    **search_data,
                    'context': context,
                    'prompt': prompt,
                    'generated_answer': "恐れ入ります。今回のご質問には正確にお答えすることができませんでした。内容を少し変えて、もう一度お試しいただけますと幸いです。",
                    'quality_score': 0.0,
                    'generation_success': False,
                    'step': 'response_failed'
                }
        
        except Exception as e:
            logger.error(f"❌ 回答生成エラー: {e}")
            return {
                **search_data,
                'context': context,
                'prompt': prompt,
                'generated_answer': "申し訳ございませんが、技術的な問題により回答を生成できませんでした。",
                'quality_score': 0.0,
                'generation_success': False,
                'generation_error': str(e),
                'step': 'response_failed'
            }
    
    def _evaluate_answer_quality(self, answer: str, question: str, search_results: List) -> float:
        """回答品質の評価"""
        if not answer or not question:
            return 0.0
        
        quality_score = 0.0
        
        # 1. 長さによる評価
        if 100 <= len(answer) <= 2000:
            quality_score += 0.3
        elif 50 <= len(answer) <= 3000:
            quality_score += 0.2
        
        # 2. 質問キーワードの含有
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        keyword_overlap = len(question_words & answer_words) / len(question_words) if question_words else 0
        quality_score += keyword_overlap * 0.3
        
        # 3. 検索結果との関連性
        if search_results:
            high_confidence_count = sum(1 for r in search_results if r.confidence_score >= 0.3)
            if high_confidence_count > 0:
                quality_score += 0.2
        
        # 4. 構造的要素の存在
        if any(pattern in answer for pattern in ['電話', 'メール', '連絡先', '問い合わせ']):
            quality_score += 0.1
        
        # 5. 丁寧語の使用
        if any(pattern in answer for pattern in ['です', 'ます', 'ございます']):
            quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    async def process_ultra_accurate_rag(self, question: str, company_id: str = None, include_chunk_visibility: bool = False) -> Dict:
        """
        🎯 超高精度RAG処理のメインフロー
        全ステップを統合した最高精度の処理
        """
        # ChatMessageオブジェクトから文字列を取得
        if hasattr(question, 'text'):
            question_text = question.text
        else:
            question_text = str(question)
        
        logger.info(f"🎯 超高精度RAG処理開始: '{question_text[:50]}...'")
        
        try:
            # Step 1: 質問受付
            question_data = await self.step1_receive_question(question, company_id)
            
            # Step 2: 超高精度検索
            search_data = await self.step2_ultra_accurate_search(question_data)
            
            if not search_data['search_success']:
                return {
                    **search_data,
                    'final_answer': "申し訳ございませんが、お問い合わせいただいた内容に関する情報が見つかりませんでした。別の表現で質問していただくか、直接お問い合わせください。",
                    'processing_success': False,
                    'chunk_visibility': None
                }
            
            # Step 3: コンテキスト構築
            context = self.build_ultra_context(search_data)
            
            if not context:
                return {
                    **search_data,
                    'final_answer': "関連する情報が見つかりませんでした。",
                    'processing_success': False,
                    'chunk_visibility': None
                }
            
            # Step 4: プロンプト構築
            prompt = f"""あなたは{company_name}の社内向け丁寧で親切なアシスタントです。

回答の際の重要な指針：
• 回答は丁寧な敬語で行ってください。
• **手元の参考資料に関連する情報が含まれている場合は、それを活用して回答してください。**
• **参考資料の情報から推測できることや、関連する内容があれば積極的に提供してください。**
• **完全に一致する情報がなくても、部分的に関連する情報があれば有効活用してください。**
• 情報の出典として「ファイル名」や「資料名」までは明示して構いませんが、技術的な内部管理情報（列番号、行番号、分割番号、データベースのIDなど）は一切出力しないでください
• 代表者名や会社名など、ユーザーが聞いている情報だけを端的に答え、表形式やファイル構造の言及は不要です。
• **全く関連性がない場合のみ、その旨を丁寧に説明してください。**
• 専門的な内容も、日常の言葉で分かりやすく説明してください。
• 手続きや連絡先については、正確な情報を漏れなくご案内してください。
• 文末には「ご不明な点がございましたら、お気軽にお申し付けください。」と添えてください。

お客様からのご質問：
{question}

手元の参考資料：
{final_context}

それでは、ご質問にお答えいたします："""
            
            # Step 5: 回答生成
            final_result = await self.step5_generate_ultra_response(search_data, context, prompt)
            
            # チャンク可視化情報の生成
            chunk_visibility_info = None
            if include_chunk_visibility and search_data.get('search_results'):
                chunk_visibility_info = self._generate_chunk_visibility_info(
                    search_data['search_results'],
                    question,
                    search_data.get('intent_analysis', {})
                )
            
            # 最終結果の構築
            return {
                **final_result,
                'final_answer': final_result['generated_answer'],
                'processing_success': final_result['generation_success'],
                'processing_time': (datetime.now() - datetime.fromisoformat(question_data['timestamp'])).total_seconds(),
                'chunk_visibility': chunk_visibility_info
            }
        
        except Exception as e:
            logger.error(f"❌ 超高精度RAG処理エラー: {e}")
            import traceback
            logger.error(f"詳細エラー: {traceback.format_exc()}")
            
            return {
                'original_question': question,
                'final_answer': "申し訳ございませんが、システムエラーが発生しました。しばらく時間をおいて再度お試しください。",
                'processing_success': False,
                'processing_error': str(e),
                'chunk_visibility': None
            }
    
    def _generate_chunk_visibility_info(self, search_results: List, query: str, intent_analysis: Dict) -> Dict:
        """チャンク可視化情報の生成"""
        try:
            from .chunk_visibility import get_chunk_visibility_system
            
            # チャンク可視化システムを取得
            visibility_system = get_chunk_visibility_system()
            
            # 動的閾値を計算（検索システムから取得）
            similarities = [r.similarity_score for r in search_results]
            dynamic_threshold = self.ultra_search.calculate_dynamic_threshold(similarities, query)
            
            # チャンク選択分析
            selection_analysis = visibility_system.analyze_chunk_selection(
                search_results, query, dynamic_threshold, intent_analysis
            )
            
            # チャンク参照情報の作成
            chunk_references = visibility_system.create_chunk_references(search_results, query)
            
            # 可視化情報のフォーマット
            return visibility_system.format_chunk_visibility_info(chunk_references, selection_analysis)
        
        except Exception as e:
            logger.error(f"チャンク可視化情報生成エラー: {e}")
            return {
                "error": "チャンク可視化情報の生成に失敗しました",
                "chunk_references": [],
                "selection_analysis": {},
                "metadata": {}
            }

# インスタンス取得関数
def get_ultra_accurate_rag_instance() -> Optional[UltraAccurateRAGProcessor]:
    """超高精度RAGプロセッサのインスタンスを取得"""
    try:
        return UltraAccurateRAGProcessor()
    except Exception as e:
        logger.error(f"超高精度RAGプロセッサの初期化に失敗: {e}")
        return None

def ultra_accurate_rag_available() -> bool:
    """超高精度RAGが利用可能かチェック"""
    try:
        instance = get_ultra_accurate_rag_instance()
        return instance is not None
    except Exception:
        return False