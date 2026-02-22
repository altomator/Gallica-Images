import pandas as pd
import argparse
from sklearn.metrics import confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import precision_recall_curve


def load_csv(file_path):
    return pd.read_csv(file_path)

parser = argparse.ArgumentParser(description="Align illustrations bounding boxes from ground truth data and dectections data.")
parser.add_argument('data',  help='data file')
args = parser.parse_args()
data_file =  args.data


if __name__ == "__main__":
    df = load_csv(data_file)
    print(df.head())

    gt_df = df.dropna(subset=['gt_x', 'gt_y', 'det_x', 'det_y'])
    print(gt_df.head())
    print(len(gt_df))

    # ROTATION
    gt_df['gt_rot'] = gt_df['gt_rot'].astype(int)
    gt_df['det_rot'] = gt_df['det_rot'].astype(int)
    print(f"Unique gt_rot values: {gt_df['gt_rot'].unique()}")
    print(f"Unique det_rot values: {gt_df['det_rot'].unique()}\n")
    print(gt_df['gt_rot'].value_counts())
    print(gt_df['det_rot'].value_counts())

    labels = sorted(gt_df['det_rot'].unique())
    cm = confusion_matrix(gt_df['gt_rot'], gt_df['det_rot'], labels=labels)
    print("Matrice de confusion : rotations réelles / détectées")
    print(pd.DataFrame(cm, index=labels, columns=labels))

    cm_norm = confusion_matrix(gt_df['gt_rot'], gt_df['det_rot'], labels=labels, normalize='true')
    plt.figure(figsize=(10, 7))
    sns.heatmap(cm_norm, annot=True, fmt='.1%', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title('Matrice de confusion normalisée : rotations réelles / détectées')
    plt.xlabel('Rotations détectées')
    plt.ylabel('Rotations réelles')
    plt.show()

    from sklearn.metrics import classification_report
    print("\Rapport de classification 'rotation' :")
    print(classification_report(gt_df['gt_rot'], gt_df['det_rot'], labels=labels))

    print("\nCourbe de précision-rappel 'rotation' :")
    for label in labels:
        precision, recall, _ = precision_recall_curve(gt_df['gt_rot'] == label, (gt_df['det_rot'] == label).astype(int))
        plt.plot(recall, precision, label=f'Class {label}')
    plt.xlabel('Rappel')
    plt.ylabel('Précision')
    plt.title('Courbe de précision-rappel pour la rotation')
    plt.legend()
    plt.show()

    print("-------------------------")
    # TECHNIQUE
    print(f"Unique gt_tech values: {gt_df['gt_tech'].unique()}")
    print(f"Unique det_tech values: {gt_df['det_tech'].unique()}\n")
    print(gt_df['gt_tech'].value_counts())
    print(gt_df['det_tech'].value_counts())

    labels = sorted(gt_df['det_tech'].unique(), reverse=False)
    cm = confusion_matrix(gt_df['gt_tech'], gt_df['det_tech'], labels=labels)
    print("Matrice de confusion : techniques réelles / détectées")
    print(pd.DataFrame(cm, index=labels, columns=labels))

    cm_norm = confusion_matrix(gt_df['gt_tech'], gt_df['det_tech'], labels=labels, normalize='true')
    plt.figure(figsize=(10, 7))
    sns.heatmap(cm_norm, annot=True, fmt='.1%', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title('Matrice de confusion normalisée : techniques réelles / détectées')
    plt.xlabel('Techniques détectées')
    plt.ylabel('Techniques réelles')
    plt.show()

    from sklearn.metrics import classification_report
    print("\nTechnique Classification Report:")
    print(classification_report(gt_df['gt_tech'], gt_df['det_tech'], labels=labels))

    print("\nTechnique Precision-Recall Curve:")
    for label in labels:
        precision, recall, _ = precision_recall_curve(gt_df['gt_tech'] == label, (gt_df['det_tech'] == label).astype(int))
        plt.plot(recall, precision, label=f'Class {label}')
    plt.xlabel('Rappel')
    plt.ylabel('Précision')
    plt.title('Courbe de précision-rappel pour la technique')
    plt.legend()
    plt.show()
    print("-------------------------")
