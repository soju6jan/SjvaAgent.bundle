# -*- coding: utf-8 -*-
import os, traceback, json, urllib, re, unicodedata, time
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
        if ret:
            return
        if ret == False and key == 'Y':
            # 태그에서 읽는 것을 막기 위해 더미로 update타도록..
            # 2022-05-26 tiem.time()이 같을 수 있음..
            results.Append(MetadataSearchResult(id='YD%s'% str(time.time()).replace('.', ''), name=media.title, year='', score=100, thumb='', lang=lang))
            return
        ret = self.instance_list[key].search(results, media, lang, manual)
        if key == 'F':
            if ret == False:
                ret = self.instance_list['K'].search(results, media, lang, manual)
        

    def update(self, metadata, media, lang):
        Log('updata : %s', metadata.id)
        # 2022-02-06 
        # 파일로 된 부가영상이 먼저 나오게 순서 변경
        # Y로 호출할 뿐 모듈은 상관 없음. static function 
        if self.instance_list['Y'].is_show_extra(media):
            import local_tv_extras
            local_tv_extras.update(metadata, media)

        self.instance_list[metadata.id[0]].update(metadata, media, lang)
        if metadata.id[0] != 'Y':
            self.instance_list['Y'].update(metadata, media, lang, is_primary=False)

        
        

        