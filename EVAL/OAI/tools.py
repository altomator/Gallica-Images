import os
import re
import json
import typing
import logging
import asyncio
import aiohttp
import datetime
from pathlib import Path
from pprint import pprint
from itertools import islice
from typing import NamedTuple
from aiohttp import ClientSession
from collections import namedtuple
from aiolimiter import AsyncLimiter
from tqdm.asyncio import tqdm_asyncio, trange
from collections import defaultdict, namedtuple

# bug potentiel
# OSError: [Errno 24] Too many open files
# ulimit -Sn 10000
# ulimit -a

class dumpsFile:
	_batch = 1
	_filesize = 0

	def __init__(self, root,filename,mb=20):
		self.root = root
		self.filename = filename
		self.mb = mb
		self.datestamp = datetime.datetime.now().strftime("%H-%M-%S-%m-%d-%Y")
		self.directory = self.mkdir()
		self._file = self.touch()
		self._firstrecord = True

	def mkdir(self):
		path = os.path.join(self.root,self.datestamp)
		if not os.path.exists(path):
			os.makedirs(path)
		return path

	def touch(self):
		filename = f'{self.filename}_{str(self._batch)}$batch_{self.mb}$mb.json'
		path = os.path.join(self.directory,filename)
		touch = open(path,'a+',encoding='utf-8')
		return touch

	def closing(self):
		self._file.seek(0, 2)
		self._file.write(']}')


	def ensure_size(self, record):
		self._filesize += len(json.dumps(record).encode('utf-8'))
		if self._filesize > self.mb * 1024 * 1024:
			print(" batch: ",self._batch)
			self._batch += 1
			self._filesize = 0
			self._firstrecord = True
			self.closing()
			self._file.close()
			self._file = self.touch()

	def append(self,*records):
		try:
			for record in records:
				self.ensure_size(record)
				if not self._firstrecord:
					self._file.write(',\n')
				else:
					self._file.write('{"data":[')
					self._firstrecord = False
				json.dump(record,self._file,ensure_ascii=False)
		except KeyboardInterrupt:
			self.closing()
			raise

	def __enter__(self):
		return self._file

	def __exit__(self,exc_type, exc_val, exc_tb):
		self.closing()


def logging_files(directory, filename):
	dt = datetime.datetime.now().strftime("-%m-%d-%Y")
	filename = filename + dt
	absolute = os.path.join(directory, filename)

	if not os.path.exists(directory):
			os.makedirs(directory)

	logger = logging.getLogger(filename)
	logger.setLevel(logging.DEBUG)
	formatter = logging.Formatter('[%(asctime)s] - %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
	file_handler = logging.FileHandler(f'{absolute}.log', mode='a')
	file_handler.setLevel(logging.DEBUG)
	file_handler.setFormatter(formatter)
	logger.addHandler(file_handler)

	return logger

def logging_stdout():
	logging.basicConfig(level=logging.INFO, format='[%(asctime)s] (%(levelname)s) | %(message)s', datefmt='%Y-%M-%d %H:%m:%S')
	logger = logging.getLogger()
	return logger

def set_event_loop_policy(func):
    def wrapper(*args, **kwargs):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        return asyncio.run(func(*args, **kwargs))
    return wrapper

class MappingLabelStudio:

	leaky_bucket = {
	'concurrents_img':50,
	'seconds_img':60,
	'client_timeout': 60,
	'get_img_timeout':60,
	'chunksize': 1024,
	}

	def __init__(self,dataset):
		self.dataset = dataset

	@property
	def mapping(self):
		with open(self.dataset,'r', encoding='utf-8') as f:

			dataset = json.load(f)
			mapping = defaultdict(lambda: defaultdict(list))
			image = namedtuple('image','uuid width height result ')
			for obj in dataset['images']:
				mapping[obj['id']] = {
					'url': obj['iiif'],
					'width': obj['width'],
					'height': obj['height']
				}

			for obj in dataset['annotations']:
				mapping[obj['id']]['result'] = obj['result']

			return mapping

	def get_url_from_log(self,log):
		regex = re.compile(r'#url#(.*)\s\$')
		url = []
		with open(log,'r') as log:
			for line in log:
				url.append(regex.findall(line)[0])
			return url

	async def download_img(self,session:ClientSession,img:NamedTuple,directory:str,logger:logging.Logger,rate_limit_img:AsyncLimiter)->None:
		if not os.path.exists(directory):
			os.makedirs(directory)
		file = img.filename + img.extension
		async with rate_limit_img:
			try:
				async with session.get(img.url,timeout=aiohttp.ClientTimeout(total=self.leaky_bucket['get_img_timeout'])) as resp:
					with open(f'{os.path.join(directory,file)}', 'wb') as image:
						async for chunk in resp.content.iter_chunked(self.leaky_bucket['chunksize']):
							image.write(chunk)
				return 200, file
			except Exception as e:
				logger.error(f'#url#{img.url} $error${e}')
				return None, file

	@set_event_loop_policy
	async def fetch_images(self,log=None):

		mapping = self.mapping

		dt = datetime.datetime.now().strftime("%Y%m%d%H%M")
		directory = Path(self.dataset).parent.absolute()
		directory_img = os.path.join(Path(self.dataset).parent.absolute(),f'IMG-{dt}')

		image = namedtuple('Image', 'filename extension url')
		extension = lambda string: '.' + string.split('/')[-1].split('.')[-1]
		filter_log = lambda iterable, log: [nt for nt in iterable if nt.url in log]
		images_list = [image(keys,extension(values['url']),values['url']) for keys, values in mapping.items()]

		if isinstance(log,str):
			url_log = self.get_url_from_log(log)
			images_list = filter_log(images_list,url_log)

		rate_limit_img = AsyncLimiter(self.leaky_bucket['concurrents_img'],self.leaky_bucket['seconds_img'])
		logger = logging_files(os.path.join(directory),f'IIIF')

		async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.leaky_bucket['client_timeout'])) as session:
			request = [self.download_img(session,img=img,directory=directory_img,logger=logger,rate_limit_img=rate_limit_img) for img in images_list]
			response = await tqdm_asyncio.gather(*request)
			error_files = [os.path.join(directory_img,x[1]) for x in filter(lambda x: x[0] == None, response)]
			list(os.remove(path) for path in error_files if os.path.exists(path))
