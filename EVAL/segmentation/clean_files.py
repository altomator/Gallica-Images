import os
import argparse


# Define folder paths

parser = argparse.ArgumentParser(description="Align data files for ground truth data and dectections data.")
parser.add_argument('gt',  help='ground truth folder')
parser.add_argument('detection',  help='detection folder')
args = parser.parse_args()
detections_folder = args.detection
groundtruth_folder = args.gt


# Function to read files from a folder
def read_files_from_folder(folder_path):
    files_content = {}
    if os.path.exists(folder_path):
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                    files_content[file_name] = file.read()
    else:
        print(f"Folder '{folder_path}' does not exist.")
    return files_content

# Read files from both folders
detections_files = read_files_from_folder(detections_folder)
groundtruths_files = read_files_from_folder(groundtruth_folder)

# Remove files in detections_folder that do not exist in groundtruths_folder
for detection_file in list(detections_files.keys()):
    if detection_file not in groundtruths_files:
        file_path = os.path.join(detections_folder, detection_file)
        try:
            os.remove(file_path)
            print(f"Deleted file: \033[92m{file_path}\033[0m")
        except OSError as e:
            print(f"Error deleting file \033[91m{file_path}\033[0m: {e}")

# Create empty files in detections_folder for files that exist in groundtruths_folder
# but not in detections_folder
for groundtruth_file in groundtruths_files.keys():
    if groundtruth_file not in detections_files:
        file_path = os.path.join(detections_folder, groundtruth_file)
        try:
            with open(file_path, 'w') as file:
                pass  # Create an empty file
                print(f"Created empty file: \033[92m{file_path}\033[0m")
        except OSError as e:
                print(f"Error creating file \033[91m{file_path}\033[0m: {e}")
