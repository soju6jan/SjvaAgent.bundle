# -*- coding: utf-8 -*-
import os, urllib, re

class SjvaAgentMusicChartArtist(Agent.Artist):
    name = 'SJVA Music Chart'
    
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        Log(media.title)
        Log(media.artist)
        if manual:
            keyword = media.artist
        else:
            keyword = media.title
        
        code = 'TA' + urllib.quote(keyword.encode('utf8'))
        meta = MetadataSearchResult(id=code, name=keyword, year='', score=100, thumb="", lang=lang)
        results.Append(meta)
        return

    def update(self, metadata, media, lang):
        pass


class SjvaAgentMusicChartAlbum(Agent.Album):
    name = 'SJVA Music Chart'
    
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        Log(media.name)
        Log(media.title)
        if manual:
            keyword = media.name
            if keyword == None:
                keyword = media.title
        else:
            keyword = media.title
        
        code = 'TB' + urllib.quote(keyword.encode('utf8'))
        meta = MetadataSearchResult(id=code, name=keyword, year='', score=100, thumb="", lang=lang)
        results.Append(meta)
        return


    def update(self, metadata, media, lang):
        code = metadata.id
        data = None
       
        valid_track_keys = []
        
        for index in media.tracks:
            filename = os.path.splitext(os.path.basename(media.tracks[index].items[0].parts[0].file))[0]
            Log('filename: %s', filename)
            
            match = re.match("^(?P<track>\d+)-(?P<title>.*?)-(?P<album_artist>[^-]+)-(?P<album>[^-]+)$", filename)
            track_key = media.tracks[index].id or int(index)
            track_meta = metadata.tracks[track_key]
            if match:
                track_meta.title = match.group('title')
                track_meta.original_title = match.group('album_artist')
            valid_track_keys.append(track_key)
        metadata.tracks.validate_keys(valid_track_keys)


        