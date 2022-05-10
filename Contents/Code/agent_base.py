# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, time, urllib2, io
from io import open
from functools import wraps
import yaml


"""
class MetadataSearchResult(XMLObject):
  def __init__(self, core, id, name=None, year=None, score=0, lang=None, thumb=None):
    XMLObject.__init__(self, core, id=id, thumb=thumb, name=name, year=year, score=score, lang=lang)
    self.tagName = "SearchResult"
"""

def d(data):
    if type(data) in [type({}), type([])]:
        import json
        return '\n' + json.dumps(data, indent=4, ensure_ascii=False)
    else:
        return str(data)



class AgentBase(object):
    key_map = {
        'com.plexapp.agents.sjva_agent_jav_censored' : 'C',         # C : censored dvd
        'com.plexapp.agents.sjva_agent_jav_censored_ama' : 'D',     # D : censored ama
        'com.plexapp.agents.sjva_agent_jav_uncensored' : 'E',       # E : uncensored 
        # W : western
        'com.plexapp.agents.sjva_agent_jav_fc2' : 'L',              # L : fc2
        'com.plexapp.agents.sjva_agent_ktv' : 'K',                  # K : 국내TV
        'com.plexapp.agents.sjva_agent_ftv' : 'F',                  # F : 외국TV
        # F : FTV
        # A : ani
        'com.plexapp.agents.sjva_agent_ott_show' : 'P',
        'com.plexapp.agents.sjva_agent_movie' : 'M',                # M : 영화
        'com.plexapp.agents.sjva_agent_music_normal' : 'S',         # S : 멜론 앨범, 아티스트 
        #'com.plexapp.agents.sjva_agent_music_folder' : 'T',         # T : 폴더 구조
        # 오디오북?
        'com.plexapp.agents.sjva_agent_audiobook' : 'B',            # B : 오디오북
           
        'com.plexapp.agents.sjva_agent_yaml' : 'Y',                 # Y : yaml
    }

    extra_map = {
        'trailer' : TrailerObject,
        'deletedscene' : DeletedSceneObject,
        'behindthescenes' : BehindTheScenesObject, 
        'interview' : InterviewObject, 
        'sceneorsample' : SceneOrSampleObject,
        'featurette' : FeaturetteObject,
        'short' : ShortObject,
        'other' : OtherObject,

        'musicvideo' : MusicVideoObject,
        'livemusicvideo' : LiveMusicVideoObject,
        'lyricmusicvideo' : LyricMusicVideoObject,
        'concertvideo' : ConcertVideoObject,
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
            param = ''
            if module_name in ['music_normal_artist', 'music_normal_album']:
                param = module_name.split('_')[-1]
                module_name = 'music_normal'
            
            module_prefs = self.get_module_prefs(module_name)
            sjva_mod_url = '/metadata/api/{module_name}'.format(module_name=module_name)

            #url = '{ddns}/metadata/api/{module_name}/search?keyword={keyword}&manual={manual}&year={year}&call=plex&apikey={apikey}'.format(
            url = '{ddns}{sjva_mod_url}/search?keyword={keyword}&manual={manual}&year={year}&call=plex&apikey={apikey}&param={param}'.format(
              ddns=Prefs['server'] if module_prefs['server'] == '' else module_prefs['server'],
              sjva_mod_url=sjva_mod_url,
              module_name=module_name,
              keyword=urllib.quote(keyword.encode('utf8')),
              manual=manual,
              year=year,
              apikey=Prefs['apikey'] if module_prefs['apikey'] == '' else module_prefs['apikey'],
              param=param,
            )
            Log(url)
            return AgentBase.my_JSON_ObjectFromURL(url)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
    

    def send_info(self, module_name, code, title=None):
        try:
            param = ''
            if module_name in ['music_normal_artist', 'music_normal_album']:
                param = module_name.split('_')[-1]
                module_name = 'music_normal'
            module_prefs = self.get_module_prefs(module_name)
            sjva_mod_url = '/metadata/api/{module_name}'.format(module_name=module_name)

            #url = '{ddns}/metadata/api/{module_name}/info?code={code}&call=plex&apikey={apikey}'.format(
            url = '{ddns}{sjva_mod_url}/info?code={code}&call=plex&apikey={apikey}&param={param}'.format(
              ddns=Prefs['server'] if module_prefs['server'] == '' else module_prefs['server'],
              sjva_mod_url=sjva_mod_url,
              module_name=module_name,
              code=urllib.quote(code.encode('utf8')),
              apikey=Prefs['apikey'] if module_prefs['apikey'] == '' else module_prefs['apikey'],
              param=param,
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
            json_filename = 'info.json'
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s?includeChildren=1' % media.id)
            section_id = str(data['MediaContainer']['librarySectionID'])
            #Log(self.d(data))
            if data['MediaContainer']['Metadata'][0]['type'] == 'album':
                #Log(d(data))
                Log('타입 : 앨범')

                if self.module_name in ['music_normal_album'] and  'Location' in data['MediaContainer']['Metadata'][0]:
                    folderpath = data['MediaContainer']['Metadata'][0]['Location'][0]['path']
                    return os.path.join(folderpath, 'album.json')

                data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s/children' % media.id)
                #Log(self.d(data))
            elif data['MediaContainer']['Metadata'][0]['type'] == 'artist':
                Log('타입 : 아티스트')
                """
                # 이거 너무 상위 폴더로 가버림.
                if self.module_name in ['music_normal_artist'] and  'Location' in data['MediaContainer']['Metadata'][0]:
                    folderpath = data['MediaContainer']['Metadata'][0]['Location'][0]['path']
                    return os.path.join(folderpath, 'artist.json')
                """
                json_filename = 'artist.json'
                data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s/children' % data['MediaContainer']['Metadata'][0]['Children']['Metadata'][0]['ratingKey'])


            if 'Media' in data['MediaContainer']['Metadata'][0]:
                filename = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']
                if self.module_name in ['movie']:
                    ret = os.path.join(os.path.dirname(filename), 'info.json')
                elif self.module_name in ['jav_censored', 'jav_censored_ama', 'jav_fc2', 'jav_uncensored']:
                    section_id_list = []
                    if Prefs['filename_json'] is not None:
                        section_id_list = Prefs['filename_json'].split(',')
                    if Prefs['filename_json'] == 'all' or section_id in section_id_list:
                        tmp = os.path.splitext(os.path.basename(filename))
                        code = tmp[0].split(' ')[0]
                        if code[-2] == 'd' and code [-3] == 'c':
                            code = code[:-3].strip(' .-')
                        ret = os.path.join(os.path.dirname(filename), '%s.json' % code)
                    else:
                        ret = os.path.join(os.path.dirname(filename), 'info.json')
                elif self.module_name in ['book']:
                    ret = os.path.join(os.path.dirname(filename), 'audio.json')
                
                elif self.module_name in ['music_normal_album']:
                    parent = os.path.split(os.path.dirname(filename))[1]
                    match = re.match('(CD|DISC)\s?(?P<disc>\d+)', parent, re.IGNORECASE)
                    if match:
                        ret = os.path.join(os.path.dirname(os.path.dirname(filename)), 'album.json')
                    else:
                        ret = os.path.join(os.path.dirname(filename), 'album.json')
                elif self.module_name in ['music_normal_artist']:
                    parent = os.path.split(os.path.dirname(filename))[1]
                    match = re.match('(CD|DISC)\s?(?P<disc>\d+)', parent, re.IGNORECASE)
                    
                    if match:
                        album_root = os.path.dirname(os.path.dirname(filename))
                    else:
                        album_root = os.path.dirname(filename)
                    album_basename = os.path.basename(album_root)
                    if album_basename.count(' - ') == 1:
                        ret = os.path.join(album_root, 'artist.json')
                    else:
                        ret = os.path.join(os.path.dirname(album_root), 'artist.json')

                
                    
                    
            elif 'Location' in data['MediaContainer']['Metadata'][0]:
                # 쇼... ktv, ftv
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
            Log('세이브 : %s', ret)
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
    # ftv에서 시즌정보
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
                Log("info.json 삭제1 %s", ret)
                os.remove(ret)
                #time.sleep(2)
        except Exception as e:
            try: 
                Log("info.json 삭제2 %s", ret)
                #os.system('rm %s' % ret)
                # 2021-11-27 by lapis https://sjva.me/bbs/board.php?bo_table=suggestions&wr_id=1978
                os.system('rm "%s"' % ret)
            except:
                pass
            #Log('Exception:%s', e)
            #Log(traceback.format_exc())

    
    def is_include_time_info(self, media):
        try:
            if Prefs['include_time_info'] == 'all':
                return True
            if Prefs['include_time_info'] == '' or Prefs['include_time_info'] is None:
                return False
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s' % media.id)
            section_id = str(data['MediaContainer']['librarySectionID'])
            section_id_list = Prefs['include_time_info'].split(',')
            return section_id in section_id_list
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
        return False

    def is_read_json(self, media):
        try:
            if Prefs['read_json'] == 'all':
                return True
            if Prefs['read_json'] == '' or Prefs['read_json'] is None:
                return False
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s' % media.id)
            section_id = str(data['MediaContainer']['librarySectionID'])
            section_id_list = Prefs['read_json'].split(',')
            return section_id in section_id_list
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
        return False

    def is_write_json(self, media):
        try:
            if Prefs['write_json'] == 'all':
                return True
            if Prefs['write_json'] == '' or Prefs['write_json'] is None:
                return False
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s' % media.id)
            section_id = str(data['MediaContainer']['librarySectionID'])
            section_id_list = Prefs['write_json'].split(',')
            return section_id in section_id_list
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
        return False
    
    def is_show_extra(self, media):
        try:
            if Prefs['show_extra_enabled'] == 'all':
                return True
            if Prefs['show_extra_enabled'] == '' or Prefs['show_extra_enabled'] is None:
                return False
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s' % media.id)
            section_id = str(data['MediaContainer']['librarySectionID'])
            section_id_list = Prefs['show_extra_enabled'].split(',')
            return section_id in section_id_list
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
        return False

    def is_collection_append(self, media):
        try:
            if Prefs['collection_disalbed'] == 'all':
                return False
            if Prefs['collection_disalbed'] == '' or Prefs['collection_disalbed'] is None:
                return True
            section_id_list = Prefs['collection_disalbed'].split(',')
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s' % media.id)
            section_id = str(data['MediaContainer']['librarySectionID'])
            return not (section_id in section_id_list)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
        return True


    def d(self, data):
        return json.dumps(data, indent=4, ensure_ascii=False)
    


    

    
    # for YAML
    def get(self, data, field, default):
        ret = data.get(field, None)
        if ret is None or ret == '':
            ret = default
        return ret
    
    def get_bool(self, data, field, default):
        ret = data.get(field, None)
        if ret is None or ret == '':
            ret = str(default)
        if ret.lower() in ['true']:
            return True
        elif ret.lower() in ['false']:
            return False
        return ret
    
    def get_list(self, data, field):
        ret = data.get(field, None)
        if ret is None:
            ret = []
        else:
            if type(ret) != type([]):
                ret = [x.strip() for x in ret.split(',')]
        return ret
    
    def get_person_list(self, data, field):
        ret = data.get(field, None)
        if ret is None:
            ret = []
        else:
            if type(ret) != type([]):
                tmp = []
                for value in ret.split(','):
                    tmp.append({'name':value.strip()})
                ret = tmp
        return ret

    def get_media_list(self, data, field):
        ret = data.get(field, None)
        if ret is None:
            ret = []
        else:
            if type(ret) != type([]):
                tmp = []
                insert_index = -1
                for idx, value in enumerate(ret.split(',')):
                    if value.startswith('http'):
                        tmp.append({'url':value.strip()})
                        insert_index = idx
                    else:
                        if insert_index > -1:
                            tmp[insert_index]['url'] = '%s,%s' % (tmp[insert_index]['url'], value)
                ret = tmp
        return ret 

    # 포인터가 아니다. 변수의 값이 넘어와버린다
    # setattr로 클래스 변수 값을 셋한다.
    # 그런데 기본형(string, int)이 아닌 것들은 포인터처럼 처리..
    # set_data만 setattr로.. 나머지는 getattr로 변수주소를 받아 처리
    def set_data(self, meta, data, field, is_primary):
        try:
            Log('set_data : %s', field)
            value = self.get(data, field, None)
            if value is not None:
                if field == 'title_sort':
                    value = unicodedata.normalize('NFKD', value)
                elif field in ['originally_available_at', 'available_at']:
                    value = Datetime.ParseDate(value).date()
                elif field in ['rating', 'audience_rating']:
                    value = float(value)
                elif field == 'year':
                    value = int(value)
                setattr(meta, field, value)
            elif is_primary:
                setattr(meta, field, None)
        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())    


    def set_data_list(self, meta, data, field, is_primary):
        try:
            meta = getattr(meta, field)
            value = self.get_list(data, field)
            if len(value) > 0:
                meta.clear()
                for tmp in value:
                    meta.add(tmp)
            elif is_primary:
                meta.clear()

        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())

    def set_data_person(self, meta, data, field, is_primary):
        try:
            meta = getattr(meta, field)
            value = self.get_person_list(data, field)
            if len(value) > 0:
                meta.clear()
                for person in value:
                    meta_person = meta.new()
                    meta_person.name = self.get(person, 'name', None)
                    meta_person.role = self.get(person, 'role', None)
                    meta_person.photo = self.get(person, 'photo', None)
            elif is_primary:
                meta.clear()

        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())

    def set_data_media(self, meta, data, field, is_primary):
        try:
            meta = getattr(meta, field)
            value = self.get_media_list(data, field)
            if len(value) > 0:
                valid_names = []
                for idx, media in enumerate(value):
                    valid_names.append(media['url'])
                    if 'thumb' in media:
                        meta[media['url']] = Proxy.Preview(HTTP.Request(media['thumb']).content, sort_order=idx+1)
                    else:
                        meta[media['url']] = Proxy.Preview(HTTP.Request(media['url']).content, sort_order=idx+1)
                meta.validate_keys(valid_names)
            elif is_primary:
                meta.validate_keys([])
            Log(meta)

        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())

    def set_data_reviews(self, meta, data, field, is_primary):
        try:
            meta = getattr(meta, field)
            value = self.get(data, field, [])
            if len(value) > 0:
                meta.clear()
                for review in value:
                    r = meta.new()
                    r.author = self.get(review, 'author', None)
                    r.source = self.get(review, 'source', None)
                    r.image = self.get(review, 'image', None)
                    r.link = self.get(review, 'link', None)
                    r.text = self.get(review, 'text', None)
            elif is_primary:
                meta.clear()
          
        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())

    def set_data_extras(self, meta, data, field, is_primary):
        try:
            meta = getattr(meta, field)
            value = self.get(data, field, [])
            if len(value) > 0:
                for extra in value:
                    mode = self.get(extra, 'mode', None)
                    extra_type = self.get(extra, 'type', 'trailer')
                    extra_class = self.extra_map[extra_type.lower()]
                    url = 'sjva://sjva.me/playvideo/%s|%s' % (mode, extra.get('param'))
                    meta.add(
                        extra_class(
                            url=url, 
                            title=self.change_html(extra.get('title', '')),
                            originally_available_at = Datetime.ParseDate(self.get(extra, 'originally_available_at', '1900-12-31')).date(),
                            thumb=self.get(extra, 'thumb', '')
                        )
                    )
                    Log('111111111111111111111')
                    Log(url)

            elif is_primary:
                #Log(meta)
                #meta.clear()
                pass
        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())


    def yaml_load(self, filepath):
        #data = self.yaml_load(filepath)
        #data = yaml.load(io.open(filepath), Loader=yaml.BaseLoader)
        try: 
            data = yaml.load(io.open(filepath, encoding='utf-8'), Loader=yaml.BaseLoader)
        except: 
            data = yaml.load(io.open(filepath, encoding='euc-kr'), Loader=yaml.BaseLoader)
        return data










class PutRequest(urllib2.Request):
    def __init__(self, *args, **kwargs):
        return urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self, *args, **kwargs):
        return 'PUT'