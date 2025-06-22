"""
分析・モニタリング機能
queue@queueu-tech.jp用の利用状況分析を提供
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from supabase_adapter import select_data, execute_query
import json

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
    """資料の参照回数分析"""
    try:
        # チャット履歴から資料参照データを取得
        base_query = """
        SELECT 
            ds.name as resource_name,
            ds.type as resource_type,
            COUNT(ch.id) as reference_count,
            COUNT(DISTINCT ch.employee_id) as unique_users,
            COUNT(DISTINCT DATE(ch.timestamp)) as unique_days,
            MAX(ch.timestamp) as last_referenced,
            AVG(CASE 
                WHEN ch.sentiment = 'positive' THEN 3
                WHEN ch.sentiment = 'neutral' THEN 2
                WHEN ch.sentiment = 'negative' THEN 1
                ELSE 2
            END) as avg_satisfaction
        FROM chat_history ch
        LEFT JOIN document_sources ds ON ds.id = ANY(
            SELECT unnest(string_to_array(ch.source_document, ','))::int
        )
        WHERE ds.name IS NOT NULL
        """
        
        if company_id:
            base_query += f" AND ch.company_id = '{company_id}'"
        
        base_query += """
        GROUP BY ds.name, ds.type
        ORDER BY reference_count DESC
        """
        
        result = execute_query(base_query)
        
        if not result:
            return {
                "resources": [],
                "total_references": 0,
                "most_referenced": None,
                "least_referenced": None,
                "summary": "データが不足しています"
            }
        
        resources = []
        for row in result:
            resources.append({
                "name": row.get("resource_name", "不明"),
                "type": row.get("resource_type", "不明"),
                "reference_count": int(row.get("reference_count", 0)),
                "unique_users": int(row.get("unique_users", 0)),
                "unique_days": int(row.get("unique_days", 0)),
                "last_referenced": row.get("last_referenced"),
                "avg_satisfaction": round(float(row.get("avg_satisfaction", 2.0)), 2) if row.get("avg_satisfaction") else 2.0,
                "usage_intensity": round(int(row.get("reference_count", 0)) / max(int(row.get("unique_users", 1)), 1), 2)
            })
        
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
        return {
            "resources": [],
            "total_references": 0,
            "summary": f"分析エラー: {str(e)}"
        }

def get_category_distribution_analysis(db, company_id: str = None) -> Dict[str, Any]:
    """質問カテゴリ分布と偏り分析"""
    try:
        # カテゴリ別の詳細分析
        base_query = """
        SELECT 
            category,
            COUNT(*) as count,
            COUNT(DISTINCT employee_id) as unique_users,
            COUNT(DISTINCT DATE(timestamp)) as unique_days,
            AVG(CASE 
                WHEN sentiment = 'positive' THEN 3
                WHEN sentiment = 'neutral' THEN 2
                WHEN sentiment = 'negative' THEN 1
                ELSE 2
            END) as avg_sentiment_score,
            SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
            SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
            SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count
        FROM chat_history
        WHERE category IS NOT NULL AND category != ''
        """
        
        if company_id:
            base_query += f" AND company_id = '{company_id}'"
        
        base_query += """
        GROUP BY category
        ORDER BY count DESC
        """
        
        result = execute_query(base_query)
        
        if not result:
            return {
                "categories": [],
                "distribution": {},
                "bias_analysis": {},
                "summary": "カテゴリデータが不足しています"
            }
        
        categories = []
        total_questions = 0
        
        for row in result:
            count = int(row.get("count", 0))
            total_questions += count
            
            categories.append({
                "category": row.get("category", "不明"),
                "count": count,
                "unique_users": int(row.get("unique_users", 0)),
                "unique_days": int(row.get("unique_days", 0)),
                "avg_sentiment_score": round(float(row.get("avg_sentiment_score", 2.0)), 2),
                "positive_count": int(row.get("positive_count", 0)),
                "neutral_count": int(row.get("neutral_count", 0)),
                "negative_count": int(row.get("negative_count", 0))
            })
        
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
        top_categories = sorted(categories, key=lambda x: x["count"], reverse=True)[:3]
        bottom_categories = sorted(categories, key=lambda x: x["count"])[:3] if len(categories) > 3 else []
        
        return {
            "categories": categories,
            "distribution": distribution,
            "bias_analysis": bias_analysis,
            "top_categories": top_categories,
            "bottom_categories": bottom_categories,
            "total_questions": total_questions,
            "category_diversity": len(categories),
            "summary": f"合計{len(categories)}カテゴリで{total_questions}件の質問があり、最も多いのは'{top_categories[0]['category']}'({top_categories[0]['count']}件)です"
        }
        
    except Exception as e:
        print(f"カテゴリ分布分析エラー: {str(e)}")
        return {
            "categories": [],
            "distribution": {},
            "bias_analysis": {},
            "summary": f"分析エラー: {str(e)}"
        }

def get_active_user_trends(db, company_id: str = None, days: int = 30) -> Dict[str, Any]:
    """アクティブユーザー推移分析"""
    try:
        # 日別アクティブユーザー数
        base_query = """
        SELECT 
            DATE(timestamp) as date,
            COUNT(DISTINCT employee_id) as active_users,
            COUNT(*) as total_messages,
            COUNT(DISTINCT employee_name) as unique_names,
            AVG(CASE 
                WHEN sentiment = 'positive' THEN 1 
                ELSE 0 
            END) as positive_ratio
        FROM chat_history
        WHERE timestamp >= %s
        """
        
        if company_id:
            base_query += f" AND company_id = '{company_id}'"
        
        base_query += """
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp)
        """
        
        # 過去30日間のデータを取得
        start_date = datetime.now() - timedelta(days=days)
        params = [start_date.strftime('%Y-%m-%d')]
        
        # パラメータ置換
        formatted_query = base_query.replace('%s', f"'{params[0]}'")
        result = execute_query(formatted_query)
        
        if not result:
            return {
                "daily_trends": [],
                "weekly_trends": [],
                "summary": "ユーザー活動データが不足しています"
            }
        
        daily_trends = []
        for row in result:
            daily_trends.append({
                "date": str(row.get("date")),
                "active_users": int(row.get("active_users", 0)),
                "total_messages": int(row.get("total_messages", 0)),
                "unique_names": int(row.get("unique_names", 0)),
                "positive_ratio": round(float(row.get("positive_ratio", 0)), 2)
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
        if len(daily_trends) >= 7:
            recent_week = daily_trends[-7:]
            previous_week = daily_trends[-14:-7] if len(daily_trends) >= 14 else []
            
            recent_avg = sum(d["active_users"] for d in recent_week) / len(recent_week)
            previous_avg = sum(d["active_users"] for d in previous_week) / len(previous_week) if previous_week else recent_avg
            
            trend_direction = "increasing" if recent_avg > previous_avg else "decreasing" if recent_avg < previous_avg else "stable"
            trend_percentage = round(((recent_avg - previous_avg) / previous_avg * 100), 2) if previous_avg > 0 else 0
        else:
            trend_direction = "insufficient_data"
            trend_percentage = 0
        
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
        return {
            "daily_trends": [],
            "weekly_trends": [],
            "summary": f"分析エラー: {str(e)}"
        }

def get_unresolved_repeat_analysis(db, company_id: str = None) -> Dict[str, Any]:
    """未解決・再質問の傾向分析"""
    try:
        # 類似質問の検出（簡易版）
        base_query = """
        SELECT 
            employee_id,
            employee_name,
            user_message,
            bot_response,
            timestamp,
            sentiment,
            category,
            LENGTH(bot_response) as response_length
        FROM chat_history
        WHERE employee_id IS NOT NULL
        """
        
        if company_id:
            base_query += f" AND company_id = '{company_id}'"
        
        base_query += " ORDER BY employee_id, timestamp"
        
        result = execute_query(base_query)
        
        if not result:
            return {
                "repeat_questions": [],
                "unresolved_patterns": [],
                "summary": "質問データが不足しています"
            }
        
        # ユーザー別の質問履歴を構築
        user_questions = {}
        for row in result:
            employee_id = row.get("employee_id")
            if employee_id not in user_questions:
                user_questions[employee_id] = []
            
            user_questions[employee_id].append({
                "message": row.get("user_message", ""),
                "response": row.get("bot_response", ""),
                "timestamp": row.get("timestamp"),
                "sentiment": row.get("sentiment", "neutral"),
                "category": row.get("category", ""),
                "response_length": int(row.get("response_length", 0)),
                "employee_name": row.get("employee_name", "")
            })
        
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
                        time_diff = datetime.fromisoformat(next_q["timestamp"].replace('Z', '+00:00')) - \
                                   datetime.fromisoformat(current["timestamp"].replace('Z', '+00:00'))
                        
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
        return {
            "repeat_questions": [],
            "unresolved_patterns": [],
            "summary": f"分析エラー: {str(e)}"
        }

def get_detailed_sentiment_analysis(db, company_id: str = None) -> Dict[str, Any]:
    """詳細な感情分析"""
    try:
        # 感情分析データの取得
        base_query = """
        SELECT 
            sentiment,
            category,
            COUNT(*) as count,
            COUNT(DISTINCT employee_id) as unique_users,
            AVG(LENGTH(user_message)) as avg_question_length,
            AVG(LENGTH(bot_response)) as avg_response_length,
            DATE(timestamp) as date
        FROM chat_history
        WHERE sentiment IS NOT NULL
        """
        
        if company_id:
            base_query += f" AND company_id = '{company_id}'"
        
        base_query += """
        GROUP BY sentiment, category, DATE(timestamp)
        ORDER BY date DESC, count DESC
        """
        
        result = execute_query(base_query)
        
        if not result:
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
        
        for row in result:
            sentiment = row.get("sentiment", "neutral")
            category = row.get("category", "その他")
            date = str(row.get("date", ""))
            count = int(row.get("count", 0))
            
            # 全体の感情分布
            if sentiment not in sentiment_distribution:
                sentiment_distribution[sentiment] = 0
            sentiment_distribution[sentiment] += count
            
            # カテゴリ別感情分布
            if category not in sentiment_by_category:
                sentiment_by_category[category] = {}
            if sentiment not in sentiment_by_category[category]:
                sentiment_by_category[category][sentiment] = 0
            sentiment_by_category[category][sentiment] += count
            
            # 時系列感情推移
            if date not in temporal_sentiment:
                temporal_sentiment[date] = {}
            if sentiment not in temporal_sentiment[date]:
                temporal_sentiment[date][sentiment] = 0
            temporal_sentiment[date][sentiment] += count
        
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
        return {
            "sentiment_distribution": {},
            "sentiment_by_category": {},
            "temporal_sentiment": [],
            "summary": f"分析エラー: {str(e)}"
        }

async def generate_gemini_insights(analytics_data: Dict[str, Any], db) -> str:
    """Geminiを使用して分析データから洞察を生成"""
    try:
        # Gemini設定を確認
        from modules.config import setup_gemini
        model = setup_gemini()
        
        if not model:
            return "Gemini APIが利用できません。基本的な統計分析のみ表示しています。"
        
        # 分析データを要約してプロンプトを作成
        prompt = f"""
以下のチャットボット利用データを分析し、ビジネス改善の洞察を日本語で提供してください：

## 資料参照分析
- 総参照回数: {analytics_data.get('resource_reference_count', {}).get('total_references', 0)}回
- アクティブリソース: {analytics_data.get('resource_reference_count', {}).get('active_resources', 0)}個
- 最も参照される資料: {analytics_data.get('resource_reference_count', {}).get('most_referenced', {}).get('name', 'N/A') if analytics_data.get('resource_reference_count', {}).get('most_referenced') else 'N/A'}

## カテゴリ分析
- 総質問数: {analytics_data.get('category_distribution_analysis', {}).get('total_questions', 0)}件
- カテゴリ数: {analytics_data.get('category_distribution_analysis', {}).get('category_diversity', 0)}種類
- 主要カテゴリ: {', '.join([cat['category'] for cat in analytics_data.get('category_distribution_analysis', {}).get('top_categories', [])[:3]])}

## ユーザー活動
- トレンド: {analytics_data.get('active_user_trends', {}).get('trend_analysis', {}).get('direction', 'N/A')}
- 変化率: {analytics_data.get('active_user_trends', {}).get('trend_analysis', {}).get('percentage_change', 0)}%

## 問題パターン
- 再質問率: {analytics_data.get('unresolved_and_repeat_analysis', {}).get('statistics', {}).get('repeat_rate', 0)}%
- 未解決率: {analytics_data.get('unresolved_and_repeat_analysis', {}).get('statistics', {}).get('unresolved_rate', 0)}%

## 感情分析
- 全体感情スコア: {analytics_data.get('sentiment_analysis', {}).get('overall_sentiment_score', 0) * 100:.1f}点/100点

上記データから以下の観点で分析してください：
1. 現在の利用状況の評価
2. 発見された問題点と課題
3. 具体的な改善提案（優先度付き）
4. 期待される効果

回答は300文字以内で簡潔にまとめてください。
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
