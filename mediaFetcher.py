#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This tool loads up a config xml and smartly fetches media
accordingly
"""
import typing
import os
import re
import pickle
from datetime import date
from paths import UrlCompatible,Url
from webFetch import WebFetch


class Download:
    """
    Represents a download
    """

    def __init__(self,downloadTo:str=None):
        """
        Name is the name you want this search returned as.

        startLocation is the url to start with
            TODO: just make it another urlLike with no wildcards

        urlLike is a regular expression to search for within the given url.
        If None, will search for known media types.
        If an array, it will search in the first url for match like the
            first element, then from the pages loaded from each of those
            search for match like the second element, and so on.
            (Any array element can be None as well.)

        :downloadTo: is the directory to put files in.
            It will be created if it does not exist.  If None,
            will create a directory with the current date.
        """
        self.name:str=''
        self.startLocation:str=''
        self.urlLike:typing.List[typing.Pattern]=[]
        if downloadTo is None:
            downloadTo=date.today().strftime('%y%m%d_%a_%b_%d_%Y')
        # if self.indexDir is None:
        #   self.indexDir=downloadTo
        if not os.path.isdir(downloadTo):
            os.mkdir(downloadTo)
        self.downloadTo:typing.Optional[str]=downloadTo
        self.speaker:typing.Optional[str]=None
        self.browserType:typing.Optional[str]=None

    def __setxmlattr__(self,node,name:str):
        if name in node.attributes:
            setattr(self,name,str(node.attributes[name].value))
        else:
            setattr(self,name,None)

    def load(self,node)->"Download":
        """
        load a download
        """
        self.__setxmlattr__(node,'name')
        self.__setxmlattr__(node,'startLocation')
        self.__setxmlattr__(node,'speaker')
        self.__setxmlattr__(node,'browserType')
        self.urlLike=[]
        for url in node.getElementsByTagName('urlLike'):
            try:
                self.urlLike.append(re.compile(
                    url.firstChild.wholeText,flags=re.IGNORECASE|re.DOTALL))
            except Exception as e:
                print('Regex error on',self.name)
                print('   r"""'+url.firstChild.wholeText+'"""')
                print('  ',str(e))

        #if self.urlLike is None:
        #    urlLike=[re.compile(
        #       r"""\"([^"]+?.(?:"""+'|'.join(self.mediaTypes)+r""")[^"]*?)\"""",
        #       flags=re.IGNORECASE|re.DOTALL)]
        #elif type(self.urlLike)!=list:
        #    urlLike=[re.compile(urlLike,flags=re.IGNORECASE|re.DOTALL)]
        #else:
        #    u2=[]
        #    for u in urlLike:
        #        if u is None:
        #            u2.append(re.compile(
        #               r"""\"([^"]+?.(?:"""+'|'.join(self.mediaTypes)+r""")[^"]*?)\""""), # noqa: E501 # pylint: disable=line-too-long
        #               flags=re.IGNORECASE|re.DOTALL)
        #        else:
        #            u2.append(re.compile(u,flags=re.IGNORECASE|re.DOTALL))
        #    urlLike=u2
        return self

def loadDownloads(
    filename:str,
    downloadTo:typing.Optional[str]=None
    )->typing.List[Download]:
    """
    load all downloads from a file
    """
    from xml.dom import minidom
    doc=minidom.parse(filename)
    downloads=doc.getElementsByTagName('download')
    downloads=[Download(downloadTo).load(download) for download in downloads]
    return downloads


class MediaFetcher(WebFetch):
    """
    Tool for downloading media from a website
    """

    def __init__(self,downloadRecordsFile:str='downloadRecords.dat'):
        WebFetch.__init__(self)
        self.indexDir:typing.Optional[str]=None
        self.startFetchQueue:typing.Dict[str,Download]={}
        self.likeFetchQueue:typing.Dict[Url,typing.Tuple[str,str,Url]]={} # url:(name,downloadTo,originalUrl) # noqa: E501 # pylint: disable=line-too-long
        self.links:typing.Dict[str,str]={}
        self.mediaTypes:typing.List[str]=['mp3','rm','rma','wma','wav','aac']
        self.debug:int=1 # 0=none 1=error 2=warning 3=info
        self.downloadRecords:typing.Dict[str,str]={}
        self.downloadRecordsFile:str=downloadRecordsFile
        self._loadDownloadRecords()

    def __del__(self):
        #self._saveDownloadRecords()
        pass

    def _loadDownloadRecords(self)->None:
        if self.downloadRecordsFile is not None \
            and os.path.isfile(self.downloadRecordsFile):
            #
            self.downloadRecords=pickle.load(
                open(self.downloadRecordsFile,'rb'))

    def _saveDownloadRecords(self)->None:
        if self.downloadRecordsFile is not None:
            pickle.dump(self.downloadRecords,
                open(self.downloadRecordsFile,'w+b'))

    def _addDownloadRecord(self,url:str,filename:str)->None:
        self.downloadRecords[url]=filename
        self._saveDownloadRecords()

    def saveAsMp3(self,mediaLocation:str,mp3FileName:str)->None:
        """
        TODO: write this.
        Possibly check out:
            http://www.jpstacey.info/blog/2006/12/06/realplayer-mp3-configurable-python-wrapper
        """
        raise NotImplementedError()

    def getFlashMedia(self,
        swfInFilename:typing.Optional[str]=None,
        swfInBuffer:typing.Optional[bytes]=None
        )->typing.Union[str,bool]:
        """
        Extracts media from a flash .swf file

        If it works, returns a string pointing to the data.
        If not, it returns False.

        See also:
            http://www.adobe.com/devnet/swf/
        """
        if swfInFilename is not None:
            f=open(swfInFilename,'rb')
            swfIn=f.read()
            f.close()
        elif swfInBuffer is not None:
            swfIn=swfInBuffer
        else:
            if self.debug>=2:
                print('[SKIP] No flash data given')
            return False
        if swfIn[0:3]=='CWS':
            # must decompress
            for i in range(4,len(swfIn)): # find zlib header
                if swfIn[i]=='x':
                    swfIn=swfIn[i:]
                    break
            import zlib
            swfIn=zlib.decompress(swfIn)
        mediaFinder=re.compile(
            r"""\0([^\0]+?.(?:"""+'|'.join(self.mediaTypes)+r"""))\0""")
        match=mediaFinder.search(swfIn)
        if match is None:
            if self.debug>=2:
                print('[SKIP] No media found in flash file')
        elif self.debug>=3:
            print('Found in flash file: '+str(match.group(1)))
            return str(match.group(1))
        return False

    def unPercentCodify(self,oringal:str)->str:
        """
        Decodes percent code delimiters from an embedded web link
        """
        z=oringal.split("%")
        output=[z[0]]
        for i in range(1,len(z)):
            if z[i][0]=="%":
                output.append(z[i])
            else:
                output.append(chr(int(z[i][:2],base=16))+z[i][2:])
        return ''.join(output)

    def _resultsFound(self,
        url:UrlCompatible,
        data:typing.Union[str,bytes]
        )->None:
        """
        get the results found
        """
        url=Url(url)
        if self.debug>=3:
            print(f'_resultsFound {url}')
        name,downloadTo,originalUrl=self.likeFetchQueue[url]
        del self.likeFetchQueue[url]
        # figure out the file extension
        ext_a=name.rsplit('.',1)
        if len(ext_a)>1:
            name=ext_a[0]
            extension=ext_a[-1]
        else:
            ext_a=url.ext
            if len(ext_a)>1:
                extension=ext_a[-1]
            else:
                extension='data'
        # save the data
        if downloadTo[-1]!=os.sep:
            downloadTo=downloadTo+os.sep
        filename=name.strip().replace(' ','_')
        filename=downloadTo+filename+'.'+extension
        if not isinstance(data,bytes):
            data=data.encode('utf-8')
        f=open(filename,'w+b')
        f.write(data)
        f.close()
        if os.sep!='/':
            filename=filename.replace(os.sep,'/')
        self.links[name]='<b><a href="'+filename+'">'+name+'</a></b>'
        self._addDownloadRecord(url,'../'+filename)

    def _startFound(self,baseUrl:UrlCompatible,html:str)->None:
        """
        This is called when an item has been downloaded
        """
        baseUrl=Url(baseUrl)
        if self.debug>=3:
            print('_startFound '+baseUrl)
        download=self.startFetchQueue[baseUrl]
        filename=download.name
        if download.speaker is not None:
            filename=filename+' - '+download.speaker
        del self.startFetchQueue[baseUrl]
        found=False
        for match in download.urlLike[0].finditer(html):
            found=True
            try:
                url=baseUrl.getRelativeUrl(str(match.group(1)))
            except IndexError as e:
                raise IndexError('No groups in expression for search \"'+download.name+'\"') from e # noqa: E501 # pylint: disable=line-too-long
            if len(download.urlLike)>1:
                # look up the next hop in the chain
                self.startFetchQueue[url]=(
                    filename,download.urlLike[1:],download.downloadTo)
                self.enqueue(self._startFound,url)
                self.runNext()
            else:
                # download the media
                if self.debug>=3:
                    print(download.name+' matched media '+url)
                # only download the file if it is new
                if url in self.downloadRecords:
                    filename=filename.rsplit('.',1)[0].strip()
                    self.links['[old] '+filename]='<b><a href="'+self.downloadRecords[url]+'">[old] '+filename+'</a></b>' # noqa: E501 # pylint: disable=line-too-long
                    if self.debug>=2:
                        print('[SKIP] Already downloaded "'+download.name+'" from '+self.downloadRecords[url]) # noqa: E501 # pylint: disable=line-too-long
                else:
                    self.likeFetchQueue[url]=(
                        filename,download.downloadTo,baseUrl)
                    self.enqueue(self._resultsFound,url)
                    self.runNext()
        if not found:
            # if the item is not retrieved, save out an html of what
            # actually was retrieved, to help determine the failure
            filename=download.downloadTo+os.sep+filename.replace(' ','_')+'_ERR.html' # noqa: E501 # pylint: disable=line-too-long
            f=open(filename,'w+')
            f.write(html)
            f.close()
            if os.sep!='/':
                filename=filename.replace(os.sep,'/')
            self.links[download.name]='<b>"'+download.name+'"</b> - Link Not Found. [see also, <a href="'+filename+'">what was downloaded</a>]' # noqa: E501 # pylint: disable=line-too-long
            if self.debug>=1:
                print('"'+download.name+'" - Link Not Found In:\n\t'+baseUrl+'\nSee \"'+filename+'\" for details.') # noqa: E501 # pylint: disable=line-too-long

    def add(self,download:str)->None:
        """
        Adds another download request to the queue.
        """
        if self.debug>=3:
            print('Queuing up '+download.name)
        self.startFetchQueue[download.startLocation]=download
        self.enqueue(self._startFound,download.startLocation)
        self.runNext()

    def getLinksHtml(self,title:typing.Optional[str]=None)->str:
        """
        Creates an html index of all the newly downloaded files.
        """
        if title is None:
            title=date.today()
            title='Recordings for '+title.strftime('%a, %b %d %Y')
        html='<html>\n<head>\n\t<title>'+title+'</title>\n</head>\n<body>'
        html=html+'<h1 style="text-decoration:underline">'+title+':</h1>\n<div style="margin-left:2cm">\n' # noqa: E501 # pylint: disable=line-too-long
        for v in self.links.values():
            html=html+'<li>'+v+'</li>'
        html=html+'</div>\n</body>\n</html>'
        return html

    def saveLinksHtml(self,
        filename:typing.Optional[str]=None,
        title:typing.Optional[str]=None
        )->str:
        """
        Saves an html index of all the newly downloaded files.
        """
        if filename is None:
            if self.indexDir is not None:
                filename=self.indexDir+'/index.htm'
        if filename is None:
            if self.debug>=1:
                print('Nothing downloaded. No index created.')
            else:
                f=open(filename,'w+')
                f.write(self.getLinksHtml(title))
                f.close()
        return filename


def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    _=args
    print('This currently does nothing from the command line.')
    return -1


if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))
