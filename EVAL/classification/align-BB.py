import os
import csv
import glob
import argparse

# Set paths to the folders
OUT_aligned = "aligned/"
OUT_agregated = "aligned.csv"
header = ['ark-vue','det_id', 'gt_x', 'gt_y', 'gt_w', 'gt_h', 'det_x', 'det_y', 'det_w', 'det_h','gt_tech','gt_rot','gt_function','gt_genre','det_tech','det_rot','det_function','det_genre']
#
matches = 0
nbb_gt = 0
nbb_det = 0

parser = argparse.ArgumentParser(description="Align illustrations bounding boxes from ground truth data and dectections data.")
parser.add_argument('gt',  help='ground truth folder')
parser.add_argument('detection',  help='detection folder')
parser.add_argument('IoU',  help='IoU threshold')
args = parser.parse_args()
IOU_THRESHOLD = args.IoU # Threshold for considering a match
DETECTIONS_FOLDER = args.detection
GROUNDTRUTH_FOLDER = args.gt

try:
    IOU_THRESHOLD = float(IOU_THRESHOLD)
except:
    print("IoU parameter must be 0.0-1.0")
    quit()

# Detection format:
#    photographie 1.0 0.395065 0.188601 0.21510300000000002 0.234205 0 Carte_postale Représentations_humaines_/_Portraits bfkfk28zc4k
# GT Format:
#    photographie 0.39380000000000004 0.1894 0.214 0.23370000000000002 0 N/A N/A
def read_boxes(file_path, has_id):
    """
    Reads bounding boxes from a txt file.
    Format: x y w h  or: x y w h id if has_id=True
    Returns a list of tuples.
    """
    boxes = []
    extras = []

    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split(' ')
            box = []
            extra = []
            technic = parts[0]
            extra.append(technic)
            if has_id:
                box_id = parts[-1]
                box.append(box_id)
                for p in parts[2:6]:
                    box.append(float(p))
                boxes.append(box)
                for p in parts[-4:-1]:
                    extra.append(p)
                extras.append(extra)
            else:
                for p in parts[-3:]:
                    extra.append(p)
                extras.append(extra)
                boxes.append([float(p) for p in parts[1:5]])
    print(extras)
    return boxes, extras


def iou(boxA, boxB):
    """
    Compute Intersection over Union (IoU) between two boxes
    box format: x, y, w, h
    """
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    interArea = interW * interH

    boxAArea = boxA[2] * boxA[3]
    boxBArea = boxB[2] * boxB[3]

    unionArea = boxAArea + boxBArea - interArea
    if unionArea == 0:
        return 0
    return interArea / unionArea

def align_boxes(gt_boxes, det_boxes, gt_extras, det_extras):
    global IOU_THRESHOLD
    global matches

    """
    Align detection boxes to ground truth boxes using IoU.
    Returns list of tuples: (det_id, gt_x, gt_y, gt_w, gt_h, det_x, det_y, det_w, det_h)
    """
    aligned = []
    used_gt = set()

    for i, det in enumerate(det_boxes):
        det_id, dx, dy, dw, dh = det
        det_extra = det_extras[i]

        best_iou = 0
        best_gt = None
        for idx, gt in enumerate(gt_boxes):
            if idx in used_gt:
                continue
            iou_score = iou((dx, dy, dw, dh), gt)
            if iou_score > best_iou:
                best_iou = iou_score
                best_gt = (idx, gt)

        if best_iou >= IOU_THRESHOLD and best_gt is not None:
            used_gt.add(best_gt[0])
            gx, gy, gw, gh = best_gt[1]
            gt_extra = gt_extras[best_gt[0]]
            print("   found a match for: \033[92m",det_id,"\033[0m")
            matches += 1
            aligned.append((det_id, gx, gy, gw, gh, dx, dy, dw, dh)+tuple(gt_extra)+tuple(det_extra))
        else:
            # No match, keep detection but set GT to None
            print("   NO match for detection \033[91m",det_id,"\033[0m")
            aligned.append((det_id, None, None, None, None,dx, dy, dw, dh, None, None, None, None)+tuple(det_extra))

    # Optionally, you can add unmatched GT boxes as well
    for idx, gt in enumerate(gt_boxes):
        if idx not in used_gt:
            gx, gy, gw, gh = gt
            print("   Unmatched \033[91m GT! \033[0m")
            gt_extra = gt_extras[idx]
            print(gt_extra)
            aligned.append((None, gx, gy, gw, gh, None, None, None, None)+tuple(gt_extra)+(None, None, None, None))

    return aligned

def process_folders(gt_folder, det_folder, output_folder):
    global nbb_gt
    global nbb_det

    os.makedirs(output_folder, exist_ok=True)

    gt_files = sorted(glob.glob(os.path.join(gt_folder, '*.txt')))
    det_files = sorted(glob.glob(os.path.join(det_folder, '*.txt')))

    # Assume filenames match between folders
    for gt_file, det_file in zip(gt_files, det_files):
        image_name = os.path.splitext(os.path.basename(gt_file))[0]
        print("...processing \033[1m",image_name,"\033[0m")
        gt_boxes, gt_extras = read_boxes(gt_file, False)
        det_boxes, det_extras = read_boxes(det_file, True)

        nbb_gt += len(gt_boxes)
        nbb_det += len(det_boxes)
        aligned = align_boxes(gt_boxes, det_boxes, gt_extras, det_extras)

        output_csv = os.path.join(output_folder, f'{image_name}_aligned.csv')
        with open(output_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in aligned:
                writer.writerow(row)
        with open(OUT_agregated, 'a', newline='') as f:
            writer = csv.writer(f)
            for row in aligned:
                writer.writerow((image_name,) + row)

        print(f'...saving aligned CSV for {image_name}\n')

    return(gt_files)


###              MAIN            ###
with open(OUT_agregated, 'w') as f:
    writer = csv.writer(f)
    writer.writerow(header)


files = process_folders(GROUNDTRUTH_FOLDER, DETECTIONS_FOLDER, OUT_aligned)
print("\n---------------------------------")
print("Number of files in GT:", len(files))
print("Number of BBox in GT:", nbb_gt)
print("Number of detected BBox:", nbb_det)
print("Number of matches:\033[1m", matches)
print("---------------------------------")
print("\033[0mCSV data saved in folder:", OUT_aligned , " and:", OUT_agregated)
