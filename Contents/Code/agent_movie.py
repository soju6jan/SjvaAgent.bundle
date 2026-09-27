# -*- coding: utf-8 -*-
from .agent_base import AgentBase
from .module_jav_censored import ModuleJavCensored, ModuleJavUnCensored, ModuleWestern
from .module_ott_show import ModuleOttShow
from .module_movie import ModuleMovie
from .module_yaml_movie import ModuleYamlMovie

Log = Log # type: Framework.api.logkit.LogKit
Prefs = Prefs # type: Framework.api.runtimekit.PrefsKit
Locale = Locale # type: Framework.api.localekit.LocaleKit
Agent = Agent # type: Framework.api.agentkit.AgentKit


class AgentMovie(Agent.Movies):
    name = "SJVA 설정"
    languages = [Locale.Language.Korean]
    primary_provider = True
    accepts_from = ['com.plexapp.agents.localmedia', 'com.plexapp.agents.localmediapatch', 'com.plexapp.agents.xbmcnfo']
    contributes_to = ['com.plexapp.agents.xbmcnfo']

    instance_list = {
        'C' : ModuleJavCensored(),
        'E' : ModuleJavUnCensored(),
        'W' : ModuleWestern(),
        'P' : ModuleOttShow(),
        'M' : ModuleMovie(),
        'Y' : ModuleYamlMovie(),
    }

    def search(self, results, media, lang, manual):
        key = AgentBase.get_key(media)
        Log('Key : %s', key)

        if manual and key in ['C', 'E', 'W'] and media.name is not None and media.name.startswith('JAVALL'):
            for jav_key in ['C', 'E', 'W']:
                self.instance_list[jav_key].search(results, media, lang, manual)
            return

        ret = self.instance_list['Y'].search(results, media, lang, manual)
        if ret or key == 'Y':
            return
        ret = self.instance_list[key].search(results, media, lang, manual)
        if ret == False and key == 'C' and Prefs['jav_dvd_search_all']:
            for jav_key in ['D', 'E', 'L']:
                if self.instance_list[jav_key].search(results, media, lang, manual):
                    return

    def update(self, metadata, media, lang):
        Log('update : %s', metadata.id)
        self.instance_list[metadata.id[0]].remove_metadata(metadata, media, "Movies")
        self.instance_list[metadata.id[0]].update(metadata, media, lang)
        if metadata.id[0] != 'Y' and self.instance_list[metadata.id[0]].is_yaml_enabled(media):
            self.instance_list['Y'].update(metadata, media, lang, is_primary=False)

        if self.instance_list['Y'].is_collection_append(media) == False:
            metadata.collections.clear()
            Log('collections clear')
        else:
            for a in metadata.collections:
                Log(a)
