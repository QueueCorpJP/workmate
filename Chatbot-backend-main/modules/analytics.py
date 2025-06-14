"""
分析・モニタリング機能
queue@queueu-tech.jp用の利用状況分析を提供
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from supabase_adapter import select_data

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
        # 全ユーザーを取得
        users_result = select_data("users", columns="id,email,company_name,created_at")
        if not users_result or not users_result.data:
            return []
        
        # 会社ごとにグループ化
        companies = {}
        for user in users_result.data:
            company_name = user.get("company_name") or user.get("email", "").split("@")[1]
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
        users_result = select_data("users", columns="id,email,name,company_name,created_at")
        if not users_result or not users_result.data:
            return []
        
        user_analytics = []
        for user in users_result.data:
            if user.get("created_at"):
                start_date = datetime.fromisoformat(user["created_at"].replace('Z', '+00:00'))
                usage_days = (datetime.now() - start_date).days
                
                user_analytics.append({
                    "user_id": user["id"],
                    "email": user["email"],
                    "name": user.get("name", ""),
                    "company_name": user.get("company_name", ""),
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
        users_result = select_data("users", columns="id,email,company_name")
        user_company_map = {}
        if users_result and users_result.data:
            for user in users_result.data:
                user_company_map[user["id"]] = user.get("company_name") or user.get("email", "").split("@")[1]
        
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
