# -*- coding: UTF-8 -*-
import os, sys, platform, traceback
reload(sys)
sys.setdefaultencoding('utf-8')

try:
    import logging
    import logging.handlers
    logger = logging.getLogger('sjva_music_normal')
    logger.setLevel(logging.DEBUG) 
    formatter = logging.Formatter(u'[%(asctime)s|%(levelname)s|%(filename)s|%(lineno)d] : %(message)s')
    file_max_bytes = 10 * 1024 * 1024 
    filename = os.path.join(os.path.dirname( os.path.abspath( __file__ ) ), '../../', 'Logs', 'sjva.scanner.musicnormal.log')
    #fileHandler = logging.FileHandler(filename, encoding='utf8')
    fileHandler = logging.handlers.RotatingFileHandler(filename=filename, maxBytes=file_max_bytes, backupCount=5, encoding='utf8')
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)
except:
    pass



def Scan(path, files, mediaList, subdirs, language=None, root=None):
  Filter.Scan(path, files, mediaList, subdirs, audio_exts, root)
  Process(path, files, mediaList, subdirs, language, root)


import Filter, Media
import os.path
import re, os, string


audio_exts = ['mp3', 'm4a', 'm4b', 'flac', 'aac', 'rm', 'rma', 'mpa', 'wav', 'wma', 'ogg', 'mp2', 'mka',
              'ac3', 'dts', 'ape', 'mpc', 'mp+', 'mpp', 'shn', 'oga', 'aiff', 'aif', 'wv', 'dsf', 'dsd', 'opus']
various_artists = ['va', 'v/a', 'various', 'various artists', 'various artist(s)', 'various artitsen', 'verschiedene']
langDecodeMap = {'ko': ['euc_kr','cp949']}

# Unicode control characters can appear in ID3v2 tags but are not legal in XML.
RE_UNICODE_CONTROL =  u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
                      u'|' + \
                      u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
                      (
                        unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
                        unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
                        unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff)
                      )

# 가수/앨범명/트랙번호 - 타이틀.확장자
# 가수 - 앨범명/트랙번호 - 타이틀.확장자

def Process(path, files, mediaList, subdirs, language=None, root=None):
  if len(files) < 1: return
  albumTracks = []
  logger.debug('PATH: %s', path)
  track_map = {}
  # Various Artists
  va_flag = None

  album_path = os.path.dirname(files[0])
  match = re.match('(CD|DISC)\s?(?P<disc>\d+)', os.path.basename(album_path), re.IGNORECASE)
  if match:
    # CD 폴더는 한단계 위까지 검사해야하기 때문에..
    album_path = os.path.dirname(os.path.dirname(files[0]))
  artist_path, album_name = os.path.split(album_path)
  cate_path, artist_name = os.path.split(artist_path)
  
  # V.A 파일은 반드시 cate root에만 있도록 수정
  # 카테 / 아티스트 / 앨범 구조면 아티스명 살림
  # 카테 / 앨범 구조만 VA로 리턴
  # 즉 아티스트폴더인줄 알았더니 V.A가 있다면 카테고리 - 앨범임
  # 다만 카테 / 아티스트 / 앨범일 때 아티스트 명은 넘기지만 검색을 하지 않도록 한다.
  
  # 카테 / 중간카테 / 앨범 : 무조건 VA 처리를 위한 파일 - VA2
  if os.path.exists(os.path.join(cate_path, 'VA1')):
    va_flag = "va_depth1"
  elif os.path.exists(os.path.join(cate_path, 'VA2')):
    va_flag = "va_depth2_artist_dummy"
  elif os.path.exists(os.path.join(artist_path, 'VA2')):
    va_flag = "va_depth1"
  #elif os.path.exists(os.path.join(album_path, 'V.A')):
  #  va_flag = True
  #elif album_name.startswith('V.A'):
  #  va_flag = True

  last_track_index = 0

  for f in files:
    try:
      logger.info(f)
      artist = None
      parsed_title = False

      # 무조건 None
      (artist, album, title, track, disc, album_artist, compil) = getInfoFromTag(f, language)
      
      # Presense of an album artist is a key thing, so if it's empty, treat it like it doesn't exist.
      if album_artist is not None and len(album_artist) == 0:
        album_artist = None
      
      #print 'artist: ', artist, ' | album_artist: ', album_artist, ' | album: ', album, ' | disc: ', str(disc), ' | title: ', title, ' | compilation: ' + str(compil)
      if album_artist and album_artist.lower() in various_artists: #(compil == '1' and (album_artist is None or len(album_artist.strip()) == 0)) or (
        album_artist = 'Various Artists'
      if artist == None or len(artist.strip()) == 0:
        artist = '[Unknown Artist]'
      if album == None or len(album.strip()) == 0:
        album = '[Unknown Album]'
      if title == None or len(title) == 0: #use the filename for the title
        title = os.path.splitext(os.path.split(f)[1])[0] #확장자 제외 파일명
        parsed_title = True

      logger.debug('title: %s', title)
      logger.debug('parsed_title: %s', parsed_title)

      if track == None:
        # See if we have a tracknumber in the title; if so, extract and strip it.
        file = os.path.splitext(os.path.basename(f))[0]
        # 18 4MEN - The 3rd Generation (Special Album) - 03. Memories
        m = re.match("^([0-9]{1,3})([^0-9].*)$", file) or re.match(".*[ \-\.]+([0-9]{2})[ \-\.]+([^0-9].*)$", file) or re.match("^[a-f]([0-9]{2})[ \-\.]+([^0-9].*)$", file)
        if m:
          track, new_title = int(m.group(1)), m.group(2)
          #if track > 100 and track % 100 < 50:
          #  disc = track / 100
          #  track = track % 100
          
          # If we don't have a title, steal it from the filename.
          # When taken from the filename, we want to remove special characters.
          if title == None or parsed_title == True:
            title = new_title.strip(' -._')
      else:
        # Check to see if the title starts with the track number and whack it.
        title = re.sub("^[ 0]*%s[ ]+" % track, '', title)

      title = title.strip()
      logger.debug('title2 : %s', title)

      (allbutParentDir, parentDir) = os.path.split(os.path.dirname(f))
      # 잘못된 파일이 너무 많음.
      #if title.count(' - ') == 1 and artist == '[Unknown Artist]': # see if we can parse the title for artist - title
      #  (artist, title) = title.split(' - ')
      #  if len(artist) == 0: artist = '[Unknown Artist]'
      
      # 이것도 앨범제목에 - 이 들어가는게 너무 많음.
      #if parentDir and parentDir.count(' - ') == 1 and (artist == '[Unknown Artist]' or album == '[Unknown Album]'):  #see if we can parse the folder dir for artist - album
      #  (pathArtist, pathAlbum) = parentDir.split(' - ')
      #  if artist == '[Unknown Artist]': artist = re.sub("\[.*?\]", '', pathArtist).strip() 
      #  if album == '[Unknown Album]': album = re.sub("\[.*?\]", '', pathAlbum).strip() 
      
      disc = '1'
      match = re.match('(CD|DISC)\s?(?P<disc>\d+)', parentDir, re.IGNORECASE)
      if match:
        disc = match.group('disc')
        (allbutParentDir, parentDir) = os.path.split(allbutParentDir)

      if album == '[Unknown Album]' and parentDir:
        album = re.sub("\[.*?\]", '', parentDir).strip()
      if artist == '[Unknown Artist]' and parentDir:
        (allbutParentDir2, parentDir2) = os.path.split(allbutParentDir)
        artist = re.sub("\[.*?\]", '', parentDir2).strip()

      if va_flag == 'va_depth2_artist_dummy':
        artist = 'VA_%s' % artist
      elif va_flag == 'va_depth1':
        artist = 'Various Artists_%s' % (cleanPass(album))

      if track != None:
        last_track_index = int(track)
      else:
        track = last_track_index + 1
        last_track_index = track

      #make sure our last move is to encode to utf-8 before handing text back.
      logger.debug('=============================================')
      logger.debug('LAST artist : %s', cleanPass(artist))
      logger.debug('LAST album : %s', cleanPass(album))
      logger.debug('LAST title : %s', cleanPass(title))
      logger.debug('LAST track : %s', track)
      logger.debug('LAST disc : %s', disc)
      logger.debug('LAST album_artist : %s', cleanPass(album_artist))

      

      disc = str(add_map(track_map, disc, track))

      t = Media.Track(cleanPass(artist), cleanPass(album), cleanPass(title), track, disc=disc, album_artist=cleanPass(album_artist), guid=None, album_guid=None)
      t.parts.append(f)
      albumTracks.append(t)
      logger.debug('Adding: [Artist: %s] [Album: %s] [Title: %s] [Tracknumber: %s] [Disk: %s] [Album Artist: %s] [File: %s]' % (artist, album, title, track, disc, album_artist, f))
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())
      logger.debug("Skipping (Metadata tag issue): " + f)

  #add all tracks in dir, but first see if this might be a Various Artist album
  #first, let's group the albums in this folder together
  albumsDict = {}
  artistDict = {}
  for t in albumTracks:
    #add all the album names to a dictionary
    if albumsDict.has_key(t.album.lower()):
      albumsDict[t.album.lower()].append(t)
    else:
      albumsDict[t.album.lower()] = [t]
    #count instances of same artist names
    if artistDict.has_key(t.artist):
      artistDict[t.artist] +=1 
    else:
      artistDict[t.artist] = 1
      
  try: (maxArtistName, maxArtistCount) = sorted(artistDict.items(), key=lambda (k,v): (v,k))[-1]
  except: maxArtistCount = 0
  
  percentSameArtist = 0
  if len(albumTracks) > 0:
    percentSameArtist = float(maxArtistCount)/len(albumTracks)
    
  #next, iterate through the album keys, and look at the tracks inside each album
  for a in albumsDict.keys():
    sameAlbum = True
    sameArtist = True
    sameAlbumArtist = True
    prevAlbum = None
    prevArtist = None
    prevAlbumArtist = None
    blankAlbumArtist = True
    for t in albumsDict[a]:
      if prevAlbum == None: prevAlbum = t.album
      if prevArtist == None: prevArtist = t.artist
      if prevAlbumArtist == None: prevAlbumArtist = t.album_artist
      if prevAlbum.lower() != t.album.lower(): sameAlbum = False
      if prevArtist.lower() != t.artist.lower(): sameArtist = False
      if prevAlbumArtist and t.album_artist and prevAlbumArtist.lower() != t.album_artist.lower(): sameAlbumArtist = False
      prevAlbum = t.album
      prevArtist = t.artist
      if t.album_artist and len(t.album_artist.strip()) > 0:
        blankAlbumArtist = False

    if sameAlbum == True and sameArtist == False and blankAlbumArtist:
      if percentSameArtist < .9: #if the number of the same artist is less than X%, let's VA it (else, let's use the most common artist)
        newArtist = 'Various Artists'
      else:
        newArtist = maxArtistName
      for tt in albumsDict[a]:
        tt.album_artist = newArtist
    
    # Same artist and album, but album artist look whacky? Make consistent.
    if sameArtist and sameAlbum and not sameAlbumArtist:
      for tt in albumsDict[a]:
        tt.album_artist = tt.artist
        
  for t in albumTracks:
    mediaList.append(t)
  return

def cleanPass(t):
  try:
    t = re.sub(RE_UNICODE_CONTROL, '', t.strip().encode('utf-8'))
  except:
    pass
  return t


def getInfoFromTag(filename, language):
  return (None, None, None, None, None, None, None)


def add_map(track_map, disc, track):
  disc = int(disc)
  track = int(track)
  while True:
    if str(disc) not in track_map:
      track_map[str(disc)] = []
    if track not in track_map[str(disc)]:
      track_map[str(disc)].append(track)
      return str(disc)
    disc = disc + 1