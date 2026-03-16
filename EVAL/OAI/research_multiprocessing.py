
import os 
import re
import io
import json
import pathlib
import asyncio
import csv
import random
from tqdm import tqdm
import uuid
import tempfile, shutil
import concurrent.futures
from pprint import pprint
from itertools import chain
from datetime import datetime
from functools import partial
from modules.tools import logging_files, set_event_loop_policy
from contextlib import ExitStack
from typing import Callable, Union
from collections import defaultdict
from tqdm.asyncio import tqdm_asyncio
from fnmatch import fnmatch, fnmatchcase



def stackfiles_from_directory(directory,authority,chunksize):

	pathfinder = lambda directory: [os.path.join(dirpath,file) for dirpath,_,files in os.walk(directory) 
							for file in files if fnmatch(file,f'*.json')]
	jsonpath = pathfinder(directory)
	random.shuffle(jsonpath)
	for i in range(0,len(jsonpath), chunksize):
		yield jsonpath[i:i + chunksize], authority

def retrieve_words_from_fields(obj,authority):
	
	keys = [key for key in authority.keys()]
	
	only_string = lambda obj: {k:((' ').join(v) if isinstance(v,list) else v)for k, v in obj.items()}
	ark = lambda id_: id_[0].split('/')[-1]
	generators_tuples = lambda obj: ([k,v] for k,v in obj.items())

	compiler = lambda words: re.compile(r'(' + ('|').join(words) + r')',re.IGNORECASE)
	keys_compiler = lambda keys,compiler,authority: {k:compiler([regex for regex in authority[k]]) for k in keys}
	
	ark_ = ark(obj['identifier'])
	g_tuples = generators_tuples(only_string(obj))
	k_compiler = keys_compiler(keys,compiler,authority)

	merge = lambda match: ';'.join(list(set(*[match])))

	process = lambda ark,generators_tuples,keys_pattern: ((ark,k,merge(pattern.findall(tuples[1])),tuples[0]) 
															for tuples in generators_tuples 
															for k, pattern in keys_pattern.items())


	filter_empty_match = lambda process: filter(lambda x: x[2],process)
	word_from_fields = (filter_empty_match(process(ark_,g_tuples,k_compiler)))

	yield from word_from_fields

def dump_in_csv(batch, dirtemp):
	filename = str(uuid.uuid4())
	with open(f'{os.path.join(dirtemp,filename)}.csv','a',newline='',encoding='utf-8') as csvfile:
		writer = csv.writer(csvfile,delimiter='|')
		writer.writerows(batch)
	
def mapping_from_fields(stacks,dirtemp,logger):

	files, authority = stacks
	exceptions = 0
	batch = []
	records = 0
	matchs = 0

	with ExitStack() as context:
		path_context = [context.enter_context(open(file,'r',encoding='utf-8')) for file in files]
		readers = map(lambda f: (f,f.name),path_context)

		for f, filename in readers:
			try:
				content = json.load(f)
			except Exception as e:
				exceptions += 1
				logger.error(f'#file#{filename} $error${e}')
			for obj in content['data']:
				records +=1
				for match in retrieve_words_from_fields(obj=obj,authority=authority):
					matchs +=1
					batch.append(match)
					if len(batch) >= 200_000:
						dump_in_csv(batch=batch,dirtemp=dirtemp)
						batch = []
		if batch:dump_in_csv(batch=batch,dirtemp=dirtemp)
	return records, matchs, exceptions

@set_event_loop_policy
async def mapping2csv(directory,chunksize,authority,write_at):

	logger = logging_files(write_at, 'MAPPING')
	filename_csv = 'CSV' + datetime.now().strftime("_%H-%M-%S-%m-%d-%Y") +'.csv'
	stackfiles = stackfiles_from_directory(directory=directory,authority=authority,chunksize=chunksize)
	loop = asyncio.get_running_loop()

	path_temp = './temp/'
	if not os.path.exists(path_temp):os.makedirs(path_temp)

	with tempfile.TemporaryDirectory(dir='./temp/') as dirtemp:
		with concurrent.futures.ProcessPoolExecutor() as pool:
			tasks = [loop.run_in_executor(pool,partial(mapping_from_fields,stacks,dirtemp,logger)) for stacks in stackfiles]
			results_from_process = await tqdm_asyncio.gather(*tasks)		

			records_sum = lambda results : sum(map(lambda x: x[0], results))
			records_mean = lambda results : sum(map(lambda x: x[0], results)) / len(results)
			match_sum = lambda results : sum(map(lambda x: x[1], results)) 
			errors_sum = lambda results : sum(map(lambda x: x[2], results)) 

		#[WRITING FINAL CSV]
		path_csv_files = list(map(lambda file: os.path.join(dirtemp, file), 
						filter(lambda file: file.endswith('.csv'), os.listdir(dirtemp))))

		if not os.path.exists(write_at):os.makedirs(write_at)

		with open(f'{os.path.join(write_at,filename_csv)}','a',newline='',encoding='utf-8') as fcsv:
			header = ('ark','group','match','from')
			writer = csv.DictWriter(fcsv,fieldnames=header,delimiter='|')
			writer.writeheader()

			with ExitStack() as stack:
				path_context = [stack.enter_context(open(path_csv,'r',encoding='utf-8')) for path_csv in path_csv_files]	
				readers = map(lambda file: (csv.reader(file, delimiter='|'),file.name),path_context)
				row_counter = 0
				for content,filename in tqdm(readers, total=len(path_context), desc=f'Reading files',unit='CSVTEMP'):
					for row in content:
						row_counter += 1
						writer.writerow(dict(zip(header,row)))

	print(f'{row_counter:,} rows for {round(os.path.getsize(os.path.join(write_at,filename_csv))/(1024 * 1024),2):,.2f}mb for the CSV')
	print(f'{records_sum(results_from_process):,} records read for a mean of {records_mean(results_from_process):,.2f} by process for {os.cpu_count()} process by default')
	print(f'{errors_sum(results_from_process):,} file(s) error(s) during the process')