# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, random
from .agent_base import AgentBase
from collections import defaultdict

class ModuleMusicFolderArtist(AgentBase):
    module_name = 'music_folder_artist'
    
    def search(self, results, media, lang, manual, **kwargs):
        try:
            if manual:
                keyword = media.artist
            else:
                keyword = media.title
            
            code = 'TA' + urllib.quote(keyword.encode('utf8'))
            meta = MetadataSearchResult(id=code, name=keyword, year='', score=100, thumb="", lang=lang)
            results.Append(meta)
            return
        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())    

    def update(self, metadata, media, lang):
        Log("ModuleMusicFolderArtist update!!")


class ModuleMusicFolderAlbum(AgentBase):
    module_name = 'music_folder_album'
    
    def search(self, results, media, lang, manual, **kwargs):
        try:
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
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())    


    def update(self, metadata, media, lang):
        try:
            code = metadata.id
            data = None
            metadata.title = urllib.unquote(code.replace('TB', ''))
            valid_track_keys = []
            
            regexes = [
                "(?P<title>.*?)-(?P<album_artist>[^-]+)-(?P<album>[^-]+)$",
                "(?P<title>.*?)$",
            ]
            for index in media.tracks:
                filename = os.path.splitext(os.path.basename(media.tracks[index].items[0].parts[0].file))[0]
                Log('filename: %s', filename)

                flag = False    
                for regex in regexes:
                    filename = re.sub('^(?P<track>\d+)', '', filename).strip(' -._')

                    match = re.match(regex, filename)
                    track_key = media.tracks[index].id or int(index)
                    track_meta = metadata.tracks[track_key]
                    if match:
                        track_meta.title = match.group('title')
                        if 'album_artist' in match.groupdict():
                            track_meta.original_title = match.group('album_artist')
                        flag = True
                        break
                if flag:
                    valid_track_keys.append(track_key)
            metadata.tracks.validate_keys(valid_track_keys)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc()) 