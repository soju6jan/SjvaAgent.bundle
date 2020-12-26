# -*- coding: utf-8 -*-
import os, traceback, json
import urllib
import re
import unicodedata
from .agent_base import AgentBase

class AgentAVCensored(Agent.Movies, AgentBase):
    module_name = 'av_censored'
    name = "SJVA AV Censored" 
    languages = [Locale.Language.Korean]
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia', 'com.plexapp.agents.xbmcnfo']
    contributes_to = ['com.plexapp.agents.xbmcnfo']
    
    def search(self, results, media, lang, manual):
        keyword = self.get_search_keyword(media, manual, from_file=True)
        keyword = keyword.replace(' ', '-')
        data = self.send_search(self.module_name, keyword, manual)
        for item in data:
            Log(item)
            #title = '[%s]%s' % (item['ui_code'], String.DecodeHTMLEntities(String.StripTags(item['title_ko'])).strip())
            if item['year'] != '' and item['year'] is not None:
                title = '{} / {} / {}'.format(item['ui_code'], item['year'], item['site'])
                year = item['year']
            else:
                title = '{} / {}'.format(item['ui_code'], item['site'])
                year = ''
            meta = MetadataSearchResult(id=item['code'], name=title, year=year, score=item['score'], thumb=item['image_url'], lang=lang)
            meta.summary = item['title_ko']
            meta.type = "movie"
            results.Append(meta)


    
    def update(self, metadata, media, lang):
        Log("UPDATE : %s" % metadata.id)
        url = '%s/metadata/api/update?code=%s&apikey=%s' % (Prefs['server'], metadata.id, Prefs['apikey'])
        data = self.send_info(self.module_name, metadata.id)
        Log(json.dumps(data, indent=4))
        metadata.title = self.change_html(data['title'])
        metadata.original_title = metadata.title_sort = data['originaltitle']
        metadata.year = data['year']
        try: metadata.duration = data['runtime']*60
        except: pass
        metadata.studio = data['studio']

        metadata.summary = self.change_html(data['plot'])
        metadata.originally_available_at = Datetime.ParseDate(data['premiered']).date()
        metadata.countries = data['country']
        metadata.tagline = self.change_html(data['tagline'])
        metadata.content_rating = data['mpaa']
        try:
            #metadata.rating = float(data['ratings'][0]['value']) * 2
            #metadata.rating_image= data['ratings'][0]['image_url']
            #metadata.rating_image = 'imdb://image.rating'
            metadata.audience_rating = float(data['ratings'][0]['value']) * 2
            metadata.audience_rating_image = 'rottentomatoes://image.rating.upright'

        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())

        ProxyClass = Proxy.Preview if data['plex_is_proxy_preview'] else Proxy.media
        art_count = 0
        for item in data['fanart']:
            if art_count >= data['plex_art_count']:
                break
            try: metadata.art[item] = ProxyClass(HTTP.Request(item).content)
            except: pass
            art_count += 1

        landscape = None
        for item in data['thumb']:
            if item['aspect'] == 'poster':
                try: metadata.posters[item['value']] = ProxyClass(HTTP.Request(item['value']).content)
                except: pass
            if item['aspect'] == 'landscape':
                if data['plex_is_landscape_to_art']:
                    landscape = item['value']
                    try: metadata.art[item['value']] = ProxyClass(HTTP.Request(item['value']).content)
                    except: pass
        
        if data['genre'] is not None:
            metadata.genres.clear()
            for item in data['genre']:
                metadata.genres.add(item)

        if data['tag'] is not None:
            metadata.collections.clear()
            for item in data['tag']:
                metadata.collections.add(item)

        if data['director'] is not None:
            metadata.directors.clear()
            meta_director = metadata.directors.new()
            meta_director.name = data['director']

        if data['actor'] is not None:
            metadata.roles.clear()
            for item in data['actor']:
                actor = metadata.roles.new()
                actor.role = item['originalname']
                actor.name = item['name']
                actor.photo = item['thumb']

        if data['extras'] is not None:
            for item in data['extras']:
                if item['mode'] == 'mp4':
                    url = 'sjva://sjva.me/video.mp4/%s' % item['content_url']
                metadata.extras.add(TrailerObject(url=url, title=data['extras'][0]['title'],originally_available_at=metadata.originally_available_at, thumb=landscape))
        return
