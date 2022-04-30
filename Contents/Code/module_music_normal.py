# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, random
from .agent_base import AgentBase
from collections import defaultdict

class ModuleMusicNormalArtist(AgentBase):
    module_name = 'music_normal_artist'
    
    def search(self, results, media, lang, manual, **kwargs):
        try:
            if manual and media.artist is not None and (media.artist.startswith('SA')):
                code = media.artist
                meta = MetadataSearchResult(id=code, name=code, year=1900, score=100, thumb="", lang=lang)
                results.Append(meta)
                return

            if self.is_read_json(media):
                if manual:
                    self.remove_info(media)
                else:
                    info_json = self.get_info_json(media)
                    if info_json is not None:
                        code = info_json['code']
                        meta = MetadataSearchResult(id=code, name=info_json['title'], year=info_json['year'], score=100, thumb="", lang=lang)
                        results.Append(meta)
                        return

            if manual:
                keyword = '%s|%s' % (media.artist, media.album)
            else:
                keyword = '%s|%s' % (media.title, media.album)
            Log('media.artist : %s', media.artist)
            Log('검색어 : %s', keyword)
            data = self.send_search(self.module_name, keyword, manual)
            for item in data:
                meta = MetadataSearchResult(id=item['code'], name=item['artist'], year='', score=item['score'], thumb=item['image'], lang=lang)
                meta.summary = self.change_html('Desc : {}\n'.format(item['desc']))
                meta.type = "movie"
                results.Append(meta) 

        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())    

    def update(self, metadata, media, lang):
        code = metadata.id
        data = None
        if self.is_read_json(media):
            info_json = self.get_info_json(media)
            if info_json is not None:
                data = info_json
        if data is None:
            data = self.send_info(self.module_name, code)
            Log("JSON 쓰기 : %s", self.is_write_json(media))
            if data is not None and self.is_write_json(media):
                self.save_info(media, data)
        
        #data = self.send_info(self.module_name, code)
        #Log(self.d(data))
        
        metadata.title = data['title']
        metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
        metadata.summary = '%s\n%s' % (data['desc'], data['info_desc'])

        for poster in data['poster']:
            metadata.posters[poster] = Proxy.Media(HTTP.Request(poster))
            
        for art in data['art']:
            metadata.art[art] = Proxy.Media(HTTP.Request(art))
        metadata.genres = data['genres']
        metadata.countries = data['countries']
        self.set_data_extras(metadata, data, 'extras', True)
        return False


class ModuleMusicNormalAlbum(AgentBase):
    module_name = 'music_normal_album'
    
    def search(self, results, media, lang, manual, **kwargs):
        Log('AAAAAAAAAAAAAAAA')

        if manual and media.name is not None and (media.name.startswith('SM')):
            code = media.name
            meta = MetadataSearchResult(id=code, name=code, year=1900, score=100, thumb="", lang=lang)
            results.Append(meta)
            return

        artist_code = media.parent_metadata.id
        artist_name = media.parent_metadata.title
        Log('artist_code: %s', artist_code)
        Log('artist_name: %s', artist_name)
        if artist_code is None:
            return

        album_title = None
        if manual:
            Log('Running custom search...')
            # Added 2016.3.25
            if media.name is not None:
                album_title = unicodedata.normalize('NFKC', unicode(media.name)).strip()
            else:
                album_title = media.title
        else:
            # 태그로 하지 않는다
            #media_name = media.parent_metadata.title + ' '
            #for no, track in media.tracks.items():
            #    media_name += ' ' + track.title
            #    break
            album_title = media.title

        Log('BBBBBBBBBBBBBBBBBBBBB')
        Log(album_title)
        keyword = '%s|%s|%s' % (album_title, artist_name, artist_code)

        Log('media.title : %s', media.title)
        Log('media.name : %s', media.name)
        Log('검색어 : %s', keyword)
        #search_data = self.send_search(self.module_name, movie_name, manual, year=movie_year)
        data = self.send_search(self.module_name, keyword, manual)

        Log(data)

        
        for item in data:
            meta = MetadataSearchResult(id=item['code'], name=item['title'], year='', score=item['score'], thumb=item['image'], lang=lang)
            meta.summary = self.change_html('{}\n'.format(item['desc']))
            meta.type = "movie"
            results.Append(meta) 



    def update(self, metadata, media, lang):
        code = metadata.id
        data = None
        if self.is_read_json(media):
            info_json = self.get_info_json(media)
            if info_json is not None:
                data = info_json
        if data is None:
            data = self.send_info(self.module_name, code)
            if data is not None and self.is_write_json(media):
                self.save_info(media, data)
        
        #data = self.send_info(self.module_name, code)
        #Log(self.d(data))
        
        metadata.title = data['title']
        metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
        metadata.summary = '%s\n%s' % (data['desc'], data['info_desc'])

        metadata.posters[data['image']] = Proxy.Media(HTTP.Request(data['image']))
        metadata.genres = data['genres']
        try: metadata.rating = float(data['rating']) *2
        except: pass
        

        metadata.studio = data['studio']
        metadata.originally_available_at = Datetime.ParseDate(data['originally_available_at']).date()
        

        metadata.album_type.add('정규')
        metadata.album_format.add('정규1')
        #if len(data['photo']) > 0:
        #    metadata.art[data['photo'][0]] = Proxy.Media(HTTP.Request(data['photo'][0]))
        #if len(data['photo']) > 1:
        #    metadata.art[data['photo'][1]] = Proxy.Media(HTTP.Request(data['photo'][1]))

        def get_track_meta(track_data, index):
            count = 0
            for cd in track_data:
                for track in cd:
                    count = count + 1
                    if count == index:
                        return track
            
        Log('가가가각')
        Log(metadata.album_format)
        Log(metadata.album_type)
        valid_track_keys = []
        valid_keys = defaultdict(list)
        for index in media.tracks:
            filename = os.path.splitext(os.path.basename(media.tracks[index].items[0].parts[0].file))[0]
            Log('filename: %s', filename)

            track_data = get_track_meta(data['track'], int(index))
            if track_data == None:
                continue
            Log(track_data['title'])

            track_key = media.tracks[index].id or int(index)
            Log('track_key: %s', track_key)
            Log('index: %s', index)
            
            valid_track_keys.append(track_key)
            t = metadata.tracks[track_key]
            Log(t.name)
            Log(t.title)
            Log(t.original_title)
            Log(t.artist)
            #t.title = filename.strip(' -._')
            t.original_title = track_data['singer']

            try:
                for idx, mode in enumerate(['txt']):
                    url = 'http://127.0.0.1:32400/:/plugins/com.plexapp.agents.sjva_agent/function/music_normal_lyric?mode={mode}&song_id={song_id}&track_key={track_key}'.format(
                        mode = mode,
                        song_id = track_data['song_id'], 
                        track_key = track_key,
                    )
                    metadata.tracks[track_key].lyrics[url] = Proxy.Remote(url, format = mode, sort_order=idx+1)
                    Log(url)
                    valid_keys[track_key].append(url)
                    Log(index)
                    Log('HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH')
                    Log(index)
                    """
                    if int(index) == 3:
                        Log('KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK')
                        url = 'https://dev.soju6jan.com/metadata/api/video?site={site}&param={param}&apikey={apikey}'.format(
                            site='youtube',
                            param='xgvckGs6xhU',
                            apikey='ooo5298ooo',
                        )
                        extra_url = 'sjva://sjva.me/playvideo/%s|%s' % ('youtube', 'QPntYezaHS4')

                        Log(url)

                        if extra_url is not None:
                            metadata.tracks[track_key].extras.add(
                                self.extra_map['musicvideo'](
                                    url=extra_url, 
                                    title='11출발 뮤직비디오',
                                    thumb='',
                                )
                            )
                    #else:
                    #    metadata.tracks[track_key].extras.clear()
                    """


            except Exception as e: 
                Log('Exception:%s', e)
                Log(traceback.format_exc())
                #metadata.tracks[track_key].lyrics.validate_keys(valid_keys[track_key])  
                
        metadata.tracks.validate_keys(valid_track_keys)

        for key in metadata.tracks:
            Log(key)
            Log(valid_keys[key])
            metadata.tracks[key].lyrics.validate_keys(valid_keys[key])




        return False

    

    