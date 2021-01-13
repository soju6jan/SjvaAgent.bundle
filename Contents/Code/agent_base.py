# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, time
from functools import wraps


"""
class MetadataSearchResult(XMLObject):
  def __init__(self, core, id, name=None, year=None, score=0, lang=None, thumb=None):
    XMLObject.__init__(self, core, id=id, thumb=thumb, name=name, year=year, score=score, lang=lang)
    self.tagName = "SearchResult"
"""


class AgentBase(object):
    key_map = {
        'com.plexapp.agents.sjva_agent_jav_censored' : 'C',
        'com.plexapp.agents.sjva_agent_jav_censored_ama' : 'D',
        'com.plexapp.agents.sjva_agent_ott_movie' : 'O',
        'com.plexapp.agents.sjva_agent_ktv' : 'K',
    }


    extra_map = {
        'Trailer' : TrailerObject,
        'DeletedScene' : DeletedSceneObject,
        'BehindTheScenes' : BehindTheScenesObject, 
        'Interview' : InterviewObject, 
        'SceneOrSample' : SceneOrSampleObject,
        'Featurette' : FeaturetteObject,
        'Short' : ShortObject,
        'Other' : OtherObject
    }
    
    def search_result_line(self):
        text = ' ' + ' '.ljust(80, "=") + ' '
        return text


    def try_except(original_function):
        @wraps(original_function)
        def wrapper_function(*args, **kwargs):  #1
            try:
                return original_function(*args, **kwargs)
            except Exception as exception: 
                Log('Exception:%s', exception)
                Log(traceback.format_exc())
        return wrapper_function

    def get_search_keyword(self, media, manual, from_file=False):
        try:
            Log('## AgentBase ## get_search_keyword ## media.name:%s, manual:%s, from_file:%s' % (media.name, manual, from_file))
           
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


    def send_search(self, module_name, keyword, manual):
        try:
            url = '{ddns}/metadata/api/{module_name}/search?keyword={keyword}&manual={manual}&call=plex&apikey={apikey}'.format(
              ddns=Prefs['server'],
              module_name=module_name,
              keyword=urllib.quote(keyword.encode('utf8')),
              manual=manual,
              apikey=Prefs['apikey']
            )
            Log(url)
            return AgentBase.my_JSON_ObjectFromURL(url)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
    

    def send_info(self, module_name, code, title=None):
        try:
            url = '{ddns}/metadata/api/{module_name}/info?code={code}&call=plex&apikey={apikey}'.format(
              ddns=Prefs['server'],
              module_name=module_name,
              code=urllib.quote(code.encode('utf8')),
              apikey=Prefs['apikey']
            )
            if title is not None:
                url += '&title=' + urllib.quote(title.encode('utf8'))
            Log(url)
            return AgentBase.my_JSON_ObjectFromURL(url)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())


    def send_episode_info(self, module_name, code):
        try:
            url = '{ddns}/metadata/api/{module_name}/episode_info?code={code}&call=plex&apikey={apikey}'.format(
              ddns=Prefs['server'],
              module_name=module_name,
              code=urllib.quote(code.encode('utf8')),
              apikey=Prefs['apikey']
            )
            Log(url)
            return AgentBase.my_JSON_ObjectFromURL(url)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())

    
    def change_html(self, text):
        if text is not None:
            return text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#35;', '#').replace('&#39;', "‘")



    def base_search(self, results, media, lang, manual, keyword):
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
            meta.summary = self.change_html(item['title_ko'])
            meta.type = "movie"
            results.Append(meta)



    def base_update(self, metadata, media, lang):
        Log("UPDATE : %s" % metadata.id)
        data = self.send_info(self.module_name, metadata.id)
        #Log(json.dumps(data, indent=4))
        metadata.title = self.change_html(data['title'])
        metadata.original_title = metadata.title_sort = data['originaltitle']
        try: metadata.year = data['year']
        except: pass
        try: metadata.duration = data['runtime']*60
        except: pass
        metadata.studio = data['studio']
        metadata.summary = self.change_html(data['plot'])
        Log(data['premiered'])
        if 'premiered' in data and data['premiered'] is not None and len(data['premiered']) == 10 and data['premiered'] != '0000-00-00':
            metadata.originally_available_at = Datetime.ParseDate(data['premiered']).date()
        metadata.countries = data['country']
        metadata.tagline = self.change_html(data['tagline'])
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
                metadata.collections.add(self.change_html(item))

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
                metadata.extras.add(TrailerObject(url=url, title=self.change_html(data['extras'][0]['title']), originally_available_at=metadata.originally_available_at, thumb=landscape))
        return


    




    @staticmethod
    def get_key(media):
        try:
            Log('...............................')
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s' % media.id)
            section_id = str(data['MediaContainer']['librarySectionID'])
            data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/sections')
            
            for item in data['MediaContainer']['Directory']:
                if item['key'] == section_id:
                    return AgentBase.key_map[item['agent']]
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())


    @staticmethod
    def my_JSON_ObjectFromURL(url, timeout=None, retry=3):
        try:
            if timeout is None:
                timeout = int(Prefs['timeout'])
            Log('my_JSON_ObjectFromURL retry : %s, url : %s', retry, url)
            return JSON.ObjectFromURL(url, timeout=timeout)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
            if retry > 0:
                time.sleep(1)
                Log('RETRY : %s', retry)
                return AgentBase.my_JSON_ObjectFromURL(url, timeout, retry=(retry-1))
            else:
                Log('CRITICAL my_JSON_ObjectFromURL error') 
    

    
    
    """
    LyricFind.bundle/Contents/Code/__init__.py:      metadata.tracks[track_key].lyrics[url] = Proxy.Remote(url, format = 'lrc', sort_order=sort_order)
./LyricFind.bundle/Contents/Code/__init__.py:    metadata.tracks[track_key].lyrics[url] = Proxy.Remote(url, format = 'txt', sort_order=sort_order)
./LyricFind.bundle/Contents/Code/__init__.py:  # We need to recreate the Proxy objects to effectively pass them through since the Framework doesn't
./LyricFind.bundle/Contents/Code/__init__.py:      metadata.tracks[track_key].lyrics[key] = Proxy.Remote(key, format='lrc' if '&lrc=1' in key else 'txt', sort_order=sort_order)
^C
    """
