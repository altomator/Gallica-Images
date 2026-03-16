from label_studio_sdk.client import Client
from label_studio_sdk.project import Project
from label_studio_sdk.data_manager import Column, Filters, Operator, Type
from urllib.parse import unquote
from datetime import datetime
from dateutil import parser
from pprint import pprint
import sys
import requests
import os
import re
import json

templates = """
<View>
	<Image name="image" value="$image"/>  
	<Header value="zone graphique"/>
		<Labels name="type" toName="image">
		<Label value="estampe" background="#ff0000"/>
		<Label value="photographie" background="#007bff"/>
		<Label value="dessin" background="#fb00ff"/>
		<Label value="décoration" background="#8589ff"/>
		<Label value="timbre" background="#ff6bd8"/>
		<Label value="tampon" background="#FFA39E"/></Labels>
	<Header value="zone textuelle"/>
	<Labels name="transcription" toName="image">
		<Label value="écriture manuscrite" background="#00ff4c"/>
		<Label value="écriture typographique" background="#a8b404"/>
	</Labels>
<Rectangle name="bbox" toName="image" strokeWidth="3"/>
<Polygon name="poly" toName="image" strokeWidth="3"/>
<Ellipse name="ellipse" toName="image"/>
</View>"""


URL = 'http://localhost:8080'
API_KEY = '36908b5e712c188d28c5b94bcda2f5209cf2ec93'
path_storage = 'C:\\Users\\gusta\\Desktop\\gallicapix_images\\images'
external_labelstudio = './project-26-at-2023-05-06-23-32-91e68d58.json'




def check_connection(url, access_token):
	ls = Client(url,access_token)
	checking, = ls.check_connection().values()
	if checking == 'UP':
		return ls 
	else: 
		print('La connection à échouer. Vérifier le domain où la clée')

def get_or_set_project(client,**kwargs):

	# templates= open('../packages_gallica/data/templates.txt',"r",encoding='utf8').read()
	kwargs['label_config'] = templates

	projects = client.list_projects()
	list_projects = [obj.get_params() for obj in projects]


	for obj in list_projects:
		if kwargs['title'] == obj['title']:
			url = client.get_url('projects') + "/" + str(obj['id'])
			print(f'{"[GET]":10}|{obj["title"]}\n{"":10}|par {obj["created_by"]["email"]:5}\n{"":10}|{url}\n')
			return client.get_project(obj['id'])
		else: 
			post_project = client.start_project(**kwargs)
			post_params = post_project.get_params()
			url = client.get_url('projects') + "/" + str(post_params['id'])
			print(f'{"[POST]":10}|{kwargs["title"]}\n{"":10}|par {post_params["created_by"]["email"]}\n{"":10}|{url}\n')
			return post_project

def rename_files_from_tree(path_storage, extension):
	is_ = 0
	isnot = 0
	for root, dirs, files in os.walk(path_storage):
		directoryname = re.split(r'\\|//|/', root)[-1]
		for file in files:
			if not re.search(directoryname, file):
				isnot +=1
				renamefile = file.replace(extension,'') + f'_{directoryname}{extension}'
				dst = os.path.join(root,renamefile)
				src = os.path.join(root,file)
				os.rename(src,dst)
			else:
				is_ += 1
	print(f'{"rename":10}|{is_} fichier(s) {extension} ont été renommés, {isnot} fichier(s) {extension} contiennent déjà le nom du dossier parent\n')

def get_or_set_local_storage(project, **kwargs):

	headers = headers = {'Authorization': f'Token {API_KEY}'}
	id_ = str(project.get_params()["id"])
	params = (('project', id_),)	
	response = requests.get(f'{URL}/api/storages/localfiles/', headers=headers, params=params)

	list_storages = []
	if response.status_code == 200:
		list_storages = response.json()
	
	for obj in list_storages:
		if obj['path'] == kwargs['local_store_path']:
			print(f"{'[GET]':10}|<{obj['path']}>\n{'':10}|crée le {parser.parse(obj['created_at']).strftime('%d/%m/%Y %H:%M')}\n")
			return obj
	else:
 		storage = project.connect_local_import_storage(**kwargs)
 		print(f"{'[POST]':10}|ajoute le localstorage <{kwargs['local_store_path']}>")
 		return storage
			
def sync_local_storage(client, storage):
	id_ = storage['id']
	type_ = storage['type']
	files = len([image for root, dirs, file  in os.walk(storage['path']) for image in file])
	last_sync = f'scan précédent le {parser.parse(storage["last_sync"]).strftime("%d/%m/%Y %H:%M")}' if storage['last_sync'] else ''

	print(f"{'[SYNC]':10}|{storage['path']}\n{'files':10}|{files} fichiers présent dans le {type_}\n{'scan..':10}|{last_sync}")
	sync =  client.sync_storage(type_, id_)
	print(f"{'add':10}|{sync['last_sync_count']} fichiers\n")

regex_out = r'(.*)full'
def add_annotation_from_extern(project,external_source,regex_out):

	def regexcompiler(str, regex):
		return re.findall(regex, str)[0]

	list_tasks = project.tasks
	ext_file = open(external_source, 'r', encoding='utf8')
	ext_annot = json.load(ext_file)
	ext_id_annotation = [(regexcompiler(unquote(obj['data']['image']).split('\\')[-1].replace('$',''),regex_out), obj['annotations'][0]["result"]) for obj in ext_annot]
	adding = 0
	for obj in list_tasks:
		decode = unquote(obj['data']['image']).split('\\')[-1].replace('$','')
		ark = regexcompiler(decode,r'(.*)full')
		for id_, result_ in ext_id_annotation:
			if (len(obj['annotations']) == 0) and (ark == id_):
				adding += 1
				print(f"{'[POST]':10}|annotation pour l'id: {obj['id']} ark: {ark}")
				project.create_annotation(task_id=obj['id'], result=result_)
	print(f"{'resume':10}|{adding} annotations ajoutées")
	
client = check_connection(URL, API_KEY)
project = get_or_set_project(client, title='gallicapix_sync_production')
storage = get_or_set_local_storage(project,local_store_path=path_storage)
# rename_files_from_tree(path_storage,'.jpg')
# sync_local_storage(client, storage)
add_annotation_from_extern(project, external_labelstudio, regex_out)
# # project.delete_tasks(task_ids=project.get_tasks_ids())











