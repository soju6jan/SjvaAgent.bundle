# -*- coding: utf-8 -*-
import json
from .agent_base import AgentBase

Log = Log # type: Framework.api.logkit.LogKit
Datetime = Datetime # Framework.api.utilkit.DatetimeKit
FeaturetteObject = FeaturetteObject # type: Framework.modelling.objects.ModelInterfaceObjectMetaclass
MetadataSearchResult = MetadataSearchResult # type: Framework.objects.MetadataSearchResult


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
            Log.Exception(str(e))





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
            templates = {'poster': [metadata.posters, set()], 'landscape' : [metadata.art, set()], 'banner':[metadata.banners, set()]}
            for item in sorted(meta_info['thumb'], key=lambda k: k['score'], reverse=True):
                image_url = item.get('value') or item.get('thumb')
                aspect = item.get('aspect') or 'poster'
                target = templates.get(aspect)
                if not target or not image_url or image_url in target[1]:
                    continue
                if aspect == 'poster':
                    self.set_http_data(image_url, metadata.posters, target[1], preview=item.get('thumb'))
                elif aspect == 'landscape':
                    self.set_http_data(image_url, metadata.art, target[1], preview=item.get('thumb'))
                elif aspect == 'banner':
                    self.set_http_data(image_url, metadata.banners, target[1], preview=item.get('thumb'))

            metadata.posters.validate_keys(templates['poster'][1])
            metadata.art.validate_keys(templates['landscape'][1])
            metadata.banners.validate_keys(templates['banner'][1])

            tmp = [int(x) for x in meta_info['extra_info']['episodes'].keys()]
            no_list = sorted(tmp, reverse=True)
            module_prefs = self.get_module_prefs(self.module_name)
            for no in no_list:
                info = meta_info['extra_info']['episodes'][str(no)]
                Log(no)
                Log(info)

                for site in ['tving', 'wavve']:
                    if site in info:
                        url = 'sjva://sjva.me/playvideo/%s|%s' % (site, info[site]['code'])
                        title = info[site]['title'] if info[site]['title'] != '' else info[site]['plot']
                        extra_media = FeaturetteObject(
                            url=url,
                            title='%s회. %s' % (no, title),
                            thumb=info[site]['thumb'],
                        )
                        metadata.extras.add(extra_media)
        except Exception as e:
            Log.Exception(str(e))


