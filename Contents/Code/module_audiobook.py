# -*- coding: utf-8 -*-
import os, unicodedata, urllib, traceback, re, time
from .agent_base import AgentBase
VARIOUS_ARTISTS_POSTER = 'https://music.plex.tv/pixogs/various_artists_poster.jpg'

# 정상 : BN코드A / BN코드
# VA : BA앨범이름 / BB앨범이름
class ModuleAudiobookArtist(AgentBase):
    module_name = 'book'
    
    def search(self, results, media, lang, manual, **kwargs):
        try:
            if media.artist.startswith('Various Artists_'):
                results.Append(MetadataSearchResult(id='BA%s' % urllib.quote(media.artist.replace('Various Artists_', '')), name= '[Various Artists]', thumb = VARIOUS_ARTISTS_POSTER, lang  = lang, score = 100))
                return
                
            if self.is_read_json(media):
                if manual:
                    self.remove_info(media)
                else:
                    info_json = self.get_info_json(media)
                    if info_json is not None:
                        code = info_json['code'] + 'A'
                        meta = MetadataSearchResult(id=code, name=info_json['author'], year='', score=100, thumb="", lang=lang)
                        results.Append(meta)
                        return

            json_path = self.get_json_filepath(media)
            folder_name = os.path.basename(os.path.dirname(json_path))
            book_name = ''
            if folder_name.count(' - ') > 0:
                book_name = folder_name.split(' - ', 1)[1]
                book_name = re.sub("\[.*?\]", '', book_name).strip()
            if manual:
                keyword = media.artist
                if keyword.find('|') == -1:
                    keyword = book_name + '|' + keyword
            else:
                #keyword = '%s|%s' % (media.album, media.title)
                keyword = '%s|%s' % (book_name, media.title)
            Log('검색어 : %s', keyword)
            data = self.send_search(self.module_name, keyword, manual)
            if data == None:
                results.Append(MetadataSearchResult(id='BE%s' % urllib.quote(media.artist), name= media.artist, thumb = VARIOUS_ARTISTS_POSTER, lang  = lang, score = 100))
                return

            for item in data:
                meta = MetadataSearchResult(id=item['code'] + 'A', name=item['author'], year='', score=item['score'], thumb=item['image'], lang=lang)
                meta.summary = self.change_html('작품 : {}\n'.format(item['title']) + self.search_result_line() + item['description'])
                meta.type = "movie"
                results.Append(meta) 
        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())    



    def update(self, metadata, media, lang):
        try:
            # 수동 일치항목 찾기로 변경할 수가 없다.
            # 앨범에 있는 json 을 지우자니 앨범 데이터가 문제고..
            # 작가가 없는 경우 새로 입힐 방법이 없음
            code = metadata.id
            if code.startswith('BA'):
                metadata.title = '[Various Artists]'
                metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
                metadata.posters[VARIOUS_ARTISTS_POSTER] = Proxy.Media(HTTP.Request(VARIOUS_ARTISTS_POSTER))
                return
            if code.startswith('BE'):
                metadata.title = urllib.unquote(code[2:])
                metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
                metadata.posters[VARIOUS_ARTISTS_POSTER] = Proxy.Media(HTTP.Request(VARIOUS_ARTISTS_POSTER))
                return
            data = None
            if self.is_read_json(media):
                info_json = self.get_info_json(media)
                if info_json is not None:
                    data = info_json
            if data is None:
                data = self.send_info(self.module_name, code[:-1])
                if data is not None and self.is_write_json(media):
                    self.save_info(media, data)
            
            #data = self.send_info(self.module_name, code)
            Log(self.d(data))
            if 'author' in data:
                metadata.title = data['author']
                metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
            if 'author_intro' in data:
                metadata.summary = data['author_intro']
            if 'poster' in data:
                metadata.posters[data['poster']] = Proxy.Media(HTTP.Request(data['poster']))
        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc()) 
        























class ModuleAudiobookAlbum(AgentBase):
    module_name = 'book'
    
    def search(self, results, media, lang, manual, **kwargs):
        try:
            artist_code = media.parent_metadata.id
            artist_name = media.parent_metadata.title
            Log('artist_code: %s', artist_code)
            Log('artist_name: %s', artist_name)
            if artist_code != None and artist_code.startswith('BA') and manual == False:
                meta = MetadataSearchResult(id='BB' + artist_code[2:], name=urllib.unquote(artist_code[2:]), year='', score=100, thumb="", lang=lang)
                results.Append(meta)
                return

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
                Log(keyword)
            if keyword is None:
                keyword = '%s|%s' % (media.album, media.artist)

            data = self.send_search(self.module_name, keyword, manual)
            #if data == None:
            #    return
            if data == None or (data != None and len(data) == 0):
                meta = MetadataSearchResult(id='BD%s' % int(time.time()), name=media.album, year='', score=100, thumb="", lang=lang)
                results.Append(meta)
                return

            for item in data:
                #Log(self.d(item))
                meta = MetadataSearchResult(id=item['code'], name=item['title'], year='', score=item['score'], thumb=item['image'], lang=lang)
                meta.summary = self.change_html('작가 : {}\n'.format(item['author']) + self.search_result_line() + item['description'])
                meta.type = "movie"
                results.Append(meta) 
        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())    


    def set_track(self, metadata, media):
        valid_track_keys = []
        for index, track_media in enumerate(media.children):
            Log(track_media.title)
            track_key = track_media.id or index
            valid_track_keys.append(track_key)
            track_meta = metadata.tracks[track_key]
            track_meta.title = track_media.title
        metadata.tracks.validate_keys(valid_track_keys)
        return


    def update(self, metadata, media, lang):
        try:
            data = None
            code = metadata.id
            if code.startswith('BB'):
                metadata.title = urllib.unquote(code[2:])
                metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
                metadata.posters[VARIOUS_ARTISTS_POSTER] = Proxy.Media(HTTP.Request(VARIOUS_ARTISTS_POSTER))
                self.set_track(metadata, media)
                return
            if code.startswith('BD'):
                metadata.title = media.title
                metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
                metadata.posters[VARIOUS_ARTISTS_POSTER] = Proxy.Media(HTTP.Request(VARIOUS_ARTISTS_POSTER))
                self.set_track(metadata, media)
                return
                

            if self.is_read_json(media):
                info_json = self.get_info_json(media)
                if info_json is not None:
                    data = info_json
            if data is None:
                data = self.send_info(self.module_name, code)
                if data is not None and self.is_write_json(media):
                    self.save_info(media, data)
            #Log(self.d(data))
            #data = self.send_info(self.module_name, code)
            metadata.title = data['title']
            metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
            metadata.summary = data['desc']
            metadata.posters[data['poster']] = Proxy.Media(HTTP.Request(data['poster']))
            metadata.rating = float(data['ratings'])
            metadata.studio = data.get('publisher', '')
            if 'premiered' in data:
                metadata.originally_available_at = Datetime.ParseDate(data['premiered']).date()
            
            valid_track_keys = []
            for index in media.tracks:
                filename = os.path.splitext(os.path.basename(media.tracks[index].items[0].parts[0].file))[0]
                track_key = media.tracks[index].id or int(index)
                valid_track_keys.append(track_key)
                t = metadata.tracks[track_key]
                t.title = filename.strip(' -._')
                t.original_title = data.get('author', '')
            metadata.tracks.validate_keys(valid_track_keys)
        except Exception as exception: 
            Log('Exception:%s', exception)
            Log(traceback.format_exc())    