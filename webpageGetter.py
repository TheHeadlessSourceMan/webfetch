"""
Abstract class that gets a "Website" from a "Bookmark"
"""
import typing
import datetime
from paths import UrlCompatible


class WebpageGetter:
    """
    generally something that gets webpages
    """
    def __init__(self):
        pass

    def get(self,
        url:UrlCompatible,
        date:typing.Optional[datetime.datetime]=None):
        """
        Derived classes must override this.
        """
        _=url,date
        raise NotImplementedError()

    def __getattr__(self,url:UrlCompatible):
        """
        Interesting feature:  You can say WebpageGetter[url] to get a webpage!
        """
        return self.get(url)
