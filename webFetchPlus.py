#########################################################
# An extended webFetch that can do cool tricks like:
#	* all the webFetch stuff like being able to download with an actual browser
#	* download/use local backup of website
#	* load all images / media / whatever that a site contains
#	* look for backed up copies of a missing website using online archives
#	* do recursive downloading (like httrack or wget, only with more features)
# And eventually:
#	* interface with your regular web browser cache
#	* download a site regularly and notify you of changes
#	* go through several steps (e.g. login forms) to get the data
#
# Also works with my pybook bookmark manager to keep backups of the bookmarked
# sites you want to be sure never to lose!
#
# Written by KC Eilander
#########################################################
import typing
import datetime
from paths import UrlCompatible
from .website import Website
from .personalBackup import PersonalBackup


class WebFetchPlus:
	"""
	Manages the loading/saving of all websites
	"""
	def __init__(self,
		personalBackups:typing.Union[None,str,PersonalBackup,typing.Iterable[PersonalBackup]]=None,
		useOnlineBackupServices:typing.Union[bool,str]=True):
		"""
		personalBackups can be PersonalBackup object, string database name, or any array thereof
		useOnlineBackupServices can be True,False, or an xml filename to the list of backup services to use
		"""
		self._personalBackups=[]
		self._webpageGetters=[]
		# add all personalBackups
		if type(personalBackups)!=list:
			personalBackups=[]
		for pb in personalBackups:
			if type(pb)==str:
				# create a PersonalBackup object from the given database
				from .personalBackup import PersonalBackup
				pb=PersonalBackup(pb)
			self._personalBackups.append(pb)
		# add all webpageGetters
		for pb in self._personalBackups: # first check the personal backup system(s)
			self._webpageGetters.append(pb)
		from .internet import Internet
		i=Internet()
		self._webpageGetters.append(i)
		if useOnlineBackupServices is not None and useOnlineBackupServices!=False:
			if useOnlineBackupServices==True:
				useOnlineBackupServices="OnlineBackupServices.xml"
			from .onlineBackupServices import OnlineBackupServices
			if useOnlineBackupServices:
				obs=OnlineBackupServices()
				self._webpageGetters.append(obs)

	def restore(self,
		websites:typing.Union[UrlCompatible,typing.Iterable[UrlCompatible]],
		date:typing.Optional[datetime.datetime]=None,
		fetchIfMissing:bool=False,
		addIfFetched:bool=False
		)->Website:
		"""
		same thing as get
		"""
		return self.get(websites,date,fetchIfMissing,addIfFetched)

	def backup(self,website:Website)->None:
		for pb in self._personalBackups:
			pb.backup(website)

	def get(self,
		websites:typing.Union[UrlCompatible,typing.Iterable[UrlCompatible]],
		date:typing.Optional[datetime.datetime]=None,
		fetchIfMissing:bool=False,
		addIfFetched:bool=False
		)->Website:
		"""
		fetches all data for a website

		if websites is a url, will autocreate a website object for fetching a single
		html page with images and css only.  The new object will be returned.

		websites can also be an array, just to make it so you don't have to loop externally
		"""
		if type(websites)==list:
			results=[]
			for website in websites:
				results.append(self.get(website,date,fetchIfMissing,addIfFetched))
			return results
		if type(websites)==str:
			createdInternally=True
			websites=Website(websites)
		else:
			createdInternally=False
		if fetchIfMissing:
			for wg in self._webpageGetters:
				data=wg.get(websites,date)
				if data is not None:
					if addIfFetched and wg not in self._personalBackups:
						self.backup(websites)
					break
		else:
			for pb in self._personalBackups:
				data=pb.get(websites,date)
				if data is not None:
					break
		return websites

	def getImages(self,
		websites:typing.Union[UrlCompatible,typing.Iterable[UrlCompatible]],
		date:typing.Optional[datetime.datetime]=None,
		fetchIfMissing:bool=False,
		addIfFetched:bool=False
		)->Website:
		"""
		a shortcut for fetching all images and only images for a given website

		if websites is a url then it will just fetch the images from there, otherwise if
		it is a websites object, it will extract the url from that and create a new website
		object (leaving the original intact)

		websites can also be an array, just to make it so you don't have to loop externally
		"""
		if type(websites)==list:
			results=[]
			for website in websites:
				results.append(self.getImages(website,date,fetchIfMissing,addIfFetched))
			return results
		if type(websites)!=str:
			website=Website(websites.url)
		else:
			website=Website(websites)
		website.includeHtml=False
		website.includeImages=True
		website.includeStylesheet=False
		website.includeJavascript=False
		website.includeAudio=False
		website.includeVideo=False
		website.includeFlash=False
		return self.get(website,date,fetchIfMissing,addIfFetched)

	def getAudio(self,
		websites:typing.Union[UrlCompatible,typing.Iterable[UrlCompatible]],
		date:typing.Optional[datetime.datetime]=None,
		fetchIfMissing:bool=False,
		addIfFetched:bool=False
		)->Website:
		"""
		a shortcut for fetching all audio and only audio for a given website

		if websites is a url then it will just fetch the audio from there, otherwise if
		it is a websites object, it will extract the url from that and create a new website
		object (leaving the original intact)

		websites can also be an array, just to make it so you don't have to loop externally
		"""
		if type(websites)==list:
			results=[]
			for website in websites:
				results.append(self.getAudio(website,date,fetchIfMissing,addIfFetched))
			return results
		if type(websites)!=str:
			website=Website(websites.url)
		else:
			website=Website(websites)
		website.includeHtml=False
		website.includeImages=False
		website.includeStylesheet=False
		website.includeJavascript=False
		website.includeAudio=True
		website.includeVideo=False
		website.includeFlash=False
		return self.get(website,date,fetchIfMissing,addIfFetched)

	def getHtmlOnly(self,
		websites:typing.Union[UrlCompatible,typing.Iterable[UrlCompatible]],
		date:typing.Optional[datetime.datetime]=None,
		fetchIfMissing:bool=False,
		addIfFetched:bool=False
		)->Website:
		"""
		a shortcut for fetching all html and only html for a given website

		if websites is a url then it will just fetch the html from there, otherwise if
		it is a websites object, it will extract the url from that and create a new website
		object (leaving the original intact)

		websites can also be an array, just to make it so you don't have to loop externally
		"""
		if type(websites)==list:
			results=[]
			for website in websites:
				results.append(self.getHtmlOnly(website,date,fetchIfMissing,addIfFetched))
			return results
		if type(websites)!=str:
			website=Website(websites.url)
		else:
			website=Website(websites)
		website.includeHtml=True
		website.includeImages=False
		website.includeStylesheet=False
		website.includeJavascript=False
		website.includeAudio=False
		website.includeVideo=False
		website.includeFlash=False
		return self.get(website,date,fetchIfMissing,addIfFetched)
