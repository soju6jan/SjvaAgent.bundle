# -*- coding: utf-8 -*-
import os, unicodedata, io, time
from .agent_base import AgentBase

class ModuleAudiobookJsonArtist(AgentBase):
    module_name = 'book_json'
    
    def search(self, results, media, lang, manual, **kwargs):
        tmp = self.get_json_filepath(media)
        filepath = tmp.replace('info.json', 'album.json')
        Log(filepath)
        if os.path.exists(filepath) == False:
            return False
        data = self.read_json(filepath)
        meta = MetadataSearchResult(id='JM%sA' % int(time.time()), name=data['artist']['title'], year='', score=100, thumb="", lang=lang)
        results.Append(meta)
        return True

    def update(self, metadata, media, lang):
        tmp = self.get_json_filepath(media)
        filepath = tmp.replace('info.json', 'album.json')
        if os.path.exists(filepath) == False:
            return False
        data = self.read_json(filepath)
        metadata.summary = data['artist']['desc']
        metadata.posters[data['artist']['img']] = Proxy.Preview(HTTP.Request(data['artist']['img']))



class ModuleAudiobookJsonAlbum(AgentBase):
    module_name = 'book_json'
    
    def search(self, results, media, lang, manual, **kwargs):
        tmp = self.get_json_filepath(media)
        filepath = tmp.replace('info.json', 'album.json')
        if os.path.exists(filepath) == False:
            return False
        data = self.read_json(filepath)
        meta = MetadataSearchResult(id='JM%s' % int(time.time()), name=data['album']['title'], year='', score=100, thumb="", lang=lang)
        results.Append(meta)
        return True


    def update(self, metadata, media, lang):
        tmp = self.get_json_filepath(media)
        filepath = tmp.replace('info.json', 'album.json')
        if os.path.exists(filepath) == False:
            return False
        data = self.read_json(filepath)
        
        metadata.title = data['album']['title']
        metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
        metadata.summary = data['album']['desc']
        metadata.posters[data['album']['img']] = Proxy.Preview(HTTP.Request(data['album']['img']))
        if 'ratings' in data['album']:
            metadata.rating = data['album']['ratings']
        if 'studio' in data['album']:
            metadata.studio = data['album']['studio']
        if 'premiered' in data['album']:
            metadata.originally_available_at = Datetime.ParseDate(data['album']['premiered']).date()
        
        valid_track_keys = []
        for index in media.tracks:
            filename = os.path.splitext(os.path.basename(media.tracks[index].items[0].parts[0].file))[0]
            track_key = media.tracks[index].id or int(index)
            valid_track_keys.append(track_key)
            Log(media.tracks[index].index)
            t = metadata.tracks[track_key]
            track = str(media.tracks[index].index)
            if track in data['album']['tracks']:
                t.title = data['album']['tracks'][track]['title']
                #if 'artist' in data['album']['tracks'][track]:
                #    t.original_title = ' '.join(data['album']['tracks'][track]['artist'])
                #else:
            else:
                t.title = filename.strip(' -._')
            if 'artist' in data:
                t.original_title = data['artist']['title']

        metadata.tracks.validate_keys(valid_track_keys)
