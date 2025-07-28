"""
Default template categories and templates creation script
This script creates initial template data for the Workmate system
"""
import asyncio
import sys
import os
sys.path.append('.')

from modules.database import get_db, SupabaseConnection
from modules.template_management import TemplateManager
from supabase_adapter import insert_data, select_data
import uuid
from datetime import datetime

async def create_default_template_data():
    """Create default template categories and templates"""
    print("🚀 Creating default template categories and templates...")
    
    db = SupabaseConnection()
    template_manager = TemplateManager(db)
    
    try:
        # Default template categories
        default_categories = [
            {
                "name": "ビジネス基本",
                "description": "基本的なビジネスコミュニケーションテンプレート",
                "display_order": 1
            },
            {
                "name": "会議・打ち合わせ",
                "description": "会議や打ち合わせに関するテンプレート",
                "display_order": 2
            },
            {
                "name": "プロジェクト管理",
                "description": "プロジェクト管理に関するテンプレート",
                "display_order": 3
            },
            {
                "name": "営業・マーケティング",
                "description": "営業活動やマーケティングに関するテンプレート",
                "display_order": 4
            },
            {
                "name": "人事・労務",
                "description": "人事や労務管理に関するテンプレート",
                "display_order": 5
            },
            {
                "name": "カスタマーサポート",
                "description": "顧客サポートに関するテンプレート",
                "display_order": 6
            }
        ]
        
        # Create system categories (available to all companies)
        category_ids = {}
        for category in default_categories:
            category_data = {
                "id": str(uuid.uuid4()),
                "name": category["name"],
                "description": category["description"],
                "display_order": category["display_order"],
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Check if category already exists
            existing = select_data("template_categories", filters={"name": category["name"]})
            if not existing.data:
                result = insert_data("template_categories", category_data)
                if result.success:
                    category_ids[category["name"]] = category_data["id"]
                    print(f"✅ Created category: {category['name']}")
                else:
                    print(f"❌ Failed to create category: {category['name']}")
            else:
                category_ids[category["name"]] = existing.data[0]["id"]
                print(f"📋 Category already exists: {category['name']}")
        
        # Default templates
        default_templates = [
            # ビジネス基本
            {
                "category": "ビジネス基本",
                "title": "メール挨拶文",
                "description": "ビジネスメールの基本的な挨拶文テンプレート",
                "content": """{{recipient_name}}様

いつもお世話になっております。
{{company_name}}の{{sender_name}}です。

{{main_content}}

何かご不明な点がございましたら、お気軽にお声がけください。
今後ともよろしくお願いいたします。

{{sender_name}}
{{company_name}}
{{contact_info}}""",
                "variables": [
                    {"name": "recipient_name", "description": "宛先の名前", "required": True},
                    {"name": "company_name", "description": "会社名", "required": True},
                    {"name": "sender_name", "description": "送信者名", "required": True},
                    {"name": "main_content", "description": "メインの内容", "required": True},
                    {"name": "contact_info", "description": "連絡先情報", "required": False}
                ]
            },
            {
                "category": "ビジネス基本",
                "title": "お詫びメール",
                "description": "ビジネスでのお詫びメールテンプレート",
                "content": """{{recipient_name}}様

{{company_name}}の{{sender_name}}です。

この度は、{{incident_description}}につきまして、
ご迷惑をおかけし、誠に申し訳ございませんでした。

{{apology_details}}

今後このようなことがないよう、{{prevention_measures}}を実施し、
再発防止に努めてまいります。

改めて深くお詫び申し上げます。

{{sender_name}}
{{company_name}}""",
                "variables": [
                    {"name": "recipient_name", "description": "宛先の名前", "required": True},
                    {"name": "company_name", "description": "会社名", "required": True},
                    {"name": "sender_name", "description": "送信者名", "required": True},
                    {"name": "incident_description", "description": "問題の概要", "required": True},
                    {"name": "apology_details", "description": "お詫びの詳細", "required": True},
                    {"name": "prevention_measures", "description": "再発防止策", "required": True}
                ]
            },
            
            # 会議・打ち合わせ
            {
                "category": "会議・打ち合わせ",
                "title": "会議議事録",
                "description": "会議の議事録作成テンプレート",
                "content": """# {{meeting_title}} 議事録

**日時**: {{meeting_date}}
**場所**: {{meeting_location}}
**参加者**: {{participants}}
**司会**: {{facilitator}}
**記録**: {{recorder}}

## 議題
{{agenda_items}}

## 討議内容
{{discussion_points}}

## 決定事項
{{decisions}}

## アクションアイテム
{{action_items}}

## 次回予定
{{next_meeting}}

記録者: {{recorder}}
作成日: {{creation_date}}""",
                "variables": [
                    {"name": "meeting_title", "description": "会議のタイトル", "required": True},
                    {"name": "meeting_date", "description": "会議の日時", "required": True},
                    {"name": "meeting_location", "description": "会議の場所", "required": True},
                    {"name": "participants", "description": "参加者", "required": True},
                    {"name": "facilitator", "description": "司会者", "required": True},
                    {"name": "recorder", "description": "記録者", "required": True},
                    {"name": "agenda_items", "description": "議題", "required": True},
                    {"name": "discussion_points", "description": "討議内容", "required": True},
                    {"name": "decisions", "description": "決定事項", "required": True},
                    {"name": "action_items", "description": "アクションアイテム", "required": True},
                    {"name": "next_meeting", "description": "次回会議予定", "required": False},
                    {"name": "creation_date", "description": "作成日", "required": True}
                ]
            },
            
            # プロジェクト管理
            {
                "category": "プロジェクト管理",
                "title": "プロジェクト進捗報告",
                "description": "プロジェクトの進捗報告テンプレート",
                "content": """# {{project_name}} 進捗報告

**報告期間**: {{report_period}}
**報告者**: {{reporter}}
**報告日**: {{report_date}}

## プロジェクト概要
- **プロジェクト名**: {{project_name}}
- **開始日**: {{start_date}}
- **予定終了日**: {{planned_end_date}}
- **進捗率**: {{progress_percentage}}%

## 今期の成果
{{achievements}}

## 課題・問題点
{{issues}}

## 次期の予定
{{next_plans}}

## リスク・懸念事項
{{risks}}

## サポートが必要な事項
{{support_needed}}

報告者: {{reporter}}""",
                "variables": [
                    {"name": "project_name", "description": "プロジェクト名", "required": True},
                    {"name": "report_period", "description": "報告期間", "required": True},
                    {"name": "reporter", "description": "報告者", "required": True},
                    {"name": "report_date", "description": "報告日", "required": True},
                    {"name": "start_date", "description": "開始日", "required": True},
                    {"name": "planned_end_date", "description": "予定終了日", "required": True},
                    {"name": "progress_percentage", "description": "進捗率", "required": True},
                    {"name": "achievements", "description": "今期の成果", "required": True},
                    {"name": "issues", "description": "課題・問題点", "required": True},
                    {"name": "next_plans", "description": "次期の予定", "required": True},
                    {"name": "risks", "description": "リスク・懸念事項", "required": False},
                    {"name": "support_needed", "description": "サポートが必要な事項", "required": False}
                ]
            },
            
            # 営業・マーケティング
            {
                "category": "営業・マーケティング",
                "title": "営業提案書",
                "description": "営業活動での提案書テンプレート",
                "content": """# {{proposal_title}}

**提案先**: {{client_name}}様
**提案者**: {{proposer_name}}
**提案日**: {{proposal_date}}

## 提案概要
{{proposal_overview}}

## 課題認識
{{problem_statement}}

## 解決策
{{solution}}

## 提供サービス・商品
{{services_products}}

## 料金・条件
{{pricing_terms}}

## 実施スケジュール
{{implementation_schedule}}

## 期待効果
{{expected_benefits}}

## 次のステップ
{{next_steps}}

{{proposer_name}}
{{company_name}}
{{contact_information}}""",
                "variables": [
                    {"name": "proposal_title", "description": "提案書のタイトル", "required": True},
                    {"name": "client_name", "description": "クライアント名", "required": True},
                    {"name": "proposer_name", "description": "提案者名", "required": True},
                    {"name": "proposal_date", "description": "提案日", "required": True},
                    {"name": "proposal_overview", "description": "提案概要", "required": True},
                    {"name": "problem_statement", "description": "課題認識", "required": True},
                    {"name": "solution", "description": "解決策", "required": True},
                    {"name": "services_products", "description": "提供サービス・商品", "required": True},
                    {"name": "pricing_terms", "description": "料金・条件", "required": True},
                    {"name": "implementation_schedule", "description": "実施スケジュール", "required": True},
                    {"name": "expected_benefits", "description": "期待効果", "required": True},
                    {"name": "next_steps", "description": "次のステップ", "required": True},
                    {"name": "company_name", "description": "会社名", "required": True},
                    {"name": "contact_information", "description": "連絡先情報", "required": True}
                ]
            },
            
            # カスタマーサポート
            {
                "category": "カスタマーサポート",
                "title": "お客様対応メール",
                "description": "カスタマーサポートでの基本対応テンプレート",
                "content": """{{customer_name}}様

いつもご利用いただき、ありがとうございます。
{{company_name}}カスタマーサポートの{{support_staff}}です。

この度は、{{inquiry_subject}}についてお問い合わせいただき、
ありがとうございます。

{{response_content}}

{{additional_information}}

他にもご不明な点やご質問がございましたら、
お気軽にお問い合わせください。

今後ともよろしくお願いいたします。

{{support_staff}}
{{company_name}} カスタマーサポート
{{support_contact}}""",
                "variables": [
                    {"name": "customer_name", "description": "お客様の名前", "required": True},
                    {"name": "company_name", "description": "会社名", "required": True},
                    {"name": "support_staff", "description": "サポートスタッフ名", "required": True},
                    {"name": "inquiry_subject", "description": "お問い合わせ件名", "required": True},
                    {"name": "response_content", "description": "回答内容", "required": True},
                    {"name": "additional_information", "description": "追加情報", "required": False},
                    {"name": "support_contact", "description": "サポート連絡先", "required": True}
                ]
            }
        ]
        
        # Create default templates
        for template in default_templates:
            if template["category"] not in category_ids:
                print(f"⚠️ Category not found: {template['category']}")
                continue
                
            template_data = {
                "id": str(uuid.uuid4()),
                "title": template["title"],
                "template_content": template["content"],
                "description": template["description"],
                "category_id": category_ids[template["category"]],
                "company_id": None,  # System-wide template
                "created_by": None,  # System template
                "template_type": "system",
                "difficulty_level": "beginner",
                "usage_count": 0,
                "is_public": True,
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Check if template already exists
            existing = select_data("prompt_templates", filters={
                "title": template["title"],
                "template_type": "system"
            })
            
            if not existing.data:
                result = insert_data("prompt_templates", template_data)
                if result.success:
                    template_id = template_data["id"]
                    print(f"✅ Created template: {template['title']}")
                    
                    # Create template variables
                    for var in template["variables"]:
                        var_data = {
                            "id": str(uuid.uuid4()),
                            "template_id": template_id,
                            "variable_name": var["name"],
                            "variable_label": var["description"],
                            "variable_type": "text",
                            "is_required": var["required"],
                            "default_value": var.get("default_value", ""),
                            "placeholder_text": var["description"],
                            "display_order": 0,
                            "created_at": datetime.now().isoformat()
                        }
                        
                        var_result = insert_data("template_variables", var_data)
                        if var_result.success:
                            print(f"  ✅ Created variable: {var['name']}")
                        else:
                            print(f"  ❌ Failed to create variable: {var['name']}")
                else:
                    print(f"❌ Failed to create template: {template['title']}")
            else:
                print(f"📋 Template already exists: {template['title']}")
        
        print("\n🎉 Default template data creation completed!")
        
    except Exception as e:
        print(f"❌ Error creating default template data: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(create_default_template_data())