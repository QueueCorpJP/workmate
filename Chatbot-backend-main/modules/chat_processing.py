"""
メインチャット処理ロジック
チャットの主要な処理フローを管理します
"""
import asyncio
from typing import Dict, Any, Optional, List
from .chat_config import (
    safe_print, HTTPException, model, get_db_cursor,
    USAGE_LIMIT_ENABLED, USAGE_LIMIT_PER_HOUR, CONTEXT_CACHING_ENABLED
)
from .chat_conversation import (
    detect_conversation_intent, generate_casual_response, 
    should_use_rag_search, extract_search_query
)
from .chat_rag import adaptive_rag_search, contextual_rag_search, format_search_results
from .chat_utils import safe_safe_print

# 使用量追跡用のグローバル変数
usage_tracker = {}

def check_usage_limit(user_id: str) -> bool:
    """
    使用量制限をチェック
    
    Args:
        user_id: ユーザーID
        
    Returns:
        制限内の場合True
    """
    if not USAGE_LIMIT_ENABLED:
        return True
    
    import time
    current_time = time.time()
    hour_ago = current_time - 3600  # 1時間前
    
    # ユーザーの使用履歴を取得
    if user_id not in usage_tracker:
        usage_tracker[user_id] = []
    
    user_usage = usage_tracker[user_id]
    
    # 1時間以内の使用回数をカウント
    recent_usage = [timestamp for timestamp in user_usage if timestamp > hour_ago]
    usage_tracker[user_id] = recent_usage  # 古い記録を削除
    
    # 制限チェック
    if len(recent_usage) >= USAGE_LIMIT_PER_HOUR:
        safe_print(f"Usage limit exceeded for user {user_id}: {len(recent_usage)}/{USAGE_LIMIT_PER_HOUR}")
        return False
    
    # 新しい使用を記録
    usage_tracker[user_id].append(current_time)
    return True

def record_usage(user_id: str, tokens_used: int = 0):
    """
    使用量を記録
    
    Args:
        user_id: ユーザーID
        tokens_used: 使用されたトークン数
    """
    try:
        cursor = get_db_cursor()
        if cursor:
            cursor.execute(
                "INSERT INTO usage_logs (user_id, tokens_used, timestamp) VALUES (%s, %s, NOW())",
                (user_id, tokens_used)
            )
            cursor.connection.commit()
    except Exception as e:
        safe_print(f"Error recording usage: {e}")

async def process_chat_message(
    message: str, 
    user_id: str = "anonymous", 
    conversation_history: List[Dict[str, str]] = None,
    use_context: bool = True
) -> Dict[str, Any]:
    """
    チャットメッセージを処理
    
    Args:
        message: ユーザーメッセージ
        user_id: ユーザーID
        conversation_history: 会話履歴
        use_context: コンテキストを使用するかどうか
        
    Returns:
        処理結果
    """
    try:
        safe_print(f"Processing chat message from user {user_id}: {message[:100]}...")
        
        # 使用量制限チェック
        if not check_usage_limit(user_id):
            raise HTTPException(
                status_code=429, 
                detail="使用量制限に達しました。1時間後に再度お試しください。"
            )
        
        # 会話意図を検出
        intent_info = detect_conversation_intent(message)
        safe_print(f"Detected intent: {intent_info}")
        
        # カジュアルな会話の場合
        if intent_info.get('is_casual', False):
            response = await generate_casual_response(message, intent_info)
            
            # 使用量を記録
            record_usage(user_id, len(response))
            
            return {
                'response': response,
                'intent': intent_info,
                'search_results': [],
                'processing_type': 'casual'
            }
        
        # RAG検索が必要な場合
        if should_use_rag_search(message, intent_info):
            # 検索クエリを抽出
            search_query = extract_search_query(message, intent_info)
            safe_print(f"Extracted search query: {search_query}")
            
            # コンテキストを構築
            context = ""
            if use_context and conversation_history:
                context_parts = []
                for entry in conversation_history[-3:]:  # 最後の3つの会話を使用
                    if entry.get('user'):
                        context_parts.append(f"ユーザー: {entry['user']}")
                    if entry.get('assistant'):
                        context_parts.append(f"アシスタント: {entry['assistant']}")
                context = "\n".join(context_parts)
            
            # RAG検索を実行
            if context:
                search_results = await contextual_rag_search(search_query, context, limit=10)
            else:
                search_results = await adaptive_rag_search(search_query, limit=10)
            
            # 検索結果をフォーマット
            formatted_results = format_search_results(search_results, max_length=2000)
            
            # Geminiで応答を生成
            response = await generate_response_with_context(
                message, formatted_results, context, intent_info
            )
            
            # 使用量を記録
            record_usage(user_id, len(response))
            
            return {
                'response': response,
                'intent': intent_info,
                'search_results': search_results,
                'processing_type': 'rag_search',
                'search_query': search_query
            }
        
        # その他の場合（基本的な応答）
        response = await generate_basic_response(message, intent_info)
        
        # 使用量を記録
        record_usage(user_id, len(response))
        
        return {
            'response': response,
            'intent': intent_info,
            'search_results': [],
            'processing_type': 'basic'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        safe_print(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"チャット処理中にエラーが発生しました: {str(e)}")

async def generate_response_with_context(
    message: str, 
    search_results: str, 
    conversation_context: str = "",
    intent_info: Dict[str, Any] = None
) -> str:
    """
    コンテキストを使用して応答を生成
    
    Args:
        message: ユーザーメッセージ
        search_results: 検索結果
        conversation_context: 会話コンテキスト
        intent_info: 意図情報
        
    Returns:
        生成された応答
    """
    try:
        if not model:
            raise Exception("Gemini model is not available")
        
        # プロンプトを構築
        prompt = build_response_prompt(message, search_results, conversation_context, intent_info)
        
        # コンテキストキャッシュを使用（有効な場合）
        if CONTEXT_CACHING_ENABLED and len(search_results) > 1000:
            safe_print("Using context caching for large search results")
            # ここでコンテキストキャッシュの実装を追加可能
        
        # 応答を生成
        response = model.generate_content(prompt)
        
        if response and response.text:
            generated_response = response.text.strip()
            safe_print(f"Generated response length: {len(generated_response)}")
            return generated_response
        else:
            raise Exception("No response generated from model")
            
    except Exception as e:
        safe_print(f"Error generating response with context: {e}")
        # フォールバック応答
        return "申し訳ございませんが、現在応答を生成できません。しばらく時間をおいて再度お試しください。"

async def generate_basic_response(message: str, intent_info: Dict[str, Any] = None) -> str:
    """
    基本的な応答を生成
    
    Args:
        message: ユーザーメッセージ
        intent_info: 意図情報
        
    Returns:
        生成された応答
    """
    try:
        if not model:
            raise Exception("Gemini model is not available")
        
        prompt = f"""
以下のメッセージに対して、親切で有用な応答を日本語で生成してください。
具体的な情報が不足している場合は、一般的なアドバイスや関連する情報を提供してください。

メッセージ: {message}

応答:"""
        
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        else:
            raise Exception("No response generated from model")
            
    except Exception as e:
        safe_print(f"Error generating basic response: {e}")
        return "ご質問ありがとうございます。より具体的な情報を教えていただけると、より詳しくお答えできます。"

def build_response_prompt(
    message: str, 
    search_results: str, 
    conversation_context: str = "",
    intent_info: Dict[str, Any] = None
) -> str:
    """
    応答生成用のプロンプトを構築
    
    Args:
        message: ユーザーメッセージ
        search_results: 検索結果
        conversation_context: 会話コンテキスト
        intent_info: 意図情報
        
    Returns:
        構築されたプロンプト
    """
    prompt_parts = []
    
    # システムプロンプト
    prompt_parts.append("""
あなたは親切で知識豊富なAIアシスタントです。
以下の検索結果を参考にして、ユーザーの質問に正確で有用な回答を日本語で提供してください。

回答の際は以下の点に注意してください：
1. 検索結果の情報を基に、正確で具体的な回答をする
2. 情報が不足している場合は、その旨を明記する
3. 関連するURLがある場合は、参考として提示する
4. 親しみやすく、理解しやすい言葉で説明する
5. 必要に応じて、手順や例を示す
""")
    
    # 会話コンテキスト
    if conversation_context:
        prompt_parts.append(f"\n【会話の流れ】\n{conversation_context}\n")
    
    # 検索結果
    if search_results:
        prompt_parts.append(f"\n【参考情報】\n{search_results}\n")
    
    # ユーザーメッセージ
    prompt_parts.append(f"\n【ユーザーの質問】\n{message}\n")
    
    # 意図に応じた指示
    if intent_info:
        intent_type = intent_info.get('intent_type', '')
        if intent_type == 'technical_question':
            prompt_parts.append("\n技術的な質問のため、具体的で実用的な回答を心がけてください。")
        elif intent_type == 'instruction_request':
            prompt_parts.append("\n手順や方法を求められているため、ステップバイステップで説明してください。")
    
    prompt_parts.append("\n【回答】")
    
    return ''.join(prompt_parts)

def get_usage_stats(user_id: str) -> Dict[str, Any]:
    """
    ユーザーの使用統計を取得
    
    Args:
        user_id: ユーザーID
        
    Returns:
        使用統計
    """
    try:
        cursor = get_db_cursor()
        if not cursor:
            return {'error': 'Database not available'}
        
        # 今日の使用量
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(tokens_used), 0)
            FROM usage_logs 
            WHERE user_id = %s AND DATE(timestamp) = CURRENT_DATE
        """, (user_id,))
        
        today_count, today_tokens = cursor.fetchone() or (0, 0)
        
        # 今月の使用量
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(tokens_used), 0)
            FROM usage_logs 
            WHERE user_id = %s AND DATE_TRUNC('month', timestamp) = DATE_TRUNC('month', CURRENT_DATE)
        """, (user_id,))
        
        month_count, month_tokens = cursor.fetchone() or (0, 0)
        
        # 現在の時間制限状況
        current_hour_usage = len(usage_tracker.get(user_id, []))
        
        return {
            'today': {
                'requests': today_count,
                'tokens': today_tokens
            },
            'month': {
                'requests': month_count,
                'tokens': month_tokens
            },
            'current_hour': {
                'requests': current_hour_usage,
                'limit': USAGE_LIMIT_PER_HOUR,
                'remaining': max(0, USAGE_LIMIT_PER_HOUR - current_hour_usage)
            }
        }
        
    except Exception as e:
        safe_print(f"Error getting usage stats: {e}")
        return {'error': str(e)}