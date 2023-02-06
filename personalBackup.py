#!/usr/bin/python
#########################################################
# WebpageGetter for restoring (and backing up) webpages
# to/from a personal database.  Picture like wget or httrack only
# with a yummy data-basey cream filling.
#
# Written by KC Eilander
#########################################################
import typing
import datetime
from paths import UrlCompatible,MimeType
from formats.plainhtml import PlainHtmlBookmarks
from .webpageGetter import WebpageGetter
from .website import Website
htmlTool=PlainHtmlBookmarks()


class PersonalBackup(WebpageGetter):
	"""
	WebpageGetter for restoring (and backing up) webpages
	to/from a personal database.  Picture like wget or httrack only
	with a yummy data-basey cream filling.
	"""
	def __init__(self,database=None):
		WebpageGetter.__init__(self)
		if database is None:
			database=()
		self.database=database
		self.fetcher=None

	def _getFetcher(self)->webfetch.WebFetch:
		if self.fetcher is None:
			from webFetch.WebFetch import WebFetch
			self.fetcher=WebFetch()
		return self.fetcher

	def _getResource(self,
		url:UrlCompatible,
		date:str='newest',
		fetchIfMissing:bool=False,
		addIfFetched:bool=False
		)->typing.Tuple[str,datetime.datetime,MimeType]:
		"""
		date can be an actual date, "oldest", or "newest" (newest is default).

		returns (data,date,mimetype)
		"""
		data=None #TODO: Get this from database
		if data is None and fetchIfMissing:
			data=self._webfetch(url)
			if data is not None and addIfFetched:
				self._saveResource(url,data)
		return (data,date,mimetype)

	def _saveResource(self,
		url:UrlCompatible,
		data:str,
		date:typing.Optional[datetime.datetime]=None
		)->None:
		"""
		Saves a single resource into a database
		"""
		if date is None:
			pass # date=Now
		#TODO: Save this to database
		pass

	def _webfetch(self,url:UrlCompatible)->typing.Tuple[str,MimeType]:
		"""
		returns (url,mime)
		"""
		data=[None] # this weirdness is to cheat the scope for the inner function
		mime=[None]
		f=self._getFetcher()
		#f.debug=99
		f.failoverOnGeneratedPages=False
		def onDone(url,html):
			data[0]=html
			mime[0]='text/html'
		f.enqueue(onDone,url)
		f.runNext()
		return (data[0],mime[0])

	def restore(self,
		website:Website,
		date:typing.Optional[datetime.datetime]=None,
		fetchIfMissing:bool=True
		)->None:
		""" """
		stuff=()
		urlsToFetch=[website.bookmark.url]
		while len(urlsToFetch) > 0:
			url=urlsToFetch[0]
			urlsToFetch=urlsToFetch[1:]
			if url in stuff: # already got it
				continue
			if url in website.ignoreUrls:
				continue
			saved=self._getResource(url,date,fetchIfMissing,addIfFetched)
			stuff[url]=saved[0]
			if saved[2]=='text/html':
				pass # TODO: left off here

	def get(self,
		url:UrlCompatible,
		date:typing.Optional[datetime.datetime]=None
		)->None:
		""" """
		return self.restore(url,date,False)

	def backup(self,website:Website)->None:
		"""
		Fetches a website and saves it to the database
		"""
		# This gets us in the ballpark, but usually the MIME type makes the decision
		audioExtensions=['mp3','wma','wav','mid','mod','acc','ra','ram']
		videoExtensions=['mpg','mpeg','mov','264','h264','mp4','wmv','avi']
		imageExtensions=['jpg','jpeg','jpe','gif','ico','bmp','png','svg']
		htmlExtensions=['htm','html','xhtml']
		htmlBuddyExtensions=['js','css']
		fetchedUrls=[]
		urlsToFetch=[website.bookmark.url]
		while len(urlsToFetch) > 0:
			url=urlsToFetch[0]
			urlsToFetch=urlsToFetch[1:]
			if url in fetchedUrls:
				continue
			if url in website.ignoreUrls:
				continue
			print('getting '+url+' ...')
			page,mime=self._webfetch(url)
			fetchedUrls.append(url)
			if page is None:
				print('ERR: retrieving page "'+url+'"... SKIPPED!')
				continue
			print('DONE!')
			if mime.startswith('image'):
				if website.saveImages:
					self._saveResource(link,page)
			elif mime=='text/html':
				basePath=url.split('&')[0].strip()
				basePath=basePath.rsplit('/',1)[0]
				if website.saveHtml:
					# save this page
					self._saveResource(url,page)
				if website.saveImages:
					# look at <img> tags
					for link in htmlTool.getImages(page,basePath=basePath):
						urlsToFetch.append(link)
				if website.saveFlash:
					# get all embedded flash objects
					for link in htmlTool.getEmbedded(page,'flash',basePath=basePath):
						urlsToFetch.append(link)
					# TODO: what about embedded video?
				# build a list of everything else
				links=[]
				for rel,link in htmlTool.getLinkRels(page,basePath=basePath):
					if website.saveImages or rel.find('icon')>=0:
						urlsToFetch.append(link)
					else:
						extension=link.split('&',1)[0].rsplit('/',1)[-1].rsplit('.',1)
						if extension in htmlBuddyExtensions:
							urlsToFetch.append(link)
				# grab all the links to see what they are
				for link in htmlTool.getLinks(page,basePath=basePath):
					save=True
					extension=str(link).split('&',1)[0].rsplit('/',1)[-1].rsplit('.',1)
					if len(extension)>1:
						extension=extension[-1]
						if website.saveVideo and extension in videoExtensions:
							urlsToFetch.append(link)
						if website.saveAudio and extension in audioExtensions:
							urlsToFetch.append(link)
						if website.saveImages and extension in imageExtensions:
							urlsToFetch.append(link)
						if website.recursive and extension in htmlExtensions:
							urlsToFetch.append(link)
						# TODO: what about links to youtube?
					elif website.recursive: # assume html
						urlsToFetch.append(link)

	def cmdline(self,argv:typing.Optional[typing.Iterable[str]]=None)->int:
		"""
		Call into this class like it's a command line.

		Don't forget that argv[0] is the calling app's name.
		(You can set it to "" if you want to.)

		if argv is unspecified, will get it from the app's
		command line.
		"""
		if argv is None:
			import sys
			argv=sys.argv
		affirmatives=['y','Y','t','T','1']
		printhelp=False
		outputpath='./'
		recursive=False
		ignoreUrls=[]
		saveHtml=True
		saveImages=True
		saveAudio=False
		saveVideo=False
		saveFlash=False
		username=None
		password=None
		requiresJavascript=False
		requiresFlash=False
		requiresCookies=False
		if len(argv)<2:
			printhelp=True
		else:
			for arg in argv[1:]:
				if arg[0]=='-':
					if arg[1]=='-':
						arg=arg[2:].split('=',1)
						if arg[0]=='backup':
							if len(arg)>1:
								url=arg[1]
								w=Website(Bookmark(url))
								w.recursive=recursive
								w.ignoreUrls=ignoreUrls
								w.saveHtml=saveHtml
								w.saveImages=saveImages
								w.saveAudio=saveAudio
								w.saveVideo=saveVideo
								w.saveFlash=saveFlash
								w.username=username
								w.password=password
								w.requiresJavascript=requiresJavascript
								w.requiresFlash=requiresFlash
								w.requiresCookies=requiresCookies
								self.backup(w)
							else:
								print("ERR: No url to back up!")
						elif arg[0]=='restore':
							if len(arg)>1:
								url=arg[1]
								w=Website(Bookmark(url))
								w.recursive=recursive
								w.ignoreUrls=ignoreUrls
								w.saveHtml=saveHtml
								w.saveImages=saveImages
								w.saveAudio=saveAudio
								w.saveVideo=saveVideo
								w.saveFlash=saveFlash
								w.username=username
								w.password=password
								w.requiresJavascript=requiresJavascript
								w.requiresFlash=requiresFlash
								w.requiresCookies=requiresCookies
								stuff=self.restore(w)
								for url,data in list(stuff.items()):
									f=open(outputpath+url,'wb')
									f.write(data)
									f.close()
							else:
								print("ERR: No url to restore!")
						elif arg[0]=='outputpath':
							if len(arg)>1:
								outputpath=arg[1]
							else:
								print("ERR: No path!")
						elif arg[0]=='recursive':
							if len(arg)>1:
								recursive=(arg[1][0] in affirmatives)
							else:
								recursive=True
						elif arg[0]=='ignoreUrls':
							if len(arg)>1:
								ignoreUrls.append(arg[1])
						elif arg[0]=='saveHtml':
							if len(arg)>1:
								saveHtml=(arg[1][0] in affirmatives)
							else:
								saveHtml=True
						elif arg[0]=='saveImages':
							if len(arg)>1:
								saveImages=(arg[1][0] in affirmatives)
							else:
								saveImages=True
						elif arg[0]=='saveAudio':
							if len(arg)>1:
								saveAudio=(arg[1][0] in affirmatives)
							else:
								saveAudio=False
						elif arg[0]=='saveVideo':
							if len(arg)>1:
								saveVideo=(arg[1][0] in affirmatives)
							else:
								saveVideo=False
						elif arg[0]=='saveFlash':
							if len(arg)>1:
								saveFlash=(arg[1][0] in affirmatives)
							else:
								saveFlash=False
						elif arg[0]=='username':
							if len(arg)>1:
								username=arg[1]
							else:
								print("ERR: No username!")
						elif arg[0]=='password':
							if len(arg)>1:
								password=arg[1]
							else:
								print("ERR: No password!")
						elif arg[0]=='requiresJavascript':
							if len(arg)>1:
								requiresJavascript=(arg[1][0] in affirmatives)
							else:
								requiresJavascript=False
						elif arg[0]=='requiresFlash':
							if len(arg)>1:
								requiresFlash=(arg[1][0] in affirmatives)
							else:
								requiresFlash=False
						elif arg[0]=='requiresCookies':
							if len(arg)>1:
								requiresCookies=(arg[1][0] in affirmatives)
							else:
								requiresCookies=False
						elif arg[0]=='help':
							printhelp=True
							break
						else:
							print('ERR: Unknown arg "--'+arg[0]+'"')
							printhelp=True
							break
					else:
						print('ERR: Unknown arg "'+arg+'"')
						printhelp=True
						break
				else:
					self.load(arg,formatName=nextFormat)
					nextFormat=None
		if printhelp:
			if len(argv)<1 or argv[0] is None or argv[0]=='':
				programName='python bookbackup.py'
			else:
				programName=argv[0].strip()
			print('ABOUT:\n\tA tool for backing up webpages to a database.  Picture like wget or httrack only')
			print('\tdelicious with data-basey cream filling.')
			print('USAGE:\n\t'+programName+' [settings] [commands]')
			print('\t(these items are processed immediately and in order from left to right)')
			print('SETTINGS:')
			print('\t--outputpath=dir .......... where to restore the url(s) to')
			print('\t--recursive[=true|false] .. recursively download the site')
			print('\t--ignore=url .............. used to help recursive from running amok (can have more than one)')
			print('\t--saveHtml[=true|false] ... save html files')
			print('\t--saveImages[=true|false] . save image files')
			print('\t--saveAudio[=true|false] .. save audio files')
			print('\t--saveVideo[=true|false] .. save video files')
			print('\t--saveFlash[=true|false] .. save flash files')
			print('\t--username=name ........... name used to log into this site')
			print('\t--password=pwd ............ password used to log into this site')
			print('\t--requiresJavascript[=true|false] . if this action requires javascript')
			print('\t--requiresFlash[=true|false] ...... if this action requires flash')
			print('\t--requiresCookies[=true|false] .... if this action requires cookies')
			print('COMMANDS:')
			print('\t--backup=url ............. backup the link')
			print('\t--restore=url ............ restore the link to the ouput path')
			print('\t--help ................... print this help')


if __name__ == '__main__':
	PersonalBackup().cmdline()