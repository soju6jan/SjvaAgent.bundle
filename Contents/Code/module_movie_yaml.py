# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, random, time, io
from .agent_base import AgentBase
import yaml

class ModuleMovieYaml(AgentBase):
    module_name = 'movie_yaml'
    
    def search(self, results, media, lang, manual, **kwargs):
        try:
            filepath = self.get_yaml_filepath(media, 'movie')
            Log('YAML : %s', filepath)
            if filepath is None:
                return False
            data = yaml.load(io.open(filepath), Loader=yaml.BaseLoader)
            Log(self.d(data))
            
            is_primary = self.get(data, 'primary', 'false')
            if is_primary != 'true':
                return False
            timestamp = int(time.time())
            posters = self.get_media_list(data, 'posters')
            thumb = posters[0]['url'] if posters else '' 
            code = self.get(data, 'code', 'YM%s' % timestamp)
            if code.startswith('YM'):
                code = 'YM%s' % code
            meta = MetadataSearchResult(
                id=code, 
                name=self.get(data, 'title', u'제목 - %s' % timestamp), 
                year=self.get(data, 'year', ''), 
                score=100, 
                thumb=thumb, 
                lang=lang
            )
            summary = self.get(data, 'tagline', '')
            if summary == '':
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
            filepath = self.get_yaml_filepath(media, 'movie')
            Log('YAML movie : %s', filepath)
            if filepath is None:
                return False
            data = yaml.load(io.open(filepath), Loader=yaml.BaseLoader)
            try: Log(self.d(data))
            except: pass
            if is_primary:
                metadata.title = self.get(data, 'title', media.title)
                metadata.original_title = self.get(data, 'original_title', metadata.title)
                metadata.title_sort = unicodedata.normalize('NFKD', self.get(data, 'title_sort', metadata.title))
                try: 
                    metadata.originally_available_at = Datetime.ParseDate(self.get(data, 'originally_available_at', '1900-12-31')).date()
                    metadata.year = self.get(data, 'year', metadata.originally_available_at.year if metadata.originally_available_at.year != 1900 else '')
                except Exception as e: 
                    Log(str(e))

            else:
                self.set_data(metadata, data, 'title', is_primary)
                self.set_data(metadata, data, 'original_title', is_primary)
                self.set_data(metadata, data, 'title_sort', is_primary)
                self.set_data(metadata, data, 'originally_available_at', is_primary)
                self.set_data(metadata, data, 'year', is_primary)
            
            self.set_data(metadata, data, 'studio', is_primary)
            self.set_data(metadata, data, 'content_rating', is_primary)
            self.set_data(metadata, data, 'tagline', is_primary)
            self.set_data(metadata, data, 'summary', is_primary)
            self.set_data(metadata, data, 'rating', is_primary)
            self.set_data(metadata, data, 'rating_image', is_primary)
            self.set_data(metadata, data, 'audience_rating', is_primary)
            self.set_data(metadata, data, 'audience_rating_image', is_primary)
            self.set_data_list(metadata, data, 'genres', is_primary)
            self.set_data_list(metadata, data, 'collections', is_primary)
            self.set_data_list(metadata, data, 'countries', is_primary)
            self.set_data_list(metadata, data, 'similar', is_primary)
            self.set_data_person(metadata, data, 'writers', is_primary)
            self.set_data_person(metadata, data, 'directors', is_primary)
            self.set_data_person(metadata, data, 'producers', is_primary)
            self.set_data_person(metadata, data, 'roles', is_primary)
            self.set_data_media(metadata, data, 'posters', is_primary)
            self.set_data_media(metadata, data, 'art', is_primary)
            self.set_data_media(metadata, data, 'themes', is_primary)
            self.set_data_reviews(metadata, data, 'reviews', is_primary)
            self.set_data_extras(metadata, data, 'extras', is_primary)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
