# -*- coding: utf-8 -*-
import os, re, unicodedata
from .agent_base import AgentBase

Log = Log # type: Framework.api.logkit.LogKit
Regex = Regex # type: Framework.api.utilkit.RegexKit
Datetime = Datetime # Framework.api.utilkit.DatetimeKit
HTTP = HTTP # type: Framework.api.networkkit.HTTPKit
Proxy = Proxy # type: Framework.api.modelkit.ProxyKit
Prefs = Prefs # type: Framework.api.preferencekit.PreferenceKit
MetadataSearchResult = MetadataSearchResult # type: Framework.objects.MetadataSearchResult
TrailerObject = TrailerObject # type: Framework.modelling.objects.ModelInterfaceObjectMetaclass


class ModuleJavCensoredBase(AgentBase):
    def get_search_keyword(self, media, manual, from_file=False):
        try:
            file_path = None
            try:
                data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s' % media.id)
                if data and 'MediaContainer' in data and 'Metadata' in data['MediaContainer']:
                    file_path = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']
            except Exception:
                pass

            if manual:
                ret = unicodedata.normalize('NFKC', unicode(media.name)).strip()
            else:
                if from_file and file_path:
                    ret = os.path.splitext(os.path.basename(file_path))[0]
                    ret = re.sub(r'\s*\[.*?\]', '', ret).strip()
                    match = Regex(r'(?P<cd>cd\d{1,2})$').search(ret)
                    if match:
                        ret = ret.replace(match.group('cd'), '').strip()
                else:
                    ret = media.name

            ret = ret.replace('JAVALL|', '').strip()
            if getattr(self, 'module_name', '') != 'western':
                ret = ret.replace(' ', '-')

            return ret, file_path
        except Exception as e:
            Log.Exception(str(e))
            return media.name, None


    def base_search(self, results, media, lang, manual, keyword, media_path=None):
        try:
            if manual and media.name is not None and media.name.startswith(('CD', 'CB', 'CT', 'CJ', 'WP', 'WS', 'W')):
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

            data = self.send_search(self.module_name, keyword, manual, media_path=media_path)
            if not isinstance(data, list):
                data = []

            use_fallback = True
            try:
                use_fallback = bool(Prefs['jav_search_all'])
            except Exception:
                try:
                    use_fallback = bool(Prefs['jav_dvd_search_all'])
                except Exception:
                    use_fallback = True

            if (not data or (len(data) > 0 and int(data[0].get('score', 0)) < 80)) and self.module_name != 'western' and use_fallback:
                Log("JAV search failed/low score for '%s'. Falling back to Western module..." % keyword)
                fallback_data = self.send_search('western', keyword, manual, media_path=media_path)
                if fallback_data and isinstance(fallback_data, list):
                    data = fallback_data

            for item in data:
                if not isinstance(item, dict):
                    continue

                is_western_item = str(item.get('code', '')).startswith('W') or getattr(self, 'module_name', '') == 'western'
                raw_display = item.get('title') if is_western_item else item.get('ui_code')
                display_name = unicode(raw_display if raw_display is not None else '')

                raw_site = item.get('site') or ('stashdb' if str(item.get('code', '')).startswith('WS') else 'tpdb')
                site_name = unicode(raw_site)

                year_val = item.get('year')
                if year_val not in ['', None, 0, 1900]:
                    year_str = unicode(year_val)
                    title = u"%s / %s / %s" % (display_name, year_str, site_name)
                    item_year = int(year_val)
                else:
                    title = u"%s / %s" % (display_name, site_name)
                    item_year = None

                item_score = int(round(float(item.get('score', 0))))
                item_thumb = str(item.get('image_url') or '')

                meta = MetadataSearchResult(id=str(item['code']), name=title, year=item_year, score=item_score, thumb=item_thumb, lang=lang)
                if item.get('title_ko'):
                    meta.summary = unicode(item['title_ko'])
                meta.type = "movie"
                results.Append(meta)

            if len(data) > 0 and int(data[0].get('score', 0)) >= 80:
                return True
            return False

        except Exception as e:
            Log.Exception("base_search 예외 발생: %s" % str(e))
            return False



    def base_update(self, metadata, media, lang):
        Log("UPDATE : %s" % metadata.id)
        data = None
        if self.is_read_json(media):
            info_json = self.get_info_json(media)
            if info_json is not None and info_json['code'] == metadata.id:
                data = info_json
        if data is None:
            target_module = self.module_name
            if metadata.id.startswith(('WP', 'WS', 'W')):
                target_module = 'western'
            elif metadata.id.startswith(('E', 'ED', 'EM', 'EP', 'EH', 'EC', 'EF')):
                target_module = 'jav_uncensored'
            elif metadata.id.startswith(('C', 'CD', 'CB', 'CT', 'CM', 'CJ')):
                target_module = 'jav_censored'

            data = self.send_info(target_module, metadata.id)
            if data is not None and self.is_write_json(media):
                self.save_info(media, data)

        #Log(json.dumps(data, indent=4))
        if 'title' in data and data['title'] is not None:
            metadata.title = self.change_html(data['title'])
        if 'originaltitle' in data and data['originaltitle'] is not None:
            metadata.original_title = data['originaltitle']

        if 'sorttitle' in data and data['sorttitle'] is not None:
            metadata.title_sort = data['sorttitle']
        elif 'originaltitle' in data and data['originaltitle'] is not None:
            metadata.title_sort = data['originaltitle']

        try: metadata.year = data['year']
        except Exception: pass
        try: metadata.duration = data['runtime']*60
        except Exception: pass
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

        except Exception as e:
            Log.Exception(str(e))

        ProxyClass = Proxy.Preview
        landscape = None
        if 'thumb' in data and data['thumb'] is not None:
            for item in data['thumb']:
                if item['aspect'] == 'poster':
                    try: metadata.posters[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=10)
                    except Exception: pass
                if item['aspect'] == 'landscape':
                    landscape = item['value']
                    try: metadata.art[item['value']] = ProxyClass(HTTP.Request(item['value']).content, sort_order=10)
                    except Exception: pass

        if 'fanart' in data and data['fanart'] is not None:
            for item in data['fanart']:
                try: metadata.art[item] = ProxyClass(HTTP.Request(item).content)
                except Exception: pass

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
                if not isinstance(item, dict):
                    continue

                display_name = item.get('name_ko') or item.get('name_org') or item.get('name') or item.get('name_en')
                if display_name:
                    actor = metadata.roles.new()
                    actor.name = display_name
                    actor.role = item.get('name_org') or item.get('originalname') or item.get('role')
                    actor.photo = item.get('thumb') or item.get('photo') or item.get('image')

        if 'extras' in data and data['extras'] is not None:
            for item in data['extras']:
                url = 'sjva://sjva.me/playvideo/%s|%s' % (item['mode'], item['content_url'])
                metadata.extras.add(TrailerObject(url=url, title=self.change_html(data['extras'][0]['title']), originally_available_at=metadata.originally_available_at, thumb=landscape))
        return


    def search(self, results, media, lang, manual):
        keyword, media_path = self.get_search_keyword(media, manual, from_file=True)
        return self.base_search(results, media, lang, manual, keyword, media_path=media_path)

    def update(self, metadata, media, lang):
        self.base_update(metadata, media, lang)



class ModuleJavCensored(ModuleJavCensoredBase):
    module_name = 'jav_censored'


class ModuleJavUnCensored(ModuleJavCensoredBase):
    module_name = 'jav_uncensored'


class ModuleWestern(ModuleJavCensoredBase):
    module_name = 'western'
