"""
チャットモジュール
チャット機能とAI応答生成を管理します
"""
import json
import re
import uuid
import sys
from datetime import datetime
import logging
# PostgreSQL関連のインポート
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException, Depends
from .company import DEFAULT_COMPANY_NAME
from .models import ChatMessage, ChatResponse
from .database import get_db, update_usage_count, get_usage_limits
from .knowledge_base import knowledge_base, get_active_resources
from .auth import check_usage_limits
from .resource import get_active_resources_by_company_id, get_active_resources_content_by_ids, get_active_resource_names_by_company_id
from .company import get_company_by_id
import os
import asyncio
import google.generativeai as genai
from .config import setup_gemini
from .utils import safe_print, safe_safe_print

logger = logging.getLogger(__name__)

def safe_print(text):
    """Windows環境でのUnicode文字エンコーディング問題を回避する安全なprint関数"""
    try:
        print(text)
    except UnicodeEncodeError:
        # エンコーディングエラーが発生した場合は、問題のある文字を置換
        try:
            safe_text = str(text).encode('utf-8', errors='replace').decode('utf-8')
            print(safe_text)
        except:
            # それでも失敗する場合はエラーメッセージのみ出力
            print("[出力エラー: Unicode文字を含むメッセージ]")

def safe_safe_print(text):
    """Windows環境でのUnicode文字エンコーディング問題を回避する安全なsafe_print関数"""
    safe_print(text)

def simple_rag_search(knowledge_text: str, query: str, max_results: int = 5) -> str:
    """
    超簡単RAG風検索 - BM25Sを使って関連部分だけを抽出
    """
    if not knowledge_text or not query:
        return knowledge_text
    
    try:
        import bm25s
        import re
        
        # テキストを段落に分割
        paragraphs = re.split(r'\n\s*\n', knowledge_text)
        paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 50]
        
        if len(paragraphs) < 2:
            return knowledge_text[:100000]  # 段落が少ない場合はそのまま
        
        # BM25S検索エンジンを作成
        corpus_tokens = bm25s.tokenize(paragraphs)
        retriever = bm25s.BM25()
        retriever.index(corpus_tokens)
        
        # 質問をトークン化して検索
        query_tokens = bm25s.tokenize([query])
        results, scores = retriever.retrieve(query_tokens, k=min(max_results, len(paragraphs)))
        
        # 関連する段落を取得
        relevant_paragraphs = []
        for i in range(results.shape[1]):
            if i < len(paragraphs):
                paragraph_idx = results[0, i]
                if paragraph_idx < len(paragraphs):
                    relevant_paragraphs.append(paragraphs[paragraph_idx])
        
        result = '\n\n'.join(relevant_paragraphs)
        safe_print(f"🎯 RAG検索完了: {len(relevant_paragraphs)}個の関連段落、{len(result)}文字 (元: {len(knowledge_text)}文字)")
        return result
        
    except Exception as e:
        safe_print(f"RAG検索エラー: {str(e)}")
        # エラーの場合は最初の部分を返す
        return knowledge_text[:100000]

# Geminiモデル（グローバル変数）
model = None

def set_model(gemini_model):
    """Geminiモデルを設定する"""
    global model
    model = gemini_model

def is_casual_conversation(message_text: str) -> bool:
    """メッセージが挨拶や一般的な会話かどうかを判定する"""
    if not message_text:
        return False
    
    message_lower = message_text.strip().lower()
    
    # 挨拶パターン
    greetings = [
        "こんにちは", "こんにちわ", "おはよう", "おはようございます", "こんばんは", "こんばんわ",
        "よろしく", "よろしくお願いします", "はじめまして", "初めまして",
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening"
    ]
    
    # お礼パターン
    thanks = [
        "ありがとう", "ありがとうございます", "ありがとうございました", "感謝します",
        "thank you", "thanks", "thx"
    ]
    
    # 別れの挨拶パターン
    farewells = [
        "さようなら", "またね", "また明日", "失礼します", "お疲れ様", "お疲れさまでした",
        "bye", "goodbye", "see you", "good bye"
    ]
    
    # 一般的な会話パターン
    casual_phrases = [
        "元気", "調子", "どう", "天気", "今日", "明日", "昨日", "週末", "休み",
        "疲れた", "忙しい", "暇", "時間", "いい天気", "寒い", "暑い", "雨",
        "how are you", "what's up", "how's it going", "nice weather", "tired", "busy"
    ]
    
    # 短い質問や相槌パターン
    short_responses = [
        "はい", "いいえ", "そうですね", "なるほど", "そうですか", "わかりました",
        "ok", "okay", "yes", "no", "i see", "alright"
    ]
    
    # メッセージが短すぎる場合（3文字以下）は一般的な会話として扱う
    if len(message_lower) <= 3:
        return True
    
    # 各パターンをチェック
    all_patterns = greetings + thanks + farewells + casual_phrases + short_responses
    
    for pattern in all_patterns:
        if pattern in message_lower:
            return True
    
    # 疑問符がなく、短いメッセージ（20文字以下）は一般的な会話として扱う
    if len(message_text) <= 20 and "?" not in message_text and "？" not in message_text:
        return True
    
    return False

async def generate_casual_response(message_text: str, company_name: str) -> str:
    """挨拶や一般的な会話に対する自然な返答を生成する"""
    try:
        if model is None:
            return "こんにちは！何かお手伝いできることはありますか？"
        
        # 挨拶や一般的な会話専用のプロンプト
        casual_prompt = f"""
あなたは{company_name}の親しみやすいアシスタントです。
ユーザーからの挨拶や一般的な会話に対して、自然で親しみやすい返答をしてください。

返答の際の注意点：
1. 親しみやすく、温かい口調で返答してください
2. 会話を続けたい場合は、適切な質問で返してください
3. 長すぎず、短すぎない適度な長さで返答してください
4. 必要に応じて、お手伝いできることがあることを伝えてください
5. 知識ベースの情報は参照せず、一般的な会話として返答してください

ユーザーのメッセージ: {message_text}
"""
        
        response = model.generate_content(casual_prompt)
        
        if response and hasattr(response, 'text') and response.text:
            return response.text.strip()
        else:
            # フォールバック応答
            message_lower = message_text.lower()
            if any(greeting in message_lower for greeting in ["こんにちは", "こんにちわ", "hello", "hi"]):
                return "こんにちは！お疲れ様です。何かお手伝いできることはありますか？"
            elif any(thanks in message_lower for thanks in ["ありがとう", "thank you", "thanks"]):
                return "どういたしまして！他にも何かお手伝いできることがあれば、お気軽にお声がけください。"
            elif any(farewell in message_lower for farewell in ["さようなら", "またね", "bye", "goodbye"]):
                return "お疲れ様でした！また何かありましたら、いつでもお声がけください。"
            else:
                return "そうですね！何かお手伝いできることがあれば、お気軽にお声がけください。"
                
    except Exception as e:
        safe_print(f"一般会話応答生成エラー: {str(e)}")
        return "こんにちは！何かお手伝いできることはありますか？"

async def process_chat(message: ChatMessage, db = Depends(get_db), current_user: dict = None):
    """チャットメッセージを処理してGeminiからの応答を返す"""
    try:
        # モデルが設定されているか確認
        if model is None:
            safe_print("❌ モデルが初期化されていません")
            raise HTTPException(status_code=500, detail="AIモデルが初期化されていません")
        
        safe_print(f"✅ モデル初期化確認: {model}")
        safe_print(f"📊 モデルタイプ: {type(model)}")
        
        # メッセージがNoneでないことを確認
        if not message or not hasattr(message, 'text') or message.text is None:
            raise HTTPException(status_code=400, detail="メッセージテキストが提供されていません")
        
        # メッセージテキストを安全に取得
        message_text = message.text if message.text is not None else ""
        
        # 最新の会社名を取得（モジュールからの直接インポートではなく、関数内で再取得）
        from .company import DEFAULT_COMPANY_NAME as current_company_name
        
        # 挨拶や一般的な会話かどうかを判定
        if is_casual_conversation(message_text):
            safe_print(f"🗣️ 一般的な会話として判定: {message_text}")
            
            # 一般的な会話の場合はナレッジを参照せずに返答
            casual_response = await generate_casual_response(message_text, current_company_name)
            
            # チャット履歴を保存（一般会話として）
            from modules.token_counter import TokenUsageTracker
            
            # ユーザーの会社IDを取得（チャット履歴保存用）
            company_id = None
            if message.user_id:
                try:
                    from supabase_adapter import select_data
                    user_result = select_data("users", columns="company_id", filters={"id": message.user_id})
                    if user_result.data and len(user_result.data) > 0:
                        user_data = user_result.data[0]
                        company_id = user_data.get('company_id')
                except Exception as e:
                    safe_print(f"会社ID取得エラー（一般会話）: {str(e)}")
            
            # トークン追跡機能を使用してチャット履歴を保存（ナレッジ参照なし）
            tracker = TokenUsageTracker(db)
            chat_id = tracker.save_chat_with_prompts(
                user_message=message_text,
                bot_response=casual_response,
                user_id=message.user_id,
                prompt_references=0,  # ナレッジ参照なし
                company_id=company_id,
                employee_id=getattr(message, 'employee_id', None),
                employee_name=getattr(message, 'employee_name', None),
                category="一般会話",
                sentiment="neutral",
                model="gemini-pro"
            )
            
            # 利用制限の処理（一般会話でも質問回数にカウント）
            remaining_questions = None
            limit_reached = False
            
            if message.user_id:
                # 質問の利用制限をチェック
                limits_check = check_usage_limits(message.user_id, "question", db)
                
                if not limits_check["is_unlimited"] and not limits_check["allowed"]:
                    response_text = f"申し訳ございません。デモ版の質問回数制限（{limits_check['limit']}回）に達しました。"
                    return {
                        "response": response_text,
                        "remaining_questions": 0,
                        "limit_reached": True
                    }
                
                # 質問カウントを更新
                if not limits_check.get("is_unlimited", False):
                    updated_limits = update_usage_count(message.user_id, "questions_used", db)
                    if updated_limits:
                        remaining_questions = updated_limits["questions_limit"] - updated_limits["questions_used"]
                        limit_reached = remaining_questions <= 0
                    else:
                        remaining_questions = limits_check["remaining"] - 1 if limits_check["remaining"] > 0 else 0
                        limit_reached = remaining_questions <= 0
            
            safe_print(f"✅ 一般会話応答完了: {len(casual_response)} 文字")
            
            return {
                "response": casual_response,
                "source": "",  # ナレッジ参照なし
                "remaining_questions": remaining_questions,
                "limit_reached": limit_reached
            }
        
        # ユーザーIDがある場合は利用制限をチェック
        remaining_questions = None
        limit_reached = False
        
        if message.user_id:
            # 質問の利用制限をチェック
            limits_check = check_usage_limits(message.user_id, "question", db)
            
            if not limits_check["is_unlimited"] and not limits_check["allowed"]:
                response_text = f"申し訳ございません。デモ版の質問回数制限（{limits_check['limit']}回）に達しました。"
                return {
                    "response": response_text,
                    "remaining_questions": 0,
                    "limit_reached": True
                }
            
            # 無制限でない場合は残り回数を計算
            if not limits_check["is_unlimited"]:
                remaining_questions = limits_check["remaining"]

        # ユーザーの会社IDを取得
        company_id = None
        if message.user_id:
            try:
                from supabase_adapter import select_data
                user_result = select_data("users", columns="company_id", filters={"id": message.user_id})
                if user_result.data and len(user_result.data) > 0:
                    user_data = user_result.data[0]
                    if user_data.get('company_id'):
                        company_id = user_data['company_id']
                        safe_print(f"ユーザーID {message.user_id} の会社ID: {company_id}")
                    else:
                        safe_print(f"ユーザーID {message.user_id} に会社IDが設定されていません")
                else:
                    safe_print(f"ユーザーID {message.user_id} が見つかりません")
            except Exception as e:
                safe_print(f"会社ID取得エラー: {str(e)}")
                # エラー時はcompany_id = Noneのまま継続
        
        # 会社固有のアクティブなリソースを取得
        # 管理者の場合は自分がアップロードしたリソースのみ取得
        uploaded_by = None
        if current_user and current_user.get("role") == "admin":
            uploaded_by = current_user["id"]
            safe_print(f"管理者ユーザー: {current_user.get('email')} - 自分のリソースのみ参照")
        
        active_sources = await get_active_resources_by_company_id(company_id, db, uploaded_by)
        safe_print(f"アクティブなリソース (会社ID: {company_id}): {', '.join(active_sources)}")
        
        # アクティブなリソースがない場合はエラーメッセージを返す
        if not active_sources:
            response_text = f"申し訳ございません。現在、アクティブな知識ベースがありません。管理画面でリソースを有効にしてください。"
            
            # チャット履歴を保存
            chat_id = str(uuid.uuid4())
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO chat_history (id, user_message, bot_response, timestamp, category, sentiment, employee_id, employee_name, user_id, company_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (chat_id, message_text, response_text, datetime.now().isoformat(), "設定エラー", "neutral", message.employee_id, message.employee_name, message.user_id, company_id)
            )
            db.commit()
            
            # ユーザーIDがある場合は質問カウントを更新（アクティブなリソースがなくても利用制限は更新する）
            if message.user_id and not limits_check.get("is_unlimited", False):
                safe_print(f"利用制限更新開始（アクティブリソースなし） - ユーザーID: {message.user_id}")
                safe_print(f"更新前の制限情報: {limits_check}")
                
                updated_limits = update_usage_count(message.user_id, "questions_used", db)
                safe_print(f"更新後の制限情報: {updated_limits}")
                
                if updated_limits:
                    remaining_questions = updated_limits["questions_limit"] - updated_limits["questions_used"]
                    limit_reached = remaining_questions <= 0
                    safe_print(f"計算された残り質問数: {remaining_questions}, 制限到達: {limit_reached}")
                else:
                    safe_print("利用制限の更新に失敗しました")
            
            safe_print(f"返り値（アクティブリソースなし）: remaining_questions={remaining_questions}, limit_reached={limit_reached}")
            
            return {
                "response": response_text,
                "remaining_questions": remaining_questions,
                "limit_reached": limit_reached
            }
        
        # pandas をインポート
        import pandas as pd
        import traceback
        
        # 選択されたリソースを使用して知識ベースを作成
        # source_info = {}  # ソース情報を保存する辞書
        active_resource_names = await get_active_resource_names_by_company_id(company_id, db)
        source_info_list = [
            {
                "name": res_name,
                "section": "",  # or default
                "page": ""
            }
            for res_name in active_resource_names
        ]
        
        # アクティブなリソースのSpecial指示を取得
        special_instructions = []
        try:
            from supabase_adapter import select_data
            for source_id in active_sources:
                source_result = select_data("document_sources", columns="name,special", filters={"id": source_id})
                if source_result.data and len(source_result.data) > 0:
                    source_data = source_result.data[0]
                    if source_data.get('special') and source_data['special'].strip():
                        special_instructions.append({
                            "name": source_data.get('name', 'Unknown'),
                            "instruction": source_data['special'].strip()
                        })
            safe_print(f"Special指示: {len(special_instructions)}個のリソースにSpecial指示があります")
        except Exception as e:
            safe_print(f"Special指示取得エラー: {str(e)}")
            special_instructions = []
        
        # safe_print(f"知識ベースの生データ長: {len(knowledge_base.raw_text) if knowledge_base.raw_text else 0}")
        safe_print(f"アクティブなソース: {active_sources}")
        active_knowledge_text = await get_active_resources_content_by_ids(active_sources, db)
        
        # RAG風検索で関連部分のみを抽出（超高速化）
        if active_knowledge_text and len(active_knowledge_text) > 50000:
            active_knowledge_text = simple_rag_search(active_knowledge_text, message_text, max_results=8)
        
        # 知識ベースのサイズを制限（API制限対応のため一時的に復活）
        MAX_KNOWLEDGE_SIZE = 300000  # 30万文字制限（API制限対応）
        if active_knowledge_text and len(active_knowledge_text) > MAX_KNOWLEDGE_SIZE:
            safe_print(f"⚠️ 知識ベースが大きすぎます ({len(active_knowledge_text)} 文字)。{MAX_KNOWLEDGE_SIZE} 文字に制限します。")
            active_knowledge_text = active_knowledge_text[:MAX_KNOWLEDGE_SIZE] + "\n\n[注意: 知識ベースが大きいため、一部のみ表示しています]"
        # アクティブな知識ベースが空の場合はエラーメッセージを返す
        if not active_knowledge_text or (isinstance(active_knowledge_text, str) and not active_knowledge_text.strip()):
            response_text = f"申し訳ございません。アクティブな知識ベースの内容が空です。管理画面で別のリソースを有効にしてください。"
            
            # トークン使用量を計算してチャット履歴を保存（エラーケース）
            from modules.token_counter import TokenUsageTracker
            
            # ユーザーの会社IDを取得（チャット履歴保存用） 
            from supabase_adapter import select_data
            user_result = select_data("users", filters={"id": message.user_id}) if hasattr(message, 'user_id') and message.user_id else None
            chat_company_id = user_result.data[0].get("company_id") if user_result and user_result.data else None
            
            # プロンプト参照数を計算（アクティブリソース数）
            error_prompt_references = len(active_sources) if active_sources else 0
            
            # トークン追跡機能を使用してチャット履歴を保存（新料金体系を使用）
            tracker = TokenUsageTracker(db)
            chat_id = tracker.save_chat_with_prompts(
                user_message=message_text,
                bot_response=response_text,
                user_id=message.user_id,
                prompt_references=error_prompt_references,
                company_id=chat_company_id,
                employee_id=getattr(message, 'employee_id', None),
                employee_name=getattr(message, 'employee_name', None),
                category="設定エラー",
                sentiment="neutral",
                model="gemini-pro"
            )
            
            # ユーザーIDがある場合は質問カウントを更新（知識ベースが空でも利用制限は更新する）
            if message.user_id and not limits_check.get("is_unlimited", False):
                safe_print(f"利用制限更新開始（知識ベース空） - ユーザーID: {message.user_id}")
                safe_print(f"更新前の制限情報: {limits_check}")
                
                updated_limits = update_usage_count(message.user_id, "questions_used", db)
                safe_print(f"更新後の制限情報: {updated_limits}")
                
                if updated_limits:
                    remaining_questions = updated_limits["questions_limit"] - updated_limits["questions_used"]
                    limit_reached = remaining_questions <= 0
                    safe_print(f"計算された残り質問数: {remaining_questions}, 制限到達: {limit_reached}")
                else:
                    safe_print("利用制限の更新に失敗しました")
            
            safe_print(f"返り値（知識ベース空）: remaining_questions={remaining_questions}, limit_reached={limit_reached}")
            
            return {
                "response": response_text,
                "remaining_questions": remaining_questions,
                "limit_reached": limit_reached
            }
            
        # 直近のメッセージを取得（最大3件に制限）
        recent_messages = []
        try:
            if message.user_id:
                with db.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        """
                        SELECT user_message, bot_response
                        FROM chat_history
                        WHERE employee_id = %s
                        ORDER BY timestamp DESC
                        LIMIT 2
                        """,
                        (message.user_id,)
                    )
                    cursor_result = cursor.fetchall()
                    # PostgreSQLの結果をリストに変換してから古い順に並べ替え
                    recent_messages = list(cursor_result)
                    recent_messages.reverse()
        except Exception as e:
            safe_print(f"会話履歴取得エラー: {str(e)}")
            recent_messages = []
        
        # 会話履歴の構築（各メッセージを制限）
        conversation_history = ""
        if recent_messages:
            conversation_history = "直近の会話履歴：\n"
            for idx, msg in enumerate(recent_messages):
                
                try:
                    user_msg = msg.get('user_message', '') or ''
                    bot_msg = msg.get('bot_response', '') or ''
                    
                    # 各メッセージを100文字に制限（トークン削減のため）
                    if len(user_msg) > 100:
                        user_msg = user_msg[:100] + "..."
                    if len(bot_msg) > 100:
                        bot_msg = bot_msg[:100] + "..."
                    
                    conversation_history += f"ユーザー: {user_msg}\n"
                    conversation_history += f"アシスタント: {bot_msg}\n\n"
                except Exception as e:
                    # Windows環境でのUnicode文字エンコーディング問題を避けるため、safe_safe_print関数を使用
                    safe_safe_print(f"会話履歴処理エラー: {str(e)}")
                    # エラーが発生した場合はその行をスキップ
                    continue

        # Special指示をプロンプトに追加するための文字列を構築
        special_instructions_text = ""
        if special_instructions:
            special_instructions_text = "\n\n特別な回答指示（以下のリソースを参照する際は、各リソースの指示に従ってください）：\n"
            for idx, inst in enumerate(special_instructions, 1):
                special_instructions_text += f"{idx}. 【{inst['name']}】: {inst['instruction']}\n"

        # プロンプトの作成
        prompt = f"""
        あなたは親切で丁寧な対応ができる{current_company_name}のアシスタントです。
        以下の知識ベースを参考に、ユーザーの質問に対して可能な限り具体的で役立つ回答を提供してください。

        利用可能なファイル: {', '.join(active_resource_names) if active_resource_names else 'なし'}

        回答の際の注意点：
        1. 常に丁寧な言葉遣いを心がけ、ユーザーに対して敬意を持って接してください
        2. 知識ベースに情報がない場合でも、一般的な文脈で回答できる場合は適切に対応してください
        3. ユーザーが「もっと詳しく」などと質問した場合は、前回の回答内容に関連する詳細情報を提供してください。「どのような情報について詳しく知りたいですか？」などと聞き返さないでください。
        4. 可能な限り具体的で実用的な情報を提供してください
        5. 知識ベースにOCRで抽出されたテキスト（PDF (OCR)と表示されている部分）が含まれている場合は、それが画像から抽出されたテキストであることを考慮してください
        6. OCRで抽出されたテキストには多少の誤りがある可能性がありますが、文脈から適切に解釈して回答してください
        7. 知識ベースの情報を使用して回答した場合は、回答の最後に「情報ソース: [ファイル名]」の形式で参照したファイル名を記載してください。
        8. 「こんにちは」「おはよう」などの単純な挨拶のみの場合は、情報ソースを記載しないでください。それ以外の質問には基本的に情報ソースを記載してください。
        9. 回答可能かどうかが判断できる質問に対しては、最初に「はい」または「いいえ」で簡潔に答えてから、具体的な説明や補足情報を記載してください
        10. 回答は**Markdown記法**を使用して見やすく整理してください。見出し（#、##、###）、箇条書き（-、*）、番号付きリスト（1.、2.）、強調（**太字**、*斜体*）、コードブロック（```）、表（|）、引用（>）などを適切に使用してください
        11. 手順や説明が複数ある場合は、番号付きリストや箇条書きを使用して構造化してください
        12. 重要な情報は**太字**で強調してください
        13. コードやファイル名、設定値などは`バッククォート`で囲んでください{special_instructions_text}
        
        利用可能なデータ列：
        {', '.join(knowledge_base.columns) if knowledge_base and hasattr(knowledge_base, 'columns') and knowledge_base.columns else "データ列なし"}

        知識ベース内容（アクティブなリソースのみ）：
        {active_knowledge_text}

        {f"画像情報：PDFから抽出された画像が{len(knowledge_base.images)}枚あります。" if knowledge_base and hasattr(knowledge_base, 'images') and knowledge_base.images and isinstance(knowledge_base.images, list) else ""}

        {conversation_history}

        ユーザーの質問：
        {message_text}
        """

        # プロンプトサイズの最終チェック（トークン制限対応）
        MAX_PROMPT_SIZE = 400000  # 40万文字制限（API制限対応）
        if len(prompt) > MAX_PROMPT_SIZE:
            safe_print(f"⚠️ プロンプトが大きすぎます ({len(prompt)} 文字)。知識ベースをさらに制限します。")
            # 知識ベースをさらに制限
            reduced_knowledge_size = MAX_PROMPT_SIZE - (len(prompt) - len(active_knowledge_text)) - 10000
            if reduced_knowledge_size > 0:
                active_knowledge_text = active_knowledge_text[:reduced_knowledge_size] + "\n\n[注意: プロンプトサイズ制限のため、知識ベースを短縮しています]"
                # プロンプトを再構築
                prompt = f"""
        あなたは親切で丁寧な対応ができる{current_company_name}のアシスタントです。
        以下の知識ベースを参考に、ユーザーの質問に対って可能な限り具体的で役立つ回答を提供してください。

        利用可能なファイル: {', '.join(active_resource_names) if active_resource_names else 'なし'}

        回答の際の注意点：
        1. 常に丁寧な言葉遣いを心がけ、ユーザーに対して敬意を持って接してください
        2. 知識ベースに情報がない場合でも、一般的な文脈で回答できる場合は適切に対応してください
        3. ユーザーが「もっと詳しく」などと質問した場合は、前回の回答内容に関連する詳細情報を提供してください。「どのような情報について詳しく知りたいですか？」などと聞き返さないでください。
        4. 可能な限り具体的で実用的な情報を提供してください
        5. 知識ベースにOCRで抽出されたテキスト（PDF (OCR)と表示されている部分）が含まれている場合は、それが画像から抽出されたテキストであることを考慮してください
        6. OCRで抽出されたテキストには多少の誤りがある可能性がありますが、文脈から適切に解釈して回答してください
        7. 知識ベースの情報を使用して回答した場合は、回答の最後に「情報ソース: [ファイル名]」の形式で参照したファイル名を記載してください。
        8. 「こんにちは」「おはよう」などの単純な挨拶のみの場合は、情報ソースを記載しないでください。それ以外の質問には基本的に情報ソースを記載してください。
        9. 回答可能かどうかが判断できる質問に対しては、最初に「はい」または「いいえ」で簡潔に答えてから、具体的な説明や補足情報を記載してください
        10. 回答は**Markdown記法**を使用して見やすく整理してください。見出し（#、##、###）、箇条書き（-、*）、番号付きリスト（1.、2.）、強調（**太字**、*斜体*）、コードブロック（```）、表（|）、引用（>）などを適切に使用してください
        11. 手順や説明が複数ある場合は、番号付きリストや箇条書きを使用して構造化してください
        12. 重要な情報は**太字**で強調してください
        13. コードやファイル名、設定値などは`バッククォート`で囲んでください{special_instructions_text}
        
        知識ベース内容（アクティブなリソースのみ）：
        {active_knowledge_text}

        {conversation_history}

        ユーザーの質問：
        {message_text}
        """
            else:
                safe_print("❌ プロンプトが大きすぎて制限できません")
                return {
                    "response": "申し訳ございません。知識ベースが大きすぎるため、現在処理できません。管理者にお問い合わせください。",
                    "source": "",
                    "remaining_questions": remaining_questions,
                    "limit_reached": limit_reached
                }

        # Geminiによる応答生成
        try:
            safe_print(f"🤖 Gemini API呼び出し開始 - モデル: {model}")
            safe_print(f"📝 プロンプト長: {len(prompt)} 文字")
            
            response = model.generate_content(prompt)
            
            safe_print(f"📨 Gemini API応答受信: {response}")
            
            if not response or not hasattr(response, 'text'):
                safe_print(f"❌ 無効な応答: response={response}, hasattr(text)={hasattr(response, 'text') if response else 'N/A'}")
                raise ValueError("AIモデルからの応答が無効です")
            
            response_text = response.text
            safe_print(f"✅ 応答テキスト取得成功: {len(response_text)} 文字")
            
        except Exception as model_error:
            error_str = str(model_error)
            safe_print(f"❌ AIモデル応答生成エラー: {error_str}")
            safe_print(f"🔍 エラータイプ: {type(model_error)}")
            
            # より詳細なエラー情報をログ出力
            import traceback
            safe_print(f"📋 エラートレースバック:")
            safe_print(traceback.format_exc())
            
            # クォータ制限エラーの場合の特別な処理
            if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
                response_text = "申し訳ございません。現在、AIサービスの利用制限に達しています。しばらく時間をおいてから再度お試しください。"
                safe_print("⏸️ 利用制限の更新をスキップ: AIモデル応答生成エラー: " + error_str)
                
                # エラー応答を返す（利用制限は更新しない）
                return {
                    "response": response_text,
                    "source": "",
                    "remaining_questions": remaining_questions,
                    "limit_reached": limit_reached
                }
            else:
                response_text = f"申し訳ございません。応答の生成中にエラーが発生しました。エラー詳細: {error_str[:100]}..."
        
        # カテゴリと感情を分析するプロンプト
        analysis_prompt = f"""
        以下のユーザーの質問と回答を分析し、以下の情報を提供してください：
        1. カテゴリ: 質問のカテゴリを1つだけ選んでください（観光情報、交通案内、ショッピング、飲食店、イベント情報、挨拶、一般的な会話、その他、未分類）
        2. 感情: ユーザーの感情を1つだけ選んでください（ポジティブ、ネガティブ、ニュートラル）
        3. 参照ソース: 回答に使用した主なソース情報を1つ選んでください。以下のソース情報から選択してください：
        {json.dumps(source_info_list, ensure_ascii=False, indent=2)}

        重要:
        - 参照ソースの選択は、回答の内容と最も関連性の高いソースを選んでください。回答の内容が特定のソースから直接引用されている場合は、そのソースを選択してください。
        - 「こんにちは」「おはよう」などの単純な挨拶のみの場合のみ、カテゴリを「挨拶」に設定し、参照ソースは空にしてください。
        - それ以外の質問には、基本的に参照ソースを設定してください。知識ベースの情報を使用している場合は、必ず適切なソースを選択してください。

        回答は以下のJSON形式で返してください：
        {{
            "category": "カテゴリ名",
            "sentiment": "感情",
            "source": {{
                "name": "ソース名",
                "section": "セクション名",
                "page": "ページ番号"
            }}
        }}

        ユーザーの質問：
        {message_text}

        生成された回答：
        {response_text}
        """
        # 分析の実行
        try:
            analysis_response = model.generate_content(analysis_prompt)
            if not analysis_response or not hasattr(analysis_response, 'text'):
                raise ValueError("分析応答が無効です")
            analysis_text = analysis_response.text
        except Exception as analysis_error:
            error_str = str(analysis_error)
            safe_print(f"分析応答生成エラー: {error_str}")
            
            # クォータ制限エラーの場合でも分析は継続（デフォルト値を使用）
            if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
                safe_print("分析でクォータ制限エラー、デフォルト値を使用")
            
            analysis_text = '{"category": "未分類", "sentiment": "neutral", "source": {"name": "", "section": "", "page": ""}}'
        
        # JSON部分を抽出
        try:
            # JSONの部分を抽出（コードブロックの中身を取得）
            json_match = re.search(r'```json\s*(.*?)\s*```', analysis_text, re.DOTALL)
            if json_match:
                analysis_json = json.loads(json_match.group(1))
            else:
                # コードブロックがない場合は直接パース
                analysis_json = json.loads(analysis_text)
                
            category = analysis_json.get("category", "未分類")
            sentiment = analysis_json.get("sentiment", "neutral")
            source_doc = analysis_json.get("source", {}).get("name", "")
            source_page = analysis_json.get("source", {}).get("page", "")

            # 単純な挨拶のみの場合はソース情報をクリア
            # message_text = message.text.strip().lower() if message.text else ""
            # greetings = ["こんにちは", "こんにちわ", "おはよう", "おはようございます", "こんばんは", "よろしく", "ありがとう", "さようなら", "hello", "hi", "thanks", "thank you", "bye"]
            
            # if category == "挨拶" or any(greeting in message_text for greeting in greetings):
            #     # 応答テキストに「情報ソース:」が含まれているかチェック
            #     if response_text and "情報ソース:" in response_text:
            #         # 情報ソース部分を削除
            #         response_text = re.sub(r'\n*情報ソース:.*$', '', response_text, flags=re.DOTALL)
            #     source_doc = ""
            #     source_page = ""
            #     safe_print("2222222222222")
                
        except Exception as json_error:
            safe_print(f"JSON解析エラー: {str(json_error)}")
            category = "未分類"
            sentiment = "neutral"
            source_doc = ""
            source_page = ""
        
        # トークン使用量を計算してチャット履歴を保存
        from modules.token_counter import TokenUsageTracker
        
        # ユーザーの会社IDを取得（トークン追跡用）
        from supabase_adapter import select_data
        user_result = select_data("users", filters={"id": message.user_id}) if message.user_id else None
        final_company_id = user_result.data[0].get("company_id") if user_result and user_result.data else None
        
        # プロンプト参照数をカウント（アクティブなリソース数）
        prompt_references = len(active_sources) if active_sources else 0
        
        safe_print(f"🔍 トークン追跡デバッグ:")
        safe_print(f"  ユーザーID: {message.user_id}")
        safe_print(f"  会社ID: {final_company_id}")
        safe_print(f"  メッセージ長: {len(message_text)}")
        safe_print(f"  応答長: {len(response_text)}")
        safe_print(f"  プロンプト参照数: {prompt_references}")
        
        # 新しいトークン追跡機能を使用してチャット履歴を保存
        try:
            tracker = TokenUsageTracker(db)
            chat_id = tracker.save_chat_with_prompts(
                user_message=message_text,
                bot_response=response_text,
                user_id=message.user_id,
                prompt_references=prompt_references,
                company_id=final_company_id,
                employee_id=message.employee_id,
                employee_name=message.employee_name,
                category=category,
                sentiment=sentiment,
                source_document=source_doc,
                source_page=source_page,
                model="gemini-pro"  # Gemini料金体系を使用
            )
            safe_print(f"✅ トークン追跡保存成功: {chat_id}")
        except Exception as token_error:
            safe_print(f"❌ トークン追跡エラー: {token_error}")
            # トークン追跡でエラーが発生した場合はフォールバック保存
            chat_id = str(uuid.uuid4())
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO chat_history (id, user_message, bot_response, timestamp, category, sentiment, employee_id, employee_name, source_document, source_page, user_id, company_id, prompt_references) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (chat_id, message_text, response_text, datetime.now().isoformat(), category, sentiment, message.employee_id, message.employee_name, source_doc, source_page, message.user_id, company_id, prompt_references)
            )
            db.commit()
        
        # ユーザーIDがある場合は質問カウントを更新
        if message.user_id and not limits_check.get("is_unlimited", False):
            safe_print(f"利用制限更新開始 - ユーザーID: {message.user_id}")
            safe_print(f"更新前の制限情報: {limits_check}")
            
            updated_limits = update_usage_count(message.user_id, "questions_used", db)
            safe_print(f"更新後の制限情報: {updated_limits}")
            
            if updated_limits:
                remaining_questions = updated_limits["questions_limit"] - updated_limits["questions_used"]
                limit_reached = remaining_questions <= 0
                safe_print(f"計算された残り質問数: {remaining_questions}, 制限到達: {limit_reached}")
            else:
                safe_print("利用制限の更新に失敗しました")
        
        safe_print(f"返り値: remaining_questions={remaining_questions}, limit_reached={limit_reached}")
        
        # ソース情報が有効な場合のみ返す（source_docとsource_pageが空でない場合）
        source_text = ""
        if source_doc and source_doc.strip():
            source_text = source_doc
            if source_page and str(source_page).strip():
                source_text += f" (P.{source_page})"
        
        safe_print(f"最終ソース情報: '{source_text}'")
        
        return {
            "response": response_text,
            "source": source_text,
            "remaining_questions": remaining_questions,
            "limit_reached": limit_reached
        }
    except Exception as e:
        safe_print(f"チャットエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def chunk_knowledge_base(text: str, chunk_size: int = 500000) -> list[str]:
    """
    知識ベースを指定されたサイズでチャンク化する
    
    Args:
        text: チャンク化するテキスト
        chunk_size: チャンクのサイズ（文字数）
    
    Returns:
        チャンク化されたテキストのリスト
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # チャンクの境界を調整（文の途中で切れないように）
        if end < len(text):
            # 最後の改行を探す
            last_newline = text.rfind('\n', start, end)
            if last_newline > start:
                end = last_newline + 1
            else:
                # 改行がない場合は最後のスペースを探す
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end
    
    return chunks

async def process_chat_chunked(message: ChatMessage, db = Depends(get_db), current_user: dict = None):
    """
    チャンク化システムを使用したチャット処理
    知識ベースを50万文字ごとにチャンク化して段階的に処理
    """
    safe_print(f"🔄 チャンク化チャット処理開始 - ユーザーID: {message.user_id}")
    
    try:
        # 基本的な初期化処理
        message_text = message.message if hasattr(message, 'message') else message.text
        remaining_questions = 0
        limit_reached = False
        
        # 利用制限チェック
        from .database import get_usage_limits
        limits_check = get_usage_limits(message.user_id, db) if message.user_id else {"is_unlimited": True, "questions_limit": 0, "questions_used": 0}
        safe_print(f"利用制限チェック結果: {limits_check}")
        
        if not limits_check.get("is_unlimited", False):
            remaining_questions = limits_check["questions_limit"] - limits_check["questions_used"]
            limit_reached = remaining_questions <= 0
            
            if limit_reached:
                safe_print(f"❌ 利用制限到達 - 残り質問数: {remaining_questions}")
                return {
                    "response": "申し訳ございません。本日の質問回数制限に達しました。明日になると再度ご利用いただけます。",
                    "remaining_questions": 0,
                    "limit_reached": True
                }
        
        # 会社名の取得
        current_company_name = "WorkMate"
        if message.user_id:
            try:
                from supabase_adapter import select_data
                user_result = select_data("users", filters={"id": message.user_id})
                if user_result and user_result.data:
                    company_id = user_result.data[0].get("company_id")
                    if company_id:
                        company_data = get_company_by_id(company_id, db)
                        current_company_name = company_data["name"] if company_data else "WorkMate"
            except Exception as e:
                safe_print(f"会社名取得エラー: {str(e)}")
        
        # アクティブなリソースの取得
        active_sources = []
        if message.user_id:
            try:
                from supabase_adapter import select_data
                user_result = select_data("users", filters={"id": message.user_id})
                if user_result and user_result.data:
                    company_id = user_result.data[0].get("company_id")
                    if company_id:
                        active_sources = await get_active_resources_by_company_id(company_id, db)
            except Exception as e:
                safe_print(f"アクティブリソース取得エラー: {str(e)}")
        
        if not active_sources:
            safe_print("❌ アクティブなリソースが見つかりません")
            return {
                "response": "申し訳ございません。アクティブな知識ベースが見つかりません。管理画面でリソースを有効にしてください。",
                "remaining_questions": remaining_questions,
                "limit_reached": limit_reached
            }
        
        # 知識ベース内容の取得
        safe_print(f"📚 知識ベース取得開始 - アクティブソース: {len(active_sources)}個")
        active_knowledge_text = await get_active_resources_content_by_ids(active_sources, db)
        
        if not active_knowledge_text or not active_knowledge_text.strip():
            safe_print("❌ 知識ベース内容が空です")
            return {
                "response": "申し訳ございません。知識ベースの内容が空です。管理画面で別のリソースを有効にしてください。",
                "remaining_questions": remaining_questions,
                "limit_reached": limit_reached
            }
        
        safe_print(f"📊 取得した知識ベース: {len(active_knowledge_text)} 文字")
        
        # RAG風検索で関連部分のみを抽出（チャンク化前の事前フィルタリング）
        if active_knowledge_text and len(active_knowledge_text) > 100000:
            active_knowledge_text = simple_rag_search(active_knowledge_text, message_text, max_results=15)
            safe_print(f"📊 RAG検索後: {len(active_knowledge_text)} 文字")
        
        # アクティブなリソースの情報とSpecial指示を取得
        special_instructions = []
        active_resource_names = []
        try:
            from supabase_adapter import select_data
            for source_id in active_sources:
                source_result = select_data("document_sources", columns="name,special", filters={"id": source_id})
                if source_result.data and len(source_result.data) > 0:
                    source_data = source_result.data[0]
                    source_name = source_data.get('name', 'Unknown')
                    active_resource_names.append(source_name)
                    
                    if source_data.get('special') and source_data['special'].strip():
                        special_instructions.append({
                            "name": source_name,
                            "instruction": source_data['special'].strip()
                        })
            safe_print(f"アクティブリソース: {len(active_resource_names)}個 - {active_resource_names}")
            safe_print(f"Special指示: {len(special_instructions)}個のリソースにSpecial指示があります")
        except Exception as e:
            safe_print(f"リソース情報取得エラー: {str(e)}")
            special_instructions = []
            active_resource_names = []

        # Special指示をプロンプトに追加するための文字列を構築
        special_instructions_text = ""
        if special_instructions:
            special_instructions_text = "\n\n特別な回答指示（以下のリソースを参照する際は、各リソースの指示に従ってください）：\n"
            for idx, inst in enumerate(special_instructions, 1):
                special_instructions_text += f"{idx}. 【{inst['name']}】: {inst['instruction']}\n"

        # 知識ベースをチャンク化
        CHUNK_SIZE = 500000  # 50万文字
        chunks = chunk_knowledge_base(active_knowledge_text, CHUNK_SIZE)
        safe_print(f"🔪 チャンク化完了: {len(chunks)}個のチャンク")
        
        # 会話履歴の取得
        conversation_history = ""
        try:
            if message.user_id:
                from supabase_adapter import select_data
                chat_history_result = select_data(
                    "chat_history",
                    filters={"employee_id": message.user_id},
                    limit=2
                )
                
                if chat_history_result and chat_history_result.data:
                    recent_messages = list(reversed(chat_history_result.data))
                    
                    if recent_messages:
                        conversation_history = "直近の会話履歴：\n"
                        for msg in recent_messages:
                            user_msg = (msg.get('user_message', '') or '')[:100]
                            bot_msg = (msg.get('bot_response', '') or '')[:100]
                            if len(msg.get('user_message', '')) > 100:
                                user_msg += "..."
                            if len(msg.get('bot_response', '')) > 100:
                                bot_msg += "..."
                            conversation_history += f"ユーザー: {user_msg}\n"
                            conversation_history += f"アシスタント: {bot_msg}\n\n"
        except Exception as e:
            safe_print(f"会話履歴取得エラー: {str(e)}")
        
        # 各チャンクを順次処理（適切な回答が得られた時点で停止）
        all_responses = []
        successful_chunks = 0
        
        for i, chunk in enumerate(chunks):
            safe_print(f"🔄 チャンク {i+1}/{len(chunks)} 処理開始 ({len(chunk)} 文字)")
            
            # 全チャンクの詳細情報を出力（デバッグ用）
            safe_print(f"🔍 チャンク{i+1}の最初の200文字: {chunk[:200]}...")
            if len(chunk) > 400:
                safe_print(f"🔍 チャンク{i+1}の最後の200文字: ...{chunk[-200:]}")
            
            # キーワード検索でデバッグ
            if "Buzz Style" in chunk:
                safe_print(f"✅ チャンク{i+1}に「Buzz Style」を発見")
            if "設定完了" in chunk:
                safe_print(f"✅ チャンク{i+1}に「設定完了」を発見")
            
            # プロンプトの作成
            prompt = f"""
あなたは親切で丁寧な対応ができる{current_company_name}のアシスタントです。
以下の知識ベースを参考に、ユーザーの質問に対して可能な限り具体的で役立つ回答を提供してください。

注意: これは知識ベース全体の一部です（チャンク {i+1}/{len(chunks)}）。
このチャンクの情報を使用して、質問に関連する情報があれば積極的に回答してください。

利用可能なファイル: {', '.join(active_resource_names) if active_resource_names else 'なし'}

回答の際の注意点：
1. 常に丁寧な言葉遣いを心がけ、ユーザーに対して敬意を持って接してください
2. 知識ベース内に質問に関連する情報があれば、部分的でも積極的に回答してください
3. 完全に関連のない情報しかない場合のみ「このチャンクには該当情報がありません」と回答してください
4. 可能な限り具体的で実用的な情報を提供してください
5. 知識ベースの情報を使用して回答した場合は、回答の最後に「情報ソース: [ファイル名]」の形式で参照したファイル名を記載してください
6. 回答は**Markdown記法**を使用して見やすく整理してください{special_instructions_text}

知識ベース内容（チャンク {i+1}/{len(chunks)}）：
{chunk}

{conversation_history}

ユーザーの質問：
{message_text}
"""
            
            # Gemini API呼び出し
            try:
                model = setup_gemini()
                
                safe_print(f"🤖 Gemini API呼び出し - チャンク {i+1}")
                safe_print(f"📏 プロンプトサイズ: {len(prompt)} 文字")
                
                # タイムアウト付きでAPI呼び出し
                import time
                start_time = time.time()
                
                response = model.generate_content(prompt)
                
                end_time = time.time()
                elapsed_time = end_time - start_time
                safe_print(f"📨 API応答受信 - チャンク {i+1} (処理時間: {elapsed_time:.2f}秒)")
                
                if response and hasattr(response, 'text'):
                    if response.text and response.text.strip():
                        chunk_response = response.text.strip()
                        safe_print(f"📝 応答テキスト長: {len(chunk_response)} 文字 - チャンク {i+1}")
                        safe_print(f"📝 応答内容（最初の100文字）: {chunk_response[:100]}...")
                        
                        # 「該当情報がありません」系の回答でない場合のみ追加
                        # より厳密な条件で「該当情報なし」を判定
                        no_info_phrases = [
                            "このチャンクには該当情報がありません",
                            "該当する情報が見つかりません", 
                            "完全に関連のない情報しかありません"
                        ]
                        
                        # 完全一致または非常に類似した応答の場合のみ除外
                        is_no_info = any(
                            phrase in chunk_response.lower() and len(chunk_response.strip()) < 100
                            for phrase in no_info_phrases
                        )
                        
                        if not is_no_info:
                            all_responses.append(chunk_response)
                            successful_chunks += 1
                            safe_print(f"✅ チャンク {i+1} 処理成功 - 回答を統合リストに追加")
                            
                            # 適切な回答が得られた場合、後続のチャンクを処理せずに終了
                            # 回答の質を判定（文字数、内容の具体性、および回答の完全性をチェック）
                            if (len(chunk_response) > 100 and 
                                not any(vague_phrase in chunk_response.lower() for vague_phrase in [
                                    "申し訳ございません", "わかりません", "不明", "詳細は", "確認できません",
                                    "情報が不足", "明確ではない", "部分的"
                                ]) and
                                # 具体的な内容が含まれているかを確認
                                any(content_indicator in chunk_response.lower() for content_indicator in [
                                    "方法", "手順", "設定", "について", "場合", "必要", "以下", "または", "および"
                                ])):
                                safe_print(f"🎯 チャンク {i+1} で十分で具体的な回答を取得 - 処理を終了")
                                break
                        else:
                            safe_print(f"ℹ️ チャンク {i+1} に該当情報なし - 除外フレーズにマッチ")
                    else:
                        safe_print(f"⚠️ チャンク {i+1} 空の応答テキスト")
                else:
                    safe_print(f"⚠️ チャンク {i+1} 無効な応答オブジェクト")
                    if response:
                        safe_print(f"🔍 応答オブジェクトの属性: {dir(response)}")
                    
            except Exception as e:
                safe_print(f"❌ チャンク {i+1} 処理エラー: {str(e)}")
                safe_print(f"🔍 エラータイプ: {type(e).__name__}")
                import traceback
                safe_print(f"🔍 エラー詳細: {traceback.format_exc()}")
                
                # Gemini API固有のエラーをチェック
                if hasattr(e, 'code'):
                    safe_print(f"🔍 APIエラーコード: {e.code}")
                if hasattr(e, 'message'):
                    safe_print(f"🔍 APIエラーメッセージ: {e.message}")
                    
                continue
            
            # APIレート制限を避けるため少し待機（最後のチャンクでない場合のみ）
            if i < len(chunks) - 1:
                await asyncio.sleep(1)
        
        # 最終回答の生成
        if all_responses:
            # 最初の有効な回答を使用（無駄な統合を避ける）
            final_response = all_responses[0]
            
            # チャンク情報を削除し、シンプルなファイル名表示に変更
            # [チャンク X/Y より] のような表示を削除
            import re
            final_response = re.sub(r'\[チャンク \d+/\d+ より\]', '', final_response)
            final_response = final_response.strip()
            
        else:
            final_response = f"""申し訳ございません。ご質問に対する適切な回答が見つかりませんでした。

別の質問方法でお試しいただくか、管理者にお問い合わせください。"""
        
        # プロンプト参照数を計算（アクティブリソース数をプロンプト参照数として使用）
        prompt_references = len(active_sources)
        safe_print(f"💰 プロンプト参照数: {prompt_references} (アクティブリソース数)")
        
        # チャット履歴の保存
        try:
            from modules.token_counter import TokenUsageTracker
            from supabase_adapter import select_data
            
            user_result = select_data("users", filters={"id": message.user_id}) if message.user_id else None
            chat_company_id = user_result.data[0].get("company_id") if user_result and user_result.data else None
            
            tracker = TokenUsageTracker(db)
            chat_id = tracker.save_chat_with_prompts(
                user_message=message_text,
                bot_response=final_response,
                user_id=message.user_id,
                prompt_references=prompt_references,
                company_id=chat_company_id,
                employee_id=message.employee_id,
                employee_name=message.employee_name,
                category="チャンク処理",
                sentiment="neutral",
                model="gemini-pro"
            )
            safe_print(f"💾 チャット履歴保存完了 - ID: {chat_id}, プロンプト参照: {prompt_references}")
        except Exception as e:
            safe_print(f"チャット履歴保存エラー: {str(e)}")
        
        # 利用制限の更新
        if message.user_id and not limits_check.get("is_unlimited", False):
            try:
                from .database import update_usage_count
                updated_limits = update_usage_count(message.user_id, "questions_used", db)
                if updated_limits:
                    remaining_questions = updated_limits["questions_limit"] - updated_limits["questions_used"]
                    limit_reached = remaining_questions <= 0
                    safe_print(f"📊 利用制限更新完了 - 残り: {remaining_questions}")
            except Exception as e:
                safe_print(f"利用制限更新エラー: {str(e)}")
        
        safe_print(f"✅ チャンク化処理完了 - 成功チャンク: {successful_chunks}/{len(chunks)}")
        
        return {
            "response": final_response,
            "remaining_questions": remaining_questions,
            "limit_reached": limit_reached,
            "chunks_processed": len(chunks),
            "successful_chunks": successful_chunks
        }
        
    except Exception as e:
        safe_print(f"❌ チャンク化処理で重大エラー: {str(e)}")
        # エラー時のデフォルト値を設定
        try:
            remaining_questions = remaining_questions if 'remaining_questions' in locals() else 0
            limit_reached = limit_reached if 'limit_reached' in locals() else False
        except:
            remaining_questions = 0
            limit_reached = False
            
        return {
            "response": f"申し訳ございません。システムエラーが発生しました: {str(e)}",
            "remaining_questions": remaining_questions,
            "limit_reached": limit_reached
        }