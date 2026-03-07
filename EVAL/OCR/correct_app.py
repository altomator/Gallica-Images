# Correction app for OCR files
# OCR files must be JSON files with a `text`` element

import streamlit as st
import os
import json
from PIL import Image
import sys

# -----------------------------
# Argument Parsing
# -----------------------------
if len(sys.argv) < 3:
    st.error("Usage: streamlit run correct_app.py -- <image_folder> <ocr_folder>")
    st.stop()

default_image_folder = sys.argv[1]
default_ocr_folder = sys.argv[2]

st.set_page_config(layout="wide")

# Sidebar for folder configuration
img_dir = st.sidebar.text_input("Chemin vers le dossier images", default_image_folder)
json_dir = st.sidebar.text_input("Chemin vers l'OCR à corriger", default_ocr_folder)

if os.path.isdir(img_dir) and os.path.isdir(json_dir):
    img_files = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])

    if not img_files:
        st.error("Aucune image trouvée dans le dossier.")
    else:
        if 'index' not in st.session_state:
            st.session_state.index = 0

        col_nav1, col_nav2 = st.columns([1, 1])
        with col_nav1:
            if st.button("⬅️ Retour") and st.session_state.index > 0:
                st.session_state.index -= 1
        with col_nav2:
            if st.button("Suivant ➡️") and st.session_state.index < len(img_files) - 1:
                st.session_state.index += 1

        current_img_filename = img_files[st.session_state.index]
        base_filename = os.path.splitext(current_img_filename)[0]
        json_filename = f"{base_filename}.json"
        
        img_path = os.path.join(img_dir, current_img_filename)
        json_path = os.path.join(json_dir, json_filename)

        st.write(f"Image {st.session_state.index + 1} sur {len(img_files)} : **{current_img_filename}**")

        # Refactored: image column (left) is larger than text column (right)
        left_col, right_col = st.columns([1, 1])

        with left_col:
            st.subheader("Image")
            image = Image.open(img_path)
            st.image(image, use_column_width=True)

        with right_col:
            st.subheader("Texte (édition)")
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    text_content = data.get("text", "")
                    
                    # Editable text area
                    edited_text = st.text_area("Contenu OCR", value=text_content, height=300, key=f"editor_{current_img_filename}")
                    
                    if st.button("💾 Enregistrer les modifications"):
                        data["text"] = edited_text
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                        st.success("Fichier JSON mis à jour avec succès !")
                except Exception as e:
                    st.error(f"Erreur lors de la manipulation du fichier JSON: {e}")
            else:
                st.warning(f"Fichier JSON associé absent : {json_filename}")
else:
    st.info("Veuillez saisir des chemins d'accès valides dans la barre latérale pour commencer.")
