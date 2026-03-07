# usage: python compare_ocr.py <gt_dir> <ocr_dir> <output_file> <format>
# This script compares the text content of two folders of files
# using a Bag of Words approach
# OCR formats : json, md, txt
# GT format : json

import os
import json
import csv
import math
from collections import Counter
import pprint
import argparse
import unicodedata
import re

output_csv = "BoW_results.csv"

nf = 0

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Compares the text content of two folders of OCR files.")
parser.add_argument("gt_dir", help="Path to the ground truth folder")
parser.add_argument("ocr_dir", help="Path to the ocr folder")
parser.add_argument("format", default="json", help="OCR format (json, md, txt)")
parser.add_argument('--relaxed', action='store_true', help='Relaxed comparison: exclusion of digits, etc.')

args = parser.parse_args()
gt_dir = args.gt_dir
ocr_dir = args.ocr_dir
relaxed_comparison = args.relaxed
txt_format = args.format

def calculate_cosine_similarity(gt_text, ocr_text):

    # replace punctuations with space
    chars_to_replace = "-,;:!?\(\)\[\]\{\}#$^*\""
    pattern = f"[{re.escape(chars_to_replace)}]"
    gt_text = re.sub(pattern, " ", gt_text)
    ocr_text = re.sub(pattern, " ", ocr_text)
    
    gt_text = gt_text.lower()
    ocr_text = ocr_text.lower()

    # IDs: replace pattern G followed by a space and multiple digits by removing the space
    gt_text = re.sub(r'd\s+(\d+)', r'd\1', gt_text)
    ocr_text = re.sub(r'd\s+(\d+)', r'd\1', ocr_text)
    gt_text = re.sub(r'g\s+(\d+)', r'g\1', gt_text)
    ocr_text = re.sub(r'g\s+(\d+)', r'g\1', ocr_text)
    gt_text = re.sub(r'a\s+(\d+)', r'a\1', gt_text)
    ocr_text = re.sub(r'a\s+(\d+)', r'a\1', ocr_text)

    words1 = gt_text.split()
    words2 = ocr_text.split()

    #punctuation = '",;()[]:?!#'
    #words1 = [w.strip(punctuation) for w in words1]
    #words2 = [w.strip(punctuation) for w in words2]

    # remove the dot at the end of words
    words1 = [w.rstrip('.') for w in words1]
    words2 = [w.rstrip('.') for w in words2]

    if relaxed_comparison:
        print("... performing relaxed comparison")

        # remove diacritics
        words1 = ["".join(c for c in unicodedata.normalize('NFD', w) if unicodedata.category(c) != 'Mn') for w in words1]
        words2 = ["".join(c for c in unicodedata.normalize('NFD', w) if unicodedata.category(c) != 'Mn') for w in words2]

        # remove numbers with more than 4 digits
        words1 = [w for w in words1 if not (w.isdigit() and len(w) > 4)]
        words2 = [w for w in words2 if not (w.isdigit() and len(w) > 4)]

        # replace words starting with  "l'" or "d'" or "n'"
        words1 = [w.replace("l'", "") for w in words1]
        words2 = [w.replace("l'", "") for w in words2]
        words1 = [w.replace("d'", "") for w in words1]
        words2 = [w.replace("d'", "") for w in words2]
        words1 = [w.replace("n'", "") for w in words1]
        words2 = [w.replace("n'", "") for w in words2]
        words1 = [w.replace("c'", "") for w in words1]
        words2 = [w.replace("c'", "") for w in words2]

        
        # remove identifiers starting with d. or g. or k or ... (identifiers)
        #words1 = [w for w in words1 if not w.startswith(("d.", "g.","d-", "g-", "d ", "g ","k ","k.", "c.", "c-", "dl", "b.","est.","a-","a."))]
        #words2 = [w for w in words2 if not w.startswith(("d.", "g.","d-", "g-", "d ", "g ","k ","k.", "c.", "c-", "dl", "b.","est.","a-","a."))]

        # remove identifiers starting with d or g followed by a number
        #words1 = [w for w in words1 if not (len(w) > 1 and w[0] in 'dgck' and w[1:].isdigit())]
        #words2 = [w for w in words2 if not (len(w) > 1 and w[0] in 'dgck' and w[1:].isdigit())]

    # remove short words (less than 2 characters)
    words1 = [w for w in words1 if len(w) > 2]
    words2 = [w for w in words2 if len(w) > 2]

    counts1 = Counter(words1)
    counts2 = Counter(words2)
    
    all_words = set(counts1.keys()) | set(counts2.keys())
    pprint.pprint(sorted(all_words))

    dot_product = sum(counts1.get(word, 0) * counts2.get(word, 0) for word in all_words)
    mag1 = math.sqrt(sum(count**2 for count in counts1.values()))
    mag2 = math.sqrt(sum(count**2 for count in counts2.values()))
    
    score = dot_product / (mag1 * mag2) if mag1 and mag2 else 0.0
    print("Bag of Words similarity: \033[91m", "%0.2f" % score, "\033[m" )

    return (len(counts1), score)

# Bag of Words approach
def compute_global_similarity(csv_file) :

    total_words = 0
    total_score = 0
    n_rows = 0
    print("-----------------------------\n... reading ", csv_file)
    with open(csv_file, 'r') as csvfile:
        my_reader = csv.DictReader(csvfile, delimiter=",")
        #n_w = len(list(my_reader))
        #print("  lines: ", n_w)    
        for row in my_reader:
            n_rows += 1
            total_words += int(row['words'])
            total_score += float(row['bow_similarity'])

        print("... found ", n_rows, "rows")
        print("Global Bag of Words similarity (files average): \033[91m", "%0.2f" % (total_score / n_rows), "\033[m" )
        csvfile.seek(0)
        my_reader = csv.DictReader(csvfile, delimiter=",")
        weighted_sum = sum(float(row['bow_similarity']) * int(row['words']) for row in my_reader)
        print("Global Bag of Words similarity (weighted average): \033[91m", "%0.2f" % (weighted_sum / total_words), "\033[m")


def compute_global_bigram_similarity(csv_file):
    total_bigrams = 0
    total_score = 0
    n_rows = 0
    

def read_text(fh, format):
    
    if format == "json":
        txt = json.load(fh).get('text', '')
        print("\033[91mJSON:\033[m ", txt)
        return txt
    elif format=="txt":
        txt = fh.read()
        print("\033[91mText:\033[m ", txt)
        return txt
    else:
        txt = fh.read()
        txt = "\n".join(line for line in txt.splitlines() if not line.startswith('!')) 
        print("\033[91mMD:\033[m ", txt)
        return txt


def compare_folders(gt_dir, ocr_dir):
    global txt_format
    global nf

    results = []


    for filename in os.listdir(gt_dir):
        if not filename.endswith('.json'): continue
        print("--------------------\n...Evaluating ", filename)
        nf += 1

        gt_path = os.path.join(gt_dir, filename)
        filename_ocr = filename.replace('json', txt_format)
        ocr_path = os.path.join(ocr_dir, filename_ocr)

        if os.path.exists(ocr_path):
            with open(gt_path, 'r') as f1, open(ocr_path, 'r') as f2:
                gt_text = read_text(f1, "json")
                ocr_text = read_text(f2, txt_format)
                if not gt_text: 
                    print("\n\033[91m...skipping, GT is empty\033[m ")
                    print("\n\033[91mOCR : ", ocr_text, "\033[m")
                    continue
                (n_words,score) = calculate_cosine_similarity(gt_text, ocr_text)   
                if n_words  == 0: 
                    print("\033[91m...skipping, no words in the GT\033[m ")
                    continue   
                results.append({'filename': filename,'words': n_words, 'bow_similarity': "%0.4f" % score})

    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['filename','words', 'bow_similarity'])
        writer.writeheader()
        writer.writerows(results)

if __name__ == "__main__":
    if not os.path.exists(gt_dir):
        print(f"Error: Ground truth directory '{gt_dir}' does not exist.")
        exit(1)
    if not os.path.exists(ocr_dir):
        print(f"Error: OCR directory '{ocr_dir}' does not exist.")
        exit(1)
    
    compare_folders(gt_dir, ocr_dir)
    print(f"\n-----------------------------\nAnalysis of {nf} files of ground truth")
    compute_global_similarity(output_csv)    
    print("(relaxed comparison: ", relaxed_comparison,")")

    #compare_json_folders('ocr_corrigés_371', 'ocr_output')
