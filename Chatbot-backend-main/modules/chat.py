"""
チャットモジュール
チャット機能とAI応答生成を管理します
"""
import json
import re
import uuid
from datetime import datetime
import logging
from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException, Depends
from .company import DEFAULT_COMPANY_NAME
from .models import ChatMessage, ChatResponse
from .database import get_db, update_usage_count, get_usage_limits
from .knowledge_base import knowledge_base, get_active_resources
from .auth import check_usage_limits
from .resource import get_active_resources_by_company_id, get_active_resources_content_by_ids, get_active_resource_names_by_company_id

logger = logging.getLogger(__name__)

# Geminiモデル（グローバル変数）
model = None

def set_model(gemini_model):
    """Geminiモデルを設定する"""
    global model
    model = gemini_model

async def process_chat(message: ChatMessage, db: Connection = Depends(get_db)):
    """チャットメッセージを処理してGeminiからの応答を返す"""
    try:
        # モデルが設定されているか確認
        if model is None:
            raise HTTPException(status_code=500, detail="AIモデルが初期化されていません")
        
        # メッセージがNoneでないことを確認
        if not message or not hasattr(message, 'text') or message.text is None:
            raise HTTPException(status_code=400, detail="メッセージテキストが提供されていません")
        
        # メッセージテキストを安全に取得
        message_text = message.text if message.text is not None else ""
        
        # 最新の会社名を取得（モジュールからの直接インポートではなく、関数内で再取得）
        from .company import DEFAULT_COMPANY_NAME as current_company_name
        
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
            cursor = db.cursor()
            cursor.execute("SELECT company_id FROM users WHERE id = %s", (message.user_id,))
            user = cursor.fetchone()
            if user and user['company_id']:
                company_id = user['company_id']
        
        # 会社固有のアクティブなリソースを取得
        # active_sources = get_active_resources(company_id)
        active_sources = await get_active_resources_by_company_id(company_id, db)
        print(f"アクティブなリソース (会社ID: {company_id}): {', '.join(active_sources)}")
        
        # アクティブなリソースがない場合はエラーメッセージを返す
        if not active_sources:
            response_text = f"申し訳ございません。現在、アクティブな知識ベースがありません。管理画面でリソースを有効にしてください。"
            
            # チャット履歴を保存
            chat_id = str(uuid.uuid4())
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO chat_history (id, user_message, bot_response, timestamp, category, sentiment, employee_id, employee_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (chat_id, message_text, response_text, datetime.now().isoformat(), "設定エラー", "neutral", message.employee_id, message.employee_name)
            )
            db.commit()
            
            # ユーザーIDがある場合は質問カウントを更新（アクティブなリソースがなくても利用制限は更新する）
            if message.user_id and not limits_check.get("is_unlimited", False):
                print(f"利用制限更新開始（アクティブリソースなし） - ユーザーID: {message.user_id}")
                print(f"更新前の制限情報: {limits_check}")
                
                updated_limits = update_usage_count(message.user_id, "questions_used", db)
                print(f"更新後の制限情報: {updated_limits}")
                
                if updated_limits:
                    remaining_questions = updated_limits["questions_limit"] - updated_limits["questions_used"]
                    limit_reached = remaining_questions <= 0
                    print(f"計算された残り質問数: {remaining_questions}, 制限到達: {limit_reached}")
                else:
                    print("利用制限の更新に失敗しました")
            
            print(f"返り値（アクティブリソースなし）: remaining_questions={remaining_questions}, limit_reached={limit_reached}")
            
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
        
        # print(f"知識ベースの生データ長: {len(knowledge_base.raw_text) if knowledge_base.raw_text else 0}")
        print(f"アクティブなソース: {active_sources}")
        active_knowledge_text = await get_active_resources_content_by_ids(active_sources, db)
        # アクティブな知識ベースが空の場合はエラーメッセージを返す
        if not active_knowledge_text or (isinstance(active_knowledge_text, str) and not active_knowledge_text.strip()):
            response_text = f"申し訳ございません。アクティブな知識ベースの内容が空です。管理画面で別のリソースを有効にしてください。"
            
            # トークン使用量を計算してチャット履歴を保存（エラーケース）
            from modules.token_counter import TokenUsageTracker
            
            # ユーザーの会社IDを取得（チャット履歴保存用）
            from supabase_adapter import select_data
            user_result = select_data("users", filters={"id": message.user_id}) if hasattr(message, 'user_id') and message.user_id else None
            chat_company_id = user_result.data[0].get("company_id") if user_result and user_result.data else None
            
            # トークン追跡機能を使用してチャット履歴を保存
            tracker = TokenUsageTracker(db)
            chat_id = tracker.save_chat_with_tokens(
                user_message=message_text,
                bot_response=response_text,
                user_id=getattr(message, 'user_id', None),
                company_id=chat_company_id,
                employee_id=message.employee_id,
                employee_name=message.employee_name,
                category="設定エラー",
                sentiment="neutral",
                model="gpt-4o-mini"
            )
            
            # ユーザーIDがある場合は質問カウントを更新（知識ベースが空でも利用制限は更新する）
            if message.user_id and not limits_check.get("is_unlimited", False):
                print(f"利用制限更新開始（知識ベース空） - ユーザーID: {message.user_id}")
                print(f"更新前の制限情報: {limits_check}")
                
                updated_limits = update_usage_count(message.user_id, "questions_used", db)
                print(f"更新後の制限情報: {updated_limits}")
                
                if updated_limits:
                    remaining_questions = updated_limits["questions_limit"] - updated_limits["questions_used"]
                    limit_reached = remaining_questions <= 0
                    print(f"計算された残り質問数: {remaining_questions}, 制限到達: {limit_reached}")
                else:
                    print("利用制限の更新に失敗しました")
            
            print(f"返り値（知識ベース空）: remaining_questions={remaining_questions}, limit_reached={limit_reached}")
            
            return {
                "response": response_text,
                "remaining_questions": remaining_questions,
                "limit_reached": limit_reached
            }
            
        # 直近のメッセージを取得（最大5件）
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
                        LIMIT 5
                        """,
                        (message.user_id,)
                    )
                    cursor_result = cursor.fetchall()
                    # PostgreSQLの結果をリストに変換してから古い順に並べ替え
                    recent_messages = list(cursor_result)
                    recent_messages.reverse()
        except Exception as e:
            print(f"会話履歴取得エラー: {str(e)}")
            recent_messages = []
        
        # 会話履歴の構築
        conversation_history = ""
        if recent_messages:
            conversation_history = "直近の会話履歴：\n"
            for idx, msg in enumerate(recent_messages):
                
                try:
                    user_msg = msg.get('user_message', '') or ''
                    bot_msg = msg.get('bot_response', '') or ''
                    conversation_history += f"ユーザー: {user_msg}\n"
                    conversation_history += f"アシスタント: {bot_msg}\n\n"
                except Exception as e:
                    print(f"会話履歴処理エラー: {str(e)}")
                    # エラーが発生した場合はその行をスキップ
                    continue

        # プロンプトの作成
        prompt = f"""
        あなたは親切で丁寧な対応ができる{current_company_name}のアシスタントです。
        以下の知識ベースを参考に、ユーザーの質問に対して可能な限り具体的で役立つ回答を提供してください。

        回答の際の注意点：
        1. 常に丁寧な言葉遣いを心がけ、ユーザーに対して敬意を持って接してください
        2. 知識ベースに情報がない場合でも、一般的な文脈で回答できる場合は適切に対応してください
        3. ユーザーが「もっと詳しく」などと質問した場合は、前回の回答内容に関連する詳細情報を提供してください。「どのような情報について詳しく知りたいですか？」などと聞き返さないでください。
        4. 可能な限り具体的で実用的な情報を提供してください
        5. 知識ベースにOCRで抽出されたテキスト（PDF (OCR)と表示されている部分）が含まれている場合は、それが画像から抽出されたテキストであることを考慮してください
        6. OCRで抽出されたテキストには多少の誤りがある可能性がありますが、文脈から適切に解釈して回答してください
        7. 知識ベースの情報を使用して回答した場合は、回答の最後に情報の出典を「情報ソース: [ドキュメント名]（[セクション名]、[ページ番号]）」の形式で必ず記載してください。複数のソースを参照した場合は、それぞれを記載してください。
        8. 「こんにちは」「おはよう」などの単純な挨拶のみの場合は、情報ソースを記載しないでください。それ以外の質問には基本的に情報ソースを記載してください。
        9. 回答可能かどうかが判断できる質問に対しては、最初に「はい」または「いいえ」で簡潔に答えてから、具体的な説明や補足情報を記載してください
        
        利用可能なデータ列：
        {', '.join(knowledge_base.columns) if knowledge_base and hasattr(knowledge_base, 'columns') and knowledge_base.columns else "データ列なし"}

        知識ベース内容（アクティブなリソースのみ）：
        {active_knowledge_text}

        {f"画像情報：PDFから抽出された画像が{len(knowledge_base.images)}枚あります。" if knowledge_base and hasattr(knowledge_base, 'images') and knowledge_base.images and isinstance(knowledge_base.images, list) else ""}

        {conversation_history}

        ユーザーの質問：
        {message_text}
        """

        # Geminiによる応答生成
        try:
            response = model.generate_content(prompt)
            if not response or not hasattr(response, 'text'):
                raise ValueError("AIモデルからの応答が無効です")
            response_text = response.text
        except Exception as model_error:
            print(f"AIモデル応答生成エラー: {str(model_error)}")
            response_text = "申し訳ございません。応答の生成中にエラーが発生しました。しばらく経ってからもう一度お試しください。"
        
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
            print(f"分析応答生成エラー: {str(analysis_error)}")
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
            #     print("2222222222222")
                
        except Exception as json_error:
            print(f"JSON解析エラー: {str(json_error)}")
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
        
        print(f"🔍 トークン追跡デバッグ:")
        print(f"  ユーザーID: {message.user_id}")
        print(f"  会社ID: {final_company_id}")
        print(f"  メッセージ長: {len(message_text)}")
        print(f"  応答長: {len(response_text)}")
        
        # トークン追跡機能を使用してチャット履歴を保存
        try:
            tracker = TokenUsageTracker(db)
            chat_id = tracker.save_chat_with_tokens(
                user_message=message_text,
                bot_response=response_text,
                user_id=message.user_id,
                company_id=final_company_id,
                employee_id=message.employee_id,
                employee_name=message.employee_name,
                category=category,
                sentiment=sentiment,
                source_document=source_doc,
                source_page=source_page,
                model="gpt-4o-mini"  # 使用しているモデル名
            )
            print(f"✅ トークン追跡保存成功: {chat_id}")
        except Exception as token_error:
            print(f"❌ トークン追跡エラー: {token_error}")
            # エラーでも通常のチャット履歴は保存する
        chat_id = str(uuid.uuid4())
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO chat_history (id, user_message, bot_response, timestamp, category, sentiment, employee_id, employee_name, source_document, source_page) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (chat_id, message_text, response_text, datetime.now().isoformat(), category, sentiment, message.employee_id, message.employee_name, source_doc, source_page)
        )
        db.commit()
        
        # ユーザーIDがある場合は質問カウントを更新
        if message.user_id and not limits_check.get("is_unlimited", False):
            print(f"利用制限更新開始 - ユーザーID: {message.user_id}")
            print(f"更新前の制限情報: {limits_check}")
            
            updated_limits = update_usage_count(message.user_id, "questions_used", db)
            print(f"更新後の制限情報: {updated_limits}")
            
            if updated_limits:
                remaining_questions = updated_limits["questions_limit"] - updated_limits["questions_used"]
                limit_reached = remaining_questions <= 0
                print(f"計算された残り質問数: {remaining_questions}, 制限到達: {limit_reached}")
            else:
                print("利用制限の更新に失敗しました")
        
        print(f"返り値: remaining_questions={remaining_questions}, limit_reached={limit_reached}")
        
        return {
            "response": response_text,
            "source": (source_doc or "") + (f" (P.{source_page})" if source_page else ""),
            "remaining_questions": remaining_questions,
            "limit_reached": limit_reached
        }
    except Exception as e:
        print(f"チャットエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))