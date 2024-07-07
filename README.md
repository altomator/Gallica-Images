# Gallica Images

## Modèle de données

Une illustration est décrite par sa technique de production (technique graphique, matériau de l'oeuvre), sa fonction et son genre.
Ces métadonnées sont indexées dans le catalogue général et proposées à la [recherche](https://catalogue.bnf.fr/recherche-uni-images-cartes.do?pageRech=imc).

### 1. Technique
Le modèle reprend les valeurs normalisée de la zone d'indexation [285](https://www.bnf.fr/sites/default/files/2018-11/IF_cattechnique.pdf) ("Technique de l’image") du format INTERMARC-B (sous-zone $f) :

- *collage* (technique mixte)
- dessin
- estampe
- impression (photomécanique, numérique)
- peinture
- photocopie
- photographie (négative, positive, positive directe, numérique)
- document électronique (né numérique) 

Note : la [zone 285](https://multimedia-ext.bnf.fr/pdf/pb-RIMB08_285.pdf) reprend les informations de la [zone 280]((https://multimedia-ext.bnf.fr/pdf/pb-RIMB18_280.pdf) (texte rédigé) mais en les normalisant avec un vocabulaire contrôlé.

La sous-zone [$j](https://www.bnf.fr/sites/default/files/2018-11/intermarc_ref_if-tech-img.pdf) décrit la technique précise de l'image (pour le dessin par exemple : crayon, fusain, pastel, etc.), mais ce niveau de description n'est pas mis en oeuvre dans le projet.

La sous-zone [$g](https://www.bnf.fr/sites/default/files/2018-11/intermarc_ref_if-materiau-doc.pdf) informe du matériau utilisé (nature du support du document iconographique).

### 2. Fonction

