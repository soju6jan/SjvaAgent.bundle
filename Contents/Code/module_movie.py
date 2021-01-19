# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, random
from .agent_base import AgentBase

class ModuleMovie(AgentBase):
    module_name = 'movie'
    
    def search(self, results, media, lang, manual, **kwargs):
        try:
            #if media.primary_metadata is not None and RE_IMDB_ID.search(media.primary_metadata.id):
            #    #pendSearchResult(results=results, id=media.primary_metadata.id, score=100)
            Log('vbvvvvvvvvvvvvvvv') 
            Log(media.primary_metadata)


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
                meta = MetadataSearchResult(id=item['code'], name=item['title'], year=item['year'], score=item['score'], thumb=item['image_url'], lang=lang)
                meta.summary = self.change_html(item['desc']) + self.search_result_line() + item['site']
                meta.type = "movie"
                results.Append(meta)

            Log(json.dumps(search_data, indent=4))


            

        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())    


    #rating_image_identifiers = {'Certified Fresh' : 'rottentomatoes://image.rating.certified', 'Fresh' : 'rottentomatoes://image.rating.ripe', 'Ripe' : 'rottentomatoes://image.rating.ripe', 'Rotten' : 'rottentomatoes://image.rating.rotten', None : ''}
    #audience_rating_image_identifiers = {'Upright' : 'rottentomatoes://image.rating.upright', 'Spilled' : 'rottentomatoes://image.rating.spilled', None : ''}
    #'imdb://image.rating'


    def update(self, metadata, media, lang):
        try:
            meta_info = self.send_info(self.module_name, metadata.id)

            Log(json.dumps(meta_info, indent=4))

            metadata.title = meta_info['title']
            metadata.original_title = meta_info['originaltitle']
            metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)

            try: 
                metadata.originally_available_at = Datetime.ParseDate(meta_info['premiered']).date()
                metadata.year = meta_info['year']
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
                if item['name'] == 'naver':
                    metadata.rating = item['value']
                    metadata.audience_rating = 0.0
                    metadata.rating_image = 'rottentomatoes://image.rating.spilled' if item['value'] < 7 else 'rottentomatoes://image.rating.upright'
                elif item['name'] == 'tmdb':
                    metadata.rating = item['value']
                    metadata.audience_rating = 0.0
                    metadata.rating_image = 'imdb://image.rating'

            
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
            
            # art
            #metadata.posters.clear()
            Log(metadata.posters)
            """
            for item in metadata.posters:
                try:
                    Log(item)
                    del metadata.posters[item]
                except Exception as e: 
                    Log('Exception:%s', e)
                    Log(traceback.format_exc())
            """

            ProxyClass = Proxy.Preview 
            valid_names = []
            poster_index = art_index = 0
            art_list = []
            for item in sorted(meta_info['art'], key=lambda k: k['score'], reverse=True):
                valid_names.append(item['value'])
                if item['aspect'] == 'poster':
                    if item['thumb'] == '':
                        metadata.posters[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=poster_index+1)
                    else:
                        metadata.posters[item['value']] = ProxyClass(HTTP.Request(item['thumb']).content, sort_order=poster_index+1)
                    poster_index += 1
                elif item['aspect'] == 'landscape':
                    art_list.append(item['value'])
                    if item['thumb'] == '':
                        metadata.art[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=art_index+1)
                    else:
                        metadata.art[item['value']] = ProxyClass(HTTP.Request(item['thumb']).content, sort_order=art_index+1)
                    art_index += 1
               

            metadata.posters.validate_keys(valid_names)
            metadata.art.validate_keys(valid_names) 
            #metadata.banners.validate_keys(valid_names)

                

            metadata.reviews.clear()
            if 'making_note' in meta_info['extra_info']:
                r = metadata.reviews.new()
                r.author = '네이버'
                r.source = '제작노트'
                r.image = 'rottentomatoes://image.review.fresh' if 'fresh' == 'fresh' else 'rottentomatoes://image.review.rotten'
                r.link = 'https://sjva.me'
                r.text = meta_info['extra_info']['making_note']
             
            """
            youtube_id = '7tXniRliqNE'
            url = '{ddns}/metadata/api/youtube?youtube_id={youtube_id}&apikey={apikey}'.format(
                ddns=Prefs['server'],
                youtube_id=youtube_id,
                apikey=Prefs['apikey']
            ) 
            """
            

            for extra in meta_info['extras']:
                if True:# and extra['thumb'] is None or extra['thumb'] == '':
                    thumb = art_list[random.randint(0, len(art_list)-1)]
                else:
                    thumb = extra['thumb']
                if extra['mode'] in ['naver', 'youtube']:
                    url = '{ddns}/metadata/api/video?site={site}&param={param}&apikey={apikey}'.format(
                        ddns=Prefs['server'],
                        site=extra['mode'],
                        param=extra['content_url'],
                        apikey=Prefs['apikey']
                    )
                    metadata.extras.add(
                        self.extra_map[extra['content_type']](
                            url='sjva://sjva.me/redirect.mp4/%s|%s' % (extra['mode'], url), 
                            title=extra['title'],
                            thumb=thumb,
                        )
                    )

            
            return

            
            """
            # poster
            ProxyClass = Proxy.Preview 
            valid_names = []
            poster_index = art_index = banner_index = 0
            for item in sorted(meta_info['thumb'], key=lambda k: k['score'], reverse=True):
                valid_names.append(item['value'])
                if item['aspect'] == 'poster':
                    if item['thumb'] == '':
                        metadata.posters[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=poster_index+1)
                    else:
                        metadata.posters[item['value']] = ProxyClass(HTTP.Request(item['thumb']).content, sort_order=poster_index+1)
                    poster_index += 1
                elif item['aspect'] == 'landscape':
                    if item['thumb'] == '':
                        metadata.art[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=art_index+1)
                    else:
                        metadata.art[item['value']] = ProxyClass(HTTP.Request(item['thumb']).content, sort_order=art_index+1)
                    art_index += 1
                elif item['aspect'] == 'banner':
                    if item['thumb'] == '':
                        metadata.banners[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=banner_index+1)
                    else:
                        metadata.banners[item['value']] = ProxyClass(HTTP.Request(item['thumb']).content, sort_order=banner_index+1)
                    banner_index += 1  

            metadata.posters.validate_keys(valid_names)
            metadata.art.validate_keys(valid_names)
            metadata.banners.validate_keys(valid_names)

            tmp = [int(x) for x in meta_info['extra_info']['episodes'].keys()]
            no_list = sorted(tmp, reverse=True)

            for no in no_list:
                info = meta_info['extra_info']['episodes'][str(no)]
                Log(no)      
                Log(info) 

                for site in ['tving', 'wavve']:
                    if site in info:
                        url = '{ddns}/metadata/api/{module_name}/stream?code={code}&call=plex&apikey={apikey}'.format(
                            ddns=Prefs['server'],
                            module_name=self.module_name,
                            code=info[site]['code'],
                            apikey=Prefs['apikey']
                        )
                        url = 'sjva://sjva.me/ott/%s' % (url)
                        title = info[site]['title'] if info[site]['title'] != '' else info[site]['plot']
                        metadata.extras.add(
                            FeaturetteObject(
                                url=url, 
                                title='%s회. %s' % (no, title),
                                thumb=info[site]['thumb'],
                            )
                        )
            """
 

        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())




"""
<Media id="69652" audioCodec="aac" videoCodec="h264" container="mp4">
<Part accessible="1" exists="1" id="75147" container="mp4" key="https://cc3001.dmm.co.jp/litevideo/freepv/1/118/118abw00043/118abw00043_mhb_w.mp4" optimizedForStreaming="1">
<Stream id="151818" streamType="1" codec="h264" index="0" displayTitle="알 수 없음 (H.264)" extendedDisplayTitle="알 수 없음 (H.264)"> </Stream>
<Stream id="151819" streamType="2" selected="1" codec="aac" index="1" channels="2" displayTitle="알 수 없음 (AAC Stereo)" extendedDisplayTitle="알 수 없음 (AAC Stereo)"> </Stream>
</Part>
</Media>
"""

