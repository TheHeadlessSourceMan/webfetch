#!/usr/bin/python
"""
class to perform an internet search
"""
import typing
import urllib.request
import urllib.parse
import urllib.error
from paths import UrlCompatible


class WebSearch:
    """
    class to perform an internet search
    """

    def __init__(self,searchEngine:str='all'):
        """
        You can tell it which search engine to use, or use all available ones.
        """
        self.searchEngine=searchEngine

    def _url2soup(self,url:UrlCompatible)->typing.Any:
        """
        Fetch a url using the best means available and return the
        results as a BeautifulSoup object.
        """
        try:
            import urllib2.request # type: ignore
            import urllib2.error # type: ignore
            import urllib2.parse # type: ignore
        except ImportError:
            urllib2=None
        # the following is not optional and
        # will throw if the library is not installed
        from BeautifulSoup import BeautifulSoup # type: ignore # noqa: E501 # pylint: disable=line-too-long,import-error
        try:
            if urllib2 is None:
                f=urllib2.request.urlopen(url)
            else:
                headers={'User-Agent':'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)'} # noqa: E501 # pylint: disable=line-too-long
                request=urllib.request.Request(url,None,headers)
                f=urllib.request.urlopen(request)
        except Exception as e:
            print(str(e)+' when processing '+url)
            f=None
        data=''
        if f is not None:
            data=f.read().decode('utf-8','ignore')
            f.close()
        return BeautifulSoup(data)

    def _googleTranslate(self,
        text:str,
        fromLanguage:str,
        toLanguage:str='en'
        )->typing.Any:
        """
        Call the google translate page
        """
        url='http://translate.google.com/translate_t'
        url=url+'?sl='+fromLanguage+'&tl='+toLanguage
        url=url+'&hl=en&ie=UTF8'
        url=url+'&text='+urllib.parse.quote_plus(text)
        soup=self._url2soup(url)
        return soup('div',id='result_box')[0].string

    def _googleSearch(self,
        searchString:str,
        page:int=1,
        resultsPerPage:int=50
        )->typing.Any:
        """
        Perform a google search
        """
        retval=[]
        url='http://www.google.com/search'
        url=url+'?q='+urllib.parse.quote_plus(searchString)
        url=url+'&num='+str(resultsPerPage)
        url=url+'&hl=en&start='+str(page-1)
        soup=self._url2soup(url)
        print(soup)
        try:
            for a in soup.findAll('a',attrs={'class':'l'}):
                retval.append(a['href'])
        except Exception as e:
            print(str(e)+' when parsing google results '+url)
        return retval

    def _yahooSearch(self,searchString:str)->typing.Any:
        import re
        url='http://search.yahoo.com/search?'
        url=url+'p='+urllib.parse.quote_plus(searchString)
        soup=self._url2soup(url)
        urlRe=re.compile(r'/\*\*(.*)')
        try:
            return [urllib.parse.unquote_plus(urlRe.findall(h3.find('a')['href'])[0]) # noqa: E501 # pylint: disable=line-too-long
                   for h3 in soup.find('div',id='web').findAll('h3')]
        except Exception as e:
            print(str(e)+' when parsing yahoo results '+url)
        return []

    def search(self,
        forThis:typing.Union[str,typing.Iterable[str]],
        notForThis:typing.Union[None,str,typing.Iterable[str]]=None
        )->typing.Any:
        """
        perform a web search and return results

        forThis can either be a proper search string or an array
        of search items (of any type)

        notForThis is just like forThis but must always be an array
        and it is invalid if forThis is not an array also.
        """
        searchString=''
        if not isinstance(forThis,str):
            for f in forThis:
                if not isinstance(f,str):
                    f=str(f)
                if f.find(' ')>=0:
                    searchString=searchString+' '+f
                else:
                    searchString=searchString+' "'+f+'"'
            for f in notForThis:
                if not isinstance(f,str):
                    f=str(f)
                if f.find(' ')>=0:
                    searchString=searchString+' -'+f
                else:
                    searchString=searchString+' -"'+f+'"'
        results=[]
        if self.searchEngine=='yahoo' or self.searchEngine=='all':
            results=self._googleSearch(searchString,1,50)
        if self.searchEngine=='google' or self.searchEngine=='all':
            results.extend(self._yahooSearch(searchString))
        return results


if __name__ == '__main__':
    import sys
    if len(sys.argv)<2:
        print('USAGE: WebSearch.py "search String"')
    else:
        searchString=' '.join(sys.argv[1:])
        search=WebSearch()
        print('Search: '+searchString+'\n    '+
            '\n    '.join(search.search(searchString)))
