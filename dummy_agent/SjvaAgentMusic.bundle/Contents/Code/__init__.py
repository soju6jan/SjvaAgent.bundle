# -*- coding: utf-8 -*-
class SjvaAgentMusicArtist(Agent.Artist):
    name = 'SJVA Music Artist (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass


class SjvaAgentMusicAlbum(Agent.Album):
    name = 'SJVA Music Album (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass
