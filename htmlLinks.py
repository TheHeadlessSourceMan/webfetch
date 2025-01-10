#!/usr/bin/python
"""
This is used to grab all links from a plain old everyday
html file
"""
import typing
import re
from paths import UrlCompatible

class HtmlLinks:
    """
    This is used to grab all links from a plain old everyday html file
    """
    __imgTagRegex=None # static and created as needed
    __linkRelTagRegex=None # static and created as needed
    __aTagRegex=None # static and created as needed
    __embedTagRegex=None # static and created as needed
    __objectTagRegex=None  # static and created as needed
    __onclickAttrRegex=None  # static and created as needed
    __scriptTagRegex=None  # static and created as needed
    __jsDocLocationRegex=None  # static and created as needed
    __jsWindowOpen=None # static and created as needed
    __jsLinkStrings=None # static and created as needed
    __mimeExtensionMap={
        'jar':'application/java-archive',
        'class':'application/java-vm',
        'swf':'application/x-shockwave-flash',
        'rtf':'text/rtf',
        'pdf':'application/pdf',
        'f4v':'video/x-f4v',
        'flv':'video/x-flv',
        'fli':'video/x-fli',
        'mpeg':'video/mpeg',
        'qt':'video/quicktime',
        'mpg':'video/mpeg',
        'h261':'video/h261',
        'h263':'video/h263',
        'h264':'video/h264',
        'ogv':'video/ogg',
        'mp4':'video/mp4', # also application/mp4
        'mp3':'audio/mp3',
        'mp4a':'audio/mp4',
        'mpga':'audio/mpeg',
        'oga':'audio/ogg',
        'aac':'audio/x-aac',
        'wav':'audio/x-wav',
        'mid':'audio/midi',
        'midi':'audio/midi',
        'wma':'audio/x-ms-wma',
        'wax':'audio/x-ms-wax',
        'aif':'audio/x-aiff',
        'aiff':'audio/x-aiff',
        'ram':'audio/x-pn-realaudio',
        'htm':'text/html',
        'html':'text/html',
        'xhtml':'text/html',
        'ico':'image/x-icon',
        'jpg':'image/jpeg',
        'jpeg':'image/jpeg',
        'jpe':'image/jpeg',
        'gif':'image/gif',
        'bmp':'image/bmp',
        'png':'image/png',
        'svg':'image/svg+xml',
        }

    def _fixurl(self,url,basePath):
        if url.find('://',10)>0:
            return url
        path=url.split('/')
        if len(path)<=1 or path[0].split('.',2)<=2:
            return 'http://'+('/'.join(path))
        path.insert(0,basePath)
        return '/'.join(path)

    def _guessMime(self,url)->str:
        """
        Try to guess mime type from file extension
        """
        url=url.rsplit('/',1)[-1]
        if url.find('&')>=0 or url.find('.')<0: # generated webpages are inconclusive # noqa: E501 # pylint: disable=line-too-long
            return ''
        extn=url.rsplit('.',1)[-1]
        if extn in ['','php','jsp','asp','cgi']: # generated webpages are inconclusive # noqa: E501 # pylint: disable=line-too-long
            return ''
        if extn in HtmlLinks.__mimeExtensionMap:
            return HtmlLinks.__mimeExtensionMap[extn]
        return ''

    def getByMime(self,
        data:UrlCompatible,
        mime:str,
        basePath:typing.Optional[UrlCompatible]=None,
        includeUnknownTypes:bool=False):
        """
        mostly you'd use a proper mime type for this, but for media you
        can also just shorten it to 'image','audio',or 'video' and
        this function will know what you mean

        includeUnknownTypes tells this whether or not to include data
        that it is unable to determine the type of (HINT: you probably
        want this for html!)
        """
        urls=[]
        if includeUnknownTypes:
            mimes=[mime,'']
        else:
            mimes=[mime]
        if mime.startswith('image'):
            for i in self.getImages(data,basePath):
                if mime=='image' or self._guessMime(data) in mimes:
                    urls.append(i)
            for i in self.getIcons(data,basePath):
                if mime=='image' or self._guessMime(data) in mimes:
                    urls.append(i)
            for a in self.getATags(data,basePath):
                if mime=='image':
                    if self._guessMime(data).split('/',1)[0] in mimes:
                        urls.append(data)
                else:
                    if self._guessMime(data) in mimes:
                        urls.append(data)
        elif mime.startswith('audio') or mime.startswith('video'):
            if mime.startswith('audio'):
                # TODO:
                for p in self.getAudioPlayers(data,mime):
                    urls.append(p)
            if mime.startswith('video'):
                # TODO:
                for p in self.getVideoPlayers(data,mime):
                    urls.append(p)
            for a in self.getATags(data,basePath):
                if mime=='audio' or mime=='video':
                    if self._guessMime(a).split('/',1)[0] in mimes:
                        urls.append(a)
                else:
                    if self._guessMime(a) in mimes:
                        urls.append(a)
        elif mime.startswith('application'):
            if mime=='application/javascript' \
                or mime=='application/emcascript':
                #
                for js in self.getJavascript(data,basePath):
                    urls.append(js)
            else:
                for a in self.getATags(data,basePath):
                    if self._guessMime(a) in mimes:
                        urls.append(a)
                for e in self.getEmbedded(data,basePath):
                    if self._guessMime(e) in mimes:
                        urls.append(e)
        elif mime.startswith('text'):
            if mime=='text/css':
                for css in self.getStylesheets(data,basePath):
                    urls.append(css)
            elif mime=='text/html':
                for a in self.getATags(data,basePath):
                    if self._guessMime(a) in mimes:
                        urls.append(a)
                for a in self.getSimpleUrlsFromJsCode(data,basePath):
                    if self._guessMime(a) in mimes:
                        urls.append(a)
        else:
            for a in self.getATags(data,basePath):
                if self._guessMime(a)[0] in mimes:
                    urls.append(a)

    def getATags(self,data,basePath=None):
        """
        Gets all urls pointed to by <a href=""> tags.

        If you're wanting all the links from this site, you're
        probably better off doing:
            getByMime(data,'text/html',basePath,True)
        """
        if basePath is None:
            if hasattr(data,'filename'):
                basePath=data.filename
            if basePath is None:
                basePath='.'
        urls=[]
        if HtmlLinks.__aTagRegex is None:
            HtmlLinks.__aTagRegex=re.compile(
                r"""<a\s+(?P<attrs>.*?href\s*=\s*"(?P<url>[^"]*)"[^>]*)""", # noqa: E501 # pylint: disable=line-too-long
                re.IGNORECASE|re.MULTILINE)
        for match in HtmlLinks.__imgTagRegex.finditer(data):
            url=self._fixurl(match.group('url'),basePath)
            urls.append(url)
        return urls

    def getSimpleUrlsFromJsCode(self,
        data,
        basePath:typing.Optional[UrlCompatible]=None,
        includeLinkLikeStrings:bool=True):
        """
        Gets all simple urls in javascript code, like
            document.location= sets or window.open("url")

        Naturally, those that require executing the javascript itsself
        will not be added.  For instance:
            document.location="foo.com" // no problem
            document.location="foo.com/item"+a+".gif" // not ok

        :includeLinkLikeStrings: tells us whether or not to search for
        things that look like possible links.  For example:
            var x = "http://whatever";
        That may be correct. Or later in the code they might say:
            y=x+'/image.gif'
        Again, we would have no way of knowing without running the javascript!
        """
        if basePath is None:
            if hasattr(data,'filename'):
                basePath=data.filename
            if basePath is None:
                basePath='.'
        urls=[]
        if HtmlLinks.__jsDocLocationRegex is None:
            HtmlLinks.__jsDocLocationRegex=re.compile(
                r"""[.\s]location\s*=\s*(?P<quote>['"]*)(?P<url>.+?)(?P=quote)(?P<compounded>\s*[+])?""") # noqa: E501 # pylint: disable=line-too-long
        if HtmlLinks.__jsWindowOpen is None:
            HtmlLinks.__jsWindowOpen=re.compile(
                r"""window[.]open\s*[(]\s*(?P<quote>['"]+)(?P<url>.+?)(?P=quote)(?P<compounded>\s*[+])?""") # noqa: E501 # pylint: disable=line-too-long
        if includeLinkLikeStrings and HtmlLinks.__jsLinkStrings is None:
            HtmlLinks.__jsLinkStrings=re.compile(
                r"""(?P<quote>['"]+)(?P<url>http(?:s)?[:][/].+?)(?P=quote)(?P<compounded>\s*[+])?""") # noqa: E501 # pylint: disable=line-too-long
        # search in the <script> blocks
        if HtmlLinks.__scriptTagRegex is None:
            HtmlLinks.__scriptTagRegex=re.compile(
                r"""<script[^>]*?>(?P<code>.*?)</script>""", # noqa: E501 # pylint: disable=line-too-long
                re.IGNORECASE|re.MULTILINE|re.DOTALL)
        for match in HtmlLinks.__scriptTagRegex.finditer(data):
            code=self._fixurl(match.group('code'),basePath)
            for match2 in HtmlLinks.__jsDocLocationRegex.finditer(code):
                if match.group('compounded').find('+')<0:
                    url=self._fixurl(match.group('url'),basePath)
                    urls.append(url)
            for match2 in HtmlLinks.__jsWindowOpen.finditer(code):
                if match.group('compounded').find('+')<0:
                    url=self._fixurl(match.group('url'),basePath)
                    urls.append(url)
            if includeLinkLikeStrings \
                and HtmlLinks.__jsLinkStrings is not None:
                #
                for match2 in HtmlLinks.__jsLinkStrings.finditer(code):
                    if match2.group('compounded').find('+')<0:
                        url=self._fixurl(match2.group('url'),basePath)
                        urls.append(url)
        # now for the onClick attrs
        if HtmlLinks.__onclickAttrRegex is None:
            HtmlLinks.__onclickAttrRegex=re.compile(
                r"""<.+?\s+onclick\s*=\s*["](?P<code>.*?)["].*?>""", # noqa: E501 # pylint: disable=line-too-long
                re.IGNORECASE|re.MULTILINE|re.DOTALL)
        for match in HtmlLinks.__onclickAttrRegex.finditer(data):
            code=self._fixurl(match.group('code'),basePath)
            for match2 in HtmlLinks.__jsDocLocationRegex.finditer(code):
                if match.group('compounded').find('+')<0:
                    url=self._fixurl(match.group('url'),basePath)
                    urls.append(url)
            for match2 in HtmlLinks.__jsWindowOpen.finditer(code):
                if match.group('compounded').find('+')<0:
                    url=self._fixurl(match.group('url'),basePath)
                    urls.append(url)
            if includeLinkLikeStrings \
                and HtmlLinks.__jsLinkStrings is not None:
                #
                for match2 in HtmlLinks.__jsLinkStrings.finditer(code):
                    if match.group('compounded').find('+')<0:
                        url=self._fixurl(match2.group('url'),basePath)
                        urls.append(url)
        return urls

    def getImages(self,data,basePath=None):
        """
        Gets all urls pointed to by <img src=""> tags

        If you instead want all images that the data refers to,
        you should instead use:
            getByMime(data,'image',basePath)
        """
        if basePath is None:
            if hasattr(data,'filename'):
                basePath=data.filename
            if basePath is None:
                basePath='.'
        urls=[]
        if HtmlLinks.__imgTagRegex is None:
            HtmlLinks.__imgTagRegex=re.compile(
                r"""<img\s+(?P<attrs>.*?src\s*=\s*"(?P<url>[^"]*)"[^>]*)""", # noqa: E501 # pylint: disable=line-too-long
                re.IGNORECASE|re.MULTILINE)
        for match in HtmlLinks.__imgTagRegex.finditer(data):
            url=self._fixurl(match.group('url'),basePath)
            urls.append(url)
        return urls

    def getIcons(self,data,basePath=None):
        """
        Gets all urls pointed to by <link rel="icon" href=""> tags

        If you instead want all images that the data refers to,
        you should instead use:
            getByMime(data,'image',basePath)
        """
        icons=[]
        for rel,url in self.getLinkRels(data,basePath):
            if rel.find('icon')>=0:
                icons.append(url)
        return icons

    def getStylesheets(self,data,basePath=None):
        """
        Gets all urls pointed to by <link rel="icon" href=""> tags
        """
        urls=[]
        for rel,url in self.getLinkRels(data,basePath):
            if rel.find('style')>=0:
                urls.append(url)
        return urls

    def getLinkRels(self,data,basePath=None):
        """
        Gets all urls pointed to by <link rel="" href=""> tags

        returns [(rel,url)]
        """
        if basePath is None:
            if hasattr(data,'filename'):
                basePath=data.filename
            if basePath is None:
                basePath='.'
        rels=[]
        if HtmlLinks.__linkRelTagRegex is None:
            HtmlLinks.__linkRelTagRegex=re.compile(
                r"""<link\s+(?P<attrs>rel="(?P<rel>[^"]*)".*?href\s*=\s*"(?P<url>[^"]*)"[^>]*)""", # noqa: E501 # pylint: disable=line-too-long
                re.IGNORECASE|re.MULTILINE)
        for match in HtmlLinks.__linkRelTagRegex.finditer(data):
            url=self._fixurl(match.group('url'),basePath)
            rels.append((match.group('rel').lower(),url))
        return rels

    def getEmbedded(self,data,basePath=None):
        """
        Gets all urls pointed to by tags like:
            <embed src="">
            <object data="">
            <applet code="">

        NOTE: This will only return one item of each url,
            for pages that contain both types of embedding

        returns [(mimeType,url)]
        (where mimeType could be empty if not specified)
        """
        if basePath is None:
            if hasattr(data,'filename'):
                basePath=data.filename
            if basePath is None:
                basePath='.'
        embeds={}
        if HtmlLinks.__embedTagRegex is None:
            HtmlLinks.__embedTagRegex=re.compile(
                r"""<embed\s+(?P<attrs>type="(?P<mimetype>[^"]*)".*?src\s*=\s*"(?P<url>[^"]*)"[^>]*)""", # noqa: E501 # pylint: disable=line-too-long
                re.IGNORECASE|re.MULTILINE)
        for match in HtmlLinks.__embedTagRegex.finditer(data):
            url=self._fixurl(match.group('url'),basePath)
            embeds[url]=(match.group('mimetype').lower(),url)
        if HtmlLinks.__objectTagRegex is None:
            HtmlLinks.__objectTagRegex=re.compile(
                r"""<object\s+(?P<attrs>type="(?P<mimetype>[^"]*)".*?data\s*=\s*"(?P<url>[^"]*)"[^>]*)""", # noqa: E501 # pylint: disable=line-too-long
                re.IGNORECASE|re.MULTILINE)
        for match in HtmlLinks.__objectTagRegex.finditer(data):
            url=self._fixurl(match.group('url'),basePath)
            embeds[url]=(match.group('mimetype').lower(),url)
        if HtmlLinks.__objectTagRegex is None:
            HtmlLinks.__objectTagRegex=re.compile(
                r"""<applet\s+(?P<attrs>codebase="(?P<codebase>[^"]*)".*?code\s*=\s*"(?P<url>[^"]*)"[^>]*)""", # noqa: E501 # pylint: disable=line-too-long
                re.IGNORECASE|re.MULTILINE)
        for match in HtmlLinks.__objectTagRegex.finditer(data):
            url=str(match.group('url'))
            if match.group('codebase') and len(str(match.group('codebase')))>0:
                url=match.group('codebase')+'/'+url
            url=self._fixurl(url,basePath)
            mime=self._guessMime(url)
            if mime=='':
                mime='application/java-archive'
            embeds[url]=(mime,url)
        return list(embeds.values())
