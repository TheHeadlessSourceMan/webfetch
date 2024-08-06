"""
This module is for "WebFatch", a tool for fetching webpage contents.
It can automatically detect and render generated webpage contents like
"document.write(stuff)" using your web browser of choice.

REQUIRES:
	Selenium RC
	http://seleniumhq.org/projects/remote-control/

USAGE:
	import webFetch
	def processResults(url,html):
		do something
	wf=webFetch.WebFetch()
	wf.enqueue(processResults,url1)
	wf.enqueue(processResults,url2)
	wf.enqueue(processResults,url3)
	wf.runAll()
"""
from .WebFetch import *
from .webfetchQT import *
from .WebForm import *
from .WebSearch import *
