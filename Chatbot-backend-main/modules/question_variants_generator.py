"""
🔄 質問バリエーション生成モジュール
Geminiを使って質問の5つのバリエーションを生成し、RAG検索の精度を向上させます

生成されるバリエーション:
1. 元の質問（オリジナル）
2. 空白を削除した質問
3. 半角文字を全角にした質問  
4. 全角文字を半角にした質問
5. 表記ゆれを正規化した質問
"""

import os
import re
import json
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import unicodedata
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class QuestionVariants:
    """質問バリエーション結果"""
    original: str                    # 元の質問
    no_spaces: str                   # 空白削除版
    full_width: str                  # 半角→全角変換版
    half_width: str                  # 全角→半角変換版
    normalized: str                  # 表記ゆれ正規化版
    katakana_to_hiragana: str        # カタカナ→ひらがな変換版
    hiragana_to_katakana: str        # ひらがな→カタカナ変換版
    partial_keywords: List[str]      # 部分キーワード版
    abbreviations: List[str]         # 略称版
    combination_patterns: List[str]  # 組み合わせパターン版
    all_variants: List[str]          # 全バリエーションのリスト（重複除去済み）

class QuestionVariantsGenerator:
    """質問バリエーション生成システム"""
    
    def __init__(self):
        """初期化"""
        self.gemini_model = self._setup_gemini()
        
        # 表記ゆれ正規化ルール
        self.normalization_rules = {
            # 会社表記
            r'株式会社|㈱|（株）|\(株\)': '株式会社',
            r'有限会社|㈲|（有）|\(有\)': '有限会社', 
            r'合同会社|（同）|\(同\)': '合同会社',
            r'合資会社|（資）|\(資\)': '合資会社',
            r'合名会社|（名）|\(名\)': '合名会社',
            
            # 役職・人物関連
            r'代表者|トップ|社長|代表取締役|代表|責任者|リーダー|CEO|ceo|最高経営責任者': '代表者',
            r'社長|代表取締役社長|代表取締役|取締役社長': '社長',
            r'部長|マネージャー|部門長|責任者|リーダー|チーフ': '部長',
            r'担当者|担当|責任者|窓口': '担当者',
            r'経営者|オーナー|代表|トップ': '経営者',
            
            # 技術用語
            r'パソコン|ＰＣ|pc': 'PC',
            r'インターネット|ネット|WEB|ウェブ': 'インターネット',
            r'メール|Ｅメール|e-mail|email': 'メール',
            r'ホームページ|HP|ＨＰ|サイト': 'ホームページ',
            
            # 一般用語
            r'お問い合わせ|問合せ|問い合せ': 'お問い合わせ',
            r'連絡先|連絡先情報|コンタクト': '連絡先',
            r'電話番号|TEL|Tel|tel|ＴＥＬ': '電話番号',
            r'住所|所在地|アドレス': '住所',
            r'場所|住所|所在地|位置|アドレス': '住所',
            r'会社|企業|法人|事業者|組織': '会社',
            r'教えて|知りたい|聞きたい|分からない': '教えて',
        }
        
        logger.info("✅ 質問バリエーション生成システム初期化完了")
    
    def _setup_gemini(self):
        """Geminiモデルの設定"""
        try:
            import google.generativeai as genai
            
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.warning("⚠️ GEMINI_API_KEY環境変数が設定されていません")
                return None
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            return model
        except Exception as e:
            logger.error(f"❌ Gemini設定エラー: {e}")
            return None
    
    def _remove_spaces(self, text: str) -> str:
        """空白文字を削除"""
        # 全角・半角スペース、タブ、改行を削除
        return re.sub(r'[\s\u3000]+', '', text)
    
    def _to_full_width(self, text: str) -> str:
        """半角文字を全角に変換"""
        # ASCII文字（数字、英字、記号）を全角に変換
        result = ""
        for char in text:
            # ASCII範囲の文字を全角に変換
            if ord(char) >= 32 and ord(char) <= 126:
                # 半角スペースは全角スペースに
                if char == ' ':
                    result += '　'
                else:
                    # その他のASCII文字は全角に変換
                    full_width_char = chr(ord(char) - 32 + 65248)
                    result += full_width_char
            else:
                result += char
        return result
    
    def _to_half_width(self, text: str) -> str:
        """全角文字を半角に変換"""
        # 全角ASCII文字を半角に変換
        result = ""
        for char in text:
            # 全角スペースは半角スペースに
            if char == '　':
                result += ' '
            # 全角ASCII文字を半角に変換
            elif ord(char) >= 65248 and ord(char) <= 65370:
                half_width_char = chr(ord(char) - 65248 + 32)
                result += half_width_char
            # カタカナの全角→半角変換も実行
            else:
                # unicodedataを使ってNFKC正規化（全角→半角変換を含む）
                normalized_char = unicodedata.normalize('NFKC', char)
                result += normalized_char
        return result
    
    def _normalize_variations(self, text: str) -> str:
        """表記ゆれを正規化"""
        normalized = text
        
        # 正規化ルールを適用
        for pattern, replacement in self.normalization_rules.items():
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        return normalized
    
    def _katakana_to_hiragana(self, text: str) -> str:
        """カタカナをひらがなに変換"""
        result = ""
        for char in text:
            # カタカナ範囲（ア-ヴ）をひらがな範囲（あ-ゔ）に変換
            if 'ア' <= char <= 'ヴ':
                hiragana_char = chr(ord(char) - ord('ア') + ord('あ'))
                result += hiragana_char
            else:
                result += char
        return result
    
    def _hiragana_to_katakana(self, text: str) -> str:
        """ひらがなをカタカナに変換"""
        result = ""
        for char in text:
            # ひらがな範囲（あ-ゔ）をカタカナ範囲（ア-ヴ）に変換
            if 'あ' <= char <= 'ゔ':
                katakana_char = chr(ord(char) - ord('あ') + ord('ア'))
                result += katakana_char
            else:
                result += char
        return result
    
    def _extract_partial_keywords(self, text: str) -> List[str]:
        """部分キーワードを抽出"""
        keywords = []
        
        # 会社名パターンの抽出
        company_patterns = [
            r'([^。、\s]+(?:株式会社|合同会社|有限会社|合資会社|合名会社))',
            r'([^。、\s]+会社)',
            r'([^。、\s]+(?:Corporation|Corp|Inc|LLC|Ltd))'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                keywords.append(match)
                # 会社名部分のみ（法人格除く）も追加
                company_name_only = re.sub(r'(株式会社|合同会社|有限会社|合資会社|合名会社|会社|Corporation|Corp|Inc|LLC|Ltd)$', '', match).strip()
                if company_name_only and company_name_only != match:
                    keywords.append(company_name_only)
        
        # 単語分割（2文字以上の単語）
        words = re.findall(r'[ぁ-ゟァ-ヿ一-龯ａ-ｚＡ-Ｚ０-９a-zA-Z0-9]{2,}', text)
        keywords.extend(words)
        
        # 電話番号パターン
        phone_patterns = [
            r'\d{2,4}-\d{2,4}-\d{4}',
            r'\d{3}-\d{3}-\d{4}',
            r'\(\d{2,4}\)\s*\d{2,4}-\d{4}',
            r'\d{10,11}'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            keywords.extend(matches)
        
        return keywords
    
    def _generate_abbreviations(self, text: str) -> List[str]:
        """略称パターンを生成（スペースパターン含む）"""
        abbreviations = []
        
        # 会社名の略称
        company_patterns = [
            r'([^。、\s]+)(株式会社|合同会社|有限会社|合資会社|合名会社)',
            r'(株式会社|合同会社|有限会社|合資会社|合名会社)\s*([^。、\s]+)'
        ]
        
        for pattern in company_patterns:
            company_match = re.search(pattern, text)
            if company_match:
                if len(company_match.groups()) == 2:
                    if pattern.startswith('([^'):  # 会社名が先にあるパターン
                        company_name = company_match.group(1)
                        company_type = company_match.group(2)
                    else:  # 法人格が先にあるパターン
                        company_type = company_match.group(1)
                        company_name = company_match.group(2)
                    
                    # 法人格の略称
                    company_abbreviations = {
                        '株式会社': ['㈱'],
                        '有限会社': ['㈲'],
                        '合同会社': ['(同)', '（同）'],
                        '合資会社': ['(資)', '（資）'],
                        '合名会社': ['(名)', '（名）']
                    }
                    
                    if company_type in company_abbreviations:
                        for abbrev in company_abbreviations[company_type]:
                            # スペースなし、半角スペース、全角スペースの3パターン
                            abbreviations.extend([
                                f'{abbrev}{company_name}',
                                f'{abbrev} {company_name}',
                                f'{abbrev}　{company_name}'
                            ])
                    
                    # カタカナの略称（最初の文字のみ）
                    katakana_chars = re.findall(r'[ァ-ヿ]', company_name)
                    if len(katakana_chars) >= 2:
                        abbreviations.append(''.join(katakana_chars[:2]))  # 最初の2文字
                        abbreviations.append(''.join(katakana_chars))      # 全カタカナ
                    
                    # 英語略称（大文字の最初の文字）
                    english_chars = re.findall(r'[A-Z]', company_name)
                    if len(english_chars) >= 2:
                        abbreviations.append(''.join(english_chars))
        
        # よくある略語パターン
        abbreviation_map = {
            'リアライズ': ['リア', 'ライズ', 'RL'],
            'インターナショナル': ['インター', 'インタナショナル', 'Intl'],
            'コーポレーション': ['コープ', 'Corp'],
            'システム': ['シス', 'Sys'],
            'サービス': ['サビス', 'Srv'],
            'テクノロジー': ['テック', 'Tech'],
            'ソリューション': ['ソリュー', 'Sol'],
            'エンジニアリング': ['エンジ', 'Eng'],
            'コンサルティング': ['コンサル', 'Cons'],
            'マネジメント': ['マネジ', 'Mgmt'],
        }
        
        for full_word, abbrevs in abbreviation_map.items():
            if full_word in text:
                abbreviations.extend(abbrevs)
        
        return abbreviations
    
    def _generate_combination_patterns(self, base_text: str, keywords: List[str], abbreviations: List[str]) -> List[str]:
        """組み合わせパターンを生成（スペースパターン含む）"""
        combinations = []
        
        # 基本的な組み合わせ
        combinations.append(base_text)
        
        # キーワード同士の組み合わせ（3つのスペースパターン）
        for i, keyword1 in enumerate(keywords[:5]):  # 最初の5個まで
            for j, keyword2 in enumerate(keywords[:5]):
                if i != j and len(keyword1) > 1 and len(keyword2) > 1:
                    # 3つのスペースパターン
                    combinations.append(f"{keyword1}{keyword2}")   # スペースなし
                    combinations.append(f"{keyword1} {keyword2}")  # 半角スペース
                    combinations.append(f"{keyword1}　{keyword2}") # 全角スペース
        
        # 略称との組み合わせ（3つのスペースパターン）
        for abbrev in abbreviations[:3]:  # 最初の3個まで
            combinations.append(abbrev)
            for keyword in keywords[:3]:
                if keyword != abbrev and len(keyword) > 1:
                    # 3つのスペースパターン
                    combinations.extend([
                        f"{abbrev}{keyword}",   # スペースなし
                        f"{abbrev} {keyword}",  # 半角スペース
                        f"{abbrev}　{keyword}", # 全角スペース
                        f"{keyword}{abbrev}",   # 逆順スペースなし
                        f"{keyword} {abbrev}",  # 逆順半角スペース
                        f"{keyword}　{abbrev}"  # 逆順全角スペース
                    ])
        
        # 法人格との組み合わせパターン
        company_types = ['株式会社', '有限会社', '合同会社', '合資会社', '合名会社']
        for company_type in company_types:
            if company_type in base_text:
                for keyword in keywords[:3]:
                    if keyword != company_type and len(keyword) > 1:
                        # 法人格 + 会社名のパターン（3つのスペースパターン）
                        combinations.extend([
                            f"{company_type}{keyword}",   # スペースなし
                            f"{company_type} {keyword}",  # 半角スペース
                            f"{company_type}　{keyword}"  # 全角スペース
                        ])
        
        return combinations
    
    async def generate_variants_with_gemini(self, question: str) -> QuestionVariants:
        """
        🧠 Geminiを使って質問の5つのバリエーションを生成
        
        Args:
            question: 元の質問
            
        Returns:
            QuestionVariants: 5つのバリエーション
        """
        logger.info(f"🔄 質問バリエーション生成開始: '{question}'")
        
        if not self.gemini_model:
            logger.warning("⚠️ Geminiが利用できません。基本変換のみ実行")
            return self._generate_basic_variants(question)
        
        try:
            # 質問の言語に適応した言い換えプロンプト
            prompt = f"""
あなたは質問バリエーションを生成する専門のAIです。与えられた質問に対して、意味を変えずに表記だけを変更したバリエーションを、以下のJSON形式で**のみ**生成してください。**JSON以外の一切のテキスト（説明、前書き、後書きなど）は含めないでください。**

【法人格のスペース規則（重要）】
・『会社』という語を含む法人格（例: 株式会社、有限会社、合同会社、㈱ など）の直後には、必ず半角スペースを 1 つ入れてください。
  例）
    ×「株式会社ABC」 → ○「株式会社 ABC」
    ×「(株)ABC」     → ○"(株) ABC"

【重要な制約】
- 質問の意味・内容は絶対に変更しないこと。
- あくまで「表記の言い換え」に限定し、新しい情報を追加しないこと。
- 文字種変換（全角⇔半角、大文字⇔小文字、カタカナ⇔ひらがななど）、スペースの有無（半角スペース、全角スペース、スペースなし）、法人格や組織名の表記バリエーション、同義語での置き換え、句読点・記号の有無や種類、その言語固有の表記ゆれや慣用表現を考慮してバリエーションを作成すること。

**質問:**
{question}

**以下のJSON形式で、最大10個のバリエーションを生成してください。余計な説明は含めないでください。**
{{
  "variants": [
    {{"text": "バリエーション1", "reason": "変更内容の説明"}},
    {{"text": "バリエーション2", "reason": "変更内容の説明"}}
  ]
}}
"""
            
            # Gemini実行（保守的設定：意味を変えない言い換え重視）
            import google.generativeai as genai
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.4,  # 一貫性重視で意味変更を防止
                    max_output_tokens=2048,  # 50個のバリエーション生成
                    top_p=0.8,  # 適度な多様性
                    top_k=50    # 適度な候補数
                )
            )
            
            if not response or not response.text:
                logger.warning("⚠️ Geminiからの応答が空です")
                return self._generate_basic_variants(question)
            
            # JSON解析
            json_content_to_parse = response.text.strip()
            
            # まず、MarkdownコードブロックからJSON内容を正確に抽出
            # r'```json\s*(\{.*?\})\s*```' は、`json`の後の空白と、JSONオブジェクトの開始・終了、その後の空白、
            # そして最後の` ``` `を考慮しています。`.*?`は非貪欲マッチで、最初の`}`で停止します。
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', json_content_to_parse, re.DOTALL)
            
            if json_match:
                json_content_to_parse = json_match.group(1) # グループ1はJSONオブジェクトのみ
                logger.info("✅ Markdownコードブロック内のJSONを抽出しました。")
            else:
                logger.warning("⚠️ Markdownコードブロック内のJSONが見つかりませんでした。応答全体をJSONとして解析を試みます。")

            try:
                variants_data = json.loads(json_content_to_parse)
                logger.info("✅ JSONを正常に解析しました。")
            except json.JSONDecodeError as e:
                logger.error(f"❌ 最終的なJSON解析エラー: {e}. 基本バリエーション生成にフォールバックします。")
                return self._generate_basic_variants(question)
            
            # バリエーションを構築
            variants = variants_data.get("variants", [])
            
            # 重複を除去しつつ全バリエーションリストを作成
            all_variants = []
            variant_reasons = []  # 理由も保存
            
            for variant_data in variants:
                variant = variant_data.get("text", "")
                reason = variant_data.get("reason", "")
                if variant and variant.strip():
                    all_variants.append(variant.strip())
                    variant_reasons.append(reason)
            
            # 重複除去（順序保持）
            unique_variants = list(dict.fromkeys(all_variants))
            unique_reasons = []
            for variant in unique_variants:
                idx = all_variants.index(variant)
                unique_reasons.append(variant_reasons[idx])
            
            all_variants = unique_variants
            variant_reasons = unique_reasons
            
            result = QuestionVariants(
                original=question,
                no_spaces=self._remove_spaces(question),
                full_width=self._to_full_width(question),
                half_width=self._to_half_width(question),
                normalized=question,  # AIが生成するので正規化なし
                katakana_to_hiragana=self._katakana_to_hiragana(question),
                hiragana_to_katakana=self._hiragana_to_katakana(question),
                partial_keywords=[],  # AIによる自由生成を重視
                abbreviations=[],     # AIによる自由生成を重視
                combination_patterns=[],  # AIによる自由生成を重視
                all_variants=all_variants
            )
            
            logger.info(f"✅ Geminiバリエーション生成完了: {len(all_variants)}個のユニークなバリエーション")
            logger.info(f"🔄 生成されたバリエーション:")
            for i, variant in enumerate(all_variants, 1):
                reason = variant_reasons[i-1] if i-1 < len(variant_reasons) else "生成理由不明"
                logger.info(f"   {i}. {variant} (理由: {reason})")
            
            # 🔥 必須パターン: 法人格の後ろに半角スペースのバリエーションを追加
            essential_space_patterns = self._generate_essential_space_patterns(question)
            for pattern in essential_space_patterns:
                if pattern and pattern.strip() and pattern not in all_variants:
                    all_variants.append(pattern.strip())
                    logger.info(f"   ✅ 必須パターン追加: {pattern}")
            
            # 会社の後ろに半角スペースを強制するルールを適用
            all_variants = self._apply_company_space_rule(all_variants)
            
            # 重複再除去して10個に制限
            dedup = []
            for v in all_variants:
                if v not in dedup:
                    dedup.append(v)
            all_variants = dedup[:10]
            
            # all_variantsを更新
            result.all_variants = all_variants
            
            logger.info(f"🎯 最終バリエーション数: {len(all_variants)}個（Gemini生成 + 必須パターン）")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Geminiバリエーション生成エラー: {e}")
            return self._generate_basic_variants(question)
    
    def _generate_basic_variants(self, question: str) -> QuestionVariants:
        """軽量基本バリエーション生成（AIフォールバック時のミニマル版）"""
        logger.info("🔄 軽量基本バリエーション生成実行中（AIによる自由予測を重視）...")
        
        # 基本変換のみ実行
        original = question.strip()
        
        # 最小限の基本バリエーションのみ
        all_variants = [
            original,  # 元の質問
            self._remove_spaces(original),  # スペース削除のみ
            self._to_full_width(original),  # 全角変換のみ
            self._to_half_width(original),  # 半角変換のみ
        ]
        
        # 重複除去
        unique_variants = []
        for variant in all_variants:
            if variant and variant.strip():
                unique_variants.append(variant.strip())
        
        # 重複除去（順序保持）
        unique_variants = list(dict.fromkeys(unique_variants))
        
        # 🔥 必須パターン: 法人格の後ろに半角スペースのバリエーションを追加
        essential_space_patterns = self._generate_essential_space_patterns(original)
        for pattern in essential_space_patterns:
            if pattern and pattern.strip() and pattern not in unique_variants:
                unique_variants.append(pattern.strip())
        
        # 会社の後ろに半角スペースを強制するルールを適用
        unique_variants = self._apply_company_space_rule(unique_variants)
        
        # 10個に制限
        unique_variants = unique_variants[:10]
        
        logger.info(f"✅ ミニマル基本バリエーション生成完了: {len(unique_variants)}個のシンプルなバリエーション")
        logger.warning("⚠️ AIによる高精度バリエーション生成が推奨されます（GEMINI_API_KEYを設定してください）")
        
        result = QuestionVariants(
            original=original,
            no_spaces=self._remove_spaces(original),
            full_width=self._to_full_width(original),
            half_width=self._to_half_width(original),
            normalized=original,  # 正規化なし
            katakana_to_hiragana=self._katakana_to_hiragana(original),
            hiragana_to_katakana=self._hiragana_to_katakana(original),
            partial_keywords=[],  # 固定的な抽出なし
            abbreviations=[],     # 固定的な略称なし
            combination_patterns=[],  # 固定的な組み合わせなし
            all_variants=unique_variants
        )
        
        return result
    
    def _generate_generic_space_patterns(self, text: str) -> List[str]:
        """汎用的なスペースパターン生成"""
        patterns = []
        
        # 基本的なスペース変換
        if ' ' in text:  # 半角スペースがある場合
            patterns.append(text.replace(' ', '　'))  # 全角スペースに変換
            patterns.append(text.replace(' ', ''))    # スペース削除
            patterns.append(text.replace(' ', '  '))  # ダブルスペース
        
        if '　' in text:  # 全角スペースがある場合
            patterns.append(text.replace('　', ' '))  # 半角スペースに変換
            patterns.append(text.replace('　', ''))   # スペース削除
        
        # 単語間へのスペース挿入（汎用的）
        words = text.split()
        if len(words) >= 2:
            # 異なるスペースパターン
            patterns.append('　'.join(words))  # 全角スペース
            patterns.append(' '.join(words))   # 半角スペース
            patterns.append(''.join(words))    # スペースなし
            
            # 部分的なスペース変更
            for i in range(len(words) - 1):
                new_words = words.copy()
                patterns.append(' '.join(new_words[:i+1]) + '　' + ' '.join(new_words[i+1:]))
        
        # 文字レベルでのスペース挿入（長い文字列の場合）
        if len(text) > 6 and ' ' not in text and '　' not in text:
            mid = len(text) // 2
            patterns.append(text[:mid] + ' ' + text[mid:])
            patterns.append(text[:mid] + '　' + text[mid:])
        
        return patterns
    
    def _generate_generic_character_patterns(self, text: str) -> List[str]:
        """汎用的な文字種変換パターン"""
        patterns = []
        
        # 全体的な文字種変換
        patterns.append(self._to_full_width(text))
        patterns.append(self._to_half_width(text))
        patterns.append(self._katakana_to_hiragana(text))
        patterns.append(self._hiragana_to_katakana(text))
        
        # 部分的な文字種変換（単語単位）
        words = re.findall(r'[^\s]+', text)
        for i, word in enumerate(words):
            if len(word) > 1:  # 1文字の単語は除外
                modified_words = words.copy()
                
                # 各単語を個別に変換
                modified_words[i] = self._to_full_width(word)
                if ' ' in text:
                    patterns.append(' '.join(modified_words))
                else:
                    patterns.append(''.join(modified_words))
                
                modified_words[i] = self._to_half_width(word)
                if ' ' in text:
                    patterns.append(' '.join(modified_words))
                else:
                    patterns.append(''.join(modified_words))
                
                modified_words[i] = self._katakana_to_hiragana(word)
                if ' ' in text:
                    patterns.append(' '.join(modified_words))
                else:
                    patterns.append(''.join(modified_words))
                
                modified_words[i] = self._hiragana_to_katakana(word)
                if ' ' in text:
                    patterns.append(' '.join(modified_words))
                else:
                    patterns.append(''.join(modified_words))
        
        return patterns
    
    def _generate_generic_punctuation_patterns(self, text: str) -> List[str]:
        """汎用的な句読点・記号パターン"""
        patterns = []
        
        # 基本的な句読点・記号変換
        punctuation_mappings = {
            '(': '（', ')': '）', '（': '(', '）': ')',
            '-': '－', '－': '-', '.': '。', '。': '.',
            ',': '、', '、': ',', '?': '？', '？': '?',
            '!': '！', '！': '!', ':': '：', '：': ':',
            ';': '；', '；': ';', '"': '"', '"': '"',
            '[': '［', ']': '］', '［': '[', '］': ']'
        }
        
        for original_punct, replacement_punct in punctuation_mappings.items():
            if original_punct in text:
                patterns.append(text.replace(original_punct, replacement_punct))
        
        # 語尾の句読点調整
        common_endings = ['。', '.', '？', '?', '！', '!']
        for ending in common_endings:
            if text.endswith(ending):
                patterns.append(text[:-1])  # 語尾削除
            else:
                patterns.append(text + ending)  # 語尾追加
        
        # 疑問文・感嘆文パターン
        if not any(text.endswith(e) for e in ['？', '?', '！', '!']):
            patterns.append(text + 'ですか')
            patterns.append(text + 'でしょうか')
        
        return patterns
    
    def _generate_generic_dot_patterns(self, text: str) -> List[str]:
        """汎用的な中点・分割パターン"""
        patterns = []
        
        # カタカナ語の中点挿入
        katakana_words = re.findall(r'[ァ-ヿー]+', text)
        for word in katakana_words:
            if len(word) >= 4:  # 4文字以上のカタカナ語
                # 自然な分割点で中点挿入
                for pos in range(2, len(word) - 1, 2):  # 2文字おきに分割点
                    dotted = word[:pos] + '・' + word[pos:]
                    patterns.append(text.replace(word, dotted))
        
        # 英語単語の中点挿入
        english_words = re.findall(r'[A-Za-z]+', text)
        for word in english_words:
            if len(word) >= 4:  # 4文字以上の英語単語
                mid = len(word) // 2
                dotted = word[:mid] + '・' + word[mid:]
                patterns.append(text.replace(word, dotted))
        
        # 数字の区切り
        numbers = re.findall(r'\d{4,}', text)  # 4桁以上の数字
        for num in numbers:
            if len(num) >= 4:
                # 3桁区切り
                formatted = f"{num[:len(num)-3]},{num[-3:]}"
                patterns.append(text.replace(num, formatted))
                # ハイフン区切り
                mid = len(num) // 2
                formatted = f"{num[:mid]}-{num[mid:]}"
                patterns.append(text.replace(num, formatted))
        
        return patterns
    
    def _generate_generic_notation_patterns(self, text: str) -> List[str]:
        """汎用的な表記ゆれパターン"""
        patterns = []
        
        # 一般的な表記ゆれマッピング（拡張可能）
        notation_mappings = {
            # 技術用語
            'パソコン': ['PC', 'ＰＣ', 'コンピュータ', 'コンピューター'],
            'PC': ['パソコン', 'ＰＣ', 'コンピュータ'],
            'ＰＣ': ['パソコン', 'PC', 'コンピュータ'],
            'メール': ['mail', 'Mail', 'MAIL', 'Eメール', 'e-mail', 'email'],
            'ホームページ': ['HP', 'ＨＰ', 'サイト', 'ウェブサイト', 'website'],
            'インターネット': ['ネット', 'WEB', 'ウェブ', 'web'],
            
            # 基本語彙
            'について': ['に関して', 'に付いて', 'につきまして', 'について'],
            '教えて': ['教えてください', 'お教えください', 'ご教示ください'],
            'ください': ['下さい', 'クダサイ'],
            'どこ': ['どちら', '何処', 'どこら'],
            'いつ': ['何時', 'いつごろ'],
            'なに': ['何', 'ナニ'],
            'だれ': ['誰', 'ダレ'],
            
            # 敬語・丁寧語
            'です': ['である', 'だ', 'であります'],
            'ます': ['る', 'ている'],
            'ある': ['あります', 'ございます'],
            
            # 数字表記
            '1': ['一', '１', 'いち'],
            '2': ['二', '２', 'に'],
            '3': ['三', '３', 'さん'],
            '4': ['四', '４', 'よん', 'し'],
            '5': ['五', '５', 'ご'],
        }
        
        for original, alternatives in notation_mappings.items():
            if original in text:
                for alt in alternatives:
                    patterns.append(text.replace(original, alt))
        
        return patterns
    
    def _generate_substring_patterns(self, text: str) -> List[str]:
        """部分文字列パターン生成"""
        patterns = []
        
        # 単語の抽出（シンプルな分割）
        words = text.split()
        for word in words:
            # 句読点を除去
            clean_word = re.sub(r'[^\w]', '', word)
            if len(clean_word) >= 2:  # 2文字以上の単語
                patterns.append(clean_word)
        
        # フレーズの抽出（2-3単語の組み合わせ）
        words_list = text.split()
        if len(words_list) >= 2:
            for i in range(len(words_list) - 1):
                # 2単語の組み合わせ
                phrase = f"{words_list[i]} {words_list[i+1]}"
                patterns.append(phrase)
                patterns.append(f"{words_list[i]}{words_list[i+1]}")  # スペースなし
                
                # 3単語の組み合わせ
                if i + 2 < len(words_list):
                    phrase3 = f"{words_list[i]} {words_list[i+1]} {words_list[i+2]}"
                    patterns.append(phrase3)
        
        # キーワード抽出（カタカナ、英語、漢字）
        katakana_words = re.findall(r'[ァ-ヿー]{2,}', text)
        patterns.extend(katakana_words)
        
        english_words = re.findall(r'[A-Za-z]{2,}', text)
        patterns.extend(english_words)
        
        kanji_words = re.findall(r'[一-龯]{2,}', text)
        patterns.extend(kanji_words)
        
        return patterns
    
    def _generate_generic_combinations(self, base_variants: List[str]) -> List[str]:
        """汎用的な組み合わせパターン"""
        combinations = []
        
        # 既存バリエーションに追加変換を適用
        for variant in base_variants[:10]:  # 最初の10個のみ使用
            if variant:
                # スペース処理の追加適用
                if ' ' in variant:
                    combinations.append(variant.replace(' ', '　'))
                    combinations.append(variant.replace(' ', ''))
                if '　' in variant:
                    combinations.append(variant.replace('　', ' '))
                    combinations.append(variant.replace('　', ''))
                
                # 文字種の追加変換
                combinations.append(self._to_full_width(variant))
                combinations.append(self._to_half_width(variant))
                combinations.append(self._katakana_to_hiragana(variant))
                combinations.append(self._hiragana_to_katakana(variant))
                
                # 正規化の追加適用
                combinations.append(self._normalize_variations(variant))
        
        return combinations
    
    def _generate_micro_adjustments(self, text: str, existing_variants: List[str]) -> List[str]:
        """微調整パターン（50個到達のための補完）"""
        patterns = []
        
        # 既存バリエーションの微細な調整
        for variant in existing_variants[:20]:  # 最初の20個を使用
            if len(patterns) >= 30:  # 最大30個追加
                break
            
            # スペースの微調整
            if ' ' in variant:
                patterns.append(variant.replace(' ', '  '))  # ダブルスペース
            
            # 重複文字の除去
            deduplicated = re.sub(r'(.)\1+', r'\1', variant)
            if deduplicated != variant:
                patterns.append(deduplicated)
            
            # 語尾の微調整
            if not variant.endswith(('。', '.', '？', '?', '！', '!')):
                patterns.append(variant + '。')
                patterns.append(variant + '？')
        
        # 元テキストの構造的変更（控えめ）
        words = text.split()
        if len(words) == 2:
            # 2単語の場合のみ順序入れ替え
            patterns.append(f"{words[1]} {words[0]}")
            patterns.append(f"{words[1]}　{words[0]}")
            patterns.append(f"{words[1]}{words[0]}")
        
        # 文字列の分割パターン
        if len(text) > 4:
            for pos in [len(text)//3, len(text)//2, (len(text)*2)//3]:
                if 1 < pos < len(text) - 1:
                    patterns.append(text[:pos] + ' ' + text[pos:])
                    patterns.append(text[:pos] + '　' + text[pos:])
        
        return patterns

    def _generate_essential_space_patterns(self, text: str) -> List[str]:
        """必須スペースパターン生成（法人格の後ろに半角スペース）"""
        patterns = []
        
        # 法人格パターンの定義
        company_patterns = [
            # 基本的な法人格
            r'(株式会社)([^\s])',  # 株式会社ABC → 株式会社 ABC
            r'(有限会社)([^\s])',  # 有限会社ABC → 有限会社 ABC  
            r'(合同会社)([^\s])',  # 合同会社ABC → 合同会社 ABC
            r'(合資会社)([^\s])',  # 合資会社ABC → 合資会社 ABC
            r'(合名会社)([^\s])',  # 合名会社ABC → 合名会社 ABC
            
            # 略称法人格
            r'(㈱)([^\s])',        # ㈱ABC → ㈱ ABC
            r'(㈲)([^\s])',        # ㈲ABC → ㈲ ABC
            r'(\(株\))([^\s])',    # (株)ABC → (株) ABC
            r'(（株）)([^\s])',     # （株）ABC → （株） ABC
            r'(\(有\))([^\s])',    # (有)ABC → (有) ABC
            r'(（有）)([^\s])',     # （有）ABC → （有） ABC
            
            # 社団・財団法人
            r'(一般社団法人)([^\s])',   # 一般社団法人ABC → 一般社団法人 ABC
            r'(公益社団法人)([^\s])',   # 公益社団法人ABC → 公益社団法人 ABC
            r'(一般財団法人)([^\s])',   # 一般財団法人ABC → 一般財団法人 ABC
            r'(公益財団法人)([^\s])',   # 公益財団法人ABC → 公益財団法人 ABC
            r'(社会福祉法人)([^\s])',   # 社会福祉法人ABC → 社会福祉法人 ABC
            r'(学校法人)([^\s])',       # 学校法人ABC → 学校法人 ABC
            r'(医療法人)([^\s])',       # 医療法人ABC → 医療法人 ABC
            
            # 一般的な組織名パターン
            r'(会社)([^\s])',     # 会社ABC → 会社 ABC
            r'([^\s]+工業)([^\s])',     # ABC工業DEF → ABC工業 DEF
            r'([^\s]+社団)([^\s])',     # ABC社団DEF → ABC社団 DEF
            r'([^\s]+法人)([^\s])',     # ABC法人DEF → ABC法人 DEF
            r'([^\s]+協会)([^\s])',     # ABC協会DEF → ABC協会 DEF
            r'([^\s]+組合)([^\s])',     # ABC組合DEF → ABC組合 DEF
            r'([^\s]+財団)([^\s])',     # ABC財団DEF → ABC財団 DEF
        ]
        
        # 逆パターン（スペースありからスペースなしへ）
        reverse_patterns = [
            r'(株式会社)\s+([^\s])',   # 株式会社 ABC → 株式会社ABC
            r'(有限会社)\s+([^\s])',   # 有限会社 ABC → 有限会社ABC
            r'(合同会社)\s+([^\s])',   # 合同会社 ABC → 合同会社ABC
            r'(合資会社)\s+([^\s])',   # 合資会社 ABC → 合資会社ABC
            r'(合名会社)\s+([^\s])',   # 合名会社 ABC → 合名会社ABC
            r'(㈱)\s+([^\s])',         # ㈱ ABC → ㈱ABC
            r'(㈲)\s+([^\s])',         # ㈲ ABC → ㈲ABC
            r'(\(株\))\s+([^\s])',     # (株) ABC → (株)ABC
            r'(（株）)\s+([^\s])',      # （株） ABC → （株）ABC
            r'(\(有\))\s+([^\s])',     # (有) ABC → (有)ABC
            r'(（有）)\s+([^\s])',      # （有） ABC → （有）ABC
            r'(一般社団法人)\s+([^\s])', # 一般社団法人 ABC → 一般社団法人ABC
            r'(公益社団法人)\s+([^\s])', # 公益社団法人 ABC → 公益社団法人ABC
            r'(一般財団法人)\s+([^\s])', # 一般財団法人 ABC → 一般財団法人ABC
            r'(公益財団法人)\s+([^\s])', # 公益財団法人 ABC → 公益財団法人ABC
        ]
        
        # 法人格の後にスペースを追加するパターン
        for pattern in company_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # スペースを追加
                new_text = text.replace(match.group(0), f"{match.group(1)} {match.group(2)}")
                if new_text != text:
                    patterns.append(new_text)
        
        # スペースありからスペースなしへのパターン
        for pattern in reverse_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # スペースを削除
                new_text = text.replace(match.group(0), f"{match.group(1)}{match.group(2)}")
                if new_text != text:
                    patterns.append(new_text)
        
        # 全角スペースから半角スペースへの変換も追加
        if '　' in text:  # 全角スペースがある場合
            patterns.append(text.replace('　', ' '))  # 半角スペースに変換
        
        # 半角スペースから全角スペースへの変換も追加
        if ' ' in text:  # 半角スペースがある場合
            patterns.append(text.replace(' ', '　'))  # 全角スペースに変換
        
        return patterns

    def _apply_company_space_rule(self, variants: List[str]) -> List[str]:
        """バリエーション内の『会社』の後に必ず半角スペースを入れるルールを適用

        例: "会社ABC" → "会社 ABC"
        複数スペースや全角スペースが存在する場合は半角スペース1つに正規化します。
        """
        processed: List[str] = []

        # 法人格リスト（必ず半角スペースを入れたい語）
        legal_entities = [
            '株式会社', '有限会社', '合同会社', '合資会社', '合名会社',
            '一般社団法人', '公益社団法人', '一般財団法人', '公益財団法人',
            '社会福祉法人', '学校法人', '医療法人',
            '㈱', '㈲', '(株)', '（株）', '(有)', '（有）', '会社'
        ]

        # 正規表現パターン生成
        patterns = [(re.compile(fr'({re.escape(le)})[\s　]*([^\s　])'), le) for le in legal_entities]

        for txt in variants:
            new_txt = txt
            for pattern, le in patterns:
                new_txt = pattern.sub(rf"{le} \2", new_txt)
            # 重複半角スペースを1つに
            new_txt = re.sub(r" {2,}", " ", new_txt)
            if new_txt not in processed and new_txt.strip():
                processed.append(new_txt.strip())
        return processed

    async def generate_variants(self, question: str) -> QuestionVariants:
        """
        メイン質問バリエーション生成メソッド
        Geminiが利用可能な場合はGeminiを使用、そうでなければ基本バリエーション生成を使用
        
        Args:
            question: 元の質問
            
        Returns:
            QuestionVariants: 生成されたバリエーション
        """
        logger.info(f"🔄 質問バリエーション生成開始: '{question}'")
        
        # Geminiが利用可能な場合はGeminiを使用
        if self.gemini_model:
            try:
                logger.info("🧠 Geminiを使用してバリエーション生成")
                return await self.generate_variants_with_gemini(question)
            except Exception as e:
                logger.error(f"❌ Geminiバリエーション生成失敗、基本生成にフォールバック: {e}")
                return self._generate_basic_variants(question)
        else:
            # Geminiが利用できない場合は基本バリエーション生成を使用
            logger.info("💡 基本バリエーション生成を使用")
            return self._generate_basic_variants(question)

# グローバルインスタンス
_variants_generator = None

def get_question_variants_generator() -> QuestionVariantsGenerator:
    """質問バリエーション生成システムのインスタンスを取得"""
    global _variants_generator
    if _variants_generator is None:
        _variants_generator = QuestionVariantsGenerator()
    return _variants_generator

async def generate_question_variants(question: str) -> QuestionVariants:
    """
    質問バリエーションを生成（外部呼び出し用）
    
    Args:
        question: 元の質問
        
    Returns:
        QuestionVariants: 生成されたバリエーション
    """
    generator = get_question_variants_generator()
    return await generator.generate_variants(question)

def variants_generator_available() -> bool:
    """質問バリエーション生成システムが利用可能かチェック"""
    try:
        # Geminiが利用できなくても基本バリエーション生成は常に利用可能
        generator = get_question_variants_generator()
        return True  # 基本バリエーション生成は常に利用可能
    except Exception:
        return False 