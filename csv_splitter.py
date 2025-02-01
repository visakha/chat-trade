import os
import csv
import glob
from typing import List, Optional, TextIO, Union

def split_csv_file(input_file: str, output_dir: Optional[str] = None) -> None:
    """
    Split a CSV file into multiple files based on 'Symbol' lines.
    
    Args:
        input_file (str): Path to the input CSV file
        output_dir (str, optional): Directory to save output files. 
                                    Defaults to the same directory as input file.
    """
    # If no output directory is specified, use the same directory as the input file
    if output_dir is None:
        output_dir = os.path.dirname(input_file)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize variables
    current_output_file: Optional[TextIO] = None
    current_output_writer: Optional[csv.writer] = None
    current_filename: Optional[str] = None
    
    try:
        with open(input_file, 'r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            
            for row in csv_reader:
                # Convert row to string for easier checking
                line: str = ','.join(row)
                
                # Check if line starts with 'Symbol'
                if line.startswith('Symbol'):
                    # Close previous file if it exists
                    if current_output_file:
                        current_output_file.close()
                    
                    # Create new output file using the previous line as filename
                    if current_filename:
                        output_path: str = os.path.join(output_dir, f"{current_filename}.csv")
                        current_output_file = open(output_path, 'w', newline='', encoding='utf-8')
                        current_output_writer = csv.writer(current_output_file)
                
                # Check if line starts with 'Account Total'
                if line.startswith('Account Total'):
                    # Close the current file
                    if current_output_file:
                        current_output_file.close()
                        current_output_file = None
                        current_output_writer = None
                        current_filename = None
                    continue
                
                # Write the row to the current output file
                if current_output_writer:
                    current_output_writer.writerow(row)
                
                # If not a 'Symbol' line, store as potential filename
                if not line.startswith('Symbol') and not line.startswith('Account Total'):
                    current_filename = row[0] if row else None
    
    finally:
        # Ensure all files are closed
        if current_output_file:
            current_output_file.close()

def main() -> None:
    # Find the CSV file in the resources directory
    csv_files: List[str] = glob.glob(r'c:\Users\vamsi\CascadeProjects\chat-trade\resources\do-not-share\*.csv')
    
    if not csv_files:
        print("No CSV files found in the resources directory.")
        return
    
    # Use the first CSV file found
    input_file: str = csv_files[0]
    output_dir: str = r'c:\Users\vamsi\CascadeProjects\chat-trade\resources\split_files'
    
    print(f"Splitting CSV file: {input_file}")
    split_csv_file(input_file, output_dir)
    print(f"Split files saved to: {output_dir}")

if __name__ == '__main__':
    main()
