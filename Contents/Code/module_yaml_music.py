# -*- coding: utf-8 -*-
import os, unicodedata, traceback, io, time, random
from .module_yaml_base import ModuelYamlBase
import yaml

class ModuleYamlArtist(ModuelYamlBase):
    module_name = 'yaml_artist'
    
    def search(self, results, media, lang, manual, **kwargs):
        try:
            filepath = self.get_yaml_filepath(media, 'artist')
            Log('YAML artist: %s', filepath)
            if filepath is None:
                return False
            data = self.yaml_load(filepath)
            Log(self.d(data))
            is_primary = self.get(data, 'primary', 'false')
            if is_primary != 'true':
                return False
            timestamp = int(time.time())
            posters = self.get_media_list(data, 'posters')
            thumb = posters[0]['url'] if posters else '' 
            code = self.get(data, 'code', 'YR%s' % timestamp).replace(' ', '')
            if not code.startswith('YR'):
                code = 'YR%s' % code
            meta = MetadataSearchResult(
                id=code, 
                name=self.get(data, 'title', u'제목 - %s' % timestamp), 
                year='', 
                score=100, 
                thumb=thumb, 
                lang=lang
            )
            summary = self.get(data, 'summary', '')
            meta.summary = summary
            meta.type = "movie"
            results.Append(meta) 
            return True
        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())    
        return False


    def update(self, metadata, media, lang, is_primary=True):
        try:
            filepath = self.get_yaml_filepath(media, 'artist')
            Log(u"아티스트 업데이트 : %s", filepath)
            if filepath is None:
                return False
            data = self.yaml_load(filepath)
            try: Log(self.d(data))
            except: pass
            self.set_data(metadata, data, 'title', is_primary)
            Log(metadata.title)
            self.set_data(metadata, data, 'title_sort', is_primary)
            self.set_data(metadata, data, 'summary', is_primary)
            self.set_data_list(metadata, data, 'countries', is_primary)
            self.set_data_list(metadata, data, 'genres', is_primary)
            self.set_data_list(metadata, data, 'styles', is_primary)
            self.set_data_list(metadata, data, 'moods', is_primary)
            self.set_data_list(metadata, data, 'similar', is_primary)
            self.set_data_list(metadata, data, 'collections', is_primary)
            self.set_data_media(metadata, data, 'posters', is_primary)
            self.set_data_media(metadata, data, 'art', is_primary)
            self.set_data_media(metadata, data, 'themes', is_primary)
            self.set_data(metadata, data, 'rating', is_primary)
            self.set_data_extras(metadata, data, 'extras', is_primary)
            
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())

        

class ModuleYamlAlbum(ModuelYamlBase):
    module_name = 'yaml_album'
    
    def search(self, results, media, lang, manual, **kwargs):
        try:
            Log(media.title)
            filepath = self.get_yaml_filepath(media, 'album')
            Log('YAML ALBUM: %s', filepath)
            if filepath is None:
                return False
            data = self.yaml_load(filepath)
            Log(self.d(data))
            
            is_primary = self.get(data, 'primary', 'false')
            if is_primary != 'true':
                return False
            timestamp = int(time.time())
            posters = self.get_media_list(data, 'posters')
            thumb = posters[0]['url'] if posters else '' 
            code = self.get(data, 'code', 'YA%s' % timestamp).replace(' ', '')
            if not code.startswith('YA'):
                code = 'YA%s' % code
            year = self.get(data, 'available_at', '')
            if year != '':
                year = year.split('-')[0]
            meta = MetadataSearchResult(
                id=code, 
                name=self.get(data, 'title', u'제목 - %s' % timestamp), 
                year=year, 
                score=100, 
                thumb=thumb, 
                lang=lang
            )
            summary = self.get(data, 'summary', '')
            meta.summary = summary
            meta.type = "movie"
            results.Append(meta) 
            return True
        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())    
        return False



    def update(self, metadata, media, lang, is_primary=True):
        try:
            # title 일치항목 찾기로만 변경됨
            # collections 반영안됨
            # gernres등은 바로 반영
            filepath = self.get_yaml_filepath(media, 'album')
            Log(u"앨범 업데이트 : %s", filepath)
            if filepath is None:
                return
            data = self.yaml_load(filepath)
            try: Log(self.d(data))
            except: pass
            self.set_data(metadata, data, 'title', is_primary)
            self.set_data(metadata, data, 'title_sort', is_primary)
            self.set_data(metadata, data, 'originally_available_at', is_primary)
            self.set_data(metadata, data, 'available_at', is_primary)
            self.set_data(metadata, data, 'summary', is_primary)
            self.set_data(metadata, data, 'studio', is_primary)
            self.set_data_person(metadata, data, 'producers', is_primary)
            self.set_data_list(metadata, data, 'countries', is_primary)
            self.set_data_list(metadata, data, 'genres', is_primary)
            self.set_data_list(metadata, data, 'styles', is_primary)
            self.set_data_list(metadata, data, 'moods', is_primary)
            self.set_data_list(metadata, data, 'collections', is_primary)
            self.set_data_media(metadata, data, 'posters', is_primary)
            self.set_data_media(metadata, data, 'art', is_primary)
            self.set_data(metadata, data, 'rating', is_primary)
            self.set_data(metadata, data, 'rating_image', is_primary)
            #self.set_data(metadata, data, 'audience_rating', is_primary)
            #self.set_data(metadata, data, 'audience_rating_image', is_primary)

            # 이것을 꼭 해줘야 트랙이 소속됨.
            valid_track_keys = []
            for index in media.tracks:
                track_key = media.tracks[index].id or int(index)
                valid_track_keys.append(track_key)
                Log(track_key)
                filename = os.path.splitext(os.path.basename(media.tracks[index].items[0].parts[0].file))[0]
                Log(filename)
                t = metadata.tracks[track_key]
                Log('aaaaaaaaaaaaaaaaaaaaaaaa')
                Log(t.title)
                Log(t.artist)
                
                #self.set_data(metadata, data, 'extras', is_primary)
                #t.title = filename.strip(' -._')
                #t.original_title = data.get('author', '')
            metadata.tracks.validate_keys(valid_track_keys)
            return self.get_bool(data, 'lyric', True)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
