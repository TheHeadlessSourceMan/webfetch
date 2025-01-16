"""
Base class for all getters
"""
from abc import abstractmethod
import typing
import pickle
import os
import sys
from paths import URLCompatible, asUrl
from .WebFetch import WebFetch
from .webfetchTypes import WebFetchResult, HttpMethod


class UrlGetter:
    """
    Base class for all getters
    """

    @abstractmethod
    def get(self,url:URLCompatible)->WebFetchResult:
        """
        Get a url and return the bytes and MimeType of the result
        """
WebpageGetter=UrlGetter


class NormalUrlGetter(UrlGetter):
    """
    Get via a simple http:// request or by file://
    """

    def __init__(self,proxy:URLCompatible=None,timeoutSeconds:float=2.0):
        """
        This normal getter can get file:// urls
        and http:// https:// urls using urllib2
        """
        self.proxy=proxy
        self._webfetch=WebFetch()
        self.timeoutSeconds=timeoutSeconds

    def get(self,
        url:URLCompatible,
        userAgent:str='Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0', # noqa: E501 # pylint: disable=line-too-long
        method:typing.Union[str,HttpMethod]='GET'
        )->WebFetchResult:
        """
        Get a url

        :param url: url to get
        :type url: URLCompatible
        :param userAgent: Which USER-AGENT browser to mimic, defaults to 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0'
        :type userAgent: str, optional
        :param method: HTTP method to use, defaults to 'GET'
        :type method: HttpMethod, optional
        :return: a web fetch result
        :rtype: WebFetchResult
        """ # noqa: E501 # pylint: disable=line-too-long
        url=asUrl(url)
        if isinstance(method,HttpMethod):
            method=str(method)
        data=None
        try:
            if url.isFile:
                data=url.read()
            else:
                #TODO: Should force this off to someobdy who does it better
                #data=self._webfetch.fetchNow(
                #   url,failoverOnGeneratedPages=True)
                import urllib.request
                req=urllib.request.Request(url)
                if userAgent is not None:
                    req.add_header('User-Agent',userAgent)
                if method is None or method!='GET':
                    req.method=method
                f=urllib.request.urlopen(req)
                if not 200<=f.status<300:
                    raise Exception('HTTP error: %d %s'%(f.status,f.reason))
                mime=f.getheader('Content-Type')
                data=f.read()
                data=(data,mime)
        except Exception as e:
            print("ERR:",url)
            raise e
        return data


class PickleCache(UrlGetter):
    """
    Quickly cache the results using python pickle
    """

    def __init__(self,urlGetter:UrlGetter,cacheFilename:str='page_cache.pkl'):
        self.urlGetter:UrlGetter=urlGetter
        self.cacheFilename:str=cacheFilename
        self.__hardCache:typing.Optional[typing.Dict[str,str]]=None
        self.__softCache:typing.Dict[str,str]={}
        self._dirty:bool=False

    def _caches(self):
        if self.__hardCache is None:
            # open the file
            if os.path.isfile(self.cacheFilename):
                f=open(self.cacheFilename,'rb')
                self.__hardCache=pickle.load(f)
                f.close()
                if not isinstance(self.__hardCache,typing.Mapping):
                    self.__hardCache={}
            else:
                self.__hardCache={}
        return self.__hardCache,self.__softCache

    def __del__(self):
        self.flush()

    def flush(self)->None:
        """
        flush the data to file
        """
        if self._dirty:
            f=open(self.cacheFilename,'wb')
            pickle.dump(self.__hardCache,f)
            f.close()
            self._dirty=False

    def cache(self,
        url:URLCompatible,
        data:bytes,
        autoflush:bool=True,
        hardCache:bool=True
        )->None:
        """
        add results to the cache
        """
        hard,soft=self._caches()
        if hardCache:
            hard[url]=data
            self._dirty=True
            if autoflush:
                self.flush()
        else:
            soft[url]=data

    def unCache(self,url:URLCompatible,autoflush:bool=True):
        """
        remove results from the cache
        """
        hard,soft=self._caches()
        if not isinstance(url,str):
            url=url.url
        if url in soft:
            del soft[url]
        if url in hard:
            del hard[url]
            self._dirty=True
            if autoflush:
                self.flush()

    def listPages(self,hardCache:bool=True)->typing.Iterable[str]:
        """
        list pages from a certain cache
        """
        hard,soft=self._caches()
        if hardCache:
            return hard.keys()
        return soft.keys()

    def get(self,
        url:URLCompatible,
        cache:bool=True,
        refetch:bool=False,
        autoflush:bool=True,
        persist:bool=True
        )->WebFetchResult:
        """
        cache - used to turn off caching for an indivitual page

        refetch - used to force re-fetch of page

        autoflush - save to file immediatly

        persist - cached page should be persisted to file
            (hard=False means the info will be dumped once program exits)

        Returns the html from the cache, last fetch for this object, or
        will go get it if it has to
        """
        if url.protocol=='file':
            cache=False # never cache local files
        if cache and not refetch:
            hard,soft=self._caches()
            if url in soft:
                return soft[url]
            if url in hard:
                return hard[url]
        data=self.urlGetter.get(url)
        if cache:
            # save changes to the appropriate cache
            if persist:
                hard[url]=data
                self._dirty=True
                self._dirty=True
                if autoflush:
                    self.flush()
            else:
                soft[url]=data
        return data


def fetch(
    url:URLCompatible,
    cacheLocation:str=None,
    cookies:typing.Dict[str,str]=None,
    userAgent:str=None)->WebFetchResult:
    """
    awesome shortcut routine to fetch a file from the web
    """
    getter:UrlGetter=NormalUrlGetter()
    if cacheLocation is not None:
        getter=PickleCache(getter,cacheFilename=cacheLocation)
    _,_=cookies,userAgent # TODO: figure out how to pass into getters
    data=getter.get(url)
    return data


def cmdline(args):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    import re
    if not args:
        print('USEAGE:\n    urlGetter cmd')
        print('CMDs:')
        print('    ls [pattern]')
        print('    get url')
        print('    fork pattern newfile')
        print('    rm pattern')
    else:
        g=PickleCache(UrlGetter())
        if args[0]=='ls':
            pages=g.listPages()
            if len(args)>1:
                regex=re.escape(' '.join(args[1:]))
                regex=regex.replace('\\*','.*') # return the kleen stars
                regex=re.compile(regex)
                p2=[]
                for p in pages:
                    if regex.match(p):
                        p2.append(p)
                pages=p2
            pages.sort()
            print('\n'.join(pages))
        elif args[0]=='rm':
            pages=g.listPages()
            if len(args)>1:
                regex=re.escape(' '.join(args[1:]))
                regex=regex.replace('\\*','.*') # return the kleen stars
                regex=re.compile(regex)
                p2=[]
                for p in pages:
                    if regex.match(p):
                        p2.append(p)
                pages=p2
                pages.sort()
                for p in pages:
                    print('deleted '+p)
                    g.unCache(p,autoflush=False)
                g.flush()
            else:
                print('ERR: Nothing to delete')
        elif args[0]=='get':
            if len(args)>1:
                url=' '.join(args[1:])
                print(g.get(url))
            else:
                print('ERR: Nothing to get')
        elif args[0]=='fork':
            pages=g.listPages()
            if len(args)>2:
                g2=PickleCache(UrlGetter(),cacheFilename=args[2])
                regex=re.escape(args[1])
                regex=regex.replace('\\*','.*') # return the kleen stars
                regex=re.compile(regex)
                p2=[]
                for p in pages:
                    if regex.match(p):
                        p2.append(p)
                pages=p2
                for k in pages:
                    g2.cache(k,g.get(k),autoflush=False)
                g2.flush()
            else:
                print('requires pattern outfile')
        else:
            print('Unrecognized command.')


if __name__=='__main__':
    cmdline(sys.argv[1:])
