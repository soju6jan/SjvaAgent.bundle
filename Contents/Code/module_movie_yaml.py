# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, random, time, io
from .agent_base import AgentBase
import yaml

extra_type_map = {
    'trailer' : TrailerObject,
    'deleted' : DeletedSceneObject,
    'behindthescenes' : BehindTheScenesObject,
    'interview' : InterviewObject,
    'scene' : SceneOrSampleObject,
    'featurette' : FeaturetteObject,
    'short' : ShortObject,
    'other' : OtherObject
}


class ModuleMovieYaml(AgentBase):
    module_name = 'movie_yaml'
    
    def get(self, data, field, default):
        ret = data.get(field, None)
        if ret is None:
            ret = default
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
                for value in ret.split(','):
                    tmp.append({'url':value.strip()})
                ret = tmp
        return ret 
    
    def search(self, results, media, lang, manual, **kwargs):
        try:
            filepath = self.get_yaml_filepath(media, 'movie')
            Log('YAML : %s', filepath)
            if filepath is None:
                return False
            data = yaml.load(io.open(filepath), Loader=yaml.FullLoader)
            Log(self.d(data))
            is_primary = self.get(data, 'primary', False)
            if is_primary == False:
                return False
            timestamp = int(time.time())
            posters = self.get(data, 'posters', None)
            thumb = ''
            if posters is not None:
                thumb = self.get(posters[0], 'thumb', '')
                if thumb == '':
                    thumb = self.get(posters[0], 'url', '')
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


    def update(self, metadata, media, lang):
        try:
            filepath = self.get_yaml_filepath(media, 'movie')
            Log('YAML movie : %s', filepath)
            if filepath is None:
                return False
            data = yaml.load(io.open(filepath), Loader=yaml.FullLoader)
            Log(self.d(data))

            metadata.title = self.get(data, 'title', media.title)
            metadata.original_title = self.get(data, 'original_title', metadata.title)
            metadata.title_sort = unicodedata.normalize('NFKD', self.get(data, 'title_sort', metadata.title))


            try: 
                metadata.originally_available_at = Datetime.ParseDate(self.get(data, 'originally_available_at', '1900-12-31').replace('.', '-')).date()
                metadata.year = self.get(data, 'year', metadata.originally_available_at.year if metadata.originally_available_at.year != 1900 else '')
            except Exception as e: 
                Log(str(e))

            metadata.studio = self.get(data, 'studio', None)
            metadata.content_rating = self.get(data, 'content_rating', None)
            metadata.tagline = self.get(data, 'tagline', None)
            metadata.summary = self.get(data, 'summary', None)

            metadata.rating = self.get(data, 'rating', None)
            metadata.rating_image = self.get(data, 'rating_image', None)
            metadata.audience_rating = self.get(data, 'audience_rating', None)
            metadata.audience_rating_image = self.get(data, 'audience_rating_image', None)


            field_list = [
                ['genres', metadata.genres],
                ['collections', metadata.collections],
                ['countries', metadata.countries],
                ['similar', metadata.similar],
            ]

            for field in field_list:
                field[1].clear()
                for value in self.get_list(data, field[0]):
                    field[1].add(value)

            field_list = [
                ['writers', metadata.writers],
                ['directors', metadata.directors],
                ['producers', metadata.producers],
                ['roles', metadata.roles],
            ]
            for field in field_list:
                field[1].clear()
                for person in self.get_person_list(data, field[0]):
                    meta_person = field[1].new()
                    meta_person.name = self.get(person, 'name', None)
                    meta_person.role = self.get(person, 'role', None)
                    meta_person.photo = self.get(person, 'photo', None)

            field_list = [
                ['posters', metadata.posters],
                ['art', metadata.art],
                ['themes', metadata.themes],
            ]
            for field in field_list:
                valid_names = []
                for idx, media in enumerate(self.get_media_list(data, field[0])):
                    valid_names.append(media['url'])
                    if 'thumb' in media:
                        field[1][media['url']] = Proxy.Preview(HTTP.Request(media['thumb']).content, sort_order=idx+1)
                    else:
                        field[1][media['url']] = Proxy.Preview(HTTP.Request(media['url']).content, sort_order=idx+1)
                field[1].validate_keys(valid_names)

            metadata.reviews.clear()
            for review in self.get(data, 'reviews', []):
                r = metadata.reviews.new()
                r.author = self.get(review, 'author', None)
                r.source = self.get(review, 'source', None)
                r.image = self.get(review, 'image', None)
                r.link = self.get(review, 'link', None)
                r.text = self.get(review, 'text', None)

            for extra in self.get(data, 'extras', []):
                mode = self.get(extra, 'mode', None)
                extra_type = self.get(extra, 'type', 'trailer')
                extra_class = extra_type_map[extra_type]
                url = 'sjva://sjva.me/playvideo/%s|%s' % (mode, extra.get('param'))

                metadata.extras.add(
                    extra_class(
                        url=url, 
                        title=self.change_html(extra.get('title', '')),
                        originally_available_at = Datetime.ParseDate(self.get(extra, 'originally_available_at', '1900-12-31').replace('.', '-')).date(),
                        thumb=self.get(extra, 'thumb', '')
                    )
                )
            return
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())

    # 다른 모듈에서 처리한 이후 있는 값들만 덮어씌움.
    def contribute(self, metadata, media, lang):
        try:
            filepath = self.get_yaml_filepath(media, 'movie')
            Log('YAML movie : %s', filepath)
            if filepath is None:
                return False
            data = yaml.load(io.open(filepath), Loader=yaml.FullLoader)
            Log(self.d(data))

            value = self.get(data, 'title', None)
            if value is not None:
                metadata.title = value
            
            value = self.get(data, 'original_title', None)
            if value is not None:
                metadata.original_title = value

            value = self.get(data, 'title_sort', None)
            if value is not None:
                metadata.title_sort = unicodedata.normalize('NFKD', value)

            value = self.get(data, 'originally_available_at', None)
            if value is not None:
                metadata.originally_available_at = Datetime.ParseDate(value.replace('.', '-')).date()
            
            value = self.get(data, 'year', None)
            if value is not None:
                metadata.year = value

            value = self.get(data, 'studio', None)
            if value is not None:
                metadata.studio = value
            
            value = self.get(data, 'content_rating', None)
            if value is not None:
                metadata.content_rating = value
            
            value = self.get(data, 'tagline', None)
            if value is not None:
                metadata.tagline = value

            value = self.get(data, 'summary', None)
            if value is not None:
                metadata.summary = value
            
            value = self.get(data, 'rating', None)
            if value is not None:
                metadata.rating = value
            
            value = self.get(data, 'rating_image', None)
            if value is not None:
                metadata.rating_image = value
            
            value = self.get(data, 'audience_rating', None)
            if value is not None:
                metadata.audience_rating = value
            
            value = self.get(data, 'audience_rating_image', None)
            if value is not None:
                metadata.audience_rating_image = value
            
            field_list = [
                ['genres', metadata.genres],
                ['collections', metadata.collections],
                ['countries', metadata.countries],
                ['similar', metadata.similar],
            ]

            for field in field_list:
                value = self.get_list(data, field[0])
                if len(value) > 0:
                    field[1].clear()
                    for tmp in value:
                        field[1].add(tmp)

            field_list = [
                ['writers', metadata.writers],
                ['directors', metadata.directors],
                ['producers', metadata.producers],
                ['roles', metadata.roles],
            ]
            for field in field_list:
                value = self.get_person_list(data, field[0])
                if len(value) > 0:
                    #field[1].clear()
                    for person in value:
                        meta_person = field[1].new()
                        meta_person.name = self.get(person, 'name', None)
                        meta_person.role = self.get(person, 'role', None)
                        meta_person.photo = self.get(person, 'photo', None)

            field_list = [
                ['posters', metadata.posters],
                ['art', metadata.art],
                ['themes', metadata.themes],
            ]
            for field in field_list:
                value = self.get_media_list(data, field[0])
                if len(value) > 0:
                    valid_names = []
                    for idx, media in enumerate(value):
                        valid_names.append(media['url'])
                        if 'thumb' in media:
                            field[1][media['url']] = Proxy.Preview(HTTP.Request(media['thumb']).content, sort_order=idx+1)
                        else:
                            field[1][media['url']] = Proxy.Preview(HTTP.Request(media['url']).content, sort_order=idx+1)
                    field[1].validate_keys(valid_names)

            value = self.get(data, 'reviews', [])
            if len(value) > 0:
                #metadata.reviews.clear()
                for review in value:
                    r = metadata.reviews.new()
                    r.author = self.get(review, 'author', None)
                    r.source = self.get(review, 'source', None)
                    r.image = self.get(review, 'image', None)
                    r.link = self.get(review, 'link', None)
                    r.text = self.get(review, 'text', None)

            value = self.get(data, 'extras', [])
            if len(value) > 0:
                for extra in value:
                    mode = self.get(extra, 'mode', None)
                    extra_type = self.get(extra, 'type', 'trailer')
                    extra_class = extra_type_map[extra_type]
                    url = 'sjva://sjva.me/playvideo/%s|%s' % (mode, extra.get('param'))
                    metadata.extras.add(
                        extra_class(
                            url=url, 
                            title=self.change_html(extra.get('title', '')),
                            originally_available_at = Datetime.ParseDate(self.get(extra, 'originally_available_at', '1900-12-31').replace('.', '-')).date(),
                            thumb=self.get(extra, 'thumb', '')
                        )
                    )
                return
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())