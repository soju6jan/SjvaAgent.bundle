# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, time, urllib2
from io import open
from .agent_base import AgentBase

class ModuelYamlBase(AgentBase):
    
    def get_yaml_filepath(self, media, content_type):
        try:
            metadata_key = media if type(media) == type('') else media.id
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s?includeChildren=1' % metadata_key)
            section_id = str(data['MediaContainer']['librarySectionID'])
            #Log(self.d(data))
            """
            if data['MediaContainer']['Metadata'][0]['type'] == 'album':
                data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s/children' % media.id)
                #Log(self.d(data))
            elif data['MediaContainer']['Metadata'][0]['type'] == 'artist':
                data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s/children' % data['MediaContainer']['Metadata'][0]['Children']['Metadata'][0]['ratingKey'])
            """

            if content_type == 'movie':
                # 파일명.yaml / xxx-aaa.yaml / movie.yaml
                folder_list = []
                if 'Media' in data['MediaContainer']['Metadata'][0]:
                    for media in data['MediaContainer']['Metadata'][0]['Media']:
                        for part in media['Part']:
                            filepath = part['file']
                            folderpath = os.path.dirname(filepath)
                            filename = os.path.basename(filepath)
                            tmp = os.path.splitext(filename)
                            yaml_filepath = os.path.join(folderpath, '%s.yaml' % tmp[0])
                            if os.path.exists(yaml_filepath):
                                return yaml_filepath
                            code = tmp[0].split(' ')[0]
                            if code[-2] == 'd' and code [-3] == 'c':
                                code = code[:-3].strip(' .-')
                            yaml_filepath = os.path.join(folderpath, '%s.yaml' % code)
                            if os.path.exists(yaml_filepath):
                                return yaml_filepath
                            yaml_filepath = os.path.join(folderpath, 'movie.yaml')
                            if os.path.exists(yaml_filepath):
                                return yaml_filepath
            elif content_type == 'show':
                filepath_list = {'show':None, 'seasons':[]}
                if 'Location' in data['MediaContainer']['Metadata'][0]:
                    folderpath = data['MediaContainer']['Metadata'][0]['Location'][0]['path']
                    yaml_filepath = os.path.join(folderpath, 'show.yaml')
                    if os.path.exists(yaml_filepath):
                        filepath_list['show'] = yaml_filepath
                    filelist = os.listdir(folderpath)
                    for filename in filelist:
                        filepath = os.path.join(folderpath, filename)
                        if os.path.isdir(filepath):
                            season_yaml_filepath = os.path.join(filepath, 'season.yaml')
                            if os.path.exists(season_yaml_filepath):
                                filepath_list['seasons'].append(season_yaml_filepath)
                    return filepath_list
            elif content_type == 'album':
                data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s/children' % metadata_key)
                filename = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']
                parent = os.path.split(os.path.dirname(filename))[1]
                match = re.match('CD(?P<disc>\d+)', parent, re.IGNORECASE)
                if match:
                    album_root = os.path.dirname(os.path.dirname(filename))
                else:
                    album_root = os.path.dirname(filename)

                #yaml_filepath = os.path.join(os.path.dirname(filename), 'album.yaml')
                yaml_filepath = os.path.join(album_root, 'album.yaml')

                if os.path.exists(yaml_filepath):
                    return yaml_filepath
            elif content_type == 'artist':
                data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s/children' % data['MediaContainer']['Metadata'][0]['Children']['Metadata'][0]['ratingKey'])
                filename = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']
                parent = os.path.split(os.path.dirname(filename))[1]
                match = re.match('CD(?P<disc>\d+)', parent, re.IGNORECASE)
                    
                if match:
                    album_root = os.path.dirname(os.path.dirname(filename))
                else:
                    album_root = os.path.dirname(filename)
                album_basename = os.path.basename(album_root)
                if False and album_basename.count(' - ') == 1:
                    yaml_filepath = os.path.join(album_root, 'artist.yaml')
                else:
                    # 2022-05-02
                    # V.A 가있다는 것은 카테-앨범 구조라고 픽스
                    # 없다면 카테 - 아티스트 - 앨범
                    # OST 컴필 등
                    artist_root = os.path.dirname(album_root)
                    cate_root = os.path.dirname(artist_root)
                    va_flag = None
                    if os.path.exists(os.path.join(cate_root, 'VA1')):
                        va_flag = "va_depth1"
                    elif os.path.exists(os.path.join(cate_root, 'VA2')):
                        va_flag = "va_depth2_artist_dummy"
                    elif os.path.exists(os.path.join(artist_root, 'VA2')):
                        va_flag = "va_depth1"

                    if va_flag == None or va_flag == 'va_depth2_artist_dummy':
                        yaml_filepath = os.path.join(artist_root, 'artist.yaml')
                    elif va_flag == 'va_depth1':
                        yaml_filepath = os.path.join(album_root, 'artist.yaml')

                if os.path.exists(yaml_filepath):
                    return yaml_filepath
                
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())

    
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
            #Log('set_data : %s', field)
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
            #Log(meta)

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
            elif is_primary:
                #Log(meta)
                #meta.clear()
                pass
        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())

