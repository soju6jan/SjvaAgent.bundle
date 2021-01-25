# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata
from .agent_base import AgentBase
from .module_jav_censored import ModuleJavCensoredDvd, ModuleJavCensoredAma
from .module_ott_show import ModuleOttShow
from .module_movie import ModuleMovie



class AgentMovie(Agent.Movies):
    name = "SJVA 설정"
    languages = [Locale.Language.Korean]
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia', 'com.plexapp.agents.xbmcnfo']
    contributes_to = ['com.plexapp.agents.xbmcnfo']
    
    instance_list = { 
        'C' : ModuleJavCensoredDvd(), 
        'D' : ModuleJavCensoredAma(), 
        'P' : ModuleOttShow(),
        'M' : ModuleMovie(), 
    }

    def search(self, results, media, lang, manual):
        key = AgentBase.get_key(media)
        Log('Key : %s', key)
        self.instance_list[key].search(results, media, lang, manual)
        
    def update(self, metadata, media, lang):
        Log('updata : %s', metadata.id)
        self.instance_list[metadata.id[0]].update(metadata, media, lang)
