#########################################################
# Abstract class that gets a "Website" from a "Bookmark"
#
# Written by KC Eilander
#########################################################
import typing
import datetime
from paths import UrlCompatible


class WebpageGetter:
	def __init__(self):
		pass

	def get(self,url:UrlCompatible,date:typing.Optional[datetime.datetime]=None):
		"""
		Derived classes must override this.
		"""
		return None

	def __getattr__(self,url:UrlCompatible):
		"""
		Interesting feature:  You can say WebpageGetter[url] to get a webpage!
		"""
		return self.get(url)