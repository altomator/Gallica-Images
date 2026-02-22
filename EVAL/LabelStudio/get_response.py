import os
import json
from collections import defaultdict
import argparse



###        PARAMETERS          ###
# output directory for the extracted data from the database
OUT_data = "DATA_db"

# URL of Gallica Image search endpoint
gi_endpoint=" https://gallica-search-api-dev.bnf.lajavaness.com/"

doc_json=0


# Function to read a txt file
def read_txt_file(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()           
            return lines
    except FileNotFoundError:
        print(f"# Error: The file {file_path} was not found #")
        quit(0)
    except Exception as e:
        print(f"# Error: An error occurred while reading the file: {e} #")
        quit(0)


### Main script execution ###

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Extract  .")
parser.add_argument("data_path", type=str,   help="Path to the dataset folder (default: current directory)")
args = parser.parse_args()
# Update the folder_path variable with the argument value
data_path = args.data_path

# Create the output directory 
if os.path.exists(OUT_data):
    for file in os.listdir(OUT_data):
        file_path = os.path.join(OUT_data, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
        except Exception as e:
            print(f"Error: {e}")
            quit(0)
os.makedirs(OUT_data, exist_ok=True)
print("Output directory for illustration data:", OUT_data)

print("--------------------------------------------")
# read the list of images to process  
gt_data = read_txt_file(data_path)
if gt_data:
    print("Data successfully read from txt file.")
else:
    print("# Failed to read data from txt file #")
    quit(0)


# Loop through the images and process them
for line in gt_data:
    # Extract the ark value from the line
    try:
        ark_value = line.strip().split('-')[0]
        #print(f"Extracted ARK value: {ark_value}")
    except IndexError:
        print("# Error: Failed to extract ARK value from the line #")
    # Check if a file named after the ARK value exists in the OUT_data folder
    ark_file_path = os.path.join(OUT_data, f"{ark_value}.json")
    if not os.path.exists(ark_file_path):
        print(f" ...calling the API for {ark_value}")
        # Construct the API call  
        url = f"{gi_endpoint}{ark_value}"
        print(f"    {url}")
        # Construct the output file name
        output_file_name = f"{OUT_data}/{ark_value}.json"
        print(f"Output file name: {output_file_name}")
        if os.path.exists(output_file_name):
            print(f"   file already exists: {output_file_name}")
            continue
        exit_code = os.system(f"wget -q -O {output_file_name} {url}")
        if exit_code != 0:
            print(f"Error: Failed to download JSON in {output_file_name}")
        else:
            doc_json += 1

    