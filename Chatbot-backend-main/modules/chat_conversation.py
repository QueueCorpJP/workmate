"""
会話検出とカジュアル応答生成
チャットの会話性を判定し、適切な応答を生成します
"""
import re
from typing import Optional, Dict, Any
from .chat_config import safe_print, model

def is_casual_conversation(message: str) -> bool:
    """
    メッセージがカジュアルな会話かどうかを判定
    
    Args:
        message: 判定するメッセージ
        
    Returns:
        カジュアルな会話の場合True
    """
    # メッセージを小文字に変換して判定
    message_lower = message.lower().strip()
    
    # 挨拶パターン
    greetings = [
        'こんにちは', 'こんばんは', 'おはよう', 'はじめまして',
        'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening'
    ]
    
    # 感謝パターン
    thanks = [
        'ありがとう', 'ありがとうございます', 'サンキュー',
        'thank you', 'thanks', 'thx'
    ]
    
    # 別れの挨拶パターン
    farewells = [
        'さようなら', 'また今度', 'バイバイ', 'お疲れ様',
        'goodbye', 'bye', 'see you', 'take care'
    ]
    
    # 簡単な質問パターン
    simple_questions = [
        '元気？', '調子はどう？', 'how are you', 'what\'s up'
    ]
    
    # 感情表現パターン
    emotions = [
        'うれしい', '嬉しい', '楽しい', '悲しい', '困った', '疲れた',
        'happy', 'sad', 'tired', 'excited', 'worried'
    ]
    
    # 短いメッセージ（10文字以下）で特定のパターンに該当する場合
    if len(message) <= 10:
        casual_short = ['はい', 'いいえ', 'そうです', 'そうですね', 'なるほど', 'ok', 'yes', 'no']
        if any(pattern in message_lower for pattern in casual_short):
            return True
    
    # 各パターンをチェック
    all_patterns = greetings + thanks + farewells + simple_questions + emotions
    
    for pattern in all_patterns:
        if pattern in message_lower:
            return True
    
    # 疑問符や感嘆符のみの短いメッセージ
    if len(message) <= 5 and ('?' in message or '？' in message or '!' in message or '！' in message):
        return True
    
    # 絵文字が含まれている場合（簡単な判定）
    emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]')
    if emoji_pattern.search(message):
        return True
    
    return False

def detect_conversation_intent(message: str) -> Dict[str, Any]:
    """
    会話の意図を検出
    
    Args:
        message: 分析するメッセージ
        
    Returns:
        意図の分析結果
    """
    message_lower = message.lower().strip()
    
    intent_result = {
        'is_casual': False,
        'intent_type': 'unknown',
        'confidence': 0.0,
        'suggested_response_type': 'search'
    }
    
    # カジュアル会話の判定
    if is_casual_conversation(message):
        intent_result['is_casual'] = True
        intent_result['suggested_response_type'] = 'casual'
        intent_result['confidence'] = 0.8
        
        # より詳細な意図分類
        if any(greeting in message_lower for greeting in ['こんにちは', 'こんばんは', 'おはよう', 'hello', 'hi']):
            intent_result['intent_type'] = 'greeting'
            intent_result['confidence'] = 0.9
        elif any(thanks in message_lower for thanks in ['ありがとう', 'thank you', 'thanks']):
            intent_result['intent_type'] = 'thanks'
            intent_result['confidence'] = 0.9
        elif any(farewell in message_lower for farewell in ['さようなら', 'バイバイ', 'goodbye', 'bye']):
            intent_result['intent_type'] = 'farewell'
            intent_result['confidence'] = 0.9
        else:
            intent_result['intent_type'] = 'casual_chat'
    
    # 質問の検出
    elif '?' in message or '？' in message:
        intent_result['intent_type'] = 'question'
        intent_result['suggested_response_type'] = 'search'
        intent_result['confidence'] = 0.7
        
        # 技術的な質問かどうか
        technical_keywords = ['API', 'SQL', 'Python', 'JavaScript', 'エラー', 'バグ', '設定', '方法']
        if any(keyword.lower() in message_lower for keyword in technical_keywords):
            intent_result['intent_type'] = 'technical_question'
            intent_result['confidence'] = 0.8
    
    # 指示・依頼の検出
    elif any(command in message_lower for command in ['教えて', '説明して', 'やり方', '方法', 'how to', 'explain']):
        intent_result['intent_type'] = 'instruction_request'
        intent_result['suggested_response_type'] = 'search'
        intent_result['confidence'] = 0.8
    
    return intent_result

async def generate_casual_response(message: str, intent_info: Dict[str, Any]) -> str:
    """
    カジュアルな応答を生成
    
    Args:
        message: 元のメッセージ
        intent_info: 意図分析結果
        
    Returns:
        生成された応答
    """
    intent_type = intent_info.get('intent_type', 'casual_chat')
    
    # 意図に応じた応答テンプレート
    response_templates = {
        'greeting': [
            'こんにちは！何かお手伝いできることはありますか？',
            'こんにちは！今日はどのようなことについて知りたいですか？',
            'こんにちは！お気軽にご質問ください。'
        ],
        'thanks': [
            'どういたしまして！他にも何かご質問があればお聞かせください。',
            'お役に立てて嬉しいです！他にもサポートが必要でしたらお知らせください。',
            'ありがとうございます！引き続きサポートさせていただきます。'
        ],
        'farewell': [
            'ありがとうございました！また何かありましたらお気軽にお声かけください。',
            'お疲れ様でした！またのご利用をお待ちしております。',
            'さようなら！また何かお手伝いできることがあればいつでもどうぞ。'
        ],
        'casual_chat': [
            'そうですね！何か具体的にお聞きしたいことはありますか？',
            'なるほど！詳しく教えていただけますか？',
            'そうですか！他にも何かご質問があればお聞かせください。'
        ]
    }
    
    # テンプレートから応答を選択
    templates = response_templates.get(intent_type, response_templates['casual_chat'])
    
    try:
        # Geminiモデルを使用してより自然な応答を生成
        if model:
            prompt = f"""
以下のメッセージに対して、親しみやすく自然な日本語で応答してください。
応答は簡潔で、相手が続けて質問しやすい雰囲気を作ってください。

メッセージ: {message}
意図: {intent_type}

応答:"""
            
            response = model.generate_content(prompt)
            generated_response = ""
            try:
                if hasattr(response, "parts") and response.parts:
                    generated_response = "".join(getattr(p, "text", "") for p in response.parts).strip()
                if not generated_response and hasattr(response, "text"):
                    generated_response = response.text.strip() if response.text else ""
                if not generated_response and hasattr(response, "candidates"):
                    for cand in response.candidates:
                        if hasattr(cand, "content") and getattr(cand.content, "parts", None):
                            generated_response = "".join(getattr(p, "text", "") for p in cand.content.parts).strip()
                            if generated_response:
                                break
            except Exception as e:
                safe_print(f"❌ parts抽出失敗: {e}")

            if generated_response:
                safe_print(f"Generated casual response: {generated_response}")
                return generated_response
    
    except Exception as e:
        safe_print(f"Error generating casual response with model: {e}")
    
    # フォールバック: テンプレートから選択
    import random
    selected_response = random.choice(templates)
    safe_print(f"Using template response: {selected_response}")
    return selected_response

def should_use_rag_search(message: str, intent_info: Dict[str, Any]) -> bool:
    """
    RAG検索を使用すべきかどうかを判定
    
    Args:
        message: メッセージ
        intent_info: 意図分析結果
        
    Returns:
        RAG検索を使用すべき場合True
    """
    # カジュアルな会話の場合は基本的にRAG検索不要
    if intent_info.get('is_casual', False):
        return False
    
    # 技術的な質問や指示・依頼の場合はRAG検索を使用
    if intent_info.get('intent_type') in ['technical_question', 'instruction_request', 'question']:
        return True
    
    # メッセージが長い場合（具体的な質問の可能性）
    if len(message) > 20:
        return True
    
    # 特定のキーワードが含まれている場合
    search_keywords = [
        '方法', 'やり方', '手順', '設定', '使い方', '問題', 'エラー', 'バグ',
        'API', 'SQL', 'Python', 'JavaScript', 'HTML', 'CSS',
        'how', 'what', 'why', 'when', 'where', 'which'
    ]
    
    message_lower = message.lower()
    if any(keyword.lower() in message_lower for keyword in search_keywords):
        return True
    
    return False

def extract_search_query(message: str, intent_info: Dict[str, Any]) -> str:
    """
    メッセージから検索クエリを抽出
    
    Args:
        message: 元のメッセージ
        intent_info: 意図分析結果
        
    Returns:
        抽出された検索クエリ
    """
    # 基本的にはメッセージをそのまま使用
    query = message.strip()
    
    # 不要な部分を除去
    remove_patterns = [
        r'^(教えて|説明して|知りたい|聞きたい)[：:：\s]*',
        r'(お願いします|ください|だろうか|でしょうか)[。．\s]*$',
        r'^(すみません|恐れ入ります)[、，\s]*',
    ]
    
    for pattern in remove_patterns:
        query = re.sub(pattern, '', query, flags=re.IGNORECASE)
    
    # 疑問符を除去
    query = query.replace('？', '').replace('?', '').strip()
    
    return query if query else message