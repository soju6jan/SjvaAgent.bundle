# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, time
from io import open
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
        'com.plexapp.agents.sjva_agent_jav_fc2' : 'L',              # L : fc2
        'com.plexapp.agents.sjva_agent_ktv' : 'K',                  # K : 국내TV
        'com.plexapp.agents.sjva_agent_ftv' : 'F',                  # F : 외국TV
        # F : FTV
        # A : ani
        'com.plexapp.agents.sjva_agent_ott_show' : 'P',
        'com.plexapp.agents.sjva_agent_movie' : 'M',                # M : 영화
        'com.plexapp.agents.sjva_agent_music' : 'V',                # V : 앨범, 아티스트 
        # 오디오북?
        'com.plexapp.agents.sjva_agent_audiobook' : 'B',            # B : 오디오북
        'com.plexapp.agents.sjva_agent_audiobook_json' : 'J',       # Y : 오디오북 yaml
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
    
    token = None

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
            module_prefs = self.get_module_prefs(module_name)
            if module_name == 'jav_fc2':
                sjva_mod_url = '/mod/api/fc2metadata'.format(module_name=module_name)
            else:
                sjva_mod_url = '/metadata/api/{module_name}'.format(module_name=module_name)

            #url = '{ddns}/metadata/api/{module_name}/search?keyword={keyword}&manual={manual}&year={year}&call=plex&apikey={apikey}'.format(
            url = '{ddns}{sjva_mod_url}/search?keyword={keyword}&manual={manual}&year={year}&call=plex&apikey={apikey}'.format(
              ddns=Prefs['server'] if module_prefs['server'] == '' else module_prefs['server'],
              sjva_mod_url=sjva_mod_url,
              module_name=module_name,
              keyword=urllib.quote(keyword.encode('utf8')),
              manual=manual,
              year=year,
              apikey=Prefs['apikey'] if module_prefs['apikey'] == '' else module_prefs['apikey']
            )
            Log(url)
            return AgentBase.my_JSON_ObjectFromURL(url)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
    

    def send_info(self, module_name, code, title=None):
        try:
            module_prefs = self.get_module_prefs(module_name)
            if module_name == 'jav_fc2':
                sjva_mod_url = '/mod/api/fc2metadata'.format(module_name=module_name)
            else:
                sjva_mod_url = '/metadata/api/{module_name}'.format(module_name=module_name)

            #url = '{ddns}/metadata/api/{module_name}/info?code={code}&call=plex&apikey={apikey}'.format(
            url = '{ddns}{sjva_mod_url}/info?code={code}&call=plex&apikey={apikey}'.format(
              ddns=Prefs['server'] if module_prefs['server'] == '' else module_prefs['server'],
              sjva_mod_url=sjva_mod_url,
              module_name=module_name,
              code=urllib.quote(code.encode('utf8')),
              apikey=Prefs['apikey'] if module_prefs['apikey'] == '' else module_prefs['apikey']
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
            module_prefs = self.get_module_prefs(module_name)
            url = '{ddns}/metadata/api/{module_name}/episode_info?code={code}&call=plex&apikey={apikey}'.format(
              ddns=Prefs['server'] if module_prefs['server'] == '' else module_prefs['server'],
              module_name=module_name,
              code=urllib.quote(code.encode('utf8')),
              apikey=Prefs['apikey'] if module_prefs['apikey'] == '' else module_prefs['apikey']
            )
            Log(url)
            return AgentBase.my_JSON_ObjectFromURL(url)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())

    
    def change_html(self, text):
        if text is not None:
            return text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#35;', '#').replace('&#39;', "‘")


    def get_module_prefs(self, module):
        try:
            ret = {'server':'', 'apikey':'', 'end_noti_filepath':'', 'include_time_info':''}
            CURRENT_PATH = re.sub(r'^\\\\\?\\', '', os.getcwd())
            pref_filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_PATH))), 'Plug-in Support', 'Preferences', 'com.plexapp.agents.sjva_agent_%s.xml' % module)
            if os.path.exists(pref_filepath):
                tfile = open(pref_filepath, encoding='utf8')
                text = tfile.read()
                tfile.close()
                if text is not None:
                    prefs = XML.ElementFromString(text)
                    for child in prefs.getchildren():
                        ret[child.tag] = '' if child.text is None else child.text

            
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
        return ret


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
    
    def get_token(self):
        try:
            if self.token is None:
                url = 'http://127.0.0.1:32400/myplex/account'
                data = JSON.ObjectFromURL(url)
                self.token = data['MyPlex']['authToken']
            return self.token
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
    
    def get_json_filepath(self, media):
        try:
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s?includeChildren=1' % media.id)
            section_id = str(data['MediaContainer']['librarySectionID'])
            #Log('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz')
            #Log(self.d(data))
            if data['MediaContainer']['Metadata'][0]['type'] == 'album':
                data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s/children' % media.id)
                #Log(self.d(data))
            elif data['MediaContainer']['Metadata'][0]['type'] == 'artist':
                data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s/children' % data['MediaContainer']['Metadata'][0]['Children']['Metadata'][0]['ratingKey'])


            if 'Media' in data['MediaContainer']['Metadata'][0]:
                filename = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']
                if self.module_name in ['movie']:
                    ret = os.path.join(os.path.dirname(filename), 'info.json')
                elif self.module_name in ['jav_censored', 'jav_censored_ama', 'jav_fc2']:
                    section_id_list = []
                    if Prefs['filename_json'] is not None:
                        section_id_list = Prefs['filename_json'].split(',')
                    if section_id in section_id_list:
                        tmp = os.path.splitext(os.path.basename(filename))
                        ret = os.path.join(os.path.dirname(filename), '%s.json' % tmp[0])
                    else:
                        ret = os.path.join(os.path.dirname(filename), 'info.json')
                elif self.module_name in ['book', 'book_json']:
                    ret = os.path.join(os.path.dirname(filename), 'info.json')
                    
            elif 'Location' in data['MediaContainer']['Metadata'][0]:
                folderpath = data['MediaContainer']['Metadata'][0]['Location'][0]['path']
                ret = os.path.join(folderpath, 'info.json')
            else:
                ret = None
            Log('info.json 위치 : %s' % ret)
            return ret
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())


    def save_info(self, media, info):
        try:
            ret = self.get_json_filepath(media)
            if ret is None:
                return
            import io
            with io.open(ret, 'w', encoding="utf-8") as outfile:
                data = json.dumps(info, ensure_ascii=False, indent=4)
                if isinstance(data, str):
                    data = data.decode("utf-8")

                outfile.write(data)
            return True
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
        return False

    

    def get_info_json(self, media):
        try:
            filepath = self.get_json_filepath(media)
            if filepath is None:
                return
            return self.read_json(filepath)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())


    def read_json(self, filepath):
        data = None
        if os.path.exists(filepath):
            import io
            with io.open(filepath, 'r', encoding="utf-8") as outfile:
                tmp = outfile.read()
            data = json.loads(tmp)
        return data

        
    # KTV에서 사용. 있으면 추가
    def append_info(self, media, key, info):
        try:
            ret = self.get_json_filepath(media)
            if ret is None:
                return
            all_data = self.get_info_json(media)
            if all_data is None:
                all_data = {}
            import io
            with io.open(ret, 'w', encoding="utf-8") as outfile:
                all_data[key] = info
                data = json.dumps(all_data, ensure_ascii=False, indent=4)
                data = data.decode('utf-8')
                if isinstance(data, str):
                    data = data.decode("utf-8")
                outfile.write(data)
            return True
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
        return False
    

    def remove_info(self, media):
        try:
            ret = self.get_json_filepath(media)
            # 구드공인 경우 캐시때문에 exists 함수 실패하는 것 같음.
            if ret is not None: #and os.path.exists(ret):
                os.remove(ret)
                #time.sleep(2)
        except Exception as e:
            try: 
                os.system('rm %s' % ret)
            except:
                pass
            #Log('Exception:%s', e)
            #Log(traceback.format_exc())

    
    def is_include_time_info(self, media):
        try:
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s' % media.id)
            section_id = str(data['MediaContainer']['librarySectionID'])
            if Prefs['include_time_info'] == 'all':
                return True
            section_id_list = Prefs['include_time_info'].split(',')
            return section_id in section_id_list
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
        return False

    def is_read_json(self, media):
        try:
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s' % media.id)
            section_id = str(data['MediaContainer']['librarySectionID'])
            if Prefs['read_json'] == 'all':
                return True
            section_id_list = Prefs['read_json'].split(',')
            return section_id in section_id_list
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
        return False

    def is_write_json(self, media):
        try:
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s' % media.id)
            section_id = str(data['MediaContainer']['librarySectionID'])
            if Prefs['write_json'] == 'all':
                return True
            section_id_list = Prefs['write_json'].split(',')
            return section_id in section_id_list
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
        return False
    
    def d(self, data):
        return json.dumps(data, indent=4, ensure_ascii=False)