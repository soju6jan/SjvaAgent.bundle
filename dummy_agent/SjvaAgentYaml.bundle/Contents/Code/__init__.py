# -*- coding: utf-8 -*-
class SjvaAgentYamlMusicArtist(Agent.Artist):
    name = 'SJVA YAML (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass


class SjvaAgentYamlMusicAlbum(Agent.Album):
    name = 'SJVA YAML (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass


class SjvaAgentYamlMusicMovie(Agent.Movies):
    name = 'SJVA YAML (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass


class SjvaAgentYamlMusicShow(Agent.TV_Shows):
    name = u'SJVA YAML (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass
