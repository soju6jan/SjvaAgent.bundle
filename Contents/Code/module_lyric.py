# -*- coding: utf-8 -*-
import os, unicodedata, traceback, io, time, urllib
from collections import defaultdict
from .agent_base import AgentBase

class ModuleLyric(AgentBase):
    module_name = 'lyric'
    
    def search(self, results, media, lang, manual, **kwargs):
        results.Append(MetadataSearchResult(id = 'null', score = 100))


    def update(self, metadata, media, lang, is_primary=True):
        try:
            valid_keys = defaultdict(list)
            path = None
            for index in media.tracks:
                track_key = media.tracks[index].id or int(index)
                Log("트랙 메타데이터 키 : %s", track_key)
                filename = os.path.splitext(os.path.basename(media.tracks[index].items[0].parts[0].file))[0]

                try:
                    for idx, mode in enumerate(['lrc', 'txt']):
                        url = 'http://127.0.0.1:32400/:/plugins/com.plexapp.agents.sjva_agent/function/get_lyric2?mode={mode}&track_key={track_key}'.format(
                            mode = mode, 
                            track_key = track_key
                        )
                        metadata.tracks[track_key].lyrics[url] = Proxy.Remote(url, format = mode, sort_order=idx+1)
                        Log(url)
                        valid_keys[track_key].append(url)
                except Exception as e: 
                    Log('Exception:%s', e)
                    Log(traceback.format_exc())
                    #metadata.tracks[track_key].lyrics.validate_keys(valid_keys[track_key])  
            Log(valid_keys)        
            for key in metadata.tracks:
                Log(key)
                Log(valid_keys[key])
                metadata.tracks[key].lyrics.validate_keys(valid_keys[key])

        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())


    """
    def update(self, metadata, media, lang, is_primary=True):
        try:
            valid_keys = defaultdict(list)
            path = None
            url = 'http://127.0.0.1:32400/library/metadata/%s' % media.id
            data = JSON.ObjectFromURL(url, headers={'accept' : 'application/json'})
            artist = data['MediaContainer']['Metadata'][0]['parentTitle']

            for index, track in enumerate(media.children):
                #Log(track.guid)
                track_key = track.guid or index
                Log("트랙 메타데이터 키 : %s", track_key)
                track_key = track_key.split('/')[-1]
                #Log(track_key)
                for item in track.items:
                    for part in item.parts:
                        try:
                            for idx, mode in enumerate(['lrc', 'txt']):
                                url = 'http://127.0.0.1:32400/:/plugins/com.plexapp.agents.sjva_agent/function/get_lyric?mode={mode}&filename={filename}&artist={artist}&track={track}'.format(
                                    mode = mode, 
                                    filename = urllib.quote(os.path.basename(part.file).encode('utf8')), 
                                    artist = urllib.quote(artist.encode('utf8')), 
                                    track = urllib.quote(track.title.encode('utf8'))
                                )
                                metadata.tracks[track_key].lyrics[url] = Proxy.Remote(url, format = mode, sort_order=idx+1)
                                valid_keys[track_key].append(url)
                        except Exception as e: 
                            Log('Exception:%s', e)
                            Log(traceback.format_exc())
                    #metadata.tracks[track_key].lyrics.validate_keys(valid_keys[track_key])  
            Log(valid_keys)        
            for key in metadata.tracks:
                Log(key)
                Log(valid_keys[key])
                metadata.tracks[key].lyrics.validate_keys(valid_keys[key])

        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
    """

