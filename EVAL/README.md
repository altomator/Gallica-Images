# Evaluation 

**Plan** : 

- [*Contexte*](#Contexte)
- [*Evaluation*](#evaluation)
- 

***

## Contexte

Mesure de la qualité des modèles d'IA entraînés dans le cadre du projet Gallica Images.


## Vérité terrain

Les annotations sont produites avec Label Studio.
Elles portent sur :
- la localisation de l'illustration dans la page scannée,
- le type de l'illustration : dessin, photo, etc.,
- la rotation éventuelle de l'illustration.

Plusieurs datasets Labe Studio sont disponibles dans le dossier [DATASETS](), organisés par type documentaire :
- photographie
- dessin
- estampe


1. Exporter au format JSON le dataset depuis [LabelStudio](https://labelstud.io/guide/export).


2. Dans le dossier de travail Python, créer un sous-dossier nommé d'après le dataset, par exemple :

```
> mkdir SET1
> cd SET1
```

Y copier l'export JSON sous le nom `dataset_LS.json` : 
```
> cp mon_path/export.json ./dataset_LS.json
```

## Contrôle de la segmentation 

### Préparation des données 

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


4. Si besoin, filtrer les pages à exclure (pages déjà utilisées pour l'apprentissage).


5. Avec le script `extract_illustrations.py`, extraire les données de la vérité terrain
(_ground truth_) du dataset LabelStudio et de la liste filtrée :

```
cd ..
python3 extract_illustrations.py SET1 --iiif
```

Ce script produit : 
- images des pages annotées avec l'API IIIF (optionnel) : dossier `GT_PAGES`
- vignettes des illustrations annotées avec l'API IIIF (optionnel) : dossier `GT_ILLUSTRATIONS`, avec des sous-dossiers par type
- données CSV pour chaque illustration (ark, titre du document, n° de vue, bounding box, rotation, type de l'illustration) enregistrées dans un fichier `GT.csv`. 
- les mêmes données au format Pascalvoc pour chaque illustration, dans un sous-dossier `DATA_gt` (fichiers nommés ark-vue.txt)

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


6. Avec le script `get_response.py`, extraire les données de la base Gallica Image relatives aux pages de la vérité terrain :

> python3 get_response.py SET1

Ce script est à lancer depuis le réseau BnF. Il lit la liste des pages annotées (`SET1/liste_pages.txt`) et produit : 
   - une réponse JSON par document Gallica,
   - stockée dans le dossier du dataset, dans un sous-dossier `DATA_db`.


7. Avec le script `extract_response.py`, exploiter les données de la base Gallica Image stockées dans `DATA_db` :

> python3 extract_response.py SET1

Ce script produit : 
 - un fichier .txt par illustration de la base (classe, confiance, bbox), stocké dans un dossier `DATA_detect`,
 - une vignette par illustration (optionnel), dans un dossier `ILL`.

Ce script annote également les images des pages (dossier `GT_PAGES`) avec les boîtes englobantes des détections (en rouge).

A ce stade, le dossier de travail doit être conforme à :
![Image annotée](https://github.com/altomator/Gallica-Images/blob/main/img/dossier.png "Dossier de travail")


### Calcul des métriques



## Divers


