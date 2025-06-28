import pandas as pd
import json

def clean_isp_data():
    """
    Clean and restructure the ISP project data
    """
    print("Loading ISP案件一覧 data...")
    
    # Read the CSV file
    df = pd.read_csv('ISP案件一覧_data.csv')
    
    print(f"Original data shape: {df.shape}")
    
    # Find the actual header row (usually row 3 or 4)
    # Look for rows that contain meaningful column names
    header_row = None
    for i in range(min(10, len(df))):
        row_values = df.iloc[i].astype(str).tolist()
        # Check if this row contains meaningful headers
        if any('顧客番号' in str(val) or '社名' in str(val) or 'プロバイダ' in str(val) for val in row_values):
            header_row = i
            break
    
    if header_row is not None:
        print(f"Found header row at index: {header_row}")
        
        # Extract headers from the identified row
        new_headers = df.iloc[header_row].astype(str).tolist()
        
        # Clean up headers - remove newlines and extra spaces, handle duplicates
        cleaned_headers = []
        header_counts = {}
        for header in new_headers:
            if header and header != 'nan':
                cleaned_header = header.replace('\n', '').replace('\r', '').strip()
                # Handle duplicate column names
                if cleaned_header in header_counts:
                    header_counts[cleaned_header] += 1
                    cleaned_header = f"{cleaned_header}_{header_counts[cleaned_header]}"
                else:
                    header_counts[cleaned_header] = 0
                cleaned_headers.append(cleaned_header)
            else:
                cleaned_headers.append(f'Column_{len(cleaned_headers)}')
        
        # Create new dataframe with cleaned data
        data_start_row = header_row + 1
        cleaned_df = df.iloc[data_start_row:].copy()
        cleaned_df.columns = cleaned_headers[:len(cleaned_df.columns)]
        
        # Reset index
        cleaned_df = cleaned_df.reset_index(drop=True)
        
        # Remove rows that are mostly empty or contain header information
        cleaned_df = cleaned_df.dropna(how='all')
        
        # Filter out rows that contain repeated noise like "No。1プロバイダ 案件一覧表: 1"
        noise_patterns = ['No。1プロバイダ', '案件一覧表', 'ステータス', '顧客情報', '獲得情報']
        
        def is_noise_row(row):
            row_str = ' '.join(str(val) for val in row if pd.notna(val))
            return any(pattern in row_str and len(row_str) < 50 for pattern in noise_patterns)
        
        # Remove noise rows
        mask = ~cleaned_df.apply(is_noise_row, axis=1)
        cleaned_df = cleaned_df[mask]
        
        print(f"Cleaned data shape: {cleaned_df.shape}")
        print(f"Columns: {list(cleaned_df.columns)}")
        
        # Show sample of cleaned data
        print("\nSample of cleaned data:")
        print(cleaned_df.head(10).to_string())
        
        # Save cleaned data
        cleaned_df.to_csv('ISP案件一覧_cleaned.csv', index=False, encoding='utf-8-sig')
        cleaned_df.to_json('ISP案件一覧_cleaned.json', orient='records', force_ascii=False, indent=2)
        
        print(f"\nCleaned data saved to:")
        print("- ISP案件一覧_cleaned.csv")
        print("- ISP案件一覧_cleaned.json")
        
        return cleaned_df
    else:
        print("Could not identify header row")
        return None

def clean_internal_data():
    """
    Clean and restructure the internal use data
    """
    print("\n" + "="*50)
    print("Loading 社内使用分 data...")
    
    # Read the CSV file
    df = pd.read_csv('社内使用分_data.csv')
    
    print(f"Original data shape: {df.shape}")
    
    # Find the actual header row
    header_row = None
    for i in range(min(10, len(df))):
        row_values = df.iloc[i].astype(str).tolist()
        # Check if this row contains meaningful headers
        if any('拠点' in str(val) or 'プロバイダ' in str(val) or '設置先' in str(val) for val in row_values):
            header_row = i
            break
    
    if header_row is not None:
        print(f"Found header row at index: {header_row}")
        
        # Extract headers from the identified row
        new_headers = df.iloc[header_row].astype(str).tolist()
        
        # Clean up headers - handle duplicates
        cleaned_headers = []
        header_counts = {}
        for header in new_headers:
            if header and header != 'nan':
                cleaned_header = header.replace('\n', '').replace('\r', '').strip()
                # Handle duplicate column names
                if cleaned_header in header_counts:
                    header_counts[cleaned_header] += 1
                    cleaned_header = f"{cleaned_header}_{header_counts[cleaned_header]}"
                else:
                    header_counts[cleaned_header] = 0
                cleaned_headers.append(cleaned_header)
            else:
                cleaned_headers.append(f'Column_{len(cleaned_headers)}')
        
        # Create new dataframe with cleaned data
        data_start_row = header_row + 1
        cleaned_df = df.iloc[data_start_row:].copy()
        cleaned_df.columns = cleaned_headers[:len(cleaned_df.columns)]
        
        # Reset index
        cleaned_df = cleaned_df.reset_index(drop=True)
        
        # Remove rows that are mostly empty
        cleaned_df = cleaned_df.dropna(how='all')
        
        # Filter out noise rows
        noise_patterns = ['社内使用分一覧表', 'ステータス', '拠点情報', '物件情報']
        
        def is_noise_row(row):
            row_str = ' '.join(str(val) for val in row if pd.notna(val))
            return any(pattern in row_str and len(row_str) < 50 for pattern in noise_patterns)
        
        # Remove noise rows
        mask = ~cleaned_df.apply(is_noise_row, axis=1)
        cleaned_df = cleaned_df[mask]
        
        print(f"Cleaned data shape: {cleaned_df.shape}")
        print(f"Columns: {list(cleaned_df.columns)}")
        
        # Show sample of cleaned data
        print("\nSample of cleaned data:")
        print(cleaned_df.head(10).to_string())
        
        # Save cleaned data
        cleaned_df.to_csv('社内使用分_cleaned.csv', index=False, encoding='utf-8-sig')
        cleaned_df.to_json('社内使用分_cleaned.json', orient='records', force_ascii=False, indent=2)
        
        print(f"\nCleaned data saved to:")
        print("- 社内使用分_cleaned.csv")
        print("- 社内使用分_cleaned.json")
        
        return cleaned_df
    else:
        print("Could not identify header row")
        return None

def generate_summary():
    """
    Generate a summary of the extracted data
    """
    print("\n" + "="*50)
    print("DATA EXTRACTION SUMMARY")
    print("="*50)
    
    summary = {
        "extraction_date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_file": "01_ISP案件一覧.xlsx",
        "sheets_processed": [],
        "total_records": 0,
        "files_created": []
    }
    
    # Check ISP data
    try:
        isp_df = pd.read_csv('ISP案件一覧_cleaned.csv')
        isp_info = {
            "sheet_name": "ISP案件一覧",
            "records": len(isp_df),
            "columns": len(isp_df.columns),
            "column_names": list(isp_df.columns)
        }
        summary["sheets_processed"].append(isp_info)
        summary["total_records"] += len(isp_df)
        summary["files_created"].extend([
            "ISP案件一覧_data.csv", "ISP案件一覧_data.json",
            "ISP案件一覧_cleaned.csv", "ISP案件一覧_cleaned.json"
        ])
        print(f"ISP案件一覧: {len(isp_df)} records, {len(isp_df.columns)} columns")
    except:
        print("ISP案件一覧: Failed to load cleaned data")
    
    # Check internal data
    try:
        internal_df = pd.read_csv('社内使用分_cleaned.csv')
        internal_info = {
            "sheet_name": "社内使用分",
            "records": len(internal_df),
            "columns": len(internal_df.columns),
            "column_names": list(internal_df.columns)
        }
        summary["sheets_processed"].append(internal_info)
        summary["total_records"] += len(internal_df)
        summary["files_created"].extend([
            "社内使用分_data.csv", "社内使用分_data.json",
            "社内使用分_cleaned.csv", "社内使用分_cleaned.json"
        ])
        print(f"社内使用分: {len(internal_df)} records, {len(internal_df.columns)} columns")
    except:
        print("社内使用分: Failed to load cleaned data")
    
    print(f"\nTotal records extracted: {summary['total_records']}")
    print(f"Files created: {len(summary['files_created'])}")
    
    # Save summary
    with open('extraction_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print("\nExtraction summary saved to: extraction_summary.json")
    
    return summary

if __name__ == "__main__":
    print("Starting data cleaning process...")
    
    # Clean ISP data
    isp_cleaned = clean_isp_data()
    
    # Clean internal data
    internal_cleaned = clean_internal_data()
    
    # Generate summary
    summary = generate_summary()
    
    print("\n" + "="*50)
    print("DATA CLEANING COMPLETED!")
    print("="*50)
    print("All corrupted/noise data has been removed.")
    print("Clean data files are ready for use.")