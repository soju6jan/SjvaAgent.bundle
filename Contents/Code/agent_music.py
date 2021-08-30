# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata
from .agent_base import AgentBase
from .module_music import ModuleMusicArtist, ModuleMusicAlbum
from .module_audiobook import ModuleAudiobookArtist, ModuleAudiobookAlbum
from .module_audiobook_json import ModuleAudiobookJsonArtist, ModuleAudiobookJsonAlbum

class AgentArtist(Agent.Artist):
    name = "SJVA 설정"
    languages = [Locale.Language.Korean]
    primary_provider = True
    #accepts_from = ['com.plexapp.agents.localmedia', 'com.plexapp.agents.localmediapatch', 'com.plexapp.agents.xbmcnfo']
    #contributes_to = ['com.plexapp.agents.xbmcnfo']


    instance_list = { 
        'V' : ModuleMusicArtist(), 
        'B' : ModuleAudiobookArtist(),
        'J' : ModuleAudiobookJsonArtist(),
    }

    def search(self, results, media, lang, manual):
        key = AgentBase.get_key(media)
        Log('Key : %s', key)
        if key == 'B':
            ret = self.instance_list['J'].search(results, media, lang, manual)
            Log(ret)
            Log(ret)
            Log(ret)
            Log(ret)
            
            if ret:
                return
        self.instance_list[key].search(results, media, lang, manual)
        
    def update(self, metadata, media, lang):
        Log('updata : %s', metadata.id)
        self.instance_list[metadata.id[0]].update(metadata, media, lang)


class AgentAlbum(Agent.Album):
    name = "SJVA 설정"
    languages = [Locale.Language.Korean]
    primary_provider = True
    #accepts_from = ['com.plexapp.agents.localmedia', 'com.plexapp.agents.localmediapatch', 'com.plexapp.agents.xbmcnfo']
    #contributes_to = ['com.plexapp.agents.xbmcnfo']

    instance_list = { 
        'V' : ModuleMusicAlbum(),
        'B' : ModuleAudiobookAlbum(),
        'J' : ModuleAudiobookJsonAlbum(),
    }

    def search(self, results, media, lang, manual):
        key = AgentBase.get_key(media)
        Log('Key : %s', key)
        if key == 'B':
            ret = self.instance_list['J'].search(results, media, lang, manual)
            if ret:
                return
        self.instance_list[key].search(results, media, lang, manual)
        
    def update(self, metadata, media, lang):
        Log('updata : %s', metadata.id)
        self.instance_list[metadata.id[0]].update(metadata, media, lang)