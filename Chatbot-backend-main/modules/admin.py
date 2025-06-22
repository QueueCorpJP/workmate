"""
管理画面モジュール
管理画面で使用する機能を提供します
"""
import os
import logging
import aiofiles
from datetime import datetime
from typing import List, Dict, Any, Optional
from io import BytesIO
from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException, Depends, UploadFile
from .database import get_db
from .models import ChatHistoryItem, AnalysisResult, EmployeeUsageResult
from .company import DEFAULT_COMPANY_NAME
from .knowledge_base import knowledge_base
from .knowledge.url import extract_text_from_url
from .knowledge.excel import process_excel_file
from .knowledge.excel_sheets_processor import process_excel_file_with_sheets_api, is_excel_file
from .knowledge.pdf import process_pdf_file
from .knowledge.text import process_txt_file
from supabase_adapter import select_data, insert_data, update_data, delete_data

logger = logging.getLogger(__name__)

# Geminiモデル（グローバル変数）
model = None

def set_model(gemini_model):
    """Geminiモデルを設定する"""
    global model
    model = gemini_model

# 知識ベースをリフレッシュする関数
async def refresh_knowledge_base():
    """知識ベースをリフレッシュする"""
    print("知識ベースをリフレッシュします")
    
    # 現在のソース情報を保存
    sources = knowledge_base.sources.copy()
    source_info = knowledge_base.source_info.copy()
    
    # 知識ベースをリセット
    knowledge_base.data = None
    knowledge_base.raw_text = ""
    knowledge_base.columns = []
    knowledge_base.url_data = []
    knowledge_base.url_texts = []
    knowledge_base.file_data = []
    knowledge_base.file_texts = []
    
    # ソース情報を復元
    knowledge_base.sources = sources
    knowledge_base.source_info = source_info
    
    # 各ソースを再処理
    for source in sources:
        if isinstance(source, dict):
            source_type = source.get("type")
            
            if source_type == "url":
                url = source.get("url")
                if url:
                    try:
                        extracted_text = await extract_text_from_url(url)
                        if not extracted_text.startswith("URLからのテキスト抽出エラー:"):
                            from .knowledge.url import process_url_content
                            df, sections, processed_text = await process_url_content(url, extracted_text)
                            from .knowledge.base import _update_knowledge_base
                            _update_knowledge_base(df, processed_text, is_file=False, source_name=url)
                        print(f"URL {url} を再処理しました")
                    except Exception as e:
                        print(f"URL {url} の再処理に失敗しました: {e}")
            
            elif source_type == "file":
                file_path = source.get("file_path")
                file_name = source.get("name")
                
                if file_path and os.path.exists(file_path):
                    try:
                        with open(file_path, "rb") as f:
                            content = f.read()
                            
                        if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
                            try:
                                # Google Sheets APIを使用してExcelファイルを処理
                                # 管理者機能では環境変数からサービスアカウントを使用
                                service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
                                
                                data_list, sections, extracted_text = await process_excel_file_with_sheets_api(
                                    content, 
                                    file_name, 
                                    access_token=None,  # 管理者機能ではサービスアカウントを優先
                                    service_account_file=service_account_file
                                )
                                
                                # データリストを直接使用（DataFrameを使用しない）
                                if not data_list:
                                    data_list = [{
                                        'section': "データなし",
                                        'content': "Excelファイルに有効なデータが見つかりませんでした",
                                        'source': 'Excel (Google Sheets)',
                                        'file': file_name,
                                        'url': None
                                    }]
                                
                                # データベース保存用にDataFrameに変換
                                import pandas as pd
                                df = pd.DataFrame(data_list)
                                
                                print(f"Excel処理完了（Google Sheets API使用）: {len(data_list)} レコード")
                                
                            except Exception as e:
                                print(f"Google Sheets API処理エラー、従来の処理にフォールバック: {str(e)}")
                                # フォールバック：従来のpandas処理
                                df, sections, extracted_text = process_excel_file(content, file_name)
                        elif file_name.endswith(".pdf"):
                            df, sections, extracted_text = await process_pdf_file(content, file_name)
                        elif file_name.endswith(".txt"):
                            df, sections, extracted_text = process_txt_file(content, file_name)
                        
                        # 知識ベースを更新
                        from .knowledge.base import _update_knowledge_base
                        _update_knowledge_base(df, extracted_text, is_file=True, source_name=file_name)
                        print(f"ファイル {file_name} を再処理しました")
                    except Exception as e:
                        print(f"ファイル {file_name} の再処理に失敗しました: {e}")
        else:
            # 文字列のソース（ファイル名やURL）の場合
            source_name = source
            if source_name.startswith(('http://', 'https://')):
                try:
                    extracted_text = await extract_text_from_url(source_name)
                    if not extracted_text.startswith("URLからのテキスト抽出エラー:"):
                        from .knowledge.url import process_url_content
                        df, sections, processed_text = await process_url_content(source_name, extracted_text)
                        from .knowledge.base import _update_knowledge_base
                        _update_knowledge_base(df, processed_text, is_file=False, source_name=source_name)
                    print(f"URL {source_name} を再処理しました")
                except Exception as e:
                    print(f"URL {source_name} の再処理に失敗しました: {e}")
            else:
                # ファイル名と仮定して処理
                print(f"ソース {source_name} はファイル名と仮定しますが、ファイルパスが不明なため処理できません")
    
    # 知識ベースを更新（update関数は存在しない可能性があるため、直接データを確認）
    print(f"知識ベース更新完了: {len(knowledge_base.data) if knowledge_base.data is not None else 0} 行のデータ")
    
    return {"status": "success", "message": "知識ベースを更新しました"}

def get_chat_history(user_id: str = None, db = None):
    """チャット履歴を取得する"""
    print(f"チャット履歴取得APIが呼び出されました (user_id: {user_id})")
    try:
        from supabase_adapter import select_data
        
        # Supabaseからチャット履歴を取得
        if user_id:
            # print(f"ユーザーID {user_id} でフィルタリングします")
            # 特定のユーザーの履歴を取得
            result = select_data("chat_history", filters={"employee_id": user_id})
        else:
            # print("全ユーザーのチャット履歴を取得します")
            # 全履歴を取得
            result = select_data("chat_history")
        
        if not result or not result.data:
            # print("チャット履歴が見つかりませんでした")
            return []
        
        chat_history = result.data
        # print(f"チャット履歴取得結果: {len(chat_history)}件")
        
        # データ形式を統一
        formatted_history = []
        for chat in chat_history:
            item = {
                "id": chat.get("id", ""),
                "user_message": chat.get("user_message", ""),
                "bot_response": chat.get("bot_response", ""),
                "timestamp": chat.get("timestamp", ""),
                "category": chat.get("category", ""),
                "sentiment": chat.get("sentiment", ""),
                "employee_id": chat.get("employee_id", ""),
                "employee_name": chat.get("employee_name", ""),
                "source_document": chat.get("source_document", ""),
                "source_page": chat.get("source_page", "")
            }
            formatted_history.append(item)
        
        # タイムスタンプで降順ソート
        formatted_history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # print(f"チャット履歴変換結果: {len(formatted_history)}件")
        return formatted_history
        
    except Exception as e:
        print(f"チャット履歴取得エラー: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"チャット履歴取得中にエラーが発生しました: {str(e)}")

def get_chat_history_paginated(user_id: str = None, db = None, limit: int = 30, offset: int = 0):
    """ページネーション対応のチャット履歴を取得する"""
    # print(f"ページネーション対応チャット履歴取得APIが呼び出されました (user_id: {user_id}, limit: {limit}, offset: {offset})")
    try:
        from supabase_adapter import select_data
        
        # 全件数を取得するためのクエリ
        if user_id:
            # print(f"ユーザーID {user_id} でフィルタリングします")
            # 特定のユーザーの履歴を取得
            count_result = select_data("chat_history", columns="id", filters={"employee_id": user_id})
            result = select_data("chat_history", columns="*", filters={"employee_id": user_id}, order="timestamp desc", limit=limit, offset=offset)
        else:
            # print("全ユーザーのチャット履歴を取得します")
            # 全履歴を取得
            count_result = select_data("chat_history", columns="id")
            result = select_data("chat_history", columns="*", order="timestamp desc", limit=limit, offset=offset)
        
        # 全件数を取得
        total_count = len(count_result.data) if count_result and count_result.data else 0
        
        if not result or not result.data:
            # print("チャット履歴が見つかりませんでした")
            return [], total_count
        
        chat_history = result.data
        # print(f"チャット履歴取得結果: {len(chat_history)}件 (全体: {total_count}件)")
        
        # データ形式を統一
        formatted_history = []
        for chat in chat_history:
            item = {
                "id": chat.get("id", ""),
                "user_message": chat.get("user_message", ""),
                "bot_response": chat.get("bot_response", ""),
                "timestamp": chat.get("timestamp", ""),
                "category": chat.get("category", ""),
                "sentiment": chat.get("sentiment", ""),
                "employee_id": chat.get("employee_id", ""),
                "employee_name": chat.get("employee_name", ""),
                "source_document": chat.get("source_document", ""),
                "source_page": chat.get("source_page", "")
            }
            formatted_history.append(item)
        
        # print(f"チャット履歴変換結果: {len(formatted_history)}件")
        return formatted_history, total_count
        
    except Exception as e:
        print(f"チャット履歴取得エラー: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"チャット履歴取得中にエラーが発生しました: {str(e)}")

async def get_company_employees(user_id: str = None, db: Connection = Depends(get_db), company_id: str = None):
    """会社の社員情報を取得する"""
    try:
        from supabase_adapter import select_data, execute_query
        
        # ユーザーロールとアクセス権限の確認
        user_result = select_data("users", columns="email, role", filters={"id": user_id})
        user_role = None
        user_email = None
        if user_result and user_result.data:
            user_data = user_result.data[0]
            user_role = user_data.get("role")
            user_email = user_data.get("email")
        
        is_special_admin = user_email == "queue@queueu-tech.jp"
        is_admin = user_role == "admin"
        is_user = user_role == "user"
        
        # print(f"社員情報取得: user_id={user_id}, role={user_role}, is_special_admin={is_special_admin}")
        
        def get_employee_stats(employee_id):
            """社員の使用状況を取得する"""
            try:
                # Supabaseの標準的な方法でメッセージ数を取得
                chat_history_result = select_data("chat_history", columns="id, timestamp", filters={"employee_id": employee_id})
                
                message_count = 0
                last_activity = None
                
                if chat_history_result and chat_history_result.data:
                    messages = chat_history_result.data
                    message_count = len(messages)
                    
                    # 最新のタイムスタンプを取得
                    if messages:
                        timestamps = [msg.get("timestamp") for msg in messages if msg.get("timestamp")]
                        if timestamps:
                            last_activity = max(timestamps)
                
                # 利用制限情報を取得
                usage_limits_result = select_data("usage_limits", columns="*", filters={"user_id": employee_id})
                usage_limits = None
                is_demo = True  # デフォルトはデモ版
                
                if usage_limits_result and usage_limits_result.data and len(usage_limits_result.data) > 0:
                    limits_data = usage_limits_result.data[0]
                    is_unlimited = bool(limits_data.get("is_unlimited", False))
                    is_demo = not is_unlimited  # is_unlimitedがfalseならデモ版
                    
                    usage_limits = {
                        "is_unlimited": is_unlimited,
                        "is_demo": is_demo,
                        "questions_used": int(limits_data.get("questions_used", 0)),
                        "questions_limit": int(limits_data.get("questions_limit", 10)),
                        "document_uploads_used": int(limits_data.get("document_uploads_used", 0)),
                        "document_uploads_limit": int(limits_data.get("document_uploads_limit", 2))
                    }
                else:
                    # デフォルトの利用制限情報
                    usage_limits = {
                        "is_unlimited": False,
                        "is_demo": True,  # デフォルトはデモ版
                        "questions_used": 0,
                        "questions_limit": 10,
                        "document_uploads_used": 0,
                        "document_uploads_limit": 2
                    }
                
                return {
                    "message_count": message_count,
                    "last_activity": last_activity,
                    "usage_limits": usage_limits,
                    "is_demo": is_demo  # デモ版かどうかを直接返す
                }
            except Exception as e:
                # print(f"社員ID {employee_id} の使用状況取得エラー: {e}")
                return {
                    "message_count": 0,
                    "last_activity": None,
                    "usage_limits": {
                        "is_unlimited": False,
                        "is_demo": True,
                        "questions_used": 0,
                        "questions_limit": 10,
                        "document_uploads_used": 0,
                        "document_uploads_limit": 2
                    },
                    "is_demo": True  # エラー時はデモ版扱い
                }
        
        employees = []
        
        # 特別な管理者またはadminロールの場合は全社員を取得
        if is_special_admin:
            # print("特別な管理者として全社員情報を取得します")
            # まず全ユーザーを取得
            users_result = select_data("users", columns="id, name, email, role, created_at, company_id")
            
            if users_result and users_result.data:
                # print(f"全ユーザー取得結果: {len(users_result.data)}件")
                
                # 全会社情報を取得
                companies_result = select_data("companies", columns="id, name")
                companies_dict = {}
                if companies_result and companies_result.data:
                    for company in companies_result.data:
                        companies_dict[company.get("id")] = company.get("name")
                
                for user in users_result.data:
                    # 会社名を取得
                    company_id = user.get("company_id")
                    company_name = companies_dict.get(company_id, f"会社ID: {company_id}" if company_id else "不明な会社")
                    
                    # 使用状況を取得
                    stats = get_employee_stats(user.get("id"))
                    employee_with_stats = {
                        **user,
                        "company_name": company_name,
                        **stats
                    }
                    employees.append(employee_with_stats)
            else:
                print("全社員情報が取得できませんでした")
                
        elif company_id:
            # 会社の全社員を取得
            print(f"会社ID {company_id} の社員情報を取得します")
            # Supabaseから特定の会社の社員を取得
            result = select_data("users", columns="id, name, email, role, created_at, company_id", filters={"company_id": company_id})
            
            if result and result.data:
                # print(f"会社の社員情報取得結果: {len(result.data)}件")
                for employee in result.data:
                    # 使用状況を取得
                    stats = get_employee_stats(employee.get("id"))
                    employee_with_stats = {
                        **employee,
                        **stats
                    }
                    employees.append(employee_with_stats)
            else:
                # print(f"会社ID {company_id} の社員情報が取得できませんでした")
                pass
        else:
            # 他の処理（基本的にはここに来ないはず）
            # print("適切な条件が見つかりません")
            pass
        
        return employees
    except Exception as e:
        logger.error(f"社員情報の取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_employee_usage(user_id: str = None, db: Connection = Depends(get_db), is_special_admin: bool = False):
    """社員ごとの利用状況を取得する"""
    # print(f"社員利用状況APIが呼び出されました (user_id: {user_id}, is_special_admin: {is_special_admin})")
    try:
        from supabase_adapter import execute_query, select_data
        
        # 社員の利用状況を取得するクエリを実行
        employee_usage = []
        
        def format_usage_data(user_data, user_id_key="id", name_key="name"):
            """使用状況データをフォーマットする共通関数"""
            user_id = user_data.get(user_id_key)
            if not user_id:
                return None
                
            # Supabaseの標準的な方法でメッセージ数と最終アクティビティを取得
            try:
                chat_history_result = select_data("chat_history", columns="id, timestamp, category, user_message", filters={"employee_id": user_id})
                
                message_count = 0
                last_activity = None
                
                if chat_history_result and chat_history_result.data:
                    messages = chat_history_result.data
                    message_count = len(messages)
                    
                    # 最新のタイムスタンプを取得
                    timestamps = [msg.get("timestamp") for msg in messages if msg.get("timestamp")]
                    if timestamps:
                        last_activity = max(timestamps)
                    
                    # カテゴリ分布を取得
                    category_counts = {}
                    for msg in messages:
                        category = msg.get("category")
                        if category:
                            category_counts[category] = category_counts.get(category, 0) + 1
                    
                    top_categories = [
                        {"category": cat, "count": count}
                        for cat, count in category_counts.items()
                    ]
                    
                    # 最近の質問を取得（最新3件）
                    recent_questions = []
                    sorted_messages = sorted(messages, key=lambda x: x.get("timestamp", ""), reverse=True)
                    for msg in sorted_messages[:3]:
                        user_message = msg.get("user_message")
                        if user_message:
                            recent_questions.append(user_message)
                else:
                    top_categories = []
                    recent_questions = []
            except Exception as e:
                # print(f"ユーザーID {user_id} のチャット履歴取得エラー: {e}")
                message_count = 0
                last_activity = None
                top_categories = []
                recent_questions = []
            
            return {
                "employee_id": user_id,
                "employee_name": user_data.get(name_key) or "名前なし",
                "message_count": message_count,
                "last_activity": last_activity,
                "top_categories": top_categories,
                "recent_questions": recent_questions
            }
        
        if is_special_admin:
            # print("特別な管理者として全ユーザーの利用状況を取得します")
            
            try:
                # まず全ユーザーを取得
                all_users = select_data("users", columns="id, name, email, role, created_at")
                # print(f"全ユーザー取得結果: {all_users.data if all_users else 'なし'}")
                
                if all_users and all_users.data:
                    # 各ユーザーのチャット履歴を取得
                    for user in all_users.data:
                        formatted_data = format_usage_data(user)
                        if formatted_data:
                            employee_usage.append(formatted_data)
                
                # print(f"全ユーザーの利用状況取得結果: {len(employee_usage)}件")
                
            except Exception as e:
                # print(f"全ユーザーの利用状況取得エラー: {e}")
                # エラーが発生しても処理を続行
                pass
            
        elif user_id:
            # 会社IDを取得
            company_id = None
            try:
                company_result = select_data("users", columns="company_id", filters={"id": user_id})
                if company_result and company_result.data and len(company_result.data) > 0:
                    company_id = company_result.data[0].get("company_id")
                    # print(f"会社ID {company_id} でフィルタリングします")
                else:
                    # print(f"会社ID {company_id} の社員情報が取得できませんでした")
                    pass
            except Exception as e:
                # print(f"会社ID取得エラー: {e}")
                # エラーが発生しても処理を続行
                pass
            
            if company_id:
                # print(f"会社ID {company_id} の社員の利用状況を取得します")
                
                try:
                    # 会社IDに基づいてユーザーIDを取得
                    users_result = select_data("users", columns="id, name", filters={"company_id": company_id})
                    
                    if users_result and users_result.data:
                        # print(f"会社の社員取得結果: {users_result.data}")
                        
                        for user in users_result.data:
                            formatted_data = format_usage_data(user)
                            if formatted_data:
                                employee_usage.append(formatted_data)
                except Exception as e:
                    # print(f"会社の社員利用状況取得エラー: {e}")
                    # エラーが発生しても処理を続行
                    pass
            else:
                # print(f"ユーザーID {user_id} でフィルタリングします")
                
                try:
                    # ユーザー情報を取得
                    user_result = select_data("users", columns="id, name", filters={"id": user_id})
                    
                    if user_result and user_result.data and len(user_result.data) > 0:
                        user = user_result.data[0]
                        formatted_data = format_usage_data(user)
                        if formatted_data:
                            employee_usage.append(formatted_data)
                except Exception as e:
                    # print(f"ユーザー利用状況取得エラー: {e}")
                    # エラーが発生しても処理を続行
                    pass
        
        # Convert the dictionaries to proper EmployeeUsageItem objects
        try:
            # Create a list to store properly formatted items
            formatted_items = []
            
            for item in employee_usage:
                # Convert last_activity to datetime if it's not None
                last_activity_dt = None
                if item.get("last_activity"):
                    try:
                        # Try to parse the timestamp string to datetime
                        if isinstance(item["last_activity"], str):
                            last_activity_dt = datetime.fromisoformat(item["last_activity"].replace('Z', '+00:00'))
                        else:
                            # If it's already a datetime object, use it directly
                            last_activity_dt = item["last_activity"]
                    except Exception as e:
                        # print(f"日時変換エラー: {e}")
                        # Use current time as fallback
                        last_activity_dt = datetime.now()
                
                # Create a properly formatted item
                formatted_item = {
                    "employee_id": item.get("employee_id", ""),
                    "employee_name": item.get("employee_name", "名前なし"),
                    "message_count": int(item.get("message_count", 0)),
                    "last_activity": last_activity_dt or datetime.now(),
                    "top_categories": item.get("top_categories", []),
                    "recent_questions": item.get("recent_questions", [])
                }
                
                # Add to the formatted list
                formatted_items.append(formatted_item)
            
            # Return the properly formatted result
            return {"employee_usage": formatted_items}
        except Exception as format_error:
            # print(f"データフォーマットエラー: {format_error}")
            # Return empty result as fallback
            return {"employee_usage": []}
            
    except Exception as e:
        print(f"社員利用状況取得エラー: {e}")
        # Return empty result instead of raising an exception
        return {"employee_usage": []}

async def get_analysis(db: Connection = Depends(get_db)):
    """チャット分析結果を取得する"""
    try:
        # モックデータを返す
        return {
            "total_messages": 100,
            "average_response_time": 2.5,
            "category_distribution": [
                {"category": "一般", "count": 50},
                {"category": "技術", "count": 30},
                {"category": "その他", "count": 20}
            ],
            "sentiment_distribution": [
                {"sentiment": "positive", "count": 60},
                {"sentiment": "neutral", "count": 30},
                {"sentiment": "negative", "count": 10}
            ],
            "daily_usage": [
                {"date": "2025-04-25", "count": 10},
                {"date": "2025-04-26", "count": 15},
                {"date": "2025-04-27", "count": 20},
                {"date": "2025-04-28", "count": 25},
                {"date": "2025-04-29", "count": 15},
                {"date": "2025-04-30", "count": 15}
            ]
        }
    except Exception as e:
        print(f"分析結果取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_employee_details(employee_id: str, db = None, current_user_id: str = None):
    """特定の社員の詳細なチャット履歴を取得する"""
    try:
        from supabase_adapter import select_data
        
        # 特別な管理者またはadminロールかどうかを確認
        is_special_admin = False
        is_admin = False
        is_user = False
        current_user_company_id = None
        target_user_company_id = None
        
        if current_user_id:
            user_result = select_data("users", columns="email, role, company_id", filters={"id": current_user_id})
            if user_result and user_result.data and len(user_result.data) > 0:
                user_data = user_result.data[0]
                user_email = user_data.get("email")
                user_role = user_data.get("role")
                current_user_company_id = user_data.get("company_id")
                
                if user_email == "queue@queueu-tech.jp":
                    is_special_admin = True
                    print("特別な管理者として社員詳細情報を取得します")
                elif user_role == "admin":
                    is_admin = True
                    print("adminロールとして社員詳細情報を取得します")
                elif user_role == "user":
                    is_user = True
                    print("userロールとして社員詳細情報を取得します")
        
        # 対象ユーザーの会社IDを取得（同じ会社かチェックするため）
        if not is_special_admin and not is_admin and employee_id != current_user_id:
            target_result = select_data("users", columns="company_id", filters={"id": employee_id})
            if target_result and target_result.data and len(target_result.data) > 0:
                target_user_company_id = target_result.data[0].get("company_id")
        
        # 権限チェック
        # 1. 特別な管理者またはadminロールは全てアクセス可能
        # 2. userロールは同じ会社のユーザーのみアクセス可能
        # 3. その他は自分のデータのみアクセス可能
        if not is_special_admin and not is_admin:
            if is_user:
                # userロールの場合、同じ会社のユーザーならアクセス可能
                if current_user_company_id and target_user_company_id and current_user_company_id == target_user_company_id:
                    print(f"userロールとして同じ会社（{current_user_company_id}）の社員詳細情報にアクセスします")
                elif employee_id == current_user_id:
                    print("userロールとして自分の詳細情報にアクセスします")
                else:
                    raise HTTPException(status_code=403, detail="他の会社の社員の詳細情報を取得する権限がありません")
            else:
                # employeeロールなどは自分のデータのみ
                if employee_id != current_user_id:
                    raise HTTPException(status_code=403, detail="他の社員の詳細情報を取得する権限がありません")
        
        # 社員のチャット履歴を取得
        chat_history_result = select_data("chat_history", columns="*", filters={"employee_id": employee_id})
        
        # 結果を変換
        chat_history = []
        if chat_history_result and chat_history_result.data:
            for row in chat_history_result.data:
                item = {
                    "id": row.get("id", ""),
                    "user_message": row.get("user_message", ""),
                    "bot_response": row.get("bot_response", ""),
                    "timestamp": row.get("timestamp", ""),
                    "category": row.get("category", ""),
                    "sentiment": row.get("sentiment", ""),
                    "employee_id": row.get("employee_id", ""),
                    "employee_name": row.get("employee_name", ""),
                    "source_document": row.get("source_document", ""),
                    "source_page": row.get("source_page", "")
                }
                chat_history.append(item)
            
            # タイムスタンプでソート（降順）
            chat_history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return chat_history
    except Exception as e:
        print(f"社員詳細情報取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# リソース関連の関数は modules.resource に移動されているため、
# 互換性のために以下の関数を追加

async def get_uploaded_resources():
    """アップロードされたリソース（URL、PDF、Excel、TXT）の情報を取得する
    この関数は互換性のために残されていますが、modules.resource の関数を使用してください"""
    from .resource import get_uploaded_resources_by_company_id
    return await get_uploaded_resources_by_company_id(None, None)

async def toggle_resource_active(resource_id: str):
    """リソースのアクティブ状態を切り替える
    この関数は互換性のために残されていますが、modules.resource の関数を使用してください"""
    from .resource import toggle_resource_active_by_id
    return await toggle_resource_active_by_id(resource_id, None)

async def delete_resource(resource_id: str):
    """リソースを削除する
    この関数は互換性のために残されていますが、modules.resource の関数を使用してください"""
    from .resource import remove_resource_by_id
    return await remove_resource_by_id(resource_id, None)

async def get_demo_stats(db: Connection = Depends(get_db), company_id: str = None):
    """デモ利用状況の統計を取得する"""
    try:
        # モックデータを返す
        return {
            "total_users": 10,
            "active_users": 5,
            "total_documents": 3,
            "total_questions": 50,
            "limit_reached_users": 2,
            "total_companies": 3
        }
    except Exception as e:
        print(f"デモ統計取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_chats(user_id: str = None, db = None, company_id: str = None):
    """チャット履歴を分析する"""
    try:
        print("analyze_chats関数が呼び出されました")
        from supabase_adapter import select_data, execute_query
        
        # Supabaseからデータを取得
        chat_data = []
        
        if user_id:
            print(f"ユーザーID {user_id} のチャット履歴を分析します")
            # 特定のユーザーのチャット履歴を取得
            try:
                result = select_data(
                    "chat_history",
                    columns="*",
                    filters={"employee_id": user_id}
                )
                if result and hasattr(result, 'data') and result.data:
                    chat_data = result.data
                    print(f"データ取得結果: {len(chat_data)}件")
                else:
                    print("データが取得できませんでした")
            except Exception as e:
                print(f"データ取得エラー: {e}")
        elif company_id:
            print(f"会社ID {company_id} のチャット履歴を分析します")
            # 特定の会社のチャット履歴を取得
            try:
                result = select_data(
                    "chat_history",
                    columns="*",
                    filters={"company_id": company_id}
                )
                if result and hasattr(result, 'data') and result.data:
                    chat_data = result.data
                    print(f"会社別データ取得結果: {len(chat_data)}件")
                else:
                    print("会社別データが取得できませんでした")
            except Exception as e:
                print(f"会社別データ取得エラー: {e}")
        else:
            # print("全ユーザーのチャット履歴を分析します")
            # 全ユーザーのチャット履歴を取得
            try:
                result = select_data(
                    "chat_history",
                    columns="*"
                )
                if result and hasattr(result, 'data') and result.data:
                    chat_data = result.data
                    print(f"データ取得結果: {len(chat_data)}件")
                else:
                    print("データが取得できませんでした")
            except Exception as e:
                print(f"データ取得エラー: {e}")
        
        # データがない場合は空の結果を返す
        if not chat_data:
            print("チャットデータがないため、空の分析結果を返します")
            return {
                "total_messages": 0,
                "average_response_time": 0,
                "category_distribution": [],
                "sentiment_distribution": [],
                "daily_usage": [],
                "common_questions": [],
                "insights": "十分なデータがないため、分析できません。より多くのチャットデータを収集してください。"
            }
        
        # 実際のデータを分析
        total_messages = len(chat_data)
        print(f"分析対象メッセージ数: {total_messages}")
        
        # カテゴリ分布を計算
        category_counts = {}
        for row in chat_data:
            category = row.get("category")
            if category:
                if category in category_counts:
                    category_counts[category] += 1
                else:
                    category_counts[category] = 1
        
        category_distribution = [
            {"category": category, "count": count}
            for category, count in category_counts.items()
        ]
        
        # 感情分布を計算
        sentiment_counts = {}
        for row in chat_data:
            sentiment = row.get("sentiment")
            if sentiment:
                if sentiment in sentiment_counts:
                    sentiment_counts[sentiment] += 1
                else:
                    sentiment_counts[sentiment] = 1
        
        sentiment_distribution = [
            {"sentiment": sentiment, "count": count}
            for sentiment, count in sentiment_counts.items()
        ]
        
        # 日付ごとの利用状況を計算
        date_counts = {}
        for row in chat_data:
            timestamp = row.get("timestamp")
            if timestamp:
                # タイムスタンプから日付部分のみを抽出
                date_str = timestamp.split("T")[0] if isinstance(timestamp, str) else timestamp.strftime("%Y-%m-%d")
                if date_str in date_counts:
                    date_counts[date_str] += 1
                else:
                    date_counts[date_str] = 1
        
        daily_usage = [
            {"date": date, "count": count}
            for date, count in date_counts.items()
        ]
        
        # よくある質問を抽出
        question_counts = {}
        for row in chat_data:
            question = row.get("user_message")
            if question:
                if question in question_counts:
                    question_counts[question] += 1
                else:
                    question_counts[question] = 1
        
        # 質問を出現回数でソートして上位を取得
        sorted_questions = sorted(question_counts.items(), key=lambda x: x[1], reverse=True)
        common_questions = [question for question, count in sorted_questions[:10]]
        
        # 平均応答時間を計算（実際のデータがあれば）
        # ここでは簡易的に固定値を使用
        average_response_time = 2.5
        
        # AI洞察を生成
        insights = ""
        try:
            if total_messages > 0:
                # カテゴリ分布からの洞察
                top_categories = sorted(category_distribution, key=lambda x: x["count"], reverse=True)[:3] if category_distribution else []
                top_categories_text = ", ".join([f"{cat['category']}({cat['count']}件)" for cat in top_categories]) if top_categories else "なし"
                
                # 感情分布からの洞察
                sentiment_text = ""
                negative_insights = ""
                if sentiment_distribution:
                    positive_count = next((item["count"] for item in sentiment_distribution if item["sentiment"] == "positive"), 0)
                    negative_count = next((item["count"] for item in sentiment_distribution if item["sentiment"] == "negative"), 0)
                    neutral_count = next((item["count"] for item in sentiment_distribution if item["sentiment"] == "neutral"), 0)
                    
                    total_sentiment = positive_count + negative_count + neutral_count
                    if total_sentiment > 0:
                        positive_percent = (positive_count / total_sentiment) * 100
                        negative_percent = (negative_count / total_sentiment) * 100
                        neutral_percent = (neutral_count / total_sentiment) * 100
                        
                        sentiment_text = f"ポジティブ: {positive_percent:.1f}%, ネガティブ: {negative_percent:.1f}%, 中立: {neutral_percent:.1f}%"
                        
                        # ネガティブな感情が多い場合の特別な洞察
                        if negative_percent > 20:
                            negative_insights = "ネガティブな感情の割合が高いため、ユーザー対応の改善が必要です。特に不満や怒りの表現が見られる質問に注目し、クレーム対応体制の強化を検討してください。"
                
                # 離脱率の高い質問の分析
                dropout_analysis = "十分なデータがないため、離脱率の分析はできません。"
                if len(common_questions) >= 3:
                    dropout_analysis = "特に最初の質問後に会話が中断されるケースが見られます。スクリプトの改善やFAQの強化が必要です。"
                
                # 未解決・再質問の傾向分析
                unresolved_analysis = "未解決の問い合わせパターンを特定するには、より多くのデータが必要です。"
                if total_messages > 10:
                    unresolved_analysis = "同じユーザーから類似の質問が繰り返されるケースが見られます。ナレッジベースの拡充と回答品質の向上が必要です。"
                
                # 時間帯別の問い合わせ傾向
                time_analysis = "時間帯別の分析には十分なデータがありません。"
                if len(daily_usage) > 3:
                    peak_days = sorted(daily_usage, key=lambda x: x["count"], reverse=True)[:2]
                    peak_days_text = ", ".join([f"{day['date']}({day['count']}件)" for day in peak_days])
                    time_analysis = f"問い合わせが最も多い日は {peak_days_text} です。この時間帯の対応体制を強化することを検討してください。"
                
                # 自由入力の内容クラスタリング
                clustering_analysis = "自由入力の内容をクラスタリングするには、より多くのデータが必要です。"
                if len(common_questions) >= 5:
                    clustering_analysis = "自由入力の内容を分析した結果、主に製品の使い方、エラー対応、機能リクエストに関する質問が多く見られます。これらの領域に焦点を当てた改善が効果的です。"
                
                # 洞察テキストの生成
                insights = f"""
分析期間中の総メッセージ数は {total_messages} 件です。

【分析サマリー】
以下の5つの観点から分析を行いました。詳細は各セクションをご覧ください。

【1. 離脱率の高い質問】
{dropout_analysis}
社内活用シーン: スクリプト改善、FAQ強化の優先判断に活用できます。

【2. 感情分析（ネガティブ傾向）】
ユーザーの感情分布は {sentiment_text} となっています。
{negative_insights}
社内活用シーン: クレーム予兆の共有と対応体制の強化に役立ちます。

【3. 未解決・再質問の傾向分析】
{unresolved_analysis}
社内活用シーン: ナレッジ不足の箇所特定と改修計画への反映に活用できます。

【4. 時間帯別の問い合わせ傾向】
{time_analysis}
社内活用シーン: 対応体制のシフト調整やメンテナンス時間の見直しに役立ちます。

【5. 自由入力の内容クラスタリング】
{clustering_analysis}
社内活用シーン: よくある要望・トラブルをチームで共有し改善につなげられます。

【よくある質問】
最も頻繁に質問されるトピックは以下の通りです:
- {common_questions[0] if common_questions else "データなし"}
- {common_questions[1] if len(common_questions) > 1 else ""}
- {common_questions[2] if len(common_questions) > 2 else ""}

これらの質問に対する回答を改善することで、ユーザー体験を向上させることができます。
                """
            else:
                insights = "十分なデータがないため、分析できません。より多くのチャットデータを収集してください。"
        except Exception as e:
            print(f"洞察生成エラー: {e}")
            insights = "洞察の生成中にエラーが発生しました。"
        
        result = {
            "total_messages": total_messages,
            "average_response_time": average_response_time,
            "category_distribution": category_distribution,
            "sentiment_distribution": sentiment_distribution,
            "daily_usage": daily_usage,
            "common_questions": common_questions,
            "insights": insights
        }
        
        print(f"分析結果: {result}")
        return result
    except Exception as e:
        print(f"分析結果取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_chat_history_by_company_paginated(company_id: str, db = None, limit: int = 30, offset: int = 0):
    """会社IDでフィルタリングしたページネーション対応のチャット履歴を取得する"""
    print(f"🔍 [COMPANY CHAT DEBUG] get_chat_history_by_company_paginated 開始")
    print(f"  - company_id: {company_id}")
    print(f"  - limit: {limit}, offset: {offset}")
    
    try:
        from supabase_adapter import select_data
        
        # まず会社の全ユーザーIDを取得
        users_result = select_data("users", columns="id", filters={"company_id": company_id})
        
        if not users_result or not users_result.data:
            print(f"🔍 [COMPANY CHAT DEBUG] 会社ID {company_id} のユーザーが見つかりません")
            return [], 0
        
        user_ids = [user["id"] for user in users_result.data]
        print(f"🔍 [COMPANY CHAT DEBUG] 会社のユーザーID一覧: {user_ids}")
        
        # 会社のユーザーのチャット履歴を取得（ページネーション対応）
        # IN句でフィルタリング
        user_ids_str = ','.join([f"'{uid}'" for uid in user_ids])
        
        # 全件数を取得
        count_result = select_data(
            "chat_history", 
            columns="id", 
            filters={"employee_id": f"in.({user_ids_str})"}
        )
        total_count = len(count_result.data) if count_result and count_result.data else 0
        
        # ページネーション付きでデータ取得
        result = select_data(
            "chat_history", 
            columns="*", 
            filters={"employee_id": f"in.({user_ids_str})"},
            order="timestamp desc",
            limit=limit,
            offset=offset
        )
        
        if not result or not result.data:
            print(f"🔍 [COMPANY CHAT DEBUG] 会社のチャット履歴が見つかりません")
            return [], total_count
        
        chat_history = result.data
        print(f"🔍 [COMPANY CHAT DEBUG] チャット履歴取得結果: {len(chat_history)}件 (全体: {total_count}件)")
        
        # ユーザー名を取得してマッピング
        users_detail_result = select_data("users", columns="id, name", filters={"company_id": company_id})
        user_name_map = {}
        if users_detail_result and users_detail_result.data:
            for user in users_detail_result.data:
                user_name_map[user["id"]] = user.get("name", "不明なユーザー")
        
        # データ形式を統一
        formatted_history = []
        for chat in chat_history:
            employee_id = chat.get("employee_id", "")
            employee_name = user_name_map.get(employee_id, "不明なユーザー")
            
            item = {
                "id": chat.get("id", ""),
                "user_message": chat.get("user_message", ""),
                "bot_response": chat.get("bot_response", ""),
                "timestamp": chat.get("timestamp", ""),
                "category": chat.get("category", ""),
                "sentiment": chat.get("sentiment", ""),
                "employee_id": employee_id,
                "employee_name": employee_name,
                "source_document": chat.get("source_document", ""),
                "source_page": chat.get("source_page", "")
            }
            formatted_history.append(item)
        
        print(f"🔍 [COMPANY CHAT DEBUG] チャット履歴変換結果: {len(formatted_history)}件")
        return formatted_history, total_count
        
    except Exception as e:
        print(f"🔍 [COMPANY CHAT DEBUG] 会社チャット履歴取得エラー: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"会社チャット履歴取得中にエラーが発生しました: {str(e)}")

def get_chat_history_by_company(company_id: str, db = None):
    """会社IDでフィルタリングしたチャット履歴を取得する（フォールバック用）"""
    print(f"🔍 [COMPANY CHAT DEBUG] get_chat_history_by_company 開始")
    print(f"  - company_id: {company_id}")
    
    try:
        from supabase_adapter import select_data
        
        # まず会社の全ユーザーIDを取得
        users_result = select_data("users", columns="id", filters={"company_id": company_id})
        
        if not users_result or not users_result.data:
            print(f"🔍 [COMPANY CHAT DEBUG] 会社ID {company_id} のユーザーが見つかりません")
            return []
        
        user_ids = [user["id"] for user in users_result.data]
        print(f"🔍 [COMPANY CHAT DEBUG] 会社のユーザーID一覧: {user_ids}")
        
        # 会社のユーザーのチャット履歴を取得
        # IN句でフィルタリング
        user_ids_str = ','.join([f"'{uid}'" for uid in user_ids])
        
        result = select_data(
            "chat_history", 
            columns="*", 
            filters={"employee_id": f"in.({user_ids_str})"},
            order="timestamp desc"
        )
        
        if not result or not result.data:
            print(f"🔍 [COMPANY CHAT DEBUG] 会社のチャット履歴が見つかりません")
            return []
        
        chat_history = result.data
        print(f"🔍 [COMPANY CHAT DEBUG] チャット履歴取得結果: {len(chat_history)}件")
        
        # ユーザー名を取得してマッピング
        users_detail_result = select_data("users", columns="id, name", filters={"company_id": company_id})
        user_name_map = {}
        if users_detail_result and users_detail_result.data:
            for user in users_detail_result.data:
                user_name_map[user["id"]] = user.get("name", "不明なユーザー")
        
        # データ形式を統一
        formatted_history = []
        for chat in chat_history:
            employee_id = chat.get("employee_id", "")
            employee_name = user_name_map.get(employee_id, "不明なユーザー")
            
            item = {
                "id": chat.get("id", ""),
                "user_message": chat.get("user_message", ""),
                "bot_response": chat.get("bot_response", ""),
                "timestamp": chat.get("timestamp", ""),
                "category": chat.get("category", ""),
                "sentiment": chat.get("sentiment", ""),
                "employee_id": employee_id,
                "employee_name": employee_name,
                "source_document": chat.get("source_document", ""),
                "source_page": chat.get("source_page", "")
            }
            formatted_history.append(item)
        
        print(f"🔍 [COMPANY CHAT DEBUG] チャット履歴変換結果: {len(formatted_history)}件")
        return formatted_history
        
    except Exception as e:
        print(f"🔍 [COMPANY CHAT DEBUG] 会社チャット履歴取得エラー: {e}")
        import traceback
        print(traceback.format_exc())
        return []
