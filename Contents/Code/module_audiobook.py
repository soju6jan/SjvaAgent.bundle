# -*- coding: utf-8 -*-
import os, unicodedata
from .agent_base import AgentBase

class ModuleAudiobookArtist(AgentBase):
    module_name = 'book'
    
    def search(self, results, media, lang, manual, **kwargs):
        if manual:
            keyword = media.artist
            if keyword.find('|') == -1:
                keyword = '|' + keyword
        else:
            keyword = '%s|%s' % (media.album, media.title)
        Log('검색어 : %s', keyword)
        data = self.send_search(self.module_name, keyword, manual)
        for item in data:
            meta = MetadataSearchResult(id=item['code'] + 'A', name=item['author'], year='', score=item['score'], thumb=item['image'], lang=lang)
            meta.summary = self.change_html('작품 : {}\n'.format(item['title']) + self.search_result_line() + item['description'])
            meta.type = "movie"
            results.Append(meta) 


    def update(self, metadata, media, lang):
        data = self.send_info(self.module_name, metadata.id)
        metadata.summary = data['author_intro']
        metadata.posters[data['poster']] = Proxy.Preview(HTTP.Request(data['poster']))



class ModuleAudiobookAlbum(AgentBase):
    module_name = 'book'
    
    def search(self, results, media, lang, manual, **kwargs):
        if manual and media.name is not None and media.name.startswith('BN'):
            meta = MetadataSearchResult(id=media.name, name=media.name, year='', score=100, thumb="", lang=lang)
            results.Append(meta)
            return

        if self.is_read_json(media):
            if manual:
                self.remove_info(media)
            else:
                info_json = self.get_info_json(media)
                if info_json is not None:
                    code = info_json['code']
                    meta = MetadataSearchResult(id=code, name=info_json['title'], year='', score=100, thumb="", lang=lang)
                    results.Append(meta)
                    return

        keyword = None
        if manual:
            keyword = media.name
        if keyword is None:
            keyword = '%s|%s' % (media.album, media.artist)

        data = self.send_search(self.module_name, keyword, manual)
        for item in data:
            meta = MetadataSearchResult(id=item['code'], name=item['title'], year='', score=item['score'], thumb=item['image'], lang=lang)
            meta.summary = self.change_html('작가 : {}\n'.format(item['author']) + self.search_result_line() + item['description'])
            meta.type = "movie"
            results.Append(meta) 


    def update(self, metadata, media, lang):
        data = None
        code = metadata.id
        if self.is_read_json(media):
            info_json = self.get_info_json(media)
            if info_json is not None:
                data = info_json
        if data is None:
            data = self.send_info(self.module_name, code)
            if data is not None and self.is_write_json(media):
                self.save_info(media, data)

        #data = self.send_info(self.module_name, code)
        metadata.title = data['title']
        metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
        metadata.summary = data['desc']
        metadata.posters[data['poster']] = Proxy.Preview(HTTP.Request(data['poster']))
        metadata.rating = float(data['ratings'])
        metadata.studio = data['publisher']
        metadata.originally_available_at = Datetime.ParseDate(data['premiered']).date()
        
        valid_track_keys = []
        for index in media.tracks:
            filename = os.path.splitext(os.path.basename(media.tracks[index].items[0].parts[0].file))[0]
            track_key = media.tracks[index].id or int(index)
            valid_track_keys.append(track_key)
            t = metadata.tracks[track_key]
            t.title = filename.strip(' -._')
            t.original_title = data['author']
        metadata.tracks.validate_keys(valid_track_keys)
