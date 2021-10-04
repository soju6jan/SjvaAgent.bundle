# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata
from .agent_base import AgentBase
from .module_jav_censored import ModuleJavCensoredDvd, ModuleJavCensoredAma, ModuleJavFc2
from .module_ott_show import ModuleOttShow
from .module_movie import ModuleMovie
from .module_yaml_movie import ModuleYamlMovie


class AgentMovie(Agent.Movies):
    name = "SJVA 설정"
    languages = [Locale.Language.Korean]
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia', 'com.plexapp.agents.localmediapatch', 'com.plexapp.agents.xbmcnfo']
    contributes_to = ['com.plexapp.agents.xbmcnfo']
    
    instance_list = { 
        'C' : ModuleJavCensoredDvd(), 
        'D' : ModuleJavCensoredAma(), 
        'L' : ModuleJavFc2(), 
        'P' : ModuleOttShow(),
        'M' : ModuleMovie(), 
        'Y' : ModuleYamlMovie(),
    }

    def search(self, results, media, lang, manual):
        key = AgentBase.get_key(media)
        Log('Key : %s', key)
        ret = self.instance_list['Y'].search(results, media, lang, manual)
        if ret or key == 'Y':
            return
        ret = self.instance_list[key].search(results, media, lang, manual)
        if ret == False and key == 'C' and Prefs['jav_dvd_search_all']:
            ret = self.instance_list['D'].search(results, media, lang, manual)
            if ret == False:
                ret = self.instance_list['L'].search(results, media, lang, manual)
        
    def update(self, metadata, media, lang):
        Log('updata : %s', metadata.id)
        self.instance_list[metadata.id[0]].update(metadata, media, lang)
        if metadata.id[0] != 'Y':
            self.instance_list['Y'].update(metadata, media, lang, is_primary=False)

         