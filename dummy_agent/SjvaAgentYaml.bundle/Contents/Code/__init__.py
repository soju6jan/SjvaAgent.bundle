# -*- coding: utf-8 -*-
class SjvaAgentYamlMusicArtist(Agent.Artist):
    name = 'SJVA YAML Artist (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass


class SjvaAgentYamlMusicAlbum(Agent.Album):
    name = 'SJVA YAML Album (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass


class SjvaAgentYamlMusicMovie(Agent.Movies):
    name = 'SJVA YAML Movie (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass


class SjvaAgentYamlMusicShow(Agent.TV_Shows):
    name = u'SJVA YAML Show (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass
