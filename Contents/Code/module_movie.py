# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata
from .agent_base import AgentBase

class ModuleMovie(AgentBase):
    module_name = 'movie'
    
    def search(self, results, media, lang, manual, **kwargs):
        try:

            
            movie_year = media.year
            movie_name = unicodedata.normalize('NFKC', unicode(media.name)).strip()            

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


    def update(self, metadata, media, lang):
        try:
            meta_info = self.send_info(self.module_name, metadata.id)

            Log(json.dumps(meta_info, indent=4))

            metadata.original_title = metadata.title
            metadata.title_sort = metadata.title
            metadata.studio = meta_info['studio']
            metadata.originally_available_at = Datetime.ParseDate(meta_info['premiered']).date()
            metadata.content_rating = meta_info['mpaa']
            metadata.summary = meta_info['plot']
            metadata.genres.clear()
            for tmp in meta_info['genre']:
                metadata.genres.add(tmp)
            
            
            return

            # rating
            for item in meta_info['ratings']:
                if item['name'] == 'tmdb':
                    metadata.rating = item['value']
                    metadata.audience_rating = 0.0

            # role
            metadata.roles.clear()
            for item in ['actor', 'director', 'credits']:
                for item in meta_info[item]:
                    actor = metadata.roles.new()
                    actor.role = item['role']
                    actor.name = item['name']
                    actor.photo = item['thumb']

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

