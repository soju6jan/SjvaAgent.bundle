# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, random, time
from .agent_base import AgentBase

class ModuleMovie(AgentBase):
    module_name = 'movie'
    
    def search(self, results, media, lang, manual, **kwargs):
        try:
            if manual and media.name is not None and (media.name.startswith('MD') or media.name.startswith('MT') or media.name.startswith('MN')):
                code = media.name
                if self.is_include_time_info(media):
                    code = code + '|%s' % int(time.time())
                meta = MetadataSearchResult(id=code, name=code, year=1900, score=100, thumb="", lang=lang)
                results.Append(meta)
                return


            if self.is_read_json(media):
                if manual:
                    self.remove_info(media)
                else:
                    info_json = self.get_info_json(media)
                    if info_json is not None:
                        code = info_json['code']
                        if self.is_include_time_info(media):
                            code = code + '|%s' % int(time.time())
                        #code = code + ('^1' if manual else '^0')
                        meta = MetadataSearchResult(id=code, name=info_json['title'], year=info_json['year'], score=100, thumb="", lang=lang)
                        results.Append(meta)
                        return

            movie_year = media.year
            movie_name = unicodedata.normalize('NFKC', unicode(media.name)).strip()            
            Log('name:[%s], year:[%s]', movie_name, movie_year)
            match = Regex(r'^(?P<name>.*?)[\s\.\[\_\(](?P<year>\d{4})').match(movie_name)
            if match:
                movie_name = match.group('name').replace('.', ' ').strip()
                movie_name = re.sub(r'\[(.*?)\]', '', movie_name )
                movie_year = match.group('year')
            Log('SEARCH : [%s] [%s]' % (movie_name, movie_year))
            search_data = self.send_search(self.module_name, movie_name, manual, year=movie_year)

            if search_data is None:
                return 

            for item in search_data:
                meta_id = item['code']
                if self.is_include_time_info(media):
                    meta_id = meta_id + '|%s' % int(time.time())
                #meta_id = meta_id + ('^1' if manual else '^0')
                meta = MetadataSearchResult(id=meta_id, name=item['title'], year=item['year'], score=item['score'], thumb=item['image_url'], lang=lang)
                meta.summary = self.change_html(item['desc']) + self.search_result_line() + item['site']
                meta.type = "movie"
                results.Append(meta) 

            # info_json에 다른 코드가 있으면 삭제
            #Log(json.dumps(search_data, indent=4))
        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())    

    #rating_image_identifiers = {'Certified Fresh' : 'rottentomatoes://image.rating.certified', 'Fresh' : 'rottentomatoes://image.rating.ripe', 'Ripe' : 'rottentomatoes://image.rating.ripe', 'Rotten' : 'rottentomatoes://image.rating.rotten', None : ''}
    #audience_rating_image_identifiers = {'Upright' : 'rottentomatoes://image.rating.upright', 'Spilled' : 'rottentomatoes://image.rating.spilled', None : ''}
    #'imdb://image.rating'

    # 스캔 : manual = False, 일치항목찾기, 메타새로고침
    # 3가지 경우 진입
    # 스캔, 메타새로고침 : info가 있으면 무조건 강제로 사용
    # 일치항목찾기 : code가 같을 경우에만 사용.
    # 이를 구분하는 방법 : search manual 값을 여기로 전달해야함. 
    # 구분자 ^ 
    # ^ 값이 없으면 메타새로고침
    # ^0 : 스캔 (manual = false)
    # ^1 : 일치항목찾기 (manual = true)
    # metadata id set은 search만 가능
    # 어떤 방식으로 서치했는지 update단에는 아는 방법을 찾지 못함
    # 일치항목찾기인 경우 info.json 삭제
    # 구드공의 경우 삭제 불가능하기때문에 변경방법 없음. read_json을 끄고 입힌 후 다시 on

    # 2021-07-29
    # MN으로 저장되어 있고, info.json을 MD로 수정했다하더라도 MD로 내용은 바뀌지만,
    # GUID를 MD로 변경할 수는 없다. 일반적으로는 문제되지 않겠지만.......
    def update(self, metadata, media, lang):
        try:
            code = metadata.id.split('|')[0]
            meta_info = None

            if self.is_read_json(media):
                info_json = self.get_info_json(media)
                if info_json is not None:
                    meta_info = info_json
            if meta_info is None:
                meta_info = self.send_info(self.module_name, code)
                if meta_info is not None and self.is_write_json(media):
                    self.save_info(media, meta_info)

            metadata.title = meta_info['title']
            metadata.original_title = meta_info['originaltitle']
            metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)

            try: 
                metadata.originally_available_at = Datetime.ParseDate(meta_info['premiered']).date()
                metadata.year = meta_info['year']
            except: 
                try: metadata.year = meta_info['year']
                except: pass

            
            metadata.content_rating = meta_info['mpaa']
            metadata.summary = meta_info['plot']
            metadata.studio = meta_info['studio']
            metadata.tagline = meta_info['tagline']
           
            metadata.countries.clear()
            for tmp in meta_info['country']:
                metadata.countries.add(tmp)

            metadata.genres.clear()
            for tmp in meta_info['genre']:
                metadata.genres.add(tmp)
 
            
            # rating
            for item in meta_info['ratings']:
                if item['name'] == 'tmdb':
                    metadata.rating = item['value']
                    metadata.audience_rating = 0.0
                    metadata.rating_image = 'imdb://image.rating'
                else:
                    score = 70
                    if 'movie_rating_score' in meta_info:
                       score = meta_info['movie_rating_score']
                    metadata.rating = item['value']
                    metadata.audience_rating = 0.0
                    metadata.rating_image = 'rottentomatoes://image.rating.spilled' if item['value']*10 < score else 'rottentomatoes://image.rating.upright'
                break
     
            # role
            metadata.roles.clear()
            for item in meta_info['actor']:
                actor = metadata.roles.new()
                actor.role = item['role']
                actor.name = item['name']
                actor.photo = item['thumb']

            metadata.directors.clear()
            for item in meta_info['director']:
                actor = metadata.directors.new()
                actor.name = item

            metadata.writers.clear()
            for item in meta_info['credits']:
                actor = metadata.writers.new()
                actor.name = item
            
            metadata.producers.clear()
            for item in meta_info['producers']:
                actor = metadata.producers.new()
                actor.name = item
            
            # art
            ProxyClass = Proxy.Preview 
            valid_names = []
            poster_index = art_index = banner_index = 0
            art_list = []
            for item in sorted(meta_info['art'], key=lambda k: k['score'], reverse=True):
                valid_names.append(item['value'])
                if item['aspect'] == 'poster' and poster_index < 3:
                    if item['thumb'] == '':
                        metadata.posters[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=poster_index+1)
                    else:
                        metadata.posters[item['value']] = ProxyClass(HTTP.Request(item['thumb']).content, sort_order=poster_index+1)
                    poster_index = poster_index + 1
                elif item['aspect'] == 'landscape' and art_index < 3:
                    art_list.append(item['value'])
                    if item['thumb'] == '':
                        metadata.art[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=art_index+1)
                    else:
                        metadata.art[item['value']] = ProxyClass(HTTP.Request(item['thumb']).content, sort_order=art_index+1)
                    art_index = art_index + 1
                #elif item['aspect'] == 'banner' and banner_index < 0:
                #    if item['thumb'] == '':
                #        metadata.banners[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=banner_index+1)
                #    else:
                #        metadata.banners[item['value']] = ProxyClass(HTTP.Request(item['thumb']).content, sort_order=banner_index+1)
                #    banner_index = banner_index + 1
            
            #metadata.posters.validate_keys(valid_names)
            #metadata.art.validate_keys(valid_names) 
            #metadata.banners.validate_keys(valid_names)

            metadata.reviews.clear()
            for item in meta_info['review']:
                r = metadata.reviews.new()
                r.author = item['author']
                r.source = item['source']
                r.image = 'rottentomatoes://image.review.fresh' if item['rating'] >= 6 else 'rottentomatoes://image.review.rotten'
                r.link = item['link'] 
                r.text = item['text']

            if 'wavve_stream' in meta_info['extra_info'] and meta_info['extra_info']['wavve_stream']['drm'] == False:
                #if meta_info['extra_info']['wavve_stream']['mode'] == '0':
                url = 'sjva://sjva.me/wavve_movie/%s' % (meta_info['extra_info']['wavve_stream']['plex'])
                #else:
                #    url = 'sjva://sjva.me/redirect.m3u8/wavve|%s' % (meta_info['extra_info']['wavve_stream']['plex2'])
                extra_media = FeaturetteObject(
                    url=url, 
                    title=u'웨이브 재생',
                    thumb='' if len(art_list) == 0 else art_list[random.randint(0, len(art_list)-1)],
                )
                metadata.extras.add(extra_media)
            
            if 'tving_stream' in meta_info['extra_info'] and meta_info['extra_info']['tving_stream']['drm'] == False:
                url = 'sjva://sjva.me/redirect.m3u8/tving|%s' % (meta_info['extra_info']['tving_stream']['plex'])
                extra_media = FeaturetteObject(
                    url=url, 
                    title=u'티빙 재생',
                    thumb='' if len(art_list) == 0 else art_list[random.randint(0, len(art_list)-1)],
                )
                metadata.extras.add(extra_media)

            module_prefs = self.get_module_prefs(self.module_name)
            for extra in meta_info['extras']:
                if extra['thumb'] is None or extra['thumb'] == '':
                    thumb = art_list[random.randint(0, len(art_list)-1)]
                else:
                    thumb = extra['thumb']
                extra_url = None
                if extra['mode'] in ['naver', 'youtube', 'kakao']:
                    url = '{ddns}/metadata/api/video?site={site}&param={param}&apikey={apikey}'.format(
                        ddns=Prefs['server'] if module_prefs['server'] == '' else module_prefs['server'],
                        site=extra['mode'],
                        param=extra['content_url'],
                        apikey=Prefs['apikey'] if module_prefs['apikey'] == '' else module_prefs['apikey']
                    )
                    extra_url = 'sjva://sjva.me/redirect.mp4/%s|%s' % (extra['mode'], url)
                #elif extra['mode'] == 'kakao':
                #    extra_url = 'sjva://sjva.me/redirect.mp4/kakao|%s' % extra['content_url']
                if extra_url is not None:
                    metadata.extras.add(
                        self.extra_map[extra['content_type'].lower()](
                            url=extra_url, 
                            title=extra['title'],
                            thumb=thumb,
                        )
                    )

            if meta_info['tag'] is not None:
                metadata.collections.clear()
                for item in meta_info['tag']:
                    metadata.collections.add((item))
            return
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())


