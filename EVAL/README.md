# Evaluation 

**Plan** : 

- [*Contexte*](#Contexte)
- [*Evaluation*](#evaluation)
- 

***

## Contexte

Mesure de la qualité

## Vérité terrain

Les annotations sont produites avec Label Studio.
Elles portent sur :
- la localisation de l'illustration dans la page scannée
- le type de l'illustration : dessin, photo, etc.
- la rotation éventuelle de l'illustration

1. Exporter au format JSON le dataset depuis [LabelStudio](https://labelstud.io/guide/export)


2. Dans le dossier de travail Python, créer un sous-dossier nommé d'après le dataset, par exemple :

```
> mkdir set_monos
> cd set_monos
```

Y copier l'export JSON : 
```
> cp mon_path/export.json ./dataset_LS_monos.json
```

## Segmentation 

1. Extraire du fichier .json les URL des pages qui ont été annotées dans Label Studio :

> grep "iiif" dataset_LS_monos.json > liste_pages.txt

Editer le fichier pour aboutir à un format ark-vue :
```
btv1b103365581-f1
btv1b103365581-f13
btv1b103365581-f17
btv1b103365581-f2
btv1b103365581-f21
btv1b103365581-f31
btv1b103365581-f32
```


4. Si besoin, filtrer les pages à exclure (pages déjà utilisées par LJN pour de l'entrainement) avec un tableau Excel fourni par LJN


5. Avec le script extract_illustrations.py, extraire les données de la vérité terrain
(ground truth) du dataset LabelStudio .json et de la liste filtrée :

> cd ..
> python3 extract_illustrations.py set_monos

## Divers


