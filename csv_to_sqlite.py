import os
import glob
import pandas as pd
import sqlite3
from typing import List, Dict, Any

def infer_column_types(df: pd.DataFrame) -> Dict[str, str]:
    """
    Infer SQLite column types based on Pandas DataFrame column types.
    
    Args:
        df (pd.DataFrame): Input DataFrame to analyze
    
    Returns:
        Dict[str, str]: Mapping of column names to SQLite column types
    """
    type_mapping = {
        'object': 'TEXT',
        'int64': 'INTEGER',
        'float64': 'REAL',
        'bool': 'INTEGER',
        'datetime64[ns]': 'DATETIME'
    }
    
    column_types = {}
    for col, dtype in df.dtypes.items():
        # Convert column name to SQLite-safe identifier
        safe_col = ''.join(c if c.isalnum() or c == '_' else '_' for c in str(col))
        
        # Map Pandas dtype to SQLite type, default to TEXT
        column_types[safe_col] = type_mapping.get(str(dtype), 'TEXT')
    
    return column_types

def csv_to_sqlite(input_dir: str, output_db: str) -> None:
    """
    Read CSV files from input directory and write to SQLite database.
    
    Args:
        input_dir (str): Directory containing CSV files
        output_db (str): Path to output SQLite database
    """
    # Find all CSV files in the input directory
    csv_files: List[str] = glob.glob(os.path.join(input_dir, '*.csv'))
    
    if not csv_files:
        print(f"No CSV files found in {input_dir}")
        return
    
    # Connect to SQLite database
    conn = sqlite3.connect(output_db)
    
    try:
        # Process each CSV file
        for csv_file in csv_files:
            # Extract table name from filename (remove .csv extension)
            table_name = os.path.splitext(os.path.basename(csv_file))[0]
            
            # Clean table name to be SQLite-safe
            safe_table_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in table_name)
            
            # Read CSV file into DataFrame
            df = pd.read_csv(csv_file, dtype=str)  # Read all columns as strings initially
            
            # Attempt to convert columns to appropriate types
            for col in df.columns:
                # Try to convert to numeric if possible
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except Exception:
                    pass
            
            # Infer column types for SQLite
            column_types = infer_column_types(df)
            
            # Create table with inferred column types
            create_table_sql = f"CREATE TABLE IF NOT EXISTS {safe_table_name} ("
            create_table_sql += ", ".join([f"{col} {dtype}" for col, dtype in column_types.items()])
            create_table_sql += ")"
            
            conn.execute(create_table_sql)
            
            # Write DataFrame to SQLite
            df.to_sql(safe_table_name, conn, if_exists='replace', index=False)
            
            print(f"Processed {csv_file} into table {safe_table_name}")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Close the database connection
        conn.close()

def main() -> None:
    # Set input and output paths
    input_dir = r'c:\Users\vamsi\CascadeProjects\chat-trade\resources\split_files'
    output_db = r'c:\Users\vamsi\CascadeProjects\chat-trade\resources\trade_data.sqlite'
    
    # Convert CSV files to SQLite database
    csv_to_sqlite(input_dir, output_db)
    
    print(f"SQLite database created at: {output_db}")

if __name__ == '__main__':
    main()
