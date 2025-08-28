"""
質問内容を分析してカテゴリーを自動分類するモジュール
"""
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from modules.config import setup_gemini
from modules.multi_gemini_client import get_multi_gemini_client, multi_gemini_available

logger = logging.getLogger(__name__)

class QuestionCategorizer:
    """質問内容を分析してカテゴリーを分類するクラス"""
    
    def __init__(self):
        self.model = setup_gemini()
        self.multi_client = None
        self._init_multi_client()
    
    def _init_multi_client(self):
        """Multi Gemini Clientの初期化"""
        try:
            if multi_gemini_available():
                self.multi_client = get_multi_gemini_client()
                logger.info("✅ QuestionCategorizer: Multi Gemini Client初期化完了")
            else:
                logger.warning("⚠️ QuestionCategorizer: Multi Gemini Client利用不可")
        except Exception as e:
            logger.error(f"❌ QuestionCategorizer: Multi Gemini Client初期化失敗: {e}")
            self.multi_client = None
        self.categories = {
            "company_info": "🏢 会社情報",
            "product_service": "🛍️ 商品・サービス",
            "procedure": "📋 手続き・業務",
            "equipment": "💻 設備・環境",
            "hr_labor": "👥 人事・労務",
            "technical": "🔧 技術サポート",
            "finance": "💰 経理・財務",
            "general": "💬 一般的な質問",
            "greeting": "👋 挨拶・雑談",
            "other": "🔗 その他"
        }
    
    def categorize_question(self, question: str) -> Dict[str, Any]:
        """
        質問内容を分析してカテゴリーを返す
        
        Args:
            question: 質問文
            
        Returns:
            Dict containing category, confidence, and reasoning
        """
        if not question or not question.strip():
            return {
                "category": "other",
                "display_name": self.categories["other"],
                "confidence": 0.0,
                "reasoning": "空の質問"
            }
        
        if not self.model:
            return self._fallback_categorization(question)
        
        try:
            prompt = f"""
以下の質問内容を分析して、最適なカテゴリーを1つ選択してください。

# 質問内容
{question}

# 選択可能なカテゴリー
- company_info: 企業情報、会社名、住所、連絡先、代表者名など
- product_service: 商品、サービス、料金、価格に関する質問
- procedure: 手続き、業務フロー、申込み、設置作業など
- equipment: PC、設備、機器に関する質問
- hr_labor: 人事、労務、採用、給与に関する質問
- technical: 技術的な問題、システム、IT関連
- finance: 経理、財務、会計に関する質問
- general: 一般的な質問、説明要求
- greeting: 挨拶、雑談、感謝など
- other: その他、分類困難なもの

# 回答形式
以下のJSON形式で回答してください：
{{
    "category": "選択したカテゴリーのキー",
    "confidence": 0.0-1.0の信頼度,
    "reasoning": "選択理由を30文字以内で"
}}

回答例：
{{
    "category": "company_info",
    "confidence": 0.95,
    "reasoning": "企業名が含まれているため"
}}
"""
            
            # Multi Gemini Clientを優先使用
            response = None
            if self.multi_client:
                try:
                    logger.info("🔄 QuestionCategorizer: Multi Gemini Client使用")
                    generation_config = {
                        "temperature": 0.1,
                        "maxOutputTokens": 4096,  # 🔧 MAX_TOKENSエラー回避（1024→4096）
                        "topP": 0.8,
                        "topK": 40
                    }
                    
                    # 既存のイベントループをチェック
                    try:
                        # 既存のループがある場合は新しいスレッドで実行
                        import concurrent.futures
                        import threading
                        
                        def run_async_in_thread():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                return new_loop.run_until_complete(
                                    self.multi_client.generate_content(prompt, generation_config)
                                )
                            finally:
                                new_loop.close()
                        
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(run_async_in_thread)
                            response_data = future.result(timeout=30)  # 30秒タイムアウト
                        
                        # レスポンスデータから text を抽出
                        if response_data:
                            text = None
                            
                            # 複数のレスポンス形式に対応
                            if isinstance(response_data, dict):
                                if "candidates" in response_data:
                                    candidate = response_data["candidates"][0]
                                    if "content" in candidate and "parts" in candidate["content"]:
                                        text = candidate["content"]["parts"][0]["text"]
                                elif "text" in response_data:
                                    text = response_data["text"]
                                elif "content" in response_data:
                                    text = response_data["content"]
                            elif isinstance(response_data, str):
                                text = response_data
                            elif hasattr(response_data, 'text'):
                                text = response_data.text
                            
                            if text:
                                # 互換性のためのレスポンスオブジェクト作成
                                class MockResponse:
                                    def __init__(self, text):
                                        self.text = text
                                response = MockResponse(text)
                                logger.info("✅ QuestionCategorizer: Multi Gemini Client成功")
                            else:
                                logger.warning("⚠️ QuestionCategorizer: レスポンスからテキストを抽出できませんでした")
                                logger.info(f"🔍 レスポンス形式詳細分析: {type(response_data)}")
                                if isinstance(response_data, dict):
                                    logger.info(f"🔍 辞書キー: {list(response_data.keys())}")
                                    if 'candidates' in response_data and response_data['candidates']:
                                        logger.info(f"🔍 候補構造: {response_data['candidates'][0] if response_data['candidates'] else 'なし'}")
                                logger.info(f"🔍 レスポンス内容: {str(response_data)[:500]}...")
                                
                                # 追加のフォールバック処理
                                if isinstance(response_data, dict):
                                    # よりディープな検索
                                    def extract_text_recursive(obj):
                                        if isinstance(obj, str):
                                            return obj
                                        elif isinstance(obj, dict):
                                            for key, value in obj.items():
                                                if key == 'text' and isinstance(value, str):
                                                    return value
                                                result = extract_text_recursive(value)
                                                if result:
                                                    return result
                                        elif isinstance(obj, list):
                                            for item in obj:
                                                result = extract_text_recursive(item)
                                                if result:
                                                    return result
                                        return None
                                    
                                    extracted_text = extract_text_recursive(response_data)
                                    if extracted_text:
                                        class MockResponse:
                                            def __init__(self, text):
                                                self.text = text
                                        response = MockResponse(extracted_text)
                                        logger.info("✅ QuestionCategorizer: 再帰的テキスト抽出成功")
                                    else:
                                        logger.error("❌ QuestionCategorizer: 再帰的抽出も失敗")
                                        # MAX_TOKENSエラーの場合はデフォルトカテゴリを使用
                                        if 'finishReason' in str(response_data) and 'MAX_TOKENS' in str(response_data):
                                            logger.info("🎯 MAX_TOKENSエラー検出 - デフォルトカテゴリで継続")
                                            class MockResponse:
                                                def __init__(self, text):
                                                    self.text = text
                                            response = MockResponse("general")
                                        else:
                                            response = None
                    
                    except Exception as async_error:
                        logger.warning(f"⚠️ QuestionCategorizer: 非同期実行エラー: {async_error}")
                        logger.debug(f"詳細エラー: {type(async_error).__name__}: {str(async_error)}")
                        response = None
                        
                except Exception as multi_error:
                    logger.warning(f"⚠️ QuestionCategorizer: Multi Gemini Client失敗: {multi_error}")
                    logger.debug(f"詳細エラー: {type(multi_error).__name__}: {str(multi_error)}")
                    response = None
            
            # フォールバック: 従来の単一APIキー方式（ただし、レート制限の場合はスキップ）
            if not response and self.model:
                logger.info("🔄 QuestionCategorizer: 従来方式でフォールバック")
                logger.debug(f"フォールバック理由: Multi Gemini Client response = {response}")
                try:
                    response = self.model.generate_content(prompt)
                    logger.info("✅ QuestionCategorizer: 従来方式成功")
                except Exception as fallback_error:
                    logger.error(f"❌ QuestionCategorizer: 従来方式エラー: {fallback_error}")
                    if "429" in str(fallback_error) or "rate limit" in str(fallback_error).lower():
                        logger.warning("⚠️ QuestionCategorizer: フォールバックもレート制限、キーワードベース分類に切り替え")
                        return self._fallback_categorization(question)
                    else:
                        raise fallback_error
            
            if response and hasattr(response, 'text') and response.text:
                # JSONを抽出してパース
                text = response.text.strip()
                
                # コードブロックから抽出
                if "```json" in text:
                    json_start = text.find("```json") + 7
                    json_end = text.find("```", json_start)
                    if json_end != -1:
                        text = text[json_start:json_end].strip()
                elif "```" in text:
                    json_start = text.find("```") + 3
                    json_end = text.find("```", json_start)
                    if json_end != -1:
                        text = text[json_start:json_end].strip()
                
                # JSONパース
                try:
                    result = json.loads(text)
                    category = result.get("category", "other")
                    confidence = float(result.get("confidence", 0.5))
                    reasoning = result.get("reasoning", "AI分析")
                    
                    # カテゴリーが有効か確認
                    if category not in self.categories:
                        category = "other"
                    
                    return {
                        "category": category,
                        "display_name": self.categories[category],
                        "confidence": confidence,
                        "reasoning": reasoning
                    }
                
                except json.JSONDecodeError:
                    logger.warning(f"JSON解析エラー: {text}")
                    return self._fallback_categorization(question)
            
            return self._fallback_categorization(question)
            
        except Exception as e:
            logger.error(f"質問分類エラー: {str(e)}")
            return self._fallback_categorization(question)
    
    def _fallback_categorization(self, question: str) -> Dict[str, Any]:
        """
        フォールバック分類（キーワードベース）
        
        Args:
            question: 質問文
            
        Returns:
            分類結果
        """
        question_lower = question.lower()
        
        # キーワードベースの分類
        keyword_mapping = {
            "company_info": [
                "株式会社", "有限会社", "合同会社", "一般社団法人", "社名", "会社名", 
                "住所", "代表者", "電話番号", "連絡先", "企業", "法人"
            ],
            "product_service": [
                "パソコン", "pc", "料金", "価格", "商品", "サービス", "安い", "高い", 
                "おすすめ", "製品", "販売", "購入"
            ],
            "procedure": [
                "手続き", "申込", "設置", "作業", "確認書", "書類", "流れ", "方法", 
                "どうすれば", "やり方", "申請"
            ],
            "equipment": [
                "pc", "パソコン", "設備", "機器", "台数", "利用中", "使用中", "導入"
            ],
            "hr_labor": [
                "採用", "人事", "給与", "労務", "社員", "従業員", "退職", "入社"
            ],
            "technical": [
                "エラー", "問題", "トラブル", "設定", "システム", "接続", "動作"
            ],
            "finance": [
                "経理", "会計", "財務", "請求", "支払", "費用", "予算"
            ],
            "greeting": [
                "こんにちは", "おはよう", "ありがとう", "よろしく", "お疲れ", "おーーい", "はじめまして"
            ]
        }
        
        max_matches = 0
        best_category = "general"
        
        for category, keywords in keyword_mapping.items():
            matches = sum(1 for keyword in keywords if keyword in question_lower)
            if matches > max_matches:
                max_matches = matches
                best_category = category
        
        # マッチしたキーワードがない場合は一般的な質問として分類
        if max_matches == 0:
            best_category = "general"
        
        return {
            "category": best_category,
            "display_name": self.categories[best_category],
            "confidence": min(0.8, max_matches * 0.2),  # キーワード数に基づく信頼度
            "reasoning": f"キーワードマッチ({max_matches}個)"
        }
    
    def batch_categorize(self, questions: list) -> Dict[str, Any]:
        """
        複数の質問を一括で分類
        
        Args:
            questions: 質問のリスト
            
        Returns:
            分類結果の辞書
        """
        results = {}
        
        for i, question in enumerate(questions):
            if question:
                result = self.categorize_question(question)
                results[question] = result
                
                # 進捗ログ
                if (i + 1) % 10 == 0:
                    logger.info(f"質問分類進捗: {i + 1}/{len(questions)}")
        
        return results

# グローバルインスタンス
_categorizer = None

def get_categorizer():
    """カテゴライザーのシングルトンインスタンスを取得"""
    global _categorizer
    if _categorizer is None:
        _categorizer = QuestionCategorizer()
    return _categorizer

def categorize_question(question: str) -> Dict[str, Any]:
    """質問を分類する便利関数"""
    categorizer = get_categorizer()
    return categorizer.categorize_question(question) 