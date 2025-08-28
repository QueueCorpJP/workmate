"""
質問分割モジュール
長い質問を複数の小さな質問に分割して処理効率を向上させる
"""

import re
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QuestionSegment:
    """分割された質問セグメント"""
    text: str
    priority: int  # 1-5 (1が最重要)
    category: str  # 'main', 'detail', 'example', 'follow_up'
    keywords: List[str]

class QuestionSplitter:
    """質問分割処理クラス"""
    
    def __init__(self):
        # 質問区切りのパターン
        self.split_patterns = [
            r'。\s*(?=[ま｢また｣|｢さらに｣|｢加えて｣|｢次に｣|｢それから｣])',  # 接続詞で区切り
            r'。\s*(?=\d+\.)',  # 番号付きリストで区切り
            r'。\s*(?=[（(]\d+[）)])',  # 番号付き括弧で区切り
            r'。\s*(?=[•・▶])',  # 箇条書きで区切り
            r'\?\s*(?=[ま｢また｣|｢さらに｣|｢加えて｣|｢次に｣])',  # 疑問符後の接続詞
        ]
        
        # 重要度判定キーワード
        self.priority_keywords = {
            1: ['最重要', '緊急', '必須', '必要', 'まず', '第一'],
            2: ['重要', '主要', '基本', '概要'],
            3: ['詳細', '具体的', '例えば', '詳しく'],
            4: ['補足', '追加', 'また', 'さらに'],
            5: ['参考', '余談', 'ちなみに', 'おまけ']
        }
    
    def should_split_question(self, question: str) -> bool:
        """質問を分割すべきかどうかを判定"""
        # 複数タスクキーワードによる判定（優先）
        multi_task_keywords = [
            'WPD', 'WPN',  # 物件番号が複数ある場合
            'について', 'に関して', 'と', 'および', 'ならびに',
            'また', 'さらに', '次に', '他に', 'あと', 'それから', 'そして',
            '1.', '2.', '3.', '①', '②', '③', '・', '•',
            'まず', '最初に', '続いて', '最後に'
        ]
        
        # 複数の質問があるかチェック
        question_marks = question.count('？') + question.count('?')
        
        # 複数タスクキーワードの数をカウント
        keyword_count = sum(question.count(keyword) for keyword in multi_task_keywords)
        
        # 物件番号が複数ある場合（WPDxxxxxx、WPNxxxxxxが複数）
        import re
        property_numbers = re.findall(r'WP[DN]\d{7}', question)
        
        # 分割条件を緩和（より多くの複数タスクを検出）
        split_conditions = [
            question_marks >= 2,  # 2つ以上の疑問符
            keyword_count >= 3,   # 3つ以上のマルチタスクキーワード
            len(property_numbers) >= 2,  # 複数の物件番号
            len(question) > 1500,  # 長い質問（3000から1500に緩和）
            '、' in question and len(question) > 200  # 読点があり200文字以上
        ]
        
        should_split = any(split_conditions)
        if should_split:
            logger.info(f"🎯 複数タスク検出: 疑問符{question_marks}個, キーワード{keyword_count}個, 物件{len(property_numbers)}個")
        
        return should_split
    
    def split_question(self, question: str) -> List[QuestionSegment]:
        """質問を複数のセグメントに分割"""
        logger.info(f"質問分割開始: {len(question)}文字")
        
        if not self.should_split_question(question):
            logger.info("分割不要と判定")
            return [QuestionSegment(
                text=question,
                priority=1,
                category='main',
                keywords=self._extract_keywords(question)
            )]
        
        segments = []
        
        # 汎用的な複数タスク分割（優先順位順）
        import re
        
        # 1. 明確な区切り文字による分割
        clear_separators = [
            r'(。\s*また)',  # 「。また」
            r'(。\s*さらに)',  # 「。さらに」  
            r'(。\s*次に)',  # 「。次に」
            r'(。\s*あと)',  # 「。あと」
            r'(\d+\.\s*)',  # 1. 2. 3. の番号付きリスト
            r'([①②③④⑤⑥⑦⑧⑨⑩])',  # 丸数字
            r'(・\s*)',  # 箇条書き
        ]
        
        for pattern in clear_separators:
            if re.search(pattern, question):
                parts = re.split(pattern, question)
                segments.extend(self._process_enhanced_split_parts(parts, pattern))
                break
        
        # 2. 接続詞による分割（明確な区切りがない場合）
        if not segments:
            connector_patterns = [
                r'(また、)',  # 「また、」
                r'(さらに、)',  # 「さらに、」
                r'(それから、)',  # 「それから、」
                r'(あと、)',  # 「あと、」
                r'(加えて、)',  # 「加えて、」
                r'(続いて、)',  # 「続いて、」
            ]
            
            for pattern in connector_patterns:
                if re.search(pattern, question):
                    parts = re.split(pattern, question)
                    segments.extend(self._process_enhanced_split_parts(parts, pattern))
                    break
        
        # 3. 物件番号による分割（特殊ケース）
        if not segments:
            property_numbers = re.findall(r'WP[DN]\d{7}', question)
            if len(property_numbers) >= 2:
                segments = self._split_by_property_numbers(question, property_numbers)
        
        # パターンマッチしない場合は長さベースで分割
        if not segments:
            segments = self._split_by_length(question)
        
        # 優先度とカテゴリの設定
        segments = self._assign_priorities_and_categories(segments)
        
        logger.info(f"質問分割完了: {len(segments)}個のセグメントに分割")
        return segments
    
    def _process_enhanced_split_parts(self, parts: List[str], pattern: str) -> List[QuestionSegment]:
        """強化された分割処理（接続詞を考慮）"""
        segments = []
        current_text = ""
        
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
                
            # 接続詞やパターンを除去
            import re
            if re.match(r'^(また|さらに|次に|あと|それから|加えて|続いて)[、。]?$', part):
                continue
            if re.match(r'^[\d①②③④⑤⑥⑦⑧⑨⑩・]\s*$', part):
                continue
                
            # 短すぎるパーツは前のセグメントに結合
            if len(part) < 10 and current_text:
                current_text += part
            else:
                # 前のセグメントを保存
                if current_text:
                    segments.append(QuestionSegment(
                        text=current_text.strip(),
                        priority=len(segments) + 1,
                        category='main',
                        keywords=self._extract_keywords(current_text)
                    ))
                current_text = part
        
        # 最後のセグメントを保存
        if current_text:
            segments.append(QuestionSegment(
                text=current_text.strip(),
                priority=len(segments) + 1,
                category='main',
                keywords=self._extract_keywords(current_text)
            ))
            
        logger.info(f"🔄 強化分割処理: {len(segments)}個のセグメント作成")
        return segments
    
    def _process_split_parts(self, parts: List[str]) -> List[QuestionSegment]:
        """分割された部分を処理（旧版・フォールバック用）"""
        segments = []
        for i, part in enumerate(parts):
            if part.strip():
                segments.append(QuestionSegment(
                    text=part.strip(),
                    priority=i + 1,
                    category='main' if i == 0 else 'detail',
                    keywords=self._extract_keywords(part)
                ))
        return segments
    
    def _split_by_property_numbers(self, question: str, property_numbers: List[str]) -> List[QuestionSegment]:
        """物件番号による分割（各物件に対して完全な質問を生成）"""
        segments = []
        
        # 共通の質問パターンを抽出
        common_patterns = [
            r'について.*教えて',
            r'の.*価格',
            r'の.*情報',
            r'の.*詳細',
            r'は.*どう',
            r'を.*知りたい'
        ]
        
        # 各物件番号に対して個別の質問を作成
        for i, prop_num in enumerate(property_numbers):
            # 基本的な質問: "物件番号について教えて"
            base_question = f"{prop_num}について教えて"
            
            # 元の質問から追加の要求を抽出
            additional_requests = []
            
            # 価格に関する質問
            if any(word in question for word in ['価格', '値段', '金額', 'コスト', '費用']):
                additional_requests.append(f"{prop_num}の価格")
            
            # 詳細に関する質問
            if any(word in question for word in ['詳細', '仕様', 'スペック', '情報']):
                additional_requests.append(f"{prop_num}の詳細情報")
            
            # 状況に関する質問
            if any(word in question for word in ['状況', '状態', 'ステータス', '進捗']):
                additional_requests.append(f"{prop_num}の状況")
            
            # 完全な質問を構築
            if additional_requests:
                full_question = f"{base_question}。また、{', '.join(additional_requests)}も知りたいです。"
            else:
                full_question = base_question
            
            segments.append(QuestionSegment(
                text=full_question,
                priority=i + 1,
                category='main',
                keywords=self._extract_keywords(full_question) + [prop_num]
            ))
        
        logger.info(f"物件番号による分割: {len(segments)}個の完全な質問を作成")
        for i, seg in enumerate(segments):
            logger.info(f"  セグメント{i+1}: {seg.text}")
        
        return segments
    
    def _split_by_length(self, question: str, max_length: int = 1500) -> List[QuestionSegment]:
        """長さベースでの質問分割"""
        segments = []
        sentences = re.split(r'[。？?]', question)
        
        current_segment = ""
        for sentence in sentences:
            if len(current_segment + sentence) > max_length and current_segment:
                segments.append(QuestionSegment(
                    text=current_segment.strip(),
                    priority=len(segments) + 1,
                    category='main' if len(segments) == 0 else 'detail',
                    keywords=self._extract_keywords(current_segment)
                ))
                current_segment = sentence
            else:
                current_segment += sentence + "。"
        
        if current_segment.strip():
            segments.append(QuestionSegment(
                text=current_segment.strip(),
                priority=len(segments) + 1,
                category='detail',
                keywords=self._extract_keywords(current_segment)
            ))
        
        return segments
    
    def _assign_priorities_and_categories(self, segments: List[QuestionSegment]) -> List[QuestionSegment]:
        """優先度とカテゴリの割り当て"""
        for segment in segments:
            # キーワードベースの優先度設定
            for priority, keywords in self.priority_keywords.items():
                if any(keyword in segment.text for keyword in keywords):
                    segment.priority = priority
                    break
            
            # カテゴリの細分化
            if any(word in segment.text for word in ['例えば', '具体的', '詳しく']):
                segment.category = 'example'
            elif any(word in segment.text for word in ['また', 'さらに', '加えて']):
                segment.category = 'follow_up'
        
        # 優先度順にソート
        segments.sort(key=lambda x: x.priority)
        return segments
    
    def _extract_keywords(self, text: str) -> List[str]:
        """テキストからキーワードを抽出"""
        # 簡単なキーワード抽出（名詞や重要そうな単語）
        keywords = []
        
        # カタカナ語を抽出
        katakana_words = re.findall(r'[ア-ヴー]{3,}', text)
        keywords.extend(katakana_words)
        
        # 英数字を含む単語を抽出
        english_words = re.findall(r'[A-Za-z0-9]{3,}', text)
        keywords.extend(english_words)
        
        # 重要そうな日本語キーワード
        important_patterns = [
            r'[手続流方法手順仕組]き?',
            r'[管理運用操作設定]',
            r'[システムサービス機能]',
            r'[会社企業組織部署]',
        ]
        
        for pattern in important_patterns:
            matches = re.findall(pattern, text)
            keywords.extend(matches)
        
        return list(set(keywords))  # 重複除去
    
    def merge_segments_responses(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分割した質問の回答をマージ"""
        logger.info(f"回答マージ開始: {len(responses)}個の回答")
        
        merged_answer_parts = []
        all_sources = []
        all_chunks = []
        
        for i, response in enumerate(responses):
            if response.get('answer'):
                merged_answer_parts.append(f"## {i+1}. 回答")
                merged_answer_parts.append(response['answer'])
                merged_answer_parts.append("")  # 空行
            
            if response.get('sources'):
                all_sources.extend(response['sources'])
            
            if response.get('used_chunks'):
                all_chunks.extend(response['used_chunks'])
        
        # 重複除去
        unique_sources = list(set(all_sources))
        
        final_answer = "\n".join(merged_answer_parts)
        if len(final_answer) > 100:  # 有用な回答がある場合
            final_answer += "\n\n## 📋 統合回答\n"
            final_answer += "上記の各項目について、関連する情報を総合的にご提供いたしました。"
            final_answer += "さらに詳細な情報が必要でしたら、具体的な項目についてお聞かせください。"
        
        logger.info(f"回答マージ完了: {len(final_answer)}文字")
        
        return {
            "answer": final_answer,
            "sources": unique_sources,
            "used_chunks": all_chunks,
            "segments_count": len(responses)
        }

# グローバルインスタンス
question_splitter = QuestionSplitter() 