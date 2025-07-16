import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_adapter import select_data

def check_database_content():
    """データベースの実際の内容を確認"""
    print("🔍 データベース内容確認開始")
    
    # 1. 全体データの確認
    print("\n=== 1. 全体データ確認 ===")
    all_data = select_data("chunks", columns="*", limit=10)
    print(f"全件数確認用サンプル: {len(all_data.data) if all_data.data else 0}件")
    
    if all_data.data:
        sample = all_data.data[0]
        print(f"サンプルデータ構造:")
        print(f"  - ID: {sample.get('id', 'N/A')}")
        print(f"  - 会社ID: {sample.get('company_id', 'N/A')}")
        print(f"  - コンテンツ長: {len(sample.get('content', ''))}")
        print(f"  - コンテンツサンプル: {sample.get('content', '')[:100]}...")
    
    # 2. 実際の会社IDでデータ確認
    print("\n=== 2. 実際の会社IDでデータ確認 ===")
    real_company_id = "5d1b1448-72dc-4506-87ad-05a326298179"
    company_data = select_data("chunks", 
                              columns="*", 
                              filters={"company_id": real_company_id}, 
                              limit=20)
    
    print(f"会社ID {real_company_id} のデータ: {len(company_data.data) if company_data.data else 0}件")
    
    # 3. 物件番号を含むデータの検索
    print("\n=== 3. 物件番号を含むデータの検索 ===")
    target_properties = ["WPD4100399", "WPD4100389", "WPD1100476", "WPN1100006"]
    
    if company_data.data:
        for prop_number in target_properties:
            print(f"\n--- {prop_number} の検索 ---")
            found_count = 0
            found_samples = []
            
            for i, chunk in enumerate(company_data.data):
                content = chunk.get('content', '').upper()  # 大文字小文字を無視
                if prop_number in content:
                    found_count += 1
                    found_samples.append({
                        'index': i,
                        'id': chunk.get('id'),
                        'snippet': content[content.find(prop_number):content.find(prop_number)+100]
                    })
            
            print(f"  {prop_number}: {found_count}件見つかりました")
            for sample in found_samples[:2]:  # 最初の2件を表示
                print(f"    ID: {sample['id']}")
                print(f"    抜粋: {sample['snippet']}...")
    
    # 4. 全データから物件番号を検索（会社IDフィルタなし）
    print("\n=== 4. 全データから物件番号を検索（会社IDフィルタなし） ===")
    all_chunks = select_data("chunks", columns="*", limit=200)
    
    if all_chunks.data:
        print(f"全データ検索対象: {len(all_chunks.data)}件")
        
        for prop_number in target_properties:
            print(f"\n--- 全データから {prop_number} を検索 ---")
            found_count = 0
            found_companies = set()
            
            for chunk in all_chunks.data:
                content = chunk.get('content', '').upper()
                if prop_number in content:
                    found_count += 1
                    found_companies.add(chunk.get('company_id', 'Unknown'))
                    if found_count <= 2:  # 最初の2件を詳細表示
                        print(f"  見つかった！")
                        print(f"    会社ID: {chunk.get('company_id')}")
                        print(f"    チャンクID: {chunk.get('id')}")
                        snippet_start = max(0, content.find(prop_number) - 50)
                        snippet_end = min(len(content), content.find(prop_number) + 150)
                        print(f"    内容: ...{content[snippet_start:snippet_end]}...")
            
            print(f"  {prop_number}: 全体で{found_count}件、{len(found_companies)}社に存在")
            print(f"  関連会社ID: {list(found_companies)}")
    
    print("\n🏁 データベース内容確認完了")

if __name__ == "__main__":
    check_database_content() 