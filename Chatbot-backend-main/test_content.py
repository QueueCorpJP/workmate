import asyncio
from modules.template_management import TemplateManager
from modules.database import SupabaseConnection

async def test_template_content():
    """テンプレート内容取得をテスト"""
    print("=== テンプレート内容取得テスト ===")
    
    db = SupabaseConnection()
    template_manager = TemplateManager(db)
    company_id = "5d1b1448-72dc-4506-87ad-05a326298179"
    
    templates = await template_manager.get_templates(company_id)
    print(f"取得したテンプレート数: {len(templates)}")
    
    if templates:
        template = templates[0]
        print(f"\n最初のテンプレート:")
        print(f"  ID: {template.get('id')}")
        print(f"  Title: {template.get('title')}")
        print(f"  Template Content: {repr(template.get('template_content', 'NOT_SET'))}")
        print(f"  Content Field: {repr(template.get('content', 'NOT_SET'))}")
        print(f"  Category Name: {template.get('category_name', 'NOT_SET')}")
        
        # 特定のテンプレートを取得してテスト
        specific_template = await template_manager.get_template_by_id(template['id'], company_id)
        if specific_template:
            print(f"\n特定テンプレート取得:")
            print(f"  Template Content: {repr(specific_template.get('template_content', 'NOT_SET'))}")
            print(f"  Content Field: {repr(specific_template.get('content', 'NOT_SET'))}")

if __name__ == "__main__":
    asyncio.run(test_template_content()) 