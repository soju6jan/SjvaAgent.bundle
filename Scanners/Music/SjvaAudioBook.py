# -*- coding: UTF-8 -*-
import os, sys, platform
reload(sys)
sys.setdefaultencoding('utf-8')

try:
    import logging
    import logging.handlers
    logger = logging.getLogger('sjva_audiobook')
    logger.setLevel(logging.DEBUG) 
    formatter = logging.Formatter(u'[%(asctime)s|%(levelname)s|%(filename)s|%(lineno)d] : %(message)s')
    file_max_bytes = 10 * 1024 * 1024 
    filename = os.path.join(os.path.dirname( os.path.abspath( __file__ ) ), '../../', 'Logs', 'sjva.scanner.audiobook.log')
    #fileHandler = logging.FileHandler(filename, encoding='utf8')
    fileHandler = logging.handlers.RotatingFileHandler(filename=filename, maxBytes=file_max_bytes, backupCount=5, encoding='utf8')
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)
except:
    pass

import re, traceback
import AudioFiles, Media

folder_regex = [
    r'\[(?P<author>.*?)\]\s*(?P<title>.*?)(\s?\[.*?\])?$'
]

file_regex = [
    r'^(?P<track>\d{1,3})',
    r'(?P<track>\d{1,3})(회|화|강)',
    r'\((?P<track>\d{1,3})\)',
    #r'(?P<track>\d{1,3})',
]


def Scan(path, files, mediaList, subdirs, language=None, root=None):
    AudioFiles.Scan(path, files, mediaList, subdirs, root)

    logger.debug('path : %s' % path)
    logger.debug('files count : %s' % len(files))
    if len(files) == 0:
        return
    folder = path.split(os.sep)[-1]
    match = re.match(folder_regex[0], folder)
    if match:
        logger.info("작가 : %s" % match.group('author'))
        logger.info("제목 : %s" % match.group('title'))
        artist = album_artist = match.group('author')
        album = match.group('title')
    else:
        album = folder
        artist = album_artist = ''
        
    
    for filepath in files:
        try:
            filename = os.path.basename(filepath)
            track = -1
            for regex in file_regex:
                match = re.search(regex, filename)
                if match:
                    track = int(match.group('track'))
                    logger.debug(regex)
                    break
            if track == -1:
                tmp = re.finditer(r'(?P<track>\d{1,3})', os.path.splitext(filename)[0])
                for m in tmp:
                    track = int(m.group())
            if track == -1:
                track = 1
               
            logger.debug("트랙번호 : %s - %s", track, filename)
            title = os.path.splitext(filename)[0].strip(' -._')
            t = Media.Track(cleanPass(artist), cleanPass(album), cleanPass(title), track, disc=1, album_artist=cleanPass(album_artist), guid=None, album_guid=None)
            t.parts.append(filepath)
            mediaList.append(t)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    logger.debug("미디어 수 : %s", len(mediaList))   








RE_UNICODE_CONTROL =  u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
                      u'|' + \
                      u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
                      (
                        unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
                        unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
                        unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff)
                      )

def cleanPass(t):
  try:
    t = re.sub(RE_UNICODE_CONTROL, '', t.strip().encode('utf-8'))
  except:
    pass
  return t

