from psycopg2.extensions import connection as Connection
from .database import ensure_string

async def get_uploaded_resources_by_company_id(company_id: str, db: Connection, uploaded_by: str = None):
    """会社IDに基づいてアップロードされたリソースの詳細情報を取得します"""
    try:
        from supabase_adapter import execute_query, select_data, get_supabase_client
        
        # Supabaseクライアントを取得
        supabase = get_supabase_client()
        
        # document_sourcesテーブルから直接データを取得
        query = supabase.table("document_sources").select("*")
        
        # 会社IDに基づいてフィルタリング
        if company_id is not None:
            query = query.eq("company_id", company_id)
        
        # アップロード者IDに基づいてフィルタリング（管理者用）
        if uploaded_by is not None:
            query = query.eq("uploaded_by", uploaded_by)
        
        # クエリを実行
        sources_result = query.execute()
        
        # 結果を取得
        sources = sources_result.data if sources_result.data else []
        print(f"Supabase APIから直接取得したリソース: {len(sources)}件")
        
        resources = []
        
        # 各リソースに対して処理
        for source in sources:
            resource_id = source.get("id")
            if not resource_id:
                continue
            
            # アップローダー名を取得
            uploader_id = source.get("uploaded_by")
            uploader_name = "不明"
            if uploader_id:
                user_query = supabase.table("users").select("name").eq("id", uploader_id)
                user_result = user_query.execute()
                if user_result.data and len(user_result.data) > 0:
                    uploader_name = user_result.data[0].get("name", "不明")
            
            # 使用回数を取得
            usage_count_query = supabase.table("chat_history").select("id").eq("source_document", resource_id)
            usage_count_result = usage_count_query.execute()
            usage_count = len(usage_count_result.data) if usage_count_result.data else 0
            
            # 最終使用日時を取得
            last_used = None
            if usage_count > 0:
                last_used_query = supabase.table("chat_history").select("timestamp").eq("source_document", resource_id).order("timestamp", desc=True).limit(1)
                last_used_result = last_used_query.execute()
                if last_used_result.data and len(last_used_result.data) > 0:
                    last_used = last_used_result.data[0].get("timestamp")
            
            # リソース情報を構築
            resources.append({
                "id": resource_id,
                "name": source.get("name", ""),
                "type": source.get("type", ""),
                "page_count": source.get("page_count"),
                "timestamp": source.get("uploaded_at"),
                "active": source.get("active", True),
                "uploaded_by": uploader_id or "",
                "uploader_name": uploader_name,
                "usage_count": usage_count,
                "last_used": last_used
            })
        
        print(f"処理後のリソース: {len(resources)}件")
        return {
            "resources": resources,
            "message": f"{len(resources)}件のリソースが見つかりました"
        }
    except Exception as e:
        print(f"リソース取得エラー: {e}")
        import traceback
        print(traceback.format_exc())
        # エラーが発生した場合は空のリソースリストを返す
        return {
            "resources": [],
            "message": f"リソースの取得中にエラーが発生しました: {str(e)}"
        }

async def toggle_resource_active_by_id(resource_id: str, db: Connection):
    try:
        from supabase_adapter import get_supabase_client
        
        # Supabaseクライアントを取得
        supabase = get_supabase_client()
        
        # リソース情報を取得
        query = supabase.table("document_sources").select("name, active").eq("id", resource_id)
        result = query.execute()
        
        if not result.data or len(result.data) == 0:
            print(f"リソースID {resource_id} が見つかりませんでした")
            return {
                "name": "",
                "active": False,
                "message": "リソースが見つかりませんでした"
            }
            
        current_active_state = result.data[0].get("active", False)
        resource_name = result.data[0].get("name", "")
        new_active_state = not current_active_state
        
        print(f"リソース '{resource_name}' のアクティブ状態を {current_active_state} から {new_active_state} に変更します")
        
        # アクティブ状態を更新
        update_query = supabase.table("document_sources").update({"active": new_active_state}).eq("id", resource_id)
        update_result = update_query.execute()
        
        print(f"更新結果: {update_result.data if update_result.data else '更新失敗'}")
        
        return {
            "name": resource_name,
            "active": new_active_state,
            "message": f"リソース '{resource_name}' のアクティブ状態を {new_active_state} に変更しました"
        }
    except Exception as e:
        print(f"リソース状態変更エラー: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            "name": "",
            "active": False,
            "message": f"リソース状態の変更中にエラーが発生しました: {str(e)}"
        }

async def remove_resource_by_id(resource_id: str, db: Connection):
    try:
        from supabase_adapter import get_supabase_client
        
        # Supabaseクライアントを取得
        supabase = get_supabase_client()
        
        # リソース名を取得（ログ用）
        query = supabase.table("document_sources").select("name").eq("id", resource_id)
        result = query.execute()
        
        resource_name = ""
        if result.data and len(result.data) > 0:
            resource_name = result.data[0].get("name", "")
            print(f"削除するリソース名: {resource_name}")
        else:
            print(f"リソースID {resource_id} が見つかりませんでした")
            return {
                "name": "",
                "message": "リソースが見つかりませんでした"
            }
        
        # リソースを削除
        delete_query = supabase.table("document_sources").delete().eq("id", resource_id)
        delete_result = delete_query.execute()
        
        print(f"削除結果: {delete_result.data if delete_result.data else '削除失敗'}")
        
        return {
            "name": resource_name,
            "message": f"リソース '{resource_name}' を削除しました"
        }
    except Exception as e:
        print(f"リソース削除エラー: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            "name": "",
            "message": f"リソースの削除中にエラーが発生しました: {str(e)}"
        }

async def get_active_resources_by_company_id(company_id: str, db: Connection, uploaded_by: str = None):
    """アクティブなリソースのIDリストを取得します"""
    try:
        from supabase_adapter import get_supabase_client
        
        # Supabaseクライアントを取得
        supabase = get_supabase_client()
        
        # クエリを構築
        query = supabase.table("document_sources").select("id").eq("active", True)
        
        if company_id is not None:
            query = query.eq("company_id", company_id)
        
        if uploaded_by is not None:
            query = query.eq("uploaded_by", uploaded_by)
        
        # クエリを実行
        result = query.execute()
        
        # IDのリストを作成
        resources = [source.get("id") for source in result.data if source.get("id")]
        
        print(f"アクティブなリソースID: {len(resources)}件")
        return resources
    except Exception as e:
        print(f"アクティブリソースID取得エラー: {e}")
        import traceback
        print(traceback.format_exc())
        return []

async def get_active_resource_names_by_company_id(company_id: str, db: Connection):
    """アクティブなリソースの名前リストを取得します"""
    try:
        from supabase_adapter import get_supabase_client
        
        # Supabaseクライアントを取得
        supabase = get_supabase_client()
        
        # クエリを構築
        query = supabase.table("document_sources").select("name").eq("active", True)
        
        if company_id is not None:
            query = query.eq("company_id", company_id)
        
        # クエリを実行
        result = query.execute()
        
        # 名前のリストを作成
        resources = [source.get("name") for source in result.data if source.get("name")]
        
        print(f"アクティブなリソース名: {len(resources)}件")
        return resources
    except Exception as e:
        print(f"アクティブリソース名取得エラー: {e}")
        import traceback
        print(traceback.format_exc())
        return []

async def get_active_resources_content_by_ids(resource_ids: list[str], db: Connection) -> str:
    """指定されたIDのリソースのコンテンツを取得して結合します"""
    # Check if resource_ids is None or empty
    if not resource_ids:
        return ""
    
    try:
        from supabase_adapter import get_supabase_client
        
        # Supabaseクライアントを取得
        supabase = get_supabase_client()
        
        print(f"リソースID一覧: {resource_ids}")
        
        combined_content = []
        
        # 各リソースIDに対して個別にクエリを実行
        for resource_id in resource_ids:
            query = supabase.table("document_sources").select("content").eq("id", resource_id)
            result = query.execute()
            
            if result.data and len(result.data) > 0:
                content = result.data[0].get("content")
                if content is not None:
                    combined_content.append(ensure_string(content, for_db=True))
                    print(f"リソースID {resource_id} のコンテンツを取得しました")
                else:
                    print(f"リソースID {resource_id} のコンテンツはNoneです")
            else:
                print(f"リソースID {resource_id} のコンテンツが見つかりませんでした")
        
        # 結合
        combined = "\n".join(combined_content)
        print(f"合計 {len(combined_content)} 件のコンテンツを結合しました")
        
        return combined
    except Exception as e:
        print(f"リソースコンテンツ取得エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return ""
