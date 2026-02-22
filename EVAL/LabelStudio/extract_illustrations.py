# Extracting illustrations and data from a LabelStudio dataset

# INPUTS:
# - folder path to the dataset
# - list of ARK IDs + vue number needeed (use to filter the dataset)
# - annotated classes to process
# - size factor for the IIIF images downloaded

#OUTPUTS:
# - full pages images -> $OUT_pages
# - illustrations images -> $OUT_ill
# - annotations data: ark, title, vue, class, bounding boxes, rotation -> $csv_file_path
# - annotations data in Pascalvoc format for every  image, in a file nammed ark-vue.txt

# USAGE:
# >python3 extract_illustrations.py


import os
from collections import defaultdict
import json
import csv
from PIL import Image, ImageDraw
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Extract illustrations and data from a LabelStudio dataset.")
parser.add_argument("folder_path", type=str,  help="Path to the dataset folder to be processed")
parser.add_argument('--iiif', action='store_true', help='Extract images with IIIF')
parser.add_argument('--annot', action='store_true', help='Annotate images')
parser.add_argument(
    '-f',
    '--factor',
    type=int,
    default=30,
    help='Size factor for the IIIF images (%)')
args = parser.parse_args()

folder_path = args.folder_path
extract_img = args.iiif
annot_img = args.annot
iiif_output = args.factor

###         PARAMETER           ###
#  Data file for the demand:
#  list of ARK IDs + vue number
file_path = 'liste_pages.txt'
#  Label Studio dataset file
json_file_path = 'dataset_LS.json'

#  Annotation type to filter
annotation_type = 'BUG,blanche,photographie,photomeca,dessin,dessinmeca,gravure,schema,plan,carte,carteajouer,estampe,peinture,décoration,bd'



######################################

# output directory for extracted images
OUT_pages = "GT_PAGES"
OUT_ill = "GT_ILLUSTRATIONS"

# output directory for GT data: one txt file per vue, Pascalvoc format
OUT_data = "DATA_gt"

# Define the CSV file path for outputing the GT data
csv_file_path = 'GT.csv'

# URL of Gallica IIIF v3 endpoint
iiif_endpoint="https://openapi.bnf.fr/iiif/image/v3/ark:/12148/"

####################################
# Read a text file and store its content in an array
def read_file_to_array(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        # Remove newline characters from each line
        return [line.strip() for line in lines]
    except FileNotFoundError:
        print(f"Error: The file \033[91m'{file_path}'\033[0m was not found.")
        return []

### MAIN ###
# Change the working directory to the script's directory
script_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_directory+"/"+folder_path)
print("Changed working directory to script directory:", os.getcwd())

# Create the output directory for storing the illustration data (CSV format)
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
os.makedirs(OUT_data, exist_ok=True)
print("Output directory for illustration data:\033[1m", OUT_data,'\033[0m')


# Open the CSV file in creation mode
with open(csv_file_path, mode='w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['ARK','Title','Vue Number','BBOX (%)','Rotation','Technique'])

# Create the output directory if it doesn't exist
os.makedirs(OUT_pages, exist_ok=True)
print("Output directory for full pages created:\033[1m", OUT_pages,'\033[0m')
os.makedirs(OUT_ill, exist_ok=True)
print("Output directory for illustrations created:\033[1m", OUT_ill,'\033[0m')

if extract_img:
    print("\033[92m# Warning: Image extraction is enabled #\033[0m")
else:
    print("\033[92m# Warning: Image extraction is disabled #\033[0m")
if annot_img:
    print("\033[92m# Warning: Image annotation is enabled #\033[0m")
else:
    print("\033[92m# Warning: Image annotation is disabled #\033[0m")



# Aggregate vue numbers by ARK identifiers (from the data file)
print("--------------------------------------------")
print("... reading the data file for the demand:", file_path)
aggregated_data = defaultdict(list)
file_path = './' + file_path
# Check if the file exists
if not os.path.exists(file_path):
    print(f"Error: The file \033[91m'{file_path}'\033[0m does not exist.")
    exit()
content_array = read_file_to_array(file_path)
for line in content_array:
    parts = line.split('-f')
    if len(parts) > 1:
        identifier = parts[0]
        #print("Identifier:", identifier)
        number = parts[1].replace('-f', '')
        aggregated_data[identifier].append(number)

print(f"Number of pages in the demand file: {len(content_array)}")
print("--------------------------------------------")
if extract_img:
    print("... now extracting the full pages with IIIF (if they don't exist) ...")
    vues = 0
    for identifier, numbers in aggregated_data.items():
        print(f"{identifier}: {numbers}")
        for number in numbers:
            # Construct the URL for the image
            image_url = f"{iiif_endpoint}{identifier}/f{number}/full/pct:{iiif_output}/0/default.jpg"
            print(f"Image URL: {image_url}")
            # Construct the output file name
            output_file_name = f"{OUT_pages}/{identifier}-{number}.jpg"
            # Download the image using wget
            if os.path.exists(output_file_name):
                print(f"File already exists: {output_file_name}")
                continue
            exit_code = os.system(f"wget -q -O {output_file_name} {image_url}")
            if exit_code != 0:
                print(f"Error: Failed to download image from \033[91m{image_url}\033[0m")
            else:
                print('.', end='')
                vues += 1
        # Print the number of images downloaded
        print(f"\nNumber of full pages downloaded: {vues}")
        print("--------------------------------------------")

print("... now reading the documents records from the Label Studio dataset file ...")
# Read the JSON data from the dataset file
json_file_path = './' + json_file_path
try:
    with open(json_file_path, 'r') as json_file:
        json_data = json_file.read()
    print("JSON data read successfully.")
except FileNotFoundError:
    print(f"Error: The file \033[91m'{json_file_path}'\033[0m was not found.")
    exit()

# Parse the JSON data and extract the documents info
arks = 0
unique_documents = {}
try:
    parsed_json = json.loads(json_data)
    print("... JSON data parsed successfully ...")
    documents = parsed_json.get("documents", [])
    for document in documents:
        ark = document.get("ark", "N/A")
        title = document.get("metadata", {}).get("title", ["N/A"])[0]
        # Store ARK and title in a dictionary, removing duplicates
        if ark not in unique_documents:
            unique_documents[ark] = title
            print(f"ARK: {ark}, Title: {title}")
            arks += 1
except json.JSONDecodeError:
    print("\033[91mError: Failed to parse JSON data.\033[0m")
    exit()
# Print the number of unique ARKs processed
print(f"\nNumber of unique ARKs found in the dataset: {arks}")
print("--------------------------------------------")

print("\n... now reading the annotations from the Label Studio dataset file ...")
print(f"    while filtering the annotation type: \033[1m{annotation_type}\033[0m ...")

# Parse the JSON data and extract the annotations info
annotations_number = 0
annotations_data = {}
annotations = parsed_json.get("annotations", [])
for annotation in annotations:
    results = []
    id = annotation.get("id", "N/A")
    # one annotation ID can have multiple bounding boxes
    targets = annotation.get("result", "N/A")
    for target in targets:
        try:
            if target.get("label", "N/A")[0] in annotation_type:
                annotations_number +=1
                results.append(target)
            else:
                print(f"Skipping annotation ID {id} with label {target.get('label', 'N/A')[0]}")
                continue
        except Exception as e :
            print(f"## Error processing annotation ID \033[91m{id}: {target}\033[0m ##")
            print(e)
            continue

    annotations_data[id] = results
    #print(f"Annotation ID: {id}, BBox: {len(results)}")

print(f"\nNumber of '{annotation_type}' annotations found in the dataset: {annotations_number}")
print("--------------------------------------------")


# Parse the JSON data and extract the annotations info
# only for the ARK-vue that are in the demand
print("... now parsing the annotated pages from the Label Studio dataset ...")
# Looking for the ark-vue couples in the "images" section of the JSON data
annotated_images = 0
bbox_nrot= 0
bbox_n = 0
images = parsed_json.get("images", [])
for image in images:
    ark = image.get("ark", "N/A")
    url = image.get("iiif", "N/A")
    id = image.get("id", "N/A")
    vue = url.split('/f')[1].split('/')[0]
    width = image.get("width", "N/A")
    height = image.get("height", "N/A")
    if ark in aggregated_data and str(vue) in aggregated_data[ark]:
        print(f"Found annotations related to the demand: {ark}/f{vue}: {id}")
        if id in annotations_data:
            #print(f" annotation ID found: {id}")
            annotated_images += 1
            # build the list of bounding boxes
            bbox_data = ""
            pascalvoc = ""

            # looping on the annotations list
            bbox_index=1
            for bb in annotations_data[id]:
                # values are expressed as % in the annotated data
                x = bb["bbox"]["x"]
                y = bb["bbox"]["y"]
                w = bb["bbox"]["width"]
                h = bb["bbox"]["height"]
                label = bb["label"][0]
                #print(label)
                if label == "blanche":
                    #we don't want to export the "blank page" class
                    bbox_data += ""
                else:
                    voc_data = str(x/100) + " " + str(y/100) + " " + str(w/100) + " " + str(h/100)
                    bbox_coord = str(x) + "," + str(y) + "," + str(w) + "," + str(h)
                    bbox_data += bbox_coord
                    bbox_n += 1
                    bbox_index += 1

                # we can have a meta data for the rotation / and a rotation value
                rot="0" # default
                try:
                    bbox_rot = bb["bbox"]["rotation"]
                    if bbox_rot != 0:
                        print(f"\n\033[91m{ark}-{vue}\033[0m: ### Unespected rotation on bbox: {bbox_rot} ###")
                except:
                     bbox_rot = "N/A"

                try:
                    meta = str(bb["meta"]["text"][0])
                    if meta=="rotation90" or meta=="rotation":
                        print(f"\n{ark}-{vue} has a rotation of: 90")
                        rot="90"
                        bbox_nrot+=1
                    elif meta=="rotation180":
                        print(f"\n{ark}-{vue} has a rotation of: 180")
                        rot="180"
                        bbox_nrot+=1
                    else:
                        print(f"\n{ark}-{vue}")
                        print(f" ### metadata: {meta} ###")
                except:
                    meta = "N/A"

                if bbox_data:
                    bbox_data += "," + rot + "," + label + ","
                    # we don't have Function and Genre data: N/A
                    pascalvoc += label + " " + voc_data + " " + rot + " N/A N/A" + "\n"

                if extract_img and bbox_data:
                    # Exporting a IIIF thumbnail for the bounding box
                    image_url = f"{iiif_endpoint}{ark}/f{vue}/pct:{x},{y},{w},{h}/pct:{iiif_output}/0/default.jpg"
                    #print(f"Image URL: {image_url}")
                    output_file_name = f"{OUT_ill}/{ark}-{vue}_{bbox_index}.jpg"
                    # Check if a subfolder named after the label exists in OUT_ill
                    label_folder = os.path.join(OUT_ill, label)
                    os.makedirs(label_folder, exist_ok=True)
                    # Update the output file name to include the label folder
                    output_file_name = os.path.join(label_folder, f"{ark}-{vue}_{bbox_index}.jpg")
                    os.system(f"wget -q -O {output_file_name} {image_url}")
                    print('.', end='')

                # Annotating the full page with bounding box and label
                image_path = f"{OUT_pages}/{ark}-{vue}.jpg"
                if annot_img:
                    if os.path.exists(image_path):
                        # open the image to extract the dimensions
                        try:
                            with Image.open(image_path) as img:
                                # Extract image dimensions
                                img_width, img_height = img.size
                        except Exception as e:
                            print(f"## Error: Unable to open image file: \033[91m{image_path}\033[0m ##")
                            print(e)
                            continue
                        with Image.open(image_path) as img:
                            draw = ImageDraw.Draw(img)
                            # Calculate the bounding box coordinates
                            # Convert percentage to pixel values
                            x_p = int(x * img_width / 100)
                            y_p = int(y * img_height / 100)
                            w_p = int(w * img_width / 100)
                            h_p = int(h * img_height / 100)
                            # Draw the bounding box
                            draw.rectangle([x_p, y_p, x_p + w_p, y_p + h_p], outline="greenyellow", width=2)
                            # Add rotation value near the top right corner of the bounding box
                            # Adjust position near the top right corner
                            draw.text((x_p+w_p-50, y_p+8), f"{rot}", fill="greenyellow")
                            draw.text((x_p+w_p-50, y_p+18), label[:8], fill="greenyellow")
                            # Save the annotated image
                            annotated_image_path = f"{OUT_pages}/{ark}-{vue}.jpg"
                            img.save(annotated_image_path)
                    else:
                        print(f"Full page not found, can't draw bounding box: \033[91m{image_path}\033[0m")

            # Write the ARK, title, vue number, bbox to the CSV file
            # Ensure the CSV file is open in append mode before writing
            if csv_file.closed:
                with open(csv_file_path, mode='a', newline='') as csv_file:
                    csv_writer = csv.writer(csv_file, delimiter=';')
                    csv_writer.writerow([ark, unique_documents[ark], vue, bbox_data])
            else:
                csv_writer.writerow([ark, unique_documents[ark], vue, bbox_data])

            # Write the data to a txt file (Pascalvoc format + extra data)
            file_name = os.path.join(OUT_data, f"{ark}-{vue}.txt")
            with open(file_name, 'a') as outfile:
                if label != "blanche":
                    print("...writing Pascalvoc format:",file_name, pascalvoc)
                    outfile.write(pascalvoc)
                else:
                    outfile.write("")

    else:
        #print(f"No annotations found in: {ark}/f{vue}: {id}")
        print('-', end='')

print("--------------------------------------------")
print(f"\nNumber of annotated pages related to the demand ({file_path}):\033[1m {annotated_images}\033[0m")
print(f"Number of illustrations generated:\033[1m {bbox_n}\033[0m")
print(f"Number of rotation found:\033[1m {bbox_nrot}\033[0m")
print("--------------------------------------------")

exit()
