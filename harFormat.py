import typing
import json
from paths import UrlCompatible, asUrl, Path


JsonPrimatives=typing.Union[str,int,float]
JsonDict=typing.Union[typing.Dict[str,"JsonLike"],"QuickAndDirtyJson"]
JsonList=typing.List["JsonLike"]
JsonLike=typing.Union[JsonPrimatives,JsonDict,JsonList]

class QuickAndDirtyJson:
    """
    The name says it all.  A quick and dirty way to turn any json into a pythonic class.
    """
    def __init__(self,
        filename:typing.Optional[UrlCompatible]=None,
        jsonObj:typing.Optional[JsonDict]=None):
        """ """
        if jsonObj is None:
            jsonObj={}
        self.jsonObj:typing.Union[JsonDict,JsonList]=jsonObj
        if filename is not None:
            self.load(filename)

    def load(self,filename:UrlCompatible)->None:
        """
        Load json from filename/url
        """
        raw=asUrl(filename).read()
        self.jsonObj=json.loads(raw)

    def save(self,filename:UrlCompatible)->None:
        """
        Save json to file
        """
        url=asUrl(filename)
        if not url.isFile:
            raise FileNotFoundError(f'Not a local file: "{url}"')
        with open(typing.cast(str,url.filePath),'wb') as f:
            f.write(json.dumps(self.jsonObj).encode('utf-8'))
            f.close()

    def __len__(self)->int:
        return len(self.jsonObj)
    
    def __iter__(self)->typing.Generator[JsonLike,None,None]:
        for item in iter(self.jsonObj):
            if isinstance(item,(dict,list)):
                item=QuickAndDirtyJson(jsonObj=typing.cast(JsonDict,item))
            yield item

    @typing.overload
    def get(self,k:typing.Any,default:JsonLike)->JsonLike: ...
    @typing.overload
    def get(self,k:typing.Any,default:None)->None: ...
    def get(self,k:typing.Any,default:typing.Optional[JsonLike]=None)->typing.Optional[JsonLike]:
        if isinstance(self.jsonObj,list):
            if k>=len(self.jsonObj):
                return default
            return self.jsonObj[k]
        return self.jsonObj.get(k,default)

    def __getitem__(self,k:typing.Any)->JsonLike:
        item=self.jsonObj[k]
        if isinstance(item,(dict,list)):
            return QuickAndDirtyJson(jsonObj=typing.cast(JsonDict,item))
        return item
        
    def __getattr__(self,k:typing.Any)->JsonLike:
        if k not in self.jsonObj:
            avail=f'\n   Available: {dir(self)}'
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{k}'{avail}")
        item:JsonLike=self.jsonObj[k]
        if isinstance(item,(dict,list)):
            return QuickAndDirtyJson(jsonObj=typing.cast(JsonDict,item))
        return item

    def set(self,k:typing.Any,v:JsonLike)->None:
        self.jsonObj[k]=v

    def __setitem__(self,k:typing.Any,v:JsonLike)->None:
        self.jsonObj[k]=v

    def __setattr__(self,k:typing.Any,v:typing.Any)->None:
        if k in self.__dict__ or k in ('jsonObj',):
            self.__dict__[k]=v
        else:
            if not isinstance(v,(list,dict,str,int,float)):
                v=str(v)
            self.jsonObj[k]=typing.cast(JsonLike,v)
    
    def __dir__(self)->typing.Iterable[str]:
        yield from dir(super())
        yield from self.__dict__.keys()
        if isinstance(self.jsonObj,dict):
            yield from self.jsonObj.keys()

    def __repr__(self)->str:
        return str(self.jsonObj)


class Har(QuickAndDirtyJson):
    """
    Represents the .HAR file format
    which is a network capture as exported by Firefox/Chrome developer tools
    
    The goal of this is to auto-snarf an entire transaction and figure out
    the format of the api calls involved.
    """
    def __init__(self,filename:typing.Optional[UrlCompatible]=None):
        QuickAndDirtyJson.__init__(self,filename)

    def getData(self,
        urlLike:typing.Union[None,str,typing.Pattern]=None,
        entries:typing.Optional[typing.Iterable[JsonDict]]=None
        )->typing.Tuple[str,str]:
        """
        :urlLike: the url must be like this
            urlLike can be a compiled regular expression to call match() on
            or if it's a string, every * will be replaced by any characters

        returns (mimeType,data)
        """
        if urlLike is not None:
            if isinstance(urlLike,str):
                import re
                urlLike=re.compile('(.*)'+re.escape(urlLike).replace(r'\*','(.*)'),re.IGNORECASE)
            if entries is None:
                entries=self.log.entries
            for entry in entries:
                if urlLike.match(entry.request.url) is not None:
                    return (entry.response.content.mimeType,entry.response.content.text)
        return ('','')

    def findEntries(self,
        resourceTypes:typing.Optional[typing.List[str]]=None,
        mimeTypes:typing.Optional[typing.List[str]]=None,
        urlLike:typing.Union[None,str,typing.Pattern]=None,
        entries:typing.Optional[typing.Iterable[JsonDict]]=None
        )->typing.Generator[JsonDict,None,None]:
        """
        Find a certain subset of entries.

        :resourceTypes: if specified, each result must have one of these resource types
        :mimeTypes: if specified, each result must have one of these mime types
        :urlLike: if specified, the url must be like this
            urlLike can be a compiled regular expression to call match() on
            or if it's a string, every * will be replaced by any characters

        Examples:
        to find just ajax (aka, xhr) requests returning json:
            findEntries(resourceTypes=['xhr'],mimeTypes=['application/json'])
        to find all html responses:
            findEntries(mimeTypes=['text/html'])
        """
        if entries is None:
            entries=self.log.entries
        if urlLike is not None and isinstance(urlLike,str):
            import re
            urlLike=re.compile('(.*)'+re.escape(urlLike).replace(r'\*','(.*)'),re.IGNORECASE)
        for entry in entries:
            if resourceTypes is not None and entry._resourceType not in resourceTypes:
                continue
            if mimeTypes is not None and entry.response.content.mimeType not in mimeTypes:
                continue
            if urlLike is not None and urlLike.match(entry.request.url) is None:
                continue
            yield entry
    def printableEntry(self,entry:JsonDict)->str:
        method=entry.request.method
        url=entry.request.url
        resourceType=entry._resourceType
        responseStatus=entry.response.status
        responseMime=entry.response.content.mimeType
        responseBytes=entry.response.content.size
        return f"[{resourceType}] {method} {url}\n"+ \
            f"   {responseStatus} {responseMime} ({responseBytes} bytes)"
    
    def printableEntries(self,entries:typing.Optional[typing.Iterable[JsonDict]]=None)->str:
        if entries is None:
            entries=self.log.entries
        return '\n\n'.join([self.printableEntry(entry) for entry in entries])

    def _makeStandin(self,s:str)->str:
        return '${'+s+'}'

    def _replaceUrl(self,url:Path,
        replacements:typing.Dict[str,typing.Any],value:str,standin:str)->None:
        """
        finds the value in the url, then replaces it with the stand-in,
        for example:
            url=Url("http://fooblatz.com/q?rutabegas")
            _replaceUrl(url,"rutabegas":"{vegetable_name}")
        """
        if url.contains(value):
            url=url.replace(value,standin)
            replacements['url']=url
        for kk,vv in url.params.items():
            if vv==value:
                url.params[kk]=standin
                replacements['url']=url

    def _replaceCookies(self,cookieJar:JsonDict,settingFrom:str,cookies:JsonList,
        replacements:typing.Dict[str,typing.Any],value:str,standin:str)->None:
        """
        finds the value in the cookies, then replaces it with the stand-in

        NOTE: if the cookies in the jar changed, will also add it to the replacements
        """
        for cookie in cookies:
            cookieId=f'{cookie.name}@{cookie.domain}'
            if cookie.value==value:
                cookieJar[cookieId]=cookie.value
                cookie.value=standin
                replaceCookies=replacements.get(settingFrom,{})
                replaceCookies[cookieId]=cookie
                replacements[settingFrom]=replaceCookies
            else:
                currentValue=cookieJar.get(cookieId)
                if currentValue is None or currentValue!=cookie.value:
                    # cookie has changed, so start tracking it!
                    cookieJar[cookieId]=cookie.value
                    replacements[cookie.value]=self._makeStandin(cookieId)

    def _replaceContents(self,contents:typing.Optional[str],settingFrom:str,
        replacements:typing.Dict[str,typing.Any],value:str,standin:str)->None:
        """
        finds the value in the cookies, then replaces it with the stand-in

        NOTE: if the cookies in the jar changed, will also add it to the replacements
        """
        if contents is not None and contents.find(value)>=0:
            replacements[settingFrom]=contents.replace(value,standin)

    def snarf(self,
        dataToVariable:typing.Dict[str,str]={},
        entries:typing.Optional[typing.Iterable[JsonDict]]=None):
        """
        This snarfs a .har file to try and determine an api

        The whole goal is to generate a configurable series of steps that can bring about
        the original data flow, only with custom data fields.

        :dataToVariable: find certain data in the requests and call that a variable
            For instance, you sumitted a form with zipcode "90210", dataToVariable={"90210","zipcode"}
            NOTE: if the variable contains "#" this is a little different because it
                may be hashed in the data ("#password" would be the most common example!)
                examples:
                    "sha1#password"
                    "md5#password"
                    "#password" (which is all hashes)
        :entries: instead of passing in all entries, you can pass in a filtered subset,
            for instance, to just snarf ajax:
                har.snarf(entries=har.findEntries(resourceTypes=['xhr']))

        NOTE: anything that ends with "key" or "token" or contains "sess[ion]" will be added to the results

        TODO: scrape html responses for forms and add those to the results
        """
        import hashlib
        for k,v in dataToVariable.items():
            hashval=v.split('#',1)
            if len(hashval)>1:
                dataToVariable[k]=hashval[1] # non-hashed
                if not hashval[0]:
                    for hashtype in ('sha1','md5'):
                        dataToVariable[getattr(hashlib,hashtype)(k)]=f'{hashtype}#{hashval[1]}'
                else:
                    dataToVariable[getattr(hashlib,hashval[0])(k)]='#'.join(hashval)
        if entries is None:
            entries=self.log.entries
        foundEntries:typing.List[typing.Tuple[JsonDict,typing.Dict[str,str]]]=[]
        cookieJar:JsonDict={}
        for entry in entries:
            replacements:typing.Dict[str,typing.Any]={}
            url:Path=Path(entry.request.url)
            for value,standin in dataToVariable.items():
                standin=self._makeStandin(standin)
                self._replaceUrl(url,replacements,value,standin)
                self._replaceCookies(cookieJar,'requestCookies',entry.request.cookies,replacements,value,standin)
                print(dir(entry.response.content))
                self._replaceContents(entry.response.content.get('text'),'requestContents',replacements,value,standin)
                self._replaceCookies(cookieJar,'responseCookies',entry.response.cookies,replacements,value,standin)
                self._replaceContents(entry.response.content.get('text'),'responseContents',replacements,value,standin)
            if replacements:
                foundEntries.append((entry,replacements))
        return foundEntries

    def __repr__(self)->str:
        return self.printableEntries()


def test():
    har=Har(r"D:\python\webfetch\sample_data\www.amazon.com.har")
    entries:typing.List[typing.Any]=list(har.findEntries(["xhr"]))
    #print(har.printableEntries(har.findEntries(["xhr"])))
    #print(entries[0].request.cookies)

    results=har.snarf({'133-5296356-0994546':'sessionId'})
    for result in results:
        print(result[1].keys())

    mime,data=har.getData(r"https://www.amazon.com/nav/ajax/*")
    if mime=='zzzapplication/json':
        parsed=json.loads(data)
        import pprint
        pprint.pprint(parsed)