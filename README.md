# Gallica Images

## Modèle de données

Une illustration est décrite par sa technique de production (technique graphique, matériau de l'oeuvre), sa fonction et son genre.
Ces métadonnées sont indexées dans le catalogue général et proposées à la [recherche](https://catalogue.bnf.fr/recherche-uni-images-cartes.do?pageRech=imc).

### 1. Technique
Le modèle reprend les valeurs normalisée de la zone d'indexation [285](https://www.bnf.fr/sites/default/files/2018-11/IF_cattechnique.pdf) ("Technique de l’image") du format INTERMARC-B (sous-zone $f) :

- **collage** (technique mixte)
- **dessin**
- **estampe**
- **impression** (photomécanique, numérique)
- **peinture**
- **photocopie**
- **photographie** (négative, positive, positive directe, numérique)
- **document électronique** (né numérique) 

_Note_ : la [zone 285](https://multimedia-ext.bnf.fr/pdf/pb-RIMB08_285.pdf) reprend les informations de la [zone 280]((https://multimedia-ext.bnf.fr/pdf/pb-RIMB18_280.pdf) (texte rédigé) mais en les normalisant avec un vocabulaire contrôlé.

La sous-zone [$j](https://www.bnf.fr/sites/default/files/2018-11/intermarc_ref_if-tech-img.pdf) décrit la technique précise de l'image (pour le dessin par exemple : crayon, fusain, pastel, etc.), mais ce niveau de description n'est pas mis en oeuvre dans le projet.

La sous-zone [$g](https://www.bnf.fr/sites/default/files/2018-11/intermarc_ref_if-materiau-doc.pdf) informe du matériau utilisé (nature du support du document iconographique).

Dans le contexte du projet Gallica Images, les catégories à inférer par un modèle IA peuvent être réduites à :

- **collage** 
- **dessin**
- **estampe**
- **impression photomécanique** 
- **peinture**
- **photographie**

Il faut noter que les techniques d'impression photomécanique et photographique ont la capacité à reproduire tous les documents iconographiques : 
- photographie d'une peinture : technique = photographie / fonction = reproduction photographique d'une peinture
- impression d'une peinture dans un livre d'art : technique = impression photomécanique / fonction = reproduction photomécanique d'une peinture

### 2. Forme ou fonction

Certains documents iconographiques appartiennent à un type lorsqu’ils ont une fonction particulière. Cf. zone d'indexation [646](https://www.bnf.fr/sites/default/files/2018-11/intermarc_ref_if-typo-img.pdf) ("Typologie des images") du format INTERMARC-B (sous-zone $a).

Un référentiel dédié existe pour les cartes et plans (zone [647](https://www.bnf.fr/sites/default/files/2018-11/DocCart_Typo%2C0.pdf).

- **Affiche** (affiches, posters)
- **Album** (album ou portfolio de photographies, carte-album) — relève plutôt du niveau du document
- **Bande dessinée**
- **Billet** (de souscription, d'entrée...)
- **Calendrier** (calendrier, almanach, agenda...)
- **Carte/faire-part** (de visite, de voeux, d'invitation,  publicitaire, faire-part de mariage...)
- **Carnet de dessins** — relève plutôt du niveau du document
- **Carte** (carte, globe...)
- **Couverture** (page de titre, couverture, faux-titre...)
- **Carte à jouer**
- **Carte postale**
- **Croquis d'architecture** (coupe, élévation, détail, profil...
- **Étiquette**
- **Éventail**
- **Ex-libris**
- **Graphique** (graphe, schéma technique...)
- **Image**
    - Image à découper
    - Image de mode
    - Image de presse
    - Image d'Épinal
    - Image publicitaire
    - Image religieuse 
- **Jeu** (abécédaire, album de jeux pour enfants, album à colorier, jeu de l'oie, puzzle, rébus, mots-croisés...)
- **Maquette** (à découper, de reliure, de décor, de costume...)
- **Menu** (de restaurant)
- **Ornement** (typographique, gravé)
- **Plan d'architecture** (plan au sol, plan de masse, plan de situation...)
- **Plan** (plan de ville, plan parcellaire, plan cadastral...)
- **Papier-peint** (échantillon de papier-peint)
- **Partition illustrée**
- **Tableau** (au sens d'illustration dans un document imprimé)
- **Autres** (Annonce d'éditeur, Assignat, Autocollant, Bon d'échange, Bon point, Brevet, Bulletin de paie, Canard, Cartouche, Certificat, Cocarde, Décalcomanie, Dessus de boîte, Dessus de bouton, Diplôme, Domino, Écran, Ephemera (publication), Feuille d'imposition, Frontispice, Kakémono, Kamishibaï, Laissez-passer, Livre animé, Livre d'artiste, Macédoine, Marque typographique, Marque-page, Matériel didactique, Modèle (architecture), Panneau décoratif, Panneau didactique, Papier à en-tête, Papier à lettres, Papier d'emballage, Passeport, Placard, Placard de thèse, Portfolio, Programme, Prospectus, Relevé (archéologie), Sac, Timbre d'artiste, Timbre-poste, Tract, Vignette, Vue d'optique, Vue stéréoscopique

_Notes_ : 
- les sous-types de la catégorie _image_ doivent être mobilisés selon les genres documentaire à traiter. 
- de même, selon les contextes, des sous-catégories peuvent être considérées comme d'importance et valorisées en tant que type (par exemple les mots-croisés dans les collections de périodiques).
- les sous-types de la catégorie _autres_ ne seront pas considérées.


