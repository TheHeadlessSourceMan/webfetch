#!/usr/bin/python
"""
A webpageGetter tool for retreiving old webpages form
online backup services (like "wayback machine")
"""
import os
import datetime
from .webpageGetter import WebpageGetter


class OnlineBackupService(WebpageGetter):
    """
    Represents a single backup service
    """

    def __init__(self,xmlConfig=None):
        """
        xmlConfig is a pig-xml.  It must all be in the same order
            as expeceted, or... kaboom!
        <OnlineBackupService name="" href="">descr</OnlineBackupService>
        """
        WebpageGetter.__init__(self)
        self.canGetByDate=False
        if xmlConfig is not None:
            xmlConfig=xmlConfig.strip().rsplit('</OnlineBackupService',1)[0].split(' ',1)[-1] # noqa: E501 # pylint: disable=line-too-long
            self.description=xmlConfig.rsplit('>',1)[-1].strip()
            xmlConfig=xmlConfig.split('>',1)[0].split('"') # [name=][name][ href=][href] # noqa: E501 # pylint: disable=line-too-long
            self._url=xmlConfig[3].strip()
            self.name=xmlConfig[1].strip()
            self.canGetByDate=(self._url.find('%d')>=0)

    def get(self,url,date=None):
        """
        get something from the backup service
        """
        backupUrl=self._url.replace('%u',url)
        if self.canGetByDate:
            if date is None:
                date=str(datetime.datetime.now())
            elif not isinstance(date,str):
                date=str(date)
            backupUrl=backupUrl.replace('%d',date)
        from webFetch import WebFetch
        print('Fetching',url,'...')
        (data,mimetype)=WebFetch.WebFetch().fetchNow(url)
        print('Got back',len(data),'bytes of',mimetype)
        return data


class OnlineBackupServices(WebpageGetter):
    """
    Look for data in an online backup service
    """
    def __init__(self):
        WebpageGetter.__init__(self)
        self._services={}
        filename=(os.path.abspath(__file__).rsplit(os.sep,1)[0])\
            +os.sep+'OnlineBackupServices.xml'
        self.load(filename)

    def load(self,filename:str):
        """
        Load the data
        """
        f=open(filename,'r',encoding='utf-8',errors='ignore')
        for line in f:
            line=line.strip()
            if line.startswith('<OnlineBackupService '):
                service=OnlineBackupService(line)
                self._services[service.name]=service

    def get(self,url,date=None,servicePreference=None):
        """
        servicePreference can be a single service or an array in order
            (a "service" in that array can either be the name of the
            service or the OnlineBackupService object itsself)
        """
        if servicePreference is None:
            servicePreference=list(self._services.keys())
        elif not isinstance(servicePreference,list):
            servicePreference=[servicePreference]
        for service in servicePreference:
            if isinstance(service,str):
                service=self._services[service]
            if date is None or service.canGetByDate:
                result=service.get(url,date)
                if result is not None:
                    return result
        if date is not None:
            # we didn't find anything in the date-matching
            # OnlineBackupServices, so lets try the others
            for service in servicePreference:
                result=service.get(url)
                if result is not None:
                    return result
        return None

    def cmdline(self,argv=None):
        """
        Call into this class like it's a command line.

        Don't forget that argv[0] is the calling app's name.
        (You can set it to "" if you want to.)

        if argv is unspecified, will get it from the app's
        command line.
        """
        # Use the Psyco python accelerator if available
        # See:
        #     http://psyco.sourceforge.net
        try:
            import psyco # type: ignore
            psyco.full() # accelerate this program
        except ImportError:
            pass
        if argv is None:
            import sys
            argv=sys.argv
        printhelp=False
        service='all'
        output='.'
        date=None
        if len(argv)<2:
            printhelp=True
        else:
            for arg in argv[1:]:
                if arg[0]=='-':
                    if arg[1]=='-':
                        arg=arg[2:].split('=',1)
                        if arg[0]=='service':
                            if len(arg)>1:
                                service=arg[1]
                            else:
                                service='all'
                        elif arg[0]=='output':
                            if len(arg)>1:
                                output=arg[1]
                            else:
                                output='.'
                        elif arg[0]=='date':
                            if len(arg)>1:
                                date=arg[1]
                            else:
                                date=None
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
                    if service=='all':
                        service=None
                    elif service not in list(self._services):
                        print('ERR: Unknown service "'+service+'"')
                        printhelp=True
                    else:
                        stuff=self.get(url,date,service)
                        url=url\
                            .replace('/','_SLASH_')\
                            .replace(':','_COLON_')\
                            .replace('.','_DOT_')
                        f=open(output+os.sep+url,'wb')
                        f.write(stuff)
                        f.close()

        if printhelp:
            if len(argv)<1 or argv[0] is None or argv[0]=='':
                programName='python pybookmarks.py'
            else:
                programName=argv[0].strip()
            print('USAGE:\n\t'+programName+' [options] url [...]')
            print('OPTIONS:')
            print('\t--service[=name] ...... the service to try (default=all)')
            print('\t--output=dir .......... where to put the results')
            print('\t--date=when ........... what archive date to shoot for')
            print('\t--help ................ print this help')
            print('KNOWN SERVICES:')
            for service in list(self._services.values()):
                print('\t'+service.name+' - '+service.description)


if __name__ == '__main__':
    OnlineBackupServices().cmdline()
