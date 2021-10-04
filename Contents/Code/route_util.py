# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, time
# /:/plugins/com.plexapp.agents.sjva_agent/function/version?X-Plex-Token=%s' % (server_url, server_token)

@route('/version') 
def version():
    from .version import VERSION
    return VERSION


@route('/kakao') 
def kakao(content_id):
    #content_id = '414068276'
    try:
        url = 'https://tv.kakao.com/katz/v2/ft/cliplink/{}/readyNplay?player=monet_html5&profile=HIGH&service=kakao_tv&section=channel&fields=seekUrl,abrVideoLocationList&startPosition=0&tid=&dteType=PC&continuousPlay=false&contentType=&{}'.format(content_id, int(time.time()))
        data = JSON.ObjectFromURL(url)
        video_url = data['videoLocation']['url']
        Log('Kakao : %s', video_url)
        return Redirect(video_url)
    except Exception as e: 
        Log('Exception:%s', e)
        Log(traceback.format_exc())

@route('/wavve') 
def wavve(sjva_url):
    try:
        data = JSON.ObjectFromURL(sjva_url)
        url = data['url']
        data = JSON.ObjectFromURL(url)
        video_url = data['playurl']
        return Redirect(video_url)
    except Exception as e: 
        Log('Exception:%s', e)
        Log(traceback.format_exc())





@route('/get_lyric') 
def get_lyric(mode, filename, artist, track):
    Log('mode : %s  ' % (mode))
    Log('artist : %s  artist : %s' % (artist, track))
    lyric = ''
    if Prefs['server']:
        try:
            url = '{ddns}/metadata/api/lyric/get_lyric?mode={mode}&filename={filename}&artist={artist}&track={track}&call=plex&apikey={apikey}'.format(ddns=Prefs['server'], mode=mode, filename=urllib.quote(filename.encode('utf8')), artist=urllib.quote(artist.encode('utf8')), track=urllib.quote(track.encode('utf8')), apikey=Prefs['apikey'])
            data = JSON.ObjectFromURL(url, timeout=5000)
            Log(data)
            lyric = data['data'] if data['ret'] == 'success' else data['log']
        except Exception as e: 
            Log('Exception:%s', e)
            lyric = str(traceback.format_exc())
    Log(lyric)
    return lyric
  