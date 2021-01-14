# -*- coding: utf-8 -*-
class SjvaAgentOttShow(Agent.Movies):
    name = 'SJVA OTT 방송 (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass
