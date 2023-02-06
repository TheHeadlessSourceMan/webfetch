"""
This has been merged into htmlTools
"""
import typing
from htmlTools import Webpage


def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    w=Webpage('edmundlloydfletcher.blogspot.com')
    #print('\n'.join([url for name,url in w.linkReIter(urlRe=r""".*20[0-9]{2}_[0-9]{2}_[0-9]{2}_archive.html""")]))
    squishyRe=r"""
    <a href="(?P<url>(?p<proto>[^:]*(?:://))[^"]*)">
    """
    w.squishyHtmlRe(squishyRe)
    return 0


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
