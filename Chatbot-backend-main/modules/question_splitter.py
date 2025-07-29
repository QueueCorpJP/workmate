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
        # 文字数による判定
        if len(question) < 1000:
            return False
        
        # 複数の疑問符や接続詞の存在
        question_marks = question.count('？') + question.count('?')
        connectives = len(re.findall(r'(また|さらに|加えて|次に|それから)', question))
        
        return question_marks > 1 or connectives > 2 or len(question) > 3000
    
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
        
        # パターンマッチングによる分割
        current_text = question
        for pattern in self.split_patterns:
            if re.search(pattern, current_text):
                parts = re.split(pattern, current_text)
                segments.extend(self._process_split_parts(parts))
                break
        
        # パターンマッチしない場合は長さベースで分割
        if not segments:
            segments = self._split_by_length(question)
        
        # 優先度とカテゴリの設定
        segments = self._assign_priorities_and_categories(segments)
        
        logger.info(f"質問分割完了: {len(segments)}個のセグメントに分割")
        return segments
    
    def _process_split_parts(self, parts: List[str]) -> List[QuestionSegment]:
        """分割された部分を処理"""
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