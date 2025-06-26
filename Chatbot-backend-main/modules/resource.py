from psycopg2.extensions import connection as Connection
from .database import ensure_string

def _clean_nan_values(text: str) -> str:
    """テキストからNaN値や無効な文字列を除去する"""
    if not text:
        return ""
    
    import re
    
    # 1. NaN値の除去
    text = re.sub(r'\bnan\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNaN\b', '', text)
    text = re.sub(r'\bNAN\b', '', text)
    text = re.sub(r'\bnone\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bnull\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b<na>\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bn/a\b', '', text, flags=re.IGNORECASE)
    
    # 2. 連続するnanを除去
    text = re.sub(r'(\s*nan\s*){2,}', ' ', text, flags=re.IGNORECASE)
    
    # 3. 余分な空白の除去
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

async def get_uploaded_resources_by_company_id(company_id: str, db: Connection, uploaded_by: str = None):
    """会社IDに基づいてアップロードされたリソースの詳細情報を取得します"""
    try:
        print(f"🔍 [DEBUG] get_uploaded_resources_by_company_id 開始")
        print(f"🔍 [DEBUG] 入力パラメータ:")
        print(f"  - company_id: {company_id} (type: {type(company_id)})")
        print(f"  - uploaded_by: {uploaded_by} (type: {type(uploaded_by)})")
        print(f"  - db: {db} (type: {type(db)})")
        
        from supabase_adapter import execute_query, select_data, get_supabase_client
        
        # Supabaseクライアントを取得
        supabase = get_supabase_client()
        print(f"🔍 [DEBUG] Supabaseクライアント取得完了: {supabase}")
        
        # document_sourcesテーブルから必要なフィールドのみ取得（contentは除外）
        query = supabase.table("document_sources").select("id,name,type,page_count,uploaded_at,active,uploaded_by,special")
        print(f"🔍 [DEBUG] 基本クエリ作成完了（contentフィールド除外で高速化）")
        
        # 会社IDに基づいてフィルタリング
        if company_id is not None:
            query = query.eq("company_id", company_id)
            print(f"🔍 [DEBUG] company_idフィルタ適用: {company_id}")
        else:
            print(f"🔍 [DEBUG] company_idフィルタなし（全件取得）")
        
        # アップロード者IDに基づいてフィルタリング（管理者用）
        if uploaded_by is not None:
            query = query.eq("uploaded_by", uploaded_by)
            print(f"🔍 [DEBUG] uploaded_byフィルタ適用: {uploaded_by}")
        else:
            print(f"🔍 [DEBUG] uploaded_byフィルタなし")
        
        # クエリを実行
        print(f"🔍 [DEBUG] Supabaseクエリ実行開始...")
        sources_result = query.execute()
        print(f"🔍 [DEBUG] Supabaseクエリ実行完了")
        print(f"🔍 [DEBUG] sources_result: {sources_result}")
        print(f"🔍 [DEBUG] sources_result.data: {sources_result.data}")
        print(f"🔍 [DEBUG] sources_result.count: {getattr(sources_result, 'count', 'N/A')}")
        
        # 結果を取得
        sources = sources_result.data if sources_result.data else []
        print(f"🔍 [DEBUG] 取得したsourcesの数: {len(sources)}")
        print(f"🔍 [DEBUG] sources詳細:")
        for i, source in enumerate(sources):
            print(f"  [{i+1}] ID: {source.get('id')}, Name: {source.get('name')}, Type: {source.get('type')}, Active: {source.get('active')}")
        
        print(f"Supabase APIから直接取得したリソース: {len(sources)}件")
        
        resources = []
        
        # 全ユーザー情報を一度に取得
        print(f"🔍 [DEBUG] ユーザー情報取得開始...")
        all_users = {}
        if sources:
            unique_uploader_ids = list(set([source.get("uploaded_by") for source in sources if source.get("uploaded_by")]))
            print(f"🔍 [DEBUG] ユニークなアップローダーID: {unique_uploader_ids}")
            if unique_uploader_ids:
                users_query = supabase.table("users").select("id, name").in_("id", unique_uploader_ids)
                users_result = users_query.execute()
                print(f"🔍 [DEBUG] ユーザー情報クエリ結果: {users_result.data}")
                if users_result.data:
                    all_users = {user["id"]: user.get("name", "不明") for user in users_result.data}
                    print(f"🔍 [DEBUG] all_usersマップ: {all_users}")
        else:
            print(f"🔍 [DEBUG] sourcesが空のため、ユーザー情報取得をスキップ")
        
        # 全チャット履歴を一度に取得（使用回数計算用）
        print(f"🔍 [DEBUG] チャット履歴取得開始...")
        all_usage_counts = {}
        all_last_used = {}
        if sources:
            resource_ids = [source.get("id") for source in sources if source.get("id")]
            print(f"🔍 [DEBUG] チャット履歴取得対象のリソースID: {resource_ids}")
            if resource_ids:
                # 使用回数を一度に取得
                usage_query = supabase.table("chat_history").select("source_document, timestamp").in_("source_document", resource_ids)
                usage_result = usage_query.execute()
                print(f"🔍 [DEBUG] チャット履歴クエリ結果: {len(usage_result.data) if usage_result.data else 0}件")
                if usage_result.data:
                    # 使用回数をカウント
                    for chat in usage_result.data:
                        source_doc = chat.get("source_document")
                        if source_doc:
                            all_usage_counts[source_doc] = all_usage_counts.get(source_doc, 0) + 1
                            # 最新の使用日時を記録
                            timestamp = chat.get("timestamp")
                            if timestamp:
                                if source_doc not in all_last_used or timestamp > all_last_used[source_doc]:
                                    all_last_used[source_doc] = timestamp
                    print(f"🔍 [DEBUG] 使用回数カウント結果: {all_usage_counts}")
                    print(f"🔍 [DEBUG] 最終使用日時: {all_last_used}")
        else:
            print(f"🔍 [DEBUG] sourcesが空のため、チャット履歴取得をスキップ")
        
        # 各リソースに対して処理
        print(f"🔍 [DEBUG] リソース処理開始...")
        for i, source in enumerate(sources):
            print(f"🔍 [DEBUG] [{i+1}/{len(sources)}] リソース処理: {source}")
            resource_id = source.get("id")
            if not resource_id:
                print(f"🔍 [DEBUG] リソースIDがない - スキップ")
                continue
            
            # アップローダー名を取得（キャッシュから）
            uploader_id = source.get("uploaded_by")
            uploader_name = all_users.get(uploader_id, "不明") if uploader_id else "不明"
            print(f"🔍 [DEBUG] アップローダー: ID={uploader_id}, Name={uploader_name}")
            
            # 使用回数を取得（キャッシュから）
            usage_count = all_usage_counts.get(resource_id, 0)
            print(f"🔍 [DEBUG] 使用回数: {usage_count}")
            
            # 最終使用日時を取得（キャッシュから）
            last_used = all_last_used.get(resource_id)
            print(f"🔍 [DEBUG] 最終使用日時: {last_used}")
            
            # リソース情報を構築
            resource_data = {
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
            }
            print(f"🔍 [DEBUG] 構築されたリソースデータ: {resource_data}")
            resources.append(resource_data)
        
        print(f"🔍 [DEBUG] 最終リソース配列:")
        for i, resource in enumerate(resources):
            print(f"  [{i+1}] {resource}")
        
        result = {
            "resources": resources,
            "message": f"{len(resources)}件のリソースが見つかりました"
        }
        
        print(f"🔍 [DEBUG] 最終レスポンス: {result}")
        print(f"処理後のリソース: {len(resources)}件")
        return result
    except Exception as e:
        print(f"❌ [ERROR] リソース取得エラー: {e}")
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ [ERROR] エラー詳細:\n{error_details}")
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
    """
    🔍 指定されたIDのリソースのコンテンツを取得して結合します
    
    本番環境での知識ベース取得問題をデバッグするため、詳細なログを出力
    """
    # Check if resource_ids is None or empty
    if not resource_ids:
        print("❌ リソースIDリストが空です")
        return ""
    
    try:
        from supabase_adapter import get_supabase_client
        
        # Supabaseクライアントを取得
        supabase = get_supabase_client()
        
        print(f"📋 リソースID一覧 ({len(resource_ids)}件): {resource_ids}")
        
        combined_content = []
        failed_resources = []
        
        # 各リソースIDに対して個別にクエリを実行
        for i, resource_id in enumerate(resource_ids):
            print(f"🔍 [{i+1}/{len(resource_ids)}] リソースID {resource_id} の処理開始")
            
            try:
                # まずリソースの基本情報を確認（contentカラム除外）
                info_query = supabase.table("document_sources").select("id,name,active").eq("id", resource_id)
                info_result = info_query.execute()
                
                if not info_result.data or len(info_result.data) == 0:
                    print(f"❌ リソースID {resource_id} が存在しません")
                    failed_resources.append({"id": resource_id, "reason": "リソースが存在しない"})
                    continue
                
                resource_info = info_result.data[0]
                resource_name = resource_info.get("name", "不明")
                is_active = resource_info.get("active", False)
                
                # ✅ 修正: chunksテーブルからコンテンツを取得
                content = await _get_content_from_chunks(resource_id, supabase)
                
                print(f"📄 リソース名: {resource_name}")
                print(f"🔘 アクティブ状態: {is_active}")
                print(f"📝 コンテンツ存在: {'あり' if content else 'なし'}")
                
                if not is_active:
                    print(f"⚠️ リソースID {resource_id} ({resource_name}) は無効です")
                    failed_resources.append({"id": resource_id, "name": resource_name, "reason": "リソースが無効"})
                    continue
                
                if content is None or content == "":
                    print(f"❌ リソースID {resource_id} ({resource_name}) のコンテンツが空です")
                    failed_resources.append({"id": resource_id, "name": resource_name, "reason": "コンテンツが空"})
                    continue
                
                # コンテンツの詳細情報を出力
                content_length = len(str(content))
                content_preview = str(content)[:200] + "..." if content_length > 200 else str(content)
                print(f"📊 コンテンツ長: {content_length:,} 文字")
                print(f"👀 コンテンツ先頭: {content_preview}")
                
                # ✅ 修正: chunksテーブルから取得したコンテンツを直接使用
                processed_content = ensure_string(content, for_db=True)
                
                # 追加のNaN値処理
                processed_content = _clean_nan_values(processed_content)
                
                combined_content.append(f"=== {resource_name} ===\n{processed_content}")
                print(f"✅ chunksテーブルからコンテンツ取得完了: {resource_name}")
                
            except Exception as resource_error:
                print(f"❌ リソースID {resource_id} 処理中にエラー: {str(resource_error)}")
                failed_resources.append({"id": resource_id, "reason": f"処理エラー: {str(resource_error)}"})
                continue
        
        # 結果のサマリーを出力
        print(f"\n📊 処理結果サマリー:")
        print(f"✅ 成功: {len(combined_content)} 件")
        print(f"❌ 失敗: {len(failed_resources)} 件")
        
        if failed_resources:
            print(f"🔍 失敗したリソース詳細:")
            for failed in failed_resources:
                print(f"  - ID: {failed['id']}, 名前: {failed.get('name', '不明')}, 理由: {failed['reason']}")
        
        # 結合
        combined = "\n\n".join(combined_content)
        final_length = len(combined)
        print(f"📝 最終的な知識ベース長: {final_length:,} 文字")
        
        if final_length == 0:
            print("❌ 最終的な知識ベースが空です - すべてのリソースが失敗")
        else:
            print(f"✅ 知識ベース結合完了 - {len(combined_content)} 件のリソース")
        
        return combined
        
    except Exception as e:
        print(f"❌ リソースコンテンツ取得で重大エラー: {str(e)}")
        import traceback
        print(f"🔍 エラー詳細:\n{traceback.format_exc()}")
        return ""

async def _get_content_from_chunks(doc_id: str, supabase) -> str:
    """chunksテーブルからドキュメントのコンテンツを取得して結合する"""
    try:
        # chunksテーブルからコンテンツを取得（document_sourcesのactiveフラグでフィルタ）
        # まずdocument_sourcesでactiveかどうかをチェック
        doc_query = supabase.table("document_sources").select("active").eq("id", doc_id).single()
        doc_result = doc_query.execute()
        
        if not doc_result.data or not doc_result.data.get("active", False):
            print(f"⚠️ ドキュメントが非アクティブまたは存在しません: {doc_id}")
            return ""
        
        # アクティブなドキュメントの場合のみchunksを取得
        chunks_query = supabase.table("chunks").select("content,chunk_index").eq("doc_id", doc_id).order("chunk_index")
        chunks_result = chunks_query.execute()
        
        if not chunks_result.data or len(chunks_result.data) == 0:
            print(f"⚠️ chunksテーブルにコンテンツが見つかりません: {doc_id}")
            return ""
        
        # チャンクをインデックス順に結合
        chunks = sorted(chunks_result.data, key=lambda x: x.get("chunk_index", 0))
        full_content = "".join([chunk.get("content", "") for chunk in chunks])
        
        print(f"📦 {len(chunks)}個のチャンクを結合: {doc_id}")
        return full_content
        
    except Exception as e:
        print(f"❌ chunksテーブルからのコンテンツ取得エラー: {str(e)}")
        return ""
