# -*- coding: utf-8 -*-
import os, sys, traceback, hashlib, codecs, urllib
from collections import defaultdict
import xml.etree.ElementTree as ET
from io import open


def Start():
    HTTP.CacheTime = 0

def file2md5(filepath):
    md5 = hashlib.md5()
    filepath = unicode(filepath)
    f = open(filepath, 'rb')
    tag = f.read(3)
    seekpos = 0
    if tag == 'ID3':
        f.read(3)
        id3Size = f.read(4)
        ii0 = int(codecs.encode(id3Size[0], 'hex'), 16)
        ii1 = int(codecs.encode(id3Size[1], 'hex'), 16)
        ii2 = int(codecs.encode(id3Size[2], 'hex'), 16)
        ii3 = int(codecs.encode(id3Size[3], 'hex'), 16)
        size = ii0 << 21 | ii1 << 14 | ii2 << 7 | ii3
        seekpos = size+10

        f.seek(seekpos)
        for i in range(0, 50000):
            ii0 = int(codecs.encode(f.read(1), 'hex'), 16)
            if ii0 == 255:
                ii1 = int(codecs.encode(f.read(1), 'hex'), 16)
                if (ii1 >> 5) == 7:
                    seekpos = seekpos + i
                    break
    f.seek(seekpos)
    chunk = f.read(163840)
    md5.update(chunk)
    f.close()
    ret = md5.hexdigest()
    Log('filepath:%s md5:%s', filepath, ret)
    return ret


@route('/version') 
def version():
    return '1.0.0'


@route('/get_lyric') 
def get_lyric(mode, md5, filename, artist, track):
    Log('mode : %s  ' % (mode))
    Log('MD5 : %s  FILENAME : %s' % (md5, filename))
    Log('artist : %s  artist : %s' % (artist, track))
    if mode == 'lrc' and Prefs['use_alsong'] and md5:
        alsong_ret, lyric = alsong(md5)
        if alsong_ret:
            return lyric

    if Prefs['server']:
        url = '{ddns}/metadata/api/lyric/get_lyric?mode={mode}&filename={filename}&artist={artist}&track={track}&call=plex&apikey={apikey}'.format(ddns=Prefs['server'], mode=mode, filename=urllib.quote(filename.encode('utf8')), artist=urllib.quote(artist.encode('utf8')), track=urllib.quote(track.encode('utf8')), apikey=Prefs['apikey'])
        Log(url)
        data = JSON.ObjectFromURL(url, timeout=5000)
        lyric = data['data'] if data['ret'] == 'success' else data['log']
    return lyric

@route('/get_lyric2') 
def get_lyric2(mode, track_key):
    Log('mode : %s  ' % (mode))
    Log('track_key : %s' % (track_key))
    lyric = ''
    if Prefs['server']:
        try:
            url = 'http://127.0.0.1:32400/library/metadata/%s' % track_key
            data = JSON.ObjectFromURL(url, headers={'accept' : 'application/json'})
            #Log(d(data))
            artist = data['MediaContainer']['Metadata'][0]['originalTitle']
            track = data['MediaContainer']['Metadata'][0]['title']
            filename = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']
            url = '{ddns}/metadata/api/lyric/get_lyric?mode={mode}&filename={filename}&artist={artist}&track={track}&call=plex&apikey={apikey}'.format(ddns=Prefs['server'], mode=mode, filename=urllib.quote(filename.encode('utf8')), artist=urllib.quote(artist.encode('utf8')), track=urllib.quote(track.encode('utf8')), apikey=Prefs['apikey'])
            data = JSON.ObjectFromURL(url, timeout=5000)
            #Log(d(data))
            lyric = data['data'] if data['ret'] == 'success' else data['log']
        except Exception as e: 
            Log('Exception:%s', e)
            lyric = str(traceback.format_exc())
    #Log(lyric)
    return lyric

def alsong(md5):
    try:
        url = 'http://lyrics.alsong.co.kr/alsongwebservice/service1.asmx'
        postData = '<?xml version="1.0" encoding="UTF-8"?>\n<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope" xmlns:SOAP-ENC="http://www.w3.org/2003/05/soap-encoding" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:ns2="ALSongWebServer/Service1Soap" xmlns:ns1="ALSongWebServer" xmlns:ns3="ALSongWebServer/Service1Soap12"><SOAP-ENV:Body><ns1:GetLyric7><ns1:encData>7c2d15b8f51ac2f3b2a37d7a445c3158455defb8a58d621eb77a3ff8ae4921318e49cefe24e515f79892a4c29c9a3e204358698c1cfe79c151c04f9561e945096ccd1d1c0a8d8f265a2f3fa7995939b21d8f663b246bbc433c7589da7e68047524b80e16f9671b6ea0faaf9d6cde1b7dbcf1b89aa8a1d67a8bbc566664342e12</ns1:encData><ns1:stQuery><ns1:strChecksum>%s</ns1:strChecksum><ns1:strVersion></ns1:strVersion><ns1:strMACAddress></ns1:strMACAddress><ns1:strIPAddress></ns1:strIPAddress></ns1:stQuery></ns1:GetLyric7></SOAP-ENV:Body></SOAP-ENV:Envelope>' % md5
        headers = {'content-type': 'application/soap+xml; charset=utf-8'}
        page = HTTP.Request(url, data=postData, headers=headers)
        #Log(page.content)
        root = ET.fromstring(page.content)
        lyric = None
        for child in root.iter():
            if child.tag.find('strLyric') != -1 :
                lyric = child.text
                if lyric is not None:
                    lyric = lyric.replace('<br>', '\n')
                    lyric = lyric.replace('[00:00.00]\n', '')
                    return True, lyric
                else:
                    return False, u'[00:00:01] 알송 서버에 가사가 없습니다.'
    except Exception as e: 
        Log('Exception:%s', e)
        Log(traceback.format_exc())
        return False, u'[00:00:01] 에러가 발생했습니다.\n[00:00:02] %s' % e



class SjvaAgentLyric(Agent.Album):
    name = 'SJVA Music Lyric'
    languages = [Locale.Language.NoLanguage]
    primary_provider = False

    def search(self, results, media, lang, manual, **kwargs):
        results.Append(MetadataSearchResult(id = 'null', score = 100))

    """
    def update(self, metadata, media, lang):
        valid_keys = defaultdict(list)
        path = None
        url = 'http://127.0.0.1:32400/library/metadata/%s' % media.id
        data = JSON.ObjectFromURL(url, headers={'accept' : 'application/json'})
        artist = data['MediaContainer']['Metadata'][0]['parentTitle']

        for index, track in enumerate(media.children):
            track_key = track.guid or index
            track_key = track_key.split('/')[-1]
            for item in track.items:
                for part in item.parts:
                    try:
                        md5 = file2md5(part.file) if Prefs['use_alsong'] else ''
                        for idx, mode in enumerate(['lrc', 'txt']):
                            url = 'http://127.0.0.1:32400/:/plugins/com.plexapp.agents.sjva_agent_lyric/function/get_lyric?mode={mode}&md5={md5}&filename={filename}&artist={artist}&track={track}'.format(
                                mode = mode, 
                                md5 = md5, 
                                filename = urllib.quote(os.path.basename(part.file).encode('utf8')), 
                                artist = urllib.quote(artist.encode('utf8')), 
                                track = urllib.quote(track.title.encode('utf8'))
                            )
                            metadata.tracks[track_key].lyrics[url] = Proxy.Remote(url, format = mode, sort_order=idx+1)
                            valid_keys[track_key].append(url)
                    except Exception as e: 
                        Log('Exception:%s', e)
                        Log(traceback.format_exc())
                    
        for key in metadata.tracks:
            metadata.tracks[key].lyrics.validate_keys(valid_keys[key])
    """

    def update(self, metadata, media, lang):
        try:
            valid_keys = defaultdict(list)
            path = None
            for index in media.tracks:
                track_key = media.tracks[index].id or int(index)
                Log("트랙 메타데이터 키 : %s", track_key)
                try:
                    for idx, mode in enumerate(['lrc', 'txt']):
                        url = 'http://127.0.0.1:32400/:/plugins/com.plexapp.agents.sjva_agent_lyric/function/get_lyric2?mode={mode}&track_key={track_key}'.format(
                            mode = mode, 
                            track_key = track_key
                        )
                        metadata.tracks[track_key].lyrics[url] = Proxy.Remote(url, format = mode, sort_order=idx+1)
                        Log(url)
                        valid_keys[track_key].append(url)
                except Exception as e: 
                    Log('Exception:%s', e)
                    Log(traceback.format_exc())
            for key in metadata.tracks:
                metadata.tracks[key].lyrics.validate_keys(valid_keys[key])

        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())