# -*- coding: utf-8 -*-
class SjvaAgentAni(Agent.TV_Shows):
    name = 'SJVA 애니 (dummy)'
    
    fallback_agent = 'com.plexapp.agents.sjva_agent'
    languages = [Locale.Language.Korean]
    primary_provider = True

    def search(self, results, media, lang, manual, **kwargs):
        pass
