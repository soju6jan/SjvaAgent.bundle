# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, urllib2
from .agent_base import AgentBase


class ModuleFtv(AgentBase):
    module_name = 'ftv'
    

    def get_year(self, media):
        try:
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s/children' % media.id)
            # 시즌
            Log(json.dumps(data, indent=4))
            filename = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']
            ret = os.path.splitext(os.path.basename(filename))[0]
            match = Regex(r'(?P<date>\d{6})').search(ret) 
            if match:
                return match.group('date')
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())



    def search(self, results, media, lang, manual):
        try:
            media.show = unicodedata.normalize('NFC', unicode(media.show)).strip()
            Log('SEARCH : %s' % media.show)
            keyword = media.show
            Log('>> [%s] [%s] [%s]' % (self.module_name, keyword, media.year))
 
            
            search_data = self.send_search(self.module_name, keyword, manual, year=media.year)

            if search_data is None:
                return 

            for item in search_data:
                meta = MetadataSearchResult(id=item['code'], name=item['title'], year=item['year'], score=item['score'], thumb=item['image_url'], lang=lang)
                meta.summary = self.change_html(item['desc']) + self.search_result_line() + item['site']
                meta.type = "movie"
                results.Append(meta)


            return

        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())

    

    def update(self, metadata, media, lang):
        #self.base_update(metadata, media, lang)
        try: 
            meta_info = self.send_info(self.module_name, metadata.id)
            
            Log(json.dumps(meta_info, indent=4))
            self.update_info(metadata, meta_info)
            

            index_list = [index for index in media.seasons]
            index_list = sorted(index_list)
            #for media_season_index in media.seasons:
            for media_season_index in index_list:
                Log('media_season_index is %s', media_season_index)
                if media_season_index == '0':
                    continue
                
                # 포스터
                # Get episode data.
                @parallelize
                def UpdateEpisodes():
                    metadata_season = metadata.seasons[media_season_index]
                    self.update_season(media_season_index, metadata_season, meta_info)
                    
                    for media_episode_index in media.seasons[media_season_index].episodes:
                        metadata_episode = metadata.seasons[media_season_index].episodes[media_episode_index]

                        @task
                        def UpdateEpisode(metadata_episode=metadata_episode, media_season_index=media_season_index, media_episode_index=media_episode_index):

                            try:
                                episode_meta_info = meta_info['seasons'][media_season_index]['episodes'][media_episode_index]
                                metadata_episode.originally_available_at = Datetime.ParseDate(episode_meta_info['premiered']).date()
                                metadata_episode.title = episode_meta_info['title']
                                metadata_episode.summary = episode_meta_info['plot']
                                try: metadata_episode.thumbs[episode_meta_info['art'][-1]] = Proxy.Preview(HTTP.Request(episode_meta_info['art'][-1]).content, sort_order=1)
                                except: pass

                                metadata_episode.directors.clear()
                                metadata_episode.producers.clear()
                                metadata_episode.writers.clear()
                                for item in episode_meta_info['writers']:
                                    meta = metadata_episode.writers.new()
                                    meta.name = item
                                for item in episode_meta_info['directors']:
                                    meta = metadata_episode.directors.new()
                                    meta.name = item
                                for item in episode_meta_info['guests']:
                                    meta = metadata_episode.guest_stars.new()
                                    meta.name = item
                            except Exception as e: 
                                Log('Exception:%s', e)
                                Log(traceback.format_exc())


            return
            # 시즌 title, summary
            if not flag_media_season:
                return
            url = 'http://127.0.0.1:32400/library/metadata/%s' % media.id
            data = JSON.ObjectFromURL(url)
            section_id = data['MediaContainer']['librarySectionID']
            token = Request.Headers['X-Plex-Token']
            for media_season_index in media.seasons:
                Log('media_season_index is %s', media_season_index)
                if media_season_index == '0':
                    continue
                filepath = media.seasons[media_season_index].all_parts()[0].file
                tmp = os.path.basename(os.path.dirname(filepath))
                season_title = None
                if tmp != metadata.title:
                    Log(tmp)
                    match = Regex(r'(?P<season_num>\d{1,4})\s*(?P<season_title>.*?)$').search(tmp)
                    if match:
                        Log('season_num : %s', match.group('season_num'))
                        Log('season_title : %s', match.group('season_title'))
                        if match.group('season_num') == media_season_index and match.group('season_title') is not None:
                            season_title = match.group('season_title')
                metadata_season = metadata.seasons[media_season_index]
                if season_title is None:
                    url = 'http://127.0.0.1:32400/library/sections/%s/all?type=3&id=%s&summary.value=%s&X-Plex-Token=%s' % (section_id, media.seasons[media_season_index].id, urllib.quote(metadata_season.summary.encode('utf8')), token)
                else:
                    url = 'http://127.0.0.1:32400/library/sections/%s/all?type=3&id=%s&title.value=%s&summary.value=%s&X-Plex-Token=%s' % (section_id, media.seasons[media_season_index].id, urllib.quote(season_title.encode('utf8')), urllib.quote(metadata_season.summary.encode('utf8')), token)
                request = PutRequest(url)
                response = urllib2.urlopen(request)



        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())





    def update_info(self, metadata, meta_info):
        metadata.title = meta_info['title']
        metadata.original_title = meta_info['originaltitle']                 
        metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
        metadata.studio = meta_info['studio']
        try: metadata.originally_available_at = Datetime.ParseDate(meta_info['premiered']).date()
        except: pass
        metadata.content_rating = meta_info['mpaa']
        metadata.summary = meta_info['plot']
        metadata.genres.clear()
        for tmp in meta_info['genre']:
            metadata.genres.add(tmp) 

        # 부가영상
        for item in meta_info['extras']:
            if item['mode'] == 'mp4':
                url = 'sjva://sjva.me/video.mp4/%s' % item['content_url']
            elif item['mode'] == 'kakao':
                url = '{ddns}/metadata/api/video?site={site}&param={param}&apikey={apikey}'.format(ddns=Prefs['server'], site=item['mode'], param=item['content_url'], apikey=Prefs['apikey'])
                url = 'sjva://sjva.me/redirect.mp4/%s|%s' % (item['mode'], url)
            metadata.extras.add(self.extra_map[item['content_type']](url=url, title=self.change_html(item['title']), originally_available_at=Datetime.ParseDate(item['premiered']).date(), thumb=item['thumb']))

        # rating
        for item in meta_info['ratings']:
            metadata.rating = item['value']
            metadata.audience_rating = 0.0

        # role
        metadata.roles.clear()
        for item in meta_info['actor']:
            actor = metadata.roles.new()
            actor.role = item['role']
            actor.name = item['name']
            actor.photo = item['image']
            Log('%s - %s'% (actor.name, actor.photo))

        # poster
        valid_names = []
        poster_index = art_index = banner_index = 0
        art_map = {'poster': [metadata.posters, 0], 'landscape' : [metadata.art, 0], 'banner':[metadata.banners, 0]}
        for item in sorted(meta_info['art'], key=lambda k: k['score'], reverse=True):
            valid_names.append(item['value'])
            try:
                target = art_map[item['aspect']]
                target[0][item['value']] = Proxy.Preview(HTTP.Request(item['value']).content, sort_order=target[1]+1)
                target[1] = target[1] + 1
            except: pass
        # 이거 확인필요. 번들제거 영향. 시즌을 주석처리안하면 쇼에 최후것만 입력됨.
        #metadata.posters.validate_keys(valid_names)
        #metadata.art.validate_keys(valid_names)
        #metadata.banners.validate_keys(valid_names)
        #metadata_season.posters.validate_keys(season_valid_names)
        #metadata_season.art.validate_keys(season_valid_names)

        # 테마2
        # Get the TVDB id from the Movie Database Agent
        tvdb_id = meta_info['code'][2:]
        Log('TVDB_ID : %s', tvdb_id)
        THEME_URL = 'https://tvthemes.plexapp.com/%s.mp3'
        if tvdb_id and THEME_URL % tvdb_id not in metadata.themes:
            tmp = THEME_URL % tvdb_id
            try: 
                metadata.themes[tmp] = Proxy.Media(HTTP.Request(THEME_URL % tvdb_id))
                valid_names.append(tmp)
                metadata.themes.validate_keys(tmp)
            except: pass
          





    def update_season(self, season_no, metadata_season, meta_info):
        valid_names = []
        poster_index = art_index = banner_index = 0
        art_map = {'poster': [metadata_season.posters, 0], 'landscape' : [metadata_season.art, 0], 'banner':[metadata_season.banners, 0]}
        Log('Season no : %s' % season_no)
        Log(season_no in meta_info['seasons'])
        for item in sorted(meta_info['seasons'][season_no]['art'], key=lambda k: k['score'], reverse=True):
            valid_names.append(item['value'])
            try:
                target = art_map[item['aspect']]
                target[0][item['value']] = Proxy.Preview(HTTP.Request(item['value']).content, sort_order=target[1]+1)
                target[1] = target[1] + 1
            except: pass 
        









    def update_episode(self, show_epi_info, episode, frequency=None):
        try:
            valid_names = []

            if 'daum' in show_epi_info:
                #if 'tving_id' in meta_info['extra_info']:
                #    param += ('|' + 'V' + meta_info['extra_info']['tving_id'])
                episode_info = self.send_episode_info(self.module_name, show_epi_info['daum']['code'])

                episode.originally_available_at = Datetime.ParseDate(episode_info['premiered']).date()
                episode.title = episode_info['title']
                episode.summary = episode_info['plot']

                thumb_index = 30
                ott_mode = 'only_thumb'
                for item in sorted(episode_info['thumb'], key=lambda k: k['score'], reverse=True):
                    valid_names.append(item['value'])
                    if item['thumb'] == '':
                        try: episode.thumbs[item['value']] = Proxy.Preview(HTTP.Request(item['value']).content, sort_order=thumb_index+1)
                        except: pass
                    else:
                        try : episode.thumbs[item['value']] = Proxy.Preview(HTTP.Request(item['thumb']).content, sort_order=thumb_index+1)
                        except: pass
                    thumb_index = thumb_index + 1
                    ott_mode = 'stop'
                
                # 부가영상
                for item in episode_info['extras']:
                    if item['mode'] == 'mp4':
                        url = 'sjva://sjva.me/video.mp4/%s' % item['content_url']
                    elif item['mode'] == 'kakao':
                        url = '{ddns}/metadata/api/video?site={site}&param={param}&apikey={apikey}'.format(ddns=Prefs['server'], site=extra['mode'], param=extra['content_url'], apikey=Prefs['apikey'])
                        url = 'sjva://sjva.me/redirect.mp4/%s|%s' % (item['mode'], url)
                        #url = 'sjva://sjva.me/redirect.mp4/kakao|%s' % item['content_url'].split('/')[-1]
                    episode.extras.add(self.extra_map[item['content_type']](url=url, title=self.change_html(item['title']), originally_available_at=Datetime.ParseDate(item['premiered']).date(), thumb=item['thumb']))
            else:
                ott_mode = 'full'

            if ott_mode != 'stop':
                for site in ['tving', 'wavve']:
                    if site in show_epi_info:
                        if ott_mode == 'full':
                            episode.originally_available_at = Datetime.ParseDate(show_epi_info[site]['premiered']).date()
                            episode.title = show_epi_info[site]['premiered']
                            if frequency is not None:
                                episode.title = u'%s회 (%s)' % (frequency, episode.title)
                            episode.summary = show_epi_info[site]['plot']

                        if ott_mode in ['full', 'only_thumb']:
                            thumb_index = 20
                            valid_names.append(show_epi_info[site]['thumb'])
                            try: episode.thumbs[show_epi_info[site]['thumb']] = Proxy.Preview(HTTP.Request(show_epi_info[site]['thumb']).content, sort_order=thumb_index+1)
                            except: pass
                
            #episode.thumbs.validate_keys(valid_names)

        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())


class PutRequest(urllib2.Request):
    def __init__(self, *args, **kwargs):
        return urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self, *args, **kwargs):
        return 'PUT'
