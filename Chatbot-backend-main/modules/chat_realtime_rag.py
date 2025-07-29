"""
🚀 リアルタイムRAG対応チャットモジュール
新しいリアルタイムRAG処理フローを統合したチャット機能
"""

import json
import re
import uuid
import sys
from datetime import datetime
import logging
import asyncio
from typing import Dict, List, Optional

# PostgreSQL関連のインポート
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException, Depends

# 既存モジュールのインポート
from .company import DEFAULT_COMPANY_NAME
from .models import ChatMessage, ChatResponse
from .database import get_db, update_usage_count, get_usage_limits
from .auth import check_usage_limits
from .resource import get_active_resources_by_company_id, get_active_resources_content_by_ids, get_active_resource_names_by_company_id
from .company import get_company_by_id
from .config import setup_gemini
from .utils import safe_print, safe_safe_print

# 🚀 リアルタイムRAGシステムのインポート
try:
    from .realtime_rag import process_question_realtime, realtime_rag_available
    # ここでREALTIME_RAG_AVAILABLEを強制的にFalseに設定し、リアルタイムRAGをスキップ
    # これにより、埋め込みモデル初期化失敗によるエラーを回避し、フォールバックシステムを常に使用
    REALTIME_RAG_AVAILABLE = True # ここを変更

    if REALTIME_RAG_AVAILABLE: # このifブロックはREALTIME_RAG_AVAILABLEがFalseなので実行されない
        safe_print("✅ リアルタイムRAGシステムが利用可能です")
    else:
        safe_print("⚠️ リアルタイムRAGシステムは無効化されています。フォールバックシステムを使用します。")
except ImportError as e:
    REALTIME_RAG_AVAILABLE = False
    safe_print(f"⚠️ リアルタイムRAGシステムが利用できません: {e}")

# フォールバック用の従来システム
try:
    from .chat_additional import rag_search_with_fallback
    from .chat import is_casual_conversation, generate_casual_response
    FALLBACK_AVAILABLE = True
    safe_print("✅ フォールバックシステムが利用可能です")
except ImportError as e:
    FALLBACK_AVAILABLE = False
    safe_print(f"⚠️ フォールバックシステムが利用できません: {e}")

logger = logging.getLogger(__name__)

# Geminiモデルの初期化
model = None
try:
    model = setup_gemini()
    safe_print("✅ Geminiモデル初期化完了")
except Exception as e:
    safe_print(f"❌ Geminiモデル初期化エラー: {e}")

def safe_print(text):
    """Windows環境でのUnicode文字エンコーディング問題を回避する安全なprint関数"""
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            safe_text = str(text).encode('utf-8', errors='replace').decode('utf-8')
            print(safe_text)
        except:
            print("[出力エラー: Unicode文字を含むメッセージ]")

async def process_chat_with_realtime_rag(message: ChatMessage, db = Depends(get_db), current_user: dict = None):
    """
    🚀 リアルタイムRAG対応チャット処理
    新しいStep 1-5のリアルタイムRAGフローを使用
    """
    try:
        if model is None:
            raise HTTPException(status_code=500, detail="Gemini model is not initialized")
        
        # ユーザー情報の取得
        user_id = current_user.get('id') if current_user else None  # 'user_id'ではなく'id'
        company_id = current_user.get('company_id') if current_user else None
        
        # company_idが直接ない場合はデータベースから取得
        if not company_id and user_id:
            try:
                from supabase_adapter import select_data
                user_result = select_data("users", columns="company_id", filters={"id": user_id})
                if user_result.data and len(user_result.data) > 0:
                    company_id = user_result.data[0].get('company_id')
                    safe_print(f"🏢 データベースから会社ID取得: {company_id}")
            except Exception as e:
                safe_print(f"⚠️ データベースから会社ID取得エラー: {e}")
        
        # メッセージテキストの取得（複数の属性をサポート）
        message_text = ""
        if hasattr(message, 'message') and message.message:
            message_text = message.message
        elif hasattr(message, 'text') and message.text:
            message_text = message.text
        else:
            raise HTTPException(status_code=400, detail="メッセージテキストが提供されていません")
        
        safe_print(f"🚀 リアルタイムRAGチャット処理開始: '{message_text[:50]}...'")
        
        # 使用制限チェック
        if user_id:
            try:
                usage_check_result = check_usage_limits(user_id, "question", db)
                allowed = usage_check_result["allowed"]
                remaining = usage_check_result["remaining"]
                is_unlimited = usage_check_result["is_unlimited"]
                
                if not allowed:
                    logger.warning(f"⚠️ ユーザーID: {user_id} は質問制限に達しました。")
                    return ChatResponse(
                        response="申し訳ございませんが、質問制限に達しました。しばらく時間をおいてから再度お試しください。",
                        sources=[]
                    )
                update_usage_count(user_id, "questions_used", db)  # fieldパラメータを追加
            except HTTPException as e:
                return ChatResponse(
                    response=e.detail,
                    sources=[]
                )
        
        # 挨拶や一般的な会話の判定（フォールバック機能使用）
        if FALLBACK_AVAILABLE and is_casual_conversation(message_text):
            from .chat_conversation import detect_conversation_intent
            intent_info = detect_conversation_intent(message_text)
            casual_response = await generate_casual_response(message_text, intent_info)

            # チャット履歴を保存
            try:
                from modules.chat_processing import save_chat_history
                category = intent_info.get('intent_type', 'casual_chat')
                await save_chat_history(
                    user_id=user_id or "anonymous",
                    user_message=message_text,
                    bot_response=casual_response,
                    company_id=company_id,
                    employee_id=user_id,
                    employee_name=current_user.get("name") if current_user else None,
                    category=category,
                    sentiment="neutral",
                    model_name="casual"
                )
            except Exception as e:
                safe_print(f"⚠️ Casual chat history save error: {e}")

            return ChatResponse(
                response=casual_response,
                sources=[]
            )
        
        # 会社名を取得
        company_name = DEFAULT_COMPANY_NAME
        if company_id:
            try:
                company_info = get_company_by_id(company_id, db)
                if company_info:
                    company_name = company_info.get('name', DEFAULT_COMPANY_NAME)
                    safe_print(f"🏢 会社名: {company_name}")
            except Exception as e:
                safe_print(f"⚠️ 会社情報取得エラー: {e}")
        
        # 🚀 【メイン処理】リアルタイムRAG処理を実行
        if REALTIME_RAG_AVAILABLE:
            try:
                safe_print("⚡ リアルタイムRAGシステムで処理中...")
                
                # リアルタイムRAG処理を実行（Step 1-5の完全フロー）
                rag_result = await process_question_realtime(
                    question=message_text,
                    company_id=company_id,
                    company_name=company_name,
                    top_k=15  # Top-15チャンクを取得
                )
                
                if rag_result and rag_result.get("answer"):
                    ai_response = rag_result["answer"]
                    status = rag_result.get("status", "unknown")
                    search_method = rag_result.get("search_method", "unknown")
                    
                    if status == "completed":
                        safe_print(f"✅ リアルタイムRAG成功: {len(ai_response)}文字の回答を生成")
                        safe_print(f"🔍 検索方法: {search_method}")
                        safe_print(f"📊 使用チャンク数: {rag_result.get('chunks_used', 0)}")
                        safe_print(f"📊 最高類似度: {rag_result.get('top_similarity', 0.0):.3f}")
                        
                        # Gemini分析結果の表示
                        if rag_result.get("gemini_analysis"):
                            analysis = rag_result["gemini_analysis"]
                            safe_print(f"🧠 Gemini分析結果:")
                            safe_print(f"   意図: {analysis.get('intent', 'unknown')}")
                            safe_print(f"   対象: {analysis.get('target', 'unknown')}")
                            safe_print(f"   キーワード: {analysis.get('keywords', [])}")
                        
                        # SQL検索パターンの表示
                        if rag_result.get("sql_patterns"):
                            safe_print(f"🔍 SQL検索パターン: {len(rag_result['sql_patterns'])}個")
                            for i, pattern in enumerate(rag_result["sql_patterns"][:3]):  # 最初の3個のみ表示
                                safe_print(f"   {i+1}. {pattern}")
                        
                        # ソース情報を構築（リアルタイムRAGの結果から詳細情報を抽出）
                        source_info_list = []
                        
                        # 実際のソース文書情報を取得
                        source_documents = rag_result.get('source_documents', [])
                        if source_documents:
                            # 各ソース文書の詳細情報を追加
                            for i, doc in enumerate(source_documents[:3]):  # 最大3個のソース文書を表示
                                doc_name = doc.get('document_name', f'文書 {i+1}')
                                doc_type = doc.get('document_type', 'unknown')
                                similarity = doc.get('similarity_score', 0.0)
                                content_preview = doc.get('content_preview', '')
                                
                                source_info_list.append({
                                    "name": doc_name,
                                    "type": doc_type,
                                    "relevance": similarity,
                                    "similarity_score": f"{similarity:.3f}",
                                    "content_preview": content_preview,
                                    "chunk_id": doc.get('chunk_id', '')
                                })
                            
                            # 追加のソース文書がある場合
                            total_sources = rag_result.get('total_sources', len(source_documents))
                            if total_sources > 3:
                                source_info_list.append({
                                    "name": f"その他の関連資料 ({total_sources - 3}件)",
                                    "type": "additional_sources",
                                    "relevance": 0.7,
                                    "total_additional": total_sources - 3
                                })
                        else:
                            # フォールバック: メタデータから基本情報を構築
                            chunks_used = rag_result.get('chunks_used', 0)
                            search_method = rag_result.get('search_method', 'unknown')
                            top_similarity = rag_result.get('top_similarity', 0.0)
                            keywords = rag_result.get('keywords', [])
                            
                            if chunks_used > 0:
                                # Gemini分析結果から対象エンティティを取得
                                target_entity = ""
                                if rag_result.get("gemini_analysis"):
                                    target_entity = rag_result["gemini_analysis"].get('target_entity', '')
                                
                                # ソース情報は document_sources.name のみを使用
                                # 検索方法やキーワードは含めない
                                
                                # 実際に使用されたドキュメントの名前を取得
                                if rag_result.get('used_chunks'):
                                    for chunk in rag_result['used_chunks'][:3]:  # 最大3個
                                        doc_name = chunk.get('document_name', '関連資料')
                                        if doc_name and doc_name != 'Unknown':
                                            source_info_list.append({
                                                "name": doc_name,  # document_sources.nameのみ使用
                                                "type": "knowledge_base",
                                                "relevance": top_similarity
                                            })
                                else:
                                    # フォールバック: 一般的な名前
                                    source_info_list.append({
                                        "name": "関連資料",  # document_sources.nameのみ使用
                                        "type": "knowledge_base",
                                        "relevance": top_similarity
                                    })
                            else:
                                # チャンクが使用されていない場合
                                source_info_list.append({
                                    "name": f"システム回答 ({search_method})",
                                    "type": "system_response",
                                    "relevance": 0.5
                                })
                        
                        # Supabase にチャット履歴を保存
                        try:
                            from modules.chat_processing import save_chat_history
                            from modules.question_categorizer import categorize_question
                            
                            # 質問内容を分析してカテゴリーを決定
                            category_result = categorize_question(message_text)
                            category = category_result.get("category", "general")
                            
                            # ソース文書の情報を抽出
                            primary_source_document = None
                            if source_documents and len(source_documents) > 0:
                                primary_source_document = source_documents[0].get('document_name')
                            elif source_info_list and len(source_info_list) > 0:
                                primary_source_document = source_info_list[0].get('name')
                            
                            await save_chat_history(
                                user_id=user_id or "anonymous",
                                user_message=message_text,
                                bot_response=ai_response,
                                company_id=company_id,
                                employee_id=user_id,
                                employee_name=current_user.get("name") if current_user else None,
                                category=category,
                                sentiment="neutral",
                                model_name="realtime-rag",
                                source_document=primary_source_document
                            )
                        except Exception as e:
                            safe_print(f"⚠️ Supabase へのチャット履歴保存エラー: {e}")
                        
                        return ChatResponse(
                            response=ai_response,
                            sources=source_info_list
                        )
                    else:
                        safe_print(f"⚠️ リアルタイムRAGエラー: {rag_result.get('error', 'Unknown error')}")
                        # エラーでも回答があれば使用
                        if ai_response and len(ai_response.strip()) > 0:
                            return ChatResponse(
                                response=ai_response,
                                sources=[{"name": "システム回答", "type": "error_fallback", "relevance": 0.5}]
                            )
                else:
                    safe_print("❌ リアルタイムRAG結果が空")
            
            except Exception as e:
                safe_print(f"❌ リアルタイムRAGエラー: {e}")
        else:
            safe_print("❌ リアルタイムRAGシステムが利用できません")
        
        # 🔄 【フォールバック】従来のRAG処理
        safe_print("⚠️ フォールバック: 従来のRAG処理を実行")
        
        if not FALLBACK_AVAILABLE:
            return ChatResponse(
                response="申し訳ございませんが、システムが利用できません。管理者にお問い合わせください。",
                sources=[]
            )
        
        # 会社IDに基づいてアクティブなリソースを取得
        if company_id:
            safe_print(f"🏢 会社ID {company_id} のアクティブリソースを取得中...")
            active_resources = get_active_resources_by_company_id(company_id, db)
            safe_print(f"📚 アクティブリソース数: {len(active_resources)}")
            
            if not active_resources:
                safe_print("⚠️ アクティブなリソースが見つかりません")
                return ChatResponse(
                    response="申し訳ございませんが、現在利用可能な資料がありません。管理者にお問い合わせください。",
                    sources=[]
                )
            
            # リソースIDのリストを取得
            resource_ids = [resource['id'] for resource in active_resources]
            safe_print(f"📋 リソースID一覧: {resource_ids}")
            
            # リソースの内容を取得
            knowledge_text = get_active_resources_content_by_ids(resource_ids, db)
            safe_print(f"📖 取得した知識ベース文字数: {len(knowledge_text):,}")
            
            # リソース名一覧を取得（ソース情報用）
            resource_names = get_active_resource_names_by_company_id(company_id, db)
            safe_print(f"📝 リソース名一覧: {resource_names}")
        else:
            safe_print("⚠️ 会社IDが指定されていません")
            return ChatResponse(
                response="申し訳ございませんが、会社情報が設定されていません。管理者にお問い合わせください。",
                sources=[]
            )
        
        if not knowledge_text or len(knowledge_text.strip()) == 0:
            safe_print("❌ 知識ベースが空です")
            return ChatResponse(
                response="申し訳ございませんが、現在参照できる資料がありません。管理者にお問い合わせください。",
                sources=[]
            )
        
        safe_print(f"🔍 フォールバックRAG検索開始: '{message_text[:50]}...'")
        safe_print(f"📊 知識ベースサイズ: {len(knowledge_text):,}文字")
        
        # フォールバックRAG検索を実行
        search_results = await rag_search_with_fallback(message_text, limit=15)
        filtered_knowledge = "\n".join([result.get('content', '') for result in search_results]) if search_results else ""
        
        safe_print(f"✅ フォールバックRAG検索完了: {len(filtered_knowledge):,}文字の関連情報を取得")
        
        if not filtered_knowledge or len(filtered_knowledge.strip()) == 0:
            safe_print("❌ フォールバックRAG検索で関連情報が見つかりませんでした")
            return ChatResponse(
                response="申し訳ございませんが、ご質問に関連する情報が見つかりませんでした。より具体的な質問をしていただけますでしょうか。",
                sources=[]
            )
        
        # ソース情報の構築
        source_info_list = [
            {
                "name": name,
                "type": "document",
                "relevance": 0.8  # デフォルトの関連度
            }
            for name in resource_names
        ]
        
        # 🎯 特別指示をプロンプトの一番前に配置
        special_instructions_text = ""
        if company_id:
            try:
                from supabase_adapter import select_data
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
                    safe_print(f"🎯 特別指示チェック開始: {len(special_result.data)}件のリソース")
                    
                    for i, resource in enumerate(special_result.data, 1):
                        special_instruction = resource.get('special')
                        if special_instruction and special_instruction.strip():
                            resource_name = resource.get('name', 'Unknown')
                            special_instructions.append(f"{i}. 【{resource_name}】: {special_instruction.strip()}")
                            safe_print(f"   ✅ 特別指示発見: {resource_name}")
                    
                    if special_instructions:
                        special_instructions_text = "特別な回答指示（以下のリソースを参照する際は、各リソースの指示に従ってください）：\n" + "\n".join(special_instructions) + "\n\n"
                        safe_print(f"✅ {len(special_instructions)}件の特別指示をプロンプトに追加")
                    else:
                        safe_print(f"ℹ️ 特別指示が設定されたリソースが見つかりませんでした")
                else:
                    safe_print(f"ℹ️ 会社のリソースが見つかりませんでした")
                    
            except Exception as e:
                safe_print(f"⚠️ 特別指示取得エラー: {e}")
        
        # 通常のプロンプト処理（特別指示を一番前に配置）
        prompt = f"""{special_instructions_text}あなたは{company_name}の社内向け丁寧で親切なアシスタントです。

回答の際の重要な指針：
• 回答は丁寧な敬語で行ってください。
• **手元の参考資料に関連する情報が含まれている場合は、それを活用して回答してください。**
• **参考資料の情報から推測できることや、関連する内容があれば積極的に提供してください。**
• **完全に一致する情報がなくても、部分的に関連する情報があれば有効活用してください。**
• 情報の出典として「ファイル名」や「資料名」までは明示して構いませんが、技術的な内部管理情報（列番号、行番号、分割番号、データベースのIDなど）は一切出力しないでください。
• 代表者名や会社名など、ユーザーが聞いている情報だけを端的に答え、表形式やファイル構造の言及は不要です。
• **全く関連性がない場合のみ、その旨を丁寧に説明してください。**
• 専門的な内容も、日常の言葉で分かりやすく説明してください。
• 手続きや連絡先については、正確な情報を漏れなくご案内してください。
• 文末には「ご不明な点がございましたら、お気軽にお申し付けください。」と添えてください。

お客様からのご質問：
{message_text}

手元の参考資料：
{filtered_knowledge}

それでは、ご質問にお答えいたします："""

        try:
            response = model.generate_content(prompt)

            ai_response = ""
            try:
                # まず parts を優先的に結合
                if hasattr(response, "parts") and response.parts:
                    ai_response = "".join(getattr(p, "text", "") for p in response.parts)
                # parts が空なら text アクセサを試す
                if not ai_response and hasattr(response, "text"):
                    ai_response = response.text or ""
                # candidates 経由の fallback
                if not ai_response and hasattr(response, "candidates"):
                    for cand in response.candidates:
                        if hasattr(cand, "content") and getattr(cand.content, "parts", None):
                            ai_response = "".join(getattr(p, "text", "") for p in cand.content.parts)
                            if ai_response:
                                break
            except Exception as e:
                safe_print(f"❌ partsからテキスト抽出失敗: {e}")
                ai_response = ""

            if not ai_response:
                ai_response = "申し訳ございませんが、回答を生成できませんでした。"
            safe_print(f"✅ フォールバック応答生成完了: {len(ai_response)}文字")
        except Exception as e:
            safe_print(f"❌ 応答生成エラー: {e}")
            ai_response = "申し訳ございませんが、システムエラーが発生しました。しばらく時間をおいてから再度お試しください。"
        
        # Supabase にチャット履歴を保存
        try:
            from modules.chat_processing import save_chat_history
            from modules.question_categorizer import categorize_question
            
            # 質問内容を分析してカテゴリーを決定
            category_result = categorize_question(message_text)
            category = category_result.get("category", "general")
            
            # フォールバック処理でのソース文書情報を抽出
            primary_source_document = None
            if search_results and len(search_results) > 0:
                # search_resultsから最初のソース文書名を取得
                primary_source_document = search_results[0].get('metadata', {}).get('source_document')
                if not primary_source_document and resource_names and len(resource_names) > 0:
                    primary_source_document = resource_names[0]
            elif resource_names and len(resource_names) > 0:
                primary_source_document = resource_names[0]
            
            await save_chat_history(
                user_id=user_id or "anonymous",
                user_message=message_text,
                bot_response=ai_response,
                company_id=company_id,
                employee_id=user_id,
                employee_name=current_user.get("name") if current_user else None,
                category=category,
                sentiment="neutral",
                model_name="realtime-rag-fallback",
                source_document=primary_source_document
            )
        except Exception as e:
            safe_print(f"⚠️ Supabase へのチャット履歴保存エラー: {e}")
        
        # レスポンスを返す
        return ChatResponse(
            response=ai_response,
            sources=source_info_list
        )
        
    except Exception as e:
        safe_print(f"❌ process_chat_with_realtime_rag で重大エラー: {str(e)}")
        import traceback
        safe_print(f"📋 エラー詳細:\n{traceback.format_exc()}")
        
        try:
            return ChatResponse(
                response="申し訳ございませんが、システムエラーが発生しました。しばらく時間をおいてから再度お試しください。",
                sources=[]
            )
        except Exception as response_error:
            safe_print(f"❌ エラーレスポンス作成も失敗: {response_error}")
            raise HTTPException(
                status_code=500, 
                detail="システムエラーが発生しました。管理者にお問い合わせください。"
            )

# 外部呼び出し用のエイリアス
process_chat = process_chat_with_realtime_rag

def get_realtime_rag_status() -> Dict:
    """リアルタイムRAGシステムの状態を取得"""
    return {
        "realtime_rag_available": REALTIME_RAG_AVAILABLE,
        "fallback_available": FALLBACK_AVAILABLE,
        "model_initialized": model is not None,
        "system_status": "ready" if REALTIME_RAG_AVAILABLE else "fallback_only"
    }