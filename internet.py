#!/usr/bin/python
"""
A webpageGetter that gets a website from the internet.
(Basically, an abstraction of the WebFetch tool.)
"""
import typing
import datetime
from paths import UrlCompatible
from .webpageGetter import WebpageGetter
from .WebFetch import WebFetch


class Internet(WebpageGetter):
    """
    A webpageGetter that gets a website from the internet.
    (Basically, an abstraction of the WebFetch tool.)
    """
    __webFetchInstance=None # This is instanciated as needed. Always use _getWebFetchInstance() to access it. # noqa: E501 # pylint: disable=line-too-long

    def __init__(self):
        WebpageGetter.__init__(self)

    def _getWebFetchInstance(self)->WebFetch:
        if self.__webFetchInstance is None:
            self.__webFetchInstance=WebFetch()
        return self.__webFetchInstance

    def get(self,
        url:UrlCompatible,
        date:typing.Optional[datetime.datetime]=None)->None:
        self._getWebFetchInstance().fetchNow(
            url,returnSeleniumObject=False,failoverOnGeneratedPages=False)

    def cmdline(self):
        """
        Run the command line interpreter
        """
        self._getWebFetchInstance().cmdline()


if __name__ == '__main__':
    Internet().cmdline() # apart from default settings, this is the same thing as running WebFetch.py # noqa: E501 # pylint: disable=line-too-long
