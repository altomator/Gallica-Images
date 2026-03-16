import sys
import json
import os
import re
import datetime
import numpy as np
from itertools import islice
import itertools
from functools import partial
from fnmatch import fnmatch, fnmatchcase
from contextlib import ExitStack
from oaipmh.client import Client 
# Créer un environnement virtuel : 
# cd pyoai-master # https://github.com/infrae/pyoai/blob/master/INSTALL.txt
# python setup.py install
# 
from pprint import pprint
from urllib.parse import unquote
import uuid
from tqdm import tqdm
import argparse


# packages locaux
from document import Document
from collections import defaultdict, namedtuple


#[ROOT] | Path de l'ensemble des annotations
root = "./root/"

# Gestion des données
nImages = 0
nAnnotations = 0

#[TEMPLATE] |Template du dataset
formatter = {
	"info": {
		"description": "Dataset from the National Library of France harvesting from http://gallica.bnf.fr/",
		"contribuor": ["Axel ETO","Jean-Philippe MOREUX", "Alexandra ADAMOVA"]
	},
	"documents": [],
	"images": [],
	"annotations":[]
}

#### ####
parser = argparse.ArgumentParser()
parser.add_argument("-max","-m", type=int, help="nombre d'images à exporter")
args = parser.parse_args()

#[PULL] | Generators d'annotation
def pull_annotations(root:str):

	#récupère l'ensemble des fichiers .json présent dans root
	dataset = lambda directory: [os.path.join(dirpath,file) for dirpath,_,files in os.walk(directory)
							for file in files if fnmatch(file,f'*.json')]

	#ouvre un context manager pour l'ensemble des fichiers
	with ExitStack() as context:
		path_context = [context.enter_context(open(file,'r',encoding='utf-8')) for file in dataset(root)]
		readers = map(lambda f: (json.load(f),f.name),path_context)

		#yield annotation
		for f, filename in readers:
			for obj in f:
				yield obj

#[ROUNDING] | Pour arrondir les [bbox,polygon]
def rounding(inst, decimal):
	if isinstance(inst, dict):
		for key in inst.keys():
			if isinstance(inst[key], float):
				inst[key] = round(inst[key], decimal)
			if isinstance(inst[key], list):
				inst[key] = [[round(element, decimal) for element in sublist] for sublist in inst[key]]

#[MAPPING] Return un dictionaire de [area, bbox, points|ellipse]
def coords_area(label, type_, coords):
	rounding(coords,2)

	#{bbox}
	if type_ == 'bbox':
		area = coords['width'] * coords['height']
		return {'area': area, 'bbox': coords, }

	#{point}
	if type_ == 'poly':
		x = [p[0] for p in coords['points']]
		y = [p[1] for p in coords['points']]
		bbox = {'x': min(x), 'y': min(y), 'width': max(x) - min(x), 'height': max(y) - min(y)}
		area = bbox['width'] * bbox['height']
		return {'area': area, 'points': coords['points'], 'bbox': bbox}
	#{ellipse}
	if type_ == 'ellipse':
		top_left = [coords['x'] - coords['radiusX'], coords['y'] - coords['radiusY']]
		bottom_right = [coords['x'] + coords['radiusX'], coords['y'] + coords['radiusY']]
		width = bottom_right[0] - top_left[0]
		height = bottom_right[1] - top_left[1]
		bbox = {'x':top_left[0], 'y':top_left[1], 'width': width, 'height': height}
		area = np.multiply(width, height)
		return {'area': area,'ellipse': coords, 'bbox': bbox}

#[ARK/REGEX] Récupère [ARK,VUE] du path de l'image à partir de regex
def get_arkview_from_path(obj):

		filename = unquote(obj['data']['image']).replace('$','').split('/')[-1]
		match = re.findall(r'(.*)-(f\d+)-full',filename)
		if not match:
			match = re.findall(r'^(.*)(f\d+)full',filename)

		ark, view = match[0]
		return ark, view


#[EXTRACT|MAPPING] 'result' from LabelStudio
def result(obj):
	global nAnnotations
	meta = False
	dict_ = defaultdict(lambda: defaultdict(list))
	for x in obj['annotations'][0]['result']:
		nAnnotations +=1
		dict_[x['id']]['value'] = x['value']
		dict_[x['id']]['type'].append(x['from_name'])
		if x.get('meta'): meta = x['meta']


	result_list = []
	for id_, obj in dict_.items():
		*coords, label = obj['value'].items()
		coords = {tuples[0]:tuples[1] for tuples in coords}
		type_ = obj['type'].pop(0)
		result = coords_area(label, type_, coords)
		result['label'] = label[1]
		result['meta'] = meta
		result_list.append(result)
	return result_list


def mapping_labelstudio(generators_obj):
	global nImages

	for obj in tqdm((generators_obj)):
		ark = get_arkview_from_path(obj)[0]
		image = get_arkview_from_path(obj)[1]
		image_id = str(uuid.uuid4())
		# stop si max défini et n >=max
		if args.max and nImages>=args.max:
			break
		nImages += 1
		width = obj["annotations"][0]['result'][0]['original_width']
		height = obj['annotations'][0]['result'][0]['original_height']
		try:
			mapping = {
				'document': {
					'ark' : ark,
					'metadata' : Document(ark).metadata
				},
				'image':{
					'ark': ark,
					'id': image_id,
					'width': obj["annotations"][0]['result'][0]['original_width'],
					'height': obj["annotations"][0]['result'][0]['original_height'],
					'iiif': f"https://gallica.bnf.fr/iiif/ark:/12148/{ark}/{image}/full/!{width},{height}/0/native.jpg"
				},
				'annotation':{
					'id' : image_id,
					'result': result(obj)
				}
			}
		except KeyError as err:
			print(f'[keyerror] vérifier annotation | {ark}-{image} | {err} ')
		yield mapping


def dumps_annotation(generators_obj):

	dt = datetime.datetime.now().strftime("%m-%d-%Y-%H-%M-%S")

	file = open(f'gallica_dataset-at-{dt}.json', 'w', encoding='utf-8')
	file.write(json.dumps(formatter))
	file.close()

	filename = file.name
	read = open(filename, 'r', encoding='utf-8')
	dataset = json.load(read)
	read.close()

	for obj in (generators_obj):
		dataset['documents'].append(obj['document'])
		dataset['images'].append(obj['image'])
		dataset['annotations'].append(obj['annotation'])


	with open(filename, 'w', encoding='utf-8') as f:
		json.dump(dataset, f, indent=4,ensure_ascii=False)

# MAIN #
pull_annotation = pull_annotations(root)
mapping_annotation = mapping_labelstudio(pull_annotation)
dumps_annotation(mapping_annotation)
print("--------------------")
print (" images : ",nImages)
print (" annotations : ",nAnnotations)
print("--------------------")
