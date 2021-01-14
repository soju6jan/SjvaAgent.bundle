# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata
from .agent_base import AgentBase
from .module_ott_movie import ModuleOttMovie
from .module_ott_show import ModuleOttShow

class AgentJavCensored(AgentBase):
    module_name = 'jav_censored'
    
    def search(self, results, media, lang, manual):
        keyword = self.get_search_keyword(media, manual, from_file=True)
        keyword = keyword.replace(' ', '-')
        self.base_search(results, media, lang, manual, keyword)
 

    def update(self, metadata, media, lang):
        self.base_update(metadata, media, lang)


class AgentJavCensoredAma(AgentBase):
    module_name = 'jav_censored_ama'
    
    def search(self, results, media, lang, manual):
        keyword = self.get_search_keyword(media, manual, from_file=True)
        keyword = keyword.replace(' ', '-')
        self.base_search(results, media, lang, manual, keyword)

    def update(self, metadata, media, lang):
        self.base_update(metadata, media, lang)



class AgentMovie(Agent.Movies):
    name = "SJVA 설정"
    languages = [Locale.Language.Korean]
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia', 'com.plexapp.agents.xbmcnfo']
    contributes_to = ['com.plexapp.agents.xbmcnfo']
    
    instance_list = {
        'C' : AgentJavCensored(), 
        'D' : AgentJavCensoredAma(), 
        'O' : ModuleOttMovie(), 
        'P' : ModuleOttShow(),
    }

    def search(self, results, media, lang, manual):
        key = AgentBase.get_key(media)
        Log('Key : %s', key)
        self.instance_list[key].search(results, media, lang, manual)
        
    def update(self, metadata, media, lang):
        Log('updata : %s', metadata.id)
        self.instance_list[metadata.id[0]].update(metadata, media, lang)






    #identifier, media_type, lang, manual, kwargs, version, primary=False):