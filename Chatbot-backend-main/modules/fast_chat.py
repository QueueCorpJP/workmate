"""
高速チャット処理モジュール
並列化、キャッシュ、高速RAGを活用したチャット処理の最適化版
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

def safe_print(text):
    """安全なprint関数"""
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            safe_text = str(text).encode('utf-8', errors='replace').decode('utf-8')
            print(safe_text)
        except:
            print("[出力エラー: Unicode文字を含むメッセージ]")

async def process_chat_fast(message, db, current_user: dict = None) -> Dict[str, Any]:
    """高速チャット処理（並列化 + キャッシュ活用）"""
    
    start_time = datetime.now()
    safe_print(f"🚀 高速チャット処理開始: {start_time}")
    
    try:
        # 1. 基本チェック（高速化）
        message_text = getattr(message, 'text', '') or getattr(message, 'message', '')
        if not message_text:
            raise ValueError("メッセージテキストが無効です")
        
        safe_print(f"📝 処理開始: '{message_text[:50]}...'")
        
        # 2. 一般会話判定（早期リターン）
        from .chat import is_casual_conversation, generate_casual_response
        if is_casual_conversation(message_text):
            safe_print(f"💬 一般会話として判定: 高速応答モード")
            
            company_name = "WorkMate"
            casual_response = await generate_casual_response(message_text, company_name)
            
            # チャット履歴保存（非同期で実行、応答速度に影響しない）
            if message.user_id:
                asyncio.create_task(save_casual_chat_async(message, casual_response, db))
            
            elapsed = (datetime.now() - start_time).total_seconds()
            safe_print(f"✅ 一般会話処理完了: {elapsed:.2f}秒")
            
            return {
                "response": casual_response,
                "source": "",
                "remaining_questions": None,
                "limit_reached": False
            }
        
        # 3. ユーザーデータの並列取得
        safe_print(f"🔄 ユーザーデータ並列取得開始")
        if message.user_id:
            from .chat_optimized import get_user_data_parallel
            company_id, limits_check, recent_messages = await get_user_data_parallel(message.user_id, db)
            
            # 利用制限チェック
            if not limits_check.get("is_unlimited", False) and not limits_check.get("allowed", True):
                safe_print(f"❌ 利用制限到達")
                return {
                    "response": f"申し訳ございません。デモ版の質問回数制限（{limits_check.get('limit', 0)}回）に達しました。",
                    "remaining_questions": 0,
                    "limit_reached": True
                }
        else:
            company_id = None
            limits_check = {"is_unlimited": True, "allowed": True, "remaining": 0}
            recent_messages = []
        
        safe_print(f"✅ ユーザーデータ取得完了: company_id={company_id}")
        
        # 4. リソース情報の並列取得
        safe_print(f"🔄 リソースデータ並列取得開始")
        uploaded_by = current_user["id"] if current_user and current_user.get("role") == "admin" else None
        
        from .chat_optimized import get_resource_data_parallel, get_special_instructions_async
        active_sources, active_knowledge_text, active_resource_names = await get_resource_data_parallel(company_id, uploaded_by, db)
        
        if not active_sources:
            safe_print(f"❌ アクティブリソースなし")
            return {
                "response": "申し訳ございません。現在、アクティブな知識ベースがありません。",
                "remaining_questions": limits_check.get("remaining", 0),
                "limit_reached": False
            }
        
        safe_print(f"✅ リソースデータ取得完了: {len(active_sources)}件のリソース")
        
        # Special指示を並列取得
        special_instructions_text = await get_special_instructions_async(active_sources, db)
        
        # 5. 🚀 並列高速RAG検索（最優先）
        if active_knowledge_text and len(active_knowledge_text) > 50000:
            safe_print(f"🔄 並列高速RAG検索開始: {len(active_knowledge_text):,}文字")
            
            try:
                # 【最優先】並列ベクトル検索を試行
                from .chat import PARALLEL_VECTOR_SEARCH_AVAILABLE
                
                if PARALLEL_VECTOR_SEARCH_AVAILABLE:
                    safe_print(f"⚡ 並列ベクトル検索使用試行")
                    
                    try:
                        from .parallel_vector_search import get_parallel_vector_search_instance_sync
                        
                        parallel_search_system = get_parallel_vector_search_instance_sync()
                        if parallel_search_system:
                            safe_print(f"✅ 並列ベクトル検索システム取得成功")
                            parallel_result = parallel_search_system.parallel_comprehensive_search_sync(
                                message_text, company_id, max_results=50
                            )
                            
                            if parallel_result and len(parallel_result.strip()) > 0:
                                active_knowledge_text = parallel_result
                                safe_print(f"✅ 並列ベクトル検索成功: {len(active_knowledge_text):,}文字")
                            else:
                                safe_print(f"⚠️ 並列ベクトル検索結果が空 - フォールバック")
                                raise ValueError("並列ベクトル検索結果が空")
                        else:
                            safe_print(f"❌ 並列ベクトル検索システム取得失敗")
                            raise ValueError("並列ベクトル検索システム取得失敗")
                            
                    except Exception as parallel_error:
                        safe_print(f"❌ 並列ベクトル検索失敗: {parallel_error}")
                        safe_print(f"🔄 従来RAGにフォールバック")
                        raise parallel_error
                else:
                    safe_print(f"⚠️ 並列ベクトル検索利用不可 - フォールバック")
                    
                # 【フォールバック1】高速RAG検索
                from .chat import SPEED_RAG_AVAILABLE
                
                if SPEED_RAG_AVAILABLE and len(active_knowledge_text) > 100000:
                    safe_print(f"⚡ 高速RAG使用試行")
                    
                    try:
                        from .rag_optimized import high_speed_rag
                        
                        # 高速RAGインスタンスの存在確認
                        if hasattr(high_speed_rag, 'lightning_search'):
                            safe_print(f"🔧 高速RAG lightning_search メソッド確認済み")
                            active_knowledge_text = await high_speed_rag.lightning_search(
                                message_text, active_knowledge_text, max_results=50
                            )
                            safe_print(f"✅ 高速RAG検索成功")
                        else:
                            safe_print(f"❌ 高速RAGメソッドが見つからない - フォールバック")
                            raise AttributeError("lightning_search method not found")
                            
                    except (ImportError, AttributeError, TypeError) as rag_error:
                        safe_print(f"❌ 高速RAG処理失敗: {type(rag_error).__name__}: {rag_error}")
                        safe_print(f"🔄 従来RAGにフォールバック")
                        from .chat import simple_rag_search
                        active_knowledge_text = simple_rag_search(
                            active_knowledge_text, message_text, max_results=50, company_id=company_id
                        )
                else:
                    safe_print(f"🔍 従来RAG使用（条件: SPEED_RAG={SPEED_RAG_AVAILABLE}, サイズ={len(active_knowledge_text):,}）")
                    from .chat import simple_rag_search
                    active_knowledge_text = simple_rag_search(
                        active_knowledge_text, message_text, max_results=50, company_id=company_id
                    )
                
                safe_print(f"✅ RAG検索完了: {len(active_knowledge_text):,}文字")
                
            except Exception as e:
                safe_print(f"❌ RAG処理で予期しないエラー: {type(e).__name__}: {e}")
                safe_print(f"🔄 最終フォールバック：従来RAG使用")
                try:
                    from .chat import simple_rag_search
                    active_knowledge_text = simple_rag_search(
                        active_knowledge_text, message_text, max_results=50, company_id=company_id
                    )
                    safe_print(f"✅ フォールバックRAG成功")
                except Exception as fallback_error:
                    safe_print(f"❌ フォールバックRAGも失敗: {fallback_error}")
                    # 最後の手段：知識ベースを縮小して返す
                    active_knowledge_text = active_knowledge_text[:100000]
                    safe_print(f"⚠️ 知識ベースを{len(active_knowledge_text):,}文字に縮小")
        
        # 6. 会話履歴の最適化構築
        from .prompt_cache import build_conversation_history_fast
        conversation_history = build_conversation_history_fast(recent_messages)
        
        # 7. 最適化されたプロンプト生成
        safe_print(f"🔄 最適化プロンプト生成開始")
        from .prompt_cache import (
            build_context_cached_prompt, estimate_prompt_size, 
            truncate_knowledge_for_size_limit, gemini_context_cache,
            generate_content_with_cache
        )
        from .config import setup_gemini_with_cache
        
        # サイズ制限チェック（高速推定）
        MAX_PROMPT_SIZE = 400000
        estimated_size = estimate_prompt_size(
            company_name="WorkMate",
            active_resource_names=active_resource_names,
            active_knowledge_text=active_knowledge_text,
            conversation_history=conversation_history,
            message_text=message_text,
            special_instructions_text=special_instructions_text
        )
        
        # サイズ制限対応
        if estimated_size > MAX_PROMPT_SIZE:
            safe_print(f"⚠️ プロンプトサイズ超過: {estimated_size:,} > {MAX_PROMPT_SIZE:,}")
            other_content_size = estimated_size - len(active_knowledge_text)
            active_knowledge_text = truncate_knowledge_for_size_limit(
                active_knowledge_text, MAX_PROMPT_SIZE, other_content_size
            )
        
        # コンテキストキャッシュ対応プロンプト構築
        prompt, cached_content_id = build_context_cached_prompt(
            company_name="WorkMate",
            active_resource_names=active_resource_names,
            active_knowledge_text=active_knowledge_text,
            conversation_history=conversation_history,
            message_text=message_text,
            special_instructions_text=special_instructions_text
        )
        
        safe_print(f"✅ プロンプト生成完了: {len(prompt):,}文字")
        
        # 8. コンテキストキャッシュ対応Gemini API呼び出し
        safe_print(f"🤖 Gemini API呼び出し開始")
        from .chat import model
        
        try:
            if cached_content_id:
                # キャッシュヒット：キャッシュ対応モデルを使用
                cache_model = setup_gemini_with_cache()
                safe_print(f"🎯 高速チャット（キャッシュ使用）: {cached_content_id}")
                
                response = generate_content_with_cache(cache_model, prompt, cached_content_id)
            else:
                # キャッシュミス：通常のモデルを使用
                safe_print(f"🤖 高速チャット（新規）: {len(prompt):,}文字")
                response = model.generate_content(prompt)
                
                # コンテキストキャッシュに保存
                if gemini_context_cache.should_cache_context(active_knowledge_text):
                    virtual_content_id = f"fast_cache_{hash(active_knowledge_text) % 100000}"
                    gemini_context_cache.store_context_cache(active_knowledge_text, virtual_content_id)
                    safe_print(f"💾 高速チャット用キャッシュ保存: {virtual_content_id}")
            
            response_text = response.text if response and hasattr(response, 'text') else "応答生成エラー"
            cache_status = "キャッシュ使用" if cached_content_id else "新規作成"
            safe_print(f"✅ Gemini応答受信: {len(response_text)}文字 ({cache_status})")
        except Exception as e:
            safe_print(f"❌ Gemini API エラー: {str(e)}")
            response_text = f"申し訳ございません。応答生成中にエラーが発生しました: {str(e)[:100]}"
        
        # 9. 利用制限更新（非同期で実行）
        remaining_questions = None
        if message.user_id and not limits_check.get("is_unlimited", False):
            # 非同期で更新（応答速度に影響しない）
            asyncio.create_task(update_usage_and_save_chat_async(
                message, response_text, db, len(active_sources)
            ))
            remaining_questions = limits_check.get("remaining", 0) - 1
        
        # 10. レスポンス生成
        elapsed = (datetime.now() - start_time).total_seconds()
        safe_print(f"🎉 高速チャット処理完了: {elapsed:.2f}秒")
        
        return {
            "response": response_text,
            "source": "",
            "remaining_questions": remaining_questions,
            "limit_reached": remaining_questions <= 0 if remaining_questions is not None else False
        }
        
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        safe_print(f"❌ 高速チャット処理エラー: {e} ({elapsed:.2f}秒)")
        
        # エラー時のフォールバック
        return {
            "response": f"申し訳ございません。処理中にエラーが発生しました: {str(e)[:100]}",
            "source": "",
            "remaining_questions": 0,
            "limit_reached": False
        }

async def save_casual_chat_async(message, response_text: str, db):
    """一般会話のチャット履歴非同期保存"""
    try:
        from modules.token_counter import TokenUsageTracker
        from supabase_adapter import select_data
        
        # 会社ID取得
        company_id = None
        if message.user_id:
            user_result = select_data("users", columns="company_id", filters={"id": message.user_id})
            if user_result.data and len(user_result.data) > 0:
                company_id = user_result.data[0].get('company_id')
        
        # チャット履歴保存
        tracker = TokenUsageTracker(db)
        chat_id = tracker.save_chat_with_prompts(
            user_message=getattr(message, 'text', '') or getattr(message, 'message', ''),
            bot_response=response_text,
            user_id=message.user_id,
            prompt_references=0,  # ナレッジ参照なし
            company_id=company_id,
            employee_id=getattr(message, 'employee_id', None),
            employee_name=getattr(message, 'employee_name', None),
            category="一般会話",
            sentiment="neutral",
            model="gemini-pro"
        )
        
        safe_print(f"✅ 一般会話履歴保存完了: {chat_id}")
        
    except Exception as e:
        safe_print(f"一般会話履歴保存エラー: {e}")

async def update_usage_and_save_chat_async(message, response_text: str, db, prompt_references: int):
    """利用制限更新とチャット履歴保存の非同期処理"""
    try:
        from modules.token_counter import TokenUsageTracker
        from .chat_optimized import update_usage_async
        from supabase_adapter import select_data
        
        # 並列実行
        user_result_task = asyncio.create_task(get_user_company_async(message.user_id))
        usage_update_task = update_usage_async(message.user_id, db)
        
        # 会社ID取得完了を待つ
        company_id = await user_result_task
        
        # チャット履歴保存
        tracker = TokenUsageTracker(db)
        chat_id = tracker.save_chat_with_prompts(
            user_message=getattr(message, 'text', '') or getattr(message, 'message', ''),
            bot_response=response_text,
            user_id=message.user_id,
            prompt_references=prompt_references,
            company_id=company_id,
            employee_id=getattr(message, 'employee_id', None),
            employee_name=getattr(message, 'employee_name', None),
            category="知識ベース検索",
            sentiment="neutral",
            model="gemini-pro"
        )
        
        # 利用制限更新完了を待つ
        await usage_update_task
        
        safe_print(f"✅ 履歴保存・利用制限更新完了: {chat_id}")
        
    except Exception as e:
        safe_print(f"履歴保存・利用制限更新エラー: {e}")

async def get_user_company_async(user_id: str) -> Optional[str]:
    """ユーザーの会社ID非同期取得"""
    try:
        from supabase_adapter import select_data
        user_result = select_data("users", columns="company_id", filters={"id": user_id})
        if user_result.data and len(user_result.data) > 0:
            return user_result.data[0].get('company_id')
        return None
    except Exception as e:
        safe_print(f"会社ID非同期取得エラー: {e}")
        return None
