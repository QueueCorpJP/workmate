"""
テンプレート管理モジュール
プロンプトテンプレートのCRUD操作とビジネスロジックを提供
"""
import uuid
import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from supabase_adapter import select_data, insert_data, update_data, delete_data, execute_query
from modules.database import SupabaseConnection

# Pydanticモデル定義
class TemplateVariable(BaseModel):
    variable_name: str
    variable_label: str
    variable_type: str = "text"  # text, textarea, date, select, number
    is_required: bool = True
    default_value: Optional[str] = None
    placeholder_text: Optional[str] = None
    validation_rules: Optional[Dict] = None
    display_order: int = 0

class TemplateCreate(BaseModel):
    title: str
    description: str
    template_content: str
    category_id: str
    template_type: str = "company"  # system, company, user
    difficulty_level: str = "beginner"  # beginner, intermediate, advanced
    is_public: bool = True
    variables: List[TemplateVariable] = []

class TemplateUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    template_content: Optional[str] = None
    category_id: Optional[str] = None
    difficulty_level: Optional[str] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    variables: Optional[List[TemplateVariable]] = None

class TemplateCategoryCreate(BaseModel):
    name: str
    description: str
    icon: Optional[str] = None
    display_order: int = 0
    category_type: str = "company"  # system, company

class TemplateCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None

class TemplateUsageCreate(BaseModel):
    template_id: str
    variable_values: Dict[str, Any]
    chat_history_id: Optional[str] = None

class TemplateManager:
    """テンプレート管理クラス"""
    
    def __init__(self, db: SupabaseConnection):
        self.db = db
    
    # カテゴリ管理
    async def get_categories(self, company_id: Optional[str] = None) -> List[Dict]:
        """カテゴリ一覧を取得（会社別フィルタリング）"""
        try:
            # システムカテゴリと会社カテゴリを取得
            categories = []
            
            # 1. システムカテゴリを取得（全社共通）
            system_result = select_data(
                "template_categories",
                filters={
                    "is_active": True,
                    "category_type": "system"
                },
                order="display_order asc, created_at asc"
            )
            
            if system_result.success and system_result.data:
                categories.extend(system_result.data)
            
            # 2. 会社カテゴリを取得（company_idがある場合のみ）
            if company_id:
                company_result = select_data(
                    "template_categories",
                    filters={
                        "is_active": True,
                        "category_type": "company",
                        "company_id": company_id
                    },
                    order="display_order asc, created_at asc"
                )
                
                if company_result.success and company_result.data:
                    categories.extend(company_result.data)
            
            return categories
        except Exception as e:
            print(f"カテゴリ取得エラー: {e}")
            return []
    
    async def create_category(self, category_data: TemplateCategoryCreate, created_by: str, company_id: Optional[str] = None) -> Dict:
        """新しいカテゴリを作成"""
        try:
            category_dict = {
                "id": str(uuid.uuid4()),
                "name": category_data.name,
                "description": category_data.description,
                "icon": category_data.icon,
                "display_order": category_data.display_order,
                "category_type": category_data.category_type,
                "is_active": True,
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat()
            }
            
            # category_typeに応じてcompany_idを設定
            if category_data.category_type == "company":
                if not company_id:
                    raise Exception("会社カテゴリの作成にはcompany_idが必要です")
                category_dict["company_id"] = company_id
            else:  # system
                category_dict["company_id"] = None
            
            result = insert_data("template_categories", category_dict)
            
            if result.success:
                return category_dict
            else:
                raise Exception(f"カテゴリ作成失敗: {result.error}")
        except Exception as e:
            print(f"カテゴリ作成エラー: {e}")
            raise
    
    async def update_category(self, category_id: str, category_data: TemplateCategoryUpdate, company_id: Optional[str] = None) -> Optional[Dict]:
        """カテゴリを更新"""
        try:
            # 既存カテゴリの取得と権限チェック
            existing_result = select_data(
                "template_categories",
                filters={"id": category_id}
            )
            
            if not existing_result.success or not existing_result.data:
                return None
            
            existing_category = existing_result.data[0]
            
            # 会社カテゴリの場合、権限チェック
            if existing_category.get("category_type") == "company":
                if not company_id or existing_category.get("company_id") != company_id:
                    return None
            
            # 更新データの準備
            update_dict = {"updated_at": datetime.datetime.now().isoformat()}
            
            if category_data.name is not None:
                update_dict["name"] = category_data.name
            if category_data.description is not None:
                update_dict["description"] = category_data.description
            if category_data.icon is not None:
                update_dict["icon"] = category_data.icon
            if category_data.display_order is not None:
                update_dict["display_order"] = category_data.display_order
            if category_data.is_active is not None:
                update_dict["is_active"] = category_data.is_active
            
            # カテゴリ更新
            result = update_data("template_categories", "id", category_id, update_dict)
            
            if result.success:
                # 更新されたカテゴリを取得して返す
                updated_result = select_data(
                    "template_categories",
                    filters={"id": category_id}
                )
                if updated_result.success and updated_result.data:
                    return updated_result.data[0]
            
            return None
        except Exception as e:
            print(f"カテゴリ更新エラー: {e}")
            raise
    
    async def delete_category(self, category_id: str, company_id: Optional[str] = None) -> bool:
        """カテゴリを削除（論理削除）"""
        try:
            # 既存カテゴリの取得と権限チェック
            existing_result = select_data(
                "template_categories",
                filters={"id": category_id}
            )
            
            if not existing_result.success or not existing_result.data:
                return False
            
            existing_category = existing_result.data[0]
            
            # 会社カテゴリの場合、権限チェック
            if existing_category.get("category_type") == "company":
                if not company_id or existing_category.get("company_id") != company_id:
                    return False
            
            # システムカテゴリは削除不可
            if existing_category.get("category_type") == "system":
                raise Exception("システムカテゴリは削除できません")
            
            # 論理削除
            result = update_data(
                "template_categories",
                "id",
                category_id,
                {
                    "is_active": False,
                    "updated_at": datetime.datetime.now().isoformat()
                }
            )
            
            return result.success
        except Exception as e:
            print(f"カテゴリ削除エラー: {e}")
            raise
    
    # テンプレート管理
    async def get_templates(self, company_id: Optional[str] = None, category_id: Optional[str] = None,
                          template_type: Optional[str] = None, user_id: Optional[str] = None) -> List[Dict]:
        """テンプレート一覧を取得（会社別フィルタリング）"""
        try:
            filters = {"is_active": True}
            
            # 会社レベルのフィルタリング
            if template_type == "system":
                # システムテンプレートは全社共通
                filters["template_type"] = "system"
            elif company_id:
                # 会社テンプレートまたはユーザーテンプレート
                filters["company_id"] = company_id
                if template_type:
                    filters["template_type"] = template_type
            else:
                # company_idがない場合はシステムテンプレートのみ返す
                filters["template_type"] = "system"
            
            if category_id:
                filters["category_id"] = category_id
            
            # テンプレートを取得
            result = select_data(
                "prompt_templates",
                filters=filters,
                order="usage_count desc, created_at desc"
            )
            
            if result.success and result.data:
                # 各テンプレートの変数情報も取得
                templates = []
                for template in result.data:
                    template_with_vars = await self._get_template_with_variables(template)
                    templates.append(template_with_vars)
                return templates
            return []
        except Exception as e:
            print(f"テンプレート取得エラー: {e}")
            return []
    
    async def get_template_by_id(self, template_id: str, company_id: Optional[str] = None) -> Optional[Dict]:
        """特定のテンプレートを取得"""
        try:
            result = select_data(
                "prompt_templates",
                filters={"id": template_id, "is_active": True}
            )
            
            if result.success and result.data:
                template = result.data[0]
                
                # 会社レベルのアクセス制御
                if template["template_type"] != "system" and company_id and template["company_id"] != company_id:
                    return None
                
                return await self._get_template_with_variables(template)
            return None
        except Exception as e:
            print(f"テンプレート取得エラー: {e}")
            return None
    
    async def create_template(self, template_data: TemplateCreate, company_id: str, created_by: str) -> Dict:
        """新しいテンプレートを作成"""
        try:
            template_id = str(uuid.uuid4())
            
            # テンプレート本体を作成
            template_dict = {
                "id": template_id,
                "title": template_data.title,
                "description": template_data.description,
                "template_content": template_data.template_content,
                "category_id": template_data.category_id,
                "template_type": template_data.template_type,
                "difficulty_level": template_data.difficulty_level,
                "usage_count": 0,
                "is_public": template_data.is_public,
                "is_active": True,
                "created_by": created_by,
                "company_id": company_id,
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat()
            }
            
            result = insert_data("prompt_templates", template_dict)
            
            if not result.success:
                raise Exception(f"テンプレート作成失敗: {result.error}")
            
            # 変数を作成
            if template_data.variables:
                await self._create_template_variables(template_id, template_data.variables)
            
            return await self._get_template_with_variables(template_dict)
        except Exception as e:
            print(f"テンプレート作成エラー: {e}")
            raise
    
    async def update_template(self, template_id: str, template_data: TemplateUpdate, 
                            company_id: str, user_id: str) -> Optional[Dict]:
        """テンプレートを更新"""
        try:
            # 既存テンプレートの取得と権限チェック
            existing = await self.get_template_by_id(template_id, company_id)
            if not existing:
                return None
            
            # 更新データの準備
            update_dict = {"updated_at": datetime.datetime.now().isoformat()}
            
            if template_data.title is not None:
                update_dict["title"] = template_data.title
            if template_data.description is not None:
                update_dict["description"] = template_data.description
            if template_data.template_content is not None:
                update_dict["template_content"] = template_data.template_content
            if template_data.category_id is not None:
                update_dict["category_id"] = template_data.category_id
            if template_data.difficulty_level is not None:
                update_dict["difficulty_level"] = template_data.difficulty_level
            if template_data.is_public is not None:
                update_dict["is_public"] = template_data.is_public
            if template_data.is_active is not None:
                update_dict["is_active"] = template_data.is_active
            
            # テンプレート更新
            result = update_data("prompt_templates", "id", template_id, update_dict)
            
            if not result.success:
                raise Exception(f"テンプレート更新失敗: {result.error}")
            
            # 変数の更新
            if template_data.variables is not None:
                await self._update_template_variables(template_id, template_data.variables)
            
            return await self.get_template_by_id(template_id, company_id)
        except Exception as e:
            print(f"テンプレート更新エラー: {e}")
            raise
    
    async def delete_template(self, template_id: str, company_id: str, user_id: str) -> bool:
        """テンプレートを削除（論理削除）"""
        try:
            # 権限チェック
            existing = await self.get_template_by_id(template_id, company_id)
            if not existing:
                return False
            
            # 論理削除
            result = update_data(
                "prompt_templates", 
                "id", 
                template_id, 
                {
                    "is_active": False,
                    "updated_at": datetime.datetime.now().isoformat()
                }
            )
            
            return result.success
        except Exception as e:
            print(f"テンプレート削除エラー: {e}")
            return False
    
    # テンプレート使用履歴
    async def record_template_usage(self, usage_data: TemplateUsageCreate, 
                                  user_id: str, company_id: str) -> Dict:
        """テンプレート使用履歴を記録"""
        try:
            # 実行されたプロンプトを生成
            template = await self.get_template_by_id(usage_data.template_id, company_id)
            if not template:
                raise Exception("テンプレートが見つかりません")
            
            executed_prompt = await self._replace_template_variables(
                template["template_content"], 
                usage_data.variable_values
            )
            
            usage_dict = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "template_id": usage_data.template_id,
                "company_id": company_id,
                "executed_prompt": executed_prompt,
                "variable_values": usage_data.variable_values,
                "chat_history_id": usage_data.chat_history_id,
                "execution_time_ms": 0,  # 実際の実行時間は別途計測
                "success": True,
                "used_at": datetime.datetime.now().isoformat()
            }
            
            result = insert_data("template_usage_history", usage_dict)
            
            if result.success:
                # 使用回数を更新
                await self._increment_usage_count(usage_data.template_id)
                return usage_dict
            else:
                raise Exception(f"使用履歴記録失敗: {result.error}")
        except Exception as e:
            print(f"テンプレート使用履歴記録エラー: {e}")
            raise
    
    async def get_template_usage_history(self, company_id: str, user_id: Optional[str] = None, 
                                       template_id: Optional[str] = None) -> List[Dict]:
        """テンプレート使用履歴を取得"""
        try:
            filters = {"company_id": company_id}
            
            if user_id:
                filters["user_id"] = user_id
            if template_id:
                filters["template_id"] = template_id
            
            result = select_data(
                "template_usage_history",
                filters=filters,
                order="used_at desc",
                limit=100
            )
            
            if result.success and result.data:
                return result.data
            return []
        except Exception as e:
            print(f"使用履歴取得エラー: {e}")
            return []
    
    # お気に入り管理
    async def add_to_favorites(self, template_id: str, user_id: str, company_id: str,
                             custom_title: Optional[str] = None) -> Dict:
        """テンプレートをお気に入りに追加"""
        try:
            # 既存のお気に入りをチェック
            existing_result = select_data(
                "user_template_favorites",
                filters={"user_id": user_id, "template_id": template_id}
            )
            
            if existing_result.success and existing_result.data:
                return existing_result.data[0]  # 既に存在する場合はそれを返す
            
            favorite_dict = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "template_id": template_id,
                "custom_title": custom_title,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            result = insert_data("user_template_favorites", favorite_dict)
            
            if result.success:
                return favorite_dict
            else:
                raise Exception(f"お気に入り追加失敗: {result.error}")
        except Exception as e:
            print(f"お気に入り追加エラー: {e}")
            raise
    
    async def remove_from_favorites(self, template_id: str, user_id: str) -> bool:
        """テンプレートをお気に入りから削除"""
        try:
            # 複合条件での削除のため、まず該当レコードを取得
            existing_result = select_data(
                "user_template_favorites",
                filters={"user_id": user_id, "template_id": template_id}
            )
            
            if existing_result.success and existing_result.data:
                favorite_id = existing_result.data[0]["id"]
                result = delete_data("user_template_favorites", "id", favorite_id)
                return result.success
            return True  # 既に存在しない場合は成功とみなす
        except Exception as e:
            print(f"お気に入り削除エラー: {e}")
            return False
    
    async def toggle_template_favorite(self, template_id: str, user_id: str) -> bool:
        """テンプレートのお気に入り状態をトグル"""
        try:
            # 現在のお気に入り状態をチェック
            existing_result = select_data(
                "user_template_favorites",
                filters={"user_id": user_id, "template_id": template_id}
            )
            
            if existing_result.success and existing_result.data:
                # 既にお気に入りの場合は削除
                favorite_id = existing_result.data[0]["id"]
                result = delete_data("user_template_favorites", "id", favorite_id)
                return False  # お気に入りから削除されたのでFalse
            else:
                # お気に入りでない場合は追加
                favorite_dict = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "template_id": template_id,
                    "created_at": datetime.datetime.now().isoformat()
                }
                result = insert_data("user_template_favorites", favorite_dict)
                return result.success  # お気に入りに追加されたのでTrue
        except Exception as e:
            print(f"お気に入りトグルエラー: {e}")
            return False
    
    async def get_user_favorites(self, user_id: str, company_id: str) -> List[Dict]:
        """ユーザーのお気に入りテンプレート一覧を取得"""
        try:
            result = select_data(
                "user_template_favorites",
                filters={"user_id": user_id},
                order="created_at desc"
            )
            
            if result.success and result.data:
                # 各お気に入りのテンプレート詳細も取得
                favorites = []
                for favorite in result.data:
                    template = await self.get_template_by_id(favorite["template_id"], company_id)
                    if template:
                        favorite["template"] = template
                        favorites.append(favorite)
                return favorites
            return []
        except Exception as e:
            print(f"お気に入り取得エラー: {e}")
            return []
    
    # テンプレート変数取得メソッド
    async def get_template_variables(self, template_id: str) -> List[Dict]:
        """テンプレートの変数一覧を取得"""
        try:
            variables_result = select_data(
                "template_variables",
                filters={"template_id": template_id},
                order="display_order asc"
            )
            
            if variables_result.success and variables_result.data:
                return variables_result.data
            return []
        except Exception as e:
            print(f"テンプレート変数取得エラー: {e}")
            return []
    
    # プライベートメソッド
    async def _get_template_with_variables(self, template: Dict) -> Dict:
        """テンプレートに変数情報とカテゴリ名を追加"""
        try:
            # 変数情報を取得
            variables_result = select_data(
                "template_variables",
                filters={"template_id": template["id"]},
                order="display_order asc"
            )
            
            template["variables"] = []
            if variables_result.success and variables_result.data:
                template["variables"] = variables_result.data
            
            # カテゴリ名を取得
            template["category_name"] = "カテゴリなし"  # デフォルト値
            if template.get("category_id"):
                try:
                    category_result = select_data(
                        "template_categories",
                        filters={"id": template["category_id"]}
                    )
                    if category_result.success and category_result.data and len(category_result.data) > 0:
                        template["category_name"] = category_result.data[0].get("name", "カテゴリなし")
                except Exception as e:
                    print(f"カテゴリ名取得エラー: {e}")
                    # デフォルト値を維持
            
            # フロントエンド互換性のためにcontentフィールドを追加
            template["content"] = template.get("template_content", "")
            
            return template
        except Exception as e:
            print(f"テンプレート変数取得エラー: {e}")
            return template
    
    async def _create_template_variables(self, template_id: str, variables: List[TemplateVariable]):
        """テンプレート変数を作成"""
        try:
            for variable in variables:
                variable_dict = {
                    "id": str(uuid.uuid4()),
                    "template_id": template_id,
                    "variable_name": variable.variable_name,
                    "variable_label": variable.variable_label,
                    "variable_type": variable.variable_type,
                    "is_required": variable.is_required,
                    "default_value": variable.default_value,
                    "placeholder_text": variable.placeholder_text,
                    "validation_rules": variable.validation_rules,
                    "display_order": variable.display_order,
                    "created_at": datetime.datetime.now().isoformat()
                }
                
                result = insert_data("template_variables", variable_dict)
                if not result.success:
                    print(f"変数作成失敗: {result.error}")
        except Exception as e:
            print(f"テンプレート変数作成エラー: {e}")
    
    async def _update_template_variables(self, template_id: str, variables: List[TemplateVariable]):
        """テンプレート変数を更新（既存を削除して再作成）"""
        try:
            # 既存変数を削除
            delete_data("template_variables", "template_id", template_id)
            
            # 新しい変数を作成
            await self._create_template_variables(template_id, variables)
        except Exception as e:
            print(f"テンプレート変数更新エラー: {e}")
    
    async def _replace_template_variables(self, template_content: str, variable_values: Dict[str, Any]) -> str:
        """テンプレート内の変数を実際の値に置換"""
        try:
            executed_prompt = template_content
            
            for variable_name, value in variable_values.items():
                # {{variable_name}} 形式の変数を置換
                placeholder = f"{{{{{variable_name}}}}}"
                executed_prompt = executed_prompt.replace(placeholder, str(value))
            
            return executed_prompt
        except Exception as e:
            print(f"変数置換エラー: {e}")
            return template_content
    
    async def _increment_usage_count(self, template_id: str):
        """テンプレートの使用回数を増加"""
        try:
            # 現在の使用回数を取得
            result = select_data("prompt_templates", filters={"id": template_id})
            if result.success and result.data:
                current_count = result.data[0].get("usage_count", 0)
                update_data(
                    "prompt_templates", 
                    "id", 
                    template_id, 
                    {"usage_count": current_count + 1}
                )
        except Exception as e:
            print(f"使用回数更新エラー: {e}")

# 会社設定管理
class CompanyTemplateSettingsManager:
    """会社テンプレート設定管理クラス"""
    
    def __init__(self, db: SupabaseConnection):
        self.db = db
    
    async def get_company_settings(self, company_id: str) -> Dict:
        """会社のテンプレート設定を取得"""
        try:
            result = select_data(
                "company_template_settings",
                filters={"company_id": company_id}
            )
            
            if result.success and result.data:
                return result.data[0]
            else:
                # デフォルト設定を作成
                return await self._create_default_settings(company_id)
        except Exception as e:
            print(f"会社設定取得エラー: {e}")
            return await self._create_default_settings(company_id)
    
    async def update_company_settings(self, company_id: str, settings: Dict) -> Dict:
        """会社のテンプレート設定を更新"""
        try:
            settings["updated_at"] = datetime.datetime.now().isoformat()
            
            result = update_data(
                "company_template_settings",
                "company_id",
                company_id,
                settings
            )
            
            if result.success:
                return await self.get_company_settings(company_id)
            else:
                raise Exception(f"設定更新失敗: {result.error}")
        except Exception as e:
            print(f"会社設定更新エラー: {e}")
            raise
    
    async def _create_default_settings(self, company_id: str) -> Dict:
        """デフォルトの会社設定を作成"""
        try:
            default_settings = {
                "company_id": company_id,
                "allow_user_templates": True,
                "allow_template_sharing": True,
                "max_templates_per_user": 50,
                "enable_template_analytics": True,
                "default_template_category": None,
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat()
            }
            
            result = insert_data("company_template_settings", default_settings)
            
            if result.success:
                return default_settings
            else:
                print(f"デフォルト設定作成失敗: {result.error}")
                return default_settings
        except Exception as e:
            print(f"デフォルト設定作成エラー: {e}")
            return {
                "company_id": company_id,
                "allow_user_templates": True,
                "allow_template_sharing": True,
                "max_templates_per_user": 50,
                "enable_template_analytics": True
            }