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
            meta = MetadataSearchResult(
                id=self.get(data, 'code', 'YM%s' % timestamp), 
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
                self.set_data(metadata.title, data, 'title', is_primary)
                self.set_data(metadata.original_title, data, 'original_title', is_primary)
                self.set_data(metadata.title_sort, data, 'title_sort', is_primary)
                self.set_data(metadata.originally_available_at, data, 'originally_available_at', is_primary)
                self.set_data(metadata.year, data, 'year', is_primary)
            
            self.set_data(metadata.studio, data, 'studio', is_primary)
            self.set_data(metadata.content_rating, data, 'content_rating', is_primary)
            self.set_data(metadata.tagline, data, 'tagline', is_primary)
            self.set_data(metadata.summary, data, 'summary', is_primary)
            self.set_data(metadata.rating, data, 'rating', is_primary)
            self.set_data(metadata.rating_image, data, 'rating_image', is_primary)
            self.set_data(metadata.audience_rating, data, 'audience_rating', is_primary)
            self.set_data(metadata.audience_rating_image, data, 'audience_rating_image', is_primary)
            self.set_data_list(metadata.genres, data, 'genres', is_primary)
            self.set_data_list(metadata.collections, data, 'collections', is_primary)
            self.set_data_list(metadata.countries, data, 'countries', is_primary)
            self.set_data_list(metadata.similar, data, 'similar', is_primary)
            self.set_data_person(metadata.writers, data, 'writers', is_primary)
            self.set_data_person(metadata.directors, data, 'directors', is_primary)
            self.set_data_person(metadata.producers, data, 'producers', is_primary)
            self.set_data_person(metadata.roles, data, 'roles', is_primary)
            self.set_data_media(metadata.posters, data, 'posters', is_primary)
            self.set_data_media(metadata.art, data, 'art', is_primary)
            self.set_data_media(metadata.themes, data, 'themes', is_primary)
            self.set_data_reviews(metadata.reviews, data, 'reviews', is_primary)
            self.set_data_extras(metadata.extras, data, 'extras', is_primary)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
