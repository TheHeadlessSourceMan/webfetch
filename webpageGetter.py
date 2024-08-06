"""
Abstract class that gets a "Website" from a "Bookmark"
"""
import typing
from abc import abstractmethod
import datetime
from paths import UrlCompatible


class WebpageGetter:
    """
    Tool to get webpages
    """
    def __init__(self):
        pass

    @abstractmethod
    def get(self,
        url:UrlCompatible,
        date:typing.Optional[datetime.datetime]=None):
        """
        Derived classes must override this.
        """
        raise NotImplementedError()

    def __getattr__(self,url:UrlCompatible):
        """
        Interesting feature:  You can say WebpageGetter[url] to get a webpage!
        """
        return self.get(url)
