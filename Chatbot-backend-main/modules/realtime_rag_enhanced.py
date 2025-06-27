"""
🚀 強化されたリアルタイムRAG処理フロー
質問受付〜RAG処理フロー（リアルタイム回答）の改良版実装

改善点:
- 強化されたベクトル検索システムの統合
- 適応的類似度閾値
- コンテキスト考慮型チャンク統合
- 改善されたプロンプト構築
- より精密な回答生成
"""

import os
import logging
import asyncio
import re
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

class EnhancedRealtimeRAGProcessor:
    """強化されたリアルタイムRAG処理システム"""
    
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
        
        # 強化されたベクトル検索システムの初期化
        try:
            from .vector_search_enhanced import get_enhanced_vector_search_instance, enhanced_vector_search_available
            if enhanced_vector_search_available():
                self.enhanced_search = get_enhanced_vector_search_instance()
                logger.info(f"✅ 強化ベクトル検索システム統合: {self.embedding_model} ({self.expected_dimensions}次元)")
            else:
                logger.error("❌ 強化ベクトル検索システムが利用できません")
                raise ValueError("強化ベクトル検索システムの初期化に失敗しました")
        except ImportError as e:
            logger.error(f"❌ 強化ベクトル検索システムのインポートエラー: {e}")
            raise ValueError("強化ベクトル検索システムが利用できません")
        
        # 回答品質パラメータ
        self.max_context_length = 120000  # コンテキスト長を増加
        self.min_chunk_relevance = 0.4    # 最小関連度閾値を上げる
        self.context_diversity_threshold = 0.7  # コンテキストの多様性閾値
        
        logger.info(f"✅ 強化リアルタイムRAGプロセッサ初期化完了")
    
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
    
    async def step1_receive_question(self, question: str, company_id: str = None) -> Dict:
        """
        ✏️ Step 1. 質問入力（強化版）
        質問の前処理と分析を実行
        """
        logger.info(f"✏️ Step 1: 強化質問受付 - '{question[:50]}...'")
        
        if not question or not question.strip():
            raise ValueError("質問が空です")
        
        # 質問の前処理と分析
        processed_question = question.strip()
        
        # 質問タイプの分析
        question_type = self._analyze_question_type(processed_question)
        
        # 重要キーワードの抽出
        key_terms = self._extract_key_terms(processed_question)
        
        return {
            "original_question": question,
            "processed_question": processed_question,
            "question_type": question_type,
            "key_terms": key_terms,
            "company_id": company_id,
            "timestamp": datetime.now().isoformat(),
            "step": 1
        }
    
    def _analyze_question_type(self, question: str) -> str:
        """質問タイプを分析"""
        question_lower = question.lower()
        
        # 手順・方法系
        if any(word in question_lower for word in ['方法', '手順', 'やり方', 'どうやって', 'どのように']):
            return 'procedure'
        
        # 情報検索系
        elif any(word in question_lower for word in ['とは', 'について', '詳細', '説明']):
            return 'information'
        
        # 問題解決系
        elif any(word in question_lower for word in ['問題', 'エラー', 'トラブル', '解決', '対処']):
            return 'troubleshooting'
        
        # 比較・選択系
        elif any(word in question_lower for word in ['違い', '比較', 'どちら', '選択', 'おすすめ']):
            return 'comparison'
        
        # 連絡先・場所系
        elif any(word in question_lower for word in ['連絡先', '電話', 'メール', '場所', 'どこ']):
            return 'contact'
        
        else:
            return 'general'
    
    def _extract_key_terms(self, question: str) -> List[str]:
        """重要キーワードを抽出"""
        # 基本的なキーワード抽出（改良版）
        # カタカナ、漢字、英数字の組み合わせを重要語として抽出
        patterns = [
            r'[ァ-ヶー]+',  # カタカナ
            r'[一-龯]+',    # 漢字
            r'[A-Za-z0-9]+', # 英数字
        ]
        
        key_terms = []
        for pattern in patterns:
            matches = re.findall(pattern, question)
            for match in matches:
                if len(match) >= 2:  # 2文字以上
                    key_terms.append(match)
        
        # 重複除去と頻度順ソート
        unique_terms = list(set(key_terms))
        
        # 長い語を優先
        unique_terms.sort(key=len, reverse=True)
        
        return unique_terms[:10]  # 上位10個
    
    async def step2_enhanced_search(self, question_data: Dict) -> List[Dict]:
        """
        🔍 Step 2. 強化ベクトル検索
        強化されたベクトル検索システムを使用して高品質な結果を取得
        """
        logger.info(f"🔍 Step 2: 強化ベクトル検索開始...")
        
        try:
            question = question_data["processed_question"]
            company_id = question_data.get("company_id")
            question_type = question_data.get("question_type", "general")
            
            # 質問タイプに応じた検索パラメータの調整
            max_results = self._get_search_params_by_type(question_type)
            
            # 強化ベクトル検索実行
            search_results = await self.enhanced_search.enhanced_vector_search(
                query=question,
                company_id=company_id,
                max_results=max_results
            )
            
            if not search_results:
                logger.warning("強化ベクトル検索で結果が見つかりませんでした")
                return []
            
            # 結果を辞書形式に変換
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    'chunk_id': result.chunk_id,
                    'document_id': result.document_id,
                    'document_name': result.document_name,
                    'content': result.content,
                    'similarity_score': result.similarity_score,
                    'relevance_score': result.relevance_score,
                    'chunk_index': result.chunk_index,
                    'document_type': result.document_type,
                    'search_method': result.search_method,
                    'quality_score': result.quality_score,
                    'context_bonus': result.context_bonus
                })
            
            logger.info(f"✅ Step 2完了: {len(formatted_results)}個の高品質チャンクを取得")
            
            # デバッグ: 上位3件の詳細を表示
            for i, result in enumerate(formatted_results[:3]):
                logger.info(f"  {i+1}. {result['document_name']} [チャンク{result['chunk_index']}]")
                logger.info(f"     関連度: {result['relevance_score']:.3f} (類似度: {result['similarity_score']:.3f})")
                logger.info(f"     品質: {result['quality_score']:.3f}, コンテキスト: {result['context_bonus']:.3f}")
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"❌ Step 2エラー: 強化ベクトル検索失敗 - {e}")
            raise
    
    def _get_search_params_by_type(self, question_type: str) -> int:
        """質問タイプに応じた検索パラメータを取得"""
        type_params = {
            'procedure': 20,      # 手順系は多めの情報が必要
            'information': 15,    # 情報系は標準
            'troubleshooting': 18, # 問題解決系は多めの情報
            'comparison': 12,     # 比較系は少なめで精度重視
            'contact': 8,         # 連絡先系は少なめで十分
            'general': 15         # 一般的な質問
        }
        
        return type_params.get(question_type, 15)
    
    async def step3_context_optimization(self, search_results: List[Dict], question_data: Dict) -> str:
        """
        🧠 Step 3. コンテキスト最適化
        検索結果を最適化してコンテキストを構築
        """
        logger.info(f"🧠 Step 3: コンテキスト最適化開始...")
        
        if not search_results:
            logger.warning("検索結果が空のため、コンテキスト構築をスキップ")
            return ""
        
        try:
            question = question_data["processed_question"]
            question_type = question_data.get("question_type", "general")
            key_terms = question_data.get("key_terms", [])
            
            # 関連度閾値による初期フィルタリング
            filtered_results = [
                result for result in search_results 
                if result['relevance_score'] >= self.min_chunk_relevance
            ]
            
            if not filtered_results:
                logger.warning("関連度閾値フィルタリング後に結果が空になりました")
                filtered_results = search_results[:5]  # 最低限の結果を確保
            
            # コンテキストの多様性を確保
            diverse_results = self._ensure_context_diversity(filtered_results)
            
            # 質問タイプに応じたコンテキスト構築
            optimized_context = self._build_optimized_context(
                diverse_results, question, question_type, key_terms
            )
            
            logger.info(f"✅ Step 3完了: {len(optimized_context)}文字の最適化コンテキストを構築")
            return optimized_context
        
        except Exception as e:
            logger.error(f"❌ Step 3エラー: コンテキスト最適化失敗 - {e}")
            # フォールバック: 基本的なコンテキスト構築
            return self._build_basic_context(search_results[:10])
    
    def _ensure_context_diversity(self, results: List[Dict]) -> List[Dict]:
        """コンテキストの多様性を確保"""
        diverse_results = []
        seen_documents = set()
        document_count = {}
        
        # 文書ごとの制限を設けて多様性を確保
        max_per_document = 3
        
        for result in results:
            doc_id = result['document_id']
            
            # 同一文書からの結果数をカウント
            current_count = document_count.get(doc_id, 0)
            
            if current_count < max_per_document:
                diverse_results.append(result)
                document_count[doc_id] = current_count + 1
                seen_documents.add(doc_id)
        
        logger.info(f"📊 多様性確保: {len(seen_documents)}個の文書から{len(diverse_results)}個のチャンクを選択")
        return diverse_results
    
    def _build_optimized_context(self, results: List[Dict], question: str, question_type: str, key_terms: List[str]) -> str:
        """最適化されたコンテキストを構築"""
        context_parts = []
        total_length = 0
        
        # 質問タイプに応じたコンテキスト構造
        if question_type == 'procedure':
            context_parts.append("【手順・方法に関する情報】")
        elif question_type == 'troubleshooting':
            context_parts.append("【問題解決に関する情報】")
        elif question_type == 'contact':
            context_parts.append("【連絡先・問い合わせ情報】")
        else:
            context_parts.append("【関連情報】")
        
        for i, result in enumerate(results):
            if total_length >= self.max_context_length:
                break
            
            # チャンク情報の構築
            relevance = result['relevance_score']
            quality = result['quality_score']
            
            chunk_header = f"\n=== 参考資料{i+1}: {result['document_name']} - チャンク{result['chunk_index']} ===\n"
            chunk_header += f"関連度: {relevance:.3f}, 品質: {quality:.3f}\n"
            
            # キーワードハイライト（ログ用）
            content = result['content']
            highlighted_terms = []
            for term in key_terms[:5]:  # 上位5個のキーワード
                if term in content:
                    highlighted_terms.append(term)
            
            if highlighted_terms:
                chunk_header += f"含有キーワード: {', '.join(highlighted_terms)}\n"
            
            chunk_content = chunk_header + content + "\n"
            
            if total_length + len(chunk_content) <= self.max_context_length:
                context_parts.append(chunk_content)
                total_length += len(chunk_content)
            else:
                # 残り容量に合わせて切り詰め
                remaining_space = self.max_context_length - total_length
                if remaining_space > 200:  # 最低限の情報が入る場合のみ
                    truncated_content = chunk_header + content[:remaining_space-len(chunk_header)-50] + "...\n"
                    context_parts.append(truncated_content)
                break
        
        return "\n".join(context_parts)
    
    def _build_basic_context(self, results: List[Dict]) -> str:
        """基本的なコンテキスト構築（フォールバック）"""
        context_parts = []
        total_length = 0
        
        for i, result in enumerate(results):
            if total_length >= self.max_context_length:
                break
            
            chunk_content = f"\n=== 参考資料{i+1}: {result['document_name']} ===\n{result['content']}\n"
            
            if total_length + len(chunk_content) <= self.max_context_length:
                context_parts.append(chunk_content)
                total_length += len(chunk_content)
            else:
                break
        
        return "\n".join(context_parts)
    
    async def step4_enhanced_answer_generation(self, question_data: Dict, context: str, company_name: str = "お客様の会社") -> str:
        """
        💡 Step 4. 強化回答生成
        最適化されたプロンプトとコンテキストを使用して高品質な回答を生成
        """
        logger.info(f"💡 Step 4: 強化回答生成開始...")
        
        if not context or len(context.strip()) == 0:
            logger.warning("コンテキストが空のため、一般的な回答を生成")
            return "申し訳ございませんが、ご質問に関連する情報が見つかりませんでした。より具体的な質問をしていただけますでしょうか。"
        
        try:
            question = question_data["processed_question"]
            question_type = question_data.get("question_type", "general")
            key_terms = question_data.get("key_terms", [])
            
            # 質問タイプに応じたプロンプト構築
            enhanced_prompt = self._build_enhanced_prompt(
                question, context, question_type, key_terms, company_name
            )
            
            # Gemini Flash 2.5で回答生成
            response = self.chat_client.generate_content(
                enhanced_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,  # 一貫性重視
                    max_output_tokens=3072,  # 出力トークン数を増加
                    top_p=0.8,
                    top_k=40
                )
            )
            
            if response and response.candidates:
                try:
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
                    # 回答の品質チェック
                    quality_score = self._evaluate_answer_quality(answer, question, key_terms)
                    logger.info(f"✅ Step 4完了: {len(answer)}文字の回答を生成 (品質スコア: {quality_score:.3f})")
                    
                    # 品質が低い場合は改善を試行
                    if quality_score < 0.5:
                        logger.warning("回答品質が低いため、改善を試行")
                        improved_answer = await self._improve_answer_quality(answer, question, context, company_name)
                        if improved_answer and len(improved_answer) > len(answer):
                            return improved_answer
                    
                    return answer
                else:
                    logger.error("LLMからの回答が空です")
                    return "申し訳ございませんが、回答の生成に失敗しました。もう一度お試しください。"
            else:
                logger.error("LLMからの回答が空です")
                return "申し訳ございませんが、回答の生成に失敗しました。もう一度お試しください。"
        
        except Exception as e:
            logger.error(f"❌ Step 4エラー: 強化回答生成失敗 - {e}")
            return "申し訳ございませんが、システムエラーが発生しました。しばらく時間をおいてから再度お試しください。"
    
    def _build_enhanced_prompt(self, question: str, context: str, question_type: str, key_terms: List[str], company_name: str) -> str:
        """強化されたプロンプトを構築"""
        
        # 質問タイプに応じた指示
        type_instructions = {
            'procedure': """
特に以下の点に注意して回答してください：
- 手順は番号付きで明確に示してください
- 各ステップで必要な情報や注意点を含めてください
- 前提条件や必要な準備があれば最初に説明してください
""",
            'troubleshooting': """
特に以下の点に注意して回答してください：
- 問題の原因と解決方法を明確に分けて説明してください
- 複数の解決方法がある場合は、優先順位をつけて提示してください
- 解決できない場合の連絡先や次のステップを示してください
""",
            'contact': """
特に以下の点に注意して回答してください：
- 連絡先情報は正確に記載してください
- 営業時間や対応可能な時間帯があれば明記してください
- 緊急時の連絡方法があれば別途示してください
""",
            'comparison': """
特に以下の点に注意して回答してください：
- 比較項目を明確にして表形式や箇条書きで整理してください
- それぞれの特徴やメリット・デメリットを説明してください
- 選択の判断基準や推奨事項があれば示してください
""",
            'general': """
特に以下の点に注意して回答してください：
- 情報を論理的に整理して説明してください
- 重要なポイントは強調して示してください
- 関連する追加情報があれば適切に含めてください
"""
        }
        
        specific_instruction = type_instructions.get(question_type, type_instructions['general'])
        
        # キーワード情報
        keyword_info = ""
        if key_terms:
            keyword_info = f"\n【重要キーワード】\n以下のキーワードに特に注意して回答してください: {', '.join(key_terms[:5])}\n"
        
        prompt = f"""あなたは{company_name}のAIアシスタントです。以下の参考資料を基に、ユーザーの質問に正確で親切に回答してください。

【重要な指示】
1. 参考資料の内容を要約せず、原文の表現をそのまま活用してください
2. 参考資料に記載されている具体的な手順、連絡先、条件等は正確に伝えてください
3. 参考資料にない情報は推測せず、「資料に記載がありません」と明記してください
4. 回答は丁寧で分かりやすい日本語で行ってください
5. 情報が複数ある場合は、関連度の高い順に整理して提示してください

{specific_instruction}
{keyword_info}
【参考資料】
{context}

【ユーザーの質問】
{question}

【回答】"""

        return prompt
    
    def _evaluate_answer_quality(self, answer: str, question: str, key_terms: List[str]) -> float:
        """回答の品質を評価"""
        if not answer or len(answer.strip()) < 20:
            return 0.0
        
        quality_score = 0.0
        answer_lower = answer.lower()
        question_lower = question.lower()
        
        # 1. 長さによる評価
        answer_length = len(answer)
        if 100 <= answer_length <= 2000:
            quality_score += 0.3
        elif 50 <= answer_length <= 3000:
            quality_score += 0.2
        
        # 2. キーワード含有率
        if key_terms:
            keyword_count = sum(1 for term in key_terms if term.lower() in answer_lower)
            keyword_ratio = keyword_count / len(key_terms)
            quality_score += keyword_ratio * 0.3
        
        # 3. 構造的要素の存在
        structural_elements = [
            r'\d+\.',  # 番号付きリスト
            r'・',     # 箇条書き
            r'【.*?】', # セクション見出し
            r'■.*?■', # 強調見出し
        ]
        
        for pattern in structural_elements:
            if re.search(pattern, answer):
                quality_score += 0.05
        
        # 4. 否定的な回答の検出（品質低下要因）
        negative_patterns = [
            '申し訳ございませんが',
            '情報が見つかりません',
            '記載がありません',
            'エラーが発生しました'
        ]
        
        negative_count = sum(1 for pattern in negative_patterns if pattern in answer)
        if negative_count > 0:
            quality_score -= 0.2 * negative_count
        
        return max(0.0, min(1.0, quality_score))
    
    async def _improve_answer_quality(self, original_answer: str, question: str, context: str, company_name: str) -> str:
        """回答品質の改善を試行"""
        try:
            improvement_prompt = f"""以下の回答を改善してください。より具体的で有用な情報を含む回答にしてください。

【元の質問】
{question}

【現在の回答】
{original_answer}

【参考資料】
{context}

【改善指示】
1. より具体的な情報を含めてください
2. 手順がある場合は明確に番号付けしてください
3. 重要な情報は強調してください
4. 不足している情報があれば補完してください

【改善された回答】"""
            
            response = self.chat_client.generate_content(
                improvement_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=3072,
                    top_p=0.9,
                    top_k=50
                )
            )
            
            if response and response.text:
                improved_answer = response.text.strip()
                if len(improved_answer) > len(original_answer) * 0.8:  # 改善された回答が十分な長さの場合
                    logger.info("✅ 回答品質改善成功")
                    return improved_answer
        
        except Exception as e:
            logger.error(f"回答品質改善エラー: {e}")
        
        return original_answer
    
    async def step5_response_finalization(self, answer: str, metadata: Dict = None) -> Dict:
        """
        ⚡️ Step 5. 回答最終化
        最終的な回答とメタデータを返す
        """
        logger.info(f"⚡️ Step 5: 回答最終化準備完了")
        
        result = {
            "answer": answer,
            "timestamp": datetime.now().isoformat(),
            "step": 5,
            "status": "completed",
            "system_version": "enhanced_realtime_rag_v2"
        }
        
        if metadata:
            result.update(metadata)
        
        logger.info(f"✅ 強化リアルタイムRAG処理完了: {len(answer)}文字の高品質回答")
        return result
    
    async def process_enhanced_realtime_rag(self, question: str, company_id: str = None, company_name: str = "お客様の会社", top_k: int = 15) -> Dict:
        """
        🚀 強化リアルタイムRAG処理フロー全体の実行
        Step 1〜5を順次実行して高品質なリアルタイム回答を生成
        """
        logger.info(f"🚀 強化リアルタイムRAG処理開始: '{question[:50]}...'")
        
        try:
            # Step 1: 質問入力と分析
            step1_result = await self.step1_receive_question(question, company_id)
            
            # Step 2: 強化ベクトル検索
            search_results = await self.step2_enhanced_search(step1_result)
            
            # Step 3: コンテキスト最適化
            optimized_context = await self.step3_context_optimization(search_results, step1_result)
            
            # Step 4: 強化回答生成
            answer = await self.step4_enhanced_answer_generation(step1_result, optimized_context, company_name)
            
            # Step 5: 回答最終化
            metadata = {
                "original_question": question,
                "processed_question": step1_result["processed_question"],
                "question_type": step1_result.get("question_type", "general"),
                "key_terms": step1_result.get("key_terms", []),
                "chunks_used": len(search_results),
                "top_relevance": search_results[0]["relevance_score"] if search_results else 0.0,
                "context_length": len(optimized_context),
                "company_id": company_id,
                "company_name": company_name
            }
            
            result = await self.step5_response_finalization(answer, metadata)
            
            logger.info(f"🎉 強化リアルタイムRAG処理成功完了")
            return result
            
        except Exception as e:
            logger.error(f"❌ 強化リアルタイムRAG処理エラー: {e}")
            error_result = {
                "answer": "申し訳ございませんが、システムエラーが発生しました。しばらく時間をおいてから再度お試しください。",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "system_version": "enhanced_realtime_rag_v2"
            }
            return error_result

# グローバルインスタンス
_enhanced_realtime_rag_processor = None

def get_enhanced_realtime_rag_processor() -> Optional[EnhancedRealtimeRAGProcessor]:
    """強化リアルタイムRAGプロセッサのインスタンスを取得（シングルトンパターン）"""
    global _enhanced_realtime_rag_processor
    
    if _enhanced_realtime_rag_processor is None:
        try:
            _enhanced_realtime_rag_processor = EnhancedRealtimeRAGProcessor()
            logger.info("✅ 強化リアルタイムRAGプロセッサ初期化完了")
        except Exception as e:
            logger.error(f"❌ 強化リアルタイムRAGプロセッサ初期化エラー: {e}")
            return None
    
    return _enhanced_realtime_rag_processor

async def process_question_enhanced_realtime(question: str, company_id: str = None, company_name: str = "お客様の会社", top_k: int = 15) -> Dict:
    """
    強化リアルタイムRAG処理の外部呼び出し用関数
    
    Args:
        question: ユーザーの質問
        company_id: 会社ID（オプション）
        company_name: 会社名（回答生成用）
        top_k: 取得する類似チャンク数
    
    Returns:
        Dict: 処理結果（回答、メタデータ等）
    """
    processor = get_enhanced_realtime_rag_processor()
    if not processor:
        return {
            "answer": "システムの初期化に失敗しました。管理者にお問い合わせください。",
            "error": "EnhancedRealtimeRAGProcessor initialization failed",
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "system_version": "enhanced_realtime_rag_v2"
        }
    
    return await processor.process_enhanced_realtime_rag(question, company_id, company_name, top_k)

def enhanced_realtime_rag_available() -> bool:
    """強化リアルタイムRAGが利用可能かチェック"""
    try:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        use_vertex_ai = os.getenv("USE_VERTEX_AI", "true").lower() == "true"
        
        return bool(api_key and supabase_url and supabase_key and use_vertex_ai)
    except Exception:
        return False