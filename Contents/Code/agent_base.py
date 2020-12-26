# -*- coding: utf-8 -*-
import os, traceback
import urllib
import re
import unicodedata
from functools import wraps

"""
class MetadataSearchResult(XMLObject):
  def __init__(self, core, id, name=None, year=None, score=0, lang=None, thumb=None):
    XMLObject.__init__(self, core, id=id, thumb=thumb, name=name, year=year, score=score, lang=lang)
    self.tagName = "SearchResult"
"""


class AgentBase(object):

    def try_except(original_function):
        @wraps(original_function)
        def wrapper_function(*args, **kwargs):  #1
            try:
                return original_function(*args, **kwargs)
            except Exception as exception: 
                Log('Exception:%s', exception)
                Log(traceback.format_exc())
        return wrapper_function

    def get_search_keyword(self, media, manual, from_file=False):
        try:
            Log('## AgentBase ## get_search_keyword ## media:%s, manual:%s, from_file:%s' % (media.name, manual, from_file))
            if manual:
                ret = unicodedata.normalize('NFKC', unicode(media.name)).strip()
            else:
                if from_file:
                    data = JSON.ObjectFromURL('http://127.0.0.1:32400/library/metadata/%s' % media.id)
                    filename = data['MediaContainer']['Metadata'][0]['Media'][0]['Part'][0]['file']
                    ret = os.path.splitext(os.path.basename(filename))[0]
                    ret = re.sub('\s*\[.*?\]', '', ret).strip()
                    match = Regex(r'(?P<cd>cd\d{1,2})$').search(ret) 
                    if match:
                        ret = ret.replace(match.group('cd'), '')
                else:
                    # from_scanner
                    ret = media.name
            return ret
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())


    def send_search(self, module_name, keyword, manual):
        try:
            url = '{ddns}/metadata/api/{module_name}/search?keyword={keyword}&manual={manual}&apikey={apikey}'.format(
              ddns=Prefs['server'],
              module_name=module_name,
              keyword=urllib.quote(keyword.encode('utf8')),
              manual=manual,
              apikey=Prefs['apikey']
            )
            Log(url)
            return JSON.ObjectFromURL(url, timeout=int(Prefs['timeout']))
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())
    

    def send_info(self, module_name, code):
        try:
            url = '{ddns}/metadata/api/{module_name}/info?code={code}&apikey={apikey}'.format(
              ddns=Prefs['server'],
              module_name=module_name,
              code=urllib.quote(code.encode('utf8')),
              apikey=Prefs['apikey']
            )
            Log(url)
            return JSON.ObjectFromURL(url, timeout=int(Prefs['timeout']))
        except Exception as e: 
            Log('Exception:%s', e)
            Log(traceback.format_exc())

    
    def change_html(self, text):
        if text is not None:
            return text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#35;', '#').replace('&#39;', "‘")


    """
    LyricFind.bundle/Contents/Code/__init__.py:      metadata.tracks[track_key].lyrics[url] = Proxy.Remote(url, format = 'lrc', sort_order=sort_order)
./LyricFind.bundle/Contents/Code/__init__.py:    metadata.tracks[track_key].lyrics[url] = Proxy.Remote(url, format = 'txt', sort_order=sort_order)
./LyricFind.bundle/Contents/Code/__init__.py:  # We need to recreate the Proxy objects to effectively pass them through since the Framework doesn't
./LyricFind.bundle/Contents/Code/__init__.py:      metadata.tracks[track_key].lyrics[key] = Proxy.Remote(key, format='lrc' if '&lrc=1' in key else 'txt', sort_order=sort_order)
^C
    """
