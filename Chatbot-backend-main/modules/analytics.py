"""
分析・モニタリング機能
queue@queueu-tech.jp用の利用状況分析を提供
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from supabase_adapter import select_data, execute_query
import json

# 安全なデータ変換関数
def safe_int(value, default=0):
    """安全にintに変換する"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    if isinstance(value, dict):
        # Supabaseから辞書形式で返される場合の処理
        if 'value' in value:
            return safe_int(value['value'], default)
        if len(value) == 1:
            return safe_int(list(value.values())[0], default)
    return default

def safe_float(value, default=0.0):
    """安全にfloatに変換する"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    if isinstance(value, dict):
        # Supabaseから辞書形式で返される場合の処理
        if 'value' in value:
            return safe_float(value['value'], default)
        if len(value) == 1:
            return safe_float(list(value.values())[0], default)
    return default

def safe_str(value, default=""):
    """安全にstrに変換する"""
    if value is None:
        return default
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        # Supabaseから辞書形式で返される場合の処理
        if 'value' in value:
            return safe_str(value['value'], default)
        if len(value) == 1:
            return safe_str(list(value.values())[0], default)
    return str(value)

def get_usage_analytics(db) -> Dict[str, Any]:
    """
    queue@queueu-tech.jp用の利用状況分析を取得
    
    Returns:
        Dict containing:
        - company_usage_periods: 会社単位の累計利用期間
        - user_usage_periods: ユーザー単位の累計利用期間
        - active_users: 過去1週間のアクティブユーザー
        - plan_continuity: プラン継続数の分析
    """
    try:
        analytics = {
            "company_usage_periods": get_company_usage_periods(db),
            "user_usage_periods": get_user_usage_periods(db),
            "active_users": get_active_users(db),
            "plan_continuity": get_plan_continuity_analysis(db)
        }
        return analytics
    except Exception as e:
        print(f"分析データ取得エラー: {str(e)}")
        return {}

def get_company_usage_periods(db) -> List[Dict[str, Any]]:
    """会社単位の累計利用期間を計算"""
    try:
        # 全ユーザーと会社情報を取得
        users_result = select_data("users", columns="id,email,company_id,created_at")
        if not users_result or not users_result.data:
            return []
        
        # 全会社情報を取得
        companies_result = select_data("companies", columns="id,name")
        company_name_map = {}
        if companies_result and companies_result.data:
            for company in companies_result.data:
                company_name_map[company["id"]] = company["name"]
        
        # 会社ごとにグループ化
        companies = {}
        for user in users_result.data:
            company_id = user.get("company_id")
            company_name = company_name_map.get(company_id) or "不明な会社"
            if company_name not in companies:
                companies[company_name] = {
                    "company_name": company_name,
                    "users": [],
                    "total_usage_days": 0,
                    "earliest_start": None
                }
            companies[company_name]["users"].append(user)
        
        # 各会社の利用期間を計算
        company_analytics = []
        for company_name, company_data in companies.items():
            # 最も早い開始日を取得
            earliest_dates = [user.get("created_at") for user in company_data["users"] if user.get("created_at")]
            if earliest_dates:
                earliest_start = min(earliest_dates)
                start_date = datetime.fromisoformat(earliest_start.replace('Z', '+00:00'))
                usage_days = (datetime.now() - start_date).days
                
                company_analytics.append({
                    "company_name": company_name,
                    "user_count": len(company_data["users"]),
                    "usage_days": usage_days,
                    "start_date": earliest_start,
                    "usage_months": round(usage_days / 30.44, 1)  # 平均月日数
                })
        
        return sorted(company_analytics, key=lambda x: x["usage_days"], reverse=True)
    
    except Exception as e:
        print(f"会社別利用期間計算エラー: {str(e)}")
        return []

def get_user_usage_periods(db) -> List[Dict[str, Any]]:
    """ユーザー単位の累計利用期間を計算"""
    try:
        # 全ユーザーを取得
        users_result = select_data("users", columns="id,email,name,company_id,created_at")
        if not users_result or not users_result.data:
            return []
        
        # 全会社情報を取得
        companies_result = select_data("companies", columns="id,name")
        company_name_map = {}
        if companies_result and companies_result.data:
            for company in companies_result.data:
                company_name_map[company["id"]] = company["name"]
        
        user_analytics = []
        for user in users_result.data:
            if user.get("created_at"):
                start_date = datetime.fromisoformat(user["created_at"].replace('Z', '+00:00'))
                usage_days = (datetime.now() - start_date).days
                company_id = user.get("company_id")
                company_name = company_name_map.get(company_id) or "不明な会社"
                
                user_analytics.append({
                    "user_id": user["id"],
                    "email": user["email"],
                    "name": user.get("name", ""),
                    "company_name": company_name,
                    "usage_days": usage_days,
                    "start_date": user["created_at"],
                    "usage_months": round(usage_days / 30.44, 1)
                })
        
        return sorted(user_analytics, key=lambda x: x["usage_days"], reverse=True)
    
    except Exception as e:
        print(f"ユーザー別利用期間計算エラー: {str(e)}")
        return []

def get_active_users(db) -> Dict[str, Any]:
    """過去1週間以内にチャットを行ったアクティブユーザーを計算"""
    try:
        # 1週間前の日時を計算
        one_week_ago = datetime.now() - timedelta(days=7)
        one_week_ago_str = one_week_ago.isoformat()
        
        # 過去1週間のチャット履歴を取得
        chat_result = select_data(
            "chat_history", 
            columns="employee_id,employee_name,timestamp",
            filters={"timestamp": f"gte.{one_week_ago_str}"}
        )
        
        if not chat_result or not chat_result.data:
            return {
                "total_active_users": 0,
                "active_users_by_company": {},
                "active_users_list": []
            }
        
        # アクティブユーザーを集計
        active_users = {}
        for chat in chat_result.data:
            user_id = chat.get("employee_id")
            if user_id and user_id not in active_users:
                active_users[user_id] = {
                    "user_id": user_id,
                    "name": chat.get("employee_name", ""),
                    "last_chat": chat.get("timestamp"),
                    "chat_count": 0
                }
            if user_id:
                active_users[user_id]["chat_count"] += 1
        
        # ユーザー情報を取得して会社別に分類
        users_result = select_data("users", columns="id,email,company_id")
        companies_result = select_data("companies", columns="id,name")
        company_name_map = {}
        if companies_result and companies_result.data:
            for company in companies_result.data:
                company_name_map[company["id"]] = company["name"]
        
        user_company_map = {}
        if users_result and users_result.data:
            for user in users_result.data:
                company_id = user.get("company_id")
                company_name = company_name_map.get(company_id) or "不明な会社"
                user_company_map[user["id"]] = company_name
        
        # 会社別アクティブユーザー数を計算
        active_by_company = {}
        active_users_list = []
        
        for user_id, user_data in active_users.items():
            company = user_company_map.get(user_id, "不明")
            if company not in active_by_company:
                active_by_company[company] = 0
            active_by_company[company] += 1
            
            user_data["company_name"] = company
            active_users_list.append(user_data)
        
        return {
            "total_active_users": len(active_users),
            "active_users_by_company": active_by_company,
            "active_users_list": sorted(active_users_list, key=lambda x: x["chat_count"], reverse=True),
            "analysis_period": f"{one_week_ago.strftime('%Y-%m-%d')} から {datetime.now().strftime('%Y-%m-%d')}"
        }
    
    except Exception as e:
        print(f"アクティブユーザー計算エラー: {str(e)}")
        return {
            "total_active_users": 0,
            "active_users_by_company": {},
            "active_users_list": []
        }

def get_plan_continuity_analysis(db) -> Dict[str, Any]:
    """プラン継続数の分析"""
    try:
        # プラン履歴を取得
        from modules.database import get_plan_history
        user_histories = get_plan_history(db=db)
        
        if not user_histories:
            return {
                "total_users": 0,
                "continuity_stats": {},
                "plan_retention": {}
            }
        
        continuity_stats = {
            "never_changed": 0,  # 一度も変更していない
            "changed_once": 0,   # 1回変更
            "changed_multiple": 0,  # 複数回変更
            "demo_to_prod_stayed": 0,  # デモ→本番で継続
            "prod_to_demo_returned": 0  # 本番→デモに戻った
        }
        
        plan_retention = {
            "demo_users": 0,
            "production_users": 0,
            "demo_avg_duration": 0,
            "production_avg_duration": 0
        }
        
        demo_durations = []
        prod_durations = []
        
        for user in user_histories:
            total_changes = user.get("total_changes", 0)
            current_plan = user.get("current_plan", "")
            changes = user.get("changes", [])
            
            # 継続性統計
            if total_changes == 0:
                continuity_stats["never_changed"] += 1
            elif total_changes == 1:
                continuity_stats["changed_once"] += 1
            else:
                continuity_stats["changed_multiple"] += 1
            
            # プラン保持統計
            if current_plan == "demo":
                plan_retention["demo_users"] += 1
            elif current_plan == "production":
                plan_retention["production_users"] += 1
            
            # 期間分析
            for change in changes:
                duration = change.get("duration_days")
                if duration:
                    if change.get("from_plan") == "demo":
                        demo_durations.append(duration)
                    elif change.get("from_plan") == "production":
                        prod_durations.append(duration)
            
            # パターン分析
            if len(changes) >= 1:
                first_change = changes[-1]  # 最初の変更（配列は新しい順）
                if first_change.get("from_plan") == "demo" and first_change.get("to_plan") == "production":
                    # デモから本番に変更し、現在も本番なら継続
                    if current_plan == "production":
                        continuity_stats["demo_to_prod_stayed"] += 1
                elif first_change.get("from_plan") == "production" and first_change.get("to_plan") == "demo":
                    continuity_stats["prod_to_demo_returned"] += 1
        
        # 平均期間計算
        if demo_durations:
            plan_retention["demo_avg_duration"] = sum(demo_durations) / len(demo_durations)
        if prod_durations:
            plan_retention["production_avg_duration"] = sum(prod_durations) / len(prod_durations)
        
        return {
            "total_users": len(user_histories),
            "continuity_stats": continuity_stats,
            "plan_retention": plan_retention,
            "duration_analysis": {
                "demo_duration_samples": len(demo_durations),
                "production_duration_samples": len(prod_durations)
            }
        }
    
    except Exception as e:
        print(f"プラン継続性分析エラー: {str(e)}")
        return {
            "total_users": 0,
            "continuity_stats": {},
            "plan_retention": {}
        }

def get_enhanced_analytics(db, company_id: str = None) -> Dict[str, Any]:
    """
    強化された分析機能を取得（sumry.mdの要求項目に対応）
    
    Args:
        db: データベース接続
        company_id: 会社IDによるフィルタリング
    
    Returns:
        Dict containing:
        - resource_reference_count: 資料の参照回数
        - category_distribution_analysis: 質問カテゴリ分布と偏り
        - active_user_trends: アクティブユーザー推移
        - unresolved_and_repeat_analysis: 未解決・再質問の傾向分析
        - sentiment_analysis: 感情分析
    """
    try:
        analytics = {
            "resource_reference_count": get_resource_reference_analysis(db, company_id),
            "category_distribution_analysis": get_category_distribution_analysis(db, company_id),
            "active_user_trends": get_active_user_trends(db, company_id),
            "unresolved_and_repeat_analysis": get_unresolved_repeat_analysis(db, company_id),
            "sentiment_analysis": get_detailed_sentiment_analysis(db, company_id),
            "analysis_metadata": {
                "generated_at": datetime.now().isoformat(),
                "analysis_type": "enhanced",
                "company_id": company_id
            }
        }
        return analytics
    except Exception as e:
        print(f"強化分析データ取得エラー: {str(e)}")
        return {}

def get_resource_reference_analysis(db, company_id: str = None) -> Dict[str, Any]:
    """資料参照回数分析（CRUD操作で実装）"""
    try:
        # chat_historyテーブルから関連データを取得
        chat_filters = {}
        if company_id:
            chat_filters["company_id"] = company_id
        
        chat_result = select_data("chat_history", 
                                 columns="source_document, employee_id, timestamp, sentiment", 
                                 filters=chat_filters)
        
        if not chat_result or not chat_result.data:
            return {
                "resources": [],
                "total_references": 0,
                "most_referenced": None,
                "least_referenced": None,
                "summary": "チャット履歴データが不足しています"
            }
        
        # document_sourcesテーブルから資料情報を取得
        doc_filters = {}
        if company_id:
            doc_filters["company_id"] = company_id
        
        doc_result = select_data("document_sources", 
                                columns="name, type, id",
                                filters=doc_filters)
        
        # 資料名のマッピングを作成
        doc_mapping = {}
        if doc_result and doc_result.data:
            for doc in doc_result.data:
                doc_mapping[doc.get("name", "")] = {
                    "name": safe_str(doc.get("name", "不明")),
                    "type": safe_str(doc.get("type", "不明"))
                }
        
        # チャット履歴から参照回数を集計
        resource_stats = {}
        for chat in chat_result.data:
            source_doc = safe_str(chat.get("source_document", ""))
            if source_doc and source_doc != "" and source_doc != "None":
                if source_doc not in resource_stats:
                    doc_info = doc_mapping.get(source_doc, {"name": source_doc, "type": "不明"})
                    resource_stats[source_doc] = {
                        "name": doc_info["name"],
                        "type": doc_info["type"],
                        "reference_count": 0,
                        "unique_users": set(),
                        "unique_days": set(),
                        "last_referenced": None,
                        "sentiments": []
                    }
                
                resource_stats[source_doc]["reference_count"] += 1
                
                employee_id = safe_str(chat.get("employee_id", ""))
                if employee_id:
                    resource_stats[source_doc]["unique_users"].add(employee_id)
                
                timestamp = safe_str(chat.get("timestamp", ""))
                if timestamp:
                    date_part = timestamp.split(" ")[0] if " " in timestamp else timestamp.split("T")[0]
                    resource_stats[source_doc]["unique_days"].add(date_part)
                    resource_stats[source_doc]["last_referenced"] = timestamp
                
                sentiment = safe_str(chat.get("sentiment", "neutral"))
                resource_stats[source_doc]["sentiments"].append(sentiment)
        
        # 結果をフォーマット
        resources = []
        for source_doc, stats in resource_stats.items():
            # 平均満足度を計算（sentiment based）
            sentiments = stats["sentiments"]
            sentiment_score = 2.0  # デフォルト
            if sentiments:
                positive_count = sentiments.count("positive")
                neutral_count = sentiments.count("neutral") 
                negative_count = sentiments.count("negative")
                total_sentiments = len(sentiments)
                if total_sentiments > 0:
                    sentiment_score = (positive_count * 3 + neutral_count * 2 + negative_count * 1) / total_sentiments
            
            unique_users_count = len(stats["unique_users"])
            
            resources.append({
                "name": stats["name"],
                "type": stats["type"],
                "reference_count": stats["reference_count"],
                "unique_users": unique_users_count,
                "unique_days": len(stats["unique_days"]),
                "last_referenced": stats["last_referenced"],
                "avg_satisfaction": round(sentiment_score, 2),
                "usage_intensity": round(stats["reference_count"] / max(unique_users_count, 1), 2)
            })
        
        # 参照回数で降順ソート
        resources.sort(key=lambda x: x["reference_count"], reverse=True)
        
        total_references = sum(r["reference_count"] for r in resources)
        most_referenced = resources[0] if resources else None
        least_referenced = resources[-1] if resources else None
        
        return {
            "resources": resources,
            "total_references": total_references,
            "most_referenced": most_referenced,
            "least_referenced": least_referenced,
            "active_resources": len(resources),
            "summary": f"合計{total_references}回の資料参照があり、{len(resources)}個のリソースが利用されています"
        }
        
    except Exception as e:
        print(f"資料参照分析エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            "resources": [],
            "total_references": 0,
            "summary": f"分析エラー: {str(e)}"
        }

def get_category_distribution_analysis(db, company_id: str = None) -> Dict[str, Any]:
    """質問カテゴリ分布と偏り分析（CRUD操作で実装）"""
    try:
        # chat_historyテーブルからカテゴリ関連データを取得
        chat_filters = {}
        if company_id:
            chat_filters["company_id"] = company_id
        
        chat_result = select_data("chat_history", 
                                 columns="category, employee_id, timestamp, sentiment", 
                                 filters=chat_filters)
        
        if not chat_result or not chat_result.data:
            return {
                "categories": [],
                "distribution": {},
                "bias_analysis": {},
                "summary": "カテゴリデータが不足しています"
            }
        
        # カテゴリ別統計を集計
        category_stats = {}
        total_questions = 0
        
        for chat in chat_result.data:
            category = safe_str(chat.get("category", "")).strip()
            if not category or category == "None":
                category = "未分類"
            
            if category not in category_stats:
                category_stats[category] = {
                    "category": category,
                    "count": 0,
                    "unique_users": set(),
                    "unique_days": set(),
                    "sentiments": []
                }
            
            category_stats[category]["count"] += 1
            total_questions += 1
            
            employee_id = safe_str(chat.get("employee_id", ""))
            if employee_id:
                category_stats[category]["unique_users"].add(employee_id)
            
            timestamp = safe_str(chat.get("timestamp", ""))
            if timestamp:
                date_part = timestamp.split(" ")[0] if " " in timestamp else timestamp.split("T")[0]
                category_stats[category]["unique_days"].add(date_part)
            
            sentiment = safe_str(chat.get("sentiment", "neutral"))
            category_stats[category]["sentiments"].append(sentiment)
        
        # カテゴリリストを作成
        categories = []
        for category, stats in category_stats.items():
            sentiments = stats["sentiments"]
            
            # 感情別カウント
            positive_count = sentiments.count("positive")
            neutral_count = sentiments.count("neutral")
            negative_count = sentiments.count("negative")
            
            # 平均感情スコア計算
            if sentiments:
                avg_sentiment_score = (positive_count * 3 + neutral_count * 2 + negative_count * 1) / len(sentiments)
            else:
                avg_sentiment_score = 2.0
            
            categories.append({
                "category": category,
                "count": stats["count"],
                "unique_users": len(stats["unique_users"]),
                "unique_days": len(stats["unique_days"]),
                "avg_sentiment_score": round(avg_sentiment_score, 2),
                "positive_count": positive_count,
                "neutral_count": neutral_count,
                "negative_count": negative_count
            })
        
        # カウント順でソート
        categories.sort(key=lambda x: x["count"], reverse=True)
        
        # 分布とバイアス分析
        distribution = {}
        bias_analysis = {}
        
        for cat in categories:
            percentage = round((cat["count"] / total_questions) * 100, 2) if total_questions > 0 else 0
            distribution[cat["category"]] = {
                "count": cat["count"],
                "percentage": percentage
            }
            
            # バイアス分析（期待値からの偏差）
            expected_percentage = 100 / len(categories) if categories else 0
            bias = percentage - expected_percentage
            
            bias_analysis[cat["category"]] = {
                "bias_score": round(bias, 2),
                "is_over_represented": bias > 10,
                "is_under_represented": bias < -10,
                "sentiment_bias": "positive" if cat["avg_sentiment_score"] > 2.3 else "negative" if cat["avg_sentiment_score"] < 1.7 else "neutral"
            }
        
        # トップ3とボトム3を特定
        top_categories = categories[:3]
        bottom_categories = categories[-3:] if len(categories) > 3 else []
        
        return {
            "categories": categories,
            "distribution": distribution,
            "bias_analysis": bias_analysis,
            "top_categories": top_categories,
            "bottom_categories": bottom_categories,
            "total_questions": total_questions,
            "category_diversity": len(categories),
            "summary": f"合計{len(categories)}カテゴリで{total_questions}件の質問があり、最も多いのは'{top_categories[0]['category']}'({top_categories[0]['count']}件)です" if top_categories else "カテゴリデータが不足しています"
        }
        
    except Exception as e:
        print(f"カテゴリ分布分析エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            "categories": [],
            "distribution": {},
            "bias_analysis": {},
            "summary": f"分析エラー: {str(e)}"
        }

def get_active_user_trends(db, company_id: str = None, days: int = 30) -> Dict[str, Any]:
    """アクティブユーザー推移分析（CRUD操作で実装）"""
    try:
        from datetime import datetime, timedelta
        
        # 過去指定日数分のチャット履歴を取得
        chat_filters = {}
        if company_id:
            chat_filters["company_id"] = company_id
        
        chat_result = select_data("chat_history", 
                                 columns="employee_id, employee_name, timestamp, sentiment", 
                                 filters=chat_filters)
        
        if not chat_result or not chat_result.data:
            return {
                "daily_trends": [],
                "weekly_trends": [],
                "summary": "ユーザー活動データが不足しています"
            }
        
        # 日付フィルタリング
        start_date = datetime.now() - timedelta(days=days)
        filtered_chats = []
        
        for chat in chat_result.data:
            timestamp_str = safe_str(chat.get("timestamp", ""))
            if timestamp_str:
                try:
                    # タイムスタンプをパース
                    if "T" in timestamp_str:
                        chat_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    else:
                        chat_date = datetime.strptime(timestamp_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
                    
                    if chat_date >= start_date:
                        filtered_chats.append({
                            "employee_id": safe_str(chat.get("employee_id", "")),
                            "employee_name": safe_str(chat.get("employee_name", "")),
                            "date": chat_date.date(),
                            "sentiment": safe_str(chat.get("sentiment", "neutral"))
                        })
                except:
                    continue  # パースできない日付はスキップ
        
        # 日別統計を集計
        daily_stats = {}
        for chat in filtered_chats:
            date_str = chat["date"].strftime('%Y-%m-%d')
            
            if date_str not in daily_stats:
                daily_stats[date_str] = {
                    "date": date_str,
                    "active_users": set(),
                    "unique_names": set(),
                    "total_messages": 0,
                    "positive_count": 0
                }
            
            daily_stats[date_str]["active_users"].add(chat["employee_id"])
            daily_stats[date_str]["unique_names"].add(chat["employee_name"])
            daily_stats[date_str]["total_messages"] += 1
            
            if chat["sentiment"] == "positive":
                daily_stats[date_str]["positive_count"] += 1
        
        # 日次トレンドリストを作成
        daily_trends = []
        for date_str, stats in sorted(daily_stats.items()):
            positive_ratio = round(stats["positive_count"] / stats["total_messages"], 2) if stats["total_messages"] > 0 else 0
            
            daily_trends.append({
                "date": date_str,
                "active_users": len(stats["active_users"]),
                "total_messages": stats["total_messages"],
                "unique_names": len(stats["unique_names"]),
                "positive_ratio": positive_ratio
            })
        
        # 週次トレンド計算
        weekly_trends = []
        if daily_trends:
            for i in range(0, len(daily_trends), 7):
                week_data = daily_trends[i:i+7]
                if week_data:
                    week_start = week_data[0]["date"]
                    week_end = week_data[-1]["date"]
                    total_active = sum(d["active_users"] for d in week_data)
                    avg_active = round(total_active / len(week_data), 1)
                    total_messages = sum(d["total_messages"] for d in week_data)
                    
                    weekly_trends.append({
                        "week_start": week_start,
                        "week_end": week_end,
                        "avg_active_users": avg_active,
                        "total_messages": total_messages,
                        "days_with_activity": len([d for d in week_data if d["active_users"] > 0])
                    })
        
        # トレンド分析
        trend_direction = "insufficient_data"
        trend_percentage = 0
        
        if len(daily_trends) >= 7:
            recent_week = daily_trends[-7:]
            previous_week = daily_trends[-14:-7] if len(daily_trends) >= 14 else []
            
            recent_avg = sum(d["active_users"] for d in recent_week) / len(recent_week)
            previous_avg = sum(d["active_users"] for d in previous_week) / len(previous_week) if previous_week else recent_avg
            
            trend_direction = "increasing" if recent_avg > previous_avg else "decreasing" if recent_avg < previous_avg else "stable"
            trend_percentage = round(((recent_avg - previous_avg) / previous_avg * 100), 2) if previous_avg > 0 else 0
        
        return {
            "daily_trends": daily_trends,
            "weekly_trends": weekly_trends,
            "trend_analysis": {
                "direction": trend_direction,
                "percentage_change": trend_percentage,
                "period": f"過去{days}日間"
            },
            "peak_day": max(daily_trends, key=lambda x: x["active_users"]) if daily_trends else None,
            "total_unique_users": len(set(d["active_users"] for d in daily_trends)) if daily_trends else 0,
            "summary": f"過去{days}日間で最大{max(d['active_users'] for d in daily_trends) if daily_trends else 0}人/日のアクティブユーザーを記録"
        }
        
    except Exception as e:
        print(f"アクティブユーザー推移分析エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            "daily_trends": [],
            "weekly_trends": [],
            "summary": f"分析エラー: {str(e)}"
        }

def get_unresolved_repeat_analysis(db, company_id: str = None) -> Dict[str, Any]:
    """未解決・再質問の傾向分析（CRUD操作で実装）"""
    try:
        # chat_historyテーブルから必要なデータを取得
        chat_filters = {}
        if company_id:
            chat_filters["company_id"] = company_id
        
        chat_result = select_data("chat_history", 
                                 columns="employee_id, employee_name, user_message, bot_response, timestamp, sentiment, category", 
                                 filters=chat_filters)
        
        if not chat_result or not chat_result.data:
            return {
                "repeat_questions": [],
                "unresolved_patterns": [],
                "summary": "質問データが不足しています"
            }
        
        # ユーザー別の質問履歴を構築
        user_questions = {}
        for chat in chat_result.data:
            employee_id = safe_str(chat.get("employee_id", ""))
            if not employee_id or employee_id == "None":
                continue
                
            if employee_id not in user_questions:
                user_questions[employee_id] = []
            
            user_questions[employee_id].append({
                "message": safe_str(chat.get("user_message", "")),
                "response": safe_str(chat.get("bot_response", "")),
                "timestamp": safe_str(chat.get("timestamp", "")),
                "sentiment": safe_str(chat.get("sentiment", "neutral")),
                "category": safe_str(chat.get("category", "")),
                "response_length": len(safe_str(chat.get("bot_response", ""))),
                "employee_name": safe_str(chat.get("employee_name", ""))
            })
        
        # 各ユーザーの質問を時系列でソート
        for employee_id in user_questions:
            user_questions[employee_id].sort(key=lambda x: x["timestamp"])
        
        # 再質問パターンの検出
        repeat_questions = []
        unresolved_patterns = []
        
        for employee_id, questions in user_questions.items():
            if len(questions) < 2:
                continue
            
            for i in range(len(questions) - 1):
                current = questions[i]
                next_q = questions[i + 1]
                
                # 簡易的な類似性チェック（共通キーワードベース）
                current_words = set(current["message"].lower().split())
                next_words = set(next_q["message"].lower().split())
                
                if len(current_words) > 2 and len(next_words) > 2:
                    common_words = current_words.intersection(next_words)
                    similarity = len(common_words) / min(len(current_words), len(next_words))
                    
                    if similarity > 0.3:  # 30%以上の類似性
                        try:
                            from datetime import datetime
                            if "T" in current["timestamp"] and "T" in next_q["timestamp"]:
                                time1 = datetime.fromisoformat(current["timestamp"].replace('Z', '+00:00'))
                                time2 = datetime.fromisoformat(next_q["timestamp"].replace('Z', '+00:00'))
                                time_diff = time2 - time1
                            else:
                                time_diff = "不明"
                        except:
                            time_diff = "不明"
                        
                        repeat_questions.append({
                            "employee_id": employee_id,
                            "employee_name": current["employee_name"],
                            "first_question": current["message"][:100] + "..." if len(current["message"]) > 100 else current["message"],
                            "repeat_question": next_q["message"][:100] + "..." if len(next_q["message"]) > 100 else next_q["message"],
                            "time_between": str(time_diff),
                            "similarity_score": round(similarity, 2),
                            "first_sentiment": current["sentiment"],
                            "repeat_sentiment": next_q["sentiment"],
                            "category": current["category"]
                        })
                
                # 未解決パターンの検出（短い回答＋ネガティブ感情）
                if (current["response_length"] < 50 or 
                    current["sentiment"] == "negative" or
                    "申し訳" in current["response"] or
                    "わかりません" in current["response"]):
                    
                    unresolved_patterns.append({
                        "employee_id": employee_id,
                        "employee_name": current["employee_name"],
                        "question": current["message"][:100] + "..." if len(current["message"]) > 100 else current["message"],
                        "response": current["response"][:100] + "..." if len(current["response"]) > 100 else current["response"],
                        "timestamp": current["timestamp"],
                        "sentiment": current["sentiment"],
                        "category": current["category"],
                        "response_length": current["response_length"],
                        "issue_type": "short_response" if current["response_length"] < 50 else 
                                     "negative_sentiment" if current["sentiment"] == "negative" else
                                     "apologetic_response"
                    })
        
        # 統計情報
        total_conversations = sum(len(questions) for questions in user_questions.values())
        repeat_rate = round((len(repeat_questions) / total_conversations * 100), 2) if total_conversations > 0 else 0
        unresolved_rate = round((len(unresolved_patterns) / total_conversations * 100), 2) if total_conversations > 0 else 0
        
        return {
            "repeat_questions": sorted(repeat_questions, key=lambda x: x["similarity_score"], reverse=True)[:20],
            "unresolved_patterns": sorted(unresolved_patterns, key=lambda x: x["timestamp"], reverse=True)[:20],
            "statistics": {
                "total_conversations": total_conversations,
                "repeat_questions_count": len(repeat_questions),
                "unresolved_patterns_count": len(unresolved_patterns),
                "repeat_rate": repeat_rate,
                "unresolved_rate": unresolved_rate
            },
            "summary": f"総会話{total_conversations}件中、再質問{len(repeat_questions)}件({repeat_rate}%)、未解決パターン{len(unresolved_patterns)}件({unresolved_rate}%)を検出"
        }
        
    except Exception as e:
        print(f"未解決・再質問分析エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            "repeat_questions": [],
            "unresolved_patterns": [],
            "summary": f"分析エラー: {str(e)}"
        }

def get_detailed_sentiment_analysis(db, company_id: str = None) -> Dict[str, Any]:
    """詳細な感情分析（CRUD操作で実装）"""
    try:
        # chat_historyテーブルから感情データを取得
        chat_filters = {}
        if company_id:
            chat_filters["company_id"] = company_id
        
        chat_result = select_data("chat_history", 
                                 columns="sentiment, category, employee_id, user_message, bot_response, timestamp", 
                                 filters=chat_filters)
        
        if not chat_result or not chat_result.data:
            return {
                "sentiment_distribution": {},
                "sentiment_by_category": {},
                "temporal_sentiment": [],
                "summary": "感情分析データが不足しています"
            }
        
        # 感情分布
        sentiment_distribution = {}
        sentiment_by_category = {}
        temporal_sentiment = {}
        
        for chat in chat_result.data:
            sentiment = safe_str(chat.get("sentiment", "neutral"))
            category = safe_str(chat.get("category", "その他"))
            timestamp = safe_str(chat.get("timestamp", ""))
            
            # 日付を抽出
            if timestamp:
                date = timestamp.split(" ")[0] if " " in timestamp else timestamp.split("T")[0]
            else:
                date = "不明"
            
            # 全体の感情分布
            if sentiment not in sentiment_distribution:
                sentiment_distribution[sentiment] = 0
            sentiment_distribution[sentiment] += 1
            
            # カテゴリ別感情分布
            if category not in sentiment_by_category:
                sentiment_by_category[category] = {}
            if sentiment not in sentiment_by_category[category]:
                sentiment_by_category[category][sentiment] = 0
            sentiment_by_category[category][sentiment] += 1
            
            # 時系列感情推移
            if date not in temporal_sentiment:
                temporal_sentiment[date] = {}
            if sentiment not in temporal_sentiment[date]:
                temporal_sentiment[date][sentiment] = 0
            temporal_sentiment[date][sentiment] += 1
        
        # 感情スコア計算
        total_responses = sum(sentiment_distribution.values())
        sentiment_score = 0
        if total_responses > 0:
            sentiment_score = (
                sentiment_distribution.get("positive", 0) * 1 +
                sentiment_distribution.get("neutral", 0) * 0.5 +
                sentiment_distribution.get("negative", 0) * 0
            ) / total_responses
        
        return {
            "sentiment_distribution": sentiment_distribution,
            "sentiment_by_category": sentiment_by_category,
            "temporal_sentiment": [
                {"date": date, "sentiments": sentiments}
                for date, sentiments in sorted(temporal_sentiment.items())
            ],
            "overall_sentiment_score": round(sentiment_score, 3),
            "total_responses": total_responses,
            "summary": f"総回答{total_responses}件の感情スコア: {round(sentiment_score * 100, 1)}点/100点"
        }
        
    except Exception as e:
        print(f"詳細感情分析エラー: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            "sentiment_distribution": {},
            "sentiment_by_category": {},
            "temporal_sentiment": [],
            "summary": f"分析エラー: {str(e)}"
        }

async def generate_gemini_insights(analytics_data: Dict[str, Any], db, company_id: str = None) -> str:
    """Geminiを使用して分析データから洞察を生成（CRUD操作で実装）"""
    try:
        # Gemini設定を確認
        from modules.config import setup_gemini
        model = setup_gemini()
        
        if not model:
            return "Gemini APIが利用できません。基本的な統計分析のみ表示しています。"
        
        # 全チャット履歴を取得（CRUD操作で実装）
        chat_filters = {}
        if company_id:
            chat_filters["company_id"] = company_id
        
        chat_result = select_data("chat_history", 
                                 columns="employee_name, user_message, bot_response, timestamp, sentiment, category, company_id",
                                 filters=chat_filters)
        
        # チャット履歴をテキスト形式に変換
        chat_history_text = ""
        recent_patterns = []
        
        if chat_result and chat_result.data:
            # 最新300件の詳細なやり取りを分析用に整形
            chat_data = chat_result.data
            # タイムスタンプでソート（新しいものから）
            chat_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            for i, chat in enumerate(chat_data[:300]):
                timestamp = safe_str(chat.get('timestamp', ''))
                employee_name = safe_str(chat.get('employee_name', '匿名'))
                sentiment = safe_str(chat.get('sentiment', 'neutral'))
                user_message = safe_str(chat.get('user_message', ''))
                bot_response = safe_str(chat.get('bot_response', ''))
                category = safe_str(chat.get('category', 'なし'))
                
                # 詳細なパターン抽出
                recent_patterns.append({
                    'index': i + 1,
                    'employee': employee_name,
                    'sentiment': sentiment,
                    'question': user_message[:300],
                    'response': bot_response[:300],
                    'category': category,
                    'timestamp': timestamp[:10]  # 日付のみ
                })
            
            # 構造化されたチャット履歴テキスト
            chat_history_text = "### 最新のやり取りパターン（最新300件）\n\n"
            for pattern in recent_patterns[:50]:  # 代表的な50件を詳細表示
                chat_history_text += f"**{pattern['index']}. [{pattern['timestamp']}] {pattern['employee']} ({pattern['sentiment']})**\n"
                chat_history_text += f"質問: {pattern['question']}\n"
                chat_history_text += f"回答: {pattern['response']}\n"
                chat_history_text += f"カテゴリ: {pattern['category']}\n\n"
        
        # 詳細で実用的なプロンプトを作成
        prompt = f"""
あなたは企業のAIチャットボット分析専門家です。以下のデータから6つの分析項目に分けて回答してください。

# 📊 データ概要
- 総チャット履歴数: {len(chat_result.data) if chat_result and chat_result.data else 0}件
- 総参照回数: {analytics_data.get('resource_reference_count', {}).get('total_references', 0)}回
- アクティブリソース: {analytics_data.get('resource_reference_count', {}).get('active_resources', 0)}個
- 総質問数: {analytics_data.get('category_distribution_analysis', {}).get('total_questions', 0)}件
- カテゴリ数: {analytics_data.get('category_distribution_analysis', {}).get('category_diversity', 0)}種類
- 再質問率: {analytics_data.get('unresolved_and_repeat_analysis', {}).get('statistics', {}).get('repeat_rate', 0)}%
- 未解決率: {analytics_data.get('unresolved_and_repeat_analysis', {}).get('statistics', {}).get('unresolved_rate', 0)}%
- 感情スコア: {analytics_data.get('sentiment_analysis', {}).get('overall_sentiment_score', 0) * 100:.1f}点/100点

{chat_history_text}

# 🎯 分析要求
以下の6項目について、必ず項目番号と見出しを明記して回答してください：

**1. 利用パターン分析**
- 最も多い質問カテゴリ上位3つとその件数を明記
- 利用頻度の高い時間帯や曜日パターン
- ユーザー1人あたりの平均質問数

**2. 品質課題の特定**
- 再質問率{analytics_data.get('unresolved_and_repeat_analysis', {}).get('statistics', {}).get('repeat_rate', 0)}%の具体的原因
- 未解決率{analytics_data.get('unresolved_and_repeat_analysis', {}).get('statistics', {}).get('unresolved_rate', 0)}%の改善必要領域
- ネガティブ感情の具体的な件数と原因

**3. 優先改善項目**
- 最優先で改善すべき項目を3つ挙げ、それぞれの改善により削減できる質問数を推定
- 各改善項目の実装難易度（高/中/低）
- ROI順での優先順位

**4. ビジネス価値評価**
- 現在の時間削減効果を時間数で推定
- 月間コスト削減効果を金額で推定
- 満足度向上による定量的効果

**5. コンテンツ戦略**
- 追加すべき資料の種類を具体的に3つ
- FAQ化すべき質問パターンの具体例を件数付きで
- 既存資料の改善ポイント

**6. 実装ロードマップ**
- 短期（1ヶ月以内）：実行可能な改善項目を3つ
- 中期（3-6ヶ月）：機能拡張項目を2つ
- 長期（6ヶ月-1年）：システム発展項目を1つ

各項目は150文字程度で、必ず具体的な数値を含めて回答してください。項目ごとに明確に分けて記載してください。
"""
        
        # Geminiで分析
        response = model.generate_content(prompt)
        
        if response and hasattr(response, 'text') and response.text:
            return response.text.strip()
        else:
            return "AI分析を実行しましたが、結果を取得できませんでした。データ品質を確認してください。"
            
    except Exception as e:
        print(f"Gemini洞察生成エラー: {str(e)}")
        return f"AI分析中にエラーが発生しました: {str(e)}"
