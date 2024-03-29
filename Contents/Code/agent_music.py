# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, time
from .agent_base import AgentBase
from .module_music_normal import ModuleMusicNormalArtist, ModuleMusicNormalAlbum
from .module_audiobook import ModuleAudiobookArtist, ModuleAudiobookAlbum
from .module_yaml_music import ModuleYamlArtist, ModuleYamlAlbum
from .module_lyric import ModuleLyric

class AgentArtist(Agent.Artist):
    name = "SJVA 설정"
    languages = [Locale.Language.Korean]
    primary_provider = True
    #accepts_from = ['com.plexapp.agents.localmedia', 'com.plexapp.agents.localmediapatch', 'com.plexapp.agents.xbmcnfo']
    #contributes_to = ['com.plexapp.agents.xbmcnfo']

    instance_list = { 
        'S' : ModuleMusicNormalArtist(),
        'B' : ModuleAudiobookArtist(),
        'Y' : ModuleYamlArtist(),
    }

    def search(self, results, media, lang, manual):
        key = AgentBase.get_key(media)
        Log('Key : %s', key)
        ret = self.instance_list['Y'].search(results, media, lang, manual)
        if ret or key == 'Y':
            return
        self.instance_list[key].search(results, media, lang, manual)
        
    def update(self, metadata, media, lang):
        Log('updata : %s', metadata.id)
        self.instance_list[metadata.id[0]].update(metadata, media, lang)
        if metadata.id[0] != 'Y':
            self.instance_list['Y'].update(metadata, media, lang, is_primary=False)


class AgentAlbum(Agent.Album):
    name = "SJVA 설정"
    languages = [Locale.Language.Korean]
    primary_provider = True
    #accepts_from = ['com.plexapp.agents.localmedia', 'com.plexapp.agents.xbmcnfo']
    #contributes_to = ['com.plexapp.agents.xbmcnfo']

    instance_list = { 
        'S' : ModuleMusicNormalAlbum(),
        'B' : ModuleAudiobookAlbum(),
        'Y' : ModuleYamlAlbum(),
        'L' : ModuleLyric(),
    }

    def search(self, results, media, lang, manual):
        key = AgentBase.get_key(media)
        Log('Key : %s', key)
        ret = self.instance_list['Y'].search(results, media, lang, manual)
        if ret: #처리했으면 True
            return
        if ret == False and key == 'Y':
            # 태그에서 읽는 것을 막기 위해 더미로 update타도록..
            results.Append(MetadataSearchResult(id='YD%s'% int(time.time()), name=media.title, year='', score=100, thumb='', lang=lang))
            return
            
        self.instance_list[key].search(results, media, lang, manual)
        


    def update(self, metadata, media, lang):
        Log('updata : %s', metadata.id)
        need_lyric = self.instance_list[metadata.id[0]].update(metadata, media, lang)
        
        if metadata.id[0] != 'Y':
            need_lyric = self.instance_list['Y'].update(metadata, media, lang, is_primary=False)
        
        
        need_lyric = False
        if need_lyric:
            Log("가사 탐색")
            self.instance_list['L'].update(metadata, media, lang, is_primary=False)
        