import asyncio
import re
import os
import csv
import aiohttp
import datetime
import logging
from pprint import pprint
from collections import namedtuple
from functools import partial
from aiohttp import ClientSession
from aiolimiter import AsyncLimiter
from tqdm.asyncio import tqdm_asyncio
from typing import Union, Tuple, List, TextIO, NamedTuple
from modules.tools import set_event_loop_policy, logging_stdout, logging_files, set_event_loop_policy



default_img = {
	'name': datetime.datetime.now().strftime("%Y%m%d%H%M"),
	'image': False,
	'region': 'full',
	'size': 'pct:50', 
	'rotation':'0',
	'quality':'native',
	'extension': 'jpg'
}

leaky_bucket_layer= {
	'concurrents_manifest':50,
	'seconds_manifest': 60,
	'concurrents_img':20,
	'seconds_img':60,
	'chunksize': 1024,
	'client_timeout': 60,
	'get_manifest_timeout':60,
	'get_img_timeout':60
}


async def reader(path: str, default_img: dict):
	document = namedtuple('Document', 'ark name image region size rotation quality extension')
	with open(path, 'r', encoding='utf-8') as file:
		reader = csv.DictReader(file, delimiter=',')
		filter_empty = lambda d,keys: {k: v for k, v in d.items() if v and k in keys}
		split_values = lambda d: {k: v.split('/') if isinstance(v, str) and '/' in v else v for k, v in d.items()}
		check_length = lambda data: set([len(values) for values in data.values() if isinstance(values,list)])
		process_row = lambda row: split_values(filter_empty(row,default_img.keys()))
		updated_default = lambda row: {**default_img, **process_row(row)} 

		for index,row in enumerate(reader,start=1):
			for keys in row.keys():
				if keys == None:
					raise ValueError(f'Wrong formatted data line {index}, separator inside cell must be $')
			if row['ark']:
				data = updated_default(row)
				data['ark'] = row['ark'] 
				if len(check_length(data)) in (0,1) :
					yield document(**data)
				else:
					raise ValueError(f'Lenght is not the same between cell {list(check_length(data))} /{data["ark"]} line {index}')

async def fetch_img(session:ClientSession,img,directory,leaky_bucket_img,logger)->None:
		if not os.path.exists(directory):
			os.makedirs(directory)
		try:
			async with leaky_bucket_img:
				async with session.get(img.url,timeout=aiohttp.ClientTimeout(total=leaky_bucket_layer['get_img_timeout'])) as resp:
					with open(f'{os.path.join(directory,img.filename)}', 'wb') as image:
						async for chunk in resp.content.iter_chunked(leaky_bucket_layer['chunksize']):
							image.write(chunk)
				return 200, img.filename
		except Exception as e:
			logger.error(f'#url#{img.url} $error${e}')
			return None, img.filename

async def fetch_manifest(doc:NamedTuple,directory:str,leaky_bucket_layer:dict,logger:logging.Logger):

	leaky_bucket_manifest = AsyncLimiter(leaky_bucket_layer['concurrents_manifest'],leaky_bucket_layer['seconds_manifest'])
	leaky_bucket_img = AsyncLimiter(leaky_bucket_layer['concurrents_img'],leaky_bucket_layer['seconds_img'])
	url = f"https://gallica.bnf.fr/iiif/ark:/12148/{doc.ark}/manifest.json"
	async with leaky_bucket_manifest:
		async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=leaky_bucket_layer['client_timeout'])) as session:
			try:
				async with session.get(url,timeout=leaky_bucket_layer['get_manifest_timeout']) as result:
					
					manifest = await result.json()
					canvases = manifest["sequences"][0]["canvases"]
					fill = lambda x,i: x[i] if isinstance(x,list) else x
					switch = lambda x,i: i if x == False else x
					filename = lambda extension, *doc: '.'.join([ '-'.join(map(str, doc)),extension]).replace(':','#')
					IMG = namedtuple('Image', 'ark url filename')

					IMG_LIST = []
			
					if isinstance(doc.image,list):
						for i, image in enumerate(doc.image):
							url_img = f'https://gallica.bnf.fr/iiif/ark:/12148/{doc.ark}/{fill(doc.image,i)}/{fill(doc.region,i)}/{fill(doc.size,i)}/{fill(doc.rotation,i)}/{fill(doc.quality,i)}.{fill(doc.extension,i)}'
							filename_img = filename(fill(doc.extension,i),doc.ark,fill(doc.image,i),fill(doc.region,i),fill(doc.size,i),fill(doc.rotation,i),fill(doc.quality,i),fill(doc.name,i))
							IMG_LIST.append(IMG(doc.ark,url_img,filename_img))
					
					elif any(isinstance(x, list) for x in doc):
						size = list(set(map(lambda x: len(x), filter(lambda x: isinstance(x, list), doc))))
						for i in range(*size):
							for index, image in enumerate(canvases,start=1):
								url_img = f'https://gallica.bnf.fr/iiif/ark:/12148/{doc.ark}/{switch(fill(doc.image,i),f"f{index}")}/{fill(doc.region,i)}/{fill(doc.size,i)}/{fill(doc.rotation,i)}/{fill(doc.quality,i)}.{fill(doc.extension,i)}'
								filename_img = filename(fill(doc.extension,i),doc.ark,switch(fill(doc.image,i),f'f{index}'),fill(doc.region,i),fill(doc.size,i),fill(doc.rotation,i),fill(doc.quality,i),fill(doc.name,i))
								IMG_LIST.append(IMG(doc.ark,url_img,filename_img))	
					else:	
						for i, image in enumerate(canvases,start=1):	
							url_img = f'https://gallica.bnf.fr/iiif/ark:/12148/{doc.ark}/{switch(fill(doc.image,i),f"f{i}")}/{doc.region}/{doc.size}/{doc.rotation}/{doc.quality}.{doc.extension}'
							filename_img = filename(fill(doc.extension,image),doc.ark,switch(fill(doc.image,i),f"f{i}"),fill(doc.region,i),fill(doc.size,i),fill(doc.rotation,i),fill(doc.quality,i),fill(doc.name,i))
							IMG_LIST.append(IMG(doc.ark,url_img,filename_img))
					
				
					request = [fetch_img(session=session,img=img,
											directory=os.path.join(directory,img.ark),
											leaky_bucket_img=leaky_bucket_img,
											logger=logger) for img in IMG_LIST]

					response = await tqdm_asyncio.gather(*request)
					error_files = [os.path.join(directory,x[1]) for x in filter(lambda x: x[0] == None, response)]
					list(os.remove(path) for path in error_files if os.path.exists(path))
					success = [x[0] for x in filter(lambda x: x[0] == 200, response)]

			except Exception as e:
				logger.error(f'#url#{url} $error${e}')

async def workers(inQ:asyncio.Queue,directory:str,leaky_bucket_layer:dict,logger:logging.Logger):
	batch = []
	#{sink the queue}
	while not inQ.empty():
		batch.append(inQ.get_nowait())
		inQ.task_done()
	#{gather request}
	request = [fetch_manifest(doc,directory=directory,leaky_bucket_layer=leaky_bucket_layer,logger=logger) for doc in batch]
	response = await asyncio.gather(*request)

@set_event_loop_policy
async def collecting_images(path:str,default=default_img,directory='./data/images/',leaky_bucket_layer=leaky_bucket_layer):
	
	#[reader]
	row = reader(path=path,default_img=default_img)
	#[batch]
	inQ = asyncio.Queue(maxsize=leaky_bucket_layer['concurrents_manifest'])
	#[logger]
	logger = logging_files(directory,'-iiif-manifest')	

	#[pipeline]
	async for doc in row:
		try:
			inQ.put_nowait(doc)
		except asyncio.QueueFull:
			await workers(inQ,directory=directory,leaky_bucket_layer=leaky_bucket_layer,logger=logger)
			inQ.put_nowait(doc)
	await workers(inQ,leaky_bucket_layer=leaky_bucket_layer,directory=directory,logger=logger)

