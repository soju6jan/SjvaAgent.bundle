# -*- coding: utf-8 -*-
import os, urllib, re, traceback

class SjvaMusicFolderArtist(Agent.Artist):
    name = 'SJVA Music Folder'
    
    languages = [Locale.Language.Korean]
    primary_provider = True

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
        Log("SjvaMusicFolderArtist update!!")
        VARIOUS_ARTISTS_POSTER = 'https://music.plex.tv/pixogs/various_artists_poster.jpg'
        metadata.posters[VARIOUS_ARTISTS_POSTER] = Proxy.Media(HTTP.Request(VARIOUS_ARTISTS_POSTER))



class SjvaMusicFolderAlbum(Agent.Album):
    name = 'SJVA Music Folder'
    
    languages = [Locale.Language.Korean]
    primary_provider = True

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
            import audiohelpers
            match_poster = False
            code = metadata.id
            data = None
            metadata.title = urllib.unquote(code.replace('TB', ''))
            valid_track_keys = []
            
            regexes = [
                "(?P<title>.*?)-(?P<album_artist>[^-]+)-(?P<album>[^-]+)$",
                #"(?P<album_artist>.*?)\s?-\s?(?P<title>.*?)$",
                "(?P<title>.*?)$",
            ]
            not_match_count = 0
            for index, track in enumerate(media.children):
                track_key = track.id or index
                valid_track_keys.append(track_key)

                for item in track.items:
                    for part in item.parts:
                        #filename = os.path.splitext(os.path.basename(media.tracks[index].items[0].parts[0].file))[0]

                        if match_poster == False:
                            audio_helper = audiohelpers.AudioHelpers(part.file)
                            ret = audio_helper.process_metadata_only_poster(metadata)
                            if len(ret) > 0:
                                match_poster = True
                            else:
                                not_match_count = not_match_count + 1
                        if not_match_count > 5:
                            match_poster = True
                      
                        filename = os.path.splitext(os.path.basename(part.file))[0]
                        Log('filename: %s', filename)
                        flag = False    
                        for regex in regexes:
                            filename = re.sub('^(?P<track>\d+)[\s\.\-\_]+', '', filename).strip(' -._')
                            match = re.match(regex, filename)
                            track_meta = metadata.tracks[track_key]
                            if match:
                                track_meta.title = match.group('title')
                                if 'album_artist' in match.groupdict():
                                    track_meta.original_title = match.group('album_artist')
                                flag = True
                                break
                
            metadata.tracks.validate_keys(valid_track_keys)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc()) 


        