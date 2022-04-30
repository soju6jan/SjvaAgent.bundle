# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata
from .agent_base import AgentBase
from .module_music_normal import ModuleMusicNormalArtist, ModuleMusicNormalAlbum
from .module_audiobook import ModuleAudiobookArtist, ModuleAudiobookAlbum
from .module_audiobook_json import ModuleAudiobookJsonArtist, ModuleAudiobookJsonAlbum
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
        'J' : ModuleAudiobookJsonArtist(),
        'Y' : ModuleYamlArtist(),
    }

    def search(self, results, media, lang, manual):
        key = AgentBase.get_key(media)
        Log('Key : %s', key)
        ret = self.instance_list['Y'].search(results, media, lang, manual)
        if ret or key == 'Y':
            return
        if key == 'B':
            ret = self.instance_list['J'].search(results, media, lang, manual)
            if ret:
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
        'J' : ModuleAudiobookJsonAlbum(),
        'Y' : ModuleYamlAlbum(),
        'L' : ModuleLyric(),
    }

    def search(self, results, media, lang, manual):
        key = AgentBase.get_key(media)
        Log('Key : %s', key)
        #ret = self.instance_list['Y'].search(results, media, lang, manual)
        #if ret or key == 'Y':
        #    return
        #if key == 'B':
        #    ret = self.instance_list['J'].search(results, media, lang, manual)
        #    if ret:
        #        return
        self.instance_list[key].search(results, media, lang, manual)
        
    def update(self, metadata, media, lang):
        Log('updata : %s', metadata.id)
        need_lyric = self.instance_list[metadata.id[0]].update(metadata, media, lang)
        Log('CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC')
        """
        if metadata.id[0] != 'Y':
            need_lyric = self.instance_list['Y'].update(metadata, media, lang, is_primary=False)
        """
        #if need_lyric != False:
        #    Log("가사 탐색")
        #    self.instance_list['L'].update(metadata, media, lang, is_primary=False)

        Log(metadata.title)
