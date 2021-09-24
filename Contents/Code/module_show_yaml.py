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
            if type(data['seasons']) == type([]):
                to_dict = {}
                for season in data['seasons']:
                    try:
                        if str(season['index']) not in to_dict:
                            to_dict[str(season['index'])] = season
                    except:
                        pass
                data['seasons'] = to_dict

            
            for season_yamlpath in filepath_list['seasons']:
                try:
                    tmp = yaml.load(io.open(season_yamlpath), Loader=yaml.BaseLoader)
                    #data['seasons'].append(tmp)
                    if 'index' in tmp:
                        data['seasons'][str(tmp['index'])] = tmp
                except Exception as exception: 
                    Log('Exception:%s', exception)
                    Log(traceback.format_exc())  

            # episodes to dict
            for season_index, season in data['seasons'].items():
                if 'episodes' in season and type(season['episodes']) == type([]):
                    to_dict = {}
                    for episode in season['episodes']:
                        try:
                            if str(episode['index']) not in to_dict:
                                to_dict[str(episode['index'])] = episode
                        except:
                            pass
                    season['episodes'] = to_dict

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
                self.set_data(metadata, data, 'title', is_primary)
                self.set_data(metadata, data, 'original_title', is_primary)
                self.set_data(metadata, data, 'title_sort', is_primary)
                self.set_data(metadata, data, 'originally_available_at', is_primary)
                            

            self.set_data(metadata, data, 'studio', is_primary)
            self.set_data(metadata, data, 'content_rating', is_primary)
            self.set_data(metadata, data, 'summary', is_primary)
            self.set_data(metadata, data, 'rating', is_primary)
            
            self.set_data_list(metadata, data, 'genres', is_primary)
            self.set_data_list(metadata, data, 'collections', is_primary)

            self.set_data_person(metadata, data, 'roles', is_primary)

            self.set_data_media(metadata, data, 'posters', is_primary)
            self.set_data_media(metadata, data, 'art', is_primary)
            self.set_data_media(metadata, data, 'themes', is_primary)
            self.set_data_extras(metadata, data, 'extras', is_primary)
                
            index_list = [index for index in media.seasons]
            index_list = sorted(index_list)

            for media_season_index in index_list:
                Log('media_season_index is %s', media_season_index)
                Log('media_season_index is %s', type(media_season_index))
                if media_season_index == '0':
                    continue
                metadata_season = metadata.seasons[media_season_index]
                if str(media_season_index) not in data['seasons']:
                    continue
                data_season = data['seasons'][str(media_season_index)]
                value = self.get(data_season, 'title', None)
                if value is not None:
                    #metadata_season.title = value
                    self.set_season_info_by_web(media, media_season_index,  title=value)
                
                value = self.get(data_season, 'summary', None)
                if value is not None:
                    #metadata_season.summary = value
                    self.set_season_info_by_web(media, media_season_index, summary=value)

                self.set_data_media(metadata_season, data_season, 'posters', is_primary)
                self.set_data_media(metadata_season, data_season, 'art', is_primary)
                self.set_data_extras(metadata_season, data_season, 'extras', is_primary)


                for media_episode_index in media.seasons[media_season_index].episodes:
                    metadata_episode = metadata.seasons[media_season_index].episodes[media_episode_index]
                                        
                    if 'episodes' not in data_season or str(media_episode_index) not in data_season['episodes']:
                        continue

                    data_episode = data_season['episodes'][str(media_episode_index)]
                    Log(self.d(data_episode))

                    self.set_data(metadata_episode, data_episode, 'title', is_primary)
                    self.set_data(metadata_episode, data_episode, 'summary', is_primary)
                    self.set_data(metadata_episode, data_episode, 'originally_available_at', is_primary)

                    self.set_data_person(metadata_episode, data, 'writers', is_primary)
                    self.set_data_person(metadata_episode, data, 'directors', is_primary)

                    self.set_data_media(metadata_episode, data_episode, 'thumbs', is_primary)
                    self.set_data_extras(metadata_episode, data_episode, 'extras', is_primary)
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

