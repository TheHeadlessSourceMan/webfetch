#!/usr/bin/python
"""
Tool to find media in a webpage
"""
import typing
from paths import Url,UrlCompatible


class MediaFinder:
    """
    Tool to find media in a webpage
    """

    def __init__(self,startUrl:UrlCompatible):
        self.startUrl:Url=Url(startUrl)
        self.then:typing.List[typing.Callable[[Url],None]]=[]

    def thenFind(self,find:str,glob:bool=True,re:bool=False,timeFormatted:bool=True):
        """
        Add the next thing to look for.

        If glob=True, you can do '*'s like "http://foo.com/*.mp3"
        If re=True, you can do regular expressions like "http://foo.com/[0-9]{1,6}.mp3"
        If timeFormatted=True, you can use strftime() formatting characters like
                "http://foo.com/%Y_%m_%d.mp3"
        """
        self.then.append((find,glob,re,timeFormatted))


    def _get(self,usingSermonator):
        """
        Generally you should add this to a sermonator instead of calling _get() directly.
        """
        pass


def cmdline(args):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    pass


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
