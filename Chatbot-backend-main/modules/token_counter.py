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
            "gemini-2.5-flash": {
                "input": 0.000667,  # ¥0.100 per 1K tokens (0.100/150 USD)
                "output": 0.006     # ¥0.900 per 1K tokens (0.900/150 USD)
            },
            "gpt-4": {
                "input": 0.03,     # $30.00 per 1M tokens
                "output": 0.06     # $60.00 per 1M tokens
            },
            "gpt-3.5-turbo": {
                "input": 0.0005,   # $0.50 per 1M tokens
                "output": 0.0015   # $1.50 per 1M tokens
            },
            # 新しい料金設定（基本料金）
            "workmate-standard": {
                "input": 0.0003,   # $0.30 per 1M tokens
                "output": 0.0025   # $2.50 per 1M tokens
            },
            # Gemini料金設定（新料金体系）
            "gemini-pro": {
                "input": 0.000667,  # ¥0.100 per 1K tokens (0.100/150 USD)
                "output": 0.006     # ¥0.900 per 1K tokens (0.900/150 USD)
            },
            "gemini-1.5-pro": {
                "input": 0.0003,   # $0.30 per 1M tokens
                "output": 0.0025   # $2.50 per 1M tokens
            },
            # 8倍販売価格料金体系（no1株式会社専用）
            "no1-premium": {
                "input_low": 0.01,      # $10.00 per 1M tokens (～200,000トークン)
                "output_low": 0.08,     # $80.00 per 1M tokens (～200,000トークン) 
                "input_high": 0.02,     # $20.00 per 1M tokens (200,000トークン超)
                "output_high": 0.12,    # $120.00 per 1M tokens (200,000トークン超)
                "threshold": 200000     # トークン閾値
            }
        }
        
        # プロンプト参照による追加料金（JPY per reference）- 新料金体系
        self.prompt_reference_cost = 0.50  # ¥0.50 per prompt reference
    
    def count_tokens(self, text: str, model: str = "gemini-2.5-flash") -> int:
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
        model: str = "gemini-2.5-flash"
    ) -> Dict:
        """入力と出力テキストからトークン数とコストを計算"""
        
        input_tokens = self.count_tokens(input_text, model)
        output_tokens = self.count_tokens(output_text, model)
        total_tokens = input_tokens + output_tokens
        
        # コスト計算
        pricing = self.pricing.get(model, self.pricing["gemini-2.5-flash"])
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
    
    def calculate_tokens_and_cost_with_prompts(
        self, 
        input_text: str, 
        output_text: str, 
        prompt_references: int = 0,
        model: str = "gemini-2.5-flash"
    ) -> Dict:
        """入力と出力テキスト、参照プロンプト数からトークン数とコストを計算"""
        
        input_tokens = self.count_tokens(input_text, model)
        output_tokens = self.count_tokens(output_text, model)
        total_tokens = input_tokens + output_tokens
        
        # 基本コスト計算
        pricing = self.pricing.get(model, self.pricing["gemini-2.5-flash"])
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        base_cost = input_cost + output_cost
        
        # プロンプト参照による追加コスト（JPYからUSDに変換）
        prompt_cost = prompt_references * (self.prompt_reference_cost / 150)
        total_cost = base_cost + prompt_cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "prompt_references": prompt_references,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "base_cost_usd": round(base_cost, 6),
            "prompt_cost_usd": round(prompt_cost, 6),
            "total_cost_usd": round(total_cost, 6),
            "model_name": model
        }
    
    def calculate_no1_premium_cost(
        self,
        input_text: str,
        output_text: str,
        model: str = "no1-premium"
    ) -> Dict:
        """no1株式会社専用：8倍販売価格料金体系での計算"""
        
        input_tokens = self.count_tokens(input_text, model)
        output_tokens = self.count_tokens(output_text, model)
        total_tokens = input_tokens + output_tokens
        
        # no1-premium料金設定を取得
        pricing = self.pricing["no1-premium"]
        threshold = pricing["threshold"]
        
        # 入力トークンの料金計算
        if input_tokens <= threshold:
            input_cost = (input_tokens / 1000) * pricing["input_low"]
        else:
            # 閾値以下の部分
            low_input_cost = (threshold / 1000) * pricing["input_low"]
            # 閾値超過の部分
            high_input_tokens = input_tokens - threshold
            high_input_cost = (high_input_tokens / 1000) * pricing["input_high"]
            input_cost = low_input_cost + high_input_cost
        
        # 出力トークンの料金計算
        if output_tokens <= threshold:
            output_cost = (output_tokens / 1000) * pricing["output_low"]
        else:
            # 閾値以下の部分
            low_output_cost = (threshold / 1000) * pricing["output_low"]
            # 閾値超過の部分
            high_output_tokens = output_tokens - threshold
            high_output_cost = (high_output_tokens / 1000) * pricing["output_high"]
            output_cost = low_output_cost + high_output_cost
        
        total_cost = input_cost + output_cost
        
        # 具体例の計算
        example_cost_per_chat = self._calculate_typical_chat_cost()
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_cost_usd": round(total_cost, 6),
            "model_name": model,
            "pricing_tier": "no1-premium",
            "example_cost_per_chat": example_cost_per_chat,
            "cost_breakdown": {
                "input_low_tier": min(input_tokens, threshold),
                "input_high_tier": max(0, input_tokens - threshold),
                "output_low_tier": min(output_tokens, threshold),
                "output_high_tier": max(0, output_tokens - threshold)
            }
        }
    
    def _calculate_typical_chat_cost(self) -> Dict:
        """典型的なチャットの料金例を計算"""
        
        # 典型的なチャットのパターン
        examples = {
            "short_chat": {
                "description": "短い質問（～100トークン入力、～300トークン出力）",
                "input_tokens": 100,
                "output_tokens": 300
            },
            "medium_chat": {
                "description": "標準的な質問（～500トークン入力、～1500トークン出力）", 
                "input_tokens": 500,
                "output_tokens": 1500
            },
            "long_chat": {
                "description": "長い質問（～2000トークン入力、～5000トークン出力）",
                "input_tokens": 2000,
                "output_tokens": 5000
            }
        }
        
        pricing = self.pricing["no1-premium"]
        results = {}
        
        for key, example in examples.items():
            input_tokens = example["input_tokens"]
            output_tokens = example["output_tokens"]
            
            # 入力コスト計算
            input_cost = (input_tokens / 1000) * pricing["input_low"]
            
            # 出力コスト計算  
            output_cost = (output_tokens / 1000) * pricing["output_low"]
            
            total_cost = input_cost + output_cost
            
            results[key] = {
                "description": example["description"],
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": round(total_cost, 4),
                "cost_jpy": round(total_cost * 150, 2)  # 1USD=150円で計算
            }
        
        return results
    
    def get_pricing_model_for_company(self, company_id: str) -> str:
        """会社IDに基づいて適用する料金モデルを決定"""
        
        # no1株式会社の実際のcompany_ID
        NO1_COMPANY_ID = "77acc2e2-ce67-458d-bd38-7af0476b297a"
        
        if company_id == NO1_COMPANY_ID:
            return "no1-premium"
        else:
            return "gemini-2.5-flash"  # その他の会社は新料金体系
    
    def calculate_cost_by_company(
        self,
        input_text: str,
        output_text: str,
        company_id: str = None,
        prompt_references: int = 0
    ) -> Dict:
        """会社IDに基づいて適切な料金体系で計算"""
        
        if not company_id:
            # company_idが提供されない場合は従来の料金体系
            return self.calculate_tokens_and_cost_with_prompts(
                input_text, output_text, prompt_references, "gemini-2.5-flash"
            )
        
        # Premium Plan（月額固定）の場合は料金0で記録
        if self.is_premium_plan_company(company_id):
            input_tokens = self.count_tokens(input_text)
            output_tokens = self.count_tokens(output_text)
            total_tokens = input_tokens + output_tokens
            
            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "prompt_references": prompt_references,
                "input_cost_usd": 0.0,
                "output_cost_usd": 0.0,
                "base_cost_usd": 0.0,
                "prompt_cost_usd": 0.0,
                "total_cost_usd": 0.0,
                "model_name": "premium-plan",
                "pricing_tier": "premium_fixed",
                "is_premium_plan": True,
                "monthly_fixed_cost_jpy": 30000
            }
        
        pricing_model = self.get_pricing_model_for_company(company_id)
        
        if pricing_model == "no1-premium":
            # no1株式会社は新料金体系（従量課金用・現在は使用しない）
            result = self.calculate_no1_premium_cost(input_text, output_text, pricing_model)
            
            # プロンプト参照コストを追加
            if prompt_references > 0:
                prompt_cost = prompt_references * (self.prompt_reference_cost / 150)
                result["prompt_references"] = prompt_references
                result["prompt_cost_usd"] = round(prompt_cost, 6)
                result["total_cost_usd"] = round(result["total_cost_usd"] + prompt_cost, 6)
            
            return result
        else:
            # その他の会社は従来の料金体系（直接計算）
            input_tokens = self.count_tokens(input_text)
            output_tokens = self.count_tokens(output_text)
            total_tokens = input_tokens + output_tokens
            
            # gemini-2.5-flashの料金設定を使用
            model_pricing = self.pricing.get("gemini-2.5-flash", {})
            input_rate = model_pricing.get("input", 0.000667)
            output_rate = model_pricing.get("output", 0.006)
            
            input_cost = (input_tokens / 1000) * input_rate
            output_cost = (output_tokens / 1000) * output_rate
            base_cost = input_cost + output_cost
            
            # プロンプト参照コスト
            prompt_cost = prompt_references * (self.prompt_reference_cost / 150)
            total_cost = base_cost + prompt_cost
            
            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "prompt_references": prompt_references,
                "input_cost_usd": round(input_cost, 6),
                "output_cost_usd": round(output_cost, 6),
                "base_cost_usd": round(base_cost, 6),
                "prompt_cost_usd": round(prompt_cost, 6),
                "total_cost_usd": round(total_cost, 6),
                "model_name": "gemini-2.5-flash",
                "pricing_tier": "standard",
                "is_premium_plan": False
            }
    
    def is_premium_plan_company(self, company_id: str) -> bool:
        """会社がPremium Plan（月額固定）かどうか判定"""
        
        # no1株式会社の実際のcompany_ID（実際のデータに基づく）
        NO1_COMPANY_ID = "77acc2e2-ce67-458d-bd38-7af0476b297a"
        
        print(f"🔍 Premium Plan判定:")
        print(f"   入力company_id: '{company_id}'")
        print(f"   NO1_COMPANY_ID: '{NO1_COMPANY_ID}'")
        print(f"   判定結果: {company_id == NO1_COMPANY_ID}")
        print(f"   company_id type: {type(company_id)}")
        print(f"   NO1_COMPANY_ID type: {type(NO1_COMPANY_ID)}")
        
        return company_id == NO1_COMPANY_ID

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
        company_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        employee_name: Optional[str] = None,
        category: Optional[str] = None,
        sentiment: Optional[str] = None,
        source_document: Optional[str] = None,
        source_page: Optional[str] = None,
        model: str = "gemini-2.5-flash"
    ) -> str:
        """チャット履歴をトークン情報と共にデータベースに保存"""
        
        # トークン数とコストを計算
        token_info = self.counter.calculate_tokens_and_cost(
            user_message, bot_response, model
        )
        
        # チャット履歴IDを生成
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # company_idがNoneの場合はデフォルト値を設定
        if company_id is None:
            print(f"⚠️ company_idがNullです。デフォルト値'default'を使用します。")
            company_id = "default"
        
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
    
    def save_chat_with_prompts(
        self,
        user_message: str,
        bot_response: str,
        user_id: str,
        prompt_references: int = 0,
        company_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        employee_name: Optional[str] = None,
        category: Optional[str] = None,
        sentiment: Optional[str] = None,
        source_document: Optional[str] = None,
        source_page: Optional[str] = None,
        model: str = "gemini-2.5-flash"
    ) -> str:
        """プロンプト参照数を含むチャット履歴をデータベースに保存"""
        
        # トークン数とコストを計算（プロンプト参照含む）
        token_info = self.counter.calculate_tokens_and_cost_with_prompts(
            user_message, bot_response, prompt_references, model
        )
        
        # チャット履歴IDを生成
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # company_idがNoneの場合はデフォルト値を設定
        if company_id is None:
            print(f"⚠️ company_idがNullです。デフォルト値'default'を使用します。")
            company_id = "default"
        
        try:
            cursor = self.db.cursor()
            
            # chat_historyテーブルに保存（新しいカラムを追加）
            cursor.execute("""
                INSERT INTO chat_history (
                    id, user_message, bot_response, timestamp, category, sentiment,
                    employee_id, employee_name, source_document, source_page,
                    input_tokens, output_tokens, total_tokens, model_name, cost_usd,
                    user_id, company_id, prompt_references, base_cost_usd, prompt_cost_usd
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                chat_id, user_message, bot_response, timestamp, category, sentiment,
                employee_id, employee_name, source_document, source_page,
                token_info["input_tokens"], token_info["output_tokens"], 
                token_info["total_tokens"], token_info["model_name"], 
                token_info["total_cost_usd"], user_id, company_id,
                token_info["prompt_references"], token_info["base_cost_usd"], 
                token_info["prompt_cost_usd"]
            ))
            
            self.db.commit()
            print(f"チャット履歴保存完了: {chat_id}, トークン数: {token_info['total_tokens']}, プロンプト参照: {prompt_references}")
            
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