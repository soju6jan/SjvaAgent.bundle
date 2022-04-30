# -*- coding: utf-8 -*-
class SjvaAgentMusicNormalArtist(Agent.Artist):
    name = 'SJVA MusicNormal (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass


class SjvaAgentMusicNormalAlbum(Agent.Album):
    name = 'SJVA MusicNormal (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass
