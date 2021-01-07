# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata
from .agent_base import AgentBase
from .module_ott_movie import ModuleOttMovie

class ModuleKtv(AgentBase):
    module_name = 'ktv'
    
    def search(self, results, media, lang, manual):
        keyword = self.get_search_keyword(media, manual, from_file=True)
        keyword = keyword.replace(' ', '-')
        self.base_search(results, media, lang, manual, keyword)

    def update(self, metadata, media, lang):
        self.base_update(metadata, media, lang)



class AgentShow(Agent.TV_Shows):
    name = "SJVA Show (Do not Select)"
    languages = [Locale.Language.Korean]
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia', 'com.plexapp.agents.xbmcnfo']
    contributes_to = ['com.plexapp.agents.xbmcnfo']
    
    instance_list = {
        'K' : ModuleKtv(), 
    }

    def search(self, results, media, lang, manual):
        key = AgentBase.get_key(media)
        Log('Key : %s', key)
        self.instance_list[key].search(results, media, lang, manual)
        
    def update(self, metadata, media, lang):
        Log('updata : %s', metadata.id)
        self.instance_list[metadata.id[0]].update(metadata, media, lang)



