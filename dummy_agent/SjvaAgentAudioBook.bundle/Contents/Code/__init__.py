# -*- coding: utf-8 -*-
class SjvaAgentAudioBookArtist(Agent.Artist):
    name = 'SJVA AudioBook (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass


class SjvaAgentAudioBookAlbum(Agent.Album):
    name = 'SJVA AudioBook (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass
