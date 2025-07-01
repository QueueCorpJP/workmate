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
                                source_name = "関連資料"
                                
                                source_info_list.append({
                                    "name": source_name,
                                    "type": "knowledge_base",
                                    "relevance": top_similarity,
                                    "search_method": search_method,
                                    "chunks_count": chunks_used,
                                    "keywords": keywords[:5],
                                    "similarity_score": f"{top_similarity:.3f}"
                                })
                            else:
                                # チャンクが使用されていない場合
                                source_info_list.append({
                                    "name": f"システム回答 ({search_method})",
                                    "type": "system_response",
                                    "relevance": 0.5
                                })
                        
                        # チャット履歴をデータベースに保存
                        try:
                            with db.cursor(cursor_factory=RealDictCursor) as cursor:
                                cursor.execute("""
                                    INSERT INTO chat_history (id, user_id, company_id, user_message, bot_response, timestamp)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, (str(uuid.uuid4()), user_id, company_id, message_text, ai_response, datetime.now().isoformat()))
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
        prompt = f"""あなたは{company_name}の社内向け丁寧で親切なアシスタントです。

回答の際の重要な指針：
• 回答は丁寧な敬語で行ってください
• 情報の出典として「ファイル名」や「資料名」までは明示して構いませんが、列番号、行番号、チャンク番号、データベースのIDなどの内部的な構造情報は一切出力しないでください
• 代表者名や会社名など、ユーザーが聞いている情報だけを端的に答え、表形式やファイル構造の言及は不要です
• 情報が見つからない場合も、失礼のない自然な日本語で「現在の資料には該当情報がございません」と案内してください
• 文末には「ご不明な点がございましたら、お気軽にお申し付けください。」と添えてください

お客様からのご質問：
{message_text}

手元の参考資料：
{filtered_knowledge}

お答えする際の心がけ：
• 手元の資料に記載されている内容のみを基に、正確にお答えします
• 資料に記載がない内容については、正直に「手元の資料には記載がございません」とお伝えします
• 専門的な内容も、日常の言葉で分かりやすく説明します
• 手続きや連絡先については、正確な情報を漏れなくご案内します

それでは、ご質問にお答えいたします："""

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
                    INSERT INTO chat_history (id, user_id, company_id, user_message, bot_response, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (str(uuid.uuid4()), user_id, company_id, message_text, ai_response, datetime.now().isoformat()))
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