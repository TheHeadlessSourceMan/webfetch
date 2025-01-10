#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
gets the mime type for a given file
"""
import typing
import os
from paths import URLCompatible, asUrl


_SIMPLE_MIME_TABLE={
    'jpg':'image/jpeg',
    'jpeg':'image/jpeg',
    'jpe':'image/jpeg',
    'gif':'image/gif',
    'png':'image/png',
    'txt':'text/plain',
    'readme':'text/plain',
    'css':'text/css',
    'htm':'text/html',
    'html':'text/html',
    'xhtml':'text/html',
    'svg':'image/svg+xml',
    'ico':'image/x-icon',
    'js':'application/javascript',
    'xml':'application/xml',
    'zip':'application-x/zip',
}


def file2mime(
    filename:URLCompatible,
    data:typing.Optional[bytes]=None,
    useOS:bool=False
    )->typing.Optional[str]:
    """
    get the mime type based on filename (or data content)

    :param useOS: see if the os can identify this mime type if we cannot

    Can return None if unknown
    """
    ret=None
    filename=asUrl(filename)
    ext=filename.ext
    if ext in _SIMPLE_MIME_TABLE:
        ret=_SIMPLE_MIME_TABLE[ext]
    elif useOS:
        ret=osFile2Mime(filename,data)
    if ret is None:
        # do a little magic number trickery
        if data is not None and data:
            if data.startswith(b'<'):
                if data.find(b'<html')>=0:
                    ret=_SIMPLE_MIME_TABLE['html']
                else:
                    ret=_SIMPLE_MIME_TABLE['xml']
            elif data.startswith(b'PK'):
                ret=_SIMPLE_MIME_TABLE['zip']
    return ret


def osFile2Mime(
    filename:URLCompatible,
    data:typing.Optional[bytes]=None
    )->str:
    """
    See if the os can identify a mime type.

    NOTE: you probably want to call file2mime(...,useOS=True)
    instead, as it may be faster
    """
    filename=asUrl(filename)
    ext=filename.ext
    _=data
    if os.name=='nt': # this is windows
        return _windowsFile2Mime(ext)
    raise NotImplementedError()


_windowsFileTypeTable:typing.Optional[typing.Dict[str,str]]=None
def _windowsFile2Mime(ext:str):
    global _windowsFileTypeTable
    if _windowsFileTypeTable is None:
        import windowsFileTypes
        _windowsFileTypeTable={}
        for k,v in windowsFileTypes.FileTypes().regMimeTypes.items():
            for extn in v:
                _windowsFileTypeTable[extn[1:]]=k
    if ext in _windowsFileTypeTable:
        return _windowsFileTypeTable[ext]
    return None


def cmdline(args:typing.Iterable[str])->int:
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
                av=[a.strip() for a in arg.split('=',1)]
                if av[0] in ['-h','--help']:
                    printhelp=True
                else:
                    print('ERR: unknown argument "'+av[0]+'"')
            else:
                file2mime(arg,None,True)
    if printhelp:
        print('Usage:')
        print('  file2mime.py [options] file')
        print('Options:')
        print('   NONE')
        return -1
    return 0


if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))
