# -*- coding: utf-8 -*-
class SjvaAgentFtv(Agent.TV_Shows):
    name = 'SJVA 외국TV (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass
