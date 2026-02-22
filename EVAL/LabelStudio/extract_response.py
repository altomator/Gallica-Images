import json
import os
from collections import defaultdict
import argparse
from PIL import Image, ImageDraw



###        PARAMETERS          ###
# GT data file (from LabelStudio)
GT_file = 'GT.csv'
# input directory for the JSON data extracted from the database thanks to the API
IN_data = 'DATA_db'
# output directory for storing the extracted data from the database: classe confidence bbox
OUT_data = "DATA_detect"
# output directory for storing the extracted text from the database
OUT_ocr = "DATA_ocr"
# GT folder of full page images
GT_folder = 'GT_PAGES'
# output directory for the extracted illustrations from the database
OUT_ill = "ILL"
# URL of Gallica IIIF v3 endpoint
iiif_endpoint="https://openapi.bnf.fr/iiif/image/v3/ark:/12148/"

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Extract illustrations and data from the Gallica Images database.")
parser.add_argument("folder_path", type=str,  help="Path to the dataset folder")
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

# Initialize a dictionary to store the ARK illustrations for a ARK doc
aggregated_data = defaultdict(list)

missing_arks = 0
arks_with_no_ill = 0
missing_GT_pages = 0
extracted_iiif = 0
annotated_pages = 0

# Function to read a JSON file
def read_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"# Error: The file \033[91m{file_path}\033[0m was not found #")
    except json.JSONDecodeError:
        print(f"# Error: The file \033[91m{file_path}\033[0m is not a valid JSON file #")

# Function to read a csv file
def read_csv_file(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            data = [line.strip().split(';') for line in lines]
            return data
    except FileNotFoundError:
        print(f"# Error: The file \033[91m{file_path}\033[0m was not found #")
    except Exception as e:
        print(f"# Error: An error occurred while reading the CSV file:\033[91m {e}\033[0m #")

def get_element(json_data, elt):
    tmp=json_data.get(elt)
    return tmp[0] if tmp else "N/A"

def clean_json(folder):
    content=""

    if os.path.exists(folder):
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            with open(file_path, "r") as file:
                content = file.read()
                # remove last ,
            content = content[:-1]
            with open(file_path, "w") as file:
                file.write(content)
                file.write("\n]\n}")

def rm_dir(folder):
    if os.path.exists(folder):
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    os.rmdir(file_path)
            except Exception as e:
                print(f"Error: {e}")

# Call the Search API on a given document ark and get the list of arks illustration
# Output the data as a .txt file per page (format: ARK-page number.txt)
def call_doc_api(ark_doc):
    global extracted_iiif
    global annotated_pages
    global aggregated_data
    global missing_arks
    global missing_GT_pages
    global arks_with_no_ill

    # Placeholder for the API call
    # actually, we read the json data
    file_path = os.path.join(f"{IN_data}/{ark_doc}.json")
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"# Error: The DB file \033[91m{file_path} for ARK \033[91m{ark_doc}\033[0m was not found! #")
        missing_arks += 1
        return None
    # Read the JSON file
    json_data = read_json_file(file_path)
    if json_data:
        # Extract the response content
        response_content = json_data.get('response', None)
        if response_content:
            arks = 0
            # Get the response
            docs = response_content.get('docs', None)
            docs_len = len(docs)
            # Get the results list lenght
            item_count = response_content.get('numFound', None)
            print("   number of records in the response:", docs_len)
            print("   results list length:", item_count)
            if item_count != docs_len:
                print("\033[91m# Warning: results list does not match the number of records in the response! #\033[0m")
            if docs_len == 0:
                aggregated_data[ark_doc].append(())
                arks_with_no_ill += 1
                return None

            doc_index=1
            for doc in docs:
                print(doc)
                ark_value = doc.get('context_ark')
                title_value = doc.get('context_title')
                if not title_value: # empty record? weird!
                    continue
                else:
                    title_value = title_value[0]
                arks += 1
                # Extract the 'id' field for the illustration
                ill_ark = doc.get('ark')
                aggregated_data[ark_doc].append(ill_ark)
                # extract the url
                url = doc.get('link')
                #print(url)
                parts = url.split('/f')
                tmp = parts[1].split('pct:')
                vue = tmp[0][:-1]
                print("  processing vue #", vue)
                tmp=tmp[1].split('/max/')
                bbox=tmp[0]
                x, y, w, h = map(float, bbox.split(','))
                tmp=tmp[1].split('/def')
                rotation=tmp[0]

                class_name = get_element(doc,'properties_technical_category')
                print(" technic : ", class_name)
                function_name = get_element(doc,'properties_form_function').replace(" ", "_")
                print(" function :", function_name)
                genre_name = get_element(doc,'properties_genre').replace(" ", "_")
                print(" genre :", genre_name)

                # confidence score not available in the DB
                confidence = 1.0

                # Write the data to a txt file (Pascalvoc format + extra data)
                file_name = os.path.join(OUT_data, f"{ark_doc}-{vue}.txt")
                with open(file_name, 'a') as outfile:
                    outfile.write(f"{class_name} {confidence} {x/100} {y/100} {w/100} {h/100} {rotation} {function_name} {genre_name} {ill_ark} \n")

                # OCR
                content_text = get_element(doc,'content_text')
                print(" content_text : ", content_text)
                context_text_before = get_element(doc,'context_text_before')
                print(" context_text_before : ", context_text_before)
                context_text_after = get_element(doc,'context_text_after')
                print(" context_text_after : ", context_text_after)
                content_section = get_element(doc,'content_section')
                print(" content_section : ", content_section)
                data = {
                "ark": ill_ark,
                "bbox": bbox,
                "technic": class_name,
                "function": function_name,
                "genre": genre_name,
                "rotation": rotation,
                "content_section": content_section,
                "content_text": content_text,
                "context_text_before": context_text_before,
                "context_text_after": context_text_after
                }

                # Write the OCR to a txt file
                ocr_name = os.path.join(OUT_ocr, f"{ark_doc}-{vue}.json")
                if not os.path.exists(ocr_name):
                    print("  writing OCR in:", ocr_name)
                    with open(ocr_name, 'a') as outfile:
                        outfile.write("{\n\"doc_ark\": \""+ark_value+"\",\n\"page\": \""+vue+"\",\n\"title\": \""+title_value+"\",\n\"ills\":[\n")
                with open(ocr_name, 'a') as outfile:
                    json.dump(data, outfile, indent=4)
                    outfile.write(",")

                # Download the illustration images using wget
                if extract_img:
                    # Construct the IIIF URL
                    iiif_url = f"{iiif_endpoint}{ark_doc}/f{vue}/pct:{bbox}/pct:{iiif_output}/{rotation}/default.jpg"
                    #print(f"IIIF URL: {iiif_url}")
                    # Construct the output file name
                    output_file_name = f"{OUT_ill}/{ark_doc}-{vue}-{doc_index}.jpg"
                    print(f"Output file name: {output_file_name}")
                    if os.path.exists(output_file_name):
                        print(f"File already exists: {output_file_name}")
                        continue
                    exit_code = os.system(f"wget -q -O {output_file_name} {iiif_url}")
                    if exit_code != 0:
                        print(f"Error: Failed to download image \033[91m{output_file_name}\033[0m")
                    else:
                        doc_index += 1
                        extracted_iiif += 1

                # Annotate the GT image with the bbox and class name
                if os.path.exists(GT_folder):
                    gt_file_name = os.path.join(GT_folder, f"{ark_doc}-{vue}.jpg")
                    print(f"Annotating GT image: {gt_file_name}")
                    if os.path.exists(gt_file_name):
                        # Annotate the GT image with the bbox and class name
                        try:
                            with Image.open(gt_file_name) as img:
                                # Extract image dimensions
                                img_width, img_height = img.size
                        except:
                            print(f"## Error: Unable to open image file: \033[91m{gt_file_name}\033[0m ##")
                            missing_GT_pages += 1
                            continue
                        with Image.open(gt_file_name) as img:
                            draw = ImageDraw.Draw(img)
                            #print(x)
                            #print(w)
                            # Calculate the bounding box coordinates
                            # Convert percentage to pixel values
                            x = int(x * img_width / 100)
                            y = int(y * img_height / 100)
                            w = int(w * img_width / 100)
                            h = int(h * img_height / 100)
                            # Draw the bounding box
                            draw.rectangle([x, y, x + w, y + h], outline="red", width=2)
                            # Add rotation value near the top right corner of the bounding box
                            # Adjust position near the top right corner
                            draw.text((x+w-50, y+8), f"{rotation}", fill="red")
                            draw.text((x+w-50, y+18), class_name[:8], fill="red")
                            # Save the annotated image
                            img.save(gt_file_name)
                            annotated_pages += 1
                    else:
                        print(f"# GT image file not found: \033[91m{gt_file_name}\033[0m. Can't annotate! #")
                        missing_GT_pages += 1
                else:
                    # Print the number of results processed
                    print(f"# Folder of GT images not found : \033[91m{GT_folder}\033[0m. Can't annotate! #")

            print("   number of illustrations processed for this document:", arks)
            return(aggregated_data)
        else:
            print("# No 'response' key found in the JSON data for ARK {ark_doc}! #")
            missing_arks += 1
            aggregated_data[ark_doc].append()
            return None
    else:
        print("\033[91m# No JSON get for ARK {ark_doc}! #\033[0m")
        missing_arks += 1
        aggregated_data[ark_doc].append()
        return None




###### MAIN ######

# Change the working directory to the script's directory
script_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_directory+"/"+folder_path)
print("...changed working directory to script directory:", os.getcwd())

# Create the output directory for storing the illustration data (CSV format)
rm_dir(OUT_ocr)
rm_dir(OUT_data)
os.makedirs(OUT_ocr, exist_ok=True)
os.makedirs(OUT_data, exist_ok=True)
print("Output directory for illustration data:", OUT_data)
print("Output directory for OCR data:", OUT_ocr)
os.makedirs(OUT_ill, exist_ok=True)
print("Output directory for illustrations:", OUT_ill)

print("--------------------------------------------")
# read the ground truth CSV file
gt_data = read_csv_file(GT_file)
if gt_data:
    print("Ground truth data successfully read from CSV file.")
else:
    print("\033[91m# Failed to read ground truth data from CSV file #\033[0m")
    exit(0)

# Print the first 5 lines of the ground truth data
print("... reading the ground truth data from CSV file")
print("    First 3 lines of ground truth data:")
for line in gt_data[:5]:
    print(line)
# Print the number of lines in the ground truth data
print("Number of lines in ground truth data:", len(gt_data))

print("--------------------------------------------")
print("Now processing the ground truth data: looking for the corresponding ARK in the database")
for line in gt_data[1:]:  # Skip the first line
    #print(line)
    # Extract and print the ark values from the ground truth data
    ark_value = line[0]
    vue_value = line[2]
    print(f"\n...{ark_value}-{vue_value}")
    if ark_value in aggregated_data:
        # Do nothing as we already processed all the illustrations for this ARK doc
        print("  ARK already processed:", ark_value)
    else:
        # Calling the API to get the list of illustrations for the ark value
        print("   calling the API for ARK:", ark_value)
        call_doc_api(ark_value)

print("--------------------------------------------")
clean_json(OUT_ocr)

print("Number of IIIF illustration extracted:\033[1m", extracted_iiif,'\033[0m')
print("Number of documents in ground truth data:\033[1m", len(aggregated_data),'\033[0m')
print("Number of pages in ground truth data:\033[1m", len(gt_data),'\033[0m')

print("Number of documents not found in the database:\033[1m", missing_arks,'\033[0m')
print("Number of documents with no illustrations:\033[1m", arks_with_no_ill,'\033[0m')
#print("Number of GT images not found:", missing_GT_pages)
print("Number of illustrations annotated on the GT pages:\033[1m", annotated_pages,'\033[0m')

# count how many empty list we have in aggregated_data
empty_count = sum(1 for v in aggregated_data.values() if not v)
print("Number of ARK documents with no illustrations:\033[1m", empty_count,'\033[0m')

#print(aggregated_data)
