# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, time
# /:/plugins/com.plexapp.agents.sjva_agent/function/version?X-Plex-Token=%s' % (server_url, server_token)
from . import d

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



@route('/music_normal_lyric') 
def music_normal_lyric(mode, song_id, track_key):
    Log('mode : %s  ' % (mode))
    Log('track_key : %s' % (track_key))
    Log('song_id : %s' % (song_id))
    lyric = ''

    from .module_music_normal import ModuleMusicNormalAlbum 
    mod = ModuleMusicNormalAlbum()
    module_prefs = mod.get_module_prefs('music_normal')
    ddns = Prefs['server'] if module_prefs['server'] == '' else module_prefs['server']
    apikey = Prefs['apikey'] if module_prefs['apikey'] == '' else module_prefs['apikey']

    if ddns:
        try:
            url = 'http://127.0.0.1:32400/library/metadata/%s' % track_key
            data = JSON.ObjectFromURL(url, headers={'accept' : 'application/json'})
            #Log(d(data))
            artist = data['MediaContainer']['Metadata'][0]['originalTitle']
            track = data['MediaContainer']['Metadata'][0]['title']
            filename = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']

            url = '{ddns}/metadata/api/music_normal/song?mode={mode}&filename={filename}&artist={artist}&track={track}&call=plex&apikey={apikey}&song_id={song_id}'.format(ddns=ddns, mode=mode, filename=urllib.quote(filename.encode('utf8')), artist=urllib.quote(artist.encode('utf8')), track=urllib.quote(track.encode('utf8')), apikey=apikey, song_id=song_id)
            data = JSON.ObjectFromURL(url, timeout=5000)
            #Log(d(data))
            lyric = data['lyric'] if data['ret'] == 'success' else data['log']
        except Exception as e: 
            Log('Exception:%s', e)
            lyric = str(traceback.format_exc())
    return lyric

@route('yaml_lyric') 
def yaml_lyric(track_key):
    Log('track_key : %s' % (track_key))
    lyric = ''
    try:
        url = 'http://127.0.0.1:32400/library/metadata/%s' % track_key
        data = JSON.ObjectFromURL(url, headers={'accept' : 'application/json'})
        # Log(d(data))
        filename = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']
        if os.path.isfile(os.path.join(os.path.dirname(filename),'album.yaml')):
            import yaml, io
            data = yaml.load(io.open(os.path.join(os.path.dirname(filename),'album.yaml'), encoding='utf-8'), Loader=yaml.BaseLoader)
            # Log(d(data))
            lyric = data['lyrics'][os.path.basename(filename)[0]]
    except Exception as e: 
        Log('Exception:%s', e)
        lyric = str(traceback.format_exc())
    return lyric

def d(data):
    return json.dumps(data, indent=4, ensure_ascii=False)


@route('/get_folderpath') 
def get_folderpath(key):
    Log('key : %s  ' % key)
    try:
        from .agent_base import AgentBase
        data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s?includeChildren=1' % key)
        section_id = str(data['MediaContainer']['librarySectionID'])
        Log(d(data))
        content_type = data['MediaContainer']['Metadata'][0]['type']
        ret = {
            'title':data['MediaContainer']['Metadata'][0]['title'], 
            'section_title':data['MediaContainer']['librarySectionTitle'], 
            'section_id':data['MediaContainer']['librarySectionID']
        }

        if content_type == 'album':
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s/children' % key)
            filename = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']
            ret['ret'] = 'album'
            ret['folder'] = os.path.dirname(filename)
        elif content_type == 'artist':
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s/children' % data['MediaContainer']['Metadata'][0]['Children']['Metadata'][0]['ratingKey'])
            filename = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']
            ret['ret'] = 'artist'
            ret['folder'] = os.path.dirname(filename)
        elif content_type == 'movie':
            tmp_folders = []
            for tmp in data['MediaContainer']['Metadata'][0]['Media']:
                tmp_folder = os.path.dirname(tmp['Part'][0]['file'])
                if tmp_folder not in tmp_folders:
                    tmp_folders.append(tmp_folder)
            ret['folder_count'] = len(tmp_folders)
            ret['ret'] = 'movie'
            if len(tmp_folders) == 1:
                ret['folder'] = tmp_folders[0]
            else:
                ret['folder'] = '|'.join(tmp_folders)
            section_id_list = []
            if Prefs['filename_json'] is not None:
                section_id_list = Prefs['filename_json'].split(',')
            if Prefs['filename_json'] == 'all' or section_id in section_id_list:
                ret['ret'] = 'movie_one_folder'
                ret['filename'] = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']

        elif content_type == 'show':
            if 'Location' in data['MediaContainer']['Metadata'][0]:
                ret['ret'] = 'show'
                ret['folder'] = data['MediaContainer']['Metadata'][0]['Location'][0]['path']
            else:
                ret['ret'] = 'show_error_not_exist_location'
        Log('get_folderpath 위치 : %s' % d(ret))
    except Exception as e: 
        Log('Exception:%s', e)
        Log(traceback.format_exc())
        ret = {'ret':'exception', 'log':str(e)}
    return (ret)
