# -*- coding: utf-8 -*-
class SjvaAgentMovie(Agent.Movies):
    name = u'SJVA 영화 (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass
