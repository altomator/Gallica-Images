# usage: streamlit run read_app.py
# this script allows to read the ocr output

import streamlit as st
import os
import json
from PIL import Image
import sys
from pathlib import Path

st.set_page_config(layout="wide")

# -----------------------------
# Argument Parsing
# -----------------------------
if len(sys.argv) < 3:
    st.error("Usage: streamlit run read_app.py -- <image_folder> <GT_folder> <ocr_folder>")
    st.stop()

default_image_folder = sys.argv[1]
default_GT_folder = sys.argv[2]
default_ocr_folder = sys.argv[3]

# Sidebar for folder configuration
img_dir = st.sidebar.text_input("Chemin vers le dossier images", default_image_folder)
json_dir = st.sidebar.text_input("Chemin vers le dossier vérité terrain (JSON)", default_GT_folder)
ocr_dir = st.sidebar.text_input("Chemin vers le dossier OCR ", default_ocr_folder)

# Get list of images
if os.path.exists(img_dir):
    images = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
else:
    images = []

if not images:
    st.error("Aucune image trouvée dans le dossier.")
    st.stop()

# Initialize session state for navigation
if 'index' not in st.session_state:
    st.session_state.index = 0

# Navigation buttons in sidebar
col_prev, col_next = st.columns(2)
if col_prev.button("⬅️ Retour") and st.session_state.index > 0:
    st.session_state.index -= 1
if col_next.button("Suivant ➡️") and st.session_state.index < len(images) - 1:
    st.session_state.index += 1

current_img_name = images[st.session_state.index]
st.write(f"Image : {current_img_name} ({st.session_state.index + 1}/{len(images)})")

# Load data files by format
def load_json_text(folder, filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('text', str(data))
    print(filename)
    return "Fichier absent : "+filename

def load_md_text(folder, filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = f.read()
            data = "\n".join(line for line in data.splitlines() if not line.startswith('!')) 
            return data
    print(filename)
    return "Fichier absent : "+filename

def load_txt_text(folder, filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = f.read()
            return data
    print(filename)
    return "Fichier absent : "+filename

# images files
img_path = os.path.join(img_dir, current_img_name)
# GT is always JSON
path = os.path.join(json_dir, os.path.splitext(current_img_name)[0])
gt_text = load_json_text(json_dir, path + ".json")
# OCR can be txt, json, md
my_dir = Path(ocr_dir)
file_name=os.path.splitext(current_img_name)[0]
print(my_dir)
files = list(my_dir.glob(f"{file_name}.*"))
if files:
    print("Found:", files[0])
    ocr_format = os.path.splitext(files[0])[1]
    print("OCR format detected: ", ocr_format)
    match ocr_format:
        case ".txt": ocr_text = load_txt_text(ocr_dir, files[0])
        case ".md": ocr_text = load_md_text(ocr_dir, files[0])
        case ".json": ocr_text = load_json_text(ocr_dir, files[0])
else:
    ocr_text = "Fichier OCR absent : "+ocr_dir+ "/"+file_name


# Display columns
col1, col2, col3 = st.columns(3)

with col1:
    st.header("Image")
    st.image(Image.open(img_path), use_column_width=True)

with col2:
    st.header("Vérité terrain")
    st.text_area("GT Content", gt_text, height=600, label_visibility="collapsed")

with col3:
    st.header("OCR")
    st.text_area("OCR Content", ocr_text, height=600, label_visibility="collapsed")
