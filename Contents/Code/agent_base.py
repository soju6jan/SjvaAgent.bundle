# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, time
from functools import wraps


"""
class MetadataSearchResult(XMLObject):
  def __init__(self, core, id, name=None, year=None, score=0, lang=None, thumb=None):
    XMLObject.__init__(self, core, id=id, thumb=thumb, name=name, year=year, score=score, lang=lang)
    self.tagName = "SearchResult"
"""


class AgentBase(object):
    key_map = {
        'com.plexapp.agents.sjva_agent_jav_censored' : 'C',         # C : censored dvd
        'com.plexapp.agents.sjva_agent_jav_censored_ama' : 'D',     # D : censored ama
        # E : uncensored 
        # W : western
        # G : fc2
        'com.plexapp.agents.sjva_agent_ktv' : 'K',                  # K : 국내TV
        # F : FTV
        # A : ani
        'com.plexapp.agents.sjva_agent_ott_show' : 'P',
        'com.plexapp.agents.sjva_agent_movie' : 'M',            # M : 영화
        # X : 앨범
        # Y : 아티스트
    }


    extra_map = {
        'Trailer' : TrailerObject,
        'DeletedScene' : DeletedSceneObject,
        'BehindTheScenes' : BehindTheScenesObject, 
        'Interview' : InterviewObject, 
        'SceneOrSample' : SceneOrSampleObject,
        'Featurette' : FeaturetteObject,
        'Short' : ShortObject,
        'Other' : OtherObject
    }
    
    def search_result_line(self):
        text = ' ' + ' '.ljust(80, "=") + ' '
        return text


    def try_except(original_function):
        @wraps(original_function)
        def wrapper_function(*args, **kwargs):  #1
            try:
                return original_function(*args, **kwargs)
            except Exception as exception: 
                Log('Exception:%s', exception)
                Log(traceback.format_exc())
        return wrapper_function

    


    def send_search(self, module_name, keyword, manual, year=''):
        try:
            url = '{ddns}/metadata/api/{module_name}/search?keyword={keyword}&manual={manual}&year={year}&call=plex&apikey={apikey}'.format(
              ddns=Prefs['server'],
              module_name=module_name,
              keyword=urllib.quote(keyword.encode('utf8')),
              manual=manual,
              year=year,
              apikey=Prefs['apikey']
            )
            Log(url)
            return AgentBase.my_JSON_ObjectFromURL(url)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
    

    def send_info(self, module_name, code, title=None):
        try:
            url = '{ddns}/metadata/api/{module_name}/info?code={code}&call=plex&apikey={apikey}'.format(
              ddns=Prefs['server'],
              module_name=module_name,
              code=urllib.quote(code.encode('utf8')),
              apikey=Prefs['apikey']
            )
            if title is not None:
                url += '&title=' + urllib.quote(title.encode('utf8'))
            Log(url)
            return AgentBase.my_JSON_ObjectFromURL(url)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())


    def send_episode_info(self, module_name, code):
        try:
            url = '{ddns}/metadata/api/{module_name}/episode_info?code={code}&call=plex&apikey={apikey}'.format(
              ddns=Prefs['server'],
              module_name=module_name,
              code=urllib.quote(code.encode('utf8')),
              apikey=Prefs['apikey']
            )
            Log(url)
            return AgentBase.my_JSON_ObjectFromURL(url)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())

    
    def change_html(self, text):
        if text is not None:
            return text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#35;', '#').replace('&#39;', "‘")



    @staticmethod
    def get_key(media):
        try:
            Log('...............................')
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s' % media.id)
            section_id = str(data['MediaContainer']['librarySectionID'])
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/sections')
            
            for item in data['MediaContainer']['Directory']:
                if item['key'] == section_id:
                    return AgentBase.key_map[item['agent']]
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())


    @staticmethod
    def my_JSON_ObjectFromURL(url, timeout=None, retry=3):
        try:
            if timeout is None:
                timeout = int(Prefs['timeout'])
            Log('my_JSON_ObjectFromURL retry : %s, url : %s', retry, url)
            return JSON.ObjectFromURL(url, timeout=timeout)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
            if retry > 0:
                time.sleep(1)
                Log('RETRY : %s', retry)
                return AgentBase.my_JSON_ObjectFromURL(url, timeout, retry=(retry-1))
            else:
                Log('CRITICAL my_JSON_ObjectFromURL error') 
    

    def get_keyword_from_file(self, media):
        try:
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s' % media.id)
            filename = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']
            ret = os.path.splitext(os.path.basename(filename))[0]
            return ret
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
    
    """
    LyricFind.bundle/Contents/Code/__init__.py:      metadata.tracks[track_key].lyrics[url] = Proxy.Remote(url, format = 'lrc', sort_order=sort_order)
./LyricFind.bundle/Contents/Code/__init__.py:    metadata.tracks[track_key].lyrics[url] = Proxy.Remote(url, format = 'txt', sort_order=sort_order)
./LyricFind.bundle/Contents/Code/__init__.py:  # We need to recreate the Proxy objects to effectively pass them through since the Framework doesn't
./LyricFind.bundle/Contents/Code/__init__.py:      metadata.tracks[track_key].lyrics[key] = Proxy.Remote(key, format='lrc' if '&lrc=1' in key else 'txt', sort_order=sort_order)
^C
    """
