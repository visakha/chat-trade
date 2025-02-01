import os
import re
import pandas as pd

def parse_positions_file(file_path):
    """
    Parse a positions CSV file and return a dictionary of DataFrames.
    
    Args:
        file_path (str): Path to the positions CSV file
    
    Returns:
        dict: A dictionary containing parsed DataFrames
    """
    # Read the file with specific parsing logic
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Extract timestamp from the first line
    timestamp_match = re.search(r'as of (.*), (\d{2}/\d{2}/\d{4})', lines[0])
    timestamp = timestamp_match.group(0) if timestamp_match else "Unknown Timestamp"
    
    # Find the start of the actual data (header row)
    header_index = next(i for i, line in enumerate(lines) if "Symbol" in line)
    
    # Read the CSV, skipping the first few rows
    df = pd.read_csv(file_path, skiprows=header_index, thousands=',', 
                     dtype={
                         'Symbol': str, 
                         'Qty (Quantity)': float, 
                         'Price': str, 
                         'Mkt Val (Market Value)': str,
                         'Day Chng % (Day Change %)': str,
                         'Day Chng $ (Day Change $)': str,
                         'Cost Basis': str,
                         'Gain $ (Gain/Loss $)': str,
                         'Gain % (Gain/Loss %)': str
                     })
    
    # Clean up column names
    df.columns = [col.split(' (')[0] if ' (' in col else col for col in df.columns]
    
    # Create a dictionary of DataFrames
    parsed_data = {
        'timestamp': timestamp,
        'positions': df[df['Symbol'].isin(['Cash & Cash Investments', 'Account Total']) == False],
        'cash': df[df['Symbol'] == 'Cash & Cash Investments'],
        'account_total': df[df['Symbol'] == 'Account Total']
    }
    
    return parsed_data

def main():
    # Dynamically find the CSV file in the resources/do-not-share directory
    resources_dir = os.path.join(os.path.dirname(__file__), 'resources', 'do-not-share')
    
    # Find the first CSV file in the directory
    csv_files = [f for f in os.listdir(resources_dir) if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in the resources/do-not-share directory.")
        return
    
    file_path = os.path.join(resources_dir, csv_files[0])
    
    try:
        positions_dict = parse_positions_file(file_path)
        
        # Print out some basic information
        print("Timestamp:", positions_dict['timestamp'])
        print("\nPositions Summary:")
        print(positions_dict['positions'].head())
        print("\nCash:", positions_dict['cash'])
        print("\nAccount Total:", positions_dict['account_total'])
    
    except Exception as e:
        print(f"Error parsing positions file: {e}")

if __name__ == '__main__':
    main()
