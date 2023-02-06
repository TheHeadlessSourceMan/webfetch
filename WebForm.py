#!/usr/bin/python
"""
tool to fill out web forms
"""
import typing
import re
from paths import UrlCompatible,Url
import urllib.request
import urllib.parse
import urllib.error


formExpr=re.compile("""<form(?P<attributes>[^>]*)>(?P<contents>.*?)</form>""",re.IGNORECASE|re.DOTALL)
formElementExpr=re.compile(r"""<(?P<tagName>[^/][^\s>]*)(?P<attributes>([^/>])*)""")
attributeExpr=re.compile(r"""\s+(?P<key>[^=]*)=\s*(?P<value>(?:"[^"]*"|'[^']*'|[^\s>]*))""")
formElements=['input','select','textarea']


class WebForm:
	"""
	This class can read/write/fill-out/submit html forms.

	HINT: To get ALL forms on an html page use the global function getForms(html)
	"""

	def __init__(self,
		textOrUrl:typing.Optional[UrlCompatible]=None,
		url:typing.Optional[UrlCompatible]=None,
		method:typing.Optional[str]=None,
		elements:typing.Optional[str]=None,
		baseUrl:typing.Optional[UrlCompatible]=None):
		"""
		if html is specified AND other values, then it will parse the
		html first, then replace the selected values
		"""
		self.elements={}
		self.attributes={}
		self.baseUrl=None
		pos=textOrUrl.find('://')
		if textOrUrl is None:
			self.html=None
		if pos is not None and 7>pos>3: # url
			self.baseUrl=textOrUrl
			f=urllib.request.urlopen(textOrUrl)
			if f is not None:
				self.html=f.read().decode('utf-8','ignore')
				f.close()
			else:
				self.html=None
		else: # the data itsself
			self.html=textOrUrl
		if self.html is not None:
			f=formExpr.search(self.html)
			if f:
				self.html=f.group(0)
				attrs=f.group(1)
				els=f.group(2)
				for a in attributeExpr.finditer(attrs):
					val=a.group(2).strip()
					if val[0]=='"' or val[0]=="'":
						val=val[1:-1]
					self.attributes[a.group(1)]=val
				for el in formElementExpr.finditer(els):
					if el.group(1).strip() in formElements:
						name=None
						val=None
						for a in attributeExpr.finditer(el.group(2)):
							if a.group(1)=='name':
								name=a.group(2).strip()
								if name[0]=='"' or name[0]=="'":
									name=name[1:-1]
							elif a.group(1)=='value':
								val=a.group(2).strip()
								if val[0]=='"' or val[0]=="'":
									val=val[1:-1]
							if name is not None and val is not None:
								self.elements[name]=val
								break
			else:
				print('No form found in html.')
		if elements is not None:
			self.setElements(elements)
		if url is not None:
			self.attributes['action']=url
		if method is not None:
			self.attributes['method']=method
		if baseUrl:
			self.baseUrl=baseUrl

	def getMethod(self)->str:
		"""
		get the form method
		"""
		if 'method' not in self.attributes:
			return 'get'
		if self.attributes['method'].lower()=='post':
			return 'post'
		return 'get'

	def getElement(self,
		name:str,
		valueIfMissing:typing.Any=None
		)->typing.Any:
		"""
		get a form element
		"""
		if name in self.elements:
			return self.elements[name]
		return valueIfMissing

	def setElement(self,
		name:str,
		value:typing.Any,
		createIfMissing:bool=True
		)->None:
		"""
		set a form element
		"""
		if createIfMissing or name in self.elements:
			self.elements[name]=value

	def setElements(self,
		toThis:typing.Dict[str,typing.Any],
		createIfMissing:bool=True)->None:
		"""
		set a series of form elements
		"""
		for k,v in list(toThis.items()):
			self.setElement(k,v)

	def getUrl(self)->Url:
		"""
		get the form url
		"""
		url=None
		if 'action' in self.attributes:
			url=self.attributes['action']
			pos=url.find('://')
			if self.baseUrl is not None and (pos is None or pos>7 or pos<3): # complete relative url
				url=url.strip()
				if url[0]=='/':
					url=url[1:]
					base=self.baseUrl.split('/')
					if len(base)>3:
						base=base[0:-1]
					base='/'.join(base)
					url=base+'/'+url
				else:
					url=self.baseUrl+url
		return url

	def currentCgi(self)->str:
		"""
		get the current cgi url
		"""
		cgi=''+str(self.getUrl())
		combiner='?'
		for k,v in list(self.elements.items()):
			# TODO: Url encode each key and value
			cgi=cgi+combiner+urllib.parse.quote_plus(k)+'='+urllib.parse.quote_plus(v)
			combiner='&'
		return cgi

	def getHtml(self)->str:
		"""
		If this form was generated from some original html, return it.
		Otherwise, return some newly-created html.
		"""
		if self.html is not None:
			return self.html
		return self.createHtml()

	def createHtml(self,justFormTag:bool=True)->str:
		"""Creates a new html form"""
		if not justFormTag:
			html='<head>\n\t<title>Form</title>\n</head><body><form'
		else:
			html='<form'
		if not justFormTag:
			html=html+'</form>\n</body>\n</html>'
		else:
			html=html+'</form>'
		return html

	def submit(self)->str:
		"""
		Returns the html fetched
		"""
		retval=None
		#TODO: May want to use curl or something instead if its available
		url=self.currentCgi()
		if self.getMethod()=='post':
			url=url.split('?',1)
			f,_=urllib.request.urlretrieve(url[0],data=url[1])
		else:
			f=urllib.request.urlopen(url)
		if f is not None:
			retval=f.read().decode('utf-8','ignore')
			f.close()
		return retval

	def __repr__(self)->str:
		"""
		get a string representation of this form
		"""
		return self.getHtml()


def getForms(html:str)->typing.Iterable[WebForm]:
	"""
	get all forms from an html page
	"""
	forms=[]
	for g in formExpr.finditer(html):
		forms.append(WebForm(g.group(0)))
	return forms


if __name__ == '__main__':
	import sys
	textOrUrl=None
	name2val={}
	printHtml=False
	printCgi=False
	printSubmitResults=False
	submitForm=False
	err=False
	for argv in sys.argv[1:]:
			if argv[0]=='-':
				if argv[1]=='s':
						submitForm=True
				elif argv[1]=='r':
						submitForm=True
						printSubmitResults=True
				elif argv[1]=='h':
						printHtml=True
				elif argv[1]=='c':
						printCgi=True
				else:
						print('Unknown argument: '+argv)
						err=True
			elif textOrUrl is None:
				textOrUrl=argv
			else:
				name=argv.split('=',1)
				if len(name)>1:
						val=name[-1]
				else:
						val=''
				name=name[0]
				name2val[name]=val
	if textOrUrl is None:
			print('Missing text or url.')
	if err:
			print('USAGE: WebForm.py [-s,-h,-c,-r] "url or text" [name=value] [...]')
			print('\t-h ........... return the form as html')
			print('\t-c ........... return the cgi string for sumitting the form')
			print('\t-r ........... submit form and return results')
			print('\t-s ........... submit form')
	else:
			f=WebForm(textOrUrl,elements=name2val)
			if printHtml:
				print('Html Form:')
				print('----------')
				print(f.getHtml())
			if printCgi:
				print('Cgi Request:')
				print('------------')
				print(f.currentCgi())
			if submitForm:
				submitResults=f.submit()
			if printSubmitResults:
				print('Submit Results:')
				print('---------------')
				print(submitResults)
