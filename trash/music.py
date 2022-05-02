# -*- coding: utf-8 -*-
"""
import urllib, unicodedata, json, difflib
import traceback, re


BASE_URL = 'http://music.naver.com'

ARTIST_SEARCH_URL = BASE_URL + '/search/search.nhn?query=%s&target=artist'
ARTIST_INFO_URL = BASE_URL + '/artist/intro.nhn?artistId=%s'
#ARTIST_ALBUM_URL = BASE_URL + '/artist/album.nhn?artistId=%s&isRegular=Y&sorting=popular'

ARTIST_ALBUM_URL = BASE_URL + '/artist/album.nhn?artistId=%s'
ARTIST_ALBUM_URL2 = BASE_URL + '/artist/album.nhn?artistId=%s&page=2'
ARTIST_PHOTO_URL = BASE_URL + '/artist/photoListJson.nhn?artistId=%s'

ALBUM_SEARCH_URL = BASE_URL + '/search/search.nhn?query=%s&target=album'
ALBUM_INFO_URL = BASE_URL + '/album/index.nhn?albumId=%s'

VARIOUS_ARTISTS_POSTER = 'http://userserve-ak.last.fm/serve/252/46209667.png'

RE_ARTIST_ID = Regex('artistId=(\d+)')
RE_ALBUM_ID = Regex('albumId=(\d+)')
RE_ALBUM_RATING = Regex(u'평점'+' (.*?)'+u'점')

def Start():
    HTTP.CacheTime = CACHE_1WEEK

########################################################################  
class NaverMusicAgent(Agent.Artist):
    name = 'Naver Music'
    languages = [Locale.Language.Korean, Locale.Language.English]
    accepts_from = ['com.plexapp.agents.localmedia']

    def search(self, results, media, lang, manual):
        # Handle a couple of edge cases where artist search will give bad results.
        if media.artist == '[Unknown Artist]': 
            return
        if media.artist == 'Various Artists':
            results.Append(MetadataSearchResult(id = 'Various%20Artists', name= 'Various Artists', thumb = VARIOUS_ARTISTS_POSTER, lang  = lang, score = 100))
            return

        # Search for artist.
        Log('Artist search: ' + media.artist)
        if manual:
            Log('Running custom search...')
            # Added 2016.3.25
            media_name = unicodedata.normalize('NFKC', unicode(media.artist)).strip()
        else:
            media_name = media.artist

        artists = self.score_artists(media, lang, SearchArtists(media_name))

        Log('Found ' + str(len(artists)) + ' artists...')
        for artist in artists:
            results.Append( MetadataSearchResult(id=artist['id'], name=artist['name'], lang=artist['lang'], score=artist['score']) )

    # 2020-03-09 네이버의 선택을 따른다. by soju6jan
    def score_artists(self, media, lang, artists):
        for i, artist in enumerate(artists):
            score = 100 - (i*5)
            score = 0 if score < 0 else score
            artist['score'] = score
            artists[i]['lang'] = lang
            Log.Debug('id: %s name: %s score: %d lang: %s' % (artist['id'], artist['name'], score, lang))
        return artists


    def update(self, metadata, media, lang):
        url = ARTIST_INFO_URL % metadata.id
        try: 
            html = HTML.ElementFromURL(url)
        except:
            raise Ex.MediaExpired

        metadata.title = html.xpath('//meta[@property="og:title"]')[0].get("content").replace(u'네이버뮤직 :: ', '').strip()
        metadata.title_sort = unicodedata.normalize('NFKD', metadata.title)
        Log.Debug('Artist Title: ' + metadata.title)
    
        try:
            summary = ''
            common = html.xpath('//div[@class="common"]//dt/text()')
            common2 = html.xpath('//div[@class="common"]//dd/text()')
            for i in range(0, len(common)):
                summary += common[i].strip() + ' : ' 
                xpath_str = '//div[@class="common"]//dd[%d]/a/text()' % (i+1)
                temp = html.xpath(xpath_str)
                if 0 == len(temp): summary += common2[i].strip()
                else: summary += ','.join(temp)
                summary += '\n'
            summary += '\n'
            summary += '\n'.join(html.xpath('//p[@class="dsc full"]//text()'))
            summary.strip()
            metadata.summary = summary
        except:
            pass

        # poster
        if metadata.title == 'Various Artists':
            metadata.posters[VARIOUS_ARTISTS_POSTER] = Proxy.Media(HTTP.Request(VARIOUS_ARTISTS_POSTER))
        else:
            img_url = html.xpath('//span[@class="thmb"]/span[contains(@class, "crop")]/img')[0].get('src')
            metadata.posters[img_url] = Proxy.Media(HTTP.Request(img_url))

        # genre
        metadata.genres.clear()
        try:
            for genre in html.xpath('//strong[@class="genre"]')[0].text.split(','):
                metadata.genres.add(genre.strip())
        except:
            pass

        # similar artist
        metadata.similar.clear()
        try:
            for similar in html.xpath('//strong[@class="tit"]'):
                metadata.similar.add(similar.text.strip())
        except:
            pass

        params = urllib.urlencode({'page': 1, 'artistId': metadata.id, 'musicianId': -1})
        r = urllib.urlopen("http://music.naver.com/artist/photoListJson.nhn", params).read()
        r = r.replace('thumbnail', '"thumbnail"')
        r = r.replace('original', '"original"')
        data = json.loads(r)
        jdata = data["photoList"]
        for i, item in enumerate(jdata):
            thumb = item.get("original")
            metadata.art[thumb] = Proxy.Preview(HTTP.Request(thumb), sort_order=(i+1))
            if i > 3:
                break

        if Prefs['artwork']:
            url = ARTIST_PHOTO_URL % metadata.id
            try: 
                data = JSON.ObjectFromURL(url)
                max_count = int(Prefs['artwork_count'])
                for i, pic in enumerate(data['photoList']):
                    metadata.art[pic['original']] = Proxy.Preview(HTTP.Request(pic['thumbnail']), sort_order=(i+1))
                    if i >= max_count:
                        break
            except:
                raise Ex.MediaExpired


########################################################################  
class NaverMusicAlbumAgent(Agent.Album):
    name = 'Naver Music'
    languages = [Locale.Language.Korean, Locale.Language.English]
    accepts_from = ['com.plexapp.agents.localmedia']

    def search(self, results, media, lang, manual):    
        if media.parent_metadata.id is None:
            return

        # Search for album.
        if manual:
            Log('Running custom search...')
            # Added 2016.3.25
            if media.name is not None:
                media_name = unicodedata.normalize('NFKC', unicode(media.name)).strip()
            else:
                media_name = media.title
        else:
            # 태그로 하지 않는다
            media_name = media.parent_metadata.title + ' '
            for no, track in media.tracks.items():
                media_name += ' ' + track.title

        try: 
            searches = [media_name, re.sub('\s?[\[\(].*?[\]\)]\s?', '', media_name)]
            Log(media_name)
            Log(searches[1])
            for search in searches:
                search = String.Quote(search.encode('utf-8'))
                url = 'https://music.naver.com/search/search.nhn?query=%s&target=album' % search
                Log(url)
                html = HTML.ElementFromURL(url)
                tags = html.xpath('//*[@id="content"]/div[3]/ul')
                find_flag = False
                if tags:
                    for idx, node in enumerate(tags):
                        tmp = node.xpath('li/dl/dd/a')
                        if len(tmp) > 0 and media.parent_metadata.id == tmp[0].attrib['href'].split('=')[1]:
                            score = 100
                        else:
                            score = 80
                            #Log(media.parent_metadata.id)
                            #Log(node.xpath('li/dl/dd/a')[0].attrib['href'].split('=')[1])
                            #continue
                        title = node.xpath('li/dl/dt/a/text()')[0]
                        if title.find(u'반주') == -1:
                            find_flag = True
                            results.Append( MetadataSearchResult(
                                id=node.xpath('li/div/a')[0].attrib['href'].split('=')[1], 
                                name=title, 
                                lang=lang, score=score- (idx*5)) )
                    if find_flag:
                        return

            for search in searches:
                search = String.Quote(search.encode('utf-8')) 
                # 곡 첫 트랙 앨범
                url = 'https://music.naver.com/search/search.nhn?query=%s&target=track' % search
                html = HTML.ElementFromURL(url)
                tags = html.xpath('//*[@id="content"]/div[3]/div[3]/table/tbody/tr[2]/td[5]/a')
                if tags:
                    results.Append( MetadataSearchResult(
                            id=tags[0].attrib['href'].split('=')[1], 
                            name=tags[0].text_content().strip(), 
                            lang=lang, score=100) )
                    return
        except:
            Log(traceback.format_exc())
            raise Ex.MediaExpired
        
        
        if manual:
            Log('Running custom search...')
            media_name = unicodedata.normalize('NFKC', unicode(media.name)).strip()
        else:
            media_name = media.title

        media_name = re.sub(r'\s?\[.*?\]\s?', '', media_name)
        Log('Album search: ' + media_name)
        Log('%s - %s', unicode(media.parent_metadata.title), media_name)
        albums = self.score_albums(media_name, lang, SearchAlbums(unicode(media.parent_metadata.title), media_name))
        Log('Found ' + str(len(albums)) + ' albums...')
        for album in albums:
            results.Append( MetadataSearchResult(id=album['id'], name=album['name'], lang=album['lang'], score=album['score']) )

        if len(albums) > 0:
            return
        Log('2nd try...')
        Log(media.tracks)
        albums = self.score_albums(media_name, lang, GetAlbumsByArtist(media.parent_metadata.id), legacy=True)
        Log('Found ' + str(len(albums)) + ' albums...')

        for album in albums:
            results.Append( MetadataSearchResult(id=album['id'], name=album['name'], lang=album['lang'], score=album['score']) )

    def score_albums(self, media_name, lang, albums, legacy=False):

        for i, album in enumerate(albums):
            id = album['id']
            name = album['name']
            s = difflib.SequenceMatcher(None, name.lower(), media_name.lower())
            score = int(s.ratio() * 100)      
            albums[i]['score'] = score
            albums[i]['lang'] = lang
            Log.Debug('id: %s name: %s score: %d lang: %s' % (id, name, score, lang))
        return albums


    def update(self, metadata, media, lang):
        Log.Debug('query album: '+metadata.id)
        url = ALBUM_INFO_URL % metadata.id
        try: 
            html = HTML.ElementFromURL(url)
        except:
            raise Ex.MediaExpired

        metadata.title = html.xpath('//h2')[0].text
        #metadata.album = html.xpath('//h2')[0].text
        #metadata.name = html.xpath('//h2')[0].text
        Log('Album Title: ' + html.xpath('//h2')[0].text)

        date_s = html.xpath('//dt[@class="date"]/following-sibling::dd')[0].text
        date_s = date_s.replace(".", "-")
        try:
            metadata.originally_available_at = Datetime.ParseDate(date_s)
        except:
            pass
        
        # rating
        try:
            metadata.rating = float(RE_ALBUM_RATING.search(html.xpath('//span[@class="_album_rating"]/em')[0].text).group(1))
        except:
            pass    

        try:
            common = html.xpath('//dl[@class="desc"]//dt/span/text()')
            common2 = html.xpath('//dl[@class="desc"]//dd/text()')
            intro = html.xpath('//p[contains(@class, "intro_desc")]//text()')
            summary = ''
            for i in range(0, len(common)):
                metadata.summary = summary
                summary += common[i].strip() + ' : ' 
                metadata.summary = summary
                xpath_str = '//dl[@class="desc"]//dd[%d]/a/text()' % (i+1)
                temp = html.xpath(xpath_str)
                if 0 == len(temp): summary += common2[i+1].strip()
                else: summary += ','.join(temp)
                metadata.summary = summary
                summary += '\n'
            summary += '\n'
            for str in intro:
                summary += str.strip() + '\n'
            summary.strip()
            
            try:
                metadata.studio = common2[4].strip()
            except:
                pass
        except:
            Log(traceback.format_exc())

        try:                     
            tracks = html.xpath('//*[@id="content"]/div[2]/div[2]/table/tbody/tr')
            summary += 'Tracks\n'
            for t in tracks[1:]:
                try:
                    summary += '%s - %s\n' % (t.xpath('td[@class="order"]/text()')[0], t.xpath('td[@class="name"]')[0].text_content().strip())
                except:
                    Log(traceback.format_exc())
            metadata.summary = summary
        except:
            Log(traceback.format_exc())
        

        # poster
        img_url = html.xpath('//meta[@property="og:image"]')[0].get('content')
        metadata.posters[img_url] = Proxy.Media(HTTP.Request(img_url))

        # genre
        metadata.genres.clear()
        
        # No genre case exist
        try:
            for genre in html.xpath('//dt[@class="type"]/following-sibling::dd')[0].text.split(','):
                metadata.genres.add(genre.strip())
        except:
            Log(traceback.format_exc())
        


########################################################################  
def SearchArtists(artist):
    url = ARTIST_SEARCH_URL % String.Quote(artist.encode('utf-8'))
    try: 
        html = HTML.ElementFromURL(url)
    except:
        raise Ex.MediaExpired

    artists = []
    #for node in html.xpath('//dt/a'):
    for node in html.xpath('//li[@style="width:49.9%"]'):
        try:
            id = RE_ARTIST_ID.search(node.xpath('./dl/dt/a')[0].get('href')).group(1)
            # 곡을 찾는데 앨범수가 나온다
            n_album = node.xpath('./dl/dd/a/em')[0].text
            artists.append({'id':id, 'name':node.xpath('./dl/dt/a')[0].get('title') })
        except:
            pass
    return artists


def GetAlbumsByArtist(artist):
    albums=[]
    url = ARTIST_ALBUM_URL % artist
    try: 
        html = HTML.ElementFromURL(url)
    except:
        raise Ex.MediaExpired

    album = []
    #for node in html.xpath('//a[contains(@class, "NPI=a:name")]'):
    for node in html.xpath('//div[@class="thmb_cover"]'):
        id = RE_ALBUM_ID.search(node.xpath('a')[0].get('href')).group(1)
        album.append({'id':id, 'name':node.xpath('./a/p/strong')[0].text})

    url = ARTIST_ALBUM_URL2 % artist
    try: 
        html = HTML.ElementFromURL(url)
    except:
        raise Ex.MediaExpired

    #for node in html.xpath('//a[contains(@class, "NPI=a:name")]'):
    for node in html.xpath('//div[@class="thmb_cover"]'):
        id = RE_ALBUM_ID.search(node.xpath('a')[0].get('href')).group(1)
        album.append({'id':id, 'name':node.xpath('./a/p/strong')[0].text})
    return album


def SearchAlbums(artist, album):
    if artist in album:
        q_str = album
    elif artist == 'None':
        q_str = album  
    else:
        q_str = album+' '+artist

    url = ALBUM_SEARCH_URL % String.Quote(q_str.encode('utf-8'))
    try: 
        html = HTML.ElementFromURL(url)
    except:
        raise Ex.MediaExpired

    album = []
    for node in html.xpath('//dt/a'):
        id = RE_ALBUM_ID.search(node.get('href')).group(1)
        album.append({'id':id, 'name':node.get('title')})
    return album

"""

import urllib, unicodedata, json, difflib
import traceback, re

########################################################################  
VARIOUS_ARTISTS_POSTER = 'http://userserve-ak.last.fm/serve/252/46209667.png'

class SjvaAgentArtist(Agent.Artist):
    name = 'SJVA Artist'
    languages = [Locale.Language.Korean, Locale.Language.English]
    accepts_from = ['com.plexapp.agents.localmedia']

    def search(self, results, media, lang, manual):
        if media.artist == '[Unknown Artist]': 
            return
        if media.artist == 'Various Artists':
            results.Append(MetadataSearchResult(id='Various Artists', name='Various Artists', thumb=VARIOUS_ARTISTS_POSTER, lang=lang, score=100))
            return

        Log('Artist search: ' + media.artist)
        artist = media_name = unicodedata.normalize('NFKC', unicode(media.artist)).strip() if manual else media.artist

        """
        artists = self.score_artists(media, lang, SearchArtists(media_name))

        Log('Found ' + str(len(artists)) + ' artists...')
        for artist in artists:
            results.Append( MetadataSearchResult(id=artist['id'], name=artist['name'], lang=artist['lang'], score=artist['score']) )
        """

    def update(self, metadata, media, lang):
        pass


########################################################################  
class SjvaAgentAlbum(Agent.Album):
    name = 'SJVA Album'
    languages = [Locale.Language.Korean, Locale.Language.English]
    accepts_from = ['com.plexapp.agents.localmedia']

    def search(self, results, media, lang, manual):    
        pass

    def update(self, metadata, media, lang):
        pass
        
