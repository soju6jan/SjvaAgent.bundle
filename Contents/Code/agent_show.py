# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata
from .agent_base import AgentBase
from .module_ktv import ModuleKtv
from .module_ftv import ModuleFtv
from .module_yaml_show import ModuleYamlShow

class AgentShow(Agent.TV_Shows):
    name = "SJVA 설정"
    languages = [Locale.Language.Korean]
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia', 'com.plexapp.agents.localmediapatch', 'com.plexapp.agents.xbmcnfo']
    contributes_to = ['com.plexapp.agents.xbmcnfo']
    
    instance_list = {
        'K' : ModuleKtv(), 
        'F' : ModuleFtv(), 
        'Y' : ModuleYamlShow(),
    }

    def search(self, results, media, lang, manual):
        key = AgentBase.get_key(media)
        Log('Key : %s', key)
        ret = self.instance_list['Y'].search(results, media, lang, manual)
        if ret or key == 'Y':
            return
        ret = self.instance_list[key].search(results, media, lang, manual)
        if key == 'F':
            if ret == False:
                ret = self.instance_list['K'].search(results, media, lang, manual)
        

    def update(self, metadata, media, lang):
        Log('updata : %s', metadata.id)
        self.instance_list[metadata.id[0]].update(metadata, media, lang)
        if metadata.id[0] != 'Y':
            self.instance_list['Y'].update(metadata, media, lang, is_primary=False)
        import local_tv_extras
        local_tv_extras.update(metadata, media)

        