"""
This fetches a webpage using a headless (invizible) browser.

It uses QT and the webkit browser it comes with

TODO integrate with webfetch
TODO working on browser pool, but qt not taking kindly to threads :((
TODO screenshot works!  but we need to somehow give it a min browser width
"""
import sys
import time
import threading
from PIL import Image # type: ignore
from PyQt4.QtGui import QApplication,QImage,QPainter # type: ignore # noqa: E501 # pylint: disable=line-too-long,import-error
from PyQt4.QtCore import QUrl # type: ignore # pylint: disable=import-error
from PyQt4.QtWebKit import QWebPage # type: ignore # noqa: E501 # pylint: disable=line-too-long,import-error


class _WfBrowser:
    """
    Represent a qt webkit browser

    See also:
        http://stackoverflow.com/questions/1197172/how-can-i-take-a-screenshot-image-of-a-website-using-python#12031316
    """

    def __init__(self,pool=None):
        self.pool=pool
        self.app=None
        self._busy=False
        self.callback=None
        self.url=None
        self.returnType=None
        self.qWebpage=None

    def __del__(self):
        self.app.quit()

    def fetch(self,url,callback,returnType='html',block=True):
        """
        returnType is the type of data you want back it can be:
            'html' to get the resultant html after scripting
            'txt' to get that converted to plain text
            'jpeg','png', or 'pdf' to get a screenshot of it
                or any other PIL-saveable image format, really
                http://pillow.readthedocs.io/en/3.1.x/handbook/image-file-formats.html
        """
        if self.app is None:
            self.app=QApplication(sys.argv)
            self.qWebpage=QWebPage(self.app)
            self.qWebpage.loadFinished.connect(self._onLoaded)
        if self._busy:
            raise Exception("Browser is busy!")
        self._busy=True
        self.returnType=returnType
        self.url=url
        self.callback=callback
        self.qWebpage.mainFrame().load(QUrl(url))
        self.app.exec_()
        if block:
            self.wait()

    def wait(self):
        """
        wait for the browser to complete
        """
        while self._busy:
            time.sleep(0.1)

    def _poolThread(self):
        while True:
            if self.pool is None:
                break
            (url,callback,fileType)=self.pool._queue.get() # noqa: E501 # pylint: disable=line-too-long,protected-access
            self.fetch(url,callback,fileType,block=True)
            self.pool._queue.task_done() # noqa: E501 # pylint: disable=line-too-long,protected-access

    def _onLoaded(self):
        #self.app.quit() # not sure I want to do this here
        frame=self.qWebpage.mainFrame()
        if self.returnType=='txt':
            data=frame.toPlainText()
        elif self.returnType in ['jpeg','png','pdf']:
            self.qWebpage.setViewportSize(frame.contentsSize())
            qImage=QImage(self.qWebpage.viewportSize(),QImage.Format_ARGB32)
            painter=QPainter(qImage)
            frame.render(painter)
            painter.end()
            pilImg=Image.fromqimage(qImage)
            import io
            f=io.StringIO()
            pilImg.save(f,format=self.returnType)
            data=f.getvalue()
            f.close()
        else:
            data=frame.toHtml()
        self.callback(self.url,data)
        self._busy=False


class BrowserPool:
    """
    The idea is this would own a number of headless browsers
    and you could just submit a job and get notified when done
    """
    def __init__(self,numBrowsers=4):
        import queue
        self._browsers=[]
        self._browserThreads=[]
        self._queue=queue.Queue()
        for _ in range(numBrowsers):
            browser=_WfBrowser(self)
            self._browsers.append(browser)
            thread=threading.Thread(target=browser._poolThread)
            self._browserThreads.append(thread)
            thread.start()

    def addJob(self,url,callback,fileType='html'):
        """
        Note that all results could come back in
        different threads
        """
        self._queue.put((url,callback,fileType))

    def wait(self):
        """
        this waits for the queue to be empty and all threads to
        call _queue.task_done()
        """
        self._queue.join()


if __name__=='__main__':
    if len(sys.argv)<2:
        print('USEAGE:\n\twebfetchQT.py [options] url [url...]')
        print('OPTIONS:')
        print('\tNONE')#print '\t--format=[html,txt,jpeg,png]'
    else:
        pool=BrowserPool()
        fileType='html'
        counter=[1]
        def callback(url,data):
            """
            called when job obtains more date
            """
            filename=f'download_{counter[0]}.{fileType}'
            print('saving %s => %s'%filename,url)
            f=open(filename,'wb')
            f.write(data.encode('utf-8'))
            f.close()
            counter[0]=counter[0]+1
        for arg in sys.argv[1:]:
            pool.addJob(arg,callback,fileType)
        pool.wait()
