#!/usr/bin/python
"""
By: K.C.Eilander
This program fetches a youtube video.
"""
import os
import urllib
import urllib.parse
from webFetch import WebFetch
defaultMediaFormat='mp4'


def youtubeFetch(
    idOrUrl,
    filename=None,
    mediaFormat=defaultMediaFormat,
    outDir='.'):
    """
    You can send in either the parameters or an array where each element is
    a set of parameters.
    """
    wf=WebFetch.WebFetch(noSelenium=True)
    wf.catalog=[]
    if hasattr(idOrUrl,'__iter__') and not isinstance(idOrUrl,str):
        counter=1
        for item in idOrUrl:
            __youtubeFetch(counter,wf,*item)
            outDir=item[3]
            counter=counter+1
    else:
        __youtubeFetch(1,wf,idOrUrl,filename,mediaFormat,outDir)
    wf.runAll()
    _createIdexPage(outDir,wf.catalog)


def _createIdexPage(outDir,catalog):
    title=outDir.strip()
    while title and title[0]=='.':
        title=title[1:]
    title=title.replace('/',' ').strip()
    html=[]
    html.append('<html>')
    html.append('<head>')
    html.append('\t<title>'+title+'</title>')
    html.append('\t<style type="text/css">')
    html.append('\t\tbody, div {margin-left:2cm;margin-right:2cm}')
    html.append('\t\t.lesson {width:120;height:200;float:left;display:inline-block;margin:3px;background:#888888}') # noqa: E501 # pylint: disable=line-too-long
    html.append('\t\timg {border:0px}')
    html.append('\t\th1 {text-decoration:underline}')
    html.append('\t\ta {text-decoration:none}')
    html.append('\t</style>')
    html.append('</head>\n<body>')
    html.append('\t<h1>'+title+'</h1>')
    html.append('\t<div>')
    for cat in catalog:
        # cat is (name,thumbnail,video)
        html.append('\t\t<div class="lesson"><a href="'+cat[2]+'"><img src="'+cat[1]+'" /><br />'+cat[0]+'</a></div>') # noqa: E501 # pylint: disable=line-too-long
    html.append('\t</div>')
    html.append('</body>')
    html.append('</html>')
    f=open(outDir+os.sep+'index.html','w',encoding='utf-8')
    f.write('\n'.join(html))
    f.close()


def __youtubeFetch(
    counter,
    wf,
    idOrUrl,
    filename,
    mediaFormat=defaultMediaFormat,
    outDir='.'):
    """
    Helper function to fetch youtubes
    """
    filename=filename.split('.',1)[0]
    def gotVideo(url,data):
        if not os.path.isdir(outDir):
            os.makedirs(outDir)
        f=open(outDir+os.sep+str(counter)+'-'+filename+'.'+mediaFormat,'wb')
        f.write(data)
        f.close()
    def gotThumbnail(url,data):
        if not os.path.isdir(outDir):
            os.makedirs(outDir)
        f=open(outDir+os.sep+str(counter)+'-'+filename+'.jpg','wb')
        f.write(data)
        f.close()
    def gotVideoPage(url,data):
        """
        Get a video page

        The flashvars are something like:ttsurl=http%3A%2F%2Fwww.youtube.com%2Fapi%2Ftimedtext%3Fsparams%3Dasr_langs%252Ccaps%252Cexpire%252Cv%26asr_langs%3Den%252Cja%26caps%3Dasr%26expire%3D1317358800%26key%3Dyttt1%26signature%3DDDA04BEEB92EA496E656DE92F9C38DEE5D8841EC.036542E5C4E031ABD6422E77E10C19BA7A856131%26hl%3Den
            fexp=907605%2C910600
            ptk=khanacademy%252Buser
            enablecsi=1
            allow_embed=1
            rvs=view_count%3D290207%26author%3Dkhanacademy%26length_seconds%3D%2528521%252C%2529%26id%3DXoEn1LfVoTo%26title%3DEquations%2B2%2Cview_count%3D200724%26author%3Dkhanacademy%26length_seconds%3D%2528533%252C%2529%26id%3Df15zA0PhSek%26title%3DEquations%2B3%2Cview_count%3D356872%26author%3Dkhanacademy%26length_seconds%3D%2528458%252C%2529%26id%3D9IUEk9fn2Vs%26title%3DAlgebra%253A%2BLinear%2BEquations%2B4%2Cview_count%3D370536%26author%3Dkhanacademy%26length_seconds%3D%2528447%252C%2529%26id%3DbAerID24QJ0%26title%3DAlgebra%253A%2BLinear%2BEquations%2B1%2Cview_count%3D11467%26author%3Dexpertmathstutor%26length_seconds%3D%2528577%252C%2529%26id%3D3PAZs0R0yfk%26title%3DMath%2B-%2BAlgebra%2B-%2B%2BSolving%2BSimple%2BEquations%2Cview_count%3D17776%26author%3Dkhanacademy%26length_seconds%3D%2528644%252C%2529%26id%3DzlJ20s5d9To%26title%3DNavigating%2Bthe%2BKhan%2BAcademy%2BVideo%2BLibrary%2Cview_count%3D125418%26author%3Dkhanacademy%26length_seconds%3D%2528365%252C%2529%26id%3DDopnmxeMt-s%26title%3DAlgebra%253A%2BLinear%2BEquations%2B2%2Cview_count%3D130936%26author%3Dkhanacademy%26length_seconds%3D%2528125%252C%2529%26id%3D6A07Pj71TUA%26title%3DBill%2BGates%2Btalks%2Babout%2Bthe%2BKhan%2BAcademy%2Bat%2BAspen%2BIdeas%2BFestival%2B2010%2Cview_count%3D405735%26author%3Dkhanacademy%26length_seconds%3D%25281265%252C%2529%26id%3D1xSQlwWGT8M%26title%3DIntroduction%2Bto%2Bthe%2Batom
            vq=auto
            autohide=2
            csi_page_type=watch5ad
            keywords=algebra%2Cintroduction
            cr=US
            cc3_module=http%3A%2F%2Fs.ytimg.com%2Fyt%2Fswfbin%2Fsubtitles3_module-vflg3yyBD.swf
            ad3_module=http%3A%2F%2Fs.ytimg.com%2Fyt%2Fswfbin%2Fad3-vflCxRzhp.swf
            gut_tag=%2F4061%2Fytpwmpu%2Fmain_3687
            ad_flags=0
            fmt_list=45%2F1280x720%2F99%2F0%2F0%2C22%2F1280x720%2F9%2F0%2F115%2C44%2F854x480%2F99%2F0%2F0%2C35%2F854x480%2F9%2F0%2F115%2C43%2F640x360%2F99%2F0%2F0%2C34%2F640x360%2F9%2F0%2F115%2C18%2F640x360%2F9%2F0%2F115%2C5%2F320x240%2F7%2F0%2F0
            length_seconds=666
            enablejsapi=1
            theme=dark
            tk=lBB26Da_FoBoJ-6B64uFxtvMVrlsKMve-JDQuw91OdIx1H_UQPoS6A%3D%3D
            plid=AASuG7Pn0U3tuUbS
            cc_font=Arial+Unicode+MS%2C+arial%2C+verdana%2C+_sans
            ad_tag=http%3A%2F%2Fad-g.doubleclick.net%2Fpfadx%2Fcom.ytpwmpu.education%2Fmain_3687%3Bsz%3DWIDTHxHEIGHT%3Bmpvid%3DAASuG7PoVGGWeij5%3B%21c%3D3687%3Bkvid%3D9Ek61w1LxSc%3Bytexp%3D907605.910600%3Bkpid%3D3687%3Bkga%3D-1%3Bkgg%3D-1%3Bkcr%3Dus%3Bkvz%3D205%3Blongform%3D1%3Bklg%3Den%3Bkr%3DF%3Bkpu%3Dkhanacademy%3Bkhd%3D1%3Bko%3Dy%3Bafc%3D1%3Bytps%3Ddefault%3Bytvt%3Dw%3Bafct%3Dsite_content%3Bkt%3DK%3Bu%3D9Ek61w1LxSc%7C3687%3Bdc_dedup%3D1%3B%3Bk2%3D174%3Bk3%3D174%3Bk2%3D688%3Bk4%3D688%3Bk2%3D436%3Bk5%3D174_688_436
            cc_asr=1
            url_encoded_fmt_stream_map=url%3Dhttp%253A%252F%252Fo-o.preferred.dfw06g01.v1.lscache4.c.youtube.com%252Fvideoplayback%253Fsparams%253Did%25252Cexpire%25252Cip%25252Cipbits%25252Citag%25252Cratebypass%25252Ccp%2526fexp%253D907605%25252C910600%2526itag%253D45%2526ip%253D209.0.0.0%2526signature%253D2B94C2299559A3A9A9ED689D16723B43112A8D2A.2DD5D36FB643B2DFB7CB2DB316EEEB6020739156%2526sver%253D3%2526ratebypass%253Dyes%2526expire%253D1317358800%2526key%253Dyt1%2526ipbits%253D8%2526cp%253DU0hQTFNQVl9FSkNOMF9LSlpJOlNlVDdfTDROQUVX%2526id%253Df4493ad70d4bc527%26quality%3Dhd720%26fallback_host%3Dtc.v1.cache4.c.youtube.com%26type%3Dvideo%252Fwebm%253B%2Bcodecs%253D%2522vp8.0%252C%2Bvorbis%2522%26itag%3D45%2Curl%3Dhttp%253A%252F%252Fo-o.preferred.dfw06g01.v15.lscache1.c.youtube.com%252Fvideoplayback%253Fsparams%253Did%25252Cexpire%25252Cip%25252Cipbits%25252Citag%25252Cratebypass%25252Ccp%2526fexp%253D907605%25252C910600%2526itag%253D22%2526ip%253D209.0.0.0%2526signature%253D2F18A021D12C3C3F42630DAE5D4BFFB4A3A33264.3228776C460314157C0C268FA6EF9A4A17DA46B9%2526sver%253D3%2526ratebypass%253Dyes%2526expire%253D1317358800%2526key%253Dyt1%2526ipbits%253D8%2526cp%253DU0hQTFNQVl9FSkNOMF9LSlpJOlNlVDdfTDROQUVX%2526id%253Df4493ad70d4bc527%26quality%3Dhd720%26fallback_host%3Dtc.v15.cache1.c.youtube.com%26type%3Dvideo%252Fmp4%253B%2Bcodecs%253D%2522avc1.64001F%252C%2Bmp4a.40.2%2522%26itag%3D22%2Curl%3Dhttp%253A%252F%252Fo-o.preferred.dfw06g01.v17.lscache3.c.youtube.com%252Fvideoplayback%253Fsparams%253Did%25252Cexpire%25252Cip%25252Cipbits%25252Citag%25252Cratebypass%25252Ccp%2526fexp%253D907605%25252C910600%2526itag%253D44%2526ip%253D209.0.0.0%2526signature%253D1D188C03DDD2104FA0F5C7D501DB4C1E3C1A70F0.308B51CEA3D5375B6B3B46B894FAB47AC55471FA%2526sver%253D3%2526ratebypass%253Dyes%2526expire%253D1317358800%2526key%253Dyt1%2526ipbits%253D8%2526cp%253DU0hQTFNQVl9FSkNOMF9LSlpJOlNlVDdfTDROQUVX%2526id%253Df4493ad70d4bc527%26quality%3Dlarge%26fallback_host%3Dtc.v17.cache3.c.youtube.com%26type%3Dvideo%252Fwebm%253B%2Bcodecs%253D%2522vp8.0%252C%2Bvorbis%2522%26itag%3D44%2Curl%3Dhttp%253A%252F%252Fo-o.preferred.dfw06g01.v11.lscache3.c.youtube.com%252Fvideoplayback%253Fsparams%253Did%25252Cexpire%25252Cip%25252Cipbits%25252Citag%25252Calgorithm%25252Cburst%25252Cfactor%25252Ccp%2526fexp%253D907605%25252C910600%2526algorithm%253Dthrottle-factor%2526itag%253D35%2526ip%253D209.0.0.0%2526burst%253D40%2526sver%253D3%2526signature%253D116E03B86D384A665569CECCEF283606F006EE3A.02C7B8FD68EF9C49307749354E9604CD7279A2CF%2526expire%253D1317358800%2526key%253Dyt1%2526ipbits%253D8%2526factor%253D1.25%2526cp%253DU0hQTFNQVl9FSkNOMF9LSlpJOlNlVDdfTDROQUVX%2526id%253Df4493ad70d4bc527%26quality%3Dlarge%26fallback_host%3Dtc.v11.cache3.c.youtube.com%26type%3Dvideo%252Fx-flv%26itag%3D35%2Curl%3Dhttp%253A%252F%252Fo-o.preferred.dfw06g01.v8.lscache8.c.youtube.com%252Fvideoplayback%253Fsparams%253Did%25252Cexpire%25252Cip%25252Cipbits%25252Citag%25252Cratebypass%25252Ccp%2526fexp%253D907605%25252C910600%2526itag%253D43%2526ip%253D209.0.0.0%2526signature%253DA78E1960E718A583CE7C3E8C32EA791029761228.101F2A93F9E74002759C8EA3D57AEC72A1BAC83F%2526sver%253D3%2526ratebypass%253Dyes%2526expire%253D1317358800%2526key%253Dyt1%2526ipbits%253D8%2526cp%253DU0hQTFNQVl9FSkNOMF9LSlpJOlNlVDdfTDROQUVX%2526id%253Df4493ad70d4bc527%26quality%3Dmedium%26fallback_host%3Dtc.v8.cache8.c.youtube.com%26type%3Dvideo%252Fwebm%253B%2Bcodecs%253D%2522vp8.0%252C%2Bvorbis%2522%26itag%3D43%2Curl%3Dhttp%253A%252F%252Fo-o.preferred.dfw06g01.v15.lscache6.c.youtube.com%252Fvideoplayback%253Fsparams%253Did%25252Cexpire%25252Cip%25252Cipbits%25252Citag%25252Calgorithm%25252Cburst%25252Cfactor%25252Ccp%2526fexp%253D907605%25252C910600%2526algorithm%253Dthrottle-factor%2526itag%253D34%2526ip%253D209.0.0.0%2526burst%253D40%2526sver%253D3%2526signature%253D271151F61217ADD1A830F22734379F389DAD4556.2E2CE5C7D4E998928122F5BD3149AC8D54EFFD36%2526expire%253D1317358800%2526key%253Dyt1%2526ipbits%253D8%2526factor%253D1.25%2526cp%253DU0hQTFNQVl9FSkNOMF9LSlpJOlNlVDdfTDROQUVX%2526id%253Df4493ad70d4bc527%26quality%3Dmedium%26fallback_host%3Dtc.v15.cache6.c.youtube.com%26type%3Dvideo%252Fx-flv%26itag%3D34%2Curl%3Dhttp%253A%252F%252Fo-o.preferred.dfw06g01.v19.lscache8.c.youtube.com%252Fvideoplayback%253Fsparams%253Did%25252Cexpire%25252Cip%25252Cipbits%25252Citag%25252Cratebypass%25252Ccp%2526fexp%253D907605%25252C910600%2526itag%253D18%2526ip%253D209.0.0.0%2526signature%253DB533AB2180E5132FC23885D9A479C3C569DC9BA0.48A205391ADB110EF120DB2103133EB322E3207A%2526sver%253D3%2526ratebypass%253Dyes%2526expire%253D1317358800%2526key%253Dyt1%2526ipbits%253D8%2526cp%253DU0hQTFNQVl9FSkNOMF9LSlpJOlNlVDdfTDROQUVX%2526id%253Df4493ad70d4bc527%26quality%3Dmedium%26fallback_host%3Dtc.v19.cache8.c.youtube.com%26type%3Dvideo%252Fmp4%253B%2Bcodecs%253D%2522avc1.42001E%252C%2Bmp4a.40.2%2522%26itag%3D18%2Curl%3Dhttp%253A%252F%252Fo-o.preferred.dfw06g01.v22.lscache6.c.youtube.com%252Fvideoplayback%253Fsparams%253Did%25252Cexpire%25252Cip%25252Cipbits%25252Citag%25252Calgorithm%25252Cburst%25252Cfactor%25252Ccp%2526fexp%253D907605%25252C910600%2526algorithm%253Dthrottle-factor%2526itag%253D5%2526ip%253D209.0.0.0%2526burst%253D40%2526sver%253D3%2526signature%253D060A674A141BB52D0F61460895E944FEFB5BEC81.CA465ED9A30E64DE4F790A591F20CBC862D57933%2526expire%253D1317358800%2526key%253Dyt1%2526ipbits%253D8%2526factor%253D1.25%2526cp%253DU0hQTFNQVl9FSkNOMF9LSlpJOlNlVDdfTDROQUVX%2526id%253Df4493ad70d4bc527%26quality%3Dsmall%26fallback_host%3Dtc.v22.cache6.c.youtube.com%26type%3Dvideo%252Fx-flv%26itag%3D5
            watermark=http%3A%2F%2Fs.ytimg.com%2Fyt%2Fswf%2Flogo-vfl_bP6ud.swf%2Chttp%3A%2F%2Fs.ytimg.com%2Fyt%2Fswf%2Fhdlogo-vfloR6wva.swf
            timestamp=1317333912
            oid=nzVqxGZyOd8
            showpopout=1
            mpu=True
            hl=en_US
            tmi=1
            ptchn=khanacademy
            no_get_video_log=1
            cc_module=http%3A%2F%2Fs.ytimg.com%2Fyt%2Fswfbin%2Fsubtitle_module-vflB4s90A.swf
            endscreen_module=http%3A%2F%2Fs.ytimg.com%2Fyt%2Fswfbin%2Fendscreen-vflFWlJG5.swf
            mpvid=AASuG7PoVGGWeij5
            as_launched_in_country=1
            referrer=None
            cid=3687
            dclk=True
            sendtmp=1
            sk=piYCZMaxEAfCVsuHDU9A90zPl-s0mHxYC
            ad_logging_flag=1
            t=vjVQa1PpcFM3A5DVi1jRp6tUDC_Ox5VLv9SIJIXKFNM%3D
            video_id=9Ek61w1LxSc
            sffb=True
        """ # noqa: E501 # pylint: disable=line-too-long
        print('\tFound "'+url+'"')
        data=data.split('title>',3)
        title=data[1].rsplit('-',1)[0].strip()
        data=data[-1]
        flashvars={}
        for d in data.split('flashvars="',1)[-1].split('"',1)[0].split('&amp;'): # noqa: E501 # pylint: disable=line-too-long
            d=d.split('=',1)
            flashvars[d[0]]=d[-1]
        video_id=urllib.parse.unquote(flashvars['video_id'])
        t=urllib.parse.unquote(flashvars['t'])
        downloadUrl='http://www.youtube.com/get_video?video_id='+video_id+'&t='+t # noqa: E501 # pylint: disable=line-too-long
        wf.enqueue(gotThumbnail,video_id)
        print('\tDownloading "'+downloadUrl+'"')
        #for k,v in flashvars.items():
        #    print(k,'=',urllib.unquote(v))
        wf.enqueue(gotVideo,downloadUrl)
    url='http://www.youtube.com/watch?v='+getId(idOrUrl)
    print('\tLooking up "'+url+'"')
    _cheaterDownload3(url)
    #wf.enqueue(gotVideoPage,url)
    # fill catalog with (name,thumbnail,video)
    wf.catalog.append((
        filename,
        outDir+os.sep+str(counter)+'-'+filename+'.jpg',
        str(counter)+'-'+filename.split('.',1)[0]+'.'+mediaFormat))

def _cheaterDownload(video_id):
    """
    This cheats by using somebody else's downloader.

    Specifically,
        https://github.com/JakeWharton/py-videodownloader
    """
    try:
        import videodownloader.providers.youtube as yt
    except ImportError:
        print('***************************************')
        print('  NEED TO INSTALL YOUTUBE DOWNLOADER!')
        cmd='git git://github.com/JakeWharton/py-videodownloader.git'
        cmd='wget --no-check-certificate -O - https://github.com/JakeWharton/py-videodownloader/tarball/master | tar -xzf -' # noqa: E501 # pylint: disable=line-too-long
        os.system(cmd)
        cmd='mv Jake*/videodownloader ./;rm -rf Jake*'
        os.system(cmd)
        print('***************************************')
        import videodownloader.providers.youtube as yt # type: ignore
    yt=yt.YouTube(video_id)
    print('cheater:\n\t'+yt.get_download_url())
    yt.run()

def _cheaterDownload3(video_id):
    """
    This cheats by using somebody else's downloader.

    Specifically,
        cclive
    """
    cmd='cclive -l 512 -N -F %t.%s -f best "'+video_id+'"'
    os.system(cmd)


def _cheaterDownload2(video_id):
    """
    This cheats by using somebody else's downloader.

    Specifically,
        http://py-youtube-downloader.googlecode.com

    This one is very closely coupled with Qt (barf!)
    """
    try:
        import youtube as videodownloader
    except ImportError:
        print('***************************************')
        print('  NEED TO INSTALL YOUTUBE DOWNLOADER!')
        cmd=[
            'wget',
            '-O',
            'Sources.zip',
            'http://py-youtube-downloader.googlecode.com/files/Sources.zip',
            ';',
            'unzip',
            '-q',
            'Sources.zip',
            ';',
            'rm',
            '-rf',
            'Sources.zip',
            'py2exe']
        os.system(cmd)
        import youtube as videodownloader
    #yt=videodownloader.YouTube(video_id)

def getId(idOrUrl):
    """
    get the video id from a url
    """
    # try http://id.youtube.com
    idOrUrl=idOrUrl.split('://',1)[-1]
    idOrUrl=idOrUrl.split('.',1)
    if len(idOrUrl)>1 and idOrUrl!='www':
        return idOrUrl[0]
    idOrUrl=idOrUrl[-1]
    # try ?v=id
    idOrUrl=idOrUrl.rsplit('v=',1)
    if len(idOrUrl)>1:
        return idOrUrl[1].split('&',1)[0]
    idOrUrl=idOrUrl[0]
    # try ?video_id=id
    idOrUrl=idOrUrl.rsplit('video_id=',1)
    if len(idOrUrl)>1:
        return idOrUrl[1].split('&',1)[0]
    idOrUrl=idOrUrl[0]
    # try /v/id
    idOrUrl=idOrUrl.rsplit('/v/',1)
    if len(idOrUrl)>1:
        return idOrUrl[1].split('&',1)[0].split('?',1)[0]
    idOrUrl=idOrUrl[0]
    # try /vi/id/
    idOrUrl=idOrUrl.rsplit('/v/',1)
    if len(idOrUrl)>1:
        return idOrUrl[1].split('/',1)[0].split('?',1)[0]
    idOrUrl=idOrUrl[0]
    # the whole thing must be the id
    return idOrUrl


def _getYoutubeThumbnailUrl(idOrUrl):
    idOrUrl=getId(idOrUrl)
    return 'http://img.youtube.com/vi/'+idOrUrl+'/2.jpg'


def _getYoutubeDownloadUrl(idOrUrl,mediaFormat=defaultMediaFormat):
    # Format info is at http://en.wikipedia.org/wiki/YouTube
    if not isinstance(mediaFormat,int):
        formats=[
            (5,'flv',),
            (34,'flv'),
            (35,'flv'),
            (18,'mp4'),
            (22,'mp4'),
            (37,'mp4'),
            (38,'webm'),
            (43,'webm'),
            (44,'webm'),
            (45,'webm'),
            (17,'3gp')]
        realFormat=defaultMediaFormat
        for f in formats:
            if f[1]==mediaFormat:
                realFormat=f[0]
        mediaFormat=realFormat
    idOrUrl=getId(idOrUrl)
    url='http://www.youtube.com/get_video?fmt='+str(mediaFormat)+'&video_id='+idOrUrl # noqa: E501 # pylint: disable=line-too-long
    return url


def cmdline(args):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printHelp=False
    params={
        'h':None,
        'format':defaultMediaFormat,
        'outDir':'.',
    }
    idOrUrl=[]
    for arg in args:
        if arg[0]=='-':
            if arg[1]=='-':
                arg=arg[2:].split('=',1)
                if arg[0]=='help':
                    printHelp=True
                elif arg[0]=='format':
                    if len(arg)>1:
                        params['format']=arg[1]
                    else:
                        params['format']=True
                elif arg[0]=='outDir':
                    if len(arg)>1:
                        params['outDir']=arg[1]
                    else:
                        params['outDir']=True
                else:
                    printHelp=True
                    print('ERR: Unknown parameter "--'+arg[0]+'"')
            else:
                for c in arg[1:]:
                    if c=='h':
                        printHelp=True
                    else:
                        printHelp=True
                        print('ERR: Unknown parameter "-'+c+'"')
        else:
            idOrUrl.append(arg)
    if not printHelp and len(idOrUrl)<1:
        printHelp=True
        print('ERR: No idOrUrl specified.')
    if printHelp:
        print('USAGE:')
        print('   youtubeFetch.py [options] idOrUrl')
        print('OPTIONS:')
        print('   -h ...................... print help')
        print('   --format ................ the video format to save')
        print('   --outDir ................ the output directory')
    else:
        youtubeFetch(' '.join(idOrUrl),params['format'],params['outDir'])


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
