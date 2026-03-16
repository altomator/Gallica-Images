import re
import os
import csv
import json
import aiohttp
import asyncio
import logging
import datetime
from oai import OAINUM
from pprint import pprint
from aiohttp import ClientSession
from collections import namedtuple
from aiolimiter import AsyncLimiter  # pip install aiolimiter
from tqdm.asyncio import tqdm_asyncio, trange
from collections import defaultdict, namedtuple
from typing import Union, Tuple, List, TextIO,NamedTuple
from tools import dumpsFile, set_event_loop_policy, logging_stdout, logging_files


class Document:

	leaky_bucket = {
	'concurrents_img':50,
	'seconds_img':60,
	'client_timeout': 60,
	'get_img_timeout':60,
	'get_manifest_timeout':60,
	'chunksize': 1024,
	}

	params_dft = {
	'name': datetime.datetime.now().strftime("%Y%m%d%H%M"),
	'image': False,
	'region': 'full',
	'size': 'full',
	'rotation':'0',
	'quality':'native',
	'extension': 'jpg'
	}

	def __init__(self, ark):
		self.ark = ark
		self._metadata = None
		self._images = None


	@property
	def metadata(self):
		if self._metadata is None:
			self._metadata = OAINUM('http://oai.bnf.fr/oai2/OAIHandler').getRecord(self.ark)
		return self._metadata

	async def fetch_manifest(self,session:ClientSession,url:str)->dict:
		async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.leaky_bucket['get_manifest_timeout'])) as result:
			return await result.json()

	@property
	@set_event_loop_policy
	async def images(self):
		async with aiohttp.ClientSession(timeout=self.leaky_bucket['get_img_timeout']) as session:
			manifest = await self.fetch_manifest(session, f"https://gallica.bnf.fr/iiif/ark:/12148/{self.ark}/manifest.json")
			canvases = manifest["sequences"][0]["canvases"]
			image = [image["images"][0]["resource"]["@id"] for image in canvases]
			self._images = image
			return self._images

	def setparams(self, params):
		document = namedtuple('Document', 'ark name image region size rotation quality extension')
		filter_empty = lambda d,keys: {k: v for k, v in d.items() if v and k in keys}
		check_length = lambda data: set([len(values) for values in data.values() if isinstance(values,list)])
		process_params = lambda row: filter_empty(row,params.keys())
		updated_default = lambda row: {**self.params_dft, **process_params(row)}
		data = updated_default(params)
		data['ark'] = self.ark
		if len(check_length(data)) in (0,1):
					return document(**data)
		else:
			raise ValueError(f'Lenght is not the same between list {list(check_length(data))}')

	async def download_img(self,session:ClientSession,img:NamedTuple,directory:str,logger:logging.Logger,rate_limit_img:AsyncLimiter)->None:
		if not os.path.exists(directory):
			os.makedirs(directory)
		async with rate_limit_img:
			try:
				async with session.get(img.url,timeout=aiohttp.ClientTimeout(total=self.leaky_bucket['get_img_timeout'])) as resp:
					with open(f'{os.path.join(directory,img.filename)}', 'wb') as image:
						async for chunk in resp.content.iter_chunked(self.leaky_bucket['chunksize']):
							image.write(chunk)
				return 200, img.filename
			except Exception as e:
				logger.error(f'#url#{img.url} $error${e}')
				return None, img.filename

	@set_event_loop_policy
	async def fetch_image(self,directory='./data/images/',params_img=None)->None:
		async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.leaky_bucket['client_timeout'])) as session:
			#{get the manifest and canvases}
			manifest = await self.fetch_manifest(session, f"https://gallica.bnf.fr/iiif/ark:/12148/{self.ark}/manifest.json")
			canvases = manifest["sequences"][0]["canvases"]

			if params_img == None:
				doc = self.setparams(self.params_dft)
			else:
				doc = self.setparams(params_img)

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

			#{create logger}
			logger = logging_files(os.path.join(directory,self.ark),f'{self.ark}-iiif')
			rate_limit_img = AsyncLimiter(self.leaky_bucket['concurrents_img'],self.leaky_bucket['seconds_img'])
			#{request each image}
			request = [self.download_img(session,doc,os.path.join(directory,self.ark),logger=logger,rate_limit_img=rate_limit_img) for doc in IMG_LIST]
			response = await tqdm_asyncio.gather(*request)

			#{delete image if exception or problem occurs}
			error_files = [os.path.join(directory,x[1]) for x in filter(lambda x: x[0] == None, response)]
			list(os.remove(path) for path in error_files if os.path.exists(path))
