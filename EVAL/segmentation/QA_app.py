import streamlit as st
import pandas as pd
import numpy as np
import cv2
import os
import argparse
from PIL import Image

# =========================
# Argument parsing
# =========================
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_file", type=str, required=True)
    args, _ = parser.parse_known_args()
    return args

ARGS = parse_args()

# =========================
# Page config
# =========================
st.set_page_config(layout="wide")
#st.title("Image Classification QA Viewer")

# =========================
# Load dataframe
# =========================
@st.cache_data
def load_data(path):
    return pd.read_csv(path, encoding='utf-8')

df = load_data(ARGS.data_file)

# =========================
# Sidebar
# =========================
st.sidebar.header("Paramètres")

gt_pages_path = st.sidebar.text_input(
    "Chemin vers le dossier des images",
    value="GT_PAGES"
)

mode = st.sidebar.radio(
    "Modalité",
    [
        "Illustations alignées",
        "VT non alignées",
        "Détections non alignées",
    ]
)

# =========================
# Helper functions
# =========================
def is_empty_row(row, prefix):
    cols = [f"{prefix}_x", f"{prefix}_y", f"{prefix}_w", f"{prefix}_h"]
    return row[cols].isna().all()

def is_full_row(row, prefix):
    cols = [f"{prefix}_x", f"{prefix}_y", f"{prefix}_w", f"{prefix}_h"]
    return row[cols].notna().all()

def filter_images(df, mode):
    grouped = df.groupby("ark-vue")
    keep = []

    for ark, g in grouped:
        if mode == "Illustations alignées":
            cond = g.apply(
                lambda r: is_full_row(r, "gt") and is_full_row(r, "det"),
                axis=1
            ).all()

        elif mode == "VT non alignées":
            cond = g.apply(
                lambda r: is_empty_row(r, "det") and is_full_row(r, "gt"),
                axis=1
            ).any()

        elif mode == "Détections non alignées":
            cond = g.apply(
                lambda r: is_empty_row(r, "gt") and is_full_row(r, "det"),
                axis=1
            ).any()
        else:
            cond = True

        if cond:
            keep.append(ark)

    return sorted(keep)

def draw_transparent_rect(img, pt1, pt2, color, alpha=0.6, thickness=2):
    overlay = img.copy()
    cv2.rectangle(overlay, pt1, pt2, color, thickness)
    return cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

def draw_center_question(img, center, color):
    cv2.putText(
        img,
        "?",
        (int(center[0] - 10), int(center[1] + 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        color,
        3,
        cv2.LINE_AA,
    )

def draw_dotted_line(img, p1, p2, color=(0, 255, 0), thickness=3):
    dist = int(np.hypot(p2[0] - p1[0], p2[1] - p1[1]))
    for i in range(0, dist, 10):
        r = i / dist
        x = int(p1[0] * (1 - r) + p2[0] * r)
        y = int(p1[1] * (1 - r) + p2[1] * r)
        cv2.circle(img, (x, y), thickness, color, -1)

# =========================
# Prepare image list
# =========================
image_list = filter_images(df, mode)

if "index" not in st.session_state:
    st.session_state.index = 0

# Navigation
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("⬅ Retour"):
        st.session_state.index = max(0, st.session_state.index - 1)

with col2:
    if st.button("Suivant ➡"):
        st.session_state.index = min(len(image_list) - 1, st.session_state.index + 1)

if not image_list:
    st.warning("Aucune image ne correspond à la modalité sélectionnée.")
    st.stop()

current_ark = image_list[st.session_state.index]

st.markdown(f"**Image {st.session_state.index + 1} / {len(image_list)}**")
st.markdown(f"**ARK:** {current_ark}")

# =========================
# Load image
# =========================
img_path = os.path.join(gt_pages_path, current_ark+'.jpg')

if not os.path.exists(img_path):
    st.error(f"Image not found: {img_path}")
    st.stop()

img = cv2.imread(img_path)
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
H, W = img.shape[:2]

rows = df[df["ark-vue"] == current_ark]
print("\n",current_ark)

# =========================
# Draw boxes
# =========================
for _, r in rows.iterrows():

    gt_full = is_full_row(r, "gt")
    det_full = is_full_row(r, "det")

    gt_center = None
    det_center = None

    # ----- GT box -----
    if gt_full:
        x, y, w, h = int(r.gt_x * W), int(r.gt_y * H), int(r.gt_w * W), int(r.gt_h * H)
        img = draw_transparent_rect(img, (x, y), (x + w, y + h), (0, 255, 0))
        cv2.putText(img, str(r.gt_tech), (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        gt_center = (x + w // 2, y + h // 2)

    # ----- DET box -----
    if det_full:
        x, y, w, h = int(r.det_x * W), int(r.det_y * H), int(r.det_w * W), int(r.det_h * H)
        img = draw_transparent_rect(img, (x, y), (x + w, y + h), (255, 0, 0))
        cv2.putText(img, str(r.det_tech), (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        # ARK id upper-right
        cv2.putText(
            img,
            str(r.det_id),
            (x + w//2 -50, y + 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 0, 0),
            1,
        )
        det_center = (x + w // 2, y + h // 2)

    # ----- alignment visuals -----
    if mode == "Illustations alignées" and gt_full and det_full:
        draw_dotted_line(img, gt_center, det_center)

    if mode == "VT non alignées" and gt_full and not det_full:
        draw_center_question(img, gt_center,(0, 255, 0))

    if mode == "VT non alignées" and gt_full and det_full:
        draw_dotted_line(img, gt_center, det_center)

    if mode == "Détections non alignées" and det_full and not gt_full:
        draw_center_question(img, det_center, (255, 0, 0))

    if mode == "Détections non alignées" and det_full and  gt_full:
        draw_dotted_line(img, gt_center, det_center)

# =========================
# Display
# =========================
st.image(Image.fromarray(img), use_column_width=True)