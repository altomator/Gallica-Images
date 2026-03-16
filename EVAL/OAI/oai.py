import asyncio
import json
import os
from tqdm import tqdm
from functools import partial
from queue import Queue, Empty
from oaipmh.client import Client
from tools import dumpsFile, logging_files
from concurrent.futures.thread import ThreadPoolExecutor
from oaipmh.metadata import MetadataRegistry, MetadataReader
from oaipmh.common import Header, Metadata
from typing import Union, Tuple, List
import inspect



class OAINUM:

	_oai_dc_reader = MetadataReader(
    fields={
    'title':       ('textList', 'oai_dc:dc/dc:title/text()'),
    'creator':     ('textList', 'oai_dc:dc/dc:creator/text()'),
    'subject':     ('textList', 'oai_dc:dc/dc:subject/text()'),
    'description': ('textList', 'oai_dc:dc/dc:description/text()'),
    'publisher':   ('textList', 'oai_dc:dc/dc:publisher/text()'),
    'contributor': ('textList', 'oai_dc:dc/dc:contributor/text()'),
    'relation':    ('textList', 'oai_dc:dc/dc:relation/text()'),
    'coverage':    ('textList', 'oai_dc:dc/dc:coverage/text()'),
    'identifier':  ('textList', 'oai_dc:dc/dc:identifier/text()'),
    'rights':      ('textList', 'oai_dc:dc/dc:rights[@xml:lang="fre"]/text()'),
    'type':        ('textList', 'oai_dc:dc/dc:type[@xml:lang="fre"]/text()'),
    'language':    ('textList', 'oai_dc:dc/dc:language/text()'),
    'date':        ('textList', 'oai_dc:dc/dc:date/text()'),
    'format':      ('textList', 'oai_dc:dc/dc:format/text()'),
    'source':      ('textList', 'oai_dc:dc/dc:source/text()'),},
    namespaces={
    'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
    'dc' : 'http://purl.org/dc/elements/1.1/'}
    )
	_tel_ap_reader = MetadataReader(
    fields={
    'identifier': ('textList', 'telap:record/tel:fullText/text()'),
    'title': ('textList', 'telap:record/dc:title/text()'),
    'alternative'
    'contributor': ('textList', 'telap:record/dc:contributor/text()'),
    'subject': ('textList', 'telap:record/dc:subject/text()'),
    'description': ('textList', 'telap:record/dc:description/text()'),
    'typeOfResource': ('textList', 'telap:record/mods:typeOfResource/text()'),
    'type': ('textList', 'telap:record/dc:type/text()'),
    'extent': ('textList', 'telap:record/dcterms:extent/text()'),
    'bibliographicCitation': ('textList', 'telap:record/dcterms:bibliographicCitation/text()'),
    'date': ('textList', 'telap:record/dc:date/text()'),
    'format': ('textList', 'telap:record/dc:format/text()'),
    'source': ('textList', 'telap:record/dc:source/text()'),
    'location': ('textList', 'telap:record/mods:location/text()'),
    'isFormatOf': ('textList', 'telap:record/dcterms:isFormatOf/text()'),
    'seeOnline': ('textList', 'telap:record/tel:seeOnline/text()'),
    'fullText': ('textList', 'telap:record/tel:fullText/text()'),

    },
    namespaces={
    'telap':'http://catalogue.bnf.fr/namespaces/TEL_ApplicationProfile',
    'dc' : 'http://purl.org/dc/elements/1.1/',
    'mods': 'http://www.loc.gov/mods',
    'dcterms': 'http://purl.org/dc/terms/',
    'tel': 'http://krait.kb.nl/coop/tel/handbook/telterms.html'}
    )

	def __init__(self, URL:str,directory='./data/'):
		self.URL = URL
		self.directory = directory

	def _client(self,metadata:Union[str,dict])->Tuple[str,Client]:
		"""
		Parameters
		----------
		metadata : str or dict
		If string must be 'oai_dc' or 'tel_ap' private attribute of the class.
		If dict must have 'fields', 'namespace', 'prefix' and respect the MetadataReader format eg:

		parser = {
			'fields':{
				'title': ('textList', 'oai_dc:dc/dc:title/text()')},
			'namespaces': {
				'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
				'dc' : 'http://purl.org/dc/elements/1.1/'},
			'prefix': 'oai_dc'
		}

		.. https://github.com/infrae/pyoai/blob/master/src/oaipmh/metadata.py
		Returns
		-------
		tuple
		Tuple with the prefix for MetadaFormat request and Client
		.. _infra/pyoai, https://github.com/infrae/pyoai

		"""
		registry = MetadataRegistry()

		if isinstance(metadata,str):
			if metadata == 'oai_dc':
				reader = self._oai_dc_reader
			if metadata == 'tel_ap':
				reader = self._tel_ap_reader
			registry.registerReader(metadata, reader)
			return metadata, Client(self.URL, registry)

		if isinstance(metadata, dict):
			reader = MetadataReader(fields=metadata['fields'], namespaces=metadata['namespaces'])
			registry.registerReader(metadata['prefix'], reader)
			return metadata['prefix'], Client(self.URL, registry)

	def mappingRecords(self,records:Tuple[Header,Metadata,None],sets='')->Union[dict,None]:
		"""
		Parameters
		----------
		records: [oaipmh.common.Header,oaipmh.common.Metadata,None]
		List contains header, metadata, _ from oaipmh.commun module
		Returns
		-------
		tuple or None:
		Tuple contains dict if records is present inside the warehouse or None if records was deleted

		"""
		header, metada, test = records
		head = {
			'identifier': header.__dict__.get('_identifier'),
			'deleted': header.__dict__.get('_deleted'),
			'datestamp': header.__dict__.get('_datestamp').strftime("%Y-%m-%d"),
			'setspec': header.__dict__.get('_setspec')
		}
		if not head['deleted']:
			data = metada.getMap()
			return data
		else:
			logger = logging_files(self.directory,f'{sets.replace(":","_")}_OAINUM')
			logger.info(f"{head['identifier'].replace('oai:bnf.fr:gallica/','')} est suprimmé du dépôt {head['setspec']}")
			return None

	@property
	def listSets(self)->Tuple[list,list]:
		"""
		@property
		---------
		Returns
		-------
		tuple
		Return list of setspec and description

		"""
		prefix, client = self._client('oai_dc')
		setsatt = [set_[0] for set_ in client.listSets()]
		setsinfo = [set_[1]for set_ in client.listSets()]
		return setsatt, setsinfo

	def getRecord(self,ark:str,metadata:Union[str,dict]='oai_dc')->Union[dict,None]:
		"""
		Parameters
		----------
		ark: str
		identifiant of the resssource
		metadata: str or dict
		If string must be 'oai_dc' or 'tel_ap' private attribute of the class.
		If dict must have three keys 'fields', 'namespace', 'prefix' and respect the MetadataReader format eg:

		parser = {
		'fields':{
			'title': ('textList', 'oai_dc:dc/dc:title/text()')},
		'namespaces': {
			'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
			'dc' : 'http://purl.org/dc/elements/1.1/'},
		'prefix': 'oai_dc'
		}
		Returns
		-------
		tuple or None:
		Tuple contains dict if records is present inside the warehouse or None if records was deleted

		"""
		prefix, client = self._client(metadata)
		print("... harvesting the OAI repository for ark: ",ark)

		record = client.getRecord(identifier=f'oai:bnf.fr:gallica/ark:/12148/{ark}', metadataPrefix=prefix)
		return self.mappingRecords(record)

	def pullSets(self,*setsname,metadata:Union[str,dict]='oai_dc',mb=20)->None:
		"""
		Parameters
		----------
		setsname : str
		Must be contain in listSets[0] to be valide
		metadata : str or dict
		If string must be 'oai_dc' or 'tel_ap' private attribute of the class.
		If dict must have 'fields', 'namespace', 'prefix' and respect the MetadataReader format eg:
		directory: str
		Location for the .json files
		mb: int
		Max size for json file

		parser = {
			'fields':{
				'title': ('textList', 'oai_dc:dc/dc:title/text()')},
			'namespaces': {
				'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
				'dc' : 'http://purl.org/dc/elements/1.1/'},
			'prefix': 'oai_dc'
		}

		Returns
		-------
		tuple
		Tuple with the prefix for MetadaFormat request and Client
		.. _infra/pyoai, https://github.com/infrae/pyoai

		"""
		prefix, client = self._client(metadata)
		for sets in setsname:
			records = []
			dumpssets = dumpsFile(os.path.join(self.directory,sets.replace(':','_')), 'records',mb)
			for record in tqdm(client.listRecords(metadataPrefix=prefix, set=sets),total=None,desc=f'Collecting records {sets}',unit=' records '):
				records.append(self.mappingRecords(record,sets=sets))
				if len(records) > 1000:
					filtered_records = list(filter(lambda x: x is not None, records))
					with dumpssets:dumpssets.append(*filtered_records)
					records = []
			with dumpssets:dumpssets.append(*filtered_records)
