"""
Single cached website
"""
import typing
import os
import datetime
import uuid
from paths import URL,URLCompatible,asUrl


class CachedWebsite:
    """
    Single cached website
    """

    def __init__(self)->None:
        self.url:typing.Optional[URL]=None
        self.retrievalDate:typing.Optional[datetime.datetime]=None
        self.dataFilename:typing.Optional[str]=None

    @property
    def filename(self)->typing.Optional[str]:
        """
        the data filename
        """
        return self.dataFilename

    @property
    def data(self)->bytes:
        """
        this value automatically loads/saves the data from file
        """
        if self.dataFilename is None:
            raise FileNotFoundError(str(self.dataFilename))
        with open(self.dataFilename,'rb') as f:
            data=f.read()
        return data
    @data.setter
    def data(self,data:bytes):
        if self.dataFilename is None:
            raise FileNotFoundError(str(self.dataFilename))
        with open(self.dataFilename,'wb') as f:
            f.write(data)

    def decode(self,data:str):
        """
        decode a line of data
        """
        data_a=data.split(',',3)
        self.retrievalDate=datetime.datetime.strptime("",data_a[0].strip())
        self.dataFilename=data_a[1].strip()
        self.url=asUrl(data_a[2].strip())

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
        self.cache:typing.Dict[typing.Optional[URL],CachedWebsite]={}

    @property
    def fetcher(self):
        """
        get either the fetcher assigned to this object, or
        a default web fetcher
        """
        if self._fetcher is None:
            if self.COMMON_DEFAULT_FETCHER is None:
                import webfetch
                self.COMMON_DEFAULT_FETCHER=webfetch.WebFetch()
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
        return str(self.cacheLocation)+os.sep+'manifest.csv'

    def __del__(self):
        """
        when this goes away, attempt to save
        """
        self.save()

    def decode(self,data:str):
        """
        decode manifest for the cache database
        """
        lines=data.split('\n')
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
            with open(self.filename,'w',encoding='utf-8') as f:
                f.write(self.encode())
            self._dirty=False

    def load(self)->None:
        """
        load the manifest file
        """
        with open(self.filename,'r',encoding='utf-8',errors='ignore') as f:
            self.decode(f.read())
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
        return hash(url)
        return hash(url)

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

    def getCache(self,
        url:URLCompatible,
        date:typing.Optional[datetime.datetime]=None
        )->typing.Optional[bytes]:
        """
        getCache

        return None if the item is not in the cache, or
            it is out-of-date.  Otherwise returns the data.
        """
        v=self.cache.get(asUrl(url))
        if v is None:
            return None
        if date is not None \
            and v.retrievalDate is None \
            or date is None \
            or v.retrievalDate<date:
            #
            return None
        return v.data

    def _nextFilename(self)->str:
        """
        get the next filename for a cached file
        """
        uid=str(uuid.uuid4().hex)
        return f'{self.cacheLocation}{os.sep}{uid}.cache'

    def setCache(self,url:URLCompatible,data:bytes,
        retrievalDate:typing.Union[None,str,datetime.datetime]=None
        )->None:
        """
        set some url data
        """
        url=asUrl(url)
        if retrievalDate is None:
            retrievalDate=datetime.datetime.now()
        else:
            retrievalDate=datetime.datetime.strptime(
                "",str(retrievalDate))
        if url in self.cache:
            cWebsite=self.cache[url]
            cWebsite.data=data
            cWebsite.retrievalDate=retrievalDate
        else:
            cWebsite=CachedWebsite()
            cWebsite.url=url
            cWebsite.dataFilename=self.cacheLocation
            cWebsite.data=self._nextFilename()
            cWebsite.retrievalDate=retrievalDate
            self.cache[URL(url)]=cWebsite
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
