"""
メインチャット処理ロジック
チャットの主要な処理フローを管理します
"""
import asyncio
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime
from supabase_adapter import select_data, insert_data
from .chat_config import (
    safe_print, HTTPException, model, get_db_cursor,
    USAGE_LIMIT_ENABLED, USAGE_LIMIT_PER_HOUR, CONTEXT_CACHING_ENABLED
)
from .chat_conversation import (
    detect_conversation_intent, generate_casual_response, 
    should_use_rag_search, extract_search_query
)
from .chat_rag import adaptive_rag_search, contextual_rag_search, format_search_results
from .comprehensive_search_system import comprehensive_search, initialize_comprehensive_search
from .chat_rag_enhanced import enhanced_rag_search, enhanced_format_search_results
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

async def save_chat_history(
    user_id: str,
    user_message: str,
    bot_response: str,
    company_id: Optional[str] = None,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    source_document: Optional[str] = None,
    source_page: Optional[str] = None,
    model_name: str = 'gemini-2.5-flash',
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float = 0.0,
    employee_id: Optional[str] = None,
    employee_name: Optional[str] = None,
) -> None:
    """
    チャット履歴をSupabaseの chat_history テーブルに保存する
    """
    try:
        safe_print(f"[DB SAVE] save_chat_history called for user {user_id}. Message: {user_message[:50]}...")
        
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # company_id が提供されていない場合、user_id から取得を試みる
        if company_id is None and user_id != "anonymous":
            safe_print(f"[DB SAVE] Attempting to get company_id for user {user_id}")
            user_data_result = select_data("users", filters={"id": user_id}, columns="company_id")
            if user_data_result and user_data_result.data:
                company_id = user_data_result.data[0].get("company_id")
                safe_print(f"[DB SAVE] Found company_id: {company_id} for user {user_id}")
            else:
                safe_print(f"[DB SAVE] No company_id found for user {user_id}")

        # 会社別料金体系に基づいて正確なコストを計算
        if company_id and user_message and bot_response:
            try:
                from modules.token_counter import TokenCounter
                counter = TokenCounter()
                
                # 会社別料金計算（RAG処理の場合はプロンプト参照1回をカウント）
                prompt_refs = 1 if use_context and search_results else 0
                cost_result = counter.calculate_cost_by_company(
                    user_message, bot_response, company_id, prompt_refs
                )
                
                # 計算結果でパラメータを上書き
                input_tokens = cost_result["input_tokens"]
                output_tokens = cost_result["output_tokens"]
                cost_usd = cost_result["total_cost_usd"]
                
                safe_print(f"[DB SAVE] Company-specific cost calculated: ${cost_usd:.6f} for company {company_id}")
                
            except Exception as calc_error:
                safe_print(f"[DB SAVE] Error calculating company-specific cost: {calc_error}")
                # エラーの場合は元の値を使用

        # employee_id が明示的に渡されていない場合は user_id を利用する
        effective_employee_id = employee_id or user_id

        data = {
            "id": chat_id,
            "user_message": user_message,
            "bot_response": bot_response,
            "timestamp": timestamp,
            "category": category,
            "sentiment": sentiment,
            "employee_id": effective_employee_id,
            "employee_name": employee_name,
            "user_id": user_id,
            "company_id": company_id,
            "source_document": source_document,
            "source_page": source_page,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "model_name": model_name,
            "cost_usd": cost_usd,
        }

        result = insert_data("chat_history", data)
        if result.success:
            safe_print(f"[DB SAVE] Chat history successfully saved to Supabase for user {user_id} with id {chat_id}")
        else:
            safe_print(f"[DB SAVE] Failed to save chat history to Supabase: {result.error}")
    except Exception as e:
        safe_print(f"[DB SAVE] Unexpected error saving chat history: {e}")
        import traceback
        safe_print(traceback.format_exc())

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
            
            # チャット履歴を保存（トークン数・コスト計算含む）
            safe_print(f"[PROCESS] Saving casual chat history for user {user_id}")
            
            # company_idを取得
            company_id = None
            if user_id != "anonymous":
                user_data_result = select_data("users", filters={"id": user_id}, columns="company_id")
                if user_data_result and user_data_result.data:
                    company_id = user_data_result.data[0].get("company_id")
            
            # トークン・コスト計算（基本応答の場合はプロンプト参照なし）
            from modules.token_counter import TokenCounter
            counter = TokenCounter()
            cost_result = counter.calculate_cost_by_company(message, response, company_id, 0)
            
            await save_chat_history(user_id, message, response, 
                                  category=intent_info.get('category'),
                                  company_id=company_id,
                                  input_tokens=cost_result.get("input_tokens", 0),
                                  output_tokens=cost_result.get("output_tokens", 0),
                                  cost_usd=cost_result.get("total_cost_usd", 0.0))
            
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
            
            # RAG検索を実行（拡張RAGシステムを使用）
            try:
                # 拡張RAGシステムを最優先で実行（PDF後半情報、動的LIMIT、文書多様性）
                search_results = await enhanced_rag_search(
                    query=search_query,
                    context=context,
                    company_id=None,  # 後で会社IDフィルタを追加可能
                    adaptive_limits=True  # クエリ複雑さに応じた動的LIMIT調整
                )
                
                if search_results:
                    safe_print(f"拡張RAG検索成功: {len(search_results)}件の高品質結果を取得")
                else:
                    # フォールバック1: 包括的検索システム
                    safe_print("拡張RAG検索で結果なし、包括的検索を試行")
                    search_results = await comprehensive_search(
                        search_query, 
                        company_id=None,
                        initial_limit=40,
                        final_limit=12
                    )
                    
                    if not search_results:
                        # フォールバック2: 従来の検索システム
                        safe_print("包括的検索でも結果なし、従来検索を実行")
                        if context:
                            search_results = await contextual_rag_search(search_query, context, limit=12)
                        else:
                            search_results = await adaptive_rag_search(search_query, limit=12)
                        
            except Exception as e:
                safe_print(f"拡張RAG検索エラー: {e}、フォールバック検索を実行")
                # フォールバック: 従来の検索システム
                if context:
                    search_results = await contextual_rag_search(search_query, context, limit=12)
                else:
                    search_results = await adaptive_rag_search(search_query, limit=12)
            
            # 検索結果をフォーマット（拡張版を使用）
            try:
                formatted_results = enhanced_format_search_results(search_results, max_length=3000)
            except Exception as e:
                safe_print(f"拡張フォーマットエラー: {e}、標準フォーマットを使用")
                formatted_results = format_search_results(search_results, max_length=2000)
            
            # Geminiで応答を生成
            response = await generate_response_with_context(
                message, formatted_results, context, intent_info
            )
            
            # 使用量を記録
            record_usage(user_id, len(response))
            
            # チャット履歴を保存
            source_document = None
            source_page = None
            if search_results and isinstance(search_results, list) and len(search_results) > 0:
                first_result = search_results[0]
                if 'metadata' in first_result:
                    source_document = first_result['metadata'].get('source_document')
                    source_page = first_result['metadata'].get('source_page')

            safe_print(f"[PROCESS] Saving RAG chat history for user {user_id}. Source: {source_document}, Page: {source_page}")
            
            # company_idを取得
            company_id = None
            if user_id != "anonymous":
                user_data_result = select_data("users", filters={"id": user_id}, columns="company_id")
                if user_data_result and user_data_result.data:
                    company_id = user_data_result.data[0].get("company_id")
            
            # トークン・コスト計算（RAG検索を使用した場合はプロンプト参照1回）
            from modules.token_counter import TokenCounter
            counter = TokenCounter()
            prompt_refs = 1  # RAG検索を使用したのでプロンプト参照1回
            cost_result = counter.calculate_cost_by_company(message, response, company_id, prompt_refs)
            
            await save_chat_history(
                user_id, message, response,
                category=intent_info.get('category'),
                source_document=source_document,
                source_page=source_page,
                company_id=company_id,
                input_tokens=cost_result.get("input_tokens", 0),
                output_tokens=cost_result.get("output_tokens", 0),
                cost_usd=cost_result.get("total_cost_usd", 0.0)
            )
            
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
        
        # チャット履歴を保存
        safe_print(f"[PROCESS] Saving basic chat history for user {user_id}")
        
        # company_idを取得
        company_id = None
        if user_id != "anonymous":
            user_data_result = select_data("users", filters={"id": user_id}, columns="company_id")
            if user_data_result and user_data_result.data:
                company_id = user_data_result.data[0].get("company_id")
        
        # トークン・コスト計算（RAG処理の場合はプロンプト参照1回をカウント）
        from modules.token_counter import TokenCounter
        counter = TokenCounter()
        prompt_refs = 1  # RAG検索を使用したのでプロンプト参照1回
        cost_result = counter.calculate_cost_by_company(message, response, company_id, prompt_refs)
        
        await save_chat_history(user_id, message, response, 
                              category=intent_info.get('category'),
                              company_id=company_id,
                              input_tokens=cost_result.get("input_tokens", 0),
                              output_tokens=cost_result.get("output_tokens", 0),
                              cost_usd=cost_result.get("total_cost_usd", 0.0))
        
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
    intent_info: Dict[str, Any] = None,
    company_id: str = None
) -> str:
    """
    応答生成用のプロンプトを構築
    
    Args:
        message: ユーザーメッセージ
        search_results: 検索結果
        conversation_context: 会話コンテキスト
        intent_info: 意図情報
        company_id: 会社ID（特別指示取得用）
        
    Returns:
        構築されたプロンプト
    """
    prompt_parts = []
    
    # 🎯 特別指示をプロンプトの一番前に配置
    special_instructions_text = ""
    if company_id:
        try:
            # アクティブなリソースの特別指示を取得
            special_result = select_data(
                "document_sources", 
                columns="name,special", 
                filters={
                    "company_id": company_id,
                    "active": True
                }
            )
            
            if special_result.data:
                special_instructions = []
                for i, resource in enumerate(special_result.data, 1):
                    special_instruction = resource.get('special')
                    if special_instruction and special_instruction.strip():
                        resource_name = resource.get('name', 'Unknown')
                        special_instructions.append(f"{i}. 【{resource_name}】: {special_instruction.strip()}")
                
                if special_instructions:
                    special_instructions_text = "特別な回答指示（以下のリソースを参照する際は、各リソースの指示に従ってください）：\n" + "\n".join(special_instructions) + "\n\n"
                    
        except Exception as e:
            safe_print(f"⚠️ 特別指示取得エラー: {e}")
    
    # 特別指示 + システムプロンプト（修正版）
    prompt_parts.append(f"""{special_instructions_text}あなたは親切で知識豊富なAIアシスタントです。
以下の検索結果を参考にして、ユーザーの質問に有用な回答を日本語で提供してください。

回答の際は以下の点に注意してください：
1. 検索結果に関連する情報が含まれている場合は、それを活用して回答する
2. 検索結果の情報から推測できることや、関連する内容があれば積極的に提供する
3. 完全に一致する情報がなくても、部分的に関連する情報があれば有効活用する
4. 親しみやすく、理解しやすい言葉で説明する
5. 必要に応じて、手順や例を示す
6. 関連するURLがある場合は、参考として提示する
7. 全く関連性がない場合のみ、その旨を丁寧に説明する
8. 情報の出典として「ファイル名」や「資料名」は明示可能ですが、技術的な内部構造情報（行番号、分割番号、データベースIDなど）は出力しない
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