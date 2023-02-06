#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
A tool for managing (fetching,caching,etc) of online data
"""
import typing
import datetime
from paths import Url


class Data:
    """
    Some data fetched from the web
    """

    def __init__(self):
        self.url:typing.Optional[Url]=None
        self.lastFetchDate:typing.Optional[datetime.datetime]=None
        self.sourceDate:typing.Optional[datetime.datetime]=None
        self.data:typing.Optional[bytes]=None

    @property
    def source(self)->Url:
        return self.url
    @property
    def origin(self)->Url:
        return self.url


class WebDataManager:
    """
    A tool for managing (fetching,caching,etc) of online data
    """

    def __init__(self):
        pass

    def fetch(self,url,refetchIfOlder=None):
        """
        :param url: full url to fetch
        :param refetchIfOlder: refetch if the data is older than this date
            (if None, don't care as long as we have it)
        """
        pass


def cmdline(args):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printhelp=False
    if not args:
        printhelp=True
    else:
        for arg in args:
            if arg.startswith('-'):
                arg=[a.strip() for a in arg.split('=',1)]
                if arg[0] in ['-h','--help']:
                    printhelp=True
                else:
                    print('ERR: unknown argument "'+arg[0]+'"')
            else:
                print('ERR: unknown argument "'+arg+'"')
    if printhelp:
        print('Usage:')
        print('  webDataManager.py [options]')
        print('Options:')
        print('   NONE')


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
