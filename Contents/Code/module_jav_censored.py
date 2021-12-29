# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, urllib2
from .agent_base import AgentBase

class ModuleJavCensoredBase(AgentBase):
    def get_search_keyword(self, media, manual, from_file=False):
        try:
            if manual:
                ret = unicodedata.normalize('NFKC', unicode(media.name)).strip()
            else:
                if from_file:
                    data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s' % media.id)
                    filename = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']
                    ret = os.path.splitext(os.path.basename(filename))[0]
                    ret = re.sub('\s*\[.*?\]', '', ret).strip()
                    match = Regex(r'(?P<cd>cd\d{1,2})$').search(ret) 
                    if match:
                        ret = ret.replace(match.group('cd'), '')
                else:
                    # from_scanner
                    ret = media.name
            return ret
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())


    def base_search(self, results, media, lang, manual, keyword):
        if manual and media.name is not None and (media.name.startswith('CD') or media.name.startswith('CB') or media.name.startswith('DT')):
            code = media.name
            meta = MetadataSearchResult(id=code, name=code, year=1900, score=100, thumb="", lang=lang)
            results.Append(meta)
            return True


        if self.is_read_json(media):
            if manual:
                self.remove_info(media)
            else:
                info_json = self.get_info_json(media)
                if info_json is not None:
                    meta = MetadataSearchResult(id=info_json['code'], name=info_json['title'], year=info_json['year'], score=100, thumb="", lang=lang)
                    results.Append(meta)
                    return True

        data = self.send_search(self.module_name, keyword, manual)
        for item in data:
            #title = '[%s]%s' % (item['ui_code'], String.DecodeHTMLEntities(String.StripTags(item['title_ko'])).strip())
            if item['year'] != '' and item['year'] is not None:
                title = '{} / {} / {}'.format(item['ui_code'], item['year'], item['site'])
                year = item['year']
            else:
                title = '{} / {}'.format(item['ui_code'], item['site'])
                year = ''
            meta = MetadataSearchResult(id=item['code'], name=title, year=year, score=item['score'], thumb=item['image_url'], lang=lang)
            meta.summary = self.change_html(item['title_ko'])
            meta.type = "movie"
            results.Append(meta) 
        if len(data) > 0 and data[0]['score'] >= 80:
            return True
        return False



    def base_update(self, metadata, media, lang):
        Log("UPDATE : %s" % metadata.id)
        data = None
        if self.is_read_json(media):
            info_json = self.get_info_json(media)
            if info_json is not None and info_json['code'] == metadata.id:
                data = info_json
        if data is None:
            data = self.send_info(self.module_name, metadata.id)
            if data is not None and self.is_write_json(media):
                self.save_info(media, data)
  
        #Log(json.dumps(data, indent=4))
        if 'title' in data and data['title'] is not None:
            metadata.title = self.change_html(data['title'])
        if 'originaltitle' in data and data['originaltitle'] is not None:
            metadata.original_title = metadata.title_sort = data['originaltitle']
        try: metadata.year = data['year']
        except: pass
        try: metadata.duration = data['runtime']*60
        except: pass
        if 'studio' in data and data['studio'] is not None:
            metadata.studio = data['studio']
        if 'plot' in data and data['plot'] is not None:
            metadata.summary = self.change_html(data['plot'])
        if 'premiered' in data and data['premiered'] is not None and len(data['premiered']) == 10 and data['premiered'] != '0000-00-00':
            metadata.originally_available_at = Datetime.ParseDate(data['premiered']).date()
        if 'country' in data and data['country'] is not None:
            metadata.countries = data['country']
        if 'tagline' in data and data['tagline'] is not None:
            metadata.tagline = self.change_html(data['tagline'])
        if 'mpaa' in data and data['mpaa'] is not None:
            metadata.content_rating = data['mpaa']
        try:
            if data['ratings'] is not None and len(data['ratings']) > 0:
                if data['ratings'][0]['max'] == 5:
                    metadata.rating = float(data['ratings'][0]['value']) * 2
                    #metadata.rating_image= data['ratings'][0]['image_url']
                    #metadata.rating_image = 'imdb://image.rating'
                    #metadata.audience_rating = float(data['ratings'][0]['value']) * 2
                    #metadata.audience_rating_image = 'rottentomatoes://image.rating.upright'

        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())

        ProxyClass = Proxy.Preview 
        landscape = None
        if 'thumb' in data and data['thumb'] is not None:
            for item in data['thumb']:
                if item['aspect'] == 'poster':
                    try: metadata.posters[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=10)
                    except: pass
                if item['aspect'] == 'landscape':
                    landscape = item['value']
                    try: metadata.art[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=10)
                    except: pass

        if 'fanart' in data and data['fanart'] is not None:
            for item in data['fanart']:
                try: metadata.art[item] = ProxyClass(HTTP.Request(item).content)
                except: pass

        if 'genre' in data and data['genre'] is not None:
            metadata.genres.clear()
            for item in data['genre']:
                metadata.genres.add(item)

        if 'tag' in data and data['tag'] is not None:
            metadata.collections.clear()
            for item in data['tag']:
                metadata.collections.add(self.change_html(item))

        if 'director' in data and data['director'] is not None:
            metadata.directors.clear()
            meta_director = metadata.directors.new()
            meta_director.name = data['director']

        if 'actor' in data and data['actor'] is not None:
            metadata.roles.clear()
            for item in data['actor']:
                actor = metadata.roles.new()
                actor.role = item['originalname']
                actor.name = item['name']
                actor.photo = item['thumb']

        if 'extras' in data and data['extras'] is not None:
            for item in data['extras']:
                if item['mode'] == 'mp4':
                    url = 'sjva://sjva.me/video.mp4/%s' % item['content_url']
                metadata.extras.add(TrailerObject(url=url, title=self.change_html(data['extras'][0]['title']), originally_available_at=metadata.originally_available_at, thumb=landscape))
        return


    



class ModuleJavCensoredDvd(ModuleJavCensoredBase):
    module_name = 'jav_censored'
    
    def search(self, results, media, lang, manual):
        keyword = self.get_search_keyword(media, manual, from_file=True)
        keyword = keyword.replace(' ', '-')
        return self.base_search(results, media, lang, manual, keyword)
 

    def update(self, metadata, media, lang):
        self.base_update(metadata, media, lang)


class ModuleJavCensoredAma(ModuleJavCensoredBase):
    module_name = 'jav_censored_ama'
    
    def search(self, results, media, lang, manual):
        keyword = self.get_search_keyword(media, manual, from_file=True)
        keyword = keyword.replace(' ', '-')
        return self.base_search(results, media, lang, manual, keyword)

    def update(self, metadata, media, lang):
        self.base_update(metadata, media, lang)


class ModuleJavFc2(ModuleJavCensoredBase):
    module_name = 'jav_fc2'
    
    def search(self, results, media, lang, manual):
        keyword = self.get_search_keyword(media, manual, from_file=True)
        keyword = keyword.replace(' ', '-')
        return self.base_search(results, media, lang, manual, keyword)

    def update(self, metadata, media, lang):
        self.base_update(metadata, media, lang)


class ModuleJavUnCensored(ModuleJavCensoredBase):
    module_name = 'jav_uncensored'
    
    def search(self, results, media, lang, manual):
        keyword = self.get_search_keyword(media, manual, from_file=True)
        keyword = keyword.replace(' ', '-')
        return self.base_search(results, media, lang, manual, keyword)

    def update(self, metadata, media, lang):
        self.base_update(metadata, media, lang)
