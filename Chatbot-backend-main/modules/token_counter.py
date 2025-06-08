"""
トークン使用量カウンターユーティリティ
OpenAI APIのトークン使用量を正確に計算・追跡します
"""

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken not available, using fallback token counting")

import uuid
from datetime import datetime
from typing import Dict, Optional, Tuple
from decimal import Decimal

class TokenCounter:
    """トークン使用量を正確に計算するクラス"""
    
    def __init__(self):
        # モデル別の料金設定（USD per 1K tokens）
        self.pricing = {
            "gpt-4o": {
                "input": 0.0025,   # $2.50 per 1M tokens
                "output": 0.01     # $10.00 per 1M tokens
            },
            "gpt-4o-mini": {
                "input": 0.00015,  # $0.15 per 1M tokens
                "output": 0.0006   # $0.60 per 1M tokens
            },
            "gpt-4": {
                "input": 0.03,     # $30.00 per 1M tokens
                "output": 0.06     # $60.00 per 1M tokens
            },
            "gpt-3.5-turbo": {
                "input": 0.0005,   # $0.50 per 1M tokens
                "output": 0.0015   # $1.50 per 1M tokens
            }
        }
    
    def count_tokens(self, text: str, model: str = "gpt-4o-mini") -> int:
        """指定されたモデルでテキストのトークン数を計算"""
        try:
            if TIKTOKEN_AVAILABLE:
                # モデル名に基づいてエンコーディングを取得
                if "gpt-4" in model:
                    encoding_name = "cl100k_base"
                elif "gpt-3.5" in model:
                    encoding_name = "cl100k_base"
                else:
                    encoding_name = "cl100k_base"  # デフォルト
                
                encoding = tiktoken.get_encoding(encoding_name)
                tokens = encoding.encode(text)
                return len(tokens)
            else:
                # フォールバック：文字数 × 1.3の推定
                return int(len(text) * 1.3)
        except Exception as e:
            print(f"トークン計算エラー: {e}")
            # フォールバック：文字数 × 1.3の推定
            return int(len(text) * 1.3)
    
    def calculate_tokens_and_cost(
        self, 
        input_text: str, 
        output_text: str, 
        model: str = "gpt-4o-mini"
    ) -> Dict:
        """入力と出力テキストからトークン数とコストを計算"""
        
        input_tokens = self.count_tokens(input_text, model)
        output_tokens = self.count_tokens(output_text, model)
        total_tokens = input_tokens + output_tokens
        
        # コスト計算
        pricing = self.pricing.get(model, self.pricing["gpt-4o-mini"])
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_cost_usd": round(total_cost, 6),
            "model_name": model
        }

class TokenUsageTracker:
    """トークン使用量をデータベースに保存・追跡するクラス"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.counter = TokenCounter()
    
    def save_chat_with_tokens(
        self,
        user_message: str,
        bot_response: str,
        user_id: str,
        company_id: str,
        employee_id: Optional[str] = None,
        employee_name: Optional[str] = None,
        category: Optional[str] = None,
        sentiment: Optional[str] = None,
        source_document: Optional[str] = None,
        source_page: Optional[str] = None,
        model: str = "gpt-4o-mini"
    ) -> str:
        """チャット履歴をトークン情報と共にデータベースに保存"""
        
        # トークン数とコストを計算
        token_info = self.counter.calculate_tokens_and_cost(
            user_message, bot_response, model
        )
        
        # チャット履歴IDを生成
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        try:
            cursor = self.db.cursor()
            
            # chat_historyテーブルに保存
            cursor.execute("""
                INSERT INTO chat_history (
                    id, user_message, bot_response, timestamp, category, sentiment,
                    employee_id, employee_name, source_document, source_page,
                    input_tokens, output_tokens, total_tokens, model_name, cost_usd,
                    user_id, company_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                chat_id, user_message, bot_response, timestamp, category, sentiment,
                employee_id, employee_name, source_document, source_page,
                token_info["input_tokens"], token_info["output_tokens"], 
                token_info["total_tokens"], token_info["model_name"], 
                token_info["total_cost_usd"], user_id, company_id
            ))
            
            self.db.commit()
            print(f"チャット履歴保存完了: {chat_id}, トークン数: {token_info['total_tokens']}")
            
            return chat_id
            
        except Exception as e:
            print(f"チャット履歴保存エラー: {e}")
            self.db.rollback()
            raise e
    
    def get_company_monthly_usage(self, company_id: str, year_month: Optional[str] = None) -> Dict:
        """会社の月次トークン使用量を取得"""
        
        if year_month is None:
            year_month = datetime.now().strftime('%Y-%m')
        
        try:
            # データベース接続タイプを確認
            print(f"🔍 データベース接続タイプ: {type(self.db)}")
            
            # Supabase接続の場合はsupabase_adapterを使用
            if 'SupabaseConnection' in str(type(self.db)):
                print("🔍 Supabase接続を検出 - supabase_adapterを使用")
                from supabase_adapter import select_data
                
                # 基本統計を取得
                try:
                    # 全チャット履歴を取得してPythonで集計
                    chat_result = select_data(
                        "chat_history", 
                        columns="input_tokens,output_tokens,total_tokens,cost_usd,user_id",
                        filters={"company_id": company_id}
                    )
                    
                    if chat_result and chat_result.data:
                        chats = chat_result.data
                        print(f"🔍 取得したチャット数: {len(chats)}")
                        
                        # Pythonで集計
                        total_input = sum(chat.get('input_tokens', 0) or 0 for chat in chats)
                        total_output = sum(chat.get('output_tokens', 0) or 0 for chat in chats)
                        total_tokens = sum(chat.get('total_tokens', 0) or 0 for chat in chats)
                        total_cost = sum(float(chat.get('cost_usd', 0) or 0) for chat in chats)
                        active_users = len(set(chat.get('user_id') for chat in chats if chat.get('user_id')))
                        conversation_count = len(chats)
                        
                        print(f"🔍 Supabase集計結果: トークン={total_tokens}, チャット={conversation_count}")
                        
                        return {
                            "company_id": company_id,
                            "year_month": year_month or "ALL",
                            "conversation_count": conversation_count,
                            "total_input_tokens": total_input,
                            "total_output_tokens": total_output,
                            "total_tokens": total_tokens,
                            "total_cost_usd": total_cost,
                            "active_users": active_users
                        }
                    else:
                        print("⚠️ Supabaseからデータを取得できませんでした")
                        return {
                            "company_id": company_id,
                            "year_month": year_month or "ALL",
                            "conversation_count": 0,
                            "total_input_tokens": 0,
                            "total_output_tokens": 0,
                            "total_tokens": 0,
                            "total_cost_usd": 0.0,
                            "active_users": 0
                        }
                        
                except Exception as supabase_error:
                    print(f"⚠️ Supabaseクエリエラー: {supabase_error}")
                    return {
                        "company_id": company_id,
                        "year_month": year_month or "ALL",
                        "conversation_count": 0,
                        "total_input_tokens": 0,
                        "total_output_tokens": 0,
                        "total_tokens": 0,
                        "total_cost_usd": 0.0,
                        "active_users": 0
                    }
            
            # PostgreSQL直接接続の場合
            else:
                print("🔍 PostgreSQL直接接続を使用")
                cursor = self.db.cursor()
                print(f"🔍 カーソータイプ: {type(cursor)}")
                
                # まず基本的なデータ確認
                cursor.execute("""
                    SELECT COUNT(*), SUM(total_tokens), MAX(total_tokens)
                    FROM chat_history 
                    WHERE company_id = %s
                """, (company_id,))
                basic_stats = cursor.fetchone()
                print(f"🔍 基本統計: 総チャット={basic_stats[0]}, 総トークン={basic_stats[1]}, 最大トークン={basic_stats[2]}")
                
                # 全期間のデータを取得
                cursor.execute("""
                    SELECT 
                        COUNT(*) as conversation_count,
                        SUM(COALESCE(input_tokens, 0)) as total_input_tokens,
                        SUM(COALESCE(output_tokens, 0)) as total_output_tokens,
                        SUM(COALESCE(total_tokens, 0)) as total_tokens,
                        SUM(COALESCE(cost_usd, 0)) as total_cost_usd,
                        COUNT(DISTINCT user_id) as active_users
                    FROM chat_history 
                    WHERE company_id = %s 
                    AND total_tokens IS NOT NULL 
                    AND total_tokens > 0
                """, (company_id,))
                
                result = cursor.fetchone()
                print(f"🔍 PostgreSQLクエリ結果: {result}")
                
                if result:
                    return {
                        "company_id": company_id,
                        "year_month": year_month or "ALL",
                        "conversation_count": result[0] or 0,
                        "total_input_tokens": result[1] or 0,
                        "total_output_tokens": result[2] or 0,
                        "total_tokens": result[3] or 0,
                        "total_cost_usd": float(result[4] or 0),
                        "active_users": result[5] or 0
                    }
                else:
                    print("⚠️ PostgreSQL結果がNullまたは空です")
                    return {
                        "company_id": company_id,
                        "year_month": year_month or "ALL",
                        "conversation_count": 0,
                        "total_input_tokens": 0,
                        "total_output_tokens": 0,
                        "total_tokens": 0,
                        "total_cost_usd": 0.0,
                        "active_users": 0
                    }
                
        except Exception as e:
            print(f"月次使用量取得エラー: {e}")
            raise e
    
    def get_user_monthly_usage(self, user_id: str, year_month: Optional[str] = None) -> Dict:
        """ユーザーの月次トークン使用量を取得"""
        
        if not year_month:
            year_month = datetime.now().strftime('%Y-%m')
        
        try:
            cursor = self.db.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as conversation_count,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(total_tokens) as total_tokens,
                    SUM(cost_usd) as total_cost_usd
                FROM chat_history 
                WHERE user_id = %s 
                AND TO_CHAR(timestamp::timestamp, 'YYYY-MM') = %s
            """, (user_id, year_month))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    "user_id": user_id,
                    "year_month": year_month,
                    "conversation_count": result[0] or 0,
                    "total_input_tokens": result[1] or 0,
                    "total_output_tokens": result[2] or 0,
                    "total_tokens": result[3] or 0,
                    "total_cost_usd": float(result[4] or 0)
                }
            else:
                return {
                    "user_id": user_id,
                    "year_month": year_month,
                    "conversation_count": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_tokens": 0,
                    "total_cost_usd": 0.0
                }
                
        except Exception as e:
            print(f"ユーザー月次使用量取得エラー: {e}")
            raise e

def calculate_japanese_pricing(total_tokens: int) -> Dict:
    """日本円での料金計算（指定された料金体系に基づく）"""
    
    basic_plan = 150000  # 基本プラン料金（円）
    basic_limit = 25000000  # 25M tokens
    
    if total_tokens <= basic_limit:
        return {
            "total_cost_jpy": basic_plan,
            "basic_plan_cost": basic_plan,
            "tier1_cost": 0,
            "tier2_cost": 0,
            "tier3_cost": 0,
            "excess_tokens": 0
        }
    
    additional_cost = 0
    tier1_cost = 0
    tier2_cost = 0
    tier3_cost = 0
    
    excess_tokens = total_tokens - basic_limit
    
    # 第1段階：25M～50M（15円/1,000 tokens）
    if excess_tokens > 0:
        tier1_tokens = min(excess_tokens, 25000000)
        tier1_cost = (tier1_tokens / 1000) * 15
        additional_cost += tier1_cost
        excess_tokens -= tier1_tokens
    
    # 第2段階：50M～100M（12円/1,000 tokens）
    if excess_tokens > 0:
        tier2_tokens = min(excess_tokens, 50000000)
        tier2_cost = (tier2_tokens / 1000) * 12
        additional_cost += tier2_cost
        excess_tokens -= tier2_tokens
    
    # 第3段階：100M超（10円/1,000 tokens）
    if excess_tokens > 0:
        tier3_cost = (excess_tokens / 1000) * 10
        additional_cost += tier3_cost
    
    return {
        "total_cost_jpy": basic_plan + additional_cost,
        "basic_plan_cost": basic_plan,
        "tier1_cost": tier1_cost,
        "tier2_cost": tier2_cost,
        "tier3_cost": tier3_cost,
        "excess_tokens": total_tokens - basic_limit
    } 