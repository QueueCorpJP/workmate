"""
🧠 Gemini 2.5 Flash質問分解・分類システム
質問をトークン分解・分類してSQL検索とEmbedding検索を最適化

実装内容:
1. Gemini 2.5 Flashを使って質問をトークン分解・分類
2. SQLに変換して構造的に探索（高速・精密）
3. 結果がゼロ件ならEmbedding検索にフォールバック
"""

import os
import re
import json
import logging
import asyncio
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)

class QueryIntent(Enum):
    """質問の意図分類"""
    SPECIFIC_INFO = "specific_info"      # 具体的情報を求める（代表者名、連絡先など）
    GENERAL_INFO = "general_info"        # 一般的情報を求める（サービス概要など）
    COMPARISON = "comparison"            # 比較・違いを求める
    EXPLANATION = "explanation"          # 説明・理由を求める
    PROCEDURE = "procedure"              # 手順・方法を求める
    UNKNOWN = "unknown"                  # 不明

@dataclass
class QueryAnalysisResult:
    """質問分析結果"""
    intent: QueryIntent
    confidence: float
    target_entity: str              # 対象エンティティ（会社名、人名など）
    keywords: List[str]             # 抽出されたキーワード
    sql_patterns: List[str]         # SQL検索パターン
    embedding_fallback: bool        # Embedding検索が必要か
    reasoning: str                  # 判定理由

@dataclass
class SearchResult:
    """検索結果"""
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    score: float
    search_method: str
    metadata: Dict = None

class GeminiQuestionAnalyzer:
    """Gemini 2.5 Flash質問分解・分類システム"""
    
    def __init__(self):
        """初期化"""
        self.db_url = self._get_db_url()
        self.gemini_model = self._setup_gemini()
        
        # SQL検索パターンテンプレート
        self.sql_templates = {
            "exact_match": "content ILIKE '%{keyword}%'",
            "company_representative": "content ~* '{company}.*代表者|代表者.*{company}'",
            "contact_info": "content ~* '{entity}.*(連絡先|電話|メール|住所)'",
            "multiple_keywords": " AND ".join(["content ILIKE '%{keyword}%'" for keyword in ["{keyword1}", "{keyword2}"]]),
            "regex_pattern": "content ~* '{pattern}'"
        }
        
        logger.info("✅ Gemini質問分解・分類システム初期化完了")
    
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
    
    def _setup_gemini(self):
        """Gemini 2.5 Flashモデルの設定"""
        try:
            import google.generativeai as genai
            
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY環境変数が設定されていません")
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            return model
        except Exception as e:
            logger.error(f"❌ Gemini設定エラー: {e}")
            return None
    
    async def analyze_question(self, question: str) -> QueryAnalysisResult:
        """
        🧠 Gemini 2.5 Flashを使って質問を分解・分類
        
        Args:
            question: ユーザーの質問
            
        Returns:
            QueryAnalysisResult: 分析結果
        """
        logger.info(f"🧠 Gemini質問分析開始: '{question}'")
        
        if not self.gemini_model:
            logger.warning("⚠️ Geminiモデルが利用できません。フォールバック分析を実行")
            fallback_result = self._fallback_analysis(question)
            return await self._append_variants(question, fallback_result)
        
        try:
            # 改善されたGemini 2.5 Flashプロンプト
            prompt = f"""
質問を分析して、検索に最適化されたキーワードを抽出してください。以下のJSON形式で回答してください：

質問: 「{question}」

分析項目:
1. 意図 (intent): specific_info, general_info, comparison, explanation, procedure, unknown のいずれか
2. 信頼度 (confidence): 0.0-1.0の数値
3. 対象エンティティ (target_entity): 会社名、人名、サービス名など（質問から推測される）
4. キーワード (keywords): 検索に最重要なキーワードのリスト（以下の指針に従う）

【キーワード抽出の指針】
- 電話番号が含まれる場合: 電話番号そのものを最重要キーワードとして含める
- 企業名を求める場合: 「社名」「会社名」「企業名」「株式会社」「有限会社」「合同会社」を含める
- 連絡先を求める場合: 「電話」「TEL」「連絡先」「住所」「メール」を含める
- 代表者を求める場合: 「代表者」「社長」「代表取締役」「責任者」「トップ」「CEO」「リーダー」「経営者」「オーナー」を含める
- 具体的な固有名詞（電話番号、会社名、人名など）は必ず含める
- 一般的な助詞（の、を、は、が、に、で、と、から、まで）は除外する

5. 判定理由 (reasoning): 判定の根拠

回答例1（電話番号から企業名を探す場合）:
{{
  "intent": "specific_info",
  "confidence": 0.95,
  "target_entity": "企業名",
  "keywords": ["053-442-6707", "電話番号", "社名", "会社名", "企業名", "株式会社"],
  "reasoning": "特定の電話番号から企業名を特定する具体的情報の質問"
}}

回答例2（代表者名を探す場合）:
{{
  "intent": "specific_info",
  "confidence": 0.90,
  "target_entity": "代表者名",
  "keywords": ["ABC株式会社", "代表者", "社長", "代表取締役", "責任者", "トップ", "CEO", "リーダー"],
  "reasoning": "特定企業の代表者名を求める具体的情報の質問"
}}

JSON形式のみで回答してください：
"""
            
            # Gemini 2.5 Flashで分析実行
            response = self.gemini_model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,  # 一貫性重視
                    'max_output_tokens': 1024,
                    'top_p': 0.8,
                    'top_k': 40
                }
            )
            
            if not response or not response.text:
                logger.warning("⚠️ Geminiからの応答が空です")
                fallback_result = self._fallback_analysis(question)
                return await self._append_variants(question, fallback_result)
            
            # JSON解析
            try:
                analysis_data = json.loads(response.text.strip())
            except json.JSONDecodeError:
                # JSONでない場合は、JSON部分を抽出
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    analysis_data = json.loads(json_match.group())
                else:
                    logger.warning("⚠️ Gemini応答からJSONを抽出できません")
                    fallback_result = self._fallback_analysis(question)
                    return await self._append_variants(question, fallback_result)
            
            # 結果の構築
            intent = QueryIntent(analysis_data.get("intent", "unknown"))
            confidence = float(analysis_data.get("confidence", 0.5))
            target_entity = analysis_data.get("target_entity", "")
            keywords = analysis_data.get("keywords", [])
            reasoning = analysis_data.get("reasoning", "Gemini分析結果")
            
            # キーワードの後処理（重複除去、空文字除去、同義語正規化）
            keywords = [k.strip() for k in keywords if k and k.strip()]
            keywords = list(dict.fromkeys(keywords))  # 順序を保ちながら重複除去
            
            # 🔥 同義語正規化を無効化（OR検索で対応）
            # keywords = self._normalize_synonyms(keywords)
            
            # SQL検索パターンの生成
            sql_patterns = self._generate_sql_patterns(intent, target_entity, keywords)
            
            # Embedding検索が必要かの判定
            embedding_fallback = intent in [QueryIntent.GENERAL_INFO, QueryIntent.EXPLANATION, QueryIntent.COMPARISON]
            
            result = QueryAnalysisResult(
                intent=intent,
                confidence=confidence,
                target_entity=target_entity,
                keywords=keywords,
                sql_patterns=sql_patterns,
                embedding_fallback=embedding_fallback,
                reasoning=reasoning
            )
            
            # バリエーションを追加
            result = await self._append_variants(question, result)
            
            logger.info(f"✅ Gemini分析完了: {intent.value} (信頼度: {confidence:.2f}) | キーワード数: {len(result.keywords)}")
            logger.info(f"🎯 対象エンティティ: {target_entity}")
            logger.info(f"🏷️ キーワード: {result.keywords}")
            logger.info(f"💭 判定理由: {reasoning}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Gemini分析エラー: {e}")
            fallback_result = self._fallback_analysis(question)
            return await self._append_variants(question, fallback_result)
    
    def _fallback_analysis(self, question: str) -> QueryAnalysisResult:
        """フォールバック分析（Geminiが利用できない場合）"""
        logger.info("🔄 フォールバック分析実行中...")
        
        # 簡単なパターンマッチング
        question_lower = question.lower()
        
        # 意図の判定
        if any(word in question_lower for word in ['代表者', '社長', 'トップ', 'ceo', '連絡先', '電話', '住所', '料金', '価格']):
            intent = QueryIntent.SPECIFIC_INFO
            confidence = 0.8
        elif any(word in question_lower for word in ['なぜ', 'どう', '理由', '背景']):
            intent = QueryIntent.EXPLANATION
            confidence = 0.6
        elif any(word in question_lower for word in ['手順', '方法', 'やり方']):
            intent = QueryIntent.PROCEDURE
            confidence = 0.6
        else:
            intent = QueryIntent.GENERAL_INFO
            confidence = 0.5
        
        # 改善されたキーワード抽出
        keywords = []
        
        # 電話番号の検出と追加
        phone_patterns = [
            r'\d{2,4}-\d{2,4}-\d{4}',  # 03-1234-5678
            r'\d{3}-\d{3}-\d{4}',      # 090-123-4567
            r'\(\d{2,4}\)\s*\d{2,4}-\d{4}',  # (03) 1234-5678
            r'\d{10,11}'               # 01234567890
        ]
        
        for pattern in phone_patterns:
            phone_matches = re.findall(pattern, question)
            for phone in phone_matches:
                keywords.append(phone)
        
        # 会社名の検出
        company_patterns = [
            r'([^。、\s]+(?:株式会社|合同会社|有限会社))', 
            r'([^。、\s]+会社)',
            r'([^。、\s]+(?:Corporation|Corp|Inc|LLC))'
        ]
        target_entity = ""
        for pattern in company_patterns:
            match = re.search(pattern, question)
            if match:
                target_entity = match.group(1)
                keywords.append(target_entity)
                break
        
        # 基本的な単語分割によるキーワード抽出
        exclude_words = ['は', 'が', 'を', 'に', 'で', 'と', 'から', 'まで', 'です', 'ます', 'だ', 'である', 'これ', 'それ', 'あの', 'その', 'この']
        for word in question.split():
            clean_word = re.sub(r'[。、！？]', '', word)
            if len(clean_word) > 1 and clean_word not in exclude_words:
                keywords.append(clean_word)
        
        # 質問の意図に基づくキーワード追加
        if '企業名' in question or '会社名' in question or '社名' in question:
            keywords.extend(['企業名', '会社名', '社名', '株式会社', '有限会社'])
            target_entity = "企業名"
            intent = QueryIntent.SPECIFIC_INFO
            confidence = 0.8
        
        if any(word in question for word in ['代表者', '社長', 'トップ', 'CEO', 'リーダー', '経営者', 'オーナー']):
            keywords.extend(['代表者', '社長', '代表取締役', '責任者', 'トップ', 'CEO', 'リーダー', '経営者', 'オーナー'])
            target_entity = "代表者"
            intent = QueryIntent.SPECIFIC_INFO
            confidence = 0.8
        
        if '電話' in question or 'TEL' in question or '連絡先' in question:
            keywords.extend(['電話', 'TEL', '連絡先', '電話番号'])
            intent = QueryIntent.SPECIFIC_INFO
            confidence = 0.8
        
        # 重複除去と空文字除去
        keywords = [k.strip() for k in keywords if k and k.strip()]
        keywords = list(dict.fromkeys(keywords))
        
        # 🔥 同義語正規化を無効化（OR検索で対応）
        # keywords = self._normalize_synonyms(keywords)
        
        # 対象エンティティの推測（キーワードから）
        if not target_entity:
            if any(k in keywords for k in ['企業名', '会社名', '社名']):
                target_entity = "企業名"
            elif any(k in keywords for k in ['代表者', '社長']):
                target_entity = "代表者"
            elif any(k in keywords for k in ['電話', 'TEL', '連絡先']):
                target_entity = "連絡先"
        
        sql_patterns = self._generate_sql_patterns(intent, target_entity, keywords)
        embedding_fallback = intent in [QueryIntent.GENERAL_INFO, QueryIntent.EXPLANATION]
        
        result = QueryAnalysisResult(
            intent=intent,
            confidence=confidence,
            target_entity=target_entity,
            keywords=keywords,
            sql_patterns=sql_patterns,
            embedding_fallback=embedding_fallback,
            reasoning="フォールバック分析による判定（パターンマッチング）"
        )
        
        logger.info(f"🔄 フォールバック分析完了: {len(keywords)}個のキーワードを抽出")
        logger.info(f"🏷️ フォールバックキーワード: {keywords}")
        
        return result
    
    def _normalize_synonyms(self, keywords: List[str]) -> List[str]:
        """
        同義語正規化: 検索精度を上げるため、同義語グループの中で最も検索しやすいキーワードのみを残す
        """
        # 同義語グループの定義（最初の要素が優先キーワード）
        synonym_groups = [
            # 役職関連
            ['代表者', 'トップ', 'CEO', 'ceo', 'リーダー', '経営者', 'オーナー', '社長', '代表取締役', '責任者'],
            # 会社関連
            ['会社', '企業', '法人', '事業者', '組織'],
            # 連絡先関連
            ['電話番号', 'TEL', 'Tel', 'tel', 'ＴＥＬ', '電話'],
            # 住所関連
            ['住所', '所在地', '場所', '位置', 'アドレス'],
            # 質問関連
            ['教えて', '知りたい', '聞きたい', '分からない'],
        ]
        
        normalized_keywords = keywords.copy()
        
        for group in synonym_groups:
            priority_keyword = group[0]  # グループの最初が優先キーワード
            found_keywords = [k for k in normalized_keywords if k in group]
            
            if len(found_keywords) > 1:
                # 複数の同義語が見つかった場合、優先キーワード以外を除去
                for keyword in found_keywords:
                    if keyword != priority_keyword:
                        try:
                            normalized_keywords.remove(keyword)
                            logger.info(f"🔄 同義語正規化: '{keyword}' → '{priority_keyword}'")
                        except ValueError:
                            pass  # 既に除去済み
        
        logger.info(f"✅ 同義語正規化完了: {len(keywords)}個 → {len(normalized_keywords)}個")
        return normalized_keywords
    
    def _classify_keywords(self, keywords: List[str]) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        キーワードを固有名詞（必須）と同義語グループ（選択）に分類
        
        Returns:
            Tuple[必須キーワード, 同義語グループ辞書]
        """
        # 同義語グループの定義
        synonym_groups_def = {
            'position': ['代表者', 'トップ', 'CEO', 'ceo', 'リーダー', '経営者', 'オーナー', '社長', '代表取締役', '責任者'],
            'company_type': ['会社', '企業', '法人', '事業者', '組織', '株式会社', '有限会社', '合同会社'],
            'contact': ['電話番号', 'TEL', 'Tel', 'tel', 'ＴＥＬ', '電話', '連絡先'],
            'location': ['住所', '所在地', '場所', '位置', 'アドレス'],
            'question_words': ['教えて', '知りたい', '聞きたい', '分からない'],
        }
        
        required_keywords = []
        found_synonym_groups = {}
        
        for keyword in keywords:
            is_synonym = False
            
            # 同義語グループに属するかチェック
            for group_name, group_words in synonym_groups_def.items():
                if keyword in group_words:
                    if group_name not in found_synonym_groups:
                        found_synonym_groups[group_name] = []
                    found_synonym_groups[group_name].append(keyword)
                    is_synonym = True
                    break
            
            # 同義語グループに属さない場合は固有名詞として扱う
            if not is_synonym:
                # 電話番号パターンのチェック
                phone_patterns = [
                    r'\d{2,4}-\d{2,4}-\d{4}',
                    r'\d{3}-\d{3}-\d{4}',
                    r'\(\d{2,4}\)\s*\d{2,4}-\d{4}',
                    r'\d{10,11}'
                ]
                
                is_phone = any(re.match(pattern, keyword) for pattern in phone_patterns)
                
                # メールアドレスパターンのチェック
                is_email = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', keyword)
                
                # 固有名詞として分類（会社名、人名、電話番号、メールアドレスなど）
                if (len(keyword) >= 2 and not keyword in ['です', 'ます', 'ている', 'だ', 'である']) or is_phone or is_email:
                    required_keywords.append(keyword)
        
        logger.info(f"🔍 キーワード分類結果:")
        logger.info(f"   固有名詞（必須）: {required_keywords}")
        logger.info(f"   同義語グループ（選択）: {found_synonym_groups}")
        
        return required_keywords, found_synonym_groups
    
    def _generate_sql_patterns(self, intent: QueryIntent, target_entity: str, keywords: List[str]) -> List[str]:
        """SQL検索パターンの生成（キーワードベース）"""
        # 新しい実装では、キーワードリストをそのまま返す
        # 実際のSQL構築は execute_sql_search で行う
        return keywords
    
    async def execute_sql_search(self, analysis: QueryAnalysisResult, company_id: str = None, limit: int = 10) -> List[SearchResult]:
        """
        🔍 SQL構造的検索の実行
        
        Args:
            analysis: 質問分析結果
            company_id: 会社ID（オプション）
            limit: 結果数制限
            
        Returns:
            List[SearchResult]: 検索結果
        """
        logger.info(f"🔍 SQL構造的検索開始: キーワード={analysis.keywords}")
        
        all_results = []
        
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    
                    # 特殊なパターン検索（電話番号、メールアドレス等）
                    special_patterns = self._detect_special_patterns(analysis.keywords)
                    
                    if special_patterns:
                        logger.info(f"🎯 特殊パターン検索: {special_patterns}")
                        for pattern_type, pattern_value in special_patterns.items():
                            if pattern_type == "phone_number":
                                # 電話番号専用検索
                                phone_results = await self._search_by_phone_number(cur, pattern_value, company_id, limit)
                                all_results.extend(phone_results)
                            elif pattern_type == "email":
                                # メールアドレス専用検索
                                email_results = await self._search_by_email(cur, pattern_value, company_id, limit)
                                all_results.extend(email_results)
                    
                    # キーワードベースの検索を実行
                    if analysis.keywords:
                        # 🔥 スマート検索: 固有名詞（AND）+ 同義語グループ（OR）
                        if len(analysis.keywords) >= 2:
                            logger.info(f"🔍 スマート検索（固有名詞AND + 同義語OR）: {analysis.keywords}")
                            
                            # キーワードを固有名詞と同義語グループに分類
                            required_keywords, synonym_groups = self._classify_keywords(analysis.keywords)
                            
                            # WHERE句の構築
                            where_conditions = []
                            params = []
                            
                            # 1. 固有名詞は必須（AND）
                            for keyword in required_keywords:
                                if any(char in keyword for char in ['-', '(', ')', '.']):
                                    where_conditions.append("c.content ~* %s")
                                    params.append(re.escape(keyword))
                                else:
                                    where_conditions.append("c.content ILIKE %s")
                                    params.append(f"%{keyword}%")
                            
                            # 2. 同義語グループは選択（OR）
                            for group_name, synonyms in synonym_groups.items():
                                if synonyms:
                                    or_conditions = []
                                    for synonym in synonyms:
                                        if any(char in synonym for char in ['-', '(', ')', '.']):
                                            or_conditions.append("c.content ~* %s")
                                            params.append(re.escape(synonym))
                                        else:
                                            or_conditions.append("c.content ILIKE %s")
                                            params.append(f"%{synonym}%")
                                    
                                    if or_conditions:
                                        where_conditions.append(f"({' OR '.join(or_conditions)})")
                            
                            if where_conditions:
                                sql = f"""
                                SELECT DISTINCT
                                    c.id as chunk_id,
                                    c.doc_id as document_id,
                                    c.chunk_index,
                                    c.content as snippet,
                                    ds.name as document_name,
                                    ds.type as document_type,
                                    1.0 as score
                                FROM chunks c
                                LEFT JOIN document_sources ds ON ds.id = c.doc_id
                                WHERE c.content IS NOT NULL
                                  AND LENGTH(c.content) > 10
                                  AND ({' OR '.join(where_conditions)})
                                """
                                
                                # 会社IDフィルタ
                                if company_id:
                                    sql += " AND c.company_id = %s"
                                    params.append(company_id)
                                
                                sql += " ORDER BY score DESC LIMIT %s"
                                params.append(limit)
                                
                                try:
                                    cur.execute(sql, params)
                                    results = cur.fetchall()
                                    
                                    for row in results:
                                        # 重複チェック
                                        if not any(r.chunk_id == row['chunk_id'] for r in all_results):
                                            all_results.append(SearchResult(
                                                chunk_id=row['chunk_id'],
                                                document_id=row['document_id'],
                                                document_name=row['document_name'] or 'Unknown',
                                                content=row['snippet'] or '',
                                                score=row['score'],
                                                search_method='sql_smart_search',
                                                metadata={
                                                    'required_keywords': required_keywords,
                                                    'synonym_groups': synonym_groups
                                                }
                                            ))
                                    
                                    logger.info(f"✅ スマート検索で{len(results)}件の結果")
                                    logger.info(f"   必須キーワード: {required_keywords}")
                                    logger.info(f"   同義語グループ: {list(synonym_groups.keys())}")
                                    
                                except Exception as e:
                                    logger.warning(f"⚠️ スマート検索エラー: {e}")
                        
                        # 2. 個別キーワード検索（結果が少ない場合）
                        if len(all_results) < limit:
                            for i, keyword in enumerate(analysis.keywords):
                                logger.info(f"🔍 個別キーワード検索 {i+1}/{len(analysis.keywords)}: {keyword}")
                                
                                # 特殊文字を含む場合は正規表現検索
                                if any(char in keyword for char in ['-', '(', ')', '.']):
                                    condition = "c.content ~* %s"
                                    keyword_param = re.escape(keyword)
                                else:
                                    condition = "c.content ILIKE %s"
                                    keyword_param = f"%{keyword}%"
                                
                                sql = f"""
                                SELECT DISTINCT
                                    c.id as chunk_id,
                                    c.doc_id as document_id,
                                    c.chunk_index,
                                    c.content as snippet,
                                    ds.name as document_name,
                                    ds.type as document_type,
                                    1.0 as score
                                FROM chunks c
                                LEFT JOIN document_sources ds ON ds.id = c.doc_id
                                WHERE c.content IS NOT NULL
                                  AND LENGTH(c.content) > 10
                                  AND {condition}
                                """
                                
                                params = [keyword_param]
                                
                                # 会社IDフィルタ
                                if company_id:
                                    sql += " AND c.company_id = %s"
                                    params.append(company_id)
                                
                                sql += " ORDER BY score DESC LIMIT %s"
                                params.append(limit)
                                
                                try:
                                    cur.execute(sql, params)
                                    results = cur.fetchall()
                                    
                                    for row in results:
                                        # 重複チェック
                                        if not any(r.chunk_id == row['chunk_id'] for r in all_results):
                                            all_results.append(SearchResult(
                                                chunk_id=row['chunk_id'],
                                                document_id=row['document_id'],
                                                document_name=row['document_name'] or 'Unknown',
                                                content=row['snippet'] or '',
                                                score=row['score'],
                                                search_method=f'sql_keyword_{i+1}',
                                                metadata={'keyword': keyword}
                                            ))
                                    
                                    logger.info(f"✅ キーワード「{keyword}」で{len(results)}件の結果")
                                    
                                except Exception as e:
                                    logger.warning(f"⚠️ キーワード「{keyword}」検索エラー: {e}")
                                    continue
            
            # 結果をスコア順でソート
            all_results.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(f"✅ SQL構造的検索完了: {len(all_results)}件の結果")
            return all_results[:limit]
            
        except Exception as e:
            logger.error(f"❌ SQL検索エラー: {e}")
            return []
    
    def _detect_special_patterns(self, keywords: List[str]) -> Dict[str, str]:
        """特殊パターン（電話番号、メールアドレス等）の検出"""
        patterns = {}
        
        for keyword in keywords:
            # 電話番号パターン
            phone_patterns = [
                r'\d{2,4}-\d{2,4}-\d{4}',  # 03-1234-5678
                r'\d{3}-\d{3}-\d{4}',      # 090-123-4567
                r'\(\d{2,4}\)\s*\d{2,4}-\d{4}',  # (03) 1234-5678
                r'\d{10,11}'               # 01234567890
            ]
            
            for pattern in phone_patterns:
                if re.match(pattern, keyword):
                    patterns['phone_number'] = keyword
                    break
            
            # メールアドレスパターン
            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', keyword):
                patterns['email'] = keyword
        
        return patterns
    
    async def _search_by_phone_number(self, cursor, phone_number: str, company_id: str = None, limit: int = 10) -> List[SearchResult]:
        """電話番号による専用検索"""
        logger.info(f"📞 電話番号検索: {phone_number}")
        
        results = []
        
        # 複数の電話番号フォーマットで検索
        phone_variants = self._generate_phone_variants(phone_number)
        
        for variant in phone_variants:
            sql = """
            SELECT DISTINCT
                c.id as chunk_id,
                c.doc_id as document_id,
                c.chunk_index,
                c.content as snippet,
                ds.name as document_name,
                ds.type as document_type,
                2.0 as score
            FROM chunks c
            LEFT JOIN document_sources ds ON ds.id = c.doc_id
            WHERE c.content IS NOT NULL
              AND LENGTH(c.content) > 10
              AND c.content ~* %s
            """
            
            params = [re.escape(variant)]
            
            if company_id:
                sql += " AND c.company_id = %s"
                params.append(company_id)
            
            sql += " ORDER BY score DESC LIMIT %s"
            params.append(limit)
            
            try:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                for row in rows:
                    # 重複チェック
                    if not any(r.chunk_id == row['chunk_id'] for r in results):
                        results.append(SearchResult(
                            chunk_id=row['chunk_id'],
                            document_id=row['document_id'],
                            document_name=row['document_name'] or 'Unknown',
                            content=row['snippet'] or '',
                            score=row['score'],
                            search_method='phone_search',
                            metadata={'phone_number': phone_number, 'variant': variant}
                        ))
                
                logger.info(f"📞 電話番号バリアント「{variant}」で{len(rows)}件")
                
            except Exception as e:
                logger.warning(f"⚠️ 電話番号検索エラー（{variant}）: {e}")
                continue
        
        return results
    
    def _generate_phone_variants(self, phone_number: str) -> List[str]:
        """電話番号の異なるフォーマットバリアントを生成"""
        # 数字のみを抽出
        digits_only = re.sub(r'[^\d]', '', phone_number)
        
        variants = [phone_number]  # 元の形式
        
        if len(digits_only) >= 10:
            # 様々なフォーマットを生成
            if len(digits_only) == 10:
                # 03-1234-5678
                variants.append(f"{digits_only[:2]}-{digits_only[2:6]}-{digits_only[6:]}")
                # 03(1234)5678
                variants.append(f"{digits_only[:2]}({digits_only[2:6]}){digits_only[6:]}")
            elif len(digits_only) == 11:
                # 090-123-4567
                variants.append(f"{digits_only[:3]}-{digits_only[3:6]}-{digits_only[6:]}")
                # 090(123)4567
                variants.append(f"{digits_only[:3]}({digits_only[3:6]}){digits_only[6:]}")
        
        # 数字のみ
        variants.append(digits_only)
        
        return list(set(variants))  # 重複を除去
    
    async def _search_by_email(self, cursor, email: str, company_id: str = None, limit: int = 10) -> List[SearchResult]:
        """メールアドレスによる専用検索"""
        logger.info(f"📧 メールアドレス検索: {email}")
        
        sql = """
        SELECT DISTINCT
            c.id as chunk_id,
            c.doc_id as document_id,
            c.chunk_index,
            c.content as snippet,
            ds.name as document_name,
            ds.type as document_type,
            2.0 as score
        FROM chunks c
        LEFT JOIN document_sources ds ON ds.id = c.doc_id
        WHERE c.content IS NOT NULL
          AND LENGTH(c.content) > 10
          AND c.content ILIKE %s
        """
        
        params = [f"%{email}%"]
        
        if company_id:
            sql += " AND c.company_id = %s"
            params.append(company_id)
        
        sql += " ORDER BY score DESC LIMIT %s"
        params.append(limit)
        
        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append(SearchResult(
                    chunk_id=row['chunk_id'],
                    document_id=row['document_id'],
                    document_name=row['document_name'] or 'Unknown',
                    content=row['snippet'] or '',
                    score=row['score'],
                    search_method='email_search',
                    metadata={'email': email}
                ))
            
            logger.info(f"📧 メールアドレス「{email}」で{len(results)}件")
            return results
            
        except Exception as e:
            logger.warning(f"⚠️ メールアドレス検索エラー: {e}")
            return []
    
    async def execute_embedding_search(self, question: str, company_id: str = None, limit: int = 10) -> List[SearchResult]:
        """
        📘 Embedding検索の実行（フォールバック）
        
        Args:
            question: 検索クエリ
            company_id: 会社ID（オプション）
            limit: 結果数制限
            
        Returns:
            List[SearchResult]: 検索結果
        """
        logger.info(f"📘 Embedding検索開始（フォールバック）: '{question}'")
        
        try:
            # Vertex AI Embeddingクライアントの取得
            from .vertex_ai_embedding import get_vertex_ai_embedding_client, vertex_ai_embedding_available
            
            if not vertex_ai_embedding_available():
                logger.warning("⚠️ Vertex AI Embeddingが利用できません")
                return []
            
            vertex_client = get_vertex_ai_embedding_client()
            if not vertex_client:
                logger.warning("⚠️ Vertex AIクライアントが取得できません")
                return []
            
            # クエリの埋め込み生成
            query_embedding = vertex_client.generate_embedding(question)
            if not query_embedding:
                logger.warning("⚠️ 埋め込み生成に失敗")
                return []
            
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # pgvectorを使用したベクトル検索
                    sql = """
                    SELECT DISTINCT
                        c.id as chunk_id,
                        c.doc_id as document_id,
                        c.chunk_index,
                        c.content as snippet,
                        ds.name as document_name,
                        ds.type as document_type,
                        (1 - (c.embedding <=> %s::vector)) as score
                    FROM chunks c
                    LEFT JOIN document_sources ds ON ds.id = c.doc_id
                    WHERE c.content IS NOT NULL
                      AND c.embedding IS NOT NULL
                      AND LENGTH(c.content) > 10
                    """
                    
                    params = [str(query_embedding)]
                    
                    if company_id:
                        sql += " AND c.company_id = %s"
                        params.append(company_id)
                    
                    sql += " ORDER BY score DESC LIMIT %s"
                    params.append(limit)
                    
                    cur.execute(sql, params)
                    results = cur.fetchall()
                    
                    search_results = []
                    for row in results:
                        search_results.append(SearchResult(
                            chunk_id=row['chunk_id'],
                            document_id=row['document_id'],
                            document_name=row['document_name'] or 'Unknown',
                            content=row['snippet'] or '',
                            score=row['score'],
                            search_method='embedding_fallback',
                            metadata={'similarity': row['score']}
                        ))
                    
                    logger.info(f"✅ Embedding検索完了: {len(search_results)}件の結果")
                    return search_results
                    
        except Exception as e:
            logger.error(f"❌ Embedding検索エラー: {e}")
            return []
    
    async def intelligent_search(self, question: str, company_id: str = None, limit: int = 20) -> Tuple[List[SearchResult], QueryAnalysisResult]:
        """
        🚀 インテリジェント検索の実行
        1. Gemini 2.5 Flashで質問分解・分類
        2. SQL構造的検索
        3. 結果がゼロ件ならEmbedding検索にフォールバック
        
        Args:
            question: ユーザーの質問
            company_id: 会社ID（オプション）
            limit: 結果数制限
            
        Returns:
            Tuple[検索結果リスト, 質問分析結果]
        """
        logger.info(f"🚀 インテリジェント検索開始: '{question}'")
        
        # 1. Gemini 2.5 Flashで質問分解・分析
        analysis = await self.analyze_question(question)
        
        # 2. SQL構造的検索の実行
        sql_results = await self.execute_sql_search(analysis, company_id, limit)
        
        # 3. 結果がゼロ件ならEmbedding検索にフォールバック
        if not sql_results and analysis.embedding_fallback:
            logger.info("🔄 SQL検索結果がゼロ件のため、Embedding検索にフォールバック")
            embedding_results = await self.execute_embedding_search(question, company_id, limit)
            
            # フォールバック結果をマーク
            for result in embedding_results:
                result.search_method = "embedding_fallback"
            
            final_results = embedding_results
        else:
            final_results = sql_results
        
        # 結果のログ出力
        self._log_search_results(question, analysis, final_results)
        
        logger.info(f"✅ インテリジェント検索完了: {len(final_results)}件の結果")
        return final_results, analysis
    
    def _log_search_results(self, question: str, analysis: QueryAnalysisResult, results: List[SearchResult]):
        """検索結果の詳細ログ出力"""
        logger.info("="*100)
        logger.info(f"🔍 【インテリジェント検索結果】{analysis.intent.value} - クエリ: '{question}'")
        logger.info("="*100)
        logger.info(f"🧠 質問意図: {analysis.intent.value}")
        logger.info(f"📊 信頼度: {analysis.confidence:.3f}")
        logger.info(f"🎯 対象エンティティ: {analysis.target_entity}")
        logger.info(f"🏷️ キーワード: {analysis.keywords}")
        logger.info(f"💭 判定理由: {analysis.reasoning}")
        logger.info(f"🔧 SQL検索パターン数: {len(analysis.sql_patterns)}")
        logger.info(f"📈 選定チャンク数: {len(results)}件")
        logger.info("-"*100)
        
        for i, result in enumerate(results[:5], 1):  # 上位5件のみ表示
            logger.info(f"📄 {i}. {result.document_name} [チャンク#{result.chunk_id}]")
            logger.info(f"    🎯 スコア: {result.score:.4f}")
            logger.info(f"    🔍 検索方法: {result.search_method}")
            logger.info(f"    📝 内容プレビュー: {result.content[:100]}...")

    async def _append_variants(self, question: str, result: QueryAnalysisResult) -> QueryAnalysisResult:
        """QuestionVariantsGenerator で得たバリエーションを keywords に追加する"""
        try:
            from modules.question_variants_generator import generate_question_variants, variants_generator_available  # 遅延 import で循環回避
        except Exception:
            return result  # ジェネレーターが読み込めない場合は何もしない

        if not variants_generator_available():
            return result

        try:
            variants = await generate_question_variants(question)
            additional = variants.all_variants if variants and variants.all_variants else []
            if additional:
                merged = list(dict.fromkeys(result.keywords + additional))
                # 法人格ベースで半角スペース正規化
                extra = []
                legal_entities = [
                    '株式会社', '有限会社', '合同会社', '合資会社', '合名会社',
                    '一般社団法人', '公益社団法人', '一般財団法人', '公益財団法人',
                    '社会福祉法人', '学校法人', '医療法人',
                    '㈱', '㈲', '(株)', '（株）', '(有)', '（有）'
                ]
                patterns = [re.compile(fr'({re.escape(le)})[\s　]*([^\s　])') for le in legal_entities]
                for kw in merged:
                    for pattern in patterns:
                        if pattern.search(kw):
                            spaced = pattern.sub(r"\1 \2", kw)
                            if spaced and spaced not in merged and spaced not in extra:
                                extra.append(spaced)
                            break
                merged.extend(extra)
                result.keywords = merged
                logger.info(f"🔄 バリエーション追加: +{len(additional)+len(extra)} → 総キーワード {len(merged)} 個 (半角スペース正規化含む)")
        except Exception as e:
            logger.error(f"❌ バリエーション生成エラー: {e}")
        return result

# グローバルインスタンス
_gemini_analyzer_instance = None

def get_gemini_question_analyzer() -> Optional[GeminiQuestionAnalyzer]:
    """Gemini質問分解・分類システムのインスタンスを取得"""
    global _gemini_analyzer_instance
    
    if _gemini_analyzer_instance is None:
        try:
            _gemini_analyzer_instance = GeminiQuestionAnalyzer()
            logger.info("✅ Gemini質問分解・分類システム初期化完了")
        except Exception as e:
            logger.error(f"❌ Gemini質問分解・分類システム初期化エラー: {e}")
            return None
    
    return _gemini_analyzer_instance

async def gemini_intelligent_search(question: str, company_id: str = None, limit: int = 20) -> Tuple[List[SearchResult], QueryAnalysisResult]:
    """Geminiインテリジェント検索の外部呼び出し用関数"""
    analyzer = get_gemini_question_analyzer()
    if not analyzer:
        return [], None
    
    return await analyzer.intelligent_search(question, company_id, limit)

def gemini_analyzer_available() -> bool:
    """Gemini質問分解・分類システムが利用可能かチェック"""
    try:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        return bool(api_key and supabase_url and supabase_key)
    except Exception:
        return False