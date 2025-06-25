"""
並列化されたデータベースアクセス関数群
チャット処理の高速化のため、複数のデータベースアクセスを並列実行
"""
import asyncio
from typing import Tuple, List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

# グローバルな ThreadPoolExecutor
_executor = ThreadPoolExecutor(max_workers=5)

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

async def get_user_data_parallel(user_id: str, db) -> Tuple[Optional[str], Dict, List]:
    """ユーザー関連データを並列取得"""
    
    def get_company_id():
        """会社IDを取得"""
        try:
            from supabase_adapter import select_data
            user_result = select_data("users", columns="company_id", filters={"id": user_id})
            if user_result and user_result.data and len(user_result.data) > 0:
                return user_result.data[0].get('company_id')
            return None
        except Exception as e:
            safe_print(f"会社ID取得エラー: {e}")
            return None
    
    def get_usage_limits():
        """利用制限を取得"""
        try:
            from .auth import check_usage_limits
            return check_usage_limits(user_id, "question", db)
        except Exception as e:
            safe_print(f"利用制限取得エラー: {e}")
            return {"is_unlimited": True, "allowed": True, "remaining": 0}
    
    def get_conversation_history():
        """会話履歴を取得"""
        try:
            from psycopg2.extras import RealDictCursor
            with db.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT user_message, bot_response FROM chat_history WHERE employee_id = %s ORDER BY timestamp DESC LIMIT 2",
                    (user_id,)
                )
                return list(cursor.fetchall())
        except Exception as e:
            safe_print(f"会話履歴取得エラー: {e}")
            return []
    
    # 並列実行
    try:
        loop = asyncio.get_event_loop()
        
        # ThreadPoolExecutorを使用して並列実行
        company_id_task = loop.run_in_executor(_executor, get_company_id)
        limits_task = loop.run_in_executor(_executor, get_usage_limits)
        history_task = loop.run_in_executor(_executor, get_conversation_history)
        
        # 全て完了を待つ
        company_id, limits_check, recent_messages = await asyncio.gather(
            company_id_task,
            limits_task,
            history_task,
            return_exceptions=True
        )
        
        # エラーハンドリング
        if isinstance(company_id, Exception):
            safe_print(f"会社ID取得中にエラー: {company_id}")
            company_id = None
        
        if isinstance(limits_check, Exception):
            safe_print(f"利用制限取得中にエラー: {limits_check}")
            limits_check = {"is_unlimited": True, "allowed": True, "remaining": 0}
        
        if isinstance(recent_messages, Exception):
            safe_print(f"会話履歴取得中にエラー: {recent_messages}")
            recent_messages = []
        
        safe_print(f"✅ 並列データ取得完了: company_id={company_id}, limits={bool(limits_check)}, history={len(recent_messages)}件")
        
        return company_id, limits_check, recent_messages
        
    except Exception as e:
        safe_print(f"並列データ取得エラー: {e}")
        # フォールバック: 順次実行
        return None, {"is_unlimited": True, "allowed": True, "remaining": 0}, []

async def get_resource_data_parallel(company_id: Optional[str], uploaded_by: Optional[str], db) -> Tuple[List[str], str, List[str]]:
    """リソース関連データを並列取得"""
    
    def get_active_sources():
        """アクティブなリソースIDを取得"""
        try:
            from .resource import get_active_resources_by_company_id
            # 非同期関数を同期的に実行（ThreadPoolExecutor内）
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    get_active_resources_by_company_id(company_id, db, uploaded_by)
                )
                return result
            finally:
                loop.close()
        except Exception as e:
            safe_print(f"アクティブリソース取得エラー: {e}")
            return []
    
    def get_resource_names(company_id):
        """リソース名を取得"""
        try:
            from .resource import get_active_resource_names_by_company_id
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    get_active_resource_names_by_company_id(company_id, db)
                )
                return result
            finally:
                loop.close()
        except Exception as e:
            safe_print(f"リソース名取得エラー: {e}")
            return []
    
    # 段階的並列実行（依存関係のため）
    try:
        loop = asyncio.get_event_loop()
        
        # 第1段階: アクティブソースとリソース名を並列取得
        sources_task = loop.run_in_executor(_executor, get_active_sources)
        names_task = loop.run_in_executor(_executor, get_resource_names, company_id)
        
        active_sources, active_resource_names = await asyncio.gather(
            sources_task,
            names_task,
            return_exceptions=True
        )
        
        # エラーハンドリング
        if isinstance(active_sources, Exception):
            safe_print(f"アクティブソース取得中にエラー: {active_sources}")
            active_sources = []
        
        if isinstance(active_resource_names, Exception):
            safe_print(f"リソース名取得中にエラー: {active_resource_names}")
            active_resource_names = []
        
        # アクティブなリソースがない場合は早期リターン
        if not active_sources:
            return [], "", []
        
        # 第2段階: リソースコンテンツを取得
        def get_content():
            try:
                from .resource import get_active_resources_content_by_ids
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        get_active_resources_content_by_ids(active_sources, db)
                    )
                    return result
                finally:
                    loop.close()
            except Exception as e:
                safe_print(f"リソースコンテンツ取得エラー: {e}")
                return ""
        
        content_task = loop.run_in_executor(_executor, get_content)
        active_knowledge_text = await content_task
        
        # エラーハンドリング
        if isinstance(active_knowledge_text, Exception):
            safe_print(f"コンテンツ取得中にエラー: {active_knowledge_text}")
            active_knowledge_text = ""
        
        safe_print(f"✅ 並列リソース取得完了: sources={len(active_sources)}件, content={len(active_knowledge_text):,}文字")
        
        return active_sources, active_knowledge_text, active_resource_names
        
    except Exception as e:
        safe_print(f"並列リソース取得エラー: {e}")
        return [], "", []

async def get_special_instructions_async(active_sources: List[str], db) -> str:
    """Special指示の非同期取得"""
    try:
        def get_special_instructions():
            try:
                from supabase_adapter import select_data
                special_instructions = []
                for source_id in active_sources:
                    source_result = select_data("document_sources", columns="name,special", filters={"id": source_id})
                    if source_result.data and len(source_result.data) > 0:
                        source_data = source_result.data[0]
                        if source_data.get('special') and source_data['special'].strip():
                            special_instructions.append({
                                "name": source_data.get('name', 'Unknown'),
                                "instruction": source_data['special'].strip()
                            })
                return special_instructions
            except Exception as e:
                safe_print(f"Special指示取得エラー: {e}")
                return []
        
        loop = asyncio.get_event_loop()
        special_instructions = await loop.run_in_executor(_executor, get_special_instructions)
        
        # Special指示テキストの構築
        special_instructions_text = ""
        if special_instructions:
            special_instructions_text = "\n\n特別な回答指示（以下のリソースを参照する際は、各リソースの指示に従ってください）：\n"
            for idx, inst in enumerate(special_instructions, 1):
                special_instructions_text += f"{idx}. 【{inst['name']}】: {inst['instruction']}\n"
        
        safe_print(f"✅ Special指示取得完了: {len(special_instructions)}件")
        return special_instructions_text
        
    except Exception as e:
        safe_print(f"Special指示非同期取得エラー: {e}")
        return ""

async def update_usage_async(user_id: str, db):
    """利用制限の非同期更新（応答速度に影響しない）"""
    try:
        def update_usage():
            try:
                from .database import update_usage_count
                return update_usage_count(user_id, "questions_used", db)
            except Exception as e:
                safe_print(f"利用制限更新エラー: {e}")
                return None
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(_executor, update_usage)
        
        if result:
            safe_print(f"✅ 利用制限更新完了: {result}")
        else:
            safe_print("⚠️ 利用制限更新失敗")
            
    except Exception as e:
        safe_print(f"非同期利用制限更新エラー: {e}")

def cleanup_executor():
    """リソースクリーンアップ"""
    global _executor
    if _executor:
        _executor.shutdown(wait=True) 