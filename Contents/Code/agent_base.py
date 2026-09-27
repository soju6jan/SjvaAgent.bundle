# -*- coding: utf-8 -*-
import os, json, re, unicodedata, time, urllib2, io
from io import open
from functools import wraps
import yaml

Core = Core # Framework.core.FrameworkCore
Log = Log # type: Framework.api.logkit.LogKit
Proxy = Proxy # type: Framework.api.modelkit.ProxyKit
HTTP = HTTP # type: Framework.api.networkkit.HTTPKit
Prefs = Prefs # type: Framework.api.runtimekit.PrefsKit
XML = XML # type: Framework.api.parsekit.XMLKit
JSON = JSON # type: Framework.api.parsekit.JSONKit
Platform = Platform # type: Framework.api.runtimekit.PlatformKit
Datetime = Datetime # type: Framework.api.utilkit.DatetimeKit
String = String # type: Framework.api.utilkit.StringKit
Regex = Regex # type: Framework.api.utilkit.RegexKit
unicode = unicode

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
        'com.plexapp.agents.sjva_agent_jav_uncensored' : 'E',       # E : uncensored
        'com.plexapp.agents.sjva_agent_western' : 'W',              # W : western
        #'com.plexapp.agents.sjva_agent_jav_censored_ama' : 'D',     # D : censored ama
        #'com.plexapp.agents.sjva_agent_jav_fc2' : 'L',              # L : fc2
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
        'trailer' : TrailerObject, # type: Framework.modelling.objects.ModelInterfaceObjectMetaclass
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
    
    site_code_mapping = {
        'daum': 'KD',
        'tving': 'KV',
        'wavve': 'KW',
        'watcha': 'KX',
        'tmdb': 'FT'
    }
    site_code_ptn = Regex(r'\{(?P<site>[^-]+)-(?P<code>[^}]+)\}', re.IGNORECASE)

    def search_result_line(self):
        text = ' ' + ' '.ljust(80, "=") + ' '
        return text


    def try_except(original_function):
        @wraps(original_function)
        def wrapper_function(*args, **kwargs):  #1
            try:
                return original_function(*args, **kwargs)
            except Exception as e:
                Log.Exception(str(e))
        return wrapper_function


    def send_search(self, module_name, keyword, manual, year='', media_path=None):
        try:
            url = self.get_api_url(module_name, "search")
            url = url + "&keyword={keyword}&manual={manual}&year={year}".format(
                keyword=String.Quote(keyword.encode('utf-8')),
                manual=manual,
                year=year,
            )
            if media_path:
                url = url + "&media_path={media_path}".format(
                    media_path=String.Quote(media_path.encode('utf-8'))
                )
            values = {'apikey': self.get_ff_apikey(module_name)}
            return AgentBase.my_JSON_ObjectFromURL(url, method="POST", values=values)
        except Exception as e:
            Log.Exception(str(e))


    def send_info(self, module_name, code, title=None):
        try:
            url = self.get_api_url(module_name, "info")
            url = url + "&code={code}".format(
                code=String.Quote(code.encode('utf-8')),
            )
            if title is not None:
                url += '&title=' + String.Quote(title.encode('utf-8'))
            values = {'apikey': self.get_ff_apikey(module_name)}
            return AgentBase.my_JSON_ObjectFromURL(url, method="POST", values=values)
        except Exception as e:
            Log.Exception(str(e))


    def send_episode_info(self, module_name, code):
        try:
            url = self.get_api_url(module_name, "episode_info")
            url = url + "&code={code}".format(
                code=String.Quote(code.encode('utf-8')),
            )
            values = {'apikey': self.get_ff_apikey(module_name)}
            return AgentBase.my_JSON_ObjectFromURL(url, method="POST", values=values)
        except Exception as e:
            Log.Exception(str(e))


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
            Log.Exception(str(e))
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
                    Log("GET_KEY: %s", item)
                    return AgentBase.key_map[item['agent']]
        except Exception as e:
            Log.Exception(str(e))


    @staticmethod
    def my_JSON_ObjectFromURL(url, timeout=None, retry=1, method='GET', values=None):
        try:
            if timeout is None:
                timeout = int(Prefs['timeout'])
            return JSON.ObjectFromURL(url, timeout=timeout, method=method, values=values)
        except Exception as e:
            if retry < 4:
                Log.Error("retry=%s url='%s' error='%s'", retry, url, str(e))
                time.sleep(1)
                return AgentBase.my_JSON_ObjectFromURL(url, timeout, retry=(retry + 1), method=method, values=values)
            else:
                Log.Error('CRITICAL my_JSON_ObjectFromURL error')


    def get_keyword_from_file(self, media):
        try:
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s' % media.id)
            filename = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']
            ret = os.path.splitext(os.path.basename(filename))[0]
            return ret
        except Exception as e:
            Log.Exception(str(e))

    def get_token(self, local=True):
        # 'Critical', 'Debug', 'Error', 'Exception', 'Info', 'Stack', 'Warn'
        try:
            if Core.sandbox.context and local:
                token = getattr(Core.sandbox.context, 'token', None)
                if token:
                    return token
        except Exception:
            pass
        try:
            token = Prefs['plex_token']
            if isinstance(token, (str, unicode)):
                token = token.strip()
                if token:
                    return token
        except Exception:
            pass

        if self.token:
            return self.token

        try:
            current_os = Platform.OS
            Log.Debug('현재 운영체제: %s', current_os)
            if current_os == 'Windows':
                Log.Warn('Windows 환경에서는 에이전트 설정에 토큰을 직접 입력해 주세요.')
                return

            pms_root = Core.app_support_path
            pref_filepath = Core.storage.join_path(pms_root, 'Preferences.xml')
            if Core.storage.file_exists(pref_filepath):
                Log('파일을 찾았습니다: %s', pref_filepath)
                file_data = Core.storage.load(pref_filepath)
                if file_data:
                    prefs_xml = XML.ElementFromString(file_data)
                    token = prefs_xml.get('PlexOnlineToken')
                    if token:
                        self.token = token.strip()
                        Log('Preferences.xml에서 토큰을 가져왔습니다.')
                        return self.token
        except Exception:
            Log.Exception('토큰 확인 중 오류가 발생했습니다.')
        Log.Error('토큰을 가져오지 못 했습니다.')

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
                elif self.module_name in ['jav_censored', 'jav_uncensored']:
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
                elif self.module_name == 'western':
                    section_id_list = []
                    if Prefs['filename_json'] is not None:
                        section_id_list = Prefs['filename_json'].split(',')
                    if Prefs['filename_json'] == 'all' or section_id in section_id_list:
                        file_base = os.path.splitext(os.path.basename(filename))[0]
                        ret = os.path.join(os.path.dirname(filename), '%s.json' % file_base)
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
            Log.Exception(str(e))


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
            Log.Exception(str(e))
        return False



    def get_info_json(self, media):
        try:
            filepath = self.get_json_filepath(media)
            if filepath is None:
                return
            return self.read_json(filepath)
        except Exception as e:
            Log.Exception(str(e))


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
            Log.Exception(str(e))
        return False


    def remove_info(self, media):
        try:
            ret = self.get_json_filepath(media)
            # 구드공인 경우 캐시때문에 exists 함수 실패하는 것 같음.
            if ret is not None: #and os.path.exists(ret):
                Log("info.json 삭제 시도 #1: %s", ret)
                os.remove(ret)
                #time.sleep(2)
        except Exception as e:
            try:
                Log("info.json 삭제 시도 #2: %s", ret)
                #os.system('rm %s' % ret)
                # 2021-11-27 by lapis https://sjva.me/bbs/board.php?bo_table=suggestions&wr_id=1978
                os.system('rm "%s"' % ret)
            except Exception:
                pass
            #Log.Exception(str(e))


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
            Log.Exception(str(e))
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
            Log.Exception(str(e))
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
            Log.Exception(str(e))
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
            Log.Exception(str(e))
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
            Log.Exception(str(e))
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
        except Exception as e:
            Log.Exception(str(e))


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

        except Exception as e:
            Log.Exception(str(e))

    def set_data_person(self, meta, data, field, is_primary):
        try:
            meta = getattr(meta, field)
            value = self.get_person_list(data, field)
            if len(value) > 0:
                meta.clear()
                for person in value:
                    meta_person = meta.new()
                    display_name = self.get(person, 'name_ko', None) or self.get(person, 'name_org', None) or self.get(person, 'name', None)
                    meta_person.name = display_name
                    meta_person.role = self.get(person, 'name_org', None) or self.get(person, 'role', None)
                    meta_person.photo = self.get(person, 'photo', None) or self.get(person, 'thumb', None)
            elif is_primary:
                meta.clear()

        except Exception as e:
            Log.Exception(str(e))

    def set_data_media(self, meta, data, field, is_primary):
        try:
            meta = getattr(meta, field)
            if is_primary:
                valid_names = set()
            else:
                valid_names = set(meta.keys())
            value = self.get_media_list(data, field)
            if len(value) > 0:
                for media in value:
                    image_url = media.get('url') or media.get('thumb')
                    if not image_url or image_url in valid_names:
                        continue
                    self.set_http_data(image_url, meta, valid_names, preview=media.get('thumb'))
            meta.validate_keys(valid_names)
            #Log(meta)

        except Exception as e:
            Log.Exception(str(e))

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

        except Exception as e:
            Log.Exception(str(e))

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
            elif is_primary:
                #Log(meta)
                #meta.clear()
                pass
        except Exception as e:
            Log.Exception(str(e))


    def yaml_load(self, filepath):
        #data = self.yaml_load(filepath)
        #data = yaml.load(io.open(filepath), Loader=yaml.BaseLoader)
        try:
            with io.open(filepath, encoding='utf-8') as f:
                return yaml.load(f, Loader=yaml.BaseLoader)
        except (UnicodeDecodeError, Exception):
            Log.Exception(filepath)
            try:
                with io.open(filepath, encoding='euc-kr') as f:
                    return yaml.load(f, Loader=yaml.BaseLoader)
            except Exception:
                Log.Exception(filepath)



    def get_code_from_folderpath(self, media):
        # 2024.09.23 폴더명에서 정보얻기
        # 카테고리는 char 무시. 영화:M, 쇼:F
        try:
            jsonpath = self.get_json_filepath(media)
            foldername = os.path.basename(os.path.dirname(jsonpath))
            Log('폴더명: %s', foldername)
            match = re.search('[\[\{](?P<code>([a-zA-Z0-9]+)|(tmdb\-\d+)|(tvdb\-\d+))[\]\}]', foldername, re.IGNORECASE)
            if match:
                tmp = match.group('code')
                code = tmp.replace('tmdb-', 'MT').replace('tvdb-', 'FU')
                Log('get_code_from_folderpath: %s', code)
                return code
        except Exception as e:
            Log.Exception(str(e))


    @classmethod
    def get_code_from_text(cls, text, movie=False):
        match = cls.site_code_ptn.search(text)
        if match:
            site = match.group('site')
            code = match.group('code')
            site_code = cls.site_code_mapping[site.lower()] + code
            if movie:
                site_code = site_code.replace('FT', 'MT')
            return site_code


    def set_http_data(self, url, container, valid_names, preview=None):
        """
        2026-03-25 halfaider
        Media는 다운로드를 즉시 하고 Preview는 나중에 필요할 때 다운로드 하는 방식
        둘 다 새로고침 시 이미지를 다운로드해서 agent 폴더에 저장함
        플렉스에서 포스터를 표시하려고 할 때,
        Preview는 저장된 파일이 원본이 아니라 판단하고 URL로부터 직접 원본 이미지를 다운받아 처리함
        Media는 저장된 파일이 원본이라 판단해서 추가 다운로드 없이 처리함
        미리 다운로드해 놓을 것이냐 아니면 필요할 때 다운로드할 것이냐의 차이
        """
        sort_order = len(valid_names) + 1

        def process(target_url, proxy_class):
            try:
                data = HTTP.Request(target_url).content
            except Exception as e:
                data = None
                Log.Error("다운로드 실패 (%s): %s", target_url, str(e))

            if data and len(data) >= 16:
                # 추가할 때는 원본 url
                container[url] = proxy_class(data, sort_order=sort_order)
                if url not in valid_names:
                    if isinstance(valid_names, list):
                        valid_names.append(url)
                    elif isinstance(valid_names, set):
                        valid_names.add(url)
            else:
                Log.Warn("유효하지 않은 데이터: %s", target_url)

        if preview:
            process(preview, Proxy.Preview)
        else:
            process(url, Proxy.Media)


    def is_yaml_enabled(self, media):
        try:
            section_id = self.get_section_id(media.id)
            if section_id:
                section_id = int(section_id)
                disallowed_sections = self.get_user_sections('yaml_disabled_sections', section_id)
                Log.Debug("[%s] media section id: %s", media.id, section_id)
                Log.Debug("[%s] yaml disabled libraries: %s", media.id, disallowed_sections)
                return section_id not in disallowed_sections
        except Exception as e:
            Log.Exception(str(e))
        return True


    def remove_metadata(self, metadata, media, metadata_type="TV Shows"):
        """
        2026-03-19 halfaider
        업데이트 전 번들 폴더를 삭제
        """
        try:
            if not Prefs['remove_metadata_on_update']:
                return
        except Exception:
            return

        try:
            pms_root = Core.app_support_path
            uid_hash = Core.data.hashing.sha1(metadata.guid)
            bundle_path = Core.storage.join_path(pms_root, "Metadata", metadata_type, uid_hash[0], uid_hash[1:] + '.bundle')
            if not Core.storage.dir_exists(bundle_path):
                Log("[%s] 삭제할 번들 폴더가 없습니다: %s", media.id, bundle_path)
                return

            to_be_removed = []
            upload_path = Core.storage.join_path(bundle_path, "Uploads")
            to_be_removed.append(upload_path)

            content_path = Core.storage.join_path(bundle_path, "Contents")
            if metadata.contributors:
                for contributor in metadata.contributors:
                    contributor_path = Core.storage.join_path(content_path, contributor)
                    to_be_removed.append(contributor_path)

            for target_path in to_be_removed:
                try:
                    if Core.storage.dir_exists(target_path):
                        Core.storage.remove_tree(target_path)
                        Log("[%s] 삭제됨: %s", media.id, target_path)
                except Exception as e:
                    Log.Exception("[%s] 삭제 실패: %s", media.id, target_path)
        except Exception as e:
            Log.Exception("[%s] 번들 폴더 삭제 실패: %s", media.id, str(e))


    def get_section_id(self, media_id):
        url = 'http://127.0.0.1:32400/library/metadata/%s' % media_id
        try:
            data = AgentBase.my_JSON_ObjectFromURL(url)
            return data['MediaContainer']['librarySectionID']
        except Exception as e:
            Log.Error("[%s] Failed to get section id: %s", media_id, str(e))


    def set_themes(self, metadata, remote_metadata, valid_names, tvdb_id=None):
        # 테마
        if 'themes' in remote_metadata.get('extra_info') or {}:
            for tmp in remote_metadata['extra_info'].get('themes') or ():
                try:
                    if tmp not in valid_names:
                        self.set_http_data(tmp, metadata.themes, valid_names)
                except Exception: pass

        if tvdb_id:
            theme_url = 'https://tvthemes.plexapp.com/%s.mp3' % tvdb_id
            if theme_url not in valid_names:
                try:
                    self.set_http_data(theme_url, metadata.themes, valid_names)
                except Exception: pass


    def set_roles(self, metadata, remote_metadata, role_types=('actor',)):
        for role_type in role_types:
            for item in remote_metadata.get(role_type) or ():
                display_name = item.get('name_ko') or item.get('name_org') or item.get('name') or item.get('name_en') or item.get('name2') or item.get('name_original')
                if display_name:
                    actor = metadata.roles.new()
                    actor.name = display_name
                    actor.role = item.get('name_org') or item.get('originalname') or item.get('role') or '출연'
                    actor.photo = item.get('thumb') or item.get('photo') or item.get('image')
                #Log.Debug('%s - %s'% (actor.name, actor.photo))


    def set_extras(self, metadata, remote_metadata):
        for item in remote_metadata.get('extras') or ():
            try:
                mode = item.get('mode') or ''
                content_url = item.get('content_url') or ''
                content_type = item.get('content_type') or 'other'
                extra_class = self.extra_map.get(content_type.lower())
                if not extra_class or not mode or not content_url:
                    continue
                url = 'sjva://sjva.me/playvideo/%s|%s' % (mode, content_url)
                metadata.extras.add(extra_class(
                    url=url,
                    title=self.change_html(item.get('title') or ""),
                    originally_available_at=Datetime.ParseDate(item.get('premiered') or "1900-01-01").date(),
                    thumb=item.get('thumb') or ''
                ))
            except Exception as e:
                Log.Error(str(e))


    def parse_guid(self, guid):
        path = guid.split("?")[0].split("://")[-1]
        parts = path.split("/")
        show_id, season, episode = (parts + [None, None])[:3]
        return {
            'show': show_id,
            'season': season,
            'episode': episode,
            'is_episode': bool(episode)
        }


    def convert_season_index(self, season_index):
        try:
            index = int(season_index)
        except Exception:
            index = 1
        # 여섯 자리 이상은 1 시즌 취급 (202501)
        if index > 99999:
            index = 1
        # 네 자리 이상은 사용자 정의 시즌
        elif index > 999:
            index = index
        # 세 자리 이상은 재생 버전별 시즌
        elif index > 99:
            index = index % 100
        return str(index)


    def reset_episode_metadata(self, episode):
        episode.title = None
        episode.summary = None
        episode.originally_available_at = None
        episode.rating = None
        episode.duration = None
        episode.content_rating = None
        episode.content_rating_age = None
        episode.writers.clear()
        episode.directors.clear()
        episode.producers.clear()
        episode.guest_stars.clear()
        episode.thumbs.validate_keys([])
        episode.absolute_index = None
        return episode


    def get_ff_apikey(self, module_name):
        try:
            module_prefs = self.get_module_prefs(module_name)
            return module_prefs['apikey'] if module_prefs['apikey'] else Prefs['apikey']
        except Exception:
            return ""


    def get_api_url(self, module_name, path):
        try:
            param = ''
            if module_name in ['music_normal_artist', 'music_normal_album']:
                param = module_name.split('_')[-1]
                module_name = 'music_normal'
            module_prefs = self.get_module_prefs(module_name)
            server = module_prefs['server'] if module_prefs['server'] else Prefs['server']
            server = server.strip(' /') + '/'
            mod_path = "metadata/api/{module_name}/{path}?call=plex&param={param}".format(
                module_name=module_name.strip(' /'),
                path=path.strip(' /'),
                param=param
            )
            return String.JoinURL(server, mod_path)
        except Exception as e:
            Log.Exception(str(e))


    def put_artwork(self, media_id, artwork_url, element="clearLogo"):
        # "thumb" "art" "clearLogo" "squareArt" "banner" "poster" "theme"
        url = "http://127.0.0.1:32400/library/metadata/{media_id}/{element}?url={artwork_url}".format(
            media_id=media_id,
            element=element,
            artwork_url=String.Quote(artwork_url)
        )
        try:
            HTTP.Request(url, method='PUT').content
        except Exception as e:
            Log.Error("이미지 업데이트 실패: %s", str(e))


    def get_matches(self, meta_id, title, year=1900, agent="tv.plex.agents.movie", lang="ko-KR"):
        url = "http://127.0.0.1:32400/library/metadata/{meta_id}/matches?manual=1&title={title}&year={year}&agent={agent}&language={lang}".format(
            meta_id=meta_id,
            title=String.Quote(title),
            year=year,
            agent=String.Quote(agent),
            lang=String.Quote(lang)
        )
        try:
            data = self.my_JSON_ObjectFromURL(url)
            if data:
                return (data.get('MediaContainer') or {}).get('SearchResult') or []
        except Exception:
            Log.Exception("매칭 검색 실패: %s (%s)", meta_id, title, year)
        return []


    def get_plex_metadata(self, plex_guid):
        guid = plex_guid.rsplit('/')[-1]
        url = "https://metadata.provider.plex.tv/library/metadata/{guid}".format(
            guid=guid,
        )
        try:
            data = JSON.ObjectFromURL(url, headers={"accpet": "application/json", "X-Plex-Token": self.get_token(local=False)})
            if data:
                return ((data.get('MediaContainer') or {}).get('Metadata') or [{}])[0]
        except Exception:
            Log.Error("플렉스 메타데이터를 가져올 수 없습니다: %s", plex_guid)
        return {}


    def get_user_sections(self, setting_name, default_section=0):
        user_sections = []
        try:
            user_setting = Prefs[setting_name]
            if user_setting == 'all' and default_section:
                user_sections.append(default_section)
            else:
                for setting in Regex(r'\W+').split(user_setting or ''):
                    if not setting:
                        continue
                    try:
                        user_sections.append(int(setting))
                    except Exception:
                        pass
        except Exception as e:
            Log.Error("%s 설정 오류 발생: %s", setting_name, str(e))
        return user_sections


    def plex_exclusive(self, metadata_id, section_id):
        section_id = int(section_id)
        allowed_slug_sections = self.get_user_sections('plex_exclusive_sections', section_id)

        if section_id not in allowed_slug_sections:
            return

        server = None
        apikey = None
        try:
            server = Prefs['server']
            apikey = Prefs['apikey']
            plex_exclusive_server = Prefs['plex_exclusive_server']
            alt_server, _, alt_apikey = plex_exclusive_server.partition('|')
            alt_server = alt_server.strip()
            if alt_server:
                server = alt_server
                apikey = alt_apikey.strip()
        except Exception:
            pass
        if not server:
            Log.Error("서버 정보가 없어서 요청을 취소합니다: %s", server)
            return
        try:
            only_tmdb = Prefs['plex_exclusive_only_tmdb']
        except Exception:
            only_tmdb = True
        try:
            url = "{server}/plex_mate/api/tool/plex_exclusive?metadata_id={metadata_id}&manual=true&only_tmdb={only_tmdb}".format(
                server=server,
                metadata_id=metadata_id,
                only_tmdb=only_tmdb
            )
            HTTP.Request(url, timeout=10, values={'apikey': apikey}, method="POST").content
        except Exception as e:
            Log.Error("플렉스 정보 업데이트 요청 실패: %s", str(e))


    def update_logo(self, metadata_id, section_id, image_container):
        section_id = int(section_id)
        allowed_logo_sections = self.get_user_sections('clear_logo_sections', section_id)
        if section_id not in allowed_logo_sections:
            return

        for logo in sorted(
            (art for art in image_container if art.get('aspect') == 'logo'),
            key=lambda k: k.get('score') or 0,
            reverse=True
        ):
            logo_url = logo.get('value') or logo.get('thumb')
            if logo_url:
                try:
                    self.put_artwork(metadata_id, logo_url)
                except Exception:
                    Log.error("로고 업데이트 실패: %s", logo_url)
                break


class PutRequest(urllib2.Request):
    def __init__(self, *args, **kwargs):
        return urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self, *args, **kwargs):
        return 'PUT'


def get_sort_key(x):
    try:
        return int(x)
    except Exception:
        return x
