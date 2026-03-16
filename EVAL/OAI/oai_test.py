from oai import OAINUM
from fnmatch import fnmatch
from pprint import pprint
import os

dir_ = './data/sets/'

# Créer une instance `gallica` et récupérer l'ensemble des sets présents à l'intérieur de l'entrepôt
gallica = OAINUM('http://oai.bnf.fr/oai2//OAIHandler', directory=dir_)
setspec,setname = gallica.listSets
print("... sets: ", len(setspec))
print("... exemples : ", setspec[250], setname[250])
print("-------------------")

# Extraire un set :
sets = ["gallica:typedoc:images"]
gallica.pullSets(*sets,mb=10)

# Extraire un record :
print(gallica.getRecord('btv1b6937398m'))
