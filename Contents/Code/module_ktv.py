# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, urllib2
from .agent_base import AgentBase, PutRequest


class ModuleKtv(AgentBase):
    module_name = 'ktv'
    
    def get_year(self, media):
        try:
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s/children' % media.id)
            # 시즌.
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
            # 2021-12-13 닥터 슬럼프 리메이크 FT105262
            if manual and media.show is not None and media.show.startswith('FT'):
                code = media.show
                meta = MetadataSearchResult(id=code, name=code, year='', score=100, thumb="", lang=lang)
                results.Append(meta)
                return

            if manual and media.show is not None and media.show.startswith('K'):
                code, title = media.show.split('|')
                if code != 'KTV':
                    meta = MetadataSearchResult(id=code, name=title, year='', score=100, thumb="", lang=lang)
                    results.Append(meta)
                    return
            
            # KTV|수당영웅
            Log('SEARCH 0: %s' % media.show)
            if manual and media.show is not None and media.show.startswith('KTV'):
                keyword = media.show.replace('KTV|', '')

            else:
                Log('SEARCH : %s' % media.show)
                keyword = media.show
                Log('>> %s : %s %s' % (self.module_name, keyword, manual))
            Log('KEYWORD : %s', keyword)
            use_json = False
            search_data = None
            search_key = u'search|%s' % keyword
            if self.is_read_json(media) and manual == False:
                info_json = self.get_info_json(media)
                if info_json is not None and search_key in info_json:
                    search_data = info_json[search_key]
                    use_json = True
            if search_data is None:
                search_data = self.send_search(self.module_name, keyword, manual)
                if search_data is not None and self.is_write_json(media):
                    self.save_info(media, {search_key:search_data})
                    #self.append_info(media, search_key, search_data)

            if search_data is None:
                return
            #Log(json.dumps(search_data, indent=4))
            # 2021-07-07
            # 다음 차단-> 차단상태에서 ott search data 저장 -> 점수 미달 -> 새로고침 안됨
            max_score = 0
            daum_max_score = 100
            equal_max_score = 100
            if 'daum' in search_data:
                data = search_data['daum']
                flag_media_season = False
                if len(media.seasons) > 1:
                    for media_season_index in media.seasons:
                        if int(media_season_index) > 1 and int(media_season_index) < 1900:
                            flag_media_season = True
                            break

                # 미디어도 시즌, 메타도 시즌 
                if flag_media_season and len(data['series']) > 1:
                    # 마지막 시즌 ID
                    results.Append(MetadataSearchResult(
                        id=data['series'][-1]['code'], 
                        name=u'%s | 시리즈' % keyword, 
                        year=data['series'][-1]['year'], 
                        score=100, lang=lang)
                    )

                # 미디어 단일, 메타 시즌
                elif len(data['series']) > 1:
                    #reversed
                    for index, series in enumerate(reversed(data['series'])):
                        Log(index)
                        Log(series)
                        if series['year'] is not None:
                            score = 95-(index*5)
                            if media.year == series['year']:
                                score = 100
                            if score < 20:
                                score = 20
                            if 'status' in series and series['status'] == 0:
                                score = score -40
                            max_score = max(max_score, score)
                            results.Append(MetadataSearchResult(id=series['code'], name=series['title'], year=series['year'], score=score, lang=lang))
                # 미디어 단일, 메타 단일 or 미디어 시즌, 메타 단일
                else:
                    # 2019-05-23 미리보기 에피들이 많아져서 그냥 방송예정도 선택되게.
                    #if data['status'] != 0:
                    # 2021-06-27 동명 컨텐츠중 년도 매칭되는것을 100으로 주기위해 99로 변경
                    if 'equal_name' in data and len(data['equal_name']) > 0:
                        score = daum_max_score = 99
                        #나의 아저씨 동명 같은 년도
                        if data['year'] == media.year:
                            score = daum_max_score = 100
                            equal_max_score = 99
                    else:
                        score = 100
                    meta = MetadataSearchResult(id=data['code'], name=data['title'], year=data['year'], thumb=data['image_url'], score=score, lang=lang)
                    tmp = data['extra_info'] + ' '
                    if data['status'] == 0:
                        tmp = tmp + u'방송예정'
                    elif data['status'] == 1:
                        tmp = tmp + u'방송중'
                    elif data['status'] == 2:
                        tmp = tmp + u'방송종료'
                    tmp = tmp + self.search_result_line() + data['desc']
                    meta.summary = tmp
                    meta.type = 'movie'
                    max_score = max(max_score, score)
                    results.Append(meta)

                if 'equal_name' in data:
                    for index, program in enumerate(data['equal_name']):
                        if program['year'] == media.year:
                            score = min(equal_max_score, 100 - (index))
                            max_score = max(max_score, score)
                            results.Append(MetadataSearchResult(id=program['code'], name='%s | %s' % (program['title'], program['studio']), year=program['year'], score=score, lang=lang))
                        else:
                            score = min(equal_max_score, 80 - (index*5))
                            max_score = max(max_score, score)
                            results.Append(MetadataSearchResult(id=program['code'], name='%s | %s' % (program['title'], program['studio']), year=program['year'], score=score, lang=lang))
            def func(show_list):
                for idx, item in enumerate(show_list):
                    score = min(daum_max_score, item['score'])
                    meta = MetadataSearchResult(id=item['code'], name=item['title'], score=score, thumb=item['image_url'], lang=lang)
                    meta.summary = item['site'] + ' ' + item['studio']
                    meta.type = "movie"
                    results.Append(meta)
                    return score
            if 'tving' in search_data:
                score = func(search_data['tving'])
                max_score = max(max_score, score)
            if 'wavve' in search_data:
                score = func(search_data['wavve'])
                max_score = max(max_score, score)
            if use_json and max_score < 85:
                self.remove_info(media)
                self.search(results, media, lang, manual)

        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())


    def update_info(self, metadata, metadata_season,  meta_info):
        #metadata.original_title = metadata.title
        #metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
        metadata.studio = meta_info['studio']
        try: metadata.originally_available_at = Datetime.ParseDate(meta_info['premiered']).date()
        except: pass
        metadata.content_rating = meta_info['mpaa']
        metadata.summary = meta_info['plot']
        metadata_season.summary = metadata.summary
        metadata.genres.clear()
        for tmp in meta_info['genre']:
            metadata.genres.add(tmp) 
        
        module_prefs = self.get_module_prefs(self.module_name)
        # 부가영상
        for item in meta_info['extras']:
            url = 'sjva://sjva.me/playvideo/%s|%s' % (item['mode'], item['content_url'])
            metadata.extras.add(self.extra_map[item['content_type'].lower()](url=url, title=self.change_html(item['title']), originally_available_at=Datetime.ParseDate(item['premiered']).date(), thumb=item['thumb']))

        # rating
        for item in meta_info['ratings']:
            if item['name'] == 'tmdb':
                metadata.rating = item['value']
                metadata.audience_rating = 0.0

        # role
        #metadata.roles.clear()
        for item in ['actor', 'director', 'credits']:
            for item in meta_info[item]:
                actor = metadata.roles.new()
                actor.role = item['role']
                actor.name = item['name']
                actor.photo = item['thumb']
                Log('%s - %s'% (actor.name, actor.photo))

        # poster
        ProxyClass = Proxy.Preview
        valid_names = []
        season_valid_names = []
        poster_index = art_index = banner_index = 0
        for item in sorted(meta_info['thumb'], key=lambda k: k['score'], reverse=True):
            valid_names.append(item['value'])
            try:
                if item['aspect'] == 'poster':
                    if item['thumb'] == '':
                        metadata.posters[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=poster_index+1)
                        metadata_season.posters[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=poster_index+1)
                    else:
                        metadata.posters[item['value']] = ProxyClass(HTTP.Request(item['thumb']).content, sort_order=poster_index+1)
                        metadata_season.posters[item['value']] = ProxyClass(HTTP.Request(item['thumb']).content, sort_order=poster_index+1)
                    season_valid_names.append(item['value'])
                    poster_index = poster_index + 1
                elif item['aspect'] == 'landscape':
                    if item['thumb'] == '':
                        metadata.art[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=art_index+1)
                        metadata_season.art[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=art_index+1)
                    else:
                        metadata.art[item['value']] = ProxyClass(HTTP.Request(item['thumb']).content, sort_order=art_index+1)
                        metadata_season.art[item['value']] = ProxyClass(HTTP.Request(item['thumb']).content, sort_order=art_index+1)
                    season_valid_names.append(item['value'])
                    art_index = art_index + 1
                elif item['aspect'] == 'banner':
                    if item['thumb'] == '': 
                        metadata.banners[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=banner_index+1)
                    else:
                        metadata.banners[item['value']] = ProxyClass(HTTP.Request(item['thumb']).content, sort_order=banner_index+1) 
                    banner_index = banner_index + 1
            except Exception as e: 
                Log('Exception:%s', e)
                #Log(traceback.format_exc())
                
        # 이거 확인필요. 번들제거 영향. 시즌을 주석처리안하면 쇼에 최후것만 입력됨.
        #metadata.posters.validate_keys(valid_names)
        #metadata.art.validate_keys(valid_names)
        #metadata.banners.validate_keys(valid_names)
        #metadata_season.posters.validate_keys(season_valid_names)
        #metadata_season.art.validate_keys(season_valid_names)

        # 테마
        valid_names = []
        if 'themes' in meta_info['extra_info']:
            for tmp in meta_info['extra_info']['themes']:
                if tmp not in metadata.themes:
                    valid_names.append(tmp)
                    metadata.themes[tmp] = Proxy.Media(HTTP.Request(tmp).content)
           
        # 테마2
        
        # Get the TVDB id from the Movie Database Agent
        tvdb_id = None
        if 'tmdb_id' in meta_info['extra_info']:
            tvdb_id = Core.messaging.call_external_function(
                'com.plexapp.agents.themoviedb',
                'MessageKit:GetTvdbId',
                kwargs = dict(
                    tmdb_id = meta_info['extra_info']['tmdb_id']
                )
            )
        Log('TVDB_ID : %s', tvdb_id)
        THEME_URL = 'https://tvthemes.plexapp.com/%s.mp3'
        if tvdb_id and THEME_URL % tvdb_id not in metadata.themes:
            tmp = THEME_URL % tvdb_id
            try: 
                metadata.themes[tmp] = Proxy.Media(HTTP.Request(THEME_URL % tvdb_id))
                valid_names.append(tmp)
            except: pass
        metadata.themes.validate_keys(valid_names)    


    def update_episode(self, show_epi_info, episode, media, info_json, is_write_json, frequency=None):
        try:
            valid_names = []

            if 'daum' in show_epi_info:
                #if 'tving_id' in meta_info['extra_info']:
                #    param += ('|' + 'V' + meta_info['extra_info']['tving_id'])
                episode_info = None
                
                if info_json is not None and show_epi_info['daum']['code'] in info_json:
                    episode_info = info_json[show_epi_info['daum']['code']]
                if episode_info is None:
                    episode_info = self.send_episode_info(self.module_name, show_epi_info['daum']['code'])
                    if episode_info is not None and is_write_json:
                        info_json[show_epi_info['daum']['code']] = episode_info

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
                module_prefs = self.get_module_prefs(self.module_name)
                for item in episode_info['extras']:
                    url = 'sjva://sjva.me/playvideo/%s|%s' % (item['mode'], item['content_url'])
                    episode.extras.add(self.extra_map[item['content_type'].lower()](url=url, title=self.change_html(item['title']), originally_available_at=Datetime.ParseDate(item['premiered']).date(), thumb=item['thumb']))
            else:
                ott_mode = 'full'

            if ott_mode != 'stop':
                for site in ['tving', 'wavve']:
                    if site in show_epi_info:
                        if ott_mode == 'full':
                            episode.originally_available_at = Datetime.ParseDate(show_epi_info[site]['premiered']).date()
                            #episode.title = show_epi_info[site]['premiered']
                            episode.title = show_epi_info[site]['title'] if show_epi_info[site]['title'] != '' else show_epi_info[site]['premiered']
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



    def update(self, metadata, media, lang):
        #self.base_update(metadata, media, lang)
        try:
            is_write_json = self.is_write_json(media)
            module_prefs = self.get_module_prefs(self.module_name)
            flag_ending = False
            flag_media_season = False
            if len(media.seasons) > 1:
                for media_season_index in media.seasons:
                    if int(media_season_index) > 1 and int(media_season_index) < 1900:
                        flag_media_season = True
                        break

            search_data = None
            search_key = u'search|%s' % media.title
            info_json = {}
            if self.is_read_json(media):
                tmp = self.get_info_json(media)
                #Log(tmp)
                if tmp is not None and search_key in tmp:
                    search_data = tmp[search_key]
                    info_json = tmp
            
            if search_data is None:
                search_data = self.send_search(self.module_name, media.title, False)
                if search_data is not None and is_write_json:
                    #self.append_info(media, search_key, search_data)
                    info_json[search_key] = search_data

            index_list = [index for index in media.seasons]
            index_list = sorted(index_list)
            #for media_season_index in media.seasons:
            
            # 2021-11-05
            metadata.roles.clear()
            for media_season_index in index_list:
                Log('media_season_index is %s', media_season_index)
                # 2022-04-05
                search_media_season_index = media_season_index
                if len(str(media_season_index)) == 3:
                    search_media_season_index = str(media_season_index)[1:]

                if search_media_season_index in ['0', '00']:
                    continue
                search_title = media.title.replace(u'[종영]', '')
                search_title = search_title.split('|')[0].strip()
                search_code = metadata.id            
                if flag_media_season and 'daum' in search_data and len(search_data['daum']['series']) > 1:
                    try: #사당보다 먼 의정부보다 가까운 3
                        search_title = search_data['daum']['series'][int(search_media_season_index)-1]['title']
                        search_code = search_data['daum']['series'][int(search_media_season_index)-1]['code']
                    except:
                        pass

                Log('flag_media_season : %s', flag_media_season)
                Log('search_title : %s', search_title)
                Log('search_code : %s', search_code)
                #self.get_json_filepath(media) 
                #self.get_json_filepath(media.seasons[media_season_index])

                meta_info = None
                if info_json is not None and search_code in info_json:
                    # 방송중이라면 저장된 정보를 무시해야 새로운 에피를 갱신
                    if info_json[search_code]['status'] == 2:
                        meta_info = info_json[search_code]
                if meta_info is None:
                    meta_info = self.send_info(self.module_name, search_code, title=search_title)
                    if meta_info is not None and is_write_json:
                        #self.append_info(media, search_code, meta_info)
                        info_json[search_code] = meta_info
  
                #Log(json.dumps(meta_info, indent=4))

                if flag_media_season:
                    metadata.title = media.title.split('|')[0].strip()
                else:
                    metadata.title = meta_info['title']
                    

                metadata.original_title = metadata.title                  
                metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
                
                if flag_media_season == False and meta_info['status'] == 2 and  module_prefs['end_noti_filepath'] != '':
                    parts = media.seasons[media_season_index].all_parts()
                    end_noti_filepath = module_prefs['end_noti_filepath'].split('|')
                    for tmp in end_noti_filepath:
                        if parts[0].file.find(tmp) != -1:
                            metadata.title = u'[종영]%s' % metadata.title
                            break

                metadata_season = metadata.seasons[media_season_index]
                self.update_info(metadata, metadata_season, meta_info)
                
                
                # 포스터
                # Get episode data.
                @parallelize
                def UpdateEpisodes():
                    for media_episode_index in media.seasons[media_season_index].episodes:
                        episode = metadata.seasons[media_season_index].episodes[media_episode_index]

                        @task
                        def UpdateEpisode(episode=episode, media_season_index=media_season_index, media_episode_index=media_episode_index, media=media):
                            frequency = False
                            show_epi_info = None
                            if media_episode_index in meta_info['extra_info']['episodes']:
                                show_epi_info = meta_info['extra_info']['episodes'][media_episode_index]
                                self.update_episode(show_epi_info, episode, media, info_json, is_write_json)
                            else:
                                #에피정보가 없다면 
                                match = Regex(r'\d{4}-\d{2}-\d{2}').search(media_episode_index)
                                if match:
                                    for key, value in meta_info['extra_info']['episodes'].items():
                                        if ('daum' in value and value['daum']['premiered'] == media_episode_index) or ('tving' in value and value['tving']['premiered'] == media_episode_index) or ('wavve' in value and value['wavve']['premiered'] == media_episode_index):
                                            show_epi_info = value
                                            self.update_episode(show_epi_info, episode, media, info_json, is_write_json, frequency=key)
                                            break
                            if show_epi_info is None:
                                return

                            episode.directors.clear()
                            episode.producers.clear()
                            episode.writers.clear()
                            for item in meta_info['credits']:
                                meta = episode.writers.new()
                                meta.role = item['role']
                                meta.name = item['name']
                                meta.photo = item['thumb']
                            for item in meta_info['director']:
                                meta = episode.directors.new()
                                meta.role = item['role']
                                meta.name = item['name']
                                meta.photo = item['thumb']
    
            # 시즌 title, summary
            if is_write_json:
                self.save_info(media, info_json)
            
            # 2021-09-15 주석처리함. 임의의 시즌으로 분할하는 경우를 고려
            #if not flag_media_season:
            #    return
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
                    match = Regex(r'(?P<season_num>\d{1,8})\s*(?P<season_title>.*?)$').search(tmp)
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
        

