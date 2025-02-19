import pandas as pd
import numpy as np
import os
import time
from datetime import datetime
import shutil

# Define input and output directories
INPUT_DIR = "/Users/aahilali/Desktop/ArangoDBInput"
OUTPUT_DIR = "/Users/aahilali/Desktop/ArangoDBOutput"

def clean_gdelt_csv(input_file, output_file):
    try:
        # Read the CSV file without headers since they're not labeled
        df = pd.read_csv(input_file, header=None,
                        delimiter='\t',  # Changed to tab delimiter
                        on_bad_lines='warn',
                        engine='python')
        
        # Define the new column headers
        new_headers = {
            0: 'GlobalEventID',
            1: 'Day',
            2: 'MonthYear',
            3: 'Year',
            4: 'FractionDate',
            5: 'Actor1Type2Code',
            6: 'Actor1Type1Code',
            16: 'Actor1Type3Code',
            17: 'Actor1CountryCode',
            25: 'IsRootEvent',
            26: 'EventCode',
            27: 'EventBaseCode',
            28: 'EventRootCode',
            29: 'QuadClass',
            30: 'GoldsteinScale',
            31: 'NumMentions',
            32: 'NumSources',
            33: 'NumArticles',
            34: 'AvgTone',
            35: 'Actor1Geo_Type',
            36: 'Actor1Geo_Fullname',
            37: 'Actor1Geo_CountryCode',
            38: 'Actor1Geo_ADM1Code',
            39: 'Actor1Geo_ADM2Code',
            40: 'Actor1Geo_Lat',
            41: 'Actor1Geo_Long',
            42: 'Actor1Geo_FeatureID'
        }
        
        # Keep only the columns we want (defined in new_headers)
        columns_to_keep = list(new_headers.keys())
        df = df[columns_to_keep]
        
        # Rename the columns
        df.columns = new_headers.values()
        
        # Save the cleaned data to a new CSV file
        df.to_csv(output_file, index=False)
        
        print(f"Processed file: {os.path.basename(input_file)}")
        print(f"Records processed: {len(df)}")
        return True
    
    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}")
        return False

def process_single_file():
    """Process the first CSV file found in the input directory"""
    for filename in os.listdir(INPUT_DIR):
        if filename.endswith('.CSV'):
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            input_path = os.path.join(INPUT_DIR, filename)
            output_filename = f"cleaned_{current_time}_{filename}"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            
            print(f"\nProcessing: {filename}")
            print(f"Started at: {current_time}")
            
            if clean_gdelt_csv(input_path, output_path):
                os.remove(input_path)
                print(f"Successfully processed and removed: {filename}")
                print(f"Cleaned file saved as: {output_filename}")
            else:
                print(f"Failed to process: {filename}")
            
            # Only process the first file found
            break

def monitor_directory():
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # First, process any file that's already there
    process_single_file()
    
    # Then start the monitoring loop
    while True:
        try:
            print("\nWaiting 15 minutes before next check...")
            time.sleep(900)  # 900 seconds = 15 minutes
            
            # Get current timestamp
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            # Check for CSV files in input directory
            for filename in os.listdir(INPUT_DIR):
                if filename.endswith('.csv'):
                    input_path = os.path.join(INPUT_DIR, filename)
                    output_filename = f"cleaned_{current_time}_{filename}"
                    output_path = os.path.join(OUTPUT_DIR, output_filename)
                    
                    print(f"\nProcessing: {filename}")
                    print(f"Started at: {current_time}")
                    
                    if clean_gdelt_csv(input_path, output_path):
                        os.remove(input_path)
                        print(f"Successfully processed and removed: {filename}")
                        print(f"Cleaned file saved as: {output_filename}")
                    else:
                        print(f"Failed to process: {filename}")
            
        except Exception as e:
            print(f"Error in monitor_directory: {str(e)}")
            print("Retrying in 15 minutes...")
            time.sleep(900)

if __name__ == "__main__":
    print("Starting directory monitor...")
    print(f"Watching directory: {INPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("Press Ctrl+C to stop the program")
    
    # Create directories if they don't exist
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        monitor_directory()
    except KeyboardInterrupt:
        print("\nProgram stopped by user")