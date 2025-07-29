"""
🚀 拡張リアルタイムRAG処理フロー - 長い質問の段階的処理システム
質問を適切に分割し、段階的に処理したうえで、最終的に統合した形で回答を提供

実装ステップ:
✏️ Step 1: 質問文を構文的にパースして、サブタスクに分割
🧠 Step 2: それぞれを個別にEmbedding & Retrieval (分割されたサブ質問ごとに、embedding検索（RAG）)
💡 Step 3: それぞれの結果をLLMで回答生成 (各分割タスクから、サブ回答を作成)
🏁 Step 4: LLMで最終統合（chain-of-thought）(各サブ回答を論理的に結合し、表形式など、構造を再整形して1つの出力にする)
"""

import os
import logging
import asyncio
import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import google.generativeai as genai
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

# 既存のモジュールをインポート
from .realtime_rag import RealtimeRAGProcessor, get_realtime_rag_processor

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class SubTask:
    """サブタスクの定義"""
    id: str
    question: str
    priority: int
    category: str
    keywords: List[str]
    expected_answer_type: str

@dataclass
class SubTaskResult:
    """サブタスクの処理結果"""
    subtask: SubTask
    chunks: List[Dict]
    answer: str
    confidence: float
    processing_time: float

@dataclass
class QuestionAnalysis:
    """質問分析結果"""
    original_question: str
    is_complex: bool
    complexity_score: float
    subtasks: List[SubTask]
    reasoning: str
    processing_strategy: str

class EnhancedRealtimeRAGProcessor:
    """拡張リアルタイムRAG処理システム - 長い質問の段階的処理対応"""
    
    def __init__(self):
        """初期化"""
        # 基本のRAGプロセッサを取得
        self.base_processor = get_realtime_rag_processor()
        if not self.base_processor:
            raise ValueError("基本RAGプロセッサの初期化に失敗しました")
        
        # Gemini APIクライアントの設定
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY または GEMINI_API_KEY 環境変数が設定されていません")
        
        genai.configure(api_key=self.api_key)
        self.analysis_model = genai.GenerativeModel("gemini-2.5-flash")
        self.integration_model = genai.GenerativeModel("gemini-2.5-flash")
        
        # 複雑さ判定の閾値
        self.complexity_threshold = 0.6
        self.min_subtasks = 2
        self.max_subtasks = 5
        
        logger.info("✅ 拡張リアルタイムRAGプロセッサ初期化完了")
    
    async def step1_parse_and_divide_question(self, question: str) -> QuestionAnalysis:
        """
        ✏️ Step 1: 質問文を構文的にパースして、サブタスクに分割
        
        Args:
            question: 元の質問文
            
        Returns:
            QuestionAnalysis: 質問分析結果とサブタスク
        """
        # ChatMessageオブジェクトから文字列を取得
        if hasattr(question, 'text'):
            question_text = question.text
        else:
            question_text = str(question)
        
        logger.info(f"✏️ Step 1: 質問分析・分割開始 - '{question_text[:100]}...'")
        
        try:
            # Gemini 2.5 Flashで質問を分析
            analysis_prompt = f"""
以下の質問を分析し、複雑な質問かどうかを判定してください。
複雑な質問の場合は、適切なサブタスクに分割してください。

質問: 「{question}」

分析項目:
1. 複雑さ判定 (is_complex): true/false
2. 複雑さスコア (complexity_score): 0.0-1.0の数値
3. 処理戦略 (processing_strategy): "simple" または "multi_step"
4. サブタスク分割 (subtasks): 複雑な場合のみ、以下の形式で2-5個のサブタスクに分割

【複雑な質問の判定基準】
- 複数の異なる情報を求めている
- 比較や分析が必要
- 手順や段階的な説明が必要
- 複数の条件や制約がある
- 文章が長く、複数の要素を含む

【サブタスク分割の指針】
- 各サブタスクは独立して回答可能にする
- 優先度を設定（1が最高優先度）
- カテゴリを分類（info_request, comparison, procedure, analysis等）
- 期待される回答タイプを指定（factual, explanatory, procedural等）

JSON形式で回答してください：

{{
  "is_complex": boolean,
  "complexity_score": number,
  "processing_strategy": "simple" | "multi_step",
  "reasoning": "判定理由",
  "subtasks": [
    {{
      "id": "subtask_1",
      "question": "具体的なサブ質問",
      "priority": 1,
      "category": "info_request",
      "keywords": ["キーワード1", "キーワード2"],
      "expected_answer_type": "factual"
    }}
  ]
}}

例1（シンプルな質問）:
{{
  "is_complex": false,
  "complexity_score": 0.3,
  "processing_strategy": "simple",
  "reasoning": "単一の情報を求める簡単な質問",
  "subtasks": []
}}

例2（複雑な質問）:
{{
  "is_complex": true,
  "complexity_score": 0.8,
  "processing_strategy": "multi_step",
  "reasoning": "複数の異なる情報と比較分析が必要な複雑な質問",
  "subtasks": [
    {{
      "id": "subtask_1",
      "question": "A社の基本情報は何ですか？",
      "priority": 1,
      "category": "info_request",
      "keywords": ["A社", "基本情報", "会社概要"],
      "expected_answer_type": "factual"
    }},
    {{
      "id": "subtask_2", 
      "question": "B社の基本情報は何ですか？",
      "priority": 1,
      "category": "info_request",
      "keywords": ["B社", "基本情報", "会社概要"],
      "expected_answer_type": "factual"
    }},
    {{
      "id": "subtask_3",
      "question": "A社とB社の違いや特徴を比較してください",
      "priority": 2,
      "category": "comparison",
      "keywords": ["A社", "B社", "比較", "違い", "特徴"],
      "expected_answer_type": "explanatory"
    }}
  ]
}}
"""
            
            # Gemini 2.5 Flashで分析実行
            response = self.analysis_model.generate_content(
                analysis_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,  # 一貫性重視
                    max_output_tokens=8192,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            if not response or not response.candidates:
                logger.warning("⚠️ Geminiからの分析応答が空です")
                return self._create_fallback_analysis(question)
            
            # レスポンスからJSONを抽出
            response_text = ""
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text'):
                    response_text += part.text
            
            # JSONの解析
            try:
                analysis_data = json.loads(response_text.strip())
            except json.JSONDecodeError:
                # Markdownコードブロック内のJSONを抽出
                json_match = re.search(r'```json\n(.*?)```', response_text, re.DOTALL)
                if json_match:
                    analysis_data = json.loads(json_match.group(1).strip())
                else:
                    logger.warning("⚠️ JSON解析に失敗、フォールバック分析を実行")
                    return self._create_fallback_analysis(question)
            
            # QuestionAnalysisオブジェクトの構築
            is_complex = analysis_data.get("is_complex", False)
            complexity_score = float(analysis_data.get("complexity_score", 0.5))
            processing_strategy = analysis_data.get("processing_strategy", "simple")
            reasoning = analysis_data.get("reasoning", "Gemini分析結果")
            
            subtasks = []
            if is_complex and analysis_data.get("subtasks"):
                for i, subtask_data in enumerate(analysis_data["subtasks"]):
                    subtask = SubTask(
                        id=subtask_data.get("id", f"subtask_{i+1}"),
                        question=subtask_data.get("question", ""),
                        priority=int(subtask_data.get("priority", 1)),
                        category=subtask_data.get("category", "info_request"),
                        keywords=subtask_data.get("keywords", []),
                        expected_answer_type=subtask_data.get("expected_answer_type", "factual")
                    )
                    subtasks.append(subtask)
            
            analysis = QuestionAnalysis(
                original_question=question,
                is_complex=is_complex,
                complexity_score=complexity_score,
                subtasks=subtasks,
                reasoning=reasoning,
                processing_strategy=processing_strategy
            )
            
            logger.info(f"✅ Step 1完了: 複雑度={complexity_score:.2f}, サブタスク数={len(subtasks)}")
            logger.info(f"🎯 処理戦略: {processing_strategy}")
            logger.info(f"💭 判定理由: {reasoning}")
            
            if subtasks:
                logger.info("📋 サブタスク一覧:")
                for subtask in subtasks:
                    logger.info(f"  - {subtask.id}: {subtask.question} (優先度: {subtask.priority})")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Step 1エラー: 質問分析失敗 - {e}")
            return self._create_fallback_analysis(question)
    
    def _create_fallback_analysis(self, question: str) -> QuestionAnalysis:
        """フォールバック分析（Geminiが利用できない場合）"""
        logger.info("🔄 フォールバック分析実行中...")
        
        # 簡単なルールベース分析
        question_length = len(question)
        question_lower = question.lower()
        
        # 複雑さの判定
        complexity_indicators = [
            ('と' in question and '違い' in question),  # 比較
            ('手順' in question or 'やり方' in question),  # 手順
            ('なぜ' in question and 'どう' in question),  # 複合質問
            question_length > 100,  # 長い質問
            question.count('？') > 1 or question.count('?') > 1,  # 複数の疑問符
            ('まず' in question or '次に' in question),  # 段階的
        ]
        
        complexity_score = sum(complexity_indicators) / len(complexity_indicators)
        is_complex = complexity_score >= 0.4
        
        if is_complex:
            # 簡単なサブタスク分割
            subtasks = self._create_simple_subtasks(question)
            processing_strategy = "multi_step"
        else:
            subtasks = []
            processing_strategy = "simple"
        
        return QuestionAnalysis(
            original_question=question,
            is_complex=is_complex,
            complexity_score=complexity_score,
            subtasks=subtasks,
            reasoning="フォールバック分析による判定（ルールベース）",
            processing_strategy=processing_strategy
        )
    
    def _create_simple_subtasks(self, question: str) -> List[SubTask]:
        """簡単なルールベースサブタスク分割"""
        subtasks = []
        
        # 比較質問の場合
        if 'と' in question and ('違い' in question or '比較' in question):
            # A と B の違い -> A について、B について、比較
            parts = question.split('と')
            if len(parts) >= 2:
                entity_a = parts[0].strip()
                entity_b = parts[1].split('の')[0].strip()
                
                subtasks.append(SubTask(
                    id="subtask_1",
                    question=f"{entity_a}について教えてください",
                    priority=1,
                    category="info_request",
                    keywords=[entity_a],
                    expected_answer_type="factual"
                ))
                
                subtasks.append(SubTask(
                    id="subtask_2", 
                    question=f"{entity_b}について教えてください",
                    priority=1,
                    category="info_request",
                    keywords=[entity_b],
                    expected_answer_type="factual"
                ))
                
                subtasks.append(SubTask(
                    id="subtask_3",
                    question=f"{entity_a}と{entity_b}の違いを比較してください",
                    priority=2,
                    category="comparison",
                    keywords=[entity_a, entity_b, "違い", "比較"],
                    expected_answer_type="explanatory"
                ))
        
        # 手順質問の場合
        elif '手順' in question or 'やり方' in question:
            subtasks.append(SubTask(
                id="subtask_1",
                question=question,
                priority=1,
                category="procedure",
                keywords=["手順", "やり方", "方法"],
                expected_answer_type="procedural"
            ))
        
        return subtasks
    
    async def step2_individual_embedding_retrieval(self, subtasks: List[SubTask], company_id: str = None, top_k: int = 10) -> List[Tuple[SubTask, List[Dict]]]:
        """
        🧠 Step 2: それぞれを個別にEmbedding & Retrieval
        分割されたサブ質問ごとに、embedding検索（RAG）を実行
        
        Args:
            subtasks: サブタスクのリスト
            company_id: 会社ID
            top_k: 各サブタスクで取得するチャンク数
            
        Returns:
            List[Tuple[SubTask, List[Dict]]]: サブタスクと対応する検索結果のペア
        """
        logger.info(f"🧠 Step 2: 個別検索開始 - {len(subtasks)}個のサブタスク")
        
        results = []
        
        # 優先度順でソート
        sorted_subtasks = sorted(subtasks, key=lambda x: x.priority)
        
        for i, subtask in enumerate(sorted_subtasks):
            logger.info(f"🔍 サブタスク {i+1}/{len(subtasks)}: {subtask.question}")
            
            try:
                # エンベディング生成
                query_embedding = await self.base_processor.step2_generate_embedding(subtask.question)
                
                if query_embedding:
                    # 類似検索実行
                    similar_chunks = await self.base_processor.step3_similarity_search(
                        query_embedding, 
                        company_id, 
                        top_k
                    )
                    
                    logger.info(f"✅ サブタスク {subtask.id}: {len(similar_chunks)}個のチャンクを取得")
                    results.append((subtask, similar_chunks))
                else:
                    logger.warning(f"⚠️ サブタスク {subtask.id}: エンベディング生成失敗")
                    results.append((subtask, []))
                
                # API制限対策：少し待機
                if i < len(sorted_subtasks) - 1:
                    await asyncio.sleep(0.2)
                    
            except Exception as e:
                logger.error(f"❌ サブタスク {subtask.id} 検索エラー: {e}")
                results.append((subtask, []))
        
        logger.info(f"✅ Step 2完了: {len(results)}個のサブタスク検索完了")
        return results
    
    async def step3_generate_sub_answers(self, subtask_results: List[Tuple[SubTask, List[Dict]]], company_name: str = "お客様の会社", company_id: str = None) -> List[SubTaskResult]:
        """
        💡 Step 3: それぞれの結果をLLMで回答生成
        各分割タスクから、サブ回答を作成（サブ回答はまだバラバラの状態）
        
        Args:
            subtask_results: サブタスクと検索結果のペア
            company_name: 会社名
            company_id: 会社ID
            
        Returns:
            List[SubTaskResult]: サブタスクの処理結果
        """
        logger.info(f"💡 Step 3: サブ回答生成開始 - {len(subtask_results)}個のサブタスク")
        
        sub_results = []
        
        for i, (subtask, chunks) in enumerate(subtask_results):
            start_time = datetime.now()
            logger.info(f"🤖 サブ回答 {i+1}/{len(subtask_results)}: {subtask.question}")
            
            try:
                # 基本RAGプロセッサを使用してサブ回答を生成
                if chunks:
                    answer = await self.base_processor.step4_generate_answer(
                        subtask.question, 
                        chunks, 
                        company_name, 
                        company_id
                    )
                    confidence = self._calculate_confidence(subtask, chunks, answer)
                else:
                    answer = f"申し訳ございませんが、「{subtask.question}」に関する情報が見つかりませんでした。"
                    confidence = 0.1
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                sub_result = SubTaskResult(
                    subtask=subtask,
                    chunks=chunks,
                    answer=answer,
                    confidence=confidence,
                    processing_time=processing_time
                )
                
                sub_results.append(sub_result)
                
                logger.info(f"✅ サブ回答 {subtask.id}: 信頼度={confidence:.2f}, 処理時間={processing_time:.2f}秒")
                logger.info(f"📝 回答プレビュー: {answer[:100]}...")
                
            except Exception as e:
                logger.error(f"❌ サブ回答 {subtask.id} 生成エラー: {e}")
                
                # エラー時のフォールバック回答
                sub_result = SubTaskResult(
                    subtask=subtask,
                    chunks=chunks,
                    answer=f"申し訳ございませんが、「{subtask.question}」の処理中にエラーが発生しました。",
                    confidence=0.0,
                    processing_time=0.0
                )
                sub_results.append(sub_result)
        
        logger.info(f"✅ Step 3完了: {len(sub_results)}個のサブ回答生成完了")
        return sub_results
    
    def _calculate_confidence(self, subtask: SubTask, chunks: List[Dict], answer: str) -> float:
        """サブ回答の信頼度を計算"""
        confidence = 0.5  # ベース信頼度
        
        # チャンク数による調整
        if chunks:
            confidence += min(len(chunks) * 0.05, 0.3)  # 最大0.3の追加
        
        # 回答長による調整
        if len(answer) > 50:
            confidence += 0.1
        
        # キーワードマッチによる調整
        answer_lower = answer.lower()
        keyword_matches = sum(1 for keyword in subtask.keywords if keyword.lower() in answer_lower)
        if keyword_matches > 0:
            confidence += min(keyword_matches * 0.1, 0.2)
        
        return min(confidence, 1.0)
    
    async def step4_final_integration(self, analysis: QuestionAnalysis, sub_results: List[SubTaskResult]) -> str:
        """
        🏁 Step 4: LLMで最終統合（chain-of-thought）
        各サブ回答を論理的に結合し、表形式など、構造を再整形して1つの出力にする
        
        Args:
            analysis: 元の質問分析結果
            sub_results: サブタスクの処理結果
            
        Returns:
            str: 統合された最終回答
        """
        logger.info(f"🏁 Step 4: 最終統合開始 - {len(sub_results)}個のサブ回答を統合")
        
        try:
            # サブ回答を整理
            sub_answers_text = []
            for i, result in enumerate(sub_results, 1):
                sub_answers_text.append(f"""
【サブ質問{i}】: {result.subtask.question}
【カテゴリ】: {result.subtask.category}
【信頼度】: {result.confidence:.2f}
【回答】: {result.answer}
""")
            
            # 統合プロンプトの構築
            integration_prompt = f"""
あなたは情報統合の専門家です。以下の元の質問に対して、複数のサブ質問への回答を論理的に統合し、構造化された包括的な回答を作成してください。

【元の質問】
{analysis.original_question}

【質問分析】
- 複雑度: {analysis.complexity_score:.2f}
- 判定理由: {analysis.reasoning}

【サブ質問への回答】
{''.join(sub_answers_text)}

【統合指針】
1. **論理的な構造化**: サブ回答を論理的な順序で整理し、関連性を明確にする
2. **情報の重複排除**: 重複する情報は統合し、簡潔にまとめる
3. **包括性の確保**: 元の質問のすべての側面に対応する
4. **読みやすさ**: 見出し、箇条書き、表形式などを活用して構造化する
5. **信頼度の反映**: 信頼度の低い情報は適切に注記する

【回答形式の指針】
- 比較質問の場合: 表形式や対比形式で整理
- 手順質問の場合: ステップバイステップで番号付きリスト
- 複合質問の場合: セクション分けして体系的に回答
- 情報不足の場合: 明確に不足部分を示し、代替案を提示

【最終統合回答】
元の質問に対する包括的で構造化された回答を以下に示します：
"""
            
            # Gemini 2.5 Flashで統合実行
            response = self.integration_model.generate_content(
                integration_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,  # 創造性と一貫性のバランス
                    max_output_tokens=8192,
                    top_p=0.9,
                    top_k=50
                )
            )
            
            if response and response.candidates:
                integrated_answer = ""
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text'):
                        integrated_answer += part.text
                
                if integrated_answer.strip():
                    logger.info(f"✅ Step 4完了: {len(integrated_answer)}文字の統合回答を生成")
                    logger.info(f"📝 統合回答プレビュー: {integrated_answer[:200]}...")
                    return integrated_answer.strip()
            
            # フォールバック: サブ回答を単純に結合
            logger.warning("⚠️ 統合処理失敗、フォールバック統合を実行")
            return self._create_fallback_integration(analysis, sub_results)
            
        except Exception as e:
            logger.error(f"❌ Step 4エラー: 最終統合失敗 - {e}")
            return self._create_fallback_integration(analysis, sub_results)
    
    def _create_fallback_integration(self, analysis: QuestionAnalysis, sub_results: List[SubTaskResult]) -> str:
        """フォールバック統合（Geminiが利用できない場合）"""
        logger.info("🔄 フォールバック統合実行中...")
        
        integration_parts = []
        integration_parts.append(f"ご質問「{analysis.original_question}」について、以下のように回答いたします：\n")
        
        # サブ回答を順序立てて結合
        for i, result in enumerate(sub_results, 1):
            if result.confidence > 0.3:  # 信頼度の高い回答のみ含める
                integration_parts.append(f"\n## {i}. {result.subtask.question}\n")
                integration_parts.append(result.answer)
            else:
                integration_parts.append(f"\n## {i}. {result.subtask.question}\n")
                integration_parts.append("申し訳ございませんが、この点については十分な情報が見つかりませんでした。")
        
        integration_parts.append("\n\n以上が、ご質問に対する包括的な回答となります。")
        integration_parts.append("ご不明な点がございましたら、お気軽にお申し付けください。")
        
        return "".join(integration_parts)
    
    async def process_enhanced_realtime_rag(self, question: str, company_id: str = None, company_name: str = "お客様の会社", top_k: int = 15) -> Dict:
        """
        🚀 拡張リアルタイムRAG処理フロー全体の実行
        長い質問を段階的に処理し、統合された回答を生成
        
        Args:
            question: ユーザーの質問
            company_id: 会社ID
            company_name: 会社名
            top_k: 各サブタスクで取得するチャンク数
            
        Returns:
            Dict: 処理結果
        """
        # ChatMessageオブジェクトから文字列を取得
        if hasattr(question, 'text'):
            question_text = question.text
        else:
            question_text = str(question)
        
        logger.info(f"🚀 拡張リアルタイムRAG処理開始: '{question_text[:100]}...'")
        start_time = datetime.now()
        
        try:
            # Step 1: 質問分析・分割
            analysis = await self.step1_parse_and_divide_question(question)
            
            # 複雑でない質問は基本RAGプロセッサで処理
            if not analysis.is_complex or len(analysis.subtasks) == 0:
                logger.info("🔄 シンプルな質問のため基本RAGプロセッサで処理")
                return await self.base_processor.process_realtime_rag(question, company_id, company_name, top_k)
            
            # Step 2: 個別検索
            subtask_results = await self.step2_individual_embedding_retrieval(analysis.subtasks, company_id, top_k)
            
            # Step 3: サブ回答生成
            sub_results = await self.step3_generate_sub_answers(subtask_results, company_name, company_id)
            
            # Step 4: 最終統合
            final_answer = await self.step4_final_integration(analysis, sub_results)
            
            # 処理時間計算
            total_processing_time = (datetime.now() - start_time).total_seconds()
            
            # 使用されたチャンクを収集
            all_chunks = []
            for result in sub_results:
                all_chunks.extend(result.chunks)
            
            # メタデータの構築
            metadata = {
                "original_question": question,
                "processing_type": "enhanced_multi_step_rag",
                "question_analysis": {
                    "is_complex": analysis.is_complex,
                    "complexity_score": analysis.complexity_score,
                    "subtasks_count": len(analysis.subtasks),
                    "reasoning": analysis.reasoning,
                    "processing_strategy": analysis.processing_strategy
                },
                "subtask_results": [
                    {
                        "id": result.subtask.id,
                        "question": result.subtask.question,
                        "category": result.subtask.category,
                        "confidence": result.confidence,
                        "chunks_used": len(result.chunks),
                        "processing_time": result.processing_time
                    }
                    for result in sub_results
                ],
                "total_chunks_used": len(all_chunks),
                "total_processing_time": total_processing_time,
                "company_id": company_id,
                "company_name": company_name
            }
            
            # 最終結果の構築
            result = {
                "answer": final_answer,
                "sources": self._extract_source_documents(all_chunks[:10]),  # main.pyが期待するフィールド名
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "metadata": metadata,
                "source_documents": self._extract_source_documents(all_chunks[:10])  # 後方互換性のため残す
            }
            
            logger.info(f"🎉 拡張リアルタイムRAG処理成功完了: {total_processing_time:.2f}秒")
            return result
            
        except Exception as e:
            logger.error(f"❌拡張リアルタイムRAG処理エラー: {e}")
            import traceback
            logger.error(f"詳細エラー: {traceback.format_exc()}")
            
            error_result = {
                "answer": "申し訳ございませんが、システムエラーが発生しました。しばらく時間をおいてから再度お試しください。",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "processing_type": "enhanced_multi_step_rag_error"
            }
            return error_result
    
    def _extract_source_documents(self, chunks: List[Dict]) -> List[Dict]:
        """ソース文書情報を抽出 - main.pyが期待する形式で返す"""
        source_documents = []
        seen_docs = set()
        
        for chunk in chunks:
            # document_sources.nameを取得（複数のフィールド名を試行）
            doc_name = (
                chunk.get('document_name') or
                chunk.get('name') or
                chunk.get('filename') or
                'Unknown Document'
            )
            
            if doc_name and doc_name not in seen_docs and doc_name not in ['システム回答', 'unknown', 'Unknown']:
                doc_info = {
                    "name": doc_name,  # main.pyが期待するフィールド名
                    "filename": doc_name,  # 後方互換性
                    "document_name": doc_name,  # 後方互換性
                    "document_type": chunk.get('document_type', 'unknown'),
                    "similarity_score": chunk.get('similarity_score', 0.0)
                }
                source_documents.append(doc_info)
                seen_docs.add(doc_name)
        
        return source_documents


# グローバルインスタンス
_enhanced_realtime_rag_processor = None

def get_enhanced_realtime_rag_processor() -> Optional[EnhancedRealtimeRAGProcessor]:
    """拡張リアルタイムRAGプロセッサのインスタンスを取得（シングルトンパターン）"""
    global _enhanced_realtime_rag_processor
    
    if _enhanced_realtime_rag_processor is None:
        try:
            _enhanced_realtime_rag_processor = EnhancedRealtimeRAGProcessor()
            logger.info("✅ 拡張リアルタイムRAGプロセッサ初期化完了")
        except Exception as e:
            logger.error(f"❌ 拡張リアルタイムRAGプロセッサ初期化エラー: {e}")
            return None
    
    return _enhanced_realtime_rag_processor

async def process_question_enhanced_realtime(
    question: str,
    company_id: str = None,
    company_name: str = "お客様の会社",
    top_k: int = 15
) -> Dict:
    """
    拡張リアルタイムRAG処理の外部呼び出し用関数
    
    Args:
        question: ユーザーの質問
        company_id: 会社ID（オプション）
        company_name: 会社名（回答生成用）
        top_k: 各サブタスクで取得するチャンク数
    
    Returns:
        Dict: 処理結果（回答、メタデータ等）
    """
    processor = get_enhanced_realtime_rag_processor()
    if not processor:
        return {
            "answer": "システムの初期化に失敗しました。管理者にお問い合わせください。",
            "error": "EnhancedRealtimeRAGProcessor initialization failed",
            "timestamp": datetime.now().isoformat(),
            "status": "error"
        }
    
    return await processor.process_enhanced_realtime_rag(question, company_id, company_name, top_k)

def enhanced_realtime_rag_available() -> bool:
    """拡張リアルタイムRAGが利用可能かチェック"""
    try:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        return bool(api_key and supabase_url and supabase_key)
    except Exception:
        return False

# 使用例とテスト用の関数
async def test_enhanced_rag_with_sample_questions():
    """サンプル質問での拡張RAGテスト"""
    sample_questions = [
        "A社とB社の違いは何ですか？それぞれの特徴と料金体系を比較して教えてください。",
        "新しいシステムを導入する手順を教えてください。また、導入時の注意点や必要な準備についても詳しく説明してください。",
        "故障受付シートの名称と記入方法について教えてください。また、提出先や処理の流れも知りたいです。",
        "パソコンの価格帯について教えてください。"  # シンプルな質問（比較用）
    ]
    
    processor = get_enhanced_realtime_rag_processor()
    if not processor:
        logger.error("❌ テスト実行不可: プロセッサの初期化に失敗")
        return
    
    logger.info("🧪 拡張RAGシステムのテスト開始")
    
    for i, question in enumerate(sample_questions, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"🧪 テスト {i}/{len(sample_questions)}: {question}")
        logger.info(f"{'='*80}")
        
        try:
            result = await processor.process_enhanced_realtime_rag(question)
            
            logger.info(f"✅ テスト {i} 完了:")
            logger.info(f"   処理タイプ: {result.get('metadata', {}).get('processing_type', 'unknown')}")
            logger.info(f"   複雑度: {result.get('metadata', {}).get('question_analysis', {}).get('complexity_score', 0):.2f}")
            logger.info(f"   処理時間: {result.get('metadata', {}).get('total_processing_time', 0):.2f}秒")
            logger.info(f"   回答長: {len(result.get('answer', ''))}文字")
            logger.info(f"   回答プレビュー: {result.get('answer', '')[:200]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト {i} 失敗: {e}")
    
    logger.info("\n🎉 拡張RAGシステムのテスト完了")

if __name__ == "__main__":
    # テスト実行
    asyncio.run(test_enhanced_rag_with_sample_questions())