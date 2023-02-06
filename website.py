class WebsiteAsset:
	def __init__(self,website):
		self.mimetype=None
		self.url=None
		self.fetchedDate=None
		self._data=None
		self.owner=website
		self.cacheDataInThisObject=True
	
	def getData(self):
		if self.cacheDataInThisObject:
			if not self._data:
				from datetime import datetime
				self.fetchedDate=datetime.now()
				self._data=self._getUrlData(self.url)
			return self._data
		elif self._data:
			self._data=None
			self.fetchedDate=None
		return self._getUrlData(self.url)
		
	def _getUrlData(self,url=None):
		"""
		Gets the data for a single url
		"""
		if url is None:
			url=self.url
	

class Website:
	"""
	Python bookmark manager class to represent an entire website.
	
	A "website" is very different from a "bookmark" in that 
	(even without going recursive). you'll probably wind up 
	saving the data returned from many url's (images, css, and soforth)
	based on a single bookmark url.
	"""
	def __init__(self,url,websitesObject=None):
		self.url=url
		self.recursive=False
		self.ignoreUrls=[]
		self.includeHtml=True
		self.includeImages=True
		self.includeStylesheet=True
		self.includeJavascript=False
		self.includeAudio=False
		self.includeVideo=False
		self.includeFlash=False
		self.username=None
		self.password=None
		self.requiresJavascript=False
		self.requiresFlash=False
		self.requiresCookies=False
		self.assets=[] # keeps temporary track of all the parts of this website
		self.lastBackup=None
		self.changeCheckInterval=0
		self._websitesObject=websitesObject
		
	def restore(self,date=None,fetchIfMissing=False,addIfFetched=False):
		"""
		same thing as get
		"""
		return self.get(date,fetchIfMissing,addIfFetched)
			
	def get(self,date=None,fetchIfMissing=False,addIfFetched=False):
		"""
		returns a dict of all url:data
		
		if there is no bound websites object, then this will try to 
		do a simple web lookup
		"""
		if self._websitesObject:
			return self._websitesObject.get(self,date,fetchIfMissing,addIfFetched)
		else:
			from .internet import Internet
			return Internet().get(self.url)
			
	def backup(self):
		"""
		Backs up all data for this website (if possible and if necessary)
		"""
		if self._websitesObject:
			return self._websitesObject.backup(self)