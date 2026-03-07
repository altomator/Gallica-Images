# Read a file with a list of pages:
# - export the IIIF images
# - extract text from the images with a Mistral AI model and save the results to a JSON file
# Models:
#  - OCR
#  - VLM

# A Mistral AI API key is required: set the MISTRAL_API_KEY environment variable
# export MISTRAL_API_KEY="____"

# python -m venv datasets
# source datasets/bin/activate
# pip install -r requirements.txt

# Note:
# - the images are extracted thanks to a IIIF API call
# - the image dimension is fixed to a constant value depending on the orientation of the image
# - the images are expected to be in the format <ark>_<page>.jpg
# - the ocr output will be in the format <ark>_<page>.json or .md

# USAGE: python extract_ocr FOLDER model_type (ocr, vmlm)
# FOLDER must contain a list of pages files:
'''
btv1b103365581-f1
btv1b103365581-f13
btv1b103365581-f17
btv1b103365581-f2
...
'''

import os
import csv
from PIL import Image
#pip install pillow
from mistralai import Mistral
import json
import sys
import requests
import argparse


# input
list_file = "liste_pages.txt"

#  output folders
iiif_output = "iiif_output"
ocr_output = "ocr_output"

# max size of the image
max_size = 2000
temperature = 0.1

# Mistral AI
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    print("\033[91m Please set the MISTRAL_API_KEY environment variable! \033[0m")
    sys.exit(1)

#model = "pixtral-12b-2409"
model = "pixtral-large-2411"
# prompt_vlm
prompt_vlm = "prompt_en_VLM.txt"

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Extract the text content from images.")
parser.add_argument("folder", help="Path to the folder to process")
parser.add_argument("format", help="Type of model: ocr, vlm", choices=['ocr', 'vlm'])

args = parser.parse_args()
list_folder = args.folder
md_format = args.format

#######
def gallica_iiif(ark, page):
    return "https://openapi.bnf.fr/iiif/image/v3/ark:/12148/" + ark + "/" + page

######
def get_iiif_info(ark, page):
    print("... calling IIIF info    ")
    iiif_url = gallica_iiif(ark, page) + "/info.json"
    #print(iiif_url)
    try:
        with requests.get(iiif_url) as response:
            data = response.json()
            return data.get('width', 0), data.get('height', 0)
    except Exception as e:
        print(f"Error fetching IIIF info: {e}")
        return 0, 0

#######
def get_iiif(url, output_file):
    print("... calling IIIF Image:  ", url)
    print("    writing in output_file: ", output_file)

    if os.path.exists(output_file):
        print("    image file already exists. No API call.")
        return output_file

    import requests
    try:
        with requests.get(url) as response:
            response.raise_for_status()
            with open(output_file, "wb") as f:
                f.write(response.content)
    except Exception as e:
        print(f"Error fetching IIIF: {e}")
        return None



##### we use MistralOCR
def extract_text_from_image_with_mistral_ocr(ark, page, width, height, output_file):
    import base64
    from mistralai import Mistral

    print("... calling MistralOCR")
    client = Mistral(api_key=api_key)

    max_dim = max_size
    if width < height: # portrait
        if max_size > height:
            max_dim = height
        gallica_url = gallica_iiif(ark, page) + "/full/,"+ str(max_dim) + "/0/default.jpg"
    else:
        if max_size > width:
            max_dim = width
        gallica_url = gallica_iiif(ark, page) + "/full/" + str(max_dim)+ ",/0/default.jpg"

    if not get_iiif(gallica_url, output_file):
        return None


    try:
        response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "image_url",
                "image_url": gallica_url,
            },
            include_image_base64=True
    )
        print("Pages processed:", len(response.pages))
        #print("Premier extrait markdown :\n")
        #print(response.pages[0].markdown[:500], "...")
        return response.pages[0].markdown

    except Exception as e:
        print(f"Error: {e}")
        return None


##### we use a basic prompt to extract the text from the image
def extract_text_from_image_with_pixtral(ark, page, width, height, output_file):
    import base64
    from mistralai import Mistral

    print("... calling Mistral: ", model)
    client = Mistral(api_key=api_key)

    max_dim = max_size
    if width < height: # portrait
        if max_size > height:
            max_dim = height
        gallica_url = gallica_iiif(ark, page) + "/full/,"+ str(max_dim) + "/0/default.jpg"
    else:
        if max_size > width:
            max_dim = width
        gallica_url = gallica_iiif(ark, page) + "/full/" + str(max_dim)+ ",/0/default.jpg"

    get_iiif(gallica_url, output_file)


    try:
        response = client.chat.complete(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system",
                 "content": "Return the answer in a JSON object with the next structure: "
                   "{\"text\": <text>}"},
            {
            "role": "user",
            "content": prompt_content
            },
            {
            "role": "user",
            "content": [
            {
                "type": "image_url",
                "image_url": gallica_url,
            }
            ],
            "response_format": {
                "type": "json_object",
            }
        }
    ])
        ocr_json = response.choices[0].message.content
        return "\n".join(ocr_json.splitlines()[1:-1])

    except Exception as e:
        print(f"Error: {e}")
        return None

######
def extract_ocr(prompt_content, pages, iiif_output, md_format):

    for i,p in enumerate(pages):
        print(f"\n----------------------\nProcessing page {i}: ",p)
        tmp = p.split('-')
        ark = tmp[0]
        page = tmp[1]

        output_file = os.path.join(iiif_output, f"{ark}-{page}.jpg")
        if md_format=="vlm":
            ocr_file = os.path.join(ocr_output, f"{ark}-{page}.json")
        else:
            ocr_file = os.path.join(ocr_output, f"{ark}-{page}.md")
        if os.path.exists(ocr_file):
            print(f"...OCR file already exists. Skipping ",ocr_file)
            continue

        # call IIIF info
        (width, height) = get_iiif_info(ark, page)
        if md_format=="vlm":
            result = extract_text_from_image_with_pixtral(ark, page, width, height, output_file)
        else:
            result = extract_text_from_image_with_mistral_ocr(ark, page, width, height, output_file)
        if result:
            print(result)
        else:
            print("# No text found! #")

        with open(ocr_file, "w", encoding="utf-8") as f:
            f.write(result + "\n")


#################################
if __name__ == "__main__":
        # Change the working directory 
        script_directory = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_directory+"/"+list_folder)
        print("Changed working directory to script directory:", os.getcwd())

        # Check if file exists
        if not os.path.exists(list_file):
            print(f"# Error: The file '{list_file}' was not found! #")
            sys.exit(1)
        with open(list_file, 'r', encoding='utf-8') as f:
            pages = f.read().splitlines()
        print(f"\033[91m...{len(pages)} pages to process from {list_file}\033[m")

        # create output dir
        if not os.path.exists(iiif_output):
            print(f"...creating output folder in {iiif_output}")
            os.makedirs(iiif_output)
        if not os.path.exists(ocr_output):
            print(f"...creating OCR folder in {ocr_output}")
            os.makedirs(ocr_output)

        # Read prompt file
        if not os.path.exists(prompt_vlm):
            print(f"# Error: The file '{prompt_vlm}' was not found! #")
            sys.exit(1)
        with open(prompt_vlm, 'r', encoding='utf-8') as prompt_file:
            prompt_content = prompt_file.read()
            #print(f"...prompt is loaded:", prompt_content)

        print(f"...calling model \033[1m{md_format}\033[0m")
        print(f"   temperature=\033[1m{temperature}\033[0m - max size=\033[1m{max_size}\033[0m")
        print(f"   prompt=\033[1m{prompt_content}\033[0m")

        extract_ocr(prompt_content, pages, iiif_output, md_format)
        print("\n---------------------\nImages files are stored in:",  iiif_output)
        print("OCR files are stored in:",  ocr_output)
