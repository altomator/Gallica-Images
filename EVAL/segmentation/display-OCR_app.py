# streamlit run display-OCR.py -- data.csv /path/to/DATA_ocr


import streamlit as st
import pandas as pd
import cv2
import numpy as np
import os
import sys
import json
from pathlib import Path

def is_full_row(row, prefix):
    cols = [f"{prefix}_x", f"{prefix}_y", f"{prefix}_w", f"{prefix}_h"]
    return row[cols].notna().all()


# -----------------------------
# Argument Parsing
# -----------------------------
if len(sys.argv) < 4:
    st.error("Usage: streamlit run display-OCR.py -- <csv_file> <image_folder> <ocr_folder>")
    st.stop()

csv_file = sys.argv[1]
default_image_folder = sys.argv[2]
default_ocr_folder = sys.argv[3]

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(layout="wide")
#st.title("OCR Evaluation Tool")

# -----------------------------
# Sidebar Configuration
# -----------------------------
st.sidebar.header("Configuration")

gt_pages_path = st.sidebar.text_input("Chemin vers le dossier images", default_image_folder)
ocr_folder = st.sidebar.text_input("Chemin vers le dossier OCR", default_ocr_folder)

# -----------------------------
# Load Data
# -----------------------------
@st.cache_data
def load_data(path):
    return pd.read_csv(path)

df = load_data(csv_file)

if "ark-vue" not in df.columns:
    st.error("CSV must contain 'ark-vue' column.")
    st.stop()

unique_images = df["ark-vue"].unique()

# -----------------------------
# Session State
# -----------------------------
if "img_index" not in st.session_state:
    st.session_state.img_index = 0

# -----------------------------
# Navigation
# -----------------------------
nav_col1, nav_col2, _ = st.columns([1, 1, 8])

with nav_col1:
    if st.button("⬅ Retour"):
        st.session_state.img_index = max(0, st.session_state.img_index - 1)

with nav_col2:
    if st.button("Suiv. ➡"):
        st.session_state.img_index = min(len(unique_images) - 1,
                                         st.session_state.img_index + 1)

current_image_name = unique_images[st.session_state.img_index]
st.markdown(f"**Image {st.session_state.img_index + 1} / {len(unique_images)}**")


# -----------------------------
# Layout
# -----------------------------
left_col, right_col = st.columns([3, 3])

# -----------------------------
# Image Display + Drawing
# -----------------------------
with left_col:

    image_path = os.path.join(gt_pages_path, current_image_name+".jpg")

    if not os.path.exists(image_path):
        st.error(f"Image not found: {image_path}")
        st.stop()

    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    H, W = image.shape[:2]

    overlay = image.copy()

    image_rows = df[df["ark-vue"] == current_image_name]

    # --- Draw Ground Truth boxes ---
    for _, row in image_rows.iterrows():
        gt_full = is_full_row(row, "gt")
        det_full = is_full_row(row, "det")

        if gt_full:
            x, y, w, h = int(row["gt_x"]*W), int(row["gt_y"]*H), int(row["gt_w"]*W), int(row["gt_h"]*H)

            if not np.isnan(x):
                cv2.rectangle(
                    overlay,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    overlay,
                    str(row["gt_tech"]),
                    (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.2,
                    (0, 255, 0),
                    1
                )

        # --- Draw Detection boxes ---
        if det_full:
            x, y, w, h = int(row["det_x"]*W), int(row["det_y"]*H), int(row["det_w"]*W), int(row["det_h"]*H)

            if not np.isnan(x):
                cv2.rectangle(
                    overlay,
                    (x, y),
                    (x + w, y + h),
                    (255, 0, 0),
                    2
                )

                # Class name
                cv2.putText(
                    overlay,
                    str(row["det_tech"]),
                    (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.25,
                    (255, 0, 0),
                    1
                )

                # det_id in middle-top
                mid_x = x + w // 2 - 40
                cv2.putText(
                    overlay,
                    str(row["det_id"]),
                    (mid_x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (255, 0, 0),
                    1
                )

    # --- Apply transparency (alpha = 0.2) ---
    alpha = 0.75
    image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)

    st.image(image, caption=current_image_name, use_column_width=True)

# -----------------------------
# OCR Panel
# -----------------------------
with right_col:

    st.header("OCR de l'illustration")

    image_rows = df[df["ark-vue"] == current_image_name]

    det_ids = image_rows["det_id"].dropna().unique()

    if len(det_ids) == 0:
        st.info("Aucune illustration détectée.")
    else:
        selected_det_id = st.selectbox("Sélectionner l'illustration", det_ids)

        json_filename = Path(current_image_name).stem + ".json"
        json_path = os.path.join(ocr_folder, json_filename)

        if not os.path.exists(json_path):
            st.error(f"OCR JSON not found: {json_path}")
        else:
            with open(json_path, "r", encoding="utf-8") as f:
                ocr_data = json.load(f)
            # Retrieve OCR content via "ark" key matching det_id
            selected_content = None
            ills = ocr_data.get("ills", [])
            for item in ills:
                if str(item.get("ark")) == str(selected_det_id):
                    selected_content = item
                    print("MATCH!")
                    break

            if selected_content is None:
                st.warning("Pas d'OCR pour cette illustration.")
            else:
                st.markdown("**Content Section :**")
                st.write(selected_content.get("content_section", ""))
                st.markdown("**Content Text :**")
                st.write(selected_content.get("content_text", ""))
                st.markdown("**Context Before :**")
                st.write(selected_content.get("context_text_before", ""))
                st.markdown("**Context After**")
                st.write(selected_content.get("context_text_after", ""))