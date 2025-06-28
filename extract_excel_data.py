import pandas as pd
import sys
import os

def extract_excel_data(file_path):
    """
    Extract data from Excel file and save as CSV
    """
    try:
        # Try to read the Excel file
        print(f"Reading Excel file: {file_path}")
        
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        print(f"Found sheets: {excel_file.sheet_names}")
        
        # Extract data from each sheet
        for sheet_name in excel_file.sheet_names:
            print(f"\nProcessing sheet: {sheet_name}")
            
            # Read the sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            print(f"Sheet dimensions: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            
            # Display first few rows
            print("\nFirst 10 rows:")
            print(df.head(10).to_string())
            
            # Save as CSV
            output_file = f"{sheet_name}_data.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"Saved data to: {output_file}")
            
            # Also save as JSON for better structure
            json_output = f"{sheet_name}_data.json"
            df.to_json(json_output, orient='records', force_ascii=False, indent=2)
            print(f"Saved data to: {json_output}")
            
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        
        # Try alternative methods
        try:
            print("Trying alternative reading method...")
            df = pd.read_excel(file_path, engine='openpyxl')
            print(f"Successfully read with openpyxl engine")
            print(f"Data shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("\nFirst 10 rows:")
            print(df.head(10).to_string())
            
            # Save the data
            df.to_csv("extracted_data.csv", index=False, encoding='utf-8-sig')
            df.to_json("extracted_data.json", orient='records', force_ascii=False, indent=2)
            
        except Exception as e2:
            print(f"Alternative method also failed: {e2}")

if __name__ == "__main__":
    file_path = "01_ISP案件一覧.xlsx"
    
    if os.path.exists(file_path):
        extract_excel_data(file_path)
    else:
        print(f"File not found: {file_path}")