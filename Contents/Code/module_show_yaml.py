# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, random, time, io, urllib2
from .agent_base import AgentBase, PutRequest
import yaml

class ModuleShowYaml(AgentBase):
    module_name = 'show_yaml'
    
    def search(self, results, media, lang, manual, **kwargs):
        try:
            filepath = self.get_yaml_filepath(media, 'show')
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
            summary = self.get(data, 'summary', '')
            meta.summary = summary
            meta.type = "movie"
            results.Append(meta) 
            return True
        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())    
        return False


    



    # 다른 모듈에서 처리한 이후 있는 값들만 덮어씌움.
    def update(self, metadata, media, lang, is_primary=True):
        try:
            filepath_list = self.get_yaml_filepath(media, 'show')
            Log('YAML show : %s', filepath_list)
            if filepath_list['show'] is None and filepath_list['seasons'] == False:
                return False
            
            data = {}
            try:
                if filepath_list['show'] is not None:
                    data = yaml.load(io.open(filepath_list['show']), Loader=yaml.BaseLoader)
            except Exception as exception: 
                Log('Exception:%s', exception)
                Log(traceback.format_exc())  
            finally:
                if 'seasons' not in data:
                    data['seasons'] = {}
            
            for season_yamlpath in filepath_list['seasons']:
                try:
                    tmp = yaml.load(io.open(season_yamlpath), Loader=yaml.BaseLoader)
                    #data['seasons'].append(tmp)
                    if 'index' in tmp:
                        data['seasons'][str(tmp['index'])] = tmp
                except Exception as exception: 
                    Log('Exception:%s', exception)
                    Log(traceback.format_exc())  

            Log(self.d(data))

            if is_primary:
                metadata.title = self.get(data, 'title', media.title)
                metadata.original_title = self.get(data, 'original_title', metadata.title)
                metadata.title_sort = unicodedata.normalize('NFKD', self.get(data, 'title_sort', metadata.title))
                try: 
                    metadata.originally_available_at = Datetime.ParseDate(self.get(data, 'originally_available_at', '1900-12-31')).date()
                except Exception as e: 
                    Log(str(e))
            else:
                self.set_data(metadata.title, data, 'title')
                self.set_data(metadata.original_title, data, 'original_title')
                self.set_data(metadata.title_sort, data, 'title_sort')
                self.set_data(metadata.originally_available_at, data, 'originally_available_at')
                            

            self.set_data(metadata.studio, data, 'studio')
            self.set_data(metadata.content_rating, data, 'content_rating')
            self.set_data(metadata.summary, data, 'summary')
            self.set_data(metadata.rating, data, 'rating')
            
            field_list = [
                ['genres', metadata.genres],
                ['collections', metadata.collections],
                #['countries', metadata.countries],
                #['similar', metadata.similar],
            ]

            for field in field_list:
                value = self.get_list(data, field[0])
                if len(value) > 0:
                    field[1].clear()
                    for tmp in value:
                        field[1].add(tmp)

            field_list = [
                #['writers', metadata.writers],
                #['directors', metadata.directors],
                #['producers', metadata.producers],
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
                    for idx, me in enumerate(value):
                        valid_names.append(me['url'])
                        if 'thumb' in me:
                            field[1][me['url']] = Proxy.Preview(HTTP.Request(me['thumb']).content, sort_order=idx+1)
                        else:
                            field[1][me['url']] = Proxy.Preview(HTTP.Request(me['url']).content, sort_order=idx+1)
                    field[1].validate_keys(valid_names)

            value = self.get(data, 'extras', [])
            if len(value) > 0:
                for extra in value:
                    mode = self.get(extra, 'mode', None)
                    extra_type = self.get(extra, 'type', 'trailer')
                    extra_class = self.extra_map[extra_type.lower()]
                    url = 'sjva://sjva.me/playvideo/%s|%s' % (mode, extra.get('param'))
                    metadata.extras.add(
                        extra_class(
                            url=url, 
                            title=self.change_html(extra.get('title', '')),
                            originally_available_at = Datetime.ParseDate(self.get(extra, 'originally_available_at', '1900-12-31')).date(),
                            thumb=self.get(extra, 'thumb', '')
                        )
                    )
                
            Log(media)
            index_list = [index for index in media.seasons]
            index_list = sorted(index_list)
            Log('11111111111111111111111111111111111')
            Log(index_list)

            for media_season_index in index_list:
                Log('media_season_index is %s', media_season_index)
                if media_season_index == '0':
                    continue
                metadata_season = metadata.seasons[media_season_index]
                Log('22222222222222222')
                Log(metadata_season)
                Log(metadata_season.title)

                if str(media_season_index) not in data['seasons']:
                    continue
                data_season = data['seasons'][str(media_season_index)]
                Log(self.d(data_season))

                value = self.get(data_season, 'title', None)
                if value is not None:
                    #metadata_season.title = value
                    self.set_season_info_by_web(media, media_season_index,  title=value)
                
                value = self.get(data_season, 'summary', None)
                if value is not None:
                    #metadata_season.summary = value
                    self.set_season_info_by_web(media, media_season_index, summary=value)

                field_list = [
                    ['posters', metadata_season.posters],
                    ['art', metadata_season.art],
                ]
                for field in field_list:
                    value = self.get_media_list(data_season, field[0])
                    if len(value) > 0:
                        valid_names = []
                        for idx, me in enumerate(value):
                            valid_names.append(me['url'])
                            if 'thumb' in me:
                                field[1][me['url']] = Proxy.Preview(HTTP.Request(me['thumb']).content, sort_order=idx+1)
                            else:
                                field[1][me['url']] = Proxy.Preview(HTTP.Request(me['url']).content, sort_order=idx+1)
                        field[1].validate_keys(valid_names)

                value = self.get(data_season, 'extras', [])
                if len(value) > 0:
                    for extra in value:
                        mode = self.get(extra, 'mode', None)
                        extra_type = self.get(extra, 'type', 'trailer')
                        extra_class = self.extra_map[extra_type.lower()]
                        url = 'sjva://sjva.me/playvideo/%s|%s' % (mode, extra.get('param'))
                        metadata_season.extras.add(
                            extra_class(
                                url=url, 
                                title=self.change_html(extra.get('title', '')),
                                originally_available_at = Datetime.ParseDate(self.get(extra, 'originally_available_at', '1900-12-31')).date(),
                                thumb=self.get(extra, 'thumb', '')
                            )
                        )




                for media_episode_index in media.seasons[media_season_index].episodes:
                    metadata_episode = metadata.seasons[media_season_index].episodes[media_episode_index]
                    Log(metadata_episode)
                    Log(metadata_episode.index)
                    Log(media_episode_index)

                    
                    if 'episodes' not in data_season or str(media_episode_index) not in data_season['episodes']:
                        continue

                    data_episode = data_season['episodes'][str(media_episode_index)]
                    Log(self.d(data_episode))
                    

                    value = self.get(data_episode, 'title', None)
                    if value is not None:
                        metadata_episode.title = value
                        
                    value = self.get(data_episode, 'summary', None)
                    if value is not None:
                        metadata_episode.summary = value


                    value = self.get(data_episode, 'originally_available_at', None)
                    if value is not None:
                        metadata.originally_available_at = Datetime.ParseDate(value).date()


                    field_list = [
                        ['writers', metadata_episode.writers],
                        ['directors', metadata_episode.directors],
                        #['producers', metadata_episode.producers],
                        #['guest_stars', metadata_episode.guest_stars],
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
                        ['thumbs', metadata_episode.thumbs],
                    ]
                    for field in field_list:
                        value = self.get_media_list(data_episode, field[0])
                        if len(value) > 0:
                            valid_names = []
                            for idx, me in enumerate(value):
                                valid_names.append(me['url'])
                                if 'thumb' in me:
                                    field[1][me['url']] = Proxy.Preview(HTTP.Request(me['thumb']).content, sort_order=idx+1)
                                else:
                                    field[1][me['url']] = Proxy.Preview(HTTP.Request(me['url']).content, sort_order=idx+1)
                            field[1].validate_keys(valid_names)

                    value = self.get(data_episode, 'extras', [])
                    if len(value) > 0:
                        for extra in value:
                            mode = self.get(extra, 'mode', None)
                            extra_type = self.get(extra, 'type', 'trailer')
                            extra_class = self.extra_map[extra_type.lower()]
                            url = 'sjva://sjva.me/playvideo/%s|%s' % (mode, extra.get('param'))
                            metadata_episode.extras.add(
                                extra_class(
                                    url=url, 
                                    title=self.change_html(extra.get('title', '')),
                                    originally_available_at = Datetime.ParseDate(self.get(extra, 'originally_available_at', '1900-12-31')).date(),
                                    thumb=self.get(extra, 'thumb', '')
                                )
                            )








        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())


    def set_season_info_by_web(self, media, media_season_index, title=None, summary=None):
        if title and summary:
            return
        url = 'http://127.0.0.1:32400/library/metadata/%s' % media.id
        data = JSON.ObjectFromURL(url)
        section_id = data['MediaContainer']['librarySectionID']
        token = Request.Headers['X-Plex-Token']
        media_season_id = media.seasons[media_season_index].id

        url = 'http://127.0.0.1:32400/library/sections/%s/all?type=3&id=%s&X-Plex-Token=%s' % (section_id, media_season_id, token)
        if title is not None:
            url = '%s&title.value=%s' % (url, urllib.quote(title.encode('utf8')))
        if summary is not None:
            url = '%s&summary.value=%s' % (url, urllib.quote(summary.encode('utf8')))

        request = PutRequest(url)
        response = urllib2.urlopen(request)

