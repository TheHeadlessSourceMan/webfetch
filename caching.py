"""
Single cached website
"""
import typing
import os
import datetime
import uuid
from paths import URL, URLCompatible


class CachedWebsite:
    """
    Single cached website
    """

    def __init__(self):
        self.url:URL=None
        self.retrievalDate:datetime.datetime=None
        self.dataFilename:str=None

    @property
    def data(self)->bytes:
        """
        this value automatically loads/saves the data from file
        """
        f=open(self.dataFilename,'rb')
        d=f.read()
        f.close()
        return d
    @data.setter
    def data(self,data:bytes):
        f=open(self.dataFilename,'wb')
        f.write(data)
        f.close()

    def decode(self,data:bytes):
        """
        decode a line of data
        """
        data_a=data.split(b',',3)
        self.retrievalDate=datetime.datetime(data_a[0].strip())
        self.dataFilename=data_a[1].strip()
        self.url=data_a[2].strip()

    def encode(self)->str:
        """
        encode a line of data
        """
        return '%s,%s,%s'%(self.retrievalDate,self.dataFilename,self.url)

    def csvHeader(self)->str:
        """
        encode a line of data
        """
        return 'retrievalDate,dataFilename,url'


class Cache:
    """
    a webpage cache system
    """

    COMMON_DEFAULT_FETCHER=None # used to maintain one fetcher across instances

    def __init__(self,cacheLocation:URLCompatible,
        fetcher:typing.Optional[str]=None,
        autosave:bool=False):
        """
        :param cacheLocation: can be
            * a single cache file
            * a folder full of cache files
        :param fetcher: a fetcher tool to use if the cache hit fails
        """
        self.cacheLocation=cacheLocation
        self._currentCache:typing.Optional[str]=None
        self._dirty:bool=False
        self._fetcher:typing.Optional[str]=fetcher
        self.autosave:bool=autosave
        self.cache:typing.Dict[URL,CachedWebsite]={}

    @property
    def fetcher(self):
        """
        get either the fetcher assigned to this object, or
        a default web fetcher
        """
        if self._fetcher is None:
            if self.COMMON_DEFAULT_FETCHER is None:
                import webFetch
                self.COMMON_DEFAULT_FETCHER=webFetch.WebFetch()
            self._fetcher=self.COMMON_DEFAULT_FETCHER
        return self._fetcher
    @fetcher.setter
    def fetcher(self,fetcher):
        self._fetcher=fetcher

    @property
    def filename(self)->str:
        """
        get the filename of the manifest
        """
        return self.cacheLocation+os.sep+'manifest.csv'

    def __del__(self):
        """
        when this goes away, attempt to save
        """
        self.save()

    def decode(self,data:bytes):
        """
        decode manifest for the cache database
        """
        lines=data.split(b'\n')
        if lines:
            lines=lines[1:]
        for line in lines:
            cw=CachedWebsite()
            cw.decode(line)
            self.cache[cw.url]=cw
        self._dirty=False

    def encode(self)->str:
        """
        encode manifest for the cache database
        """
        ret:typing.List[str]=[]
        for v in self.cache.values():
            if not ret:
                ret.append(v.csvHeader())
            ret.append(v.encode())
        return '\n'.join(ret)

    def save(self)->None:
        """
        save out the manifest file
        """
        if self._dirty:
            f=open(self.filename,'wb')
            f.write(self.encode())
            f.close()
            self._dirty=False

    def load(self)->None:
        """
        load the manifest file
        """
        f=open(self.filename,'rb')
        self.decode(f.read())
        f.close()
        self._dirty=False

    @property
    def dirty(self)->bool:
        """
        whether or not the database needs saved
        """
        return self._dirty
    @dirty.setter
    def dirty(self,dirty:bool):
        self._dirty=dirty
        if self._dirty and self.autosave:
            self.save()

    def _hashUrl(self,url:URLCompatible):
        """
        turn a url into a hashable value
        """
        return url.__hash__()

    def fetch(self,url:URLCompatible,
        date:typing.Optional[datetime.datetime]=None
        )->bytes:
        """
        Derived classes must override this.
        """
        if hasattr(self.cacheLocation,'fetch'):
            return self.cacheLocation.fetch(url,date)
        if not isinstance(self.cacheLocation,str):
            raise Exception()
        if not os.path.isdir(self.cacheLocation):
            os.mkdir(self.cacheLocation)
        data=self.getCache(url,date)
        if data is None:
            data=self.fetcher.fetch(url)
            self.setCache(url,data)
        return data

    def getCache(self,url:URLCompatible,
        date:typing.Optional[datetime.datetime]=None
        )->typing.Optional[bytes]:
        """
        getCache

        return None if the item is not in the cache, or
            it is out-of-date.  Otherwise returns the data.
        """
        v=self.cache.get(url)
        if v is None:
            return None
        if date is not None and v.retrievalDate is None or v.retrievalDate<date:
            return None
        return v.data

    def _nextFilename(self)->str:
        """
        get the next filename for a cached file
        """
        return self.cacheLocation+os.sep+uuid.uuid4().hex+'.cache'

    def setCache(self,url:URLCompatible,data:bytes,
        retrievalDate:typing.Union[None,str,datetime.datetime]=None
        )->None:
        """
        set some url data
        """
        if retrievalDate is None:
            retrievalDate=datetime.datetime.now()
        if not isinstance(retrievalDate,str):
            retrievalDate=str(retrievalDate)
        if url in self.cache:
            cWebsite=self.cache[url]
            cWebsite.data=data
            cWebsite.retrievalDate=retrievalDate
        else:
            cWebsite=CachedWebsite()
            cWebsite.url=url
            cWebsite.filename=self.cacheLocation
            cWebsite.data=self._nextFilename()
            cWebsite.retrievalDate=retrievalDate
            self.cache[url]=cWebsite
        self.dirty=True

    def __getattr__(self,url:URLCompatible)->bytes:
        """
        Interesting feature:  You can say WebpageGetter[url] to get a webpage!
        """
        return self.fetch(url)

    def __setattr__(self,url:URLCompatible,data:bytes)->None:
        """
        Interesting feature:  You can say WebpageGetter[url] to get a webpage!
        """
        return self.setCache(url,data)
