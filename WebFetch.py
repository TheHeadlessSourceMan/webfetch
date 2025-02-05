#!/usr/bin/python
"""
Fetches a web resource.

If it appears to be generated by javascript,
will get using browser via selenium.
If it appears to be generated by javascript, will get
using browser via selenium.
"""
import typing
import os
from pathlib import Path
import sys
import re
import subprocess
from paths import Url,UrlCompatible
lastSeleniumPort:int=4000
hasJavascriptTricksRE:typing.Pattern=None


WebFetchCallback=typing.Union[
    typing.Callable[[typing.Any],None],
    typing.Callable[[Url,str],None],
    typing.Callable[[typing.Any],None],
    typing.Callable[[Url,str],None]]


hasJavascriptTricksRE=re.compile(
    r"""(innerhtml\s*=)|(document[.]write\s*\()|(<script[^>]*src="[^"]+"[^>]*>)""", # noqa: E501 # pylint: disable=line-too-long
    re.IGNORECASE)


class WebFetch:
    """
    Fetches a web resource.

    If it appears to be generated by javascript, will get using
    browser via selenium.
    """

    lastSeleniumPort:int=3100

    def __init__(self,
        browser:str='firefox',
        remoteIp:typing.Optional[str]=None,
        port:typing.Optional[int]=None,
        startSeleniumNow:bool=False,
        noSelenium:bool=False):
        """
        If remoteIp is unspecified, will automatically create a local selenium
        server and attach to it

        :param startSeleniumNow: is used to speed things up if you know you'll
            be using selenium
        :param noSelenium: will force the simple html even if javascript tricks
            are detected
        """
        if port is None:
            port=self.lastSeleniumPort
            self.lastSeleniumPort+=1
        if remoteIp is None:
            remoteIp='localhost'
        else:
            # sanity check
            startSeleniumNow=False
        self.seleniumVersion:str='1.0.1'
        self.p:str=None
        self.queue:typing.List[typing.Tuple[WebFetchCallback,Url,bool]]=[]
        self.browser:str=browser
        self.remoteIp:typing.Optional[str]=remoteIp
        self.port:typing.Optional[int]=port
        self.noSelenium:bool=noSelenium
        self.debug:int=1 # 0=none 1=error 2=warning 3=info
        self.failoverOnGeneratedPages:bool=True
        self.trickyPages:typing.List[str]=[] # Keep track of pages that employ javascript tricks like document.write(html) # noqa: E501 # pylint: disable=line-too-long
        if startSeleniumNow:
            self._start()

    def _start(self,restartIfRunning:bool=True)->None:
        """
        Start (or restart) a local selenium server
        """
        if restartIfRunning:
            self._stop()
        if self.p is None:
            directory=Path(f'selenium-remote-control-{self.seleniumVersion}')
            jar=directory/ f'selenium-server-{self.seleniumVersion}selenium-server.jar' # noqa: E501 # pylint: disable=line-too-long
            pythonDir=directory/f'selenium-python-client-driver-{self.seleniumVersion}' # noqa: E501 # pylint: disable=line-too-long
            sys.path.append(pythonDir)
            self.p=subprocess.Popen(('java','-jar',jar,'-port ',str(self.port))) # noqa: E501 # pylint: disable=line-too-long

    def enqueue(self,fn:WebFetchCallback,
        urlOrHtml:typing.Union[UrlCompatible,str],
        returnSeleniumObject:bool=False
        )->None:
        """
        if returnSeleniumObject
            calls fn(selenium.selenium) passing a Selenium RC object
        else
            calls fn(url,html)
        """
        self.queue.append((fn,urlOrHtml,returnSeleniumObject))

    def fetchNow(self,urlOrHtml:typing.Union[UrlCompatible,str],
        returnSeleniumObject:bool=False,
        failoverOnGeneratedPages:bool=False)->None:
        """
        A shortcut for those who don't care about the fancy stuff

        returns (data[],mimetype)
        """
        data=[None] # this is to cheat the scope for the inner function
        mime=[None]
        oldFailover=self.failoverOnGeneratedPages
        self.failoverOnGeneratedPages=failoverOnGeneratedPages
        def onDone(url,html):
            data[0]=html
            mime[0]='text/html'
        self.enqueue(onDone,urlOrHtml)
        self.runAll() # blocks until everything is processed
        self.failoverOnGeneratedPages=oldFailover
        return (data[0],mime[0])

    def runNext(self)->None:
        """
        run the next fetch in the queue
        """
        retval=None
        if self.queue:
            if self.debug>=3:
                print('runNext - queue empty')
            return retval
        fn,url,returnSeleniumObject=self.queue.pop(0)
        urlCut=url.split('/')
        domain='/'.join(urlCut[0:3])
        page='/'.join(urlCut[3:])
        html=None
        urlDenotationPos=url.find('://')
        if urlDenotationPos<3 or urlDenotationPos>7:
            if self.debug>=3:
                print('accepting html, not url')
            # they gave us data, not a url
            html=url
            if not returnSeleniumObject:
                # TODO: Somehow turn this into a selenium.selenium object
                #  call fn
                retval=''
            else:
                retval=fn('',html)
        elif (not returnSeleniumObject) and domain not in self.trickyPages:
            # Lets see if we can get away with the fast way
            if self.debug>=3:
                print('attempting urllib fetch of',url)
            import urllib.request
            import urllib.parse
            import urllib.error
            f=urllib.request.urlopen(url)
            if f is not None:
                html=f.read().decode('utf-8','ignore')
                f.close()

                if self.noSelenium:
                    retval=fn(url,html)
                else:
                    if (not self.failoverOnGeneratedPages) \
                        or hasJavascriptTricksRE.search(html) is None:
                        #
                        retval=fn(url,html)
                    else:
                        # There were JavaScript tricks employed.
                        # Must use Selenium to decode page.
                        if self.debug>=2:
                            print('There were JavaScript tricks employed on this page.') # noqa: E501 # pylint: disable=line-too-long
                            print('You must use Selenium to decode it.')
                        self.trickyPages.append(domain)
                        html=False
            else:
                if self.debug>=3:
                    print('fringe case')
        if html is None:
            # Fetch page with Selenium
            self._start(False)
            sel=selenium(self.remoteIp,self.port,'*'+self.browser,domain)
            sel.start()
            sel.open(page)
            sel.wait_for_page_to_load(10000)
            if returnSeleniumObject:
                retval=fn(sel)
            else:
                print(dir(sel))
                retval=fn(url,sel)
            sel.stop()
        return retval

    def runAll(self)->None:
        """
        fetch all of the items in the queue right now
        """
        while self.runNext() is not None:
            pass

    def __del__(self)->None:
        self._stop()

    def _stop(self)->None:
        if self.p is not None:
            try:
                import win32api # type: ignore
                import win32con # type: ignore
                print('Stopping server on local windows system.')
                try:
                    handle=win32api.OpenProcess(
                        win32con.PROCESS_TERMINATE,0,self.p.pid)
                    if handle:
                        win32api.TerminateProcess(handle,0)
                        win32api.CloseHandle(handle)
                except Exception as e:
                    print(e)
            except ImportError as e:
                print('Not on windows.  Stopping local server posix style. \n\t'+str(e)) # noqa: E501 # pylint: disable=line-too-long
                os.kill(self.p.pid)
            self.p=None

    def cmdline(self,argv:typing.Optional[typing.Iterable[str]]=None)->int:
        """
        Call into this class like it's a command line.

        Don't forget that argv[0] is the calling app's name.
        (You can set it to "" if you want to.)
        Don't forget that argv[0] is the calling app's name.
        (You can set it to "" if you want to.)

        if argv is unspecified, will get it from the app's
        command line.
        """
        if argv is None:
            argv=sys.argv
        printhelp=False
        output='.'
        if len(argv)<2:
            printhelp=True
        else:
            for arg in argv[1:]:
                if arg[0]=='-':
                    if arg[1]=='-':
                        arg=arg[2:].split('=',1)
                        if arg[0]=='output':
                            if len(arg)>1:
                                output=arg[1]
                            else:
                                output='.'
                        elif arg[0]=='help':
                            printhelp=True
                            break
                        else:
                            print('ERR: Unknown arg "--'+arg[0]+'"')
                            printhelp=True
                            break
                    else:
                        print('ERR: Unknown arg "'+arg+'"')
                        printhelp=True
                        break
                else:
                    url=arg
                    stuff,mimetype=self.fetchNow(url)
                    url=url\
                        .replace('/','_SLASH_')\
                        .replace(':','_COLON_')\
                        .replace('.','_DOT_')
                    f=Path(output)/url
                    f.write_text(stuff,'utf-8')

        if printhelp:
            if len(argv)<2 or argv[0] is None or argv[0]=='':
                programName='python WebFetch.py'
            else:
                programName=argv[0].strip()
            print('USAGE:\n\t'+programName+' [options] url [...]')
            print('OPTIONS:')
            print('\t--output=dir .......... where to put the results')
            print('\t--help ................ print this help')


if __name__ == '__main__':
    WebFetch().cmdline()

    WebFetch().cmdline()
