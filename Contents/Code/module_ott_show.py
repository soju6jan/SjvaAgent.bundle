# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, urllib2
from .agent_base import AgentBase


class ModuleOttShow(AgentBase):
    module_name = 'ott_show'

    def search(self, results, media, lang, manual):
        try:
            keyword = self.get_keyword_from_file(media)
            Log('SEARCH : %s' % keyword)

            search_data = self.send_search(self.module_name, keyword, manual)

            if search_data is None:
                return
            Log(json.dumps(search_data, indent=4))

            
            def func(show_list):
                for idx, item in enumerate(show_list):
                    meta = MetadataSearchResult(id=item['code'], name=item['title'], score=item['score'], thumb=item['image_url'], lang=lang)
                    meta.summary = item['site'] + ' ' + item['studio']
                    meta.type = "movie"
                    results.Append(meta)
            if 'tving' in search_data:
                func(search_data['tving'])
            if 'wavve' in search_data:
                func(search_data['wavve'])

        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())





    def update(self, metadata, media, lang):
        #self.base_update(metadata, media, lang)
        try:
            meta_info = self.send_info(self.module_name, metadata.id)
            metadata.original_title = metadata.title
            metadata.title_sort = metadata.title
            metadata.studio = meta_info['studio']
            metadata.originally_available_at = Datetime.ParseDate(meta_info['premiered']).date()
            metadata.content_rating = meta_info['mpaa']
            metadata.summary = meta_info['plot']
            metadata.genres.clear()
            for tmp in meta_info['genre']:
                metadata.genres.add(tmp)
            
            

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
                        url = '{ddns}/metadata/api/{module_name}/stream.m3u8?code={code}&call=plex&apikey={apikey}'.format(
                            ddns=Prefs['server'],
                            module_name=self.module_name,
                            code=info[site]['code'],
                            apikey=Prefs['apikey'],
                        )
                        url = 'sjva://sjva.me/%s/%s|%s' % ('redirect.m3u8' if site=='tving' else 'ott', site, url)
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


