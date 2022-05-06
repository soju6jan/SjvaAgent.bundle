# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, random, time
from .agent_base import AgentBase
from collections import defaultdict

VARIOUS_ARTISTS_POSTER = 'https://music.plex.tv/pixogs/various_artists_poster.jpg'


class ModuleMusicNormalArtist(AgentBase):
    module_name = 'music_normal_artist'
    
    def search(self, results, media, lang, manual, **kwargs):
        try:
            if media.artist == '[Unknown Artist]': 
                return
            if media.artist == 'Various Artists':
                #results.Append(MetadataSearchResult(id = 'Various%20Artists', name= '[Various Artists]', thumb = VARIOUS_ARTISTS_POSTER, lang  = lang, score = 100))
                results.Append(MetadataSearchResult(id='SD%s' % int(time.time()), name= '[Various Artists]', thumb = VARIOUS_ARTISTS_POSTER, lang  = lang, score = 100))
                return

            if manual and media.artist is not None and (media.artist.startswith('SA')):
                code = media.artist
                meta = MetadataSearchResult(id=code, name=code, year='', score=100, thumb="", lang=lang)
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
            
            # 동명이인... 폴더에 있는 [MA1234] 처리
            json_path = self.get_json_filepath(media)
            album_basename = os.path.basename(os.path.dirname(json_path))
            match = re.search("\[MA(?P<code>\d+)\]", album_basename)
            if match:
                meta = MetadataSearchResult(id='SA%s' % match.group('code'), name=album_basename, year='', score=100, thumb='', lang=lang)
                results.Append(meta) 

            if manual:
                keyword = '%s|%s' % (media.artist, media.album)
            else:
                keyword = '%s|%s' % (media.title, media.album)
            Log('media.artist : %s', media.artist)
            Log('KEYWORD : %s', keyword)
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
        if code.startswith('SD'):
            metadata.title = '[Various Artists]'
            metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
            metadata.posters[VARIOUS_ARTISTS_POSTER] = Proxy.Media(HTTP.Request(VARIOUS_ARTISTS_POSTER))
            return
        data = None
        if self.is_read_json(media):
            info_json = self.get_info_json(media)
            if info_json is not None:
                data = info_json
        if data is None:
            data = self.send_info(self.module_name, code)
            Log("JSON WRITE : %s", self.is_write_json(media))
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
        if manual and media.name is not None and (media.name.startswith('SM')):
            code = media.name
            meta = MetadataSearchResult(id=code, name=code, year='', score=100, thumb="", lang=lang)
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

        artist_code = media.parent_metadata.id
        artist_name = media.parent_metadata.title
        Log('artist_code: %s', artist_code)
        Log('artist_name: %s', artist_name)
        
        # 폴더명에 있는 날짜
        album_folder_name = os.path.basename(os.path.dirname(self.get_json_filepath(media)))
        pub_date = date_from_target(album_folder_name)
        Log("album_folder_name : %s [%s]", album_folder_name, pub_date)

        album_title = None
        if manual:
            if media.name is not None:
                album_title = re.sub("\[.*?\]", '', media.name).strip()
            else:
                album_title = re.sub("\[.*?\]", '', media.title).strip()
        else:
            album_title = re.sub("\[.*?\]", '', media.title).strip()

        keyword = '%s|%s|%s|%s' % (album_title, artist_name, artist_code, pub_date)
        Log('keyword : %s', keyword)
        #search_data = self.send_search(self.module_name, movie_name, manual, year=movie_year)
        data = self.send_search(self.module_name, keyword, manual)
        #Log(data)

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
        
        #metadata.title = '[%s] %s' % (data['album_type'], data['title'])

        #Log(self.d(data))
        #Log( 'title' in data)
        #Log( 'code' in data)
        #Log("title : %s", data['title'])
        try:
            #Log('title' in data)
            #tmp = u'%s' % data['titie'] 1818181818
            tmp = unicode(data['title'])
            metadata.title_sort = unicodedata.normalize('NFKD', tmp)
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
            new_string = ''.join(char for char in data['title'] if char.isalnum() or char == ' ')
            metadata.title_sort = unicodedata.normalize('NFKD', new_string)
            # 특수문자 때문에
            #Log("title : %s", tmp)
            # iter 안 먹음
            #new = []
            #for i in len(tmp):
            #    if tmp[i] == ' ' or tmp[i].isalnum():
            #        new.append(tmp[i])
            
            #metadata.title_sort = unicodedata.normalize('NFKD', new_string)

        metadata.summary = '%s\n%s' % (data['desc'], data['info_desc'])

        metadata.posters[data['image']] = Proxy.Media(HTTP.Request(data['image']))
        metadata.genres = [data['album_type']] + data['genres']
        try: metadata.rating = float(data['rating']) *2
        except: pass

        metadata.studio = data['studio']
        metadata.originally_available_at = Datetime.ParseDate(data['originally_available_at']).date()
        

        valid_track_keys = []
        valid_keys = defaultdict(list)
        Log("==========================================")
        Log("media.children : %s", len(media.children))
        Log("media.tracks : %s", len(media.tracks))

        more_disc = True if len(media.children) != len(media.tracks) else False 
        #for index in media.tracks:
        for index, track_media in enumerate(media.children):
            track_key = track_media.id or index

            #data = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s/children' % track_key)

            if more_disc:
                # 18 disc index 알수 있는 방법이 없음.
                cu = AgentBase.my_JSON_ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s?includeChildren=1' % track_key)
                #Log(cu)
                disc_index = cu['MediaContainer']['Metadata'][0]['parentIndex']
            else:
                disc_index = 1
            
            #continue
            valid_track_keys.append(track_key)
            #Log(len(media.tracks[index].items))
            #filename = os.path.splitext(os.path.basename(media.tracks[index].items[0].parts[0].file))[0]
            #Log('filename: %s', filename)

            try:
                track_data = data['track'][disc_index-1][int(track_media.index)-1]
            except:
                track_data = None
                Log("ERROR: disc_index %s %s", disc_index, track_media.index)

            if track_data == None:
                continue
            track_meta = metadata.tracks[track_key]
            """
            Log("---------------------------------------")
            Log('INDEX: %s', index)
            Log('TRACK_KEY: %s', track_key)
            Log('track_media.index: %s', track_media.index) #CD별로 동일. 트랙번호
            Log('track_media.absoluteIndex: %s', track_media.absoluteIndex) #의미없는 index
            Log("PLEX데이터 미디어: %s", track_media.title)
            Log("PLEX데이터 메타: %s", track_meta.title)
            Log("PLEX데이터 disc_index: %s", track_meta.disc_index)
            Log("PLEX데이터 track_index: %s", track_meta.track_index)
            Log("에이전트데이터: %s", track_data['title'])
            """

            #track_key = media.tracks[index].id or int(index)
            #valid_track_keys.append(track_key)
            #t = metadata.tracks[track_key]
            if track_data['singer'] != '':
                #track_meta.original_title = track_data['singer']
                if track_data['title'] == track_media.title:
                    track_meta.original_title = '%s' % (track_data['singer'])
                else:
                    track_meta.original_title = '%s - %s' % (track_data['singer'], track_data['title'])

            if track_data['song_id'] == '':
                continue
            try: 
                for idx, mode in enumerate(['txt']):
                    url = 'http://127.0.0.1:32400/:/plugins/com.plexapp.agents.sjva_agent/function/music_normal_lyric?mode={mode}&song_id={song_id}&track_key={track_key}'.format(
                        mode = mode,
                        song_id = track_data['song_id'], 
                        track_key = track_key,
                    )
                    metadata.tracks[track_key].lyrics[url] = Proxy.Remote(url, format = mode, sort_order=idx+1)
                    valid_keys[track_key].append(url)
                    """
                    # MUSICVIDEO
                    if int(index) == 3:
                        extra_url = 'sjva://sjva.me/playvideo/%s|%s' % ('youtube', 'QPntYezaHS4')
                        Log(url)
                        metadata.tracks[track_key].extras.add(
                            self.extra_map['musicvideo'](
                                url=extra_url, 
                                title='11출발 뮤직비디오',
                                thumb='',
                            )
                        )
                    """
            except Exception as e: 
                Log('Exception:%s', e)
                Log(traceback.format_exc())
                #metadata.tracks[track_key].lyrics.validate_keys(valid_keys[track_key])  
                
        metadata.tracks.validate_keys(valid_track_keys)

        for key in metadata.tracks:
            #Log(key)
            #Log(valid_keys[key])
            metadata.tracks[key].lyrics.validate_keys(valid_keys[key])

        metadata.title = '[%s] %s' % (data['album_type'], data['title'])
        return False


    




# date on folder basename

def date_from_target(target):
    regex = '[^\d](?P<year>\d{4})([\.-]?(?P<month>\d{1,2})([\.-]?(?P<day>\d{1,2}))?)?[^\d]'
    try:
        match = re.search(regex, target)
        if match == None:
            return ''
        year = int(match.group('year'))
        if year < 1900 or year > 2100:
            return ''
        
        if 'month' not in match.groupdict():
            return str(year)
        month = int(match.group('month'))
        if month < 1 or month > 12:
            return str(year)
        
        if 'day' not in match.groupdict():
            return str(year) + str(month).zfill(2)
        day = int(match.group('day'))
        if day < 1 or day > 31:
            return str(year) + str(month).zfill(2)
        
        return str(year) + str(month).zfill(2) + str(day).zfill(2)
    except:
        return ''

