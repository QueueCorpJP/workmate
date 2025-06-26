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
    REALTIME_RAG_AVAILABLE = realtime_rag_available()
    if REALTIME_RAG_AVAILABLE:
        safe_print("✅ リアルタイムRAGシステムが利用可能です")
    else:
        safe_print("⚠️ リアルタイムRAGシステムの設定が不完全です")
except ImportError as e:
    REALTIME_RAG_AVAILABLE = False
    safe_print(f"⚠️ リアルタイムRAGシステムが利用できません: {e}")

# フォールバック用の従来システム
try:
    from .chat import simple_rag_search_fallback, is_casual_conversation, generate_casual_response
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
        user_id = current_user.get('user_id') if current_user else None
        company_id = current_user.get('company_id') if current_user else None
        
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
                check_usage_limits(user_id, db)
                update_usage_count(user_id, db)
            except HTTPException as e:
                return ChatResponse(
                    response=e.detail,
                    sources=[]
                )
        
        # 挨拶や一般的な会話の判定（フォールバック機能使用）
        if FALLBACK_AVAILABLE and is_casual_conversation(message_text):
            company_name = DEFAULT_COMPANY_NAME
            if company_id:
                company_info = get_company_by_id(company_id, db)
                if company_info:
                    company_name = company_info.get('name', DEFAULT_COMPANY_NAME)
            
            casual_response = await generate_casual_response(message_text, company_name)
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
                    
                    if status == "completed":
                        safe_print(f"✅ リアルタイムRAG成功: {len(ai_response)}文字の回答を生成")
                        safe_print(f"📊 使用チャンク数: {rag_result.get('chunks_used', 0)}")
                        safe_print(f"📊 最高類似度: {rag_result.get('top_similarity', 0.0):.3f}")
                        
                        # ソース情報を構築（リアルタイムRAGの結果から）
                        source_info_list = [
                            {
                                "name": f"関連資料 (類似度: {rag_result.get('top_similarity', 0.0):.3f})",
                                "type": "realtime_rag",
                                "relevance": rag_result.get('top_similarity', 0.8)
                            }
                        ]
                        
                        # チャット履歴をデータベースに保存
                        try:
                            with db.cursor(cursor_factory=RealDictCursor) as cursor:
                                cursor.execute("""
                                    INSERT INTO chat_history (user_id, company_id, user_message, ai_response, created_at)
                                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                                """, (user_id, company_id, message_text, ai_response))
                                db.commit()
                                safe_print("✅ チャット履歴をデータベースに保存しました")
                        except Exception as e:
                            safe_print(f"⚠️ チャット履歴保存エラー: {e}")
                        
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
        filtered_knowledge = simple_rag_search_fallback(knowledge_text, message_text, max_results=15, company_id=company_id)
        
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
        
        # 通常のプロンプト処理
        prompt = f"""あなたは{company_name}のAIアシスタントです。以下の情報を基に、ユーザーの質問に正確で親切に回答してください。

【重要な指示】
1. 提供された情報のみを使用して回答してください
2. 情報にない内容は推測せず、「提供された情報には記載がありません」と明記してください
3. 回答は丁寧で分かりやすい日本語で行ってください
4. 具体的な手順や連絡先がある場合は、正確に伝えてください

【参考情報】
{filtered_knowledge}

【ユーザーの質問】
{message_text}

【回答】"""

        try:
            response = model.generate_content(prompt)
            ai_response = response.text if response and response.text else "申し訳ございませんが、回答を生成できませんでした。"
            safe_print(f"✅ フォールバック応答生成完了: {len(ai_response)}文字")
        except Exception as e:
            safe_print(f"❌ 応答生成エラー: {e}")
            ai_response = "申し訳ございませんが、システムエラーが発生しました。しばらく時間をおいてから再度お試しください。"
        
        # チャット履歴をデータベースに保存
        try:
            with db.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO chat_history (user_id, company_id, user_message, ai_response, created_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (user_id, company_id, message_text, ai_response))
                db.commit()
                safe_print("✅ チャット履歴をデータベースに保存しました")
        except Exception as e:
            safe_print(f"⚠️ チャット履歴保存エラー: {e}")
        
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