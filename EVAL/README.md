# Evaluation 

**Plan** : 

- [*Contexte*](#Contexte)
- [*Vérité terrain*](#Contexte)
- [*Evaluation quantitative*](#evaluation)
- [*Evaluation qualitative*](#evaluation)


***

## Contexte

Mesure de la qualité des modèles d'IA entraînés dans le cadre du projet Gallica Images.


## Vérité terrain

Les annotations sont produites avec Label Studio.
Elles portent sur :
- la localisation de l'illustration dans la page scannée,
- le type de l'illustration : dessin, photo, etc.,
- la rotation éventuelle de l'illustration.

Plusieurs datasets Label Studio sont disponibles dans le dossier [DATASETS](), organisés par type documentaire :
- photographie,
- dessin,
- estampe.


1. Exporter au format JSON le dataset depuis [LabelStudio](https://labelstud.io/guide/export).


2. Dans le dossier de travail Python, créer un sous-dossier nommé d'après le dataset, par exemple :

```
mkdir SET1
cd SET1
```

Y copier l'export JSON sous le nom `dataset_LS.json` : 
```
cp mon_path/export.json ./dataset_LS.json
```

## Evaluation quantitative

### Contrôle de la segmentation 

#### 1. Préparation des données 

1. Extraire du fichier .json les URL des pages qui ont été annotées dans Label Studio :

> grep "iiif" dataset_LS.json > liste_pages.txt

Editer le fichier `liste_pages.txt`pour aboutir à un format `ark-vue` :
```
btv1b103365581-f1
btv1b103365581-f13
btv1b103365581-f17
btv1b103365581-f2
btv1b103365581-f21
...
```


4. Si besoin, filtrer les pages à exclure (pages utilisées pour l'apprentissage).


5. Avec le script `extract_illustrations.py` ([source](https://github.com/altomator/Gallica-Images/blob/main/EVAL/LabelStudio/extract_illustrations.py)), extraire les données de la vérité terrain
(_ground truth_) du dataset LabelStudio et de la liste filtrée. Il dispose de deux options :

- extraction des vignettes des pages et des illustrations avec l'API Gallica IIIF : `--iiif`
- annotation des pages avec les boîtes englobantes des illustrations : `--annot`
- facteur de taille de téléchargement des images IIIF (50% par défaut)
  
```
cd ..
python3 extract_illustrations.py SET1 --iiif 25
```

Ce script produit : 
- images des pages annotées avec l'API IIIF (optionnel) : dossier `GT_PAGES`
- vignettes des illustrations annotées avec l'API IIIF (optionnel) : dossier `GT_ILLUSTRATIONS`, avec des sous-dossiers par type
- données CSV pour chaque illustration (ark, titre du document, n° de vue, bounding box, rotation, type de l'illustration) enregistrées dans un fichier `GT.csv`. 
- les mêmes données au format Pascalvoc pour chaque illustration, dans un sous-dossier `DATA_gt` (fichiers nommés ark-vue.txt)

Note : les boîtes sont exprimées en valeur relative (% des dimensions de la page).

Exemple `GT.csv` : 
```
ARK,Title,Vue Number,BBOX (%),Rotation,Label
btv1b103365581;[Recueil. Portraits d'Aristide Briand];1;9.06,6.28,82.04,69.47,0,photographie,
btv1b103365581;[Recueil. Portraits d'Aristide Briand];13;21.43,16.12,57.66,52.78,0,photographie,
btv1b103365581;[Recueil. Portraits d'Aristide Briand];17;1.98,1.67,94.27,81.0,0,photographie,
btv1b103365581;[Recueil. Portraits d'Aristide Briand];2;8.38,5.28,82.23,70.71,0,photographie,
...
```

Dans le cas d'une page contenant plusieurs illustrations : 
```
btv1b8432385n;Una visita al fronte italiano : Maggio 1916;6;39.38,18.94,21.4,23.37,0,photographie,19.02,52.77,21.66,23.23,0,photographie,57.74,53.07,21.6,23.58,0,photographie,
```

Exemple Pascalvoc pour le fichier `btv1b103365581-6.txt` :
```
photographie 0.39380000000000004 0.1894 0.214 0.23370000000000002
photographie 0.1902 0.5277000000000001 0.21660000000000001 0.2323
photographie 0.5774 0.5307 0.21600000000000003 0.23579999999999998
```

Ce script annote également les images des pages annotées (dossier `GT_PAGES`) avec les boîtes englobantes (en vert) des illustrations de la vérité terrain.

![Image annotée](https://github.com/altomator/Gallica-Images/blob/main/img/page.png "Page annotée")


6. Avec le script `get_response.py` ([source](https://github.com/altomator/Gallica-Images/blob/main/EVAL/LabelStudio/get_response.py)), extraire les données de la base Gallica Image relatives aux pages de la vérité terrain :
```
python get_response.py SET1
```
Ce script est à lancer depuis le réseau BnF. Il lit la liste des pages annotées (`SET1/liste_pages.txt`) et produit : 
   - une réponse JSON par document Gallica,
   - stockée dans le dossier du dataset, dans un sous-dossier `DATA_db`.


7. Avec le script `extract_response.py` ([source](https://github.com/altomator/Gallica-Images/blob/main/EVAL/LabelStudio/extract_response.py)), exploiter les données de la base Gallica Image stockées dans `DATA_db` :

```
python extract_response.py SET1
```

Ce script produit : 
 - un fichier .txt par page au format Pascal VOC (classe, confiance, x, y, w, h), stocké dans un dossier `DATA_detect`. Le format est enrichi par les métadonnées suivantes : rotation, fonction, genre, ARK de l'illustration
- un fichier JSON par page incluant les principales métadonnées et les textes océrisés, dans un dossier `DATA_ocr`,
- une vignette par illustration (optionnel), dans un dossier `ILL`.

Exemple du format Pascal VOC pour btv1b8432385n-6.txt (3 illustations décrites) :
```
photographie 1.0 0.395065 0.188601 0.21510300000000002 0.234205 0 Carte_postale Représentations_humaines_/_Portraits bfkfk28zc4k 
photographie 1.0 0.579109 0.529845 0.215216 0.235005 0 Carte_postale Représentations_humaines_/_Portraits bfkfk28zc68 
photographie 1.0 0.191361 0.523878 0.21456399999999998 0.238319 0 Carte_postale Représentations_humaines_/_Portraits bfkfk28zc5x 
```

Exemple du format JSON pour btv1b8432385n-6.json :
```
{
"doc_ark": "btv1b8432385n",
"page": "6",
"title": "Una visita al fronte italiano : Maggio 1916",
"ills":[
{
    "ark": "bfkfk28zc4k",
    "bbox": "39.5065,18.8601,21.5103,23.4205",
    "technic": "photographie",
    "function": "Carte_postale",
    "genre": "Repr\u00e9sentations_humaines_/_Portraits",
    "rotation": "0",
    "content_section": "N/A",
    "content_text": "N/A",
    "context_text_before": "N/A",
    "context_text_after": "Venise"
},
{...
```
Ce script annote également les images des pages (dossier `GT_PAGES`) avec les boîtes englobantes des détections (en rouge).

A ce stade, le dossier de travail doit être conforme à :

![Dossier](https://github.com/altomator/Gallica-Images/blob/main/img/dossier.png "Dossier de travail")


#### 2. Calcul des métriques

1. Recopier les dossiers `DATA_gt` et `DATA_detect` dans le dossier de calcul des métriques `SegMetric`.

9. Harmoniser les fichiers (on doit obtenir le même nombre de fichiers dans chacun des deux dossiers) avec le script `clean_files.py` ([source](https://github.com/altomator/Gallica-Images/blob/main/EVAL/segmentation/clean_files.py)) :

```
python clean_files.py DATA_gt DATA_detect
```

10. Calculer les métriques : 

L'objectif est d'aligner les segmentations (boîtes englobantes) entre la vérité terrain et les détections puis de mesurer une métrique de recouvrement.

Pour ce faire, le script calcule la moyenne (mAP) des précisions moyennes de chaque classe (AP, _average precision_), en considérant une détection correcte si la valeur IoU (_intersection over union_) de recouvrement entre la vérité terrain et la boîte prédite est ≥ à un seuil donné et la classe est correcte (ici la technique de l'illustration). mAP@50 signifie donc _mean Average Precision_ pour un IoU de 0.50.

![IoU](https://github.com/altomator/Gallica-Images/blob/main/img/iou.jpg "IoU")

Installer localement les bibliothèques `lib` de ce [github](https://github.com/eypros/Object-Detection-Metrics/tree/master) puis appeler le script `analyse-AP.py` ([source](https://github.com/altomator/Gallica-Images/blob/main/EVAL/segmentation/analyse-AP.py)) avec les paramètres suivants :
- les techniques présentes dans le dataset,
- le seuil de détection IoU (0.5 par défaut = permissif, 0.75 = strict).
  
```
python analyse-AP.py --accepted-classes photographie dessin estampe --gt-coords rel --det-coords rel --gt-format xywh --det-format xywh --img-size 800,800 --threshold 0.75 --gt-folder DATA_gt --det-folder DATA_detect
```

Pour focaliser l'analyse sur la segmentation et non la segmentation + classification, demander l'analyse sur la classe principale du dataset :
```
python analyse-AP.py --accepted-classes photographie --gt-coords rel --det-coords rel --gt-format xywh --det-format xywh --img-size 800,800 --threshold 0.75 --gt-folder DATA_gt --det-folder DATA_detect
```

Le script calcule la courbe AP et la valeur de la précision moyenne pour chaque classe (la précision moyenne est l'aire sous la courbe précision-rappel d'un détecteur d'objets pour une classe donnée) ainsi que la moyenne des moyennes.

![Courbe AP](https://github.com/altomator/Gallica-Images/blob/main/img/AP.png "Courbe AP")

Métriques AP : 
```
AP: 0.00000 (décoration)
AP: 0.80920 (photographie)
mAP: 0.40460
```

### Contrôle des classifications (technique, fonction, genre)

Les classifications générées sont décrites dans les fichiers du dossier `DATA_detect` :
- technique de l'illustration,
- fonction et genre de l'illustration,
- éventuelle rotation de l'illustration.

Afin de minimiser l'influence de la segmentation sur l'évaluation de ces données, on aligne au préalable la vérité terrain et les détections (même approche que ci-avant) avec le script `align-BB.py` ([source](https://github.com/altomator/Gallica-Images/blob/main/EVAL/classification/align-BB.py)), puis les mesures sont faites sur les illustrations alignées.

1. Alignement avec un seuil IoU :
   
```
python align-BB.py DATA_gt DATA_det 0.75
    ...
...processing  btv1b8529846d-9 
   found a match for:  bfkfk25r8x6 
...saving aligned CSV for btv1b8529846d-9
---------------------------------
Number of files in GT: 633
Number of BBox in GT: 1006
Number of detected BBox: 996
Number of matches: 953
---------------------------------
```

2. Mesures

Le script `analyse.py` ([source](https://github.com/altomator/Gallica-Images/blob/main/EVAL/classification/analyse.py)) produit une série d'analyses sur les illustrations alignées : 
- matrice de confusion
- courbe de précision/rappel

```
python analyse.py aligned.csv
```

3. Contrôle visuel
4. 



### Contrôle de l'OCR




## Evaluation qualitative

### Avec Panoptic

## Divers


